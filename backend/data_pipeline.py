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

def try_tv_login(username, password, max_retries=10, delay=3):
    """
    Attempts to log in to TradingView with aggressive retry loop.
    Keeps trying until success, with exponential-ish backoff.
    """
    if not TV_AVAILABLE:
        return None

    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"Attempting TV Login ({attempt})...")
            if username and password:
                tv_instance = TvDatafeed(username, password)
            else:
                tv_instance = TvDatafeed()
            
            # Verify login worked by making a simple request
            test = tv_instance.get_hist("BTCUSD", "BITSTAMP", Interval.in_daily, n_bars=5)
            if test is not None and len(test) > 0:
                print("TV Login Successful!")
                return tv_instance
            else:
                raise Exception("Login succeeded but test fetch failed")
                
        except Exception as e:
            print(f"TV Login failed (Attempt {attempt}): {e}")
            if attempt >= max_retries:
                print("Max retries reached. Falling back to Guest mode...")
                try:
                    return TvDatafeed()
                except:
                    return None
            wait_time = min(delay * (1.5 ** (attempt - 1)), 30)  # Max 30s wait
            time.sleep(wait_time)

tv = try_tv_login(TV_USERNAME, TV_PASSWORD) if TV_AVAILABLE else None

# Output directory and cache setup
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, 'data_cache_info.json')

def check_data_freshness(symbol_name, cache_hours=12):
    """
    Checks if cached data for a symbol is still fresh (within cache_hours).
    Returns True if data needs refresh, False if cache is still valid.
    """
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_info = json.load(f)
            if symbol_name in cache_info:
                last_update = datetime.fromisoformat(cache_info[symbol_name])
                hours_elapsed = (datetime.now() - last_update).total_seconds() / 3600
                if hours_elapsed < cache_hours:
                    return False  # Cache is still fresh
    except Exception:
        pass
    return True  # Needs refresh

def update_cache_timestamp(symbol_name):
    """Updates the cache timestamp for a symbol."""
    try:
        cache_info = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_info = json.load(f)
        cache_info[symbol_name] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_info, f)
    except Exception:
        pass

START_DATE = '1970-01-01'

