"""
Treasury Auction Demand Module
==============================
Fetches auction results from TreasuryDirect API including:
- Bid-to-Cover Ratio (BTC)
- Direct Bidder % (domestic demand)
- Indirect Bidder % (foreign demand - proxy for central banks)
- Tail (High Yield - When Issued Yield)
- Auction demand scoring and signal generation

Data Source: TreasuryDirect.gov API
Endpoint: https://www.treasurydirect.gov/TA_WS/securities/

Author: Quantitative Analysis Assistant
Date: January 2026
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
from typing import Dict, List, Any, Optional, Tuple

# ==============================================================================
# CONFIGURATION
# ==============================================================================

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

TREASURY_DIRECT_BASE_URL = "https://www.treasurydirect.gov/TA_WS"

# Security types to fetch
SECURITY_TYPES = ['Bill', 'Note', 'Bond', 'TIPS', 'FRN', 'CMB']

# Cache configuration
CACHE_FILE = os.path.join(OUTPUT_DIR, 'treasury_auction_demand_cache.json')
CACHE_HOURS = 6  # Refresh every 6 hours (auctions happen during business hours)

# Historical lookback for analysis
LOOKBACK_YEARS = 2

# Bid-to-Cover thresholds by security type (historical averages)
BTC_THRESHOLDS = {
    'Bill': {'weak': 2.4, 'strong': 2.8, 'avg': 2.6},
    'Note': {'weak': 2.3, 'strong': 2.7, 'avg': 2.5},
    'Bond': {'weak': 2.2, 'strong': 2.6, 'avg': 2.4},
    'TIPS': {'weak': 2.3, 'strong': 2.7, 'avg': 2.5},
    'FRN':  {'weak': 2.5, 'strong': 3.0, 'avg': 2.75},
    'CMB':  {'weak': 2.8, 'strong': 3.3, 'avg': 3.0},
}

# Indirect bidder thresholds (foreign demand - higher = more foreign demand)
INDIRECT_THRESHOLDS = {
    'Bill': {'weak': 55, 'strong': 70, 'avg': 62},
    'Note': {'weak': 60, 'strong': 75, 'avg': 67},
    'Bond': {'weak': 60, 'strong': 75, 'avg': 67},
    'TIPS': {'weak': 55, 'strong': 70, 'avg': 62},
    'FRN':  {'weak': 45, 'strong': 60, 'avg': 52},
    'CMB':  {'weak': 50, 'strong': 65, 'avg': 57},
}


# ==============================================================================
# CACHE MANAGEMENT
# ==============================================================================

def is_cache_fresh() -> bool:
    """Check if cache exists and is fresh."""
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        hours_elapsed = (datetime.now() - file_mtime).total_seconds() / 3600
        return hours_elapsed < CACHE_HOURS
    except Exception:
        return False


def load_cache() -> Optional[Dict]:
    """Load cached data."""
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data: Dict) -> None:
    """Save data to cache."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save auction demand cache: {e}")


# ==============================================================================
# API FETCHING FUNCTIONS
# ==============================================================================

def fetch_auctioned_securities(security_type: str, max_results: int = 250) -> List[Dict]:
    """
    Fetch auctioned securities of a specific type from TreasuryDirect API.
    
    Parameters:
    -----------
    security_type : str
        One of: Bill, Note, Bond, TIPS, FRN, CMB
    max_results : int
        Maximum number of results (API max is 250 per request)
    
    Returns:
    --------
    List[Dict] : List of auction records
    """
    url = f"{TREASURY_DIRECT_BASE_URL}/securities/auctioned"
    params = {
        'format': 'json',
        'type': security_type,
        'pagesize': min(max_results, 250)
    }
    
    headers = {
        'User-Agent': 'GLI-CLI-Dashboard/1.0 (Treasury Auction Analysis)',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, list):
            return data
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"  [TreasuryDirect] Error fetching {security_type}: {e}")
        return []


