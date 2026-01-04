"""
Official Rate Sources Module
============================
Fetches official compounded rates and indices for XCCY basis calculation.

Sources:
- EUR: ECB SDMX API (3M Compounded €STR Average)
- USD: FRED SOFRINDEX (calculate 3M from index ratio)
- GBP: FRED SONIA Compounded Index (calculate 3M from index ratio)
- JPY: BoJ Call Rate via bojdata (with XLSX fallback)

Author: Quantitative Analysis Module
Date: January 2026
"""

import pandas as pd
import numpy as np
import requests
import os
import time
from pathlib import Path
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# ============================================================
# BOJ PATCH CONSTANTS
# ============================================================
BOJ_CURRENT_POLICY_RATE = 0.75  # BoJ policy rate as of Dec 19, 2025
FRED_JPY_CALL_RATE = 'IRSTCI01JPM156N'


# ============================================================
# INDEX-BASED RATE CALCULATION
# ============================================================

def compute_rate_from_index(
    index_series: pd.Series,
    tenor_days: int = 90,
    annualize_basis: int = 360
) -> pd.Series:
    """
    Calculate annualized rate from compounded index using ratio method.
    
    This is the market-standard approach used by ISDA/CME for term rates.
    
    Formula:
        R = (Index_t / Index_{t-tenor} - 1) * (annualize_basis / tenor_days) * 100
    
    Args:
        index_series: Compounded overnight index (e.g., SOFRINDEX, SONIA Index)
        tenor_days: Number of days for the term rate (default: 90 for 3M)
        annualize_basis: Day count basis for annualization (360 or 365)
        
    Returns:
        Annualized rate in percentage (e.g., 5.25 for 5.25%)
    """
    if index_series is None or index_series.empty:
        return pd.Series(dtype=float)
    
    # Shift by tenor to get the index value N days ago
    shifted = index_series.shift(tenor_days)
    
    # Calculate ratio and convert to annualized rate
    ratio = index_series / shifted
    rate = (ratio - 1) * (annualize_basis / tenor_days) * 100
    
    rate.name = f'{index_series.name}_3M_RATE' if index_series.name else 'COMPOUNDED_3M_RATE'
    return rate


# ============================================================
# EUR: ECB SDMX API
# ============================================================

