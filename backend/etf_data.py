import os
import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
import logging
from datetime import date, datetime

load_dotenv()

def get_db_connection():
    """Create a database connection using DATABASE_URL_ETF from .env."""
    db_url = os.getenv('DATABASE_URL_ETF')
    if not db_url:
        logging.error("DATABASE_URL_ETF not found in environment variables.")
        return None
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def fetch_etf_data():
    """
    Fetch ETF data from Supabase and format it for the dashboard.
    Returns a dictionary with summary, flows, and daily data.
    """
    conn = get_db_connection()
    if not conn:
        return {}

    data = {
        'summary': [],
        'daily': {},
        'flows_agg': [],
        'dates': []
    }

    try:
        # 1. Fetch Summary Data for the last few days to handle fallbacks
        # We fetch the latest date and the previous ones to fill holes
        summary_query = """
            SELECT *
            FROM v_etf_summary 
            WHERE date >= (SELECT MAX(date) FROM v_etf_summary) - INTERVAL '10 days'
            ORDER BY date DESC
        """
        df_summary_raw = pd.read_sql(summary_query, conn)
        # logging.info(f"Summary columns: {df_summary_raw.columns.tolist()}")
        
        # Fallback logic: For each ticker, get the latest record, 
        # but if NAV/Discount is null, find the most recent non-null
        latest_date = df_summary_raw['date'].max()
        tickers = df_summary_raw['ticker'].unique()
        summary_list = []
        
        for ticker in tickers:
            ticker_data = df_summary_raw[df_summary_raw['ticker'] == ticker].sort_values('date', ascending=False)
            latest_rec = ticker_data.iloc[0].to_dict()
            
            # If latest is not the actual latest global date, it might be an inactive ETF or missing record
            # But the user specifically wants the D-1 fallback if TODAY is null.
            
            fields_to_fix = ['nav', 'premium_discount', 'market_price', 'shares_outstanding', 'holdings_btc', 'aum_usd']
            for field in fields_to_fix:
                if pd.isna(latest_rec[field]) or latest_rec[field] == 0:
                    # Look back for non-null
                    non_null_vals = ticker_data[ticker_data[field].notnull() & (ticker_data[field] != 0)][field]
                    if not non_null_vals.empty:
                        latest_rec[field] = non_null_vals.iloc[0]
            
            # Ensure date is string
            if isinstance(latest_rec['date'], (date, datetime)):
                latest_rec['date'] = latest_rec['date'].isoformat()
                
            summary_list.append(latest_rec)
        
        # Sort by AUM
        summary_list = sorted(summary_list, key=lambda x: x['aum_usd'] or 0, reverse=True)
        data['summary'] = summary_list

        # 3. Fetch Daily Flows & AUM history
        # We join with etf_daily_data to get holdings for total AUM calculation
        agg_query = """
            SELECT 
                f.date, 
                SUM(f.flow_btc) as total_flow_btc, 
                SUM(f.flow_btc * COALESCE(p.price_usd, 0)) as total_flow_usd,
                SUM(COALESCE(d.holdings_btc, 0) * COALESCE(p.price_usd, 0)) as total_aum_usd,
                CASE 
                    WHEN SUM(COALESCE(d.holdings_btc, 0) * COALESCE(p.price_usd, 0)) > 0 
                    THEN SUM(COALESCE(d.premium_discount, 0) * COALESCE(d.holdings_btc, 0) * COALESCE(p.price_usd, 0)) / SUM(COALESCE(d.holdings_btc, 0) * COALESCE(p.price_usd, 0))
                    ELSE 0 
                END as avg_premium_discount
            FROM etf_flows f
            LEFT JOIN btc_prices p ON f.date = p.date
            LEFT JOIN etf_daily_data d ON f.etf_id = d.etf_id AND f.date = d.date
            GROUP BY f.date
            ORDER BY f.date ASC
        """
        df_agg = pd.read_sql(agg_query, conn)
        df_agg['cum_flow_btc'] = df_agg['total_flow_btc'].cumsum()
        df_agg['cum_flow_usd'] = df_agg['total_flow_usd'].cumsum()
        
        # --- Data Cleaning: Wash Outliers in Premium/Discount (Jan 2025) ---
        # A 2% threshold is usually safe for Spot BTC ETFs
        outlier_mask = (df_agg['avg_premium_discount'] > 2) | (df_agg['avg_premium_discount'] < -2)
        # Handle date type comparison safely
        df_agg['date_dt'] = pd.to_datetime(df_agg['date']).dt.date
        jan_2025_mask = (df_agg['date_dt'] >= date(2025, 1, 1)) & (df_agg['date_dt'] < date(2025, 2, 1))
        df_agg.loc[outlier_mask & jan_2025_mask, 'avg_premium_discount'] = np.nan
        df_agg['avg_premium_discount'] = df_agg['avg_premium_discount'].ffill().fillna(0)

        # Normalization: Rolling Z-Score and Percentile (252 days)
        window_norm = 252
        df_agg['pd_zscore_1y'] = (df_agg['avg_premium_discount'] - df_agg['avg_premium_discount'].rolling(window=window_norm, min_periods=30).mean()) / df_agg['avg_premium_discount'].rolling(window=window_norm, min_periods=30).std()
        df_agg['pd_percentile_1y'] = df_agg['avg_premium_discount'].rolling(window=window_norm, min_periods=30).rank(pct=True) * 100

        # Rolling Flows (7d, 30d, 90d)
        df_agg['flow_usd_7d'] = df_agg['total_flow_usd'].rolling(window=7, min_periods=1).sum()
        df_agg['flow_usd_30d'] = df_agg['total_flow_usd'].rolling(window=30, min_periods=1).sum()
        df_agg['flow_usd_90d'] = df_agg['total_flow_usd'].rolling(window=90, min_periods=1).sum()
        
        # ROC Calculation for Total AUM
        for days in [7, 30, 90]:
            df_agg[f'aum_roc_{days}d'] = df_agg['total_aum_usd'].pct_change(periods=days) * 100
        
        # Moving Average for charts (e.g., 20d SMA)
        df_agg['flow_usd_ma20'] = df_agg['total_flow_usd'].rolling(window=20, min_periods=5).mean()
        
        # Convert date to string for JSON compatibility
        df_agg['date'] = df_agg['date'].astype(str)
        # Thorough cleaning for JSON
        df_agg = df_agg.drop(columns=['date_dt']).fillna(0).replace([np.inf, -np.inf], 0)
        data['flows_agg'] = df_agg.to_dict(orient='list')
        data['dates'] = df_agg['date'].tolist()

        # 4. Fetch Daily Data for each individual ETF (top ones)
        top_etfs = [s['ticker'] for s in summary_list[:15]]
        individual_daily = {}
        for ticker in top_etfs:
            ind_query = f"""
                SELECT 
                    f.date, 
                    f.flow_btc, 
                    f.flow_btc * COALESCE(p.price_usd, 0) as flow_usd,
                    d.nav, 
                    d.shares_outstanding, 
                    d.holdings_btc,
                    d.premium_discount
                FROM etf_flows f
                JOIN etfs e ON f.etf_id = e.id
                LEFT JOIN btc_prices p ON f.date = p.date
                LEFT JOIN etf_daily_data d ON f.etf_id = d.etf_id AND f.date = d.date
                WHERE e.ticker = '{ticker}'
                ORDER BY f.date ASC
            """
            df_ind = pd.read_sql(ind_query, conn)
            df_ind['date'] = df_ind['date'].astype(str)
            
            # Forward fill NAV and other metrics to avoid zeros/gaps in charts
            cols_to_fill = ['nav', 'shares_outstanding', 'holdings_btc', 'premium_discount']
            df_ind[cols_to_fill] = df_ind[cols_to_fill].ffill()

            # --- Individual Data Cleaning: Wash Outliers in Premium/Discount (Jan 2025) ---
            outlier_mask_ind = (df_ind['premium_discount'] > 3) | (df_ind['premium_discount'] < -3)
            df_ind['date_dt'] = pd.to_datetime(df_ind['date']).dt.date
            jan_2025_mask_ind = (df_ind['date_dt'] >= date(2025, 1, 1)) & (df_ind['date_dt'] < date(2025, 2, 1))
            df_ind.loc[outlier_mask_ind & jan_2025_mask_ind, 'premium_discount'] = np.nan
            df_ind['premium_discount'] = df_ind['premium_discount'].ffill().fillna(0)

            # Individual Normalization: Rolling Z-Score and Percentile (252 days)
            df_ind['pd_zscore_1y'] = (df_ind['premium_discount'] - df_ind['premium_discount'].rolling(window=window_norm, min_periods=30).mean()) / df_ind['premium_discount'].rolling(window=window_norm, min_periods=30).std()
            df_ind['pd_percentile_1y'] = df_ind['premium_discount'].rolling(window=window_norm, min_periods=30).rank(pct=True) * 100
            
            # Clean up internal column and finalize for JSON
            df_ind = df_ind.drop(columns=['date_dt']).fillna(0).replace([np.inf, -np.inf], 0)
            individual_daily[ticker] = df_ind.to_dict(orient='list')
        
        data['individual_daily'] = individual_daily

    except Exception as e:
        logging.error(f"Error fetching ETF data: {e}")
    finally:
        conn.close()

    return data

if __name__ == "__main__":
    # Test connection and fetching
    result = fetch_etf_data()
    if result:
        print("Successfully fetched ETF data.")
        print(f"Summary records: {len(result.get('summary', []))}")
        print(f"Individual tracks for: {list(result.get('individual_daily', {}).keys())}")
    else:
        print("Failed to fetch ETF data.")
