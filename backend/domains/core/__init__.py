"""
Shared Domain - Core data used across multiple tabs

This domain contains data that is referenced by multiple other domains
and tabs to avoid duplication:

SHARED DATA:
- dates: Global date index (used by ALL tabs)
- btc_price: Bitcoin price series (used by BTC, Stablecoins, Narratives, Currencies)
- gli_components: CB balance sheets (used by GLI, US System, GlobalFlows)

Other domains reference this shared data by key rather than duplicating.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

from ..base import BaseDomain, clean_for_json, calculate_rocs, rolling_percentile


class SharedDomain(BaseDomain):
    """
    Shared data domain.
    
    Contains:
    - dates: Global date index
    - btc: Bitcoin price (used by multiple tabs as overlay)
    - central_banks: Individual CB balance sheets in USD (used by GLI, M2, US System)
    """
    
    @property
    def name(self) -> str:
        return "shared"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Extract shared data.
        
        Args:
            df: Main DataFrame
        
        Returns:
            Dict with shared reference data
        """
        result = {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'metadata': {
                'data_start': df.index.min().strftime('%Y-%m-%d'),
                'data_end': df.index.max().strftime('%Y-%m-%d'),
                'total_rows': len(df),
            }
        }
        
        # BTC price (referenced by Stablecoins, Narratives, Currencies, BTC Analysis)
        if 'BTC' in df.columns:
            btc = df['BTC'].ffill()
            result['btc'] = {
                'price': clean_for_json(btc),
                'rocs': {k: clean_for_json(v) for k, v in calculate_rocs(btc).items()}
            }
        
        # Central Bank balance sheets in USD (referenced by GLI, US System, M2)
        cb_cols = [
            ('FED_USD', 'fed'), ('ECB_USD', 'ecb'), ('BOJ_USD', 'boj'),
            ('BOE_USD', 'boe'), ('PBOC_USD', 'pboc'), ('BOC_USD', 'boc'),
            ('RBA_USD', 'rba'), ('SNB_USD', 'snb'), ('BOK_USD', 'bok'),
            ('RBI_USD', 'rbi'), ('CBR_USD', 'cbr'), ('BCB_USD', 'bcb'),
            ('RBNZ_USD', 'rbnz'), ('SR_USD', 'sr'), ('BNM_USD', 'bnm')
        ]
        
        result['central_banks'] = {}
        for col, name in cb_cols:
            if col in df.columns:
                result['central_banks'][name] = clean_for_json(df[col].ffill())
        
        return result


