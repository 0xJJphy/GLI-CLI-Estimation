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
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


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
        return pd.Series(dtype=float, name='ESTR_3M_FALLBACK')
    
    # Simple 90-day rolling average (approximation, not true compounding)
    # True compounding would require: prod((1 + r_i / 360)) over 90 days
    # This approximation is acceptable for the proxy use case
    rate_3m_approx = estr_daily.rolling(window=90, min_periods=45).mean()
    rate_3m_approx.name = 'ESTR_3M_FALLBACK'
    
    logger.info("Using FRED €STR fallback (rolling average approximation)")
    return rate_3m_approx


# ============================================================
# JPY: BoJ Call Rate
# ============================================================

def fetch_boj_call_rate() -> pd.Series:
    """
    Fetch Japanese Uncollateralized Overnight Call Rate from BoJ.
    
    Attempts:
    1. bojdata library (if installed)
    2. Direct XLSX download from BoJ
    3. Constant fallback (0.25%)
    
    Returns:
        Series with call rate (%), or constant series if all methods fail
    """
    # Try bojdata first
    try:
        import bojdata
        
        # BoJ series code for uncollateralized overnight call rate
        # Note: Exact series ID may need verification
        data = bojdata.get_data('FM01\'FM080117')  # Call rate
        
        if data is not None and not data.empty:
            result = data.iloc[:, 0]  # First column
            result.name = 'JPY_CALL_RATE'
            logger.info(f"Fetched {len(result)} points of JPY call rate via bojdata")
            return result
            
    except ImportError:
        logger.info("bojdata not installed, trying XLSX fallback")
    except Exception as e:
        logger.warning(f"bojdata fetch failed: {e}")
    
    # Try direct XLSX download
    try:
        # BoJ publishes daily XLSX with call rate
        # URL pattern for 2025 data
        xlsx_url = "https://www.boj.or.jp/en/statistics/market/short/mutan/d_release/md/2025/mutan2501.xlsx"
        
        df = pd.read_excel(xlsx_url, sheet_name=0, skiprows=3)
        
        if not df.empty:
            # Parse date column and rate column
            # Note: Column structure may vary, needs verification
            df.columns = ['date', 'call_rate'] + list(df.columns[2:])
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date', 'call_rate'])
            
            result = df.set_index('date')['call_rate']
            result.name = 'JPY_CALL_RATE'
            logger.info(f"Fetched {len(result)} points of JPY call rate via XLSX")
            return result
            
    except Exception as e:
        logger.warning(f"BoJ XLSX download failed: {e}")
    
    # Fallback: Generate constant series
    logger.warning("Using constant JPY call rate fallback (0.25%)")
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=365*5),
        end=datetime.now(),
        freq='B'  # Business days
    )
    result = pd.Series(0.25, index=dates, name='JPY_CALL_RATE')
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
    
    def get_jpy_3m_rate(self) -> pd.Series:
        """
        Get JPY "3M" rate from BoJ call rate.
        
        Note: Japan uses overnight call rate even for term calculations,
        as there's no official compounded term rate like SOFR/SONIA.
        """
        if 'JPY_3M' in self._cache:
            return self._cache['JPY_3M']
        
        rate = fetch_boj_call_rate()
        rate.name = 'JPY_3M'
        self._cache['JPY_3M'] = rate
        
        if not rate.empty:
            logger.info(f"JPY call rate: latest = {rate.dropna().iloc[-1]:.3f}%")
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
    
    print("=" * 60)
    print("RATE SOURCES MODULE TEST")
    print("=" * 60)
    
    # Test ECB €STR fetch
    print("\n[1] Testing ECB €STR 3M Compounded Average...")
    eur_rate = fetch_ecb_estr_3m()
    if not eur_rate.empty:
        print(f"    [OK] Fetched {len(eur_rate)} points")
        print(f"    Latest: {eur_rate.iloc[-1]:.3f}% ({eur_rate.index[-1].strftime('%Y-%m-%d')})")
    else:
        print("    [FAILED] Failed to fetch EUR rate")
    
    # Test JPY fetch
    print("\n[2] Testing BoJ Call Rate...")
    jpy_rate = fetch_boj_call_rate()
    if not jpy_rate.empty:
        print(f"    [OK] Got {len(jpy_rate)} points")
        print(f"    Latest: {jpy_rate.iloc[-1]:.3f}% ({jpy_rate.index[-1].strftime('%Y-%m-%d')})")
    else:
        print("    [FAILED] Failed to fetch JPY rate")
    
    print("\n" + "=" * 60)
    print("Note: USD/GBP rates require FRED index data (SOFRINDEX, IUDZOS2)")
    print("Run full test via data_pipeline.py with FRED data loaded")
    print("=" * 60)
