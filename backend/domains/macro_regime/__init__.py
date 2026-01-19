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
from analytics.regime_v2 import (
    calculate_macro_regime_v2a, 
    calculate_macro_regime_v2b, 
    calculate_stress_historical,
    calculate_cli_v2
)


class MacroRegimeDomain(BaseDomain):
    """Macro regime domain."""
    
    @property
    def name(self) -> str:
        return "macro_regime"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process macro regime data with V2A and V2B logic."""
        # DEBUG: Check columns
        if 'GLI_TOTAL' not in df.columns:
             print("CRITICAL ERROR: GLI_TOTAL missing from MacroRegimeDomain df input!")
             print("Columns:", df.columns.tolist())

        # Calculate CLI V2 first (dependency for regimes)
        cli_v2_df = calculate_cli_v2(df)
        
        # Inject CLI V2 into df so distinct regime functions can use it if they check for 'CLI_V2'
        # We use .copy() to avoid SettingWithCopy warnings if df is a slice, though typically it's a new frame here.
        df['CLI_V2'] = cli_v2_df['CLI_V2']

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
            'cli_v2': clean_for_json(cli_v2_df['CLI_V2']),
            # Top-level legacy aliases for compatibility
            'score': v2a_clean.get('score', []),
            'regime_code': v2a_clean.get('regime_code', []),
            'total_z': v2a_clean.get('total_z', []),
        }
        
        # Add diagnostic fields from v2a to top level if needed
        for k in ['liquidity_z', 'credit_z', 'brakes_z', 'cli_gli_divergence', 
                  'cb_diffusion_13w', 'cb_hhi_13w']:
            if k in v2a_clean:
                # SPECIAL HANDLING: cli_gli_divergence
                # If the last values are 0 (likely due to ffill padding of GLI vs daily CLI),
                # we should set them to None so the frontend shows the last REAL value, not 0.
                if k == 'cli_gli_divergence':
                     series = v2a_data[k]
                     # Find last non-zero valid index
                     last_valid_idx = None
                     if not series.empty:
                         # Check backwards for first non-zero
                         for i in range(len(series)-1, -1, -1):
                             val = series.iloc[i]
                             if pd.notnull(val) and abs(val) > 1e-6: # Treat near-zero as zero
                                 last_valid_idx = i
                                 break
                     
                     # If we found a valid end, everything after it should be None
                     clean_series = clean_for_json(series)
                     if last_valid_idx is not None and last_valid_idx < len(clean_series) - 1:
                         # Replace trailing zeros/values with None
                         for i in range(last_valid_idx + 1, len(clean_series)):
                             clean_series[i] = None
                     
                     result[k] = clean_series
                else:
                    result[k] = v2a_clean[k]
                
        return result


