import os
import pandas as pd
import numpy as np
import json
from datetime import datetime, date
from dotenv import load_dotenv
import time

# tvDatafeed import
try:
    from tvDatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    print("WARNING: tvDatafeed not found. Please install it using: pip install git+https://github.com/rongardF/tvdatafeed.git")
    TV_AVAILABLE = False

load_dotenv()

TV_USERNAME = os.environ.get('TV_USERNAME')
TV_PASSWORD = os.environ.get('TV_PASSWORD')

# 30 years of daily data = ~7500 bars
N_BARS = 7500
CACHE_MAX_AGE_HOURS = 12

# Output path
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'commodities_data.json')

def get_tv_instance():
    if not TV_AVAILABLE:
        return None
    try:
        if TV_USERNAME and TV_PASSWORD:
            return TvDatafeed(TV_USERNAME, TV_PASSWORD)
        else:
            return TvDatafeed()
    except Exception as e:
        print(f"TV Login failed: {e}")
        return None

def fetch_historical_data(tv_instance, symbol, exchange, interval=Interval.in_daily, n_bars=N_BARS):
    """Fetch historical data with retries."""
    for attempt in range(3):
        try:
            data = tv_instance.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
            if data is not None and not data.empty:
                return data
            print(f"No data for {symbol} on attempt {attempt+1}")
        except Exception as e:
            print(f"Error fetching {symbol} [attempt {attempt+1}]: {e}")
        time.sleep(2)
    return None

# Configuration for Commodities
COMMODITIES_CONFIG = {
    'GOLD': ('TVC', 'Gold'),
    'SILVER': ('TVC', 'Silver'),
    'USOIL': ('TVC', 'Crude Oil (WTI)'),
    'HG1!': ('COMEX', 'Copper'),
    'PLATINUM': ('TVC', 'Platinum'),
    'UX1!': ('NYMEX', 'Uranium'),
    'PALLADIUM': ('TVC', 'Palladium'),
    'GASOLINE': ('TVC', 'Gasoline'),
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
            print("Cache has no dates - will refresh")
            return False
        
        last_cached_date = cached['dates'][-1]
        today = date.today()
        
        if today.weekday() == 0:
            expected_date = today.replace(day=today.day - 3)
        elif today.weekday() == 6:
            expected_date = today.replace(day=today.day - 2)
        elif today.weekday() == 5:
            expected_date = today.replace(day=today.day - 1)
        else:
            expected_date = today.replace(day=today.day - 1)
        
        last_cached = datetime.strptime(last_cached_date, '%Y-%m-%d').date()
        
        if last_cached >= expected_date:
            print(f"✓ Cache is up-to-date (last date: {last_cached_date})")
            return True
        
        print(f"Cache is stale (last: {last_cached_date}, expected: {expected_date}) - will refresh")
        return False
        
    except Exception as e:
        print(f"Error checking cache: {e} - will refresh")
        return False

def run_scraper(force_refresh=False):
    """Run the commodity scraper. Will skip if cache is valid unless force_refresh=True."""
    
    if not force_refresh and is_cache_valid():
        print("Using cached data - run with --force to refresh")
        return
    
    tv = get_tv_instance()
    if not tv:
        print("Error: Could not initialize TradingView instance.")
        return

    data_output = {
        'dates': [],
        'commodities': {},
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Use GOLD as base for dates
    print(f"Fetching base commodity (GOLD) with {N_BARS} bars (~30 years)...")
    base_df = fetch_historical_data(tv, 'GOLD', 'TVC', n_bars=N_BARS)
    if base_df is None or base_df.empty:
        print("Error: Could not fetch base commodity data.")
        return

    # Normalize dates
    base_df.index = base_df.index.normalize()
    dates_list = [d.strftime('%Y-%m-%d') for d in base_df.index]
    data_output['dates'] = dates_list

    # Initialize dataframe
    all_prices = pd.DataFrame(index=base_df.index)
    all_prices['GOLD'] = base_df['close']

    # Fetch other commodities
    for symbol, (exchange, name) in COMMODITIES_CONFIG.items():
        if symbol == 'GOLD': continue
        
        print(f"Fetching {symbol} from {exchange}...")
        df = fetch_historical_data(tv, symbol, exchange, n_bars=N_BARS)
        if df is not None and not df.empty:
            df.index = df.index.normalize()
            df = df[~df.index.duplicated(keep='last')]
            all_prices[symbol] = df['close']
        else:
            print(f"Warning: Could not fetch {symbol}")

    # Process each commodity
    for symbol in all_prices.columns:
        print(f"Processing {symbol}...")
        prices = all_prices[symbol].ffill()
        
        data_output['commodities'][symbol] = {
            'absolute': clean_series(prices),
            'roc_7d': clean_series(calc_roc(prices, 7)),
            'roc_30d': clean_series(calc_roc(prices, 30)),
            'roc_90d': clean_series(calc_roc(prices, 90)),
            'roc_180d': clean_series(calc_roc(prices, 180)),
            'roc_yoy': clean_series(calc_roc(prices, 252)),
        }

    # Fetch BTC for overlay
    print("Fetching BTC for overlay...")
    btc_df = fetch_historical_data(tv, 'BTCUSD', 'BITSTAMP', n_bars=N_BARS)
    if btc_df is not None and not btc_df.empty:
        btc_df.index = btc_df.index.normalize()
        btc_aligned = btc_df['close'].reindex(all_prices.index).ffill()
        data_output['btc'] = {
            'absolute': clean_series(btc_aligned),
            'roc_30d': clean_series(calc_roc(btc_aligned, 30))
        }

    # Save to JSON
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data_output, f)
    
    print(f"✓ Successfully saved {len(dates_list)} days of data to {OUTPUT_PATH}")

if __name__ == "__main__":
    import sys
    force = '--force' in sys.argv or '-f' in sys.argv
    run_scraper(force_refresh=force)
