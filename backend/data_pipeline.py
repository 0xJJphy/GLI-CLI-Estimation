import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fredapi import Fred
from dotenv import load_dotenv
import json
import time

# tvDatafeed import
try:
    from tvDatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    print("WARNING: tvDatafeed not found. Please install it using: pip install git+https://github.com/rongardF/tvdatafeed.git")
    TvDatafeed = None
    Interval = None
    TV_AVAILABLE = False

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
load_dotenv()

FRED_API_KEY = os.environ.get('FRED_API_KEY')
TV_USERNAME = os.environ.get('TV_USERNAME')
TV_PASSWORD = os.environ.get('TV_PASSWORD')
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'FRED') # Default to FRED

if not FRED_API_KEY:
    print("WARNING: FRED_API_KEY not found in environment. Please add it to your .env file.")

fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

def try_tv_login(username, password, max_retries=5, delay=2):
    """Attempts to log in to TradingView with a retry loop."""
    if not TV_AVAILABLE:
        return None

    for i in range(max_retries):
        try:
            print(f"Attempting TV Login ({i+1}/{max_retries})...")
            if username and password:
                tv_instance = TvDatafeed(username, password)
            else:
                tv_instance = TvDatafeed()
            print("TV Login Successful!")
            return tv_instance
        except Exception as e:
            print(f"TV Login failed (Attempt {i+1}): {e}")
            if i < max_retries - 1:
                time.sleep(delay)
    print("Could not log in to TradingView after multiple attempts. Fallback to Guest.")
    try:
        return TvDatafeed()
    except:
        return None

tv = try_tv_login(TV_USERNAME, TV_PASSWORD) if TV_AVAILABLE else None

START_DATE = '1970-01-01'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# SERIES DEFINITIONS
# ============================================================
# Mapping: FRED_ID -> Internal Name
FRED_CONFIG = {
    'WALCL': 'FED',
    'ECBASSETSW': 'ECB',
    'JPNASSETS': 'BOJ',
    'MABMM301GBM189S': 'BOE',
    'MABMM301CNA189S': 'PBOC',
    'DEXUSEU': 'EURUSD',
    'DEXJPUS': 'USDJPY',
    'DEXUSUK': 'GBPUSD',
    'DEXCHUS': 'USDCNY',
    'WTREGEN': 'TGA',
    'RRPONTSYD': 'RRP',
    'BAMLH0A0HYM2': 'HY_SPREAD',
    'BAMLC0A0CM': 'IG_SPREAD',
    'NFCI': 'NFCI',
    'NFCICREDIT': 'NFCI_CREDIT',
    'NFCIRISK': 'NFCI_RISK',
    'DRTSCILM': 'LENDING_STD',
    'VIXCLS': 'VIX'
}

# Mapping: Symbol -> Internal Name (TradingView ECONOMICS)
TV_CONFIG = {
    'USCBBS': ('ECONOMICS', 'FED'),
    'EUCBBS': ('ECONOMICS', 'ECB'),
    'JPCBBS': ('ECONOMICS', 'BOJ'),
    'GBCBBS': ('ECONOMICS', 'BOE'),
    'CNCBBS': ('ECONOMICS', 'PBOC'),
    'EURUSD': ('FX_IDC', 'EURUSD'),
    'USDJPY': ('FX_IDC', 'USDJPY'),
    'GBPUSD': ('FX_IDC', 'GBPUSD'),
    'CNYUSD': ('FX_IDC', 'CNYUSD'),
    'BTCUSD': ('BITSTAMP', 'BTC'),
}

# ============================================================
# DATA FETCHING
# ============================================================
def fetch_fred_series(series_id, name):
    if not fred:
        return pd.Series(dtype=float, name=name)
    try:
        data = fred.get_series(series_id, observation_start=START_DATE)
        data.name = name
        return data
    except Exception as e:
        print(f"Error fetching FRED {series_id} ({name}): {e}")
        return pd.Series(dtype=float, name=name)

