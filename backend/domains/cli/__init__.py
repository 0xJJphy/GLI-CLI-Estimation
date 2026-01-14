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
        }
        
        # Weights for CLI calculation
        weights = {
            'hy_spread': 0.25,
            'ig_spread': 0.15,
            'nfci_credit': 0.20,
            'nfci_risk': 0.20,
            'lending_std': 0.10,
            'vix': 0.10
        }
        
        # Calculate Z-scores
        z_scores = {}
        for name, series in components.items():
            if series is not None and not series.empty:
                series = series.ffill()
                z = calculate_zscore(series, 252)
                # Invert spread-type indicators (higher = worse conditions)
                if name in ['hy_spread', 'ig_spread', 'lending_std', 'vix', 'nfci_credit', 'nfci_risk']:
                    z = -z
                z_scores[name] = z
        
        # Calculate composite CLI
        cli_total = pd.Series(0.0, index=df.index)
        total_weight = 0
        
        for name, z in z_scores.items():
            weight = weights.get(name, 0)
            cli_total += z.fillna(0) * weight
            total_weight += weight
        
        if total_weight > 0:
            cli_total = cli_total / total_weight
        
        result['total'] = clean_for_json(cli_total)
        result['percentile'] = clean_for_json(rolling_percentile(cli_total, window=1260))
        result['rocs'] = {k: clean_for_json(v) for k, v in calculate_rocs(cli_total).items()}
        
        # Raw component values
        result['raw'] = {
            'hy_spread': clean_for_json(components['hy_spread'].ffill()),
            'ig_spread': clean_for_json(components['ig_spread'].ffill()),
            'nfci_credit': clean_for_json(components['nfci_credit'].ffill()),
            'nfci_risk': clean_for_json(components['nfci_risk'].ffill()),
            'lending_std': clean_for_json(components['lending_std'].ffill()),
            'vix': clean_for_json(components['vix'].ffill()),
        }
        
        # Component Z-scores
        result['components'] = {
            f'{name}_z': clean_for_json(z) for name, z in z_scores.items()
        }
        
        result['weights'] = weights
        
        return result