def fetch_all_auction_data(lookback_days: int = 730, silent: bool = False) -> pd.DataFrame:
    """
    Fetch auction data for all security types.
    
    Parameters:
    -----------
    lookback_days : int
        Number of days to look back (default 2 years)
    silent : bool
        Suppress progress output
    
    Returns:
    --------
    pd.DataFrame : Combined auction data with parsed fields
    """
    all_auctions = []
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    for sec_type in SECURITY_TYPES:
        if not silent:
            print(f"  [TreasuryDirect] Fetching {sec_type} auctions...")
        
        auctions = fetch_auctioned_securities(sec_type)
        
        for auction in auctions:
            try:
                # Parse auction date
                auction_date_str = auction.get('auctionDate', '')
                if not auction_date_str:
                    continue
                    
                auction_date = datetime.strptime(auction_date_str[:10], '%Y-%m-%d')
                
                # Skip if before cutoff
                if auction_date < cutoff_date:
                    continue
                
                # Extract key metrics
                record = {
                    'auction_date': auction_date,
                    'issue_date': auction.get('issueDate', '')[:10] if auction.get('issueDate') else None,
                    'maturity_date': auction.get('maturityDate', '')[:10] if auction.get('maturityDate') else None,
                    'security_type': auction.get('securityType', sec_type),
                    'security_term': auction.get('securityTerm', ''),
                    'cusip': auction.get('cusip', ''),
                    
                    # Bid-to-Cover Ratio (KEY METRIC)
                    'bid_to_cover': _safe_float(auction.get('bidToCoverRatio')),
                    
                    # Bidder breakdown
                    'competitive_accepted': _safe_float(auction.get('competitiveAccepted')),
                    'competitive_tendered': _safe_float(auction.get('competitiveTendered')),
                    'noncompetitive_accepted': _safe_float(auction.get('noncompetitiveAccepted')),
                    
                    # Direct bidders (domestic - hedge funds, mutual funds, etc.)
                    'direct_bidder_accepted': _safe_float(auction.get('directBidderAccepted')),
                    'direct_bidder_tendered': _safe_float(auction.get('directBidderTendered')),
                    
                    # Indirect bidders (foreign - central banks, sovereign wealth funds)
                    'indirect_bidder_accepted': _safe_float(auction.get('indirectBidderAccepted')),
                    'indirect_bidder_tendered': _safe_float(auction.get('indirectBidderTendered')),
                    
                    # Primary dealers (what's left after direct + indirect)
                    'primary_dealer_accepted': _safe_float(auction.get('primaryDealerAccepted')),
                    'primary_dealer_tendered': _safe_float(auction.get('primaryDealerTendered')),
                    
                    # Pricing
                    'high_yield': _safe_float(auction.get('highInvestmentRate')) or _safe_float(auction.get('highYield')),
                    'high_discount_rate': _safe_float(auction.get('highDiscountRate')),
                    'avg_median_yield': _safe_float(auction.get('averageMedianYield')),
                    'low_yield': _safe_float(auction.get('lowInvestmentRate')) or _safe_float(auction.get('lowYield')),
                    
                    # Amounts
                    'offering_amount': _safe_float(auction.get('offeringAmount')) or _safe_float(auction.get('totalAccepted')),
                    'total_accepted': _safe_float(auction.get('totalAccepted')),
                    'total_tendered': _safe_float(auction.get('totalTendered')),
                    
                    # Allocation
                    'allocation_pct': _safe_float(auction.get('allocationPercentage')),
                }
                
                all_auctions.append(record)
                
            except Exception as e:
                continue
        
        # Rate limiting
        time.sleep(0.2)
    
    if not all_auctions:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_auctions)
    df = df.sort_values('auction_date', ascending=False).reset_index(drop=True)
    
    # Calculate derived metrics
    df = _calculate_derived_metrics(df)
    
    if not silent:
        print(f"  [TreasuryDirect] Fetched {len(df)} auction records")
    
    return df


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    if value is None or value == '' or value == 'null':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate derived metrics from raw auction data."""
    
    # Bidder percentages
    total_accepted = df['total_accepted'].fillna(0)
    
    # Indirect Bidder % (foreign demand - KEY METRIC)
    df['indirect_pct'] = np.where(
        total_accepted > 0,
        (df['indirect_bidder_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    # Direct Bidder % (domestic non-dealer demand)
    df['direct_pct'] = np.where(
        total_accepted > 0,
        (df['direct_bidder_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    # Primary Dealer % (dealers - forced buyers)
    df['dealer_pct'] = np.where(
        total_accepted > 0,
        (df['primary_dealer_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    # Amount in billions
    df['amount_billions'] = df['offering_amount'].fillna(0) / 1e9
    
    # Term in weeks (for categorization)
    df['term_weeks'] = df['security_term'].apply(_parse_term_to_weeks)
    
    # Categorize by maturity bucket
    df['maturity_bucket'] = df.apply(_categorize_maturity, axis=1)
    
    return df


def _parse_term_to_weeks(term_str: str) -> Optional[int]:
    """Parse security term string to weeks."""
    if not term_str:
        return None
    
    term_str = str(term_str).lower()
    
    # Week patterns
    if 'week' in term_str:
        try:
            return int(term_str.split('-')[0].strip())
        except:
            pass
    
    # Day patterns
    if 'day' in term_str:
        try:
            days = int(term_str.split('-')[0].strip())
            return max(1, days // 7)
        except:
            pass
    
    # Month patterns
    if 'month' in term_str:
        try:
            months = int(term_str.split('-')[0].strip())
            return months * 4
        except:
            pass
    
    # Year patterns
    if 'year' in term_str:
        try:
            years = int(term_str.split('-')[0].strip())
            return years * 52
        except:
            pass
    
    return None


def _categorize_maturity(row) -> str:
    """Categorize auction by maturity bucket."""
    sec_type = row.get('security_type', '')
    term_weeks = row.get('term_weeks')
    
    if sec_type == 'Bill':
        return 'Short-Term (Bills)'
    elif sec_type in ['Note', 'FRN']:
        if term_weeks and term_weeks <= 104:  # 2 years
            return 'Short Coupon (2Y)'
        elif term_weeks and term_weeks <= 260:  # 5 years
            return 'Belly (3-5Y)'
        else:
            return 'Intermediate (7-10Y)'
    elif sec_type == 'Bond':
        return 'Long-Term (20-30Y)'
    elif sec_type == 'TIPS':
        return 'TIPS (Inflation)'
    elif sec_type == 'CMB':
        return 'Cash Management Bills'
    
    return 'Other'


# ==============================================================================
# ANALYSIS FUNCTIONS
# ==============================================================================

def calculate_auction_demand_score(df: pd.DataFrame, lookback_auctions: int = 10) -> Dict:
    """
    Calculate aggregate auction demand score based on recent auctions.
    
    Score ranges from -100 (very weak demand) to +100 (very strong demand).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Auction data from fetch_all_auction_data()
    lookback_auctions : int
        Number of recent auctions to consider per security type
    
    Returns:
    --------
    Dict : Demand metrics and scores
    """
    if df.empty:
        return _empty_demand_result()
    
    results = {
        'overall_score': 0,
        'signal': 'NEUTRAL',
        'by_type': {},
        'recent_auctions': [],
        'metrics': {},
        'timestamp': datetime.now().isoformat()
    }
    
    scores = []
    
    for sec_type in SECURITY_TYPES:
        type_df = df[df['security_type'] == sec_type].head(lookback_auctions)
        
        if type_df.empty:
            continue
        
        type_score = _calculate_type_score(type_df, sec_type)
        
        results['by_type'][sec_type] = type_score
        
        # Weight by importance (Bills and Notes matter most for refinancing)
        weight = {'Bill': 0.30, 'Note': 0.35, 'Bond': 0.15, 'TIPS': 0.10, 'FRN': 0.05, 'CMB': 0.05}.get(sec_type, 0.1)
        scores.append(type_score['score'] * weight)
    
    if scores:
        results['overall_score'] = round(sum(scores) / sum([0.30, 0.35, 0.15, 0.10, 0.05, 0.05][:len(scores)]), 1)
    
    # Determine signal
    if results['overall_score'] >= 30:
        results['signal'] = 'STRONG_DEMAND'
        results['signal_color'] = 'green'
    elif results['overall_score'] >= 10:
        results['signal'] = 'SOLID_DEMAND'
        results['signal_color'] = 'lightgreen'
    elif results['overall_score'] <= -30:
        results['signal'] = 'WEAK_DEMAND'
        results['signal_color'] = 'red'
    elif results['overall_score'] <= -10:
        results['signal'] = 'SOFT_DEMAND'
        results['signal_color'] = 'orange'
    else:
        results['signal'] = 'NEUTRAL'
        results['signal_color'] = 'gray'
    
    # Add recent notable auctions
    results['recent_auctions'] = _get_recent_notable_auctions(df, n=10)
    
    # Aggregate metrics
    results['metrics'] = {
        'avg_btc_all': round(df['bid_to_cover'].dropna().mean(), 2) if not df['bid_to_cover'].dropna().empty else None,
        'avg_indirect_all': round(df['indirect_pct'].dropna().mean(), 1) if not df['indirect_pct'].dropna().empty else None,
        'avg_direct_all': round(df['direct_pct'].dropna().mean(), 1) if not df['direct_pct'].dropna().empty else None,
        'avg_dealer_all': round(df['dealer_pct'].dropna().mean(), 1) if not df['dealer_pct'].dropna().empty else None,
        'total_auctions': len(df),
        'date_range': {
            'start': df['auction_date'].min().strftime('%Y-%m-%d') if not df.empty else None,
            'end': df['auction_date'].max().strftime('%Y-%m-%d') if not df.empty else None
        }
    }
    
    return results


def _calculate_type_score(df: pd.DataFrame, sec_type: str) -> Dict:
    """Calculate demand score for a specific security type."""
    btc_thresh = BTC_THRESHOLDS.get(sec_type, BTC_THRESHOLDS['Note'])
    indirect_thresh = INDIRECT_THRESHOLDS.get(sec_type, INDIRECT_THRESHOLDS['Note'])
    
    # Get averages
    avg_btc = df['bid_to_cover'].dropna().mean() if not df['bid_to_cover'].dropna().empty else None
    avg_indirect = df['indirect_pct'].dropna().mean() if not df['indirect_pct'].dropna().empty else None
    avg_direct = df['direct_pct'].dropna().mean() if not df['direct_pct'].dropna().empty else None
    
    # Calculate component scores (-50 to +50 each)
    btc_score = 0
    if avg_btc is not None:
        if avg_btc >= btc_thresh['strong']:
            btc_score = 50
        elif avg_btc >= btc_thresh['avg']:
            btc_score = 25 * (avg_btc - btc_thresh['avg']) / (btc_thresh['strong'] - btc_thresh['avg'])
        elif avg_btc >= btc_thresh['weak']:
            btc_score = -25 * (btc_thresh['avg'] - avg_btc) / (btc_thresh['avg'] - btc_thresh['weak'])
        else:
            btc_score = -50
    
    indirect_score = 0
    if avg_indirect is not None:
        if avg_indirect >= indirect_thresh['strong']:
            indirect_score = 50
        elif avg_indirect >= indirect_thresh['avg']:
            indirect_score = 25 * (avg_indirect - indirect_thresh['avg']) / (indirect_thresh['strong'] - indirect_thresh['avg'])
        elif avg_indirect >= indirect_thresh['weak']:
            indirect_score = -25 * (indirect_thresh['avg'] - avg_indirect) / (indirect_thresh['avg'] - indirect_thresh['weak'])
        else:
            indirect_score = -50
    
    # Combined score (BTC weighted 60%, Indirect 40%)
    combined_score = (btc_score * 0.6) + (indirect_score * 0.4)
    
    return {
        'score': round(combined_score, 1),
        'avg_btc': round(avg_btc, 2) if avg_btc else None,
        'avg_indirect_pct': round(avg_indirect, 1) if avg_indirect else None,
        'avg_direct_pct': round(avg_direct, 1) if avg_direct else None,
        'btc_score': round(btc_score, 1),
        'indirect_score': round(indirect_score, 1),
        'auction_count': len(df),
        'thresholds': {
            'btc': btc_thresh,
            'indirect': indirect_thresh
        }
    }


def _get_recent_notable_auctions(df: pd.DataFrame, n: int = 10) -> List[Dict]:
    """Get recent notable auctions with demand indicators."""
    recent = df.head(n * 2)  # Get more to filter
    
    notable = []
    for _, row in recent.iterrows():
        if pd.isna(row.get('bid_to_cover')):
            continue
        
        sec_type = row.get('security_type', 'Note')
        btc_thresh = BTC_THRESHOLDS.get(sec_type, BTC_THRESHOLDS['Note'])
        
        btc = row['bid_to_cover']
        indirect = row.get('indirect_pct')
        
        # Determine if notable
        if btc >= btc_thresh['strong']:
            demand_level = 'STRONG'
            color = 'green'
        elif btc <= btc_thresh['weak']:
            demand_level = 'WEAK'
            color = 'red'
        else:
            demand_level = 'NORMAL'
            color = 'gray'
        
        notable.append({
            'date': row['auction_date'].strftime('%Y-%m-%d'),
            'security': f"{row.get('security_term', '')} {sec_type}",
            'cusip': row.get('cusip', ''),
            'bid_to_cover': round(btc, 2),
            'indirect_pct': round(indirect, 1) if indirect else None,
            'direct_pct': round(row.get('direct_pct', 0), 1) if row.get('direct_pct') else None,
            'amount_billions': round(row.get('amount_billions', 0), 1),
            'demand_level': demand_level,
            'color': color
        })
        
        if len(notable) >= n:
            break
    
    return notable


def _empty_demand_result() -> Dict:
    """Return empty demand result structure."""
    return {
        'overall_score': 0,
        'signal': 'NO_DATA',
        'signal_color': 'gray',
        'by_type': {},
        'recent_auctions': [],
        'metrics': {},
        'timestamp': datetime.now().isoformat()
    }


# ==============================================================================
# TIME SERIES GENERATION
# ==============================================================================

def generate_btc_time_series(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Generate time series of bid-to-cover ratios by security type.
    
    Returns daily series with forward-fill for non-auction days.
    """
    if df.empty:
        return {}
    
    series = {}
    
    # Overall BTC (weighted average by amount)
    df_valid = df[df['bid_to_cover'].notna() & df['amount_billions'].notna()].copy()
    
    if not df_valid.empty:
        # Group by date and calculate weighted average
        daily = df_valid.groupby(df_valid['auction_date'].dt.date).apply(
            lambda x: np.average(x['bid_to_cover'], weights=x['amount_billions']) if len(x) > 0 else np.nan
        )
        series['BTC_ALL'] = pd.Series(daily, index=pd.to_datetime(daily.index))
    
    # By security type
    for sec_type in ['Bill', 'Note', 'Bond']:
        type_df = df_valid[df_valid['security_type'] == sec_type]
        if not type_df.empty:
            daily = type_df.groupby(type_df['auction_date'].dt.date)['bid_to_cover'].mean()
            series[f'BTC_{sec_type.upper()}'] = pd.Series(daily, index=pd.to_datetime(daily.index))
    
    # Indirect bidder % (foreign demand)
    df_indirect = df[df['indirect_pct'].notna()].copy()
    if not df_indirect.empty:
        daily = df_indirect.groupby(df_indirect['auction_date'].dt.date)['indirect_pct'].mean()
        series['INDIRECT_PCT'] = pd.Series(daily, index=pd.to_datetime(daily.index))
    
    return series