def fetch_tv_series(symbol, exchange, name, n_bars=5000):
    if not tv:
        return pd.Series(dtype=float, name=name)
    try:
        # TradingView interval mapping
        # We use daily for most, but economics might be less frequent
        df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=n_bars)
        if df is not None and len(df) > 0:
            s = df['close']
            s.name = name
            return s
        return pd.Series(dtype=float, name=name)
    except Exception as e:
        print(f"Error fetching TV {symbol} ({name}): {e}")
        return pd.Series(dtype=float, name=name)

# ============================================================
# CALCULATIONS
# ============================================================
def normalize_zscore(series, window=504):
    mean = series.rolling(window=window, min_periods=100).mean()
    std = series.rolling(window=window, min_periods=100).std()
    return (series - mean) / std

def calculate_gli_from_trillions(df):
    """Summarizes GLI components that are already in Trillions USD."""
    res = pd.DataFrame(index=df.index)
    cols = ['FED_USD', 'ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD']
    for col in cols:
        if col in df.columns:
            res[col] = df[col]
        else:
            res[col] = 0.0
    res['GLI_TOTAL'] = res[cols].sum(axis=1)
    return res

def calculate_us_net_liq_from_trillions(df):
    """Calculates Net Liq from Trillion-scale components."""
    res = pd.DataFrame(index=df.index)
    # df['FED_USD'] is Trillions. TGA and RRP should also be in Trillions.
    res['NET_LIQUIDITY'] = df.get('FED_USD', 0) - df.get('TGA_USD', 0) - df.get('RRP_USD', 0)
    return res

def calculate_cli(df):
    """Calculates Credit Liquidity Index."""
    res = pd.DataFrame(index=df.index)
    res['HY_SPREAD_Z'] = normalize_zscore(df['HY_SPREAD'])
    res['IG_SPREAD_Z'] = normalize_zscore(df['IG_SPREAD'])
    res['NFCI_CREDIT_Z'] = df['NFCI_CREDIT']
    res['NFCI_RISK_Z'] = df['NFCI_RISK']
    res['LENDING_STD_Z'] = normalize_zscore(df['LENDING_STD'])
    res['VIX_Z'] = normalize_zscore(df['VIX'])
    
    weights = {
        'HY_SPREAD_Z': 0.25,
        'IG_SPREAD_Z': 0.15,
        'NFCI_CREDIT_Z': 0.20,
        'NFCI_RISK_Z': 0.20,
        'LENDING_STD_Z': 0.10,
        'VIX_Z': 0.10
    }
    
    res['CLI'] = sum(res[col] * weight for col, weight in weights.items() if col in res.columns)
    return res

def calculate_gli(df, source='FRED'):
    """Calculates Global Liquidity Index in Trillions USD for 5 major central banks."""
    res = pd.DataFrame(index=df.index)
    
    if source == 'TV':
        # TradingView Units (ECONOMICS) - All are Raw Units (Units of Currency)
        res['FED_USD'] = df['FED'] / 1e12
        res['ECB_USD'] = (df['ECB'] * df['EURUSD']) / 1e12
        
        if 'USDJPY' in df.columns:
            res['BOJ_USD'] = (df['BOJ'] / df['USDJPY']) / 1e12
        elif 'JPYUSD' in df.columns:
            res['BOJ_USD'] = (df['BOJ'] * df['JPYUSD']) / 1e12
        else:
            # Fallback if no FX
            res['BOJ_USD'] = df['BOJ'] / 150e12
        
        res['BOE_USD'] = (df['BOE'] * df['GBPUSD']) / 1e12
        
        if 'CNYUSD' in df.columns:
            res['PBOC_USD'] = (df['PBOC'] * df['CNYUSD']) / 1e12
        elif 'USDCNY' in df.columns:
            res['PBOC_USD'] = (df['PBOC'] / df['USDCNY']) / 1e12
        else:
            res['PBOC_USD'] = (df['PBOC'] / 7.2) / 1e12
            
    else:
        # FRED Units logic:
        res['FED_USD'] = df['FED'] / 1e6
        res['ECB_USD'] = (df['ECB'] / 1e6) * df['EURUSD']
        res['BOJ_USD'] = (df['BOJ'] / 1e4) / df['USDJPY']
        res['BOE_USD'] = (df['BOE'] / 1e3) * df['GBPUSD']
        res['PBOC_USD'] = (df['PBOC'] / 1e12) / df['USDCNY']
    
    res['GLI_TOTAL'] = res[['FED_USD', 'ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD']].sum(axis=1)
    return res