class GLIDomain(BaseDomain):
    """
    Global Liquidity Index domain.
    
    Aggregates central bank balance sheets into GLI metrics.
    References: shared.central_banks (no duplication of raw CB data)
    """
    
    @property
    def name(self) -> str:
        return "gli"
    
    def _calc_constant_fx_gli(self, df: pd.DataFrame) -> pd.Series:
        """Calculate GLI with constant FX rates (last available)."""
        # Use last known FX rates for all calculations
        fx_cols = ['EURUSD', 'JPYUSD', 'GBPUSD', 'CNYUSD', 'CADUSD', 'AUDUSD', 
                   'CHFUSD', 'INRUSD', 'RUBUSD', 'BRLUSD', 'KRWUSD', 'NZDUSD',
                   'SEKUSD', 'MYRUSD']
        
        last_fx = {col: df[col].ffill().iloc[-1] if col in df.columns else 1.0 
                   for col in fx_cols}
        
        # Sum CBs with constant FX (simplified - Fed already in USD)
        constant_gli = pd.Series(0.0, index=df.index)
        
        if 'FED_USD' in df.columns:
            constant_gli += df['FED_USD'].ffill()
        
        # Add other CBs (already converted to USD in preprocessing)
        for col in ['ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD', 'BOC_USD', 
                    'RBA_USD', 'SNB_USD', 'BOK_USD', 'RBI_USD', 'CBR_USD',
                    'BCB_USD', 'RBNZ_USD', 'SR_USD', 'BNM_USD']:
            if col in df.columns:
                constant_gli += df[col].ffill()
        
        return constant_gli
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Process GLI data.
        
        NOTE: Does NOT duplicate CB balance sheets - those are in shared domain.
        Only computes aggregates and derived metrics.
        """
        result = {
            'dates_ref': 'shared',  # Reference to shared domain for dates
            'cb_data_ref': 'shared.central_banks',  # Reference to shared CB data
        }
        
        # Calculate GLI_TOTAL
        cb_cols = ['FED_USD', 'ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD',
                   'BOC_USD', 'RBA_USD', 'SNB_USD', 'BOK_USD', 'RBI_USD',
                   'CBR_USD', 'BCB_USD', 'RBNZ_USD', 'SR_USD', 'BNM_USD']
        
        gli_total = pd.Series(0.0, index=df.index)
        active_cbs = 0
        
        for col in cb_cols:
            if col in df.columns and df[col].notna().any():
                gli_total += df[col].ffill()
                active_cbs += 1
        
        result['total'] = clean_for_json(gli_total)
        result['constant_fx'] = clean_for_json(self._calc_constant_fx_gli(df))
        result['cb_count'] = active_cbs
        
        # ROCs
        result['rocs'] = {k: clean_for_json(v) for k, v in calculate_rocs(gli_total).items()}
        
        # Bank-level ROCs and impacts
        result['bank_rocs'] = {}
        result['weights'] = {}
        
        latest_gli = gli_total.iloc[-1] if gli_total.iloc[-1] > 0 else 1.0
        
        for col in cb_cols:
            if col in df.columns and df[col].notna().any():
                bank_name = col.replace('_USD', '').lower()
                series = df[col].ffill()
                
                # ROCs
                rocs = calculate_rocs(series)
                
                # Impact on GLI
                impacts = {}
                for period, days in [('1m', 22), ('3m', 66), ('6m', 132), ('1y', 252)]:
                    delta = series - series.shift(days)
                    impact = (delta / gli_total.shift(days)) * 100
                    impacts[f'impact_{period}'] = impact
                
                result['bank_rocs'][bank_name] = {
                    **{k: clean_for_json(v) for k, v in rocs.items()},
                    **{k: clean_for_json(v) for k, v in impacts.items()}
                }
                
                # Weight
                result['weights'][bank_name] = float(series.iloc[-1] / latest_gli * 100)
        
        return result


class USSystemDomain(BaseDomain):
    """
    US System domain - Fed balance sheet components and net liquidity.
    
    References: shared.central_banks.fed (no duplication)
    
    Contains:
    - Net Liquidity calculation
    - RRP, TGA, Bank Reserves
    - Repo operations
    - System metrics
    """
    
    @property
    def name(self) -> str:
        return "us_system"
    
    def _calc_zscore(self, series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling Z-score."""
        mean = series.rolling(window, min_periods=window // 4).mean()
        std = series.rolling(window, min_periods=window // 4).std()
        return ((series - mean) / std.replace(0, np.nan))
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Process US System data.
        
        NOTE: Fed balance sheet data is in shared domain.
        This domain computes net liquidity and derived metrics.
        """
        result = {
            'fed_ref': 'shared.central_banks.fed',  # Reference, not duplicate
        }
        
        # Core components
        fed_usd = df['FED_USD'].ffill() if 'FED_USD' in df.columns else pd.Series(0.0, index=df.index)
        rrp_usd = df['RRP_USD'].ffill() if 'RRP_USD' in df.columns else pd.Series(0.0, index=df.index)
        tga_usd = df['TGA_USD'].ffill() if 'TGA_USD' in df.columns else pd.Series(0.0, index=df.index)
        reserves = df['BANK_RESERVES'].ffill() if 'BANK_RESERVES' in df.columns else pd.Series(0.0, index=df.index)
        
        # Net Liquidity = Fed - TGA - RRP
        net_liquidity = fed_usd - tga_usd - rrp_usd
        
        result['net_liquidity'] = clean_for_json(net_liquidity)
        result['rrp'] = clean_for_json(rrp_usd)
        result['tga'] = clean_for_json(tga_usd)
        result['bank_reserves'] = clean_for_json(reserves)
        
        # ROCs
        result['net_liq_rocs'] = {k: clean_for_json(v) for k, v in calculate_rocs(net_liquidity).items()}
        
        # System metrics
        result['metrics'] = {
            # RRP drain rate and weeks to empty
            'rrp_drain_weekly': clean_for_json((rrp_usd - rrp_usd.shift(5)).rolling(4).mean()),
            'rrp_weeks_to_empty': clean_for_json(rrp_usd / ((rrp_usd - rrp_usd.shift(5)).rolling(4).mean().abs() + 0.001)),
            # TGA Z-score
            'tga_zscore': clean_for_json(self._calc_zscore(tga_usd, 252)),
            # Fed momentum
            'fed_momentum': clean_for_json(fed_usd.ewm(span=60).mean() - fed_usd.ewm(span=130).mean()),
            # Absolute deltas
            'rrp_delta_4w': clean_for_json(rrp_usd - rrp_usd.shift(20)),
            'rrp_delta_13w': clean_for_json(rrp_usd - rrp_usd.shift(65)),
            'tga_delta_4w': clean_for_json(tga_usd - tga_usd.shift(20)),
            'tga_delta_13w': clean_for_json(tga_usd - tga_usd.shift(65)),
            'netliq_delta_4w': clean_for_json(net_liquidity - net_liquidity.shift(20)),
            'netliq_delta_13w': clean_for_json(net_liquidity - net_liquidity.shift(65)),
        }
        
        # Repo operations (if available)
        if 'SRF_USAGE' in df.columns:
            srf = df['SRF_USAGE'].ffill()
            net_repo = srf - rrp_usd
            result['repo_operations'] = {
                'srf_usage': clean_for_json(srf),
                'rrp_usage': clean_for_json(rrp_usd),
                'net_repo': clean_for_json(net_repo),
                'net_repo_zscore': clean_for_json(self._calc_zscore(net_repo, 252)),
            }
            
        # Repo Stress (SOFR - IORB Spread)
        # Legacy dashboardData.repo_stress logic
        sofr = df['SOFR'].ffill() if 'SOFR' in df.columns else pd.Series(0.0, index=df.index)
        iorb = df['IORB'].ffill() if 'IORB' in df.columns else pd.Series(0.0, index=df.index)
        srf_rate = df['SRF_RATE'].ffill() if 'SRF_RATE' in df.columns else pd.Series(0.0, index=df.index)
        rrp_award = df['RRP_AWARD'].ffill() if 'RRP_AWARD' in df.columns else pd.Series(0.0, index=df.index)
        repo_spread = sofr - iorb
        
        result['repo_stress'] = {
            'total': clean_for_json(repo_spread), # Main spread value
            'sofr': clean_for_json(sofr),
            'iorb': clean_for_json(iorb),
            'srf_rate': clean_for_json(srf_rate),
            'rrp_award': clean_for_json(rrp_award),
            'z_score': clean_for_json(self._calc_zscore(repo_spread, 252))
        }
        
        # Financial Stress Indices
        # St. Louis Fed Financial Stress Index (ST_LOUIS_STRESS)
        if 'ST_LOUIS_STRESS' in df.columns:
            stlfsi = df['ST_LOUIS_STRESS'].ffill()
            result['st_louis_stress'] = {
                'total': clean_for_json(stlfsi),
                'z_score': clean_for_json(self._calc_zscore(stlfsi, 1260)), # 5yr window
                'percentile': clean_for_json(rolling_percentile(stlfsi, 1260))
            }
            
        # Kansas City Financial Stress Index (KANSAS_CITY_STRESS)
        if 'KANSAS_CITY_STRESS' in df.columns:
            kcfsi = df['KANSAS_CITY_STRESS'].ffill()
            result['kansas_city_stress'] = {
                'total': clean_for_json(kcfsi),
                'z_score': clean_for_json(self._calc_zscore(kcfsi, 1260)), # 5yr window
                'percentile': clean_for_json(rolling_percentile(kcfsi, 1260))
            }
        
        return result


class M2Domain(BaseDomain):
    """
    Global M2 Money Supply domain.
    
    Aggregates M2 from major economies, converted to USD.
    """
    
    @property
    def name(self) -> str:
        return "m2"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process M2 data."""
        result = {'economies': {}}
        
        # M2 columns and their FX conversion pairs
        m2_config = {
            'USM2': ('us', None, 1e12),  # Already in USD, convert to trillions
            'EUM2': ('eu', 'EURUSD', 1e12),
            'CNM2': ('cn', 'CNYUSD', 1e12),
            'JPM2': ('jp', 'JPYUSD', 1e12),
            'GBM2': ('gb', 'GBPUSD', 1e12),
            'CAM2': ('ca', 'CADUSD', 1e12),
            'AUM3': ('au', 'AUDUSD', 1e12),
            'INM2': ('in', 'INRUSD', 1e12),
            'CHM2': ('ch', 'CHFUSD', 1e12),
            'RUM2': ('ru', 'RUBUSD', 1e12),
            'BRM2': ('br', 'BRLUSD', 1e12),
            'KRM2': ('kr', 'KRWUSD', 1e12),
            'MXM2': ('mx', 'MXNUSD', 1e12),
            'IDM2': ('id', 'IDRUSD', 1e12),
            'ZAM2': ('za', 'ZARUSD', 1e12),
            'MYM2': ('my', 'MYRUSD', 1e12),
            'SEM2': ('se', 'SEKUSD', 1e12),
        }
        
        m2_total = pd.Series(0.0, index=df.index)
        
        for col, (name, fx_col, divisor) in m2_config.items():
            if col in df.columns:
                m2_local = df[col].ffill() / divisor
                
                # Convert to USD
                if fx_col and fx_col in df.columns:
                    fx_rate = df[fx_col].ffill()
                    m2_usd = m2_local * fx_rate
                else:
                    m2_usd = m2_local
                
                result['economies'][name] = clean_for_json(m2_usd)
                if name == 'gb':
                    result['economies']['uk'] = result['economies']['gb']
                m2_total += m2_usd.fillna(0)
        
        result['total'] = clean_for_json(m2_total)
        result['rocs'] = {k: clean_for_json(v) for k, v in calculate_rocs(m2_total).items()}
        
        # Economy-level ROCs and weights
        result['economy_rocs'] = {}
        result['weights'] = {}
        
        latest_m2 = m2_total.iloc[-1] if m2_total.iloc[-1] > 0 else 1.0
        
        for name, series_data in result['economies'].items():
            if series_data:
                series = pd.Series(series_data, index=df.index)
                rocs = calculate_rocs(series)
                result['economy_rocs'][name] = {k: clean_for_json(v) for k, v in rocs.items()}
                last_val = series.iloc[-1] if not pd.isna(series.iloc[-1]) else 0
                result['weights'][name] = float(last_val / latest_m2 * 100)
        
        # Add UK as alias for GB for frontend compatibility
        if 'gb' in result['economies']:
            result['economies']['uk'] = result['economies']['gb']
            result['economy_rocs']['uk'] = result['economy_rocs']['gb']
            result['weights']['uk'] = result['weights']['gb']
        
        return result