def generate_rolling_demand_metrics(df: pd.DataFrame, window_auctions: int = 10) -> Dict[str, pd.Series]:
    """
    Generate rolling demand metrics for trend analysis.
    """
    if df.empty:
        return {}
    
    metrics = {}
    
    df_sorted = df.sort_values('auction_date').copy()
    
    # Rolling BTC average
    if 'bid_to_cover' in df_sorted.columns:
        rolling_btc = df_sorted['bid_to_cover'].rolling(window=window_auctions, min_periods=3).mean()
        metrics['BTC_ROLLING'] = pd.Series(
            rolling_btc.values, 
            index=pd.to_datetime(df_sorted['auction_date'])
        )
    
    # Rolling indirect %
    if 'indirect_pct' in df_sorted.columns:
        rolling_indirect = df_sorted['indirect_pct'].rolling(window=window_auctions, min_periods=3).mean()
        metrics['INDIRECT_ROLLING'] = pd.Series(
            rolling_indirect.values,
            index=pd.to_datetime(df_sorted['auction_date'])
        )
    
    # Z-score of recent BTC vs historical
    if 'bid_to_cover' in df_sorted.columns:
        btc_zscore = (
            df_sorted['bid_to_cover'] - df_sorted['bid_to_cover'].rolling(50, min_periods=20).mean()
        ) / df_sorted['bid_to_cover'].rolling(50, min_periods=20).std()
        metrics['BTC_ZSCORE'] = pd.Series(
            btc_zscore.values,
            index=pd.to_datetime(df_sorted['auction_date'])
        )
    
    return metrics


