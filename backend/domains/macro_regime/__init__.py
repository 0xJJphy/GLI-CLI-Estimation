"""
Macro Regime Domain - Combined regime scoring

Contains:
- Multi-factor macro regime (liquidity + credit + brakes)
- CLI-GLI divergence
- Stress indices aggregation
- Transition signals
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json
from analytics.regime_v2 import calculate_macro_regime_v2a, calculate_macro_regime_v2b, calculate_stress_historical


class MacroRegimeDomain(BaseDomain):
    """Macro regime domain."""
    
    @property
    def name(self) -> str:
        return "macro_regime"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process macro regime data with V2A and V2B logic."""
        # Calculate V2A (Inflation-Aware) and V2B (Growth-Aware)
        v2a_data = calculate_macro_regime_v2a(df)
        v2b_data = calculate_macro_regime_v2b(df)
        stress_historical = calculate_stress_historical(df)
        
        # Clean for JSON
        v2a_clean = {k: clean_for_json(v) for k, v in v2a_data.items()}
        v2b_clean = {k: clean_for_json(v) for k, v in v2b_data.items()}
        stress_clean = {k: clean_for_json(v) for k, v in stress_historical.items()}
        
        # Combine into result
        result = {
            'v2a': v2a_clean,
            'v2b': v2b_clean,
            'stress_historical': stress_clean,
            # CLI data for comparison chart
            'cli_v1': clean_for_json(df.get('CLI', pd.Series(0, index=df.index))),
            'cli_v2': clean_for_json(df.get('CLI_V2', pd.Series(0, index=df.index))),
            # Top-level legacy aliases for compatibility
            'score': v2a_clean.get('score', []),
            'regime_code': v2a_clean.get('regime_code', []),
            'total_z': v2a_clean.get('total_z', []),
        }
        
        # Add diagnostic fields from v2a to top level if needed
        for k in ['liquidity_z', 'credit_z', 'brakes_z', 'cli_gli_divergence']:
            if k in v2a_clean:
                result[k] = v2a_clean[k]
                
        return result