def calculate_rocs(df, windows={'1M': 21, '3M': 63, '6M': 126, '1Y': 252}):
    """Calculates Rate of Change for specified windows."""
    rocs = {}
    for label, window in windows.items():
        # ROC Calculation: (Current / Past) - 1
        roc = (df / df.shift(window) - 1) * 100
        rocs[label] = roc.fillna(0)
    return rocs

def calculate_cross_correlation(series1, series2, max_lag=90):
    """
    Calculates cross-correlation between two series with different lags.
    Returns dict with lag as key and correlation as value.
    Negative lag means series1 leads series2.
    Positive lag means series2 leads series1.
    """
    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            # series1 leads (shift series2 backward)
            s1 = series1.iloc[:lag]
            s2 = series2.iloc[-lag:]
        elif lag > 0:
            # series2 leads (shift series1 backward)
            s1 = series1.iloc[lag:]
            s2 = series2.iloc[:-lag]
        else:
            s1 = series1
            s2 = series2

        # Calculate correlation on aligned data
        valid_idx = s1.index.intersection(s2.index)
        if len(valid_idx) > 30:  # Minimum 30 observations
            corr = s1[valid_idx].corr(s2[valid_idx])
            if pd.notnull(corr):
                correlations[lag] = corr

    return correlations

def calculate_btc_fair_value(df_t):
    """
    Calculates Bitcoin 'fair value' based on regression model using GLI, CLI, VIX.
    Returns DataFrame with actual BTC, fair value, and deviation bands.
    """
    from sklearn.linear_model import LinearRegression

    result = pd.DataFrame(index=df_t.index)

    # Check if we have BTC data
    if 'BTC' not in df_t.columns:
        return result

    # Prepare features - use lagged values for predictive power
    # GLI typically leads BTC by 30-60 days
    features = pd.DataFrame({
        'GLI_TOTAL': df_t.get('GLI_TOTAL', 0).shift(45),  # 45-day lag
        'CLI': df_t.get('CLI', 0).shift(14),  # 14-day lag
        'VIX': df_t.get('VIX', 0),  # Coincident
        'NET_LIQ': df_t.get('NET_LIQUIDITY', 0).shift(30),  # 30-day lag
    })

    target = df_t['BTC']

    # Create training set (drop NaN)
    train_data = pd.concat([features, target], axis=1).dropna()

    if len(train_data) < 100:  # Need minimum data
        result['BTC_ACTUAL'] = target
        return result

    X = train_data[['GLI_TOTAL', 'CLI', 'VIX', 'NET_LIQ']].values
    y = train_data['BTC'].values

    # Fit regression model
    model = LinearRegression()
    model.fit(X, y)

    # Predict on all available data
    X_all = features.dropna()
    predictions = pd.Series(model.predict(X_all.values), index=X_all.index)

    # Calculate residuals and standard deviation
    residuals = target[predictions.index] - predictions
    std_dev = residuals.std()

    # Build result DataFrame
    result['BTC_ACTUAL'] = target
    result['BTC_FAIR_VALUE'] = predictions
    result['BTC_UPPER_1SD'] = predictions + std_dev
    result['BTC_LOWER_1SD'] = predictions - std_dev
    result['BTC_UPPER_2SD'] = predictions + 2 * std_dev
    result['BTC_LOWER_2SD'] = predictions - 2 * std_dev
    result['BTC_DEVIATION_PCT'] = ((target - predictions) / predictions * 100)
    result['BTC_DEVIATION_ZSCORE'] = residuals / std_dev

    return result