# ==============================================================================
# MAIN FETCH FUNCTION (with caching)
# ==============================================================================

def fetch_treasury_auction_demand(silent: bool = False) -> Dict:
    """
    Main function to fetch and analyze Treasury auction demand.
    
    Uses caching to avoid excessive API calls.
    
    Returns:
    --------
    Dict : Complete auction demand analysis including:
        - demand_score: Overall demand score and signal
        - time_series: Historical BTC and indirect % series
        - rolling_metrics: Rolling averages for trend analysis
        - raw_auctions: Recent auction details for display
    """
    # Check cache first
    if is_cache_fresh():
        cached = load_cache()
        if cached:
            if not silent:
                print("  [TreasuryDirect] Using cached auction demand data")
            return cached
    
    if not silent:
        print("  [TreasuryDirect] Fetching fresh auction demand data...")
    
    # Fetch raw data
    df = fetch_all_auction_data(lookback_days=LOOKBACK_YEARS * 365, silent=silent)
    
    if df.empty:
        if not silent:
            print("  [TreasuryDirect] No auction data available, trying cache fallback")
        cached = load_cache()
        if cached:
            return cached
        return _empty_demand_result()
    
    # Calculate demand score
    demand_score = calculate_auction_demand_score(df)
    
    # Generate time series
    time_series = generate_btc_time_series(df)
    
    # Generate rolling metrics
    rolling_metrics = generate_rolling_demand_metrics(df)
    
    # Format for JSON
    def series_to_json(s: pd.Series) -> Dict:
        if s is None or s.empty:
            return {}
        return {
            d.strftime('%Y-%m-%d'): round(v, 4) if not pd.isna(v) else None
            for d, v in s.items()
        }
    
    result = {
        'demand_score': demand_score,
        'time_series': {k: series_to_json(v) for k, v in time_series.items()},
        'rolling_metrics': {k: series_to_json(v) for k, v in rolling_metrics.items()},
        'raw_auctions': df.head(50).to_dict('records') if not df.empty else [],
        'last_updated': datetime.now().isoformat()
    }
    
    # Convert datetime objects in raw_auctions
    for auction in result['raw_auctions']:
        for key, value in auction.items():
            if isinstance(value, (datetime, pd.Timestamp)):
                auction[key] = value.strftime('%Y-%m-%d')
    
    # Save to cache
    save_cache(result)
    
    if not silent:
        print(f"  [TreasuryDirect] Auction demand score: {demand_score['overall_score']} ({demand_score['signal']})")
    
    return result


