"""
Crypto Domain - Bitcoin analysis, crypto regimes, narratives

Contains:
- BTC fair value models (referenced from shared.btc for price)
- Crypto market regimes
- Narrative rotation (DeFi, Meme, AI, L1, DePIN, RWA)
- CAI (Crypto Altseason Index)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
from scipy.stats import norm

from ..base import BaseDomain, clean_for_json, calculate_rocs


class CryptoDomain(BaseDomain):
    """
    Crypto analytics domain.
    
    References:
    - shared.btc: Bitcoin price (no duplication)
    - stablecoins.total: Total stablecoin supply
    """
    
    @property
    def name(self) -> str:
        return "crypto"
    
    def _calculate_regimes(self, df: pd.DataFrame, m_stable: pd.Series) -> Dict[str, Any]:
        """Calculate crypto market regimes."""
        # Data prep
        m_total = df['TOTAL_MCAP'].ffill() / 1e9 if 'TOTAL_MCAP' in df.columns else pd.Series(1, index=df.index)
        m_btc = df['BTC_MCAP'].ffill() / 1e9 if 'BTC_MCAP' in df.columns else pd.Series(1, index=df.index)
        
        # Risk assets = Total - BTC - Stables
        m_risk = (m_total - m_btc - m_stable).clip(lower=0.1)
        
        # Log ratios
        rs_risk_btc = np.log(m_risk / m_btc)
        rs_stable_risk = np.log(m_stable / m_risk)
        
        # Momentum
        delta_rs_risk = rs_risk_btc.diff(30)
        delta_rs_stable = rs_stable_risk.diff(30)
        
        # Returns
        r_total = m_total.pct_change(30)
        r_stable = m_stable.pct_change(30)
        r_btc = m_btc.pct_change(30)
        
        # Regime classification
        T_CAPITULATION = -0.15
        T_MOMENTUM = 0.005
        
        is_capitulation = (r_total < T_CAPITULATION) & (r_stable < -0.01)
        is_stable_refuge = (r_total < 0) & (delta_rs_stable > T_MOMENTUM)
        is_flight_to_quality = (r_total < 0) & (delta_rs_risk < -T_MOMENTUM)
        is_alt_season = (delta_rs_risk > T_MOMENTUM) & (r_stable >= 0)
        is_btc_season = (delta_rs_risk < -T_MOMENTUM) & (r_btc > 0)
        
        regime = np.where(is_capitulation, "Capitulation",
                 np.where(is_stable_refuge, "Stable Refuge",
                 np.where(is_flight_to_quality, "Flight to Quality",
                 np.where(is_alt_season, "Alt Season",
                 np.where(is_btc_season, "BTC Season", "Neutral")))))
        
        # CAI (Altseason Index)
        rs_90 = rs_risk_btc.diff(90)
        rs_90_clean = rs_90.astype(float).replace([np.inf, -np.inf], np.nan)
        mu = rs_90_clean.expanding(min_periods=90).mean()
        sd = rs_90_clean.expanding(min_periods=90).std().replace(0, np.nan)
        z_rs_90 = (rs_90_clean - mu) / sd
        cai_raw = pd.Series(norm.cdf(z_rs_90) * 100, index=df.index)
        cai = cai_raw.rolling(7, min_periods=1).mean()
        
        return {
            'regime': pd.Series(regime, index=df.index),
            'cai': cai,
            'rs_risk_btc': rs_risk_btc,
            'delta_rs_risk': delta_rs_risk,
            'm_risk': m_risk
        }
    
    def _calculate_narratives(self, df: pd.DataFrame, m_risk: pd.Series) -> Dict[str, Any]:
        """Calculate narrative metrics."""
        narratives = {
            'DEFI_MCAP': 'defi',
            'MEME_MCAP': 'meme',
            'AI_MCAP': 'ai',
            'LAYER1_MCAP': 'l1',
            'DEPIN_MCAP': 'depin',
            'RWA_MCAP': 'rwa'
        }
        
        m_btc = df['BTC_MCAP'].ffill() / 1e9 if 'BTC_MCAP' in df.columns else pd.Series(1, index=df.index)
        
        result = {}
        for col, name in narratives.items():
            if col in df.columns:
                m_narrative = df[col].ffill() / 1e9
                
                # Relative strength vs BTC
                rs_btc = np.log(m_narrative / m_btc)
                mom_btc = rs_btc.diff(30)
                
                # Share of alts
                share_of_alts = np.log(m_narrative / m_risk)
                mom_share = share_of_alts.diff(30)
                
                result[name] = {
                    'mcap': clean_for_json(m_narrative),
                    'mom_btc': clean_for_json(mom_btc),
                    'mom_share': clean_for_json(mom_share),
                }
        
        return result
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process crypto data."""
        result = {
            'btc_price_ref': 'shared.btc',  # Reference, not duplicate
            'stablecoin_supply_ref': 'stablecoins.total',
        }
        
        # Get stablecoin supply from kwargs or calculate
        stablecoins_result = kwargs.get('stablecoins', {})
        if stablecoins_result and 'total' in stablecoins_result:
            m_stable = pd.Series(stablecoins_result['total'], index=df.index)
        elif 'STABLE_INDEX_MCAP' in df.columns:
            m_stable = df['STABLE_INDEX_MCAP'].ffill() / 1e9
        else:
            m_stable = pd.Series(0, index=df.index)
        
        # Regimes
        regimes = self._calculate_regimes(df, m_stable)
        result['regimes'] = clean_for_json(regimes['regime'])
        result['cai'] = clean_for_json(regimes['cai'])
        result['rs_risk_btc'] = clean_for_json(regimes['rs_risk_btc'])
        result['delta_rs_risk'] = clean_for_json(regimes['delta_rs_risk'])
        
        # Narratives
        result['narratives'] = self._calculate_narratives(df, regimes['m_risk'])
        
        # Dominance
        if 'BTC_DOM' in df.columns:
            result['btc_dominance'] = clean_for_json(df['BTC_DOM'].ffill())
        if 'ETH_DOM' in df.columns:
            result['eth_dominance'] = clean_for_json(df['ETH_DOM'].ffill())
        
        # Market caps
        if 'TOTAL_MCAP' in df.columns:
            result['total_mcap'] = clean_for_json(df['TOTAL_MCAP'].ffill() / 1e9)
        if 'BTC_MCAP' in df.columns:
            result['btc_mcap'] = clean_for_json(df['BTC_MCAP'].ffill() / 1e9)
        if 'ETH_MCAP' in df.columns:
            result['eth_mcap'] = clean_for_json(df['ETH_MCAP'].ffill() / 1e9)
        
        return result
