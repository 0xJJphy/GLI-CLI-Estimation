"""
scraper_indexes.py
Fetches global stock index data from TradingView with caching.
"""
import os
import sys
import pandas as pd
import numpy as np
import json
from datetime import datetime, date

# Add backend to path for utils imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Use shared TV client
from utils.tv_client import fetch_historical_data, get_tv_session, TV_AVAILABLE

# Configuration
N_BARS = 7500  # ~30 years of daily data
CACHE_MAX_AGE_HOURS = 12
# Path: backend/scrapers -> backend -> project_root -> frontend/public
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'indexes_data.json')

# Index symbols and exchanges
INDEXES_CONFIG = {
    'SPX': ('TVC', 'S&P 500'),
    'NDX': ('TVC', 'Nasdaq 100'),
    'DJI': ('TVC', 'Dow Jones'),
    'RUT': ('TVC', 'Russell 2000'),
    'NIFTY': ('NSE', 'Nifty 50'),
    'DAX': ('XETR', 'DAX 40'),
    'NI225': ('OSE', 'Nikkei 225'),
    'HSI': ('HSI', 'Hang Seng'),
    'BUZZ': ('AMEX', 'VanEck Social Sentiment ETF'),
}

def calc_roc(series, period):
    return ((series / series.shift(period)) - 1) * 100

def clean_series(series):
    return [float(x) if pd.notnull(x) and np.isfinite(x) else None for x in series.tolist()]

def is_cache_valid():
    """Check if cached data is recent enough to skip refresh."""
    if not os.path.exists(OUTPUT_PATH):
        print("No cached data found - will fetch fresh data")
        return False
    
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(OUTPUT_PATH))
        age_hours = (datetime.now() - file_mtime).total_seconds() / 3600
        
        if age_hours > CACHE_MAX_AGE_HOURS:
            print(f"Cache is {age_hours:.1f}h old (max: {CACHE_MAX_AGE_HOURS}h) - will refresh")
            return False
        
        with open(OUTPUT_PATH, 'r') as f:
            cached = json.load(f)
        
        if not cached.get('dates'):
            return False
        
        last_cached_date = cached['dates'][-1]
        today = date.today()
        
        # Adjust for weekends
        if today.weekday() == 0:  # Monday
            expected_date = today.replace(day=today.day - 3)
        elif today.weekday() in [5, 6]:  # Sat/Sun
            expected_date = today.replace(day=today.day - (today.weekday() - 4))
        else:
            expected_date = today.replace(day=today.day - 1)
        
        last_cached = datetime.strptime(last_cached_date, '%Y-%m-%d').date()
        
        if last_cached >= expected_date:
            print(f"[OK] Cache is up-to-date (last date: {last_cached_date})")
            return True
        
        print(f"Cache stale (last: {last_cached_date}) - will refresh")
        return False
        
    except Exception as e:
        print(f"Error checking cache: {e}")
        return False

def run_scraper(force_refresh=False):
    """Run the index scraper."""
    
    if not force_refresh and is_cache_valid():
        print("Using cached data - run with --force to refresh")
        return
    
    if not TV_AVAILABLE:
        print("Error: TvDatafeed not available")
        return
    
    # Initialize session once (singleton)
    tv = get_tv_session()
    if not tv:
        print("Error: Could not initialize TradingView session")
        return

    data_output = {
        'dates': [],
        'indexes': {},
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Use SPX as base for dates
    print(f"Fetching SPX with {N_BARS} bars...")
    base_df = fetch_historical_data('SPX', 'TVC', n_bars=N_BARS)
    if base_df is None or base_df.empty:
        print("Error: Could not fetch base index data")
        return

    base_df.index = base_df.index.normalize()
    data_output['dates'] = [d.strftime('%Y-%m-%d') for d in base_df.index]

    all_prices = pd.DataFrame(index=base_df.index)
    all_prices['SPX'] = base_df['close']

    # Fetch other indices (reusing same session)
    for symbol, (exchange, name) in INDEXES_CONFIG.items():
        if symbol == 'SPX':
            continue
        
        print(f"Fetching {symbol} from {exchange}...")
        df = fetch_historical_data(symbol, exchange, n_bars=N_BARS)
        if df is not None and not df.empty:
            df.index = df.index.normalize()
            df = df[~df.index.duplicated(keep='last')]
            all_prices[symbol] = df['close']
        else:
            print(f"Warning: Could not fetch {symbol}")

    # Process each index
    for symbol in all_prices.columns:
        print(f"Processing {symbol}...")
        prices = all_prices[symbol].ffill()
        
        data_output['indexes'][symbol] = {
            'absolute': clean_series(prices),
            'roc_7d': clean_series(calc_roc(prices, 7)),
            'roc_30d': clean_series(calc_roc(prices, 30)),
            'roc_90d': clean_series(calc_roc(prices, 90)),
            'roc_180d': clean_series(calc_roc(prices, 180)),
            'roc_yoy': clean_series(calc_roc(prices, 252)),
        }

    # Fetch BTC overlay
    print("Fetching BTC overlay...")
    btc_df = fetch_historical_data('BTCUSD', 'BITSTAMP', n_bars=N_BARS)
    if btc_df is not None and not btc_df.empty:
        btc_df.index = btc_df.index.normalize()
        btc_aligned = btc_df['close'].reindex(all_prices.index).ffill()
        data_output['btc'] = {
            'absolute': clean_series(btc_aligned),
            'roc_30d': clean_series(calc_roc(btc_aligned, 30))
        }

    # Save
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data_output, f)
    
    print(f"[OK] Saved {len(data_output['dates'])} days to {OUTPUT_PATH}")

if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    run_scraper(force_refresh=force)
