"""
CLI Domain - Credit Liquidity Index

Measures credit market conditions through spread and stress indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json, calculate_rocs, calculate_zscore, rolling_percentile
from analytics.regime_v2 import calculate_cli_v2


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
                    # Fix: Use Expanding Window (Lifetime) for Z-Score to match Regime intent
                    # Was defaulting to window=252 which is too volatile/short-term
                    z = calculate_zscore(calc_series, min_periods=100, expanding=True)
                
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
        
        # --- NEW: CLI V2 (Advanced Regime Signal) Integration ---
        # Calculate V2 series using the strict regime_v2 logic
        cli_v2_df = calculate_cli_v2(df)
        
        # Add V2 output series
        result['v2_total'] = clean_for_json(cli_v2_df['CLI_V2'])
        result['v2_percentile'] = clean_for_json(cli_v2_df['CLI_V2_PERCENTILE'])
        
        # Raw component values (Normalized to BPS where applicable)
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
        
        # --- PHASE 2: SIGNAL MIGRATION ---
        result['signals'] = {} # Initialize signals dict

        # Generate signals for each CLI component
        # Using z_scores_inverted where High Z = Good (Bullish) and Low Z = Bad (Bearish)
        for name, z_series in z_scores_inverted.items():
            # Get the last raw value for the signal display (converted to float)
            raw_val = float(components[name].iloc[-1]) if not components[name].empty else 0
            result['signals'][name] = self._calc_cli_signal(name, z_series, raw_val)

        return result
    
    def _calc_cli_signal(self, name: str, z_series: pd.Series, raw_val: float) -> Dict[str, Any]:
        """
        Calculate Signal State based on Z-Score with Rich Text.
        Input z_series is already inverted so that High Z (>0) is Good/Bullish.
        """
        if z_series is None or z_series.empty:
            return {'state': 'neutral', 'label': 'NO DATA', 'desc': 'Insufficient data', 'value': 0}
            
        last_z = z_series.iloc[-1]
        
        if pd.isna(last_z):
            return {'state': 'neutral', 'label': 'NO DATA', 'desc': 'Data is NaN', 'value': 0}
            
        # 1. Determine State (Standard Normal - High is Good/Bullish)
        state = 'neutral'
        if last_z > 1.0:
            state = 'bullish'
        elif last_z > 0.5:
             state = 'bullish' # Leaning Bullish
        elif last_z < -1.5:
            state = 'bearish'
        elif last_z < -0.5:
            state = 'warning'
            
        # 2. component-specific Text Configuration
        # Keys: hy_spread, ig_spread, nfci_credit, nfci_risk, lending_std, vix, move, fx_vol
        
        # Default text
        label = "NORMAL"
        desc = "Metrics are within normal historical range."
        
        # Specific configurations
        # Note: "Bullish" here means Positive Risk Sentiment (Low Stress)
        # "Bearish" means Negative Risk Sentiment (High Stress)
        
        texts = {
            'hy_spread': {
                'bullish': ('RISK ON', 'High Yield spreads are tight, favoring risk assets.'),
                'warning': ('CAUTION', 'Spreads are beginning to widen.'),
                'bearish': ('STRESS', 'HY Spreads blowing out. Credit stress imminent.'),
                'neutral': ('NORMAL', 'Spreads within normal regime.')
            },
            'ig_spread': {
                'bullish': ('STABLE', 'Investment Grade credit is stable.'),
                'warning': ('WIDENING', 'IG spreads showing some pressure.'),
                'bearish': ('DISTRESS', 'Significant stress in high-grade credit.'),
                'neutral': ('NORMAL', 'IG markets functioning normally.')
            },
            'vix': {
                'bullish': ('CALM', 'Volatility is suppressed. Supportive of carry.'),
                'warning': ('ELEVATED', 'VIX is rising above baseline.'),
                'bearish': ('FEAR', 'High volatility regime. Hedging expensive.'),
                'neutral': ('NORMAL', 'Standard volatility environment.')
            },
             'move': {
                'bullish': ('CALM', 'Bond market volatility is low.'),
                'warning': ('NERVOUS', 'Treasury volatility ticking up.'),
                'bearish': ('VOLATILE', 'Extreme bond market volatility.'),
                'neutral': ('NORMAL', 'Bond vol within normal range.')
            },
            'fx_vol': {
                'bullish': ('STABLE', 'Currency markets are quiet.'),
                'warning': ('ACTIVE', 'FX volatility increasing.'),
                'bearish': ('TURBULENT', 'Significant dislocation in FX markets.'),
                'neutral': ('NORMAL', 'FX vol normal.')
            },
            'nfci_credit': {
                'bullish': ('LOOSE', 'Credit conditions are accommodating.'),
                'warning': ('TIGHTENING', 'Credit conditions starting to tighten.'),
                'bearish': ('TIGHT', 'Financial conditions explicitly tight.'),
                'neutral': ('NEUTRAL', 'Balanced financial conditions.')
            },
             'lending_std': {
                'bullish': ('EASING', 'Banks are easing lending standards.'),
                'warning': ('OBSERVING', 'Banks marginally tightening.'),
                'bearish': ('RESTRICTIVE', 'Banks aggressively tightening credit.'),
                'neutral': ('NEUTRAL', 'Lending standards unchanged.')
            }
        }
        
        # Fallback for nfci_risk or others
        default_texts = {
            'bullish': ('POSITIVE', 'Conditions represent a tailwind.'),
            'warning': ('WATCH', 'Conditions deteriorating slightly.'),
            'bearish': ('NEGATIVE', 'Conditions represent a headwind.'),
            'neutral': ('NEUTRAL', 'Conditions are neutral.')
        }

        # Select Text
        config = texts.get(name, default_texts)
        if state in config:
            label, desc = config[state]
        else:
            # Fallback if state matches nothing (unlikely)
            label, desc = default_texts.get(state, ('UNKNOWN', 'Signal state undefined.'))

        return {
            'state': state,
            'label': label,
            'desc': desc,
            'value': float(raw_val),
            'percentile': 0 # Optional
        }
