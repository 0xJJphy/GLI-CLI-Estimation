"""
Offshore Liquidity Domain - Eurodollar stress, XCCY basis

Contains:
- OBFR-EFFR spread (offshore USD funding stress)
- Fed CB Liquidity Swaps
- XCCY basis (reference to existing module)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json, calculate_zscore


class OffshoreDomain(BaseDomain):
    """Offshore liquidity domain."""
    
    @property
    def name(self) -> str:
        return "offshore"
    
    def _calc_percentile(self, series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling percentile."""
        def percentile_rank(arr):
            if len(arr) < window // 2:
                return np.nan
            current = arr[-1]
            if np.isnan(current):
                return np.nan
            return (arr[:-1] < current).sum() / (len(arr) - 1) * 100
        return series.rolling(window, min_periods=window // 2).apply(percentile_rank, raw=True)
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process offshore liquidity data."""
        result = {}
        
        # OBFR-EFFR spread (offshore vs onshore funding cost)
        if 'OBFR' in df.columns and 'EFFR' in df.columns:
            obfr = df['OBFR'].ffill()
            effr = df['EFFR'].ffill()
            spread_bps = (obfr - effr) * 100
            
            result['obfr_effr_spread'] = clean_for_json(spread_bps)
            result['obfr_effr_spread_z'] = clean_for_json(calculate_zscore(spread_bps, 252))
            result['obfr'] = clean_for_json(obfr)
            result['effr'] = clean_for_json(effr)
        
        # CB Swaps
        if 'CB_LIQ_SWAPS' in df.columns or 'FED_CB_SWAPS' in df.columns:
            swaps_col = 'CB_LIQ_SWAPS' if 'CB_LIQ_SWAPS' in df.columns else 'FED_CB_SWAPS'
            swaps = df[swaps_col].ffill() / 1e9  # Billions
            result['cb_swaps'] = clean_for_json(swaps)
            result['cb_swaps_active'] = clean_for_json((swaps > 0.1).astype(int))
        
        # SOFR-IORB spread (repo market stress)
        if 'SOFR' in df.columns and 'IORB' in df.columns:
            sofr = df['SOFR'].ffill()
            iorb = df['IORB'].ffill()
            repo_spread = (sofr - iorb) * 100  # bps
            
            result['sofr_iorb_spread'] = clean_for_json(repo_spread)
            result['sofr_iorb_spread_z'] = clean_for_json(calculate_zscore(repo_spread, 252))
        
        # SOFR Volume
        if 'SOFR_VOLUME' in df.columns:
            vol = df['SOFR_VOLUME'].ffill()
            result['sofr_volume'] = clean_for_json(vol)
            result['sofr_volume_roc_5d'] = clean_for_json(vol.pct_change(5) * 100)
        
        # Composite stress score
        stress_score = pd.Series(0, index=df.index)
        components = 0
        
        if 'obfr_effr_spread_z' in result:
            obfr_z = pd.Series(result['obfr_effr_spread_z'], index=df.index)
            stress_score += self._calc_percentile(obfr_z) * 0.7
            components += 0.7
        
        if 'cb_swaps' in result:
            swaps = pd.Series(result['cb_swaps'], index=df.index)
            swaps_pct = self._calc_percentile(swaps)
            stress_score += swaps_pct * 0.3
            components += 0.3
        
        if components > 0:
            result['stress_score'] = clean_for_json(stress_score / components)
        
        # XCCY basis is calculated in offshore_liquidity.py module
        # Reference it rather than duplicate
        result['xccy_basis_ref'] = 'offshore_liquidity_module'
        
        return result
