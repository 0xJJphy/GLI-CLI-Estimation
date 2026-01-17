"""
CLI Domain - Credit Liquidity Index

Measures credit market conditions through spread and stress indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json, calculate_rocs, calculate_zscore, rolling_percentile


class CLIDomain(BaseDomain):
    """
    Credit Liquidity Index domain.
    
    Components:
    - HY Spread (High Yield)
    - IG Spread (Investment Grade)
    - NFCI Credit/Risk sub-indices
    - Lending Standards
    - VIX
    """
    
    @property
    def name(self) -> str:
        return "cli"
    
    def _calc_component_zscore(self, series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate Z-score for CLI component (inverted for spreads)."""
        if series is None or series.empty:
            return pd.Series(dtype=float)
        z = calculate_zscore(series, window)
        # Higher spread = tighter credit = negative CLI, so invert
        return -z
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process CLI data."""
        result = {}
        
        # Component Z-scores (inverted where higher = worse)
        components = {
            'hy_spread': df.get('HY_SPREAD', pd.Series(dtype=float)),
            'ig_spread': df.get('IG_SPREAD', pd.Series(dtype=float)),
            'nfci_credit': df.get('NFCI_CREDIT', pd.Series(dtype=float)),
            'nfci_risk': df.get('NFCI_RISK', pd.Series(dtype=float)),
            'lending_std': df.get('LENDING_STD', pd.Series(dtype=float)),
            'vix': df.get('VIX', pd.Series(dtype=float)),
            'move': df.get('MOVE', pd.Series(dtype=float)),
            'fx_vol': df.get('FX_VOL', pd.Series(dtype=float)),
        }
        
        # Weights for CLI calculation
        weights = {
            'hy_spread': 0.20,
            'ig_spread': 0.10,
            'nfci_credit': 0.15,
            'nfci_risk': 0.15,
            'lending_std': 0.10,
            'vix': 0.10,
            'move': 0.10,
            'fx_vol': 0.10
        }
        
        # Calculate Z-scores
        z_scores_raw = {}     # For output (High = Stress)
        z_scores_inverted = {} # For CLI calculation (High = Good)
        
        # CRITICAL: Filter pre-2000 data to match legacy regime distribution
        cutoff_date = pd.Timestamp('2000-01-01')
        
        for name, series in components.items():
            if series is not None and not series.empty:
                # Ensure 1970 alignment but mask pre-2000 for calculation context
                calc_series = series.copy()
                calc_series.loc[calc_series.index < cutoff_date] = np.nan
                calc_series = calc_series.ffill()
                
                # Calculate Raw Z-Score (Higher Value -> Higher Z)
                if name in ['nfci_credit', 'nfci_risk']:
                    # NFCI is already a Z-score (centered at 0, std=1 typically)
                    # Legacy regime_v2 just uses the raw value (inverted)
                    z = calc_series
                else:
                    z = calculate_zscore(calc_series, window=252)
                
                z_scores_raw[name] = z
                
                # Invert spread-type indicators (Higher Value = Worse Condition = Negative Score)
                if name in ['hy_spread', 'ig_spread', 'lending_std', 'vix', 'nfci_credit', 'nfci_risk', 'move', 'fx_vol']:
                    z_scores_inverted[name] = -z
                else:
                    z_scores_inverted[name] = z
        
        # Calculate composite CLI using Inverted scores (Higher = Better)
        cli_total = pd.Series(0.0, index=df.index)
        total_weight = 0
        
        for name, z in z_scores_inverted.items():
            weight = weights.get(name, 0)
            cli_total += z.fillna(0) * weight
            total_weight += weight
        
        if total_weight > 0:
            cli_total = cli_total / total_weight
        
        result['total'] = clean_for_json(cli_total)
        result['percentile'] = clean_for_json(rolling_percentile(cli_total, min_periods=100, expanding=True))
        result['rocs'] = {k: clean_for_json(v) for k, v in calculate_rocs(cli_total).items()}
        
        # Raw component values
        result['raw'] = {
            'hy_spread': clean_for_json(components['hy_spread'].ffill()),
            'ig_spread': clean_for_json(components['ig_spread'].ffill()),
            'nfci_credit': clean_for_json(components['nfci_credit'].ffill()),
            'nfci_risk': clean_for_json(components['nfci_risk'].ffill()),
            'lending_std': clean_for_json(components['lending_std'].ffill()),
            'vix': clean_for_json(components['vix'].ffill()),
            'move': clean_for_json(components['move'].ffill()),
            'fx_vol': clean_for_json(components['fx_vol'].ffill()),
        }
        
        # Component Z-scores and Percentiles
        result['components'] = {}
        for name, z in z_scores_raw.items():
            result['components'][f'{name}_z'] = clean_for_json(z)
            
            # Calculate percentile for component (raw series)
            raw_series = components[name].copy()
            raw_series.loc[raw_series.index < cutoff_date] = np.nan
            raw_series = raw_series.ffill()
            
            # Use expanding percentile for components too
            pct = rolling_percentile(raw_series, min_periods=100, expanding=True)
            result['components'][f'{name}_pct'] = clean_for_json(pct)
        
        result['weights'] = weights
        
        return result