def fetch_ecb_estr_3m(
    start_date: str = None,
    end_date: str = None,
    use_index: bool = False
) -> pd.Series:
    """
    Fetch 3M Compounded €STR Average from ECB SDMX API.
    
    Primary: EST.B.EU000A2QQF32.CR (3M Compounded Average Rate)
    Alternative: EST.B.EU000A2QQF08.CI (Compounded Index) → compute rate
    
    Args:
        start_date: Start date (YYYY-MM-DD), default 5 years ago
        end_date: End date (YYYY-MM-DD), default today
        use_index: If True, fetch index and compute rate instead of direct avg
        
    Returns:
        Series with 3M €STR compounded average rate (%)
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # ECB SDMX REST API endpoint
    # URL format: service/data/flowRef/key
    base_url = "https://data-api.ecb.europa.eu/service/data"
    
    if use_index:
        # Compounded Index
        flow_ref = "EST"
        series_key = "B.EU000A2QQF08.CI"
        fallback_description = "€STR Compounded Index"
    else:
        # 3M Compounded Average Rate (preferred - no calculation needed)
        flow_ref = "EST"
        series_key = "B.EU000A2QQF32.CR"
        fallback_description = "€STR 3M Compounded Average"
    
    url = f"{base_url}/{flow_ref}/{series_key}"
    
    params = {
        'startPeriod': start_date,
        'endPeriod': end_date,
        'format': 'csvdata'
    }
    
    headers = {
        'Accept': 'text/csv',
        'User-Agent': 'rates_sources/1.0 (requests)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse CSV response
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        
        if df.empty:
            logger.warning(f"ECB API returned empty data for {series_key}")
            return pd.Series(dtype=float, name='ESTR_3M')
        
        # ECB SDMX CSV has 'TIME_PERIOD' and 'OBS_VALUE' columns
        if 'TIME_PERIOD' in df.columns and 'OBS_VALUE' in df.columns:
            df['TIME_PERIOD'] = pd.to_datetime(df['TIME_PERIOD'])
            result = df.set_index('TIME_PERIOD')['OBS_VALUE'].sort_index()
            result.name = 'ESTR_3M'
            
            if use_index:
                # If we fetched index, compute rate from it
                result = compute_rate_from_index(result, tenor_days=90, annualize_basis=360)
            
            logger.info(f"Fetched {len(result)} points of {fallback_description}")
            return result
        else:
            logger.warning(f"Unexpected ECB response format: {df.columns.tolist()}")
            return pd.Series(dtype=float, name='ESTR_3M')
            
    except requests.exceptions.RequestException as e:
        logger.error(f"ECB API request failed: {e}")
        return pd.Series(dtype=float, name='ESTR_3M')
    except Exception as e:
        logger.error(f"Error processing ECB data: {e}")
        return pd.Series(dtype=float, name='ESTR_3M')


def fetch_estr_fallback_from_fred(df_fred: pd.DataFrame) -> pd.Series:
    """
    Fallback: Compute 3M €STR from daily rate via rolling compound.
    
    Uses FRED series ECBESTRVOLWGTTRMDRATE (daily €STR rate).
    Less accurate than ECB's official 3M average but works as backup.
    
    Args:
        df_fred: DataFrame with FRED data containing 'ESTR' column
        
    Returns:
        Approximate 3M compounded €STR rate (%)
    """
    estr_daily = df_fred.get('ESTR', pd.Series(dtype=float))
    
    if estr_daily.empty:
        # Try original FRED ticker as fallback
        estr_daily = df_fred.get('ECBESTRVOLWGTTRMDMNRT', pd.Series(dtype=float))
    
    if estr_daily.empty:
        return pd.Series(dtype=float, name='ESTR_3M_FALLBACK')
    
    # Simple 90-day rolling average (approximation, not true compounding)
    # True compounding would require: prod((1 + r_i / 360)) over 90 days
    # This approximation is acceptable for the proxy use case
    rate_3m_approx = estr_daily.rolling(window=90, min_periods=45).mean()
    rate_3m_approx.name = 'ESTR_3M_FALLBACK'
    
    logger.info("Using FRED €STR fallback (rolling average approximation)")
    return rate_3m_approx


# ============================================================
# BOJ CALL RATE WITH CACHE (HISTORICAL FROM 2000)
# ============================================================

# Cache configuration
BOJ_CACHE_FILENAME = 'boj_call_rate_cache.csv'
BOJ_START_YEAR = 2000
BOJ_XLSX_START_DATE = '2025-09-01'  # BoJ started daily XLSX pattern around this date


def _get_boj_cache_path() -> Path:
    """Get path to BoJ cache file (backend/cache/boj_call_rate_cache.csv)."""
    cache_dir = Path(__file__).resolve().parent / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / BOJ_CACHE_FILENAME


def _load_boj_cache() -> pd.Series:
    """Load BoJ rates from local cache file."""
    cache_path = _get_boj_cache_path()
    if not cache_path.exists():
        return pd.Series(dtype=float, name='JPY_CALL_RATE')
    
    try:
        df = pd.read_csv(cache_path, parse_dates=['date'], index_col='date')
        if 'rate' in df.columns:
            result = df['rate'].dropna()
            result.name = 'JPY_CALL_RATE'
            return result
    except Exception as e:
        logger.warning(f"Failed to load BoJ cache: {e}")
    
    return pd.Series(dtype=float, name='JPY_CALL_RATE')


def _save_boj_cache(data: pd.Series) -> None:
    """Save BoJ rates to local cache file."""
    if data.empty:
        return
    
    cache_path = _get_boj_cache_path()
    try:
        df = pd.DataFrame({'date': data.index, 'rate': data.values})
        df.to_csv(cache_path, index=False)
        logger.debug(f"Saved {len(data)} points to BoJ cache")
    except Exception as e:
        logger.warning(f"Failed to save BoJ cache: {e}")


def _parse_boj_xlsx_rate(content: bytes) -> Optional[float]:
    """Parse BoJ XLSX content and extract the Average rate."""
    from io import BytesIO
    try:
        df = pd.read_excel(BytesIO(content), sheet_name=0, header=None)
        
        # Direct position: row 9 (0-indexed), column 2
        if df.shape[0] > 9 and df.shape[1] > 2:
            raw_val = df.iloc[9, 2]
            rate_value = pd.to_numeric(raw_val, errors='coerce')
            if not pd.isna(rate_value):
                return float(rate_value)
        
        # Fallback: search for 'Average' text
        for idx in range(df.shape[0]):
            cell_val = str(df.iloc[idx, 1]) if df.shape[1] > 1 else ''
            if 'Average' in cell_val or '平均' in cell_val:
                if df.shape[1] > 2:
                    rate_value = pd.to_numeric(df.iloc[idx, 2], errors='coerce')
                    if not pd.isna(rate_value):
                        return float(rate_value)
    except Exception as e:
        logger.debug(f"Failed to parse BoJ XLSX: {e}")
    
    return None


def fetch_boj_xlsx_daily(start_date: str = None, end_date: str = None, use_cache: bool = True) -> pd.Series:
    """
    Fetch BoJ call rate from daily XLSX files with caching.
    
    Only fetches dates that are missing from the cache and within the XLSX availability window
    (post Sept 2025). For historical data, use FRED fallback.
    
    Args:
        start_date: Start date (YYYY-MM-DD), defaults to BOJ_XLSX_START_DATE
        end_date: End date (YYYY-MM-DD), defaults to today
        use_cache: Whether to use local cache (default True)
        
    Returns:
        Series with call rate indexed by date
    """
    base_url = "https://www.boj.or.jp/en/statistics/market/short/mutan/d_release/md"
    
    # Define date range
    xlsx_start = pd.Timestamp(BOJ_XLSX_START_DATE)
    end_dt = pd.Timestamp(end_date) if end_date else pd.Timestamp(datetime.now().date())
    start_dt = pd.Timestamp(start_date) if start_date else xlsx_start
    
    # Clamp to XLSX availability
    start_dt = max(start_dt, xlsx_start)
    
    if start_dt > end_dt:
        return pd.Series(dtype=float, name='JPY_CALL_RATE')
    
    # Load existing cache
    cached = _load_boj_cache() if use_cache else pd.Series(dtype=float)
    
    # Determine which dates we need to fetch
    all_biz_days = pd.date_range(start=start_dt, end=end_dt, freq='B')
    if not cached.empty:
        cached_dates = set(cached.index.normalize())
        missing_dates = [d for d in all_biz_days if d.normalize() not in cached_dates]
    else:
        missing_dates = list(all_biz_days)
    
    # Only fetch recent missing dates (last 60 days to avoid hammering server)
    cutoff = pd.Timestamp(datetime.now().date()) - pd.Timedelta(days=60)
    dates_to_fetch = [d for d in missing_dates if d >= cutoff]
    
    if not dates_to_fetch:
        logger.debug("All XLSX dates already cached, skipping fetch")
        result = cached[(cached.index >= start_dt) & (cached.index <= end_dt)]
        return result if not result.empty else pd.Series(dtype=float, name='JPY_CALL_RATE')
    
    logger.info(f"Fetching {len(dates_to_fetch)} missing BoJ XLSX dates...")
    
    new_rates = {}
    for date in dates_to_fetch:
        year = date.year
        date_str = date.strftime('%Y%m%d')
        xlsx_url = f"{base_url}/{year}/md{date_str}.xlsx"
        
        try:
            response = requests.get(xlsx_url, timeout=10, headers={
                'User-Agent': 'rates_sources/2.0 (requests)'
            })
            
            if response.status_code == 200:
                rate_value = _parse_boj_xlsx_rate(response.content)
                if rate_value is not None:
                    new_rates[date] = rate_value
                    logger.debug(f"BoJ: {date.strftime('%Y-%m-%d')} -> {rate_value:.4f}%")
                    
        except Exception as e:
            logger.debug(f"BoJ XLSX {date_str}: {e}")
    
    # Merge new rates into cache
    if new_rates:
        new_series = pd.Series(new_rates, name='JPY_CALL_RATE')
        new_series.index = pd.to_datetime(new_series.index)
        
        if not cached.empty:
            combined = pd.concat([cached, new_series])
            combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        else:
            combined = new_series.sort_index()
        
        # Save updated cache
        if use_cache:
            _save_boj_cache(combined)
        
        result = combined[(combined.index >= start_dt) & (combined.index <= end_dt)]
        logger.info(f"Fetched {len(new_rates)} new BoJ XLSX points")
        return result
    
    # Return cached data if no new rates
    if not cached.empty:
        result = cached[(cached.index >= start_dt) & (cached.index <= end_dt)]
        return result
    
    return pd.Series(dtype=float, name='JPY_CALL_RATE')


# ============================================================
# FRED FALLBACK (MONTHLY -> DAILY) WITH CACHE
# ============================================================

def fetch_jpy_rate_from_fred(start_year: int = BOJ_START_YEAR, use_cache: bool = True) -> pd.Series:
    """
    Fetch Japan call rate from FRED (monthly, forward-filled to daily).
    
    Uses IRSTCI01JPM156N: Interest Rates: Call Money/Interbank Rate: Total for Japan
    This provides historical data from 1985 onwards until recent months.
    
    Args:
        start_year: Start year for data (default 2000)
        use_cache: Whether to use cache for combined result
        
    Returns:
        Series with rate forward-filled to daily frequency
    """
    try:
        # Direct FRED CSV download (no API key required)
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={FRED_JPY_CALL_RATE}"
        df = pd.read_csv(url, parse_dates=['observation_date'], index_col='observation_date')
        monthly = df.iloc[:, 0]
        
        if monthly is not None and not monthly.empty:
            # Filter by start year
            monthly = monthly[monthly.index.year >= start_year]
            
            # Resample to daily and forward-fill
            daily = monthly.resample('D').ffill()
            daily.name = 'JPY_CALL_RATE'
            logger.info(f"FRED JPY rate: {len(daily)} points ({daily.index.min().strftime('%Y-%m-%d')} to {daily.index.max().strftime('%Y-%m-%d')})")
            return daily
            
    except Exception as e:
        logger.warning(f"FRED JPY rate fetch failed: {e}")
    
    return pd.Series(dtype=float, name='JPY_CALL_RATE')


# ============================================================
# MAIN JPY FETCHER (WITH CACHE & FALLBACKS)
# ============================================================

def fetch_boj_call_rate(start_year: int = BOJ_START_YEAR) -> pd.Series:
    """
    Fetch Japanese Uncollateralized Overnight Call Rate.
    
    Strategy:
    1. Load local cache (historical + recent XLSX data)
    2. For historical data (pre-Sept 2025): Use FRED monthly data (ffill to daily)
    3. For recent data (post-Sept 2025): Fetch BoJ daily XLSX files
    4. Merge sources, preferring XLSX where available (more accurate)
    5. Fallback to constant if all methods fail
    
    Args:
        start_year: Start year for historical data (default 2000)
    
    Returns:
        Series with call rate (%), or constant series if all methods fail
    """
    
    # Try bojdata library first (if installed)
    try:
        import bojdata
        if hasattr(bojdata, 'get_series'):
            series = bojdata.get_series('FM01\'FM080117')
        else:
            series = bojdata.FM08_117 if hasattr(bojdata, 'FM08_117') else None
            
        if series is not None and not series.empty:
            result = series[series.index.year >= start_year].copy()
            result.name = 'JPY_CALL_RATE'
            logger.info(f"Fetched {len(result)} points of JPY call rate via bojdata")
            return result
            
    except ImportError:
        logger.debug("bojdata not installed, using FRED + XLSX")
    except Exception as e:
        logger.warning(f"bojdata fetch failed: {e}")
    
    # Load cached data first
    cached = _load_boj_cache()
    
    # Fetch FRED historical data (2000 to ~present, monthly -> daily ffill)
    fred_data = fetch_jpy_rate_from_fred(start_year=start_year, use_cache=True)
    
    # Fetch recent BoJ XLSX data (Sept 2025 onwards, only missing dates)
    xlsx_data = fetch_boj_xlsx_daily(use_cache=True)
    
    # Merge: FRED for historical, XLSX for recent (XLSX takes priority)
    parts = []
    
    if not fred_data.empty:
        parts.append(fred_data)
    
    if not xlsx_data.empty:
        parts.append(xlsx_data)
    
    if parts:
        combined = pd.concat(parts)
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        combined = combined[combined.index.year >= start_year]
        
        if not combined.empty:
            # Resample to business days and forward-fill gaps
            biz_idx = pd.date_range(start=combined.index.min(), end=combined.index.max(), freq='B')
            combined = combined.reindex(biz_idx).ffill()
            
            combined.name = 'JPY_CALL_RATE'
            logger.info(f"BoJ combined: {len(combined)} points ({combined.index.min().strftime('%Y-%m-%d')} to {combined.index.max().strftime('%Y-%m-%d')})")
            
            # Update cache with combined data
            _save_boj_cache(combined)
            
            return combined
    
    # Final fallback: constant rate
    logger.warning(f"Using constant JPY call rate fallback ({BOJ_CURRENT_POLICY_RATE}%)")
    dates = pd.date_range(
        start=datetime(start_year, 1, 1),
        end=datetime.now(),
        freq='B'
    )
    result = pd.Series(BOJ_CURRENT_POLICY_RATE, index=dates, name='JPY_CALL_RATE')
    return result


# ============================================================
# AGGREGATED RATE FETCHER
# ============================================================

class ForeignRateFetcher:
    """
    Fetches and computes foreign currency benchmark rates.
    
    Supports index-based calculation (USD, GBP) and direct rate fetching (EUR, JPY).
    """
    
    def __init__(self, df_fred: pd.DataFrame = None):
        """
        Initialize with FRED data for index-based calculations.
        
        Args:
            df_fred: DataFrame with FRED data containing:
                     - SOFR_INDEX (SOFRINDEX)
                     - SONIA_INDEX (IUDZOS2)
                     - Optionally ESTR for fallback
        """
        self.df_fred = df_fred if df_fred is not None else pd.DataFrame()
        self._cache = {}
    
    def get_usd_3m_rate(self) -> pd.Series:
        """
        Get USD 3M rate from SOFR Index.
        
        Uses index ratio: R = (Index_t / Index_{t-90} - 1) * 4 * 100
        """
        if 'USD_3M' in self._cache:
            return self._cache['USD_3M']
        
        sofr_index = self.df_fred.get('SOFR_INDEX', pd.Series(dtype=float))
        
        if sofr_index.empty:
            logger.warning("SOFR_INDEX not found in FRED data, USD 3M rate unavailable")
            return pd.Series(dtype=float, name='USD_3M')
        
        rate = compute_rate_from_index(sofr_index, tenor_days=90, annualize_basis=360)
        rate.name = 'USD_3M'
        self._cache['USD_3M'] = rate
        
        logger.info(f"Computed USD 3M rate from SOFRINDEX: latest = {rate.dropna().iloc[-1]:.3f}%")
        return rate
    
    def get_gbp_3m_rate(self) -> pd.Series:
        """
        Get GBP 3M rate from SONIA Compounded Index.
        
        Uses index ratio with 365 day count (GBP convention).
        """
        if 'GBP_3M' in self._cache:
            return self._cache['GBP_3M']
        
        sonia_index = self.df_fred.get('SONIA_INDEX', pd.Series(dtype=float))
        
        if sonia_index.empty:
            logger.warning("SONIA_INDEX not found in FRED data, GBP 3M rate unavailable")
            return pd.Series(dtype=float, name='GBP_3M')
        
        rate = compute_rate_from_index(sonia_index, tenor_days=90, annualize_basis=365)
        rate.name = 'GBP_3M'
        self._cache['GBP_3M'] = rate
        
        logger.info(f"Computed GBP 3M rate from SONIA Index: latest = {rate.dropna().iloc[-1]:.3f}%")
        return rate
    
    def get_eur_3m_rate(self) -> pd.Series:
        """
        Get EUR 3M rate from ECB (primary) or FRED fallback.
        """
        if 'EUR_3M' in self._cache:
            return self._cache['EUR_3M']
        
        # Try ECB SDMX API first
        rate = fetch_ecb_estr_3m()
        
        if rate.empty:
            # Fallback to FRED
            rate = fetch_estr_fallback_from_fred(self.df_fred)
        
        rate.name = 'EUR_3M'
        self._cache['EUR_3M'] = rate
        
        if not rate.empty:
            logger.info(f"EUR 3M rate: latest = {rate.dropna().iloc[-1]:.3f}%")
        return rate
    
    def get_jpy_3m_rate(self, lookback_years: int = 5) -> pd.Series:
        """
        Get JPY "3M" rate from BoJ call rate.
        
        Note: Japan uses overnight call rate even for term calculations,
        as there's no official compounded term rate like SOFR/SONIA.
        """
        if 'JPY_3M' in self._cache:
            return self._cache['JPY_3M']
        
        rate = fetch_boj_call_rate()  # Fallback hierarchy
        rate.name = 'JPY_3M'
        self._cache['JPY_3M'] = rate
        
        if not rate.empty:
            logger.info(f"JPY call rate (BoJ XLSX): latest = {rate.dropna().iloc[-1]:.3f}%")
        return rate
    
    def get_rate_for_currency(self, currency: str) -> pd.Series:
        """
        Get 3M rate for a specific currency.
        
        Args:
            currency: 'USD', 'EUR', 'GBP', 'JPY'
            
        Returns:
            3M rate series (%)
        """
        fetchers = {
            'USD': self.get_usd_3m_rate,
            'EUR': self.get_eur_3m_rate,
            'GBP': self.get_gbp_3m_rate,
            'JPY': self.get_jpy_3m_rate,
        }
        
        if currency not in fetchers:
            logger.warning(f"Unknown currency: {currency}")
            return pd.Series(dtype=float)
        
        return fetchers[currency]()
    
    def sanity_check_usd(self) -> Tuple[bool, float]:
        """
        Sanity check: Compare computed USD 3M vs FRED's SOFR90DAYAVG.
        
        Returns:
            (passes_check, difference_bps)
        """
        computed = self.get_usd_3m_rate()
        published = self.df_fred.get('SOFR_90D_AVG', pd.Series(dtype=float))
        
        if computed.empty or published.empty:
            return False, float('nan')
        
        # Align and compare latest values
        common_idx = computed.index.intersection(published.index)
        if len(common_idx) == 0:
            return False, float('nan')
        
        latest_computed = computed.loc[common_idx[-1]]
        latest_published = published.loc[common_idx[-1]]
        
        diff_bps = abs(latest_computed - latest_published) * 100
        passes = diff_bps < 5  # Within 5 basis points
        
        logger.info(f"USD sanity check: computed={latest_computed:.4f}%, published={latest_published:.4f}%, diff={diff_bps:.1f}bp")
        return passes, diff_bps


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=" * 70)
    print("BOJ CALL RATE FETCHER - FIXED VERSION TEST")
    print("=" * 70)
    
    # Test 1: Direct XLSX fetch (new pattern)
    print("\n[1] Testing BoJ XLSX daily fetch (NEW pattern: md{YYYYMMDD}.xlsx)...")
    xlsx_result = fetch_boj_xlsx_daily(lookback_days=10)
    if not xlsx_result.empty:
        print(f"    [OK] Fetched {len(xlsx_result)} daily points")
        print(f"    Latest: {xlsx_result.iloc[-1]:.4f}% ({xlsx_result.index[-1].strftime('%Y-%m-%d')})")
    else:
        print("    [WARN] XLSX fetch returned empty (may be holiday/weekend)")
    
    # Test 2: FRED fallback
    print("\n[2] Testing FRED fallback...")
    fred_result = fetch_jpy_rate_from_fred()
    if not fred_result.empty:
        print(f"    [OK] FRED data available: {len(fred_result)} points")
        print(f"    Latest: {fred_result.dropna().iloc[-1]:.4f}%")
    else:
        print("    [WARN] FRED fallback not available")
    
    # Test 3: Full function with all fallbacks
    print("\n[3] Testing full fetch_boj_call_rate() with fallbacks...")
    full_result = fetch_boj_call_rate()
    if not full_result.empty:
        print(f"    [OK] Got {len(full_result)} points")
        print(f"    Latest: {full_result.dropna().iloc[-1]:.4f}% ({full_result.dropna().index[-1].strftime('%Y-%m-%d')})")
    else:
        print("    [FAILED] All sources failed")
    
    print("\n" + "=" * 70)
    print("Test complete.")
    print("=" * 70)
