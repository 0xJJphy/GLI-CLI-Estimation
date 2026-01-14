"""
tv_client.py
Shared TradingView session manager with singleton pattern.
Provides lazy initialization and connection caching.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# TvDatafeed import
try:
    from tvDatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    print("WARNING: tvDatafeed not found. Install: pip install git+https://github.com/rongardF/tvdatafeed.git")
    TvDatafeed = None
    Interval = None
    TV_AVAILABLE = False

# Singleton instance
_tv_instance = None
_is_logged_in = False

def get_tv_session(force_new=False):
    """
    Get or create a TradingView session (singleton pattern).
    
    Args:
        force_new: If True, create a new session even if one exists.
    
    Returns:
        TvDatafeed instance or None if not available.
    """
    global _tv_instance, _is_logged_in
    
    if not TV_AVAILABLE:
        print("TvDatafeed not available")
        return None
    
    if _tv_instance is not None and not force_new:
        return _tv_instance
    
    username = os.environ.get('TV_USERNAME')
    password = os.environ.get('TV_PASSWORD')
    
    try:
        if username and password:
            print(f"Logging into TradingView as {username}...")
            _tv_instance = TvDatafeed(username, password)
            _is_logged_in = True
        else:
            print("Using TradingView without login (limited access)")
            _tv_instance = TvDatafeed()
            _is_logged_in = False
        return _tv_instance
    except Exception as e:
        print(f"TradingView login failed: {e}")
        # Try without login as fallback
        try:
            _tv_instance = TvDatafeed()
            _is_logged_in = False
            return _tv_instance
        except Exception as e2:
            print(f"TradingView fallback also failed: {e2}")
            return None

def is_session_active():
    """Check if there's an active TV session."""
    return _tv_instance is not None

def is_logged_in():
    """Check if the session is authenticated."""
    return _is_logged_in

def close_session():
    """Close the TV session (for cleanup)."""
    global _tv_instance, _is_logged_in
    _tv_instance = None
    _is_logged_in = False

def fetch_historical_data(symbol, exchange, interval=None, n_bars=7500, retries=3):
    """
    Fetch historical data with automatic session management and retries.
    
    Args:
        symbol: TradingView symbol (e.g., 'SPX', 'GOLD')
        exchange: Exchange code (e.g., 'TVC', 'COMEX')
        interval: Interval enum (default: daily)
        n_bars: Number of bars to fetch
        retries: Number of retry attempts
    
    Returns:
        DataFrame with OHLCV data or None on failure
    """
    import time
    
    if interval is None:
        interval = Interval.in_daily if Interval else None
    
    tv = get_tv_session()
    if not tv:
        return None
    
    for attempt in range(retries):
        try:
            data = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=n_bars)
            if data is not None and not data.empty:
                return data
            print(f"No data for {symbol} on attempt {attempt+1}")
        except Exception as e:
            print(f"Error fetching {symbol} [attempt {attempt+1}/{retries}]: {e}")
            if "session" in str(e).lower() or "login" in str(e).lower():
                # Session may have expired, try to reconnect
                print("Session issue detected, reconnecting...")
                get_tv_session(force_new=True)
        time.sleep(1 + attempt)  # Progressive backoff
    
    return None

# Re-export Interval for convenience
__all__ = ['get_tv_session', 'fetch_historical_data', 'is_session_active', 
           'is_logged_in', 'close_session', 'Interval', 'TV_AVAILABLE']