# ==============================================================================
# INTEGRATION HELPER FOR DATA_PIPELINE.PY
# ==============================================================================

def get_auction_demand_for_pipeline() -> Dict:
    """
    Simplified function for integration with data_pipeline.py.
    
    Returns format ready for dashboard_data.json.
    """
    try:
        result = fetch_treasury_auction_demand(silent=True)
        
        return {
            'score': result.get('demand_score', {}).get('overall_score', 0),
            'signal': result.get('demand_score', {}).get('signal', 'NO_DATA'),
            'signal_color': result.get('demand_score', {}).get('signal_color', 'gray'),
            'by_type': result.get('demand_score', {}).get('by_type', {}),
            'recent_auctions': result.get('demand_score', {}).get('recent_auctions', []),
            'metrics': result.get('demand_score', {}).get('metrics', {}),
            'time_series': result.get('time_series', {}),
            'rolling': result.get('rolling_metrics', {}),
            'last_updated': result.get('last_updated')
        }
    except Exception as e:
        print(f"  [TreasuryDirect] Error in auction demand pipeline: {e}")
        return {
            'score': 0,
            'signal': 'ERROR',
            'signal_color': 'gray',
            'by_type': {},
            'recent_auctions': [],
            'metrics': {},
            'time_series': {},
            'rolling': {},
            'last_updated': datetime.now().isoformat()
        }


# ==============================================================================
# MAIN (for testing)
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TREASURY AUCTION DEMAND MODULE")
    print("=" * 70)
    
    print("\nFetching auction data from TreasuryDirect API...")
    
    result = fetch_treasury_auction_demand(silent=False)
    
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    demand = result.get('demand_score', {})
    print(f"\nOverall Demand Score: {demand.get('overall_score', 'N/A')}")
    print(f"Signal: {demand.get('signal', 'N/A')}")
    
    print("\nBy Security Type:")
    for sec_type, data in demand.get('by_type', {}).items():
        print(f"  {sec_type}:")
        print(f"    Score: {data.get('score', 'N/A')}")
        print(f"    Avg BTC: {data.get('avg_btc', 'N/A')}")
        print(f"    Avg Indirect %: {data.get('avg_indirect_pct', 'N/A')}%")
    
    print("\nRecent Notable Auctions:")
    for auction in demand.get('recent_auctions', [])[:5]:
        print(f"  {auction['date']}: {auction['security']} - BTC: {auction['bid_to_cover']} ({auction['demand_level']})")
    
    print("\nTime Series Available:")
    for key in result.get('time_series', {}).keys():
        print(f"  - {key}")
    
    print("\n✅ Module ready for integration with data_pipeline.py")