def max_bars_from_start(start_date: str, interval) -> int:
    """
    Calculates the maximum number of bars from start_date to now.
    Prevents requesting timestamps before 1970 which causes OSError on Windows.
    """
    start = pd.Timestamp(start_date)
    now = pd.Timestamp.now().normalize()  # Use tz-naive now() to match start

    if interval == Interval.in_monthly:
        return (now.year - start.year) * 12 + (now.month - start.month) + 1
    if interval == Interval.in_weekly:
        return int((now - start).days // 7) + 1
    if interval == Interval.in_daily:
        return int((now - start).days) + 1

    return 1500  # Default fallback

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
# Matches the PineScript GLI indicator by QuantitativeAlpha
TV_CONFIG = {
    # ==========================================================
    # CENTRAL BANK BALANCE SHEETS (17 banks)
    # ==========================================================
    # Major CBs
    'USCBBS': ('ECONOMICS', 'FED'),      # Federal Reserve
    'EUCBBS': ('ECONOMICS', 'ECB'),      # European Central Bank
    'JPCBBS': ('ECONOMICS', 'BOJ'),      # Bank of Japan
    'CNCBBS': ('ECONOMICS', 'PBOC'),     # People's Bank of China
    'GBCBBS': ('ECONOMICS', 'BOE'),      # Bank of England
    # Additional CBs (from "other_active" in PineScript)
    'CACBBS': ('ECONOMICS', 'BOC'),      # Bank of Canada
    'AUCBBS': ('ECONOMICS', 'RBA'),      # Reserve Bank of Australia
    'INCBBS': ('ECONOMICS', 'RBI'),      # Reserve Bank of India
    'CHCBBS': ('ECONOMICS', 'SNB'),      # Swiss National Bank
    'RUCBBS': ('ECONOMICS', 'CBR'),      # Central Bank of Russia
    'BRCBBS': ('ECONOMICS', 'BCB'),      # Banco Central do Brasil
    'KRCBBS': ('ECONOMICS', 'BOK'),      # Bank of Korea
    'NZCBBS': ('ECONOMICS', 'RBNZ'),     # Reserve Bank of New Zealand
    'SECBBS': ('ECONOMICS', 'SR'),       # Sveriges Riksbank (Sweden)
    'MYCBBS': ('ECONOMICS', 'BNM'),      # Bank Negara Malaysia
    
    # ==========================================================
    # M2 MONEY SUPPLY (14 economies)
    # ==========================================================
    # Major M2s
    'USM2': ('ECONOMICS', 'USM2'),       # USA
    'EUM2': ('ECONOMICS', 'EUM2'),       # EU
    'CNM2': ('ECONOMICS', 'CNM2'),       # China
    'JPM2': ('ECONOMICS', 'JPM2'),       # Japan
    # Additional M2s (from "other_m2_active" in PineScript)
    'GBM2': ('ECONOMICS', 'GBM2'),       # UK
    'CAM2': ('ECONOMICS', 'CAM2'),       # Canada
    'AUM3': ('ECONOMICS', 'AUM3'),       # Australia (M3)
    'INM2': ('ECONOMICS', 'INM2'),       # India
    'CHM2': ('ECONOMICS', 'CHM2'),       # Switzerland
    'RUM2': ('ECONOMICS', 'RUM2'),       # Russia
    'BRM2': ('ECONOMICS', 'BRM2'),       # Brazil
    'KRM2': ('ECONOMICS', 'KRM2'),       # Korea
    'MXM2': ('ECONOMICS', 'MXM2'),       # Mexico
    'IDM2': ('ECONOMICS', 'IDM2'),       # Indonesia
    'ZAM2': ('ECONOMICS', 'ZAM2'),       # South Africa
    'MYM2': ('ECONOMICS', 'MYM2'),       # Malaysia
    'SEM2': ('ECONOMICS', 'SEM2'),       # Sweden
    
    # ==========================================================
    # FX RATES (all needed for conversions)
    # ==========================================================
    'EURUSD': ('FX_IDC', 'EURUSD'),
    'JPYUSD': ('FX_IDC', 'JPYUSD'),
    'GBPUSD': ('FX_IDC', 'GBPUSD'),
    'CNYUSD': ('FX_IDC', 'CNYUSD'),
    'CADUSD': ('FX_IDC', 'CADUSD'),
    'AUDUSD': ('FX_IDC', 'AUDUSD'),
    'INRUSD': ('FX_IDC', 'INRUSD'),
    'CHFUSD': ('FX_IDC', 'CHFUSD'),
    'RUBUSD': ('FX_IDC', 'RUBUSD'),
    'BRLUSD': ('FX_IDC', 'BRLUSD'),
    'KRWUSD': ('FX_IDC', 'KRWUSD'),
    'NZDUSD': ('FX_IDC', 'NZDUSD'),
    'SEKUSD': ('FX_IDC', 'SEKUSD'),
    'MYRUSD': ('FX_IDC', 'MYRUSD'),
    'MXNUSD': ('FX_IDC', 'MXNUSD'),
    'IDRUSD': ('FX_IDC', 'IDRUSD'),
    'ZARUSD': ('FX_IDC', 'ZARUSD'),
    
    # ==========================================================
    # OTHER
    # ==========================================================
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

def fetch_tv_series(symbol, exchange, name, n_bars=1500, max_retries=3):
    """
    Fetches TradingView data with smart interval fallback for ECONOMICS.
    ECONOMICS data is typically monthly, so we try monthly → weekly → daily.
    Caps n_bars to avoid pre-1970 timestamps which cause OSError on Windows.
    """
    if not tv:
        return pd.Series(dtype=float, name=name)

    # ECONOMICS data: try daily first (highest resolution), then weekly, then monthly
    if exchange == "ECONOMICS":
        intervals = [Interval.in_daily, Interval.in_weekly, Interval.in_monthly]
    else:
        intervals = [Interval.in_daily]

    last_err = None

    for interval in intervals:
        # Cap n_bars to avoid pre-1970 timestamps (causes OSError on Windows)
        if exchange == "ECONOMICS":
            safe_cap = max_bars_from_start(START_DATE, interval)
            effective_n = min(n_bars, safe_cap)
        else:
            effective_n = n_bars

        for attempt in range(1, max_retries + 1):
            try:
                df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=effective_n)
                
                if df is not None and len(df) > 0 and "close" in df.columns:
                    s = df["close"].copy()
                    s.name = name
                    return s
                    
            except OSError as e:
                last_err = e
                # If Errno 22, try with even fewer bars (aggressive cap)
                if getattr(e, "errno", None) == 22 and effective_n > 200:
                    effective_n = max(200, effective_n // 2)
                time.sleep(1.5 * attempt)
            except Exception as e:
                last_err = e
                time.sleep(1.5 * attempt)

    if last_err:
        print(f"Error fetching TV {symbol} ({name}): {last_err}")
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
    """
    Calculates Credit Liquidity Index.
    SIGN CONVENTION: Higher CLI = easier credit conditions (bullish).
    Spreads ↑, VIX ↑, lending standards ↑ mean TIGHTER conditions => CLI ↓
    Therefore we NEGATE all z-scores.
    """
    res = pd.DataFrame(index=df.index)
    # Negate all z-scores: higher spread/VIX/lending = tighter = LOWER CLI
    res['HY_SPREAD_Z'] = -normalize_zscore(df['HY_SPREAD'])
    res['IG_SPREAD_Z'] = -normalize_zscore(df['IG_SPREAD'])
    res['NFCI_CREDIT_Z'] = -df['NFCI_CREDIT']  # NFCI already z-scored, negate
    res['NFCI_RISK_Z'] = -df['NFCI_RISK']
    res['LENDING_STD_Z'] = -normalize_zscore(df['LENDING_STD'])
    res['VIX_Z'] = -normalize_zscore(df['VIX'])
    
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
    """
    Calculates Global Liquidity Index in Trillions USD.
    Includes up to 16 central banks matching PineScript GLI indicator.
    """
    res = pd.DataFrame(index=df.index)
    
    if source == 'TV':
        # TradingView Units (ECONOMICS) - All are Raw Units (Units of Currency)
        # All CBs are converted to USD trillions using format: CB_local * XXXUSD / 1e12
        
        # Helper function for CB conversion
        def convert_cb(cb_col, fx_col, fx_fallback):
            if cb_col in df.columns:
                fx = df.get(fx_col, fx_fallback)
                return (df[cb_col] * fx) / 1e12
            return pd.Series(dtype=float)
        
        # Major 5 CBs
        res['FED_USD'] = df.get('FED', 0) / 1e12  # Already USD
        res['ECB_USD'] = convert_cb('ECB', 'EURUSD', 1.08)
        
        # BOJ uses JPYUSD (direct) or 1/USDJPY
        if 'BOJ' in df.columns:
            if 'JPYUSD' in df.columns:
                res['BOJ_USD'] = (df['BOJ'] * df['JPYUSD']) / 1e12
            else:
                res['BOJ_USD'] = df['BOJ'] / 150e12  # Fallback
        
        res['PBOC_USD'] = convert_cb('PBOC', 'CNYUSD', 0.14)
        res['BOE_USD'] = convert_cb('BOE', 'GBPUSD', 1.27)
        
        # Additional 11 CBs (matching PineScript "other_active")
        res['BOC_USD'] = convert_cb('BOC', 'CADUSD', 0.74)
        res['RBA_USD'] = convert_cb('RBA', 'AUDUSD', 0.65)
        res['RBI_USD'] = convert_cb('RBI', 'INRUSD', 0.012)
        res['SNB_USD'] = convert_cb('SNB', 'CHFUSD', 1.13)
        res['CBR_USD'] = convert_cb('CBR', 'RUBUSD', 0.011)
        res['BCB_USD'] = convert_cb('BCB', 'BRLUSD', 0.17)
        res['BOK_USD'] = convert_cb('BOK', 'KRWUSD', 0.00077)
        res['RBNZ_USD'] = convert_cb('RBNZ', 'NZDUSD', 0.60)
        res['SR_USD'] = convert_cb('SR', 'SEKUSD', 0.095)
        res['BNM_USD'] = convert_cb('BNM', 'MYRUSD', 0.22)
            
    else:
        # FRED Units logic (original 5 only):
        res['FED_USD'] = df['FED'] / 1e6
        res['ECB_USD'] = (df['ECB'] / 1e6) * df['EURUSD']
        res['BOJ_USD'] = (df['BOJ'] / 1e4) / df['USDJPY']
        res['BOE_USD'] = (df['BOE'] / 1e3) * df['GBPUSD']
        res['PBOC_USD'] = (df['PBOC'] / 1e12) / df['USDCNY']
    
    # Sum all available CBs dynamically
    cb_cols = [c for c in res.columns if c.endswith('_USD')]
    res['GLI_TOTAL'] = res[cb_cols].sum(axis=1)
    return res

def calculate_global_m2(df):
    """
    Calculates Global M2 Money Supply in Trillions USD.
    Includes up to 14 economies matching PineScript GLI indicator.
    """
    res = pd.DataFrame(index=df.index)
    
    # Helper function for M2 conversion
    def convert_m2(m2_col, fx_col, fx_fallback):
        if m2_col in df.columns:
            fx = df.get(fx_col, fx_fallback)
            return (df[m2_col] * fx) / 1e3  # Convert to trillions
        return pd.Series(dtype=float)
    
    # Major 4 M2s
    res['US_M2_USD'] = df.get('USM2', 0) / 1e3  # Already in USD billions
    res['EU_M2_USD'] = convert_m2('EUM2', 'EURUSD', 1.08)
    res['CN_M2_USD'] = convert_m2('CNM2', 'CNYUSD', 0.14)
    
    # Japan M2 uses JPYUSD
    if 'JPM2' in df.columns:
        if 'JPYUSD' in df.columns:
            res['JP_M2_USD'] = (df['JPM2'] * df['JPYUSD']) / 1e3
        else:
            res['JP_M2_USD'] = df['JPM2'] / 150e3  # Fallback
    
    # Additional 10 M2s (matching PineScript "other_m2_active")
    res['UK_M2_USD'] = convert_m2('GBM2', 'GBPUSD', 1.27)
    res['CA_M2_USD'] = convert_m2('CAM2', 'CADUSD', 0.74)
    res['AU_M2_USD'] = convert_m2('AUM3', 'AUDUSD', 0.65)  # Australia uses M3
    res['IN_M2_USD'] = convert_m2('INM2', 'INRUSD', 0.012)
    res['CH_M2_USD'] = convert_m2('CHM2', 'CHFUSD', 1.13)
    res['RU_M2_USD'] = convert_m2('RUM2', 'RUBUSD', 0.011)
    res['BR_M2_USD'] = convert_m2('BRM2', 'BRLUSD', 0.17)
    res['KR_M2_USD'] = convert_m2('KRM2', 'KRWUSD', 0.00077)
    res['MX_M2_USD'] = convert_m2('MXM2', 'MXNUSD', 0.058)
    res['ID_M2_USD'] = convert_m2('IDM2', 'IDRUSD', 0.000063)
    res['ZA_M2_USD'] = convert_m2('ZAM2', 'ZARUSD', 0.054)
    res['MY_M2_USD'] = convert_m2('MYM2', 'MYRUSD', 0.22)
    res['SE_M2_USD'] = convert_m2('SEM2', 'SEKUSD', 0.095)
    
    # Calculate total dynamically
    m2_cols = [c for c in res.columns if c.endswith('_M2_USD')]
    if m2_cols:
        res['M2_TOTAL'] = res[m2_cols].sum(axis=1)
    else:
        res['M2_TOTAL'] = 0
    
    return res

def calculate_rocs(df, windows={'1M': 21, '3M': 63, '6M': 126, '1Y': 252}):
    """
    Calculates Rate of Change for specified windows.
    NOTE: NaN values are preserved (not filled) to avoid artificial floors
    and contaminated correlations. Convert to None only for JSON output.
    """
    rocs = {}
    for label, window in windows.items():
        # ROC Calculation: (Current / Past) - 1
        roc = (df / df.shift(window) - 1) * 100
        rocs[label] = roc  # Keep NaN, don't fillna(0)
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
        
        # Align indices
        common_idx = s1.index.intersection(s2.index)
        if len(common_idx) > 30:
            correlations[lag] = s1.loc[common_idx].corr(s2.loc[common_idx])
        else:
            correlations[lag] = None
    return correlations

def calculate_lag_correlation_analysis(df, max_lag=30):
    """
    Calculates multi-window ROCs for CLI and BTC, then computes lag correlations.
    Returns a dictionary with ROC series and lag correlation analysis.
    """
    results = {
        'rocs': {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
        },
        'lag_correlations': {}
    }
    
    windows = {'7d': 7, '14d': 14, '30d': 30}
    
    # Calculate ROCs for CLI and BTC at each window
    for label, window in windows.items():
        # CLI ROC
        if 'CLI' in df.columns:
            cli_roc = (df['CLI'] / df['CLI'].shift(window) - 1) * 100
            results['rocs'][f'cli_{label}'] = [float(x) if pd.notnull(x) else None for x in cli_roc.tolist()]
        
        # BTC ROC
        if 'BTC_Price' in df.columns:
            btc_roc = (df['BTC_Price'] / df['BTC_Price'].shift(window) - 1) * 100
            results['rocs'][f'btc_{label}'] = [float(x) if pd.notnull(x) else None for x in btc_roc.tolist()]
            
            # Compute lag correlations for this window
            if 'CLI' in df.columns:
                correlations = []
                lags = list(range(0, max_lag + 1))
                
                cli_roc_clean = cli_roc.dropna()
                btc_roc_clean = btc_roc.dropna()
                
                for lag in lags:
                    # CLI at time t vs BTC at time t+lag (CLI leads)
                    # This means: does CLI's change today predict BTC's change in 'lag' days?
                    if lag == 0:
                        common_idx = cli_roc_clean.index.intersection(btc_roc_clean.index)
                    else:
                        # Shift BTC backward by 'lag' days to see if CLI today correlates with BTC later
                        btc_shifted = btc_roc_clean.shift(-lag)
                        common_idx = cli_roc_clean.index.intersection(btc_shifted.dropna().index)
                        btc_roc_clean_lag = btc_shifted
                    
                    if len(common_idx) > 50:
                        if lag == 0:
                            corr = cli_roc_clean.loc[common_idx].corr(btc_roc_clean.loc[common_idx])
                        else:
                            corr = cli_roc_clean.loc[common_idx].corr(btc_roc_clean_lag.loc[common_idx])
                        correlations.append(round(corr, 4) if pd.notnull(corr) else None)
                    else:
                        correlations.append(None)
                
                # Find optimal lag
                valid_corrs = [(i, c) for i, c in enumerate(correlations) if c is not None]
                if valid_corrs:
                    optimal_idx, max_corr = max(valid_corrs, key=lambda x: abs(x[1]))
                    optimal_lag = lags[optimal_idx]
                else:
                    optimal_lag = 0
                    max_corr = 0
                
                results['lag_correlations'][label] = {
                    'lags': lags,
                    'correlations': correlations,
                    'optimal_lag': optimal_lag,
                    'max_corr': round(max_corr, 4) if max_corr else 0
                }
    
    return results


def calculate_btc_fair_value(df_t):
    """
    Calculates dual Bitcoin fair value models:
    1. Standard Quant (Macro Only)
    2. Adoption-Adjusted (Macro + Power Law/Log-Time)
    """
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    result = pd.DataFrame(index=df_t.index)
    
    if 'BTC' not in df_t.columns:
        return result
    
    btc_series = df_t['BTC'].dropna()
    if len(btc_series) < 100:
        return result
    
    # 1. Base Macro Features
    raw_features = pd.DataFrame({
        'GLI_TOTAL': df_t.get('GLI_TOTAL', 0).shift(45),
        'CLI': df_t.get('CLI', 0).shift(14),
        'VIX': df_t.get('VIX', 0),
        'NET_LIQ': df_t.get('NET_LIQUIDITY', 0).shift(30),
    })

    # 2. Adoption Feature (Log Days since Genesis 2009-01-03)
    genesis_date = pd.Timestamp('2009-01-03')
    days_since_genesis = (df_t.index - genesis_date).days
    # Avoid log(0)
    raw_features['ADOPTION'] = np.log(np.maximum(days_since_genesis, 1))

    btc_start = btc_series.index.min()
    valid_mask = (df_t.index >= btc_start)
    
    # Training Data
    y_train_raw = btc_series
    X_train_raw = raw_features.loc[y_train_raw.index]
    train_data = pd.concat([X_train_raw, np.log(y_train_raw)], axis=1).dropna()
    
    if len(train_data) < 100:
        return result
        
    y_train = train_data['BTC'] # log_btc
    scaler = StandardScaler()

    # --- MODEL 1: MACRO ONLY ---
    X_m_train = train_data[['GLI_TOTAL', 'CLI', 'VIX', 'NET_LIQ']]
    X_m_scaled = scaler.fit_transform(X_m_train)
    model_m = LinearRegression()
    model_m.fit(X_m_scaled, y_train.values)
    
    X_m_full = raw_features[['GLI_TOTAL', 'CLI', 'VIX', 'NET_LIQ']].loc[valid_mask].ffill().bfill()
    X_m_full_scaled = scaler.transform(X_m_full)
    log_pred_m = pd.Series(model_m.predict(X_m_full_scaled), index=X_m_full.index)
    
    # --- MODEL 2: ADOPTION ADJUSTED (Macro + Time) ---
    X_a_train = train_data[['GLI_TOTAL', 'CLI', 'VIX', 'NET_LIQ', 'ADOPTION']]
    X_a_scaled = scaler.fit_transform(X_a_train)
    # Use Ridge to prevent multicollinearity between Time and Liquidity
    model_a = Ridge(alpha=1.0)
    model_a.fit(X_a_scaled, y_train.values)
    
    X_a_full = raw_features[['GLI_TOTAL', 'CLI', 'VIX', 'NET_LIQ', 'ADOPTION']].loc[valid_mask].ffill().bfill()
    X_a_full_scaled = scaler.transform(X_a_full)
    log_pred_a = pd.Series(model_a.predict(X_a_full_scaled), index=X_a_full.index)

    # Helper to calculate bands and metrics
    def build_model_df(log_pred, btc_actual):
        pred_fair = np.exp(log_pred)
        log_actual = np.log(btc_actual.dropna())
        common_idx = log_actual.index.intersection(log_pred.index)
        std_log = (log_actual[common_idx] - log_pred[common_idx]).std()
        
        df = pd.DataFrame(index=log_pred.index)
        df['FAIR_VALUE'] = pred_fair
        df['UPPER_1SD'] = pred_fair * np.exp(std_log)
        df['LOWER_1SD'] = pred_fair * np.exp(-std_log)
        df['UPPER_2SD'] = pred_fair * np.exp(2 * std_log)
        df['LOWER_2SD'] = pred_fair * np.exp(-2 * std_log)
        df['DEVIATION_PCT'] = (btc_actual - pred_fair) / pred_fair * 100
        df['DEVIATION_ZSCORE'] = (np.log(btc_actual) - log_pred) / std_log
        return df

    res_m = build_model_df(log_pred_m, df_t['BTC']).rename(columns=lambda x: f"BTC_{x}")
    res_a = build_model_df(log_pred_a, df_t['BTC']).rename(columns=lambda x: f"ADJ_BTC_{x}")

    result_btc = pd.concat([res_m, res_a], axis=1)
    result_btc['BTC_ACTUAL'] = df_t['BTC']
    
    return result.join(result_btc, how='left')

def calculate_btc_fair_value_v2(df_t):
    """
    QUANT V2: Enhanced Bitcoin Fair Value Model
    
    Key Improvements:
    1. Weekly frequency (W-FRI) to avoid ffill autocorrelation
    2. Models Δlog(BTC) returns instead of log(BTC) levels (avoids spurious regression)
    3. ElasticNet with multiple lags (1-8 weeks) for automatic feature selection
    4. GLI as PCA factor (not sum) to handle colinearity
    5. Rolling 52-week volatility for adaptive bands
    6. Walk-forward cross-validation metrics
    """
    from sklearn.linear_model import ElasticNetCV
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.decomposition import PCA
    import numpy as np
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    result = {}
    
    if 'BTC' not in df_t.columns:
        return result
    
    # 1. Resample to Weekly (Friday)
    df_weekly = df_t.resample('W-FRI').last().dropna(how='all')
    
    btc_series = df_weekly['BTC'].dropna()
    if len(btc_series) < 100:
        return result
    
    # 2. Calculate Δlog returns (weekly)
    btc_log_ret = np.log(btc_series).diff()
    
    # 3. Build GLI PCA Factor
    gli_cols = ['FED_USD', 'ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD']
    gli_available = [c for c in gli_cols if c in df_weekly.columns]
    
    if len(gli_available) >= 3:
        gli_df = df_weekly[gli_available].ffill().bfill()
        # Calculate Δlog for each CB
        gli_dlog = np.log(gli_df).diff()
        gli_dlog_clean = gli_dlog.dropna()
        
        if len(gli_dlog_clean) > 50:
            scaler_pca = RobustScaler()
            gli_scaled = scaler_pca.fit_transform(gli_dlog_clean)
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(gli_scaled)
            gli_factor = pd.Series(pca_result[:, 0], index=gli_dlog_clean.index, name='GLI_FACTOR')
        else:
            gli_factor = pd.Series(dtype=float)
    else:
        gli_factor = pd.Series(dtype=float)
    
    # 4. Prepare Features with Multiple Lags (1-8 weeks)
    feature_df = pd.DataFrame(index=df_weekly.index)
    
    # CLI changes
    if 'CLI' in df_weekly.columns:
        cli_series = df_weekly['CLI'].ffill()
        cli_dlog = cli_series.diff()
        for lag in range(1, 9):
            feature_df[f'CLI_L{lag}'] = cli_dlog.shift(lag)
    
    # GLI Factor lags
    if not gli_factor.empty:
        for lag in range(1, 9):
            feature_df[f'GLI_L{lag}'] = gli_factor.shift(lag)
    
    # VIX changes
    if 'VIX' in df_weekly.columns:
        vix_series = df_weekly['VIX'].ffill()
        vix_diff = vix_series.diff()
        for lag in range(1, 5):
            feature_df[f'VIX_L{lag}'] = vix_diff.shift(lag)
    
    # Net Liquidity changes
    if 'NET_LIQUIDITY' in df_weekly.columns:
        netliq = df_weekly['NET_LIQUIDITY'].ffill()
        netliq_dlog = np.log(netliq.replace(0, np.nan)).diff()
        for lag in range(1, 9):
            feature_df[f'NETLIQ_L{lag}'] = netliq_dlog.shift(lag)
    
    # 5. Align data for training - all on weekly index
    btc_start = btc_series.index.min()
    common_idx = btc_log_ret.index.intersection(feature_df.index)
    common_idx = common_idx[common_idx >= btc_start]
    
    y = btc_log_ret.loc[common_idx]
    X = feature_df.loc[common_idx]
    
    # Clean dataset
    train_data = pd.concat([X, y.rename('TARGET')], axis=1).dropna()
    
    if len(train_data) < 100:
        return result
    
    y_train = train_data['TARGET']
    X_train = train_data.drop('TARGET', axis=1)
    
    # 6. ElasticNet with CV for automatic lag selection
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    model = ElasticNetCV(
        l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95],
        alphas=np.logspace(-4, 0, 20),
        cv=5,
        max_iter=5000,
        random_state=42
    )
    model.fit(X_scaled, y_train)
    
    # 7. Generate predictions using the same common index
    X_full = feature_df.loc[common_idx].ffill().bfill()
    X_full_scaled = scaler.transform(X_full)
    pred_returns = pd.Series(model.predict(X_full_scaled), index=X_full.index)
    
    # 8. Reconstruct log price from cumulative returns
    log_btc_actual = np.log(btc_series)
    first_log = log_btc_actual.iloc[0]
    log_pred_cumulative = pred_returns.cumsum() + first_log
    fair_value = np.exp(log_pred_cumulative)
    
    # 9. Rolling 52-week volatility bands
    residuals = log_btc_actual.loc[fair_value.index] - log_pred_cumulative.loc[log_btc_actual.index.intersection(fair_value.index)]
    rolling_std = residuals.rolling(window=52, min_periods=20).std().ffill().bfill()
    
    # Use median std as fallback for early periods
    median_std = rolling_std.median()
    rolling_std = rolling_std.fillna(median_std)
    
    upper_1sd = fair_value * np.exp(rolling_std)
    lower_1sd = fair_value * np.exp(-rolling_std)
    upper_2sd = fair_value * np.exp(2 * rolling_std)
    lower_2sd = fair_value * np.exp(-2 * rolling_std)
    
    # 10. Deviation metrics
    deviation_pct = (btc_series - fair_value) / fair_value * 100
    deviation_zscore = residuals / rolling_std
    
    # 11. Walk-forward OOS metrics (simplified)
    oos_start = int(len(train_data) * 0.7)
    if oos_start > 50:
        oos_resid = y_train.iloc[oos_start:] - model.predict(X_scaled[oos_start:])
        oos_rmse = np.sqrt((oos_resid ** 2).mean())
        oos_mae = np.abs(oos_resid).mean()
        hit_rate = (np.sign(y_train.iloc[oos_start:]) == np.sign(model.predict(X_scaled[oos_start:]))).mean()
    else:
        oos_rmse, oos_mae, hit_rate = np.nan, np.nan, np.nan
    
    # 12. Feature importance (non-zero coefficients)
    feature_importance = dict(zip(X_train.columns, model.coef_))
    active_features = {k: v for k, v in feature_importance.items() if abs(v) > 1e-6}
    
    # 13. Predicted vs Actual Returns (for returns comparison chart)
    actual_returns = btc_log_ret.loc[common_idx] * 100  # Convert to percentage
    predicted_returns_pct = pred_returns * 100  # Convert to percentage
    
    # 14. Rebalanced Fair Value (quarterly reset to avoid cumulative drift)
    # Reset fair value to actual BTC price every 13 weeks (quarterly)
    rebalanced_fv = pd.Series(index=fair_value.index, dtype=float)
    rebalance_period = 13  # weeks
    
    for i, date in enumerate(fair_value.index):
        if i == 0 or i % rebalance_period == 0:
            # Reset to actual BTC price
            if date in btc_series.index:
                base_log = np.log(btc_series.loc[date])
            else:
                base_log = np.log(fair_value.iloc[i])
            cumulative_pred = 0
        else:
            cumulative_pred += pred_returns.iloc[i] if i < len(pred_returns) else 0
        
        rebalanced_fv.iloc[i] = np.exp(base_log + cumulative_pred)
    
    # Build result dictionary
    result = {
        'dates': fair_value.index.strftime('%Y-%m-%d').tolist(),
        'fair_value': [float(x) if pd.notnull(x) else None for x in fair_value.tolist()],
        'upper_1sd': [float(x) if pd.notnull(x) else None for x in upper_1sd.tolist()],
        'lower_1sd': [float(x) if pd.notnull(x) else None for x in lower_1sd.tolist()],
        'upper_2sd': [float(x) if pd.notnull(x) else None for x in upper_2sd.tolist()],
        'lower_2sd': [float(x) if pd.notnull(x) else None for x in lower_2sd.tolist()],
        'btc_price': [float(x) if pd.notnull(x) else None for x in btc_series.tolist()],
        'deviation_pct': [float(x) if pd.notnull(x) else None for x in deviation_pct.tolist()],
        'deviation_zscore': [float(x) if pd.notnull(x) else None for x in deviation_zscore.tolist()],
        # New: Returns comparison data
        'returns': {
            'dates': actual_returns.index.strftime('%Y-%m-%d').tolist(),
            'actual': [float(x) if pd.notnull(x) else None for x in actual_returns.tolist()],
            'predicted': [float(x) if pd.notnull(x) else None for x in predicted_returns_pct.tolist()],
        },
        # New: Rebalanced fair value
        'rebalanced_fv': [float(x) if pd.notnull(x) else None for x in rebalanced_fv.tolist()],
        'metrics': {
            'oos_rmse': round(oos_rmse, 6) if pd.notnull(oos_rmse) else None,
            'oos_mae': round(oos_mae, 6) if pd.notnull(oos_mae) else None,
            'hit_rate': round(hit_rate, 4) if pd.notnull(hit_rate) else None,
            'r2_insample': round(model.score(X_scaled, y_train), 4),
            'alpha': round(model.alpha_, 6),
            'l1_ratio': round(model.l1_ratio_, 2),
            'n_active_features': len(active_features),
        },
        'active_features': active_features,
        'frequency': 'weekly'
    }
    
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
    cached_fred_file = os.path.join(OUTPUT_DIR, 'fred_cache_data.json')
    
    # Load cached FRED data if exists
    cached_fred = {}
    if os.path.exists(cached_fred_file):
        try:
            with open(cached_fred_file, 'r') as f:
                cached_fred = json.load(f)
        except Exception:
            cached_fred = {}
    
    fred_fetched = 0
    fred_cached = 0
    for sid, name in FRED_CONFIG.items():
        # FRED updates daily, use 24 hour cache
        if not check_data_freshness(f"FRED_{name}", cache_hours=24) and name in cached_fred:
            # Use cached data
            raw_fred[name] = pd.Series(cached_fred[name]['values'], 
                                       index=pd.to_datetime(cached_fred[name]['dates']), 
                                       name=name)
            fred_cached += 1
        else:
            # Fetch fresh data
            s = fetch_fred_series(sid, name)
            if not s.empty:
                raw_fred[name] = s
                update_cache_timestamp(f"FRED_{name}")
                # Cache the data
                cached_fred[name] = {
                    'dates': s.index.strftime('%Y-%m-%d').tolist(),
                    'values': s.tolist()
                }
                fred_fetched += 1
    
    # Save updated FRED cache
    try:
        with open(cached_fred_file, 'w') as f:
            json.dump(cached_fred, f)
    except Exception as e:
        print(f"Warning: Could not save FRED cache: {e}")
    
    print(f"  -> Fetched {fred_fetched} FRED symbols, used cache for {fred_cached} symbols")
    
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
    cached_data_file = os.path.join(OUTPUT_DIR, 'tv_cache_data.json')
    
    # Load cached TV data if exists
    cached_tv = {}
    if os.path.exists(cached_data_file):
        try:
            with open(cached_data_file, 'r') as f:
                cached_tv = json.load(f)
        except Exception:
            cached_tv = {}
    
    if tv:
        symbols_fetched = 0
        symbols_cached = 0
        for symbol, (exchange, name) in TV_CONFIG.items():
            # Check if cache is still fresh (12 hours for most data)
            cache_hours = 12 if exchange == "ECONOMICS" else 1  # FX updates more frequently
            if not check_data_freshness(name, cache_hours=cache_hours) and name in cached_tv:
                # Use cached data
                raw_tv[name] = pd.Series(cached_tv[name]['values'], 
                                         index=pd.to_datetime(cached_tv[name]['dates']), 
                                         name=name)
                symbols_cached += 1
            else:
                # Fetch fresh data
                s = fetch_tv_series(symbol, exchange, name, n_bars=5000)
                if not s.empty:
                    raw_tv[name] = s
                    update_cache_timestamp(name)
                    # Cache the data
                    cached_tv[name] = {
                        'dates': s.index.strftime('%Y-%m-%d').tolist(),
                        'values': s.tolist()
                    }
                    symbols_fetched += 1
        
        # Save updated cache
        try:
            with open(cached_data_file, 'w') as f:
                json.dump(cached_tv, f)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
        
        print(f"  -> Fetched {symbols_fetched} symbols, used cache for {symbols_cached} symbols")
    
    df_tv_t = pd.DataFrame(index=pd.concat(raw_tv.values()).index.unique() if raw_tv else []).sort_index()
    if raw_tv:
        for name, s in raw_tv.items(): df_tv_t[name] = s
        
        # Only ffill for most series. bfill ONLY for FX rates as they are denominators.
        # All FX rates from TV_CONFIG matching PineScript
        all_fx = ['EURUSD', 'JPYUSD', 'GBPUSD', 'CNYUSD', 'CADUSD', 'AUDUSD', 'INRUSD', 'CHFUSD', 
                  'RUBUSD', 'BRLUSD', 'KRWUSD', 'NZDUSD', 'SEKUSD', 'MYRUSD', 'MXNUSD', 'IDRUSD', 'ZARUSD']
        fx_cols = [c for c in all_fx if c in df_tv_t.columns]
        for c in fx_cols:
            df_tv_t[c] = df_tv_t[c].ffill().bfill()
        
        # Everything else only ffills (forward in time)
        other_cols = [c for c in df_tv_t.columns if c not in fx_cols]
        for c in other_cols:
            df_tv_t[c] = df_tv_t[c].ffill()
        
        # Unit Logic for TV -> Trillions (Major 5 CBs)
        res_tv_t = pd.DataFrame(index=df_tv_t.index)
        res_tv_t['FED_USD'] = df_tv_t.get('FED', 0) / 1e12
        eurusd = df_tv_t.get('EURUSD', df_fred.get('EURUSD', 1.0))
        res_tv_t['ECB_USD'] = (df_tv_t.get('ECB', 0) * eurusd) / 1e12
        jpyusd = df_tv_t.get('JPYUSD', 1.0 / df_fred.get('USDJPY', 150))  # JPYUSD from TV, fallback to 1/USDJPY from FRED
        res_tv_t['BOJ_USD'] = (df_tv_t.get('BOJ', 0) * jpyusd) / 1e12
        gbpusd = df_tv_t.get('GBPUSD', df_fred.get('GBPUSD', 1.3))
        res_tv_t['BOE_USD'] = (df_tv_t.get('BOE', 0) * gbpusd) / 1e12
        cnynusd = df_tv_t.get('CNYUSD', df_fred.get('CNYUSD', 0.14))
        res_tv_t['PBOC_USD'] = (df_tv_t.get('PBOC', 0) * cnynusd) / 1e12

        # Additional 4 CBs
        if 'BOC' in df_tv_t.columns:
            cadusd = df_tv_t.get('CADUSD', 0.74)  # Fallback
            res_tv_t['BOC_USD'] = (df_tv_t.get('BOC', 0) * cadusd) / 1e12
        if 'RBA' in df_tv_t.columns:
            audusd = df_tv_t.get('AUDUSD', 0.65)  # Fallback
            res_tv_t['RBA_USD'] = (df_tv_t.get('RBA', 0) * audusd) / 1e12
        if 'SNB' in df_tv_t.columns:
            chfusd = df_tv_t.get('CHFUSD', 1.1)  # Fallback
            res_tv_t['SNB_USD'] = (df_tv_t.get('SNB', 0) * chfusd) / 1e12
        if 'BOK' in df_tv_t.columns:
            krwusd = df_tv_t.get('KRWUSD', 0.00077)  # Fallback ~1/1300
            res_tv_t['BOK_USD'] = (df_tv_t.get('BOK', 0) * krwusd) / 1e12

        # Bitcoin price (already in USD, no conversion needed)
        res_tv_t['BTC'] = df_tv_t.get('BTC', pd.Series(dtype=float))

        # M2 Money Supply data (pass through ALL M2s from TV_CONFIG for calculate_global_m2)
        all_m2 = ['USM2', 'EUM2', 'CNM2', 'JPM2', 'GBM2', 'CAM2', 'AUM3', 'INM2', 'CHM2', 
                  'RUM2', 'BRM2', 'KRM2', 'MXM2', 'IDM2', 'ZAM2', 'MYM2', 'SEM2']
        for m2_col in all_m2:
            if m2_col in df_tv_t.columns:
                res_tv_t[m2_col] = df_tv_t[m2_col]
        
        # Also pass through all FX rates for calculate_global_m2
        for fx_col in all_fx:
            if fx_col in df_tv_t.columns:
                res_tv_t[fx_col] = df_tv_t[fx_col]

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
        btc_analysis_v2 = calculate_btc_fair_value_v2(df_t)  # Quant v2 model
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

        # Predictive Lag Correlation Analysis (CLI vs BTC ROC)
        predictive = {}
        if 'BTC' in df_t.columns and 'CLI' in df_t.columns:
            analysis_df = pd.DataFrame({
                'CLI': df_t['CLI'],
                'BTC_Price': df_t['BTC']
            })
            predictive = calculate_lag_correlation_analysis(analysis_df.dropna(), max_lag=30)

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
                # Additional CBs
                'boc': clean_for_json(gli.get('BOC_USD', pd.Series(dtype=float))),
                'rba': clean_for_json(gli.get('RBA_USD', pd.Series(dtype=float))),
                'snb': clean_for_json(gli.get('SNB_USD', pd.Series(dtype=float))),
                'bok': clean_for_json(gli.get('BOK_USD', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in gli_rocs.items()}
            },
            'm2': (lambda m2_data, m2_rocs: {
                'total': clean_for_json(m2_data.get('M2_TOTAL', pd.Series(dtype=float))),
                'us': clean_for_json(m2_data.get('US_M2_USD', pd.Series(dtype=float))),
                'eu': clean_for_json(m2_data.get('EU_M2_USD', pd.Series(dtype=float))),
                'cn': clean_for_json(m2_data.get('CN_M2_USD', pd.Series(dtype=float))),
                'jp': clean_for_json(m2_data.get('JP_M2_USD', pd.Series(dtype=float))),
                'uk': clean_for_json(m2_data.get('UK_M2_USD', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in m2_rocs.items()}
            })(calculate_global_m2(df_t), calculate_rocs(calculate_global_m2(df_t).get('M2_TOTAL', pd.Series(dtype=float)))),
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
                'models': {
                    'macro': {
                        'fair_value': clean_for_json(btc_analysis.get('BTC_FAIR_VALUE', pd.Series(dtype=float))),
                        'upper_1sd': clean_for_json(btc_analysis.get('BTC_UPPER_1SD', pd.Series(dtype=float))),
                        'lower_1sd': clean_for_json(btc_analysis.get('BTC_LOWER_1SD', pd.Series(dtype=float))),
                        'upper_2sd': clean_for_json(btc_analysis.get('BTC_UPPER_2SD', pd.Series(dtype=float))),
                        'lower_2sd': clean_for_json(btc_analysis.get('BTC_LOWER_2SD', pd.Series(dtype=float))),
                        'deviation_pct': clean_for_json(btc_analysis.get('BTC_DEVIATION_PCT', pd.Series(dtype=float))),
                        'deviation_zscore': clean_for_json(btc_analysis.get('BTC_DEVIATION_ZSCORE', pd.Series(dtype=float))),
                    },
                    'adoption': {
                        'fair_value': clean_for_json(btc_analysis.get('ADJ_BTC_FAIR_VALUE', pd.Series(dtype=float))),
                        'upper_1sd': clean_for_json(btc_analysis.get('ADJ_BTC_UPPER_1SD', pd.Series(dtype=float))),
                        'lower_1sd': clean_for_json(btc_analysis.get('ADJ_BTC_LOWER_1SD', pd.Series(dtype=float))),
                        'upper_2sd': clean_for_json(btc_analysis.get('ADJ_BTC_UPPER_2SD', pd.Series(dtype=float))),
                        'lower_2sd': clean_for_json(btc_analysis.get('ADJ_BTC_LOWER_2SD', pd.Series(dtype=float))),
                        'deviation_pct': clean_for_json(btc_analysis.get('ADJ_BTC_DEVIATION_PCT', pd.Series(dtype=float))),
                        'deviation_zscore': clean_for_json(btc_analysis.get('ADJ_BTC_DEVIATION_ZSCORE', pd.Series(dtype=float))),
                    },
                    'quant_v2': btc_analysis_v2  # New Quant v2 model with weekly data
                },
                'rocs': {k: clean_for_json(v) for k, v in btc_rocs.items()} if btc_rocs else {}
            },
            'correlations': correlations,
            'predictive': predictive
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
