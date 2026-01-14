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

from ..base import BaseDomain, clean_for_json, calculate_zscore


class MacroRegimeDomain(BaseDomain):
    """Macro regime domain."""
    
    @property
    def name(self) -> str:
        return "macro_regime"
    
    def _zscore_roll(self, s: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling Z-score."""
        mean = s.rolling(window, min_periods=window // 4).mean()
        std = s.rolling(window, min_periods=window // 4).std()
        return ((s - mean) / std.replace(0, np.nan))
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process macro regime data with all legacy fields."""
        result = {
            'cli_ref': 'cli.total',  # Reference
            'gli_ref': 'gli.total',
        }
        
        # Get GLI and CLI from kwargs or df
        gli_result = kwargs.get('gli', {})
        cli_result = kwargs.get('cli', {})
        
        gli_total = pd.Series(gli_result.get('total', []), index=df.index) if gli_result else df.get('GLI_TOTAL', pd.Series(0, index=df.index))
        cli_total = pd.Series(cli_result.get('total', []), index=df.index) if cli_result else df.get('CLI', pd.Series(0, index=df.index))
        
        # Liquidity Z
        gli_impulse = gli_total.diff(65)  # 13 weeks
        liquidity_z = self._zscore_roll(gli_impulse).clip(-3, 3)
        
        # Credit Z (CLI is already a Z-score)
        credit_z = cli_total.clip(-3, 3)
        
        # Brakes Z (real rate shock + repo stress)
        brakes_z = pd.Series(0, index=df.index)
        real_rate_shock_4w = pd.Series(0, index=df.index)
        repo_stress = pd.Series(0, index=df.index)
        
        if 'TIPS_REAL_RATE' in df.columns:
            real_rate_shock_4w = df['TIPS_REAL_RATE'].ffill().diff(20)
            brakes_z += self._zscore_roll(real_rate_shock_4w).clip(-3, 3).fillna(0) * 0.5
        
        if 'SOFR' in df.columns and 'IORB' in df.columns:
            repo_stress = (df['SOFR'].ffill() - df['IORB'].ffill()) * 100  # bps
            brakes_z += self._zscore_roll(repo_stress).clip(-3, 3).fillna(0) * 0.5
        
        # Total Z and regime
        total_z = (liquidity_z.fillna(0) * 0.4 + 
                   credit_z.fillna(0) * 0.4 + 
                   (-brakes_z.fillna(0)) * 0.2)
        
        # Regime classification
        def classify_regime(z):
            if pd.isna(z):
                return 0
            if z >= 1.0:
                return 2  # Risk On
            elif z >= 0:
                return 1  # Cautious Bull
            elif z >= -1.0:
                return -1  # Cautious Bear
            else:
                return -2  # Risk Off
        
        regime_code = total_z.apply(classify_regime)
        
        # Transition signal (regime change)
        transition = (regime_code != regime_code.shift(1)).astype(int)
        
        # CLI-GLI divergence
        cli_gli_div = credit_z - liquidity_z
        
        result['score'] = clean_for_json(total_z)
        result['total_z'] = clean_for_json(total_z)  # Legacy alias
        result['regime_code'] = clean_for_json(regime_code)
        result['transition'] = clean_for_json(transition)
        result['liquidity_z'] = clean_for_json(liquidity_z)
        result['credit_z'] = clean_for_json(credit_z)
        result['brakes_z'] = clean_for_json(brakes_z)
        result['cli_gli_divergence'] = clean_for_json(cli_gli_div)
        
        # === CB DIFFUSION (Breadth) ===
        # % of central banks expanding their balance sheets
        cb_cols = [c for c in df.columns if c.startswith('CB_') and c.endswith('_TOTAL')]
        if len(cb_cols) >= 3:
            # Calculate 13-week impulse for each CB
            cb_expanding = pd.DataFrame()
            for col in cb_cols:
                impulse = df[col].ffill().diff(65)
                cb_expanding[col] = (impulse > 0).astype(int)
            
            # Diffusion = % expanding
            cb_diffusion_13w = cb_expanding.mean(axis=1) * 100
            result['cb_diffusion_13w'] = clean_for_json(cb_diffusion_13w)
        else:
            # Fallback: use GLI components if available
            result['cb_diffusion_13w'] = clean_for_json(pd.Series(50, index=df.index))  # Neutral default
        
        # === CB CONCENTRATION (HHI) ===
        # Herfindahl-Hirschman Index of CB contribution to GLI
        if len(cb_cols) >= 3:
            cb_abs_impulse = pd.DataFrame()
            for col in cb_cols:
                impulse = df[col].ffill().diff(65).abs()
                cb_abs_impulse[col] = impulse
            
            # Normalize shares and calculate HHI
            total_abs = cb_abs_impulse.sum(axis=1).replace(0, np.nan)
            shares = cb_abs_impulse.div(total_abs, axis=0)
            hhi = (shares ** 2).sum(axis=1) * 10000  # Standard HHI scale
            result['cb_hhi_13w'] = clean_for_json(hhi)
        else:
            result['cb_hhi_13w'] = clean_for_json(pd.Series(5000, index=df.index))  # Neutral HHI default
        
        # === REPO STRESS ===
        result['repo_stress'] = clean_for_json(repo_stress)
        
        # === REAL RATE SHOCK ===
        result['real_rate_shock_4w'] = clean_for_json(real_rate_shock_4w)
        
        # === RESERVES SPREAD Z ===
        if 'RESERVES' in df.columns:
            reserves = df['RESERVES'].ffill()
            reserves_z = self._zscore_roll(reserves)
            result['reserves_spread_z'] = clean_for_json(reserves_z.clip(-3, 3))
        else:
            result['reserves_spread_z'] = clean_for_json(pd.Series(0, index=df.index))
        
        # === STRESS INDICES ===
        result['stress'] = {}
        if 'ST_LOUIS_STRESS' in df.columns:
            result['stress']['st_louis'] = clean_for_json(df['ST_LOUIS_STRESS'].ffill())
        if 'KANSAS_CITY_STRESS' in df.columns:
            result['stress']['kansas_city'] = clean_for_json(df['KANSAS_CITY_STRESS'].ffill())
        
        return result

