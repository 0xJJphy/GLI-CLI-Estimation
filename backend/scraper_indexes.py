import os
import pandas as pd
import numpy as np
import json
from datetime import datetime
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

def fetch_historical_data(tv_instance, symbol, exchange, interval=Interval.in_daily, n_bars=3000):
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

# Configuration for Indexes
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

def run_scraper():
    tv = get_tv_instance()
    if not tv:
        print("Error: Could not initialize TradingView instance.")
        return

    data_output = {
        'dates': [],
        'indexes': {}
    }

    # Use SPX as base for dates
    print("Fetching base index (SPX)...")
    base_df = fetch_historical_data(tv, 'SPX', 'TVC', n_bars=1500)
    if base_df is None or base_df.empty:
        print("Error: Could not fetch base index data.")
        return

    # Normalize dates to YYYY-MM-DD
    base_df.index = base_df.index.normalize()
    dates_list = [d.strftime('%Y-%m-%d') for d in base_df.index]
    data_output['dates'] = dates_list

    # Initialize dataframe for all indices aligned to base dates
    all_prices = pd.DataFrame(index=base_df.index)
    all_prices['SPX'] = base_df['close']

    # Fetch other indices
    for symbol, (exchange, name) in INDEXES_CONFIG.items():
        if symbol == 'SPX': continue
        
        print(f"Fetching {symbol} from {exchange}...")
        df = fetch_historical_data(tv, symbol, exchange, n_bars=1500)
        if df is not None and not df.empty:
            df.index = df.index.normalize()
            # Ensure no duplicates before join
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

    # Fetch BTC for overlay
    print("Fetching BTC for overlay...")
    btc_df = fetch_historical_data(tv, 'BTCUSD', 'BITSTAMP', n_bars=1500)
    if btc_df is not None and not btc_df.empty:
        btc_df.index = btc_df.index.normalize()
        btc_aligned = btc_df['close'].reindex(all_prices.index).ffill()
        data_output['btc'] = {
            'absolute': clean_series(btc_aligned),
            'roc_30d': clean_series(calc_roc(btc_aligned, 30))
        }

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'public', 'indexes_data.json')
    with open(output_path, 'w') as f:
        json.dump(data_output, f)
    
    print(f"Successfully saved data to {output_path}")

if __name__ == "__main__":
    run_scraper()