def calculate_us_net_liq(df, source='FRED'):
    """Calculates US Net Liquidity in Trillions USD."""
    res = pd.DataFrame(index=df.index)
    
    if source == 'TV':
        # Everything is RAW (Units of Currency)
        fed_t = df['FED'] / 1e12
        tga_t = df['TGA'] / 1e12
        rrp_t = df['RRP'] / 1e12
    else:
        # Legacy FRED Units: FED: Millions, TGA: Millions, RRP: Billions
        fed_t = df['FED'] / 1e6
        tga_t = df['TGA'] / 1e6
        rrp_t = df['RRP'] / 1e3
    
    res['NET_LIQUIDITY'] = fed_t - tga_t - rrp_t
    return res

# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline():
    print("Starting Data Pipeline...")
    
    # 1. Fetch FRED Baseline and Normalize to Trillions
    print("Fetching FRED Baseline Data (Trillions)...")
    dfs_fred_t = {}
    raw_fred = {}
    for sid, name in FRED_CONFIG.items():
        raw_fred[name] = fetch_fred_series(sid, name)
    
    # Unit Logic for FRED -> Trillions
    df_fred = pd.DataFrame(index=pd.concat(raw_fred.values()).index.unique()).sort_index()
    for name, s in raw_fred.items():
        df_fred[name] = s
    df_fred = df_fred.ffill().bfill()
    
    # Derived Trillion Columns
    df_fred_t = pd.DataFrame(index=df_fred.index)
    df_fred_t['FED_USD'] = df_fred['FED'] / 1e6
    df_fred_t['ECB_USD'] = (df_fred['ECB'] / 1e6) * df_fred.get('EURUSD', 1.0)
    df_fred_t['BOJ_USD'] = (df_fred['BOJ'] / 1e4) / df_fred.get('USDJPY', 150)
    df_fred_t['BOE_USD'] = (df_fred['BOE'] / 1e12) * df_fred.get('GBPUSD', 1.3) # Raw -> Trillions
    df_fred_t['PBOC_USD'] = (df_fred['PBOC'] / 1e12) / df_fred.get('USDCNY', 7.2) # Raw -> Trillions
    df_fred_t['TGA_USD'] = df_fred['TGA'] / 1e6
    df_fred_t['RRP_USD'] = df_fred['RRP'] / 1e3
    df_fred_t['VIX'] = df_fred['VIX']
    df_fred_t['HY_SPREAD'] = df_fred['HY_SPREAD']
    df_fred_t['CLI'] = calculate_cli(df_fred)['CLI']

    # 2. Fetch TV and Normalize to Trillions
    print("Fetching TradingView Update Data (Trillions)...")
    raw_tv = {}
    if tv:
        for symbol, (exchange, name) in TV_CONFIG.items():
            s = fetch_tv_series(symbol, exchange, name, n_bars=1000)
            if not s.empty: raw_tv[name] = s
    
    df_tv_t = pd.DataFrame(index=pd.concat(raw_tv.values()).index.unique() if raw_tv else []).sort_index()
    if raw_tv:
        for name, s in raw_tv.items(): df_tv_t[name] = s
        df_tv_t = df_tv_t.ffill().bfill()
        
        # Unit Logic for TV -> Trillions
        res_tv_t = pd.DataFrame(index=df_tv_t.index)
        res_tv_t['FED_USD'] = df_tv_t.get('FED', 0) / 1e12
        eurusd = df_tv_t.get('EURUSD', df_fred.get('EURUSD', 1.0))
        res_tv_t['ECB_USD'] = (df_tv_t.get('ECB', 0) * eurusd) / 1e12
        usdjpy = df_tv_t.get('USDJPY', df_fred.get('USDJPY', 150))
        res_tv_t['BOJ_USD'] = (df_tv_t.get('BOJ', 0) / usdjpy) / 1e12
        gbpusd = df_tv_t.get('GBPUSD', df_fred.get('GBPUSD', 1.3))
        res_tv_t['BOE_USD'] = (df_tv_t.get('BOE', 0) * gbpusd) / 1e12
        cnynusd = df_tv_t.get('CNYUSD', df_fred.get('CNYUSD', 0.14))
        res_tv_t['PBOC_USD'] = (df_tv_t.get('PBOC', 0) * cnynusd) / 1e12

        # Bitcoin price (already in USD, no conversion needed)
        res_tv_t['BTC'] = df_tv_t.get('BTC', pd.Series(dtype=float))

        # TGA/RRP are usually not in TV economics, fallback to FRED baseline
        # We use combine_first to ensure we have the full FRED history for these columns
        # Then we ffill() to carry the last FRED value forward to the latest TV date
        res_tv_t = res_tv_t.combine_first(df_fred_t[['TGA_USD', 'RRP_USD', 'VIX', 'HY_SPREAD', 'CLI']]).ffill()
        df_tv_t = res_tv_t
    
    # 3. Hybrid Merge (Trillions to Trillions)
    # Clip hybrid to start exactly when FRED starts
    fred_start = df_fred_t.index.min()
    
    if not df_tv_t.empty:
        df_hybrid_t = df_tv_t.combine_first(df_fred_t)
        df_hybrid_t = df_hybrid_t[df_hybrid_t.index >= fred_start]
    else:
        df_hybrid_t = df_fred_t

    # 4. Final Processing and JSON Save
    def process_and_save_final(df_t, filename):
        # Alignment: Ensure index is strictly daily for charts
        all_dates = pd.date_range(start=df_t.index.min(), end=df_t.index.max(), freq='D')
        df_t = df_t.reindex(all_dates).ffill()

        gli = calculate_gli_from_trillions(df_t)
        us_net_liq = calculate_us_net_liq_from_trillions(df_t)

        # Add GLI_TOTAL and NET_LIQUIDITY to df_t for BTC calculations
        df_t['GLI_TOTAL'] = gli['GLI_TOTAL']
        df_t['NET_LIQUIDITY'] = us_net_liq['NET_LIQUIDITY']

        # Bitcoin Analysis
        btc_analysis = calculate_btc_fair_value(df_t)
        btc_rocs = {}
        if 'BTC' in df_t.columns and df_t['BTC'].notna().sum() > 0:
            btc_rocs = calculate_rocs(df_t['BTC'])

        # Cross-Correlations
        correlations = {}
        if 'BTC' in df_t.columns and df_t['BTC'].notna().sum() > 100:
            btc_clean = df_t['BTC'].dropna()

            # GLI vs BTC
            gli_clean = gli['GLI_TOTAL'].loc[btc_clean.index].dropna()
            if len(gli_clean) > 100:
                correlations['gli_btc'] = calculate_cross_correlation(gli_clean, btc_clean.loc[gli_clean.index], max_lag=90)

            # CLI vs BTC
            cli_clean = df_t['CLI'].loc[btc_clean.index].dropna()
            if len(cli_clean) > 100:
                correlations['cli_btc'] = calculate_cross_correlation(cli_clean, btc_clean.loc[cli_clean.index], max_lag=90)

            # VIX vs BTC
            vix_clean = df_t['VIX'].loc[btc_clean.index].dropna()
            if len(vix_clean) > 100:
                correlations['vix_btc'] = calculate_cross_correlation(vix_clean, btc_clean.loc[vix_clean.index], max_lag=90)

            # Net Liq vs BTC
            netliq_clean = us_net_liq['NET_LIQUIDITY'].loc[btc_clean.index].dropna()
            if len(netliq_clean) > 100:
                correlations['netliq_btc'] = calculate_cross_correlation(netliq_clean, btc_clean.loc[netliq_clean.index], max_lag=90)

        # JSON structure (same as before)
        gli_rocs = calculate_rocs(gli['GLI_TOTAL'])
        net_liq_rocs = calculate_rocs(us_net_liq['NET_LIQUIDITY'])
        
        def clean_for_json(obj):
            if isinstance(obj, pd.Series):
                # Return None (null in JSON) instead of 0 for NaN to avoid spiky chart floors
                return [float(x) if pd.notnull(x) else None for x in obj.tolist()]
            return obj

        # Helper for safer last date extraction
        def get_safe_last_date(series):
            try:
                valid = series.dropna()
                if not valid.empty:
                    return valid.index[-1].strftime('%Y-%m-%d')
            except:
                pass
            return "N/A"

        data_output = {
            'dates': df_t.index.strftime('%Y-%m-%d').tolist(),
            'last_dates': {k: get_safe_last_date(df_t[k]) for k in df_t.columns},
            'gli': {
                'total': clean_for_json(gli['GLI_TOTAL']),
                'fed': clean_for_json(gli['FED_USD']),
                'ecb': clean_for_json(gli['ECB_USD']),
                'boj': clean_for_json(gli['BOJ_USD']),
                'boe': clean_for_json(gli['BOE_USD']),
                'pboc': clean_for_json(gli['PBOC_USD']),
                'rocs': {k: clean_for_json(v) for k, v in gli_rocs.items()}
            },
            'us_net_liq': clean_for_json(us_net_liq['NET_LIQUIDITY']),
            'us_net_liq_rocs': {k: clean_for_json(v) for k, v in net_liq_rocs.items()},
            'bank_rocs': {
                b: {k: clean_for_json(calculate_rocs(gli[f'{b.upper()}_USD'])[k]) for k in ['1M', '3M', '6M', '1Y']}
                for b in ['fed', 'ecb', 'boj', 'boe', 'pboc']
            },
            'cli': clean_for_json(df_t['CLI']),
            'vix': clean_for_json(df_t['VIX']),
            'hy_spread': clean_for_json(df_t['HY_SPREAD']),
            'btc': {
                'price': clean_for_json(btc_analysis.get('BTC_ACTUAL', pd.Series(dtype=float))),
                'fair_value': clean_for_json(btc_analysis.get('BTC_FAIR_VALUE', pd.Series(dtype=float))),
                'upper_1sd': clean_for_json(btc_analysis.get('BTC_UPPER_1SD', pd.Series(dtype=float))),
                'lower_1sd': clean_for_json(btc_analysis.get('BTC_LOWER_1SD', pd.Series(dtype=float))),
                'upper_2sd': clean_for_json(btc_analysis.get('BTC_UPPER_2SD', pd.Series(dtype=float))),
                'lower_2sd': clean_for_json(btc_analysis.get('BTC_LOWER_2SD', pd.Series(dtype=float))),
                'deviation_pct': clean_for_json(btc_analysis.get('BTC_DEVIATION_PCT', pd.Series(dtype=float))),
                'deviation_zscore': clean_for_json(btc_analysis.get('BTC_DEVIATION_ZSCORE', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in btc_rocs.items()} if btc_rocs else {}
            },
            'correlations': correlations
        }

        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'w') as f:
            json.dump(data_output, f)

    process_and_save_final(df_fred_t, 'dashboard_data_fred.json')
    process_and_save_final(df_hybrid_t, 'dashboard_data_tv.json')
    import shutil
    shutil.copyfile(os.path.join(OUTPUT_DIR, 'dashboard_data_tv.json'), os.path.join(OUTPUT_DIR, 'dashboard_data.json'))
    print("Pipeline complete.")

if __name__ == "__main__":
    run_pipeline()
