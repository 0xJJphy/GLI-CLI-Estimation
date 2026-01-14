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
        # Use title case keys to match legacy format expected by frontend
        narratives = {
            'DEFI_MCAP': 'DeFi',
            'MEME_MCAP': 'Meme',
            'AI_MCAP': 'AI',
            'LAYER1_MCAP': 'L1',
            'DEPIN_MCAP': 'DePIN',
            'RWA_MCAP': 'RWA'
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
                
                # Get current (last) values for displaying in cards
                last_mcap = m_narrative.iloc[-1] if len(m_narrative) > 0 else None
                last_mom_btc = mom_btc.iloc[-1] if len(mom_btc) > 0 else None
                last_mom_share = mom_share.iloc[-1] if len(mom_share) > 0 else None
                
                result[name] = {
                    'mcap': clean_for_json(m_narrative),
                    'mom_btc': clean_for_json(mom_btc),
                    'mom_share': clean_for_json(mom_share),
                    # Current values for narrative cards
                    'current_mcap': float(last_mcap) if last_mcap is not None and not np.isnan(last_mcap) else 0,
                    'current_mom_btc': float(last_mom_btc) if last_mom_btc is not None and not np.isnan(last_mom_btc) else 0,
                    'current_mom_share': float(last_mom_share) if last_mom_share is not None and not np.isnan(last_mom_share) else 0,
                }
        
        return result
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process crypto data with all legacy fields."""
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
        
        # === FEAR & GREED INDEX ===
        if 'FNG' in df.columns:
            fng = df['FNG'].ffill()
            result['fear_greed'] = clean_for_json(fng)
            
            # ROC metrics for F&G
            periods = {'7d': 7, '30d': 30, '90d': 90, '180d': 180, '365d': 365}
            for name, period in periods.items():
                roc = fng.pct_change(period) * 100
                result[f'fng_roc_{name}'] = clean_for_json(roc)
                
                # Z-score (rolling)
                z = (roc - roc.rolling(252, min_periods=63).mean()) / roc.rolling(252, min_periods=63).std()
                result[f'fng_roc_{name}_z'] = clean_for_json(z.clip(-3, 3))
                
                # Percentile (rolling)
                def rolling_pct_rank(s):
                    return s.expanding(min_periods=63).apply(lambda x: (x < x.iloc[-1]).mean() * 100, raw=False)
                result[f'fng_roc_{name}_pct'] = clean_for_json(rolling_pct_rank(roc))
            
            # Current F&G
            last_fng = fng.iloc[-1] if len(fng) > 0 else None
            result['fng_current'] = {
                'value': float(last_fng) if last_fng is not None and not np.isnan(last_fng) else None,
                'label': 'Fear' if last_fng and last_fng < 25 else 'Greed' if last_fng and last_fng > 75 else 'Neutral'
            }
        
        # === CAI ROC METRICS ===
        cai = regimes['cai']
        if cai is not None and len(cai) > 0:
            periods = {'7d': 7, '30d': 30, '90d': 90, '180d': 180, '365d': 365}
            for name, period in periods.items():
                roc = cai.diff(period)
                result[f'cai_roc_{name}'] = clean_for_json(roc)
                
                z = (roc - roc.rolling(252, min_periods=63).mean()) / roc.rolling(252, min_periods=63).std()
                result[f'cai_roc_{name}_z'] = clean_for_json(z.clip(-3, 3))
                
                def rolling_pct_rank(s):
                    return s.expanding(min_periods=63).apply(lambda x: (x < x.iloc[-1]).mean() * 100, raw=False)
                result[f'cai_roc_{name}_pct'] = clean_for_json(rolling_pct_rank(roc))
            
            # Current CAI
            last_cai = cai.iloc[-1] if len(cai) > 0 else None
            result['cai_current'] = {
                'value': float(last_cai) if last_cai is not None and not np.isnan(last_cai) else None,
                'label': 'Alt Season' if last_cai and last_cai > 75 else 'BTC Season' if last_cai and last_cai < 25 else 'Neutral'
            }
        
        # === DOMINANCE ===
        if 'BTC_DOM' in df.columns:
            result['btc_dominance'] = clean_for_json(df['BTC_DOM'].ffill())
            result['btc_dom'] = clean_for_json(df['BTC_DOM'].ffill())  # Legacy alias
        if 'ETH_DOM' in df.columns:
            result['eth_dominance'] = clean_for_json(df['ETH_DOM'].ffill())
            result['eth_dom'] = clean_for_json(df['ETH_DOM'].ffill())  # Legacy alias
        
        # Others dominance = 100 - BTC - ETH - Stablecoin
        if 'BTC_DOM' in df.columns and 'ETH_DOM' in df.columns:
            btc_d = df['BTC_DOM'].ffill()
            eth_d = df['ETH_DOM'].ffill()
            # Stablecoin dominance approximation
            total_mcap = df['TOTAL_MCAP'].ffill() / 1e9 if 'TOTAL_MCAP' in df.columns else pd.Series(1e12, index=df.index)
            stable_dom = (m_stable / total_mcap * 100).clip(0, 100)
            others_dom = (100 - btc_d - eth_d - stable_dom).clip(0, 100)
            result['others_dom'] = clean_for_json(others_dom)
            result['others_dominance'] = clean_for_json(others_dom)
            result['stablecoin_dominance'] = clean_for_json(stable_dom)
        
        # === STABLECOIN SUPPLY ===
        result['stablecoin_supply'] = clean_for_json(m_stable)
        
        # === MARKET CAPS ===
        if 'TOTAL_MCAP' in df.columns:
            result['total_mcap'] = clean_for_json(df['TOTAL_MCAP'].ffill() / 1e9)
        if 'BTC_MCAP' in df.columns:
            result['btc_mcap'] = clean_for_json(df['BTC_MCAP'].ffill() / 1e9)
        if 'ETH_MCAP' in df.columns:
            result['eth_mcap'] = clean_for_json(df['ETH_MCAP'].ffill() / 1e9)
        
        # === DEFI DOMINANCE ===
        if 'DEFI_MCAP' in df.columns and 'TOTAL_MCAP' in df.columns:
            defi_dom = (df['DEFI_MCAP'].ffill() / df['TOTAL_MCAP'].ffill() * 100).clip(0, 100)
            result['defi_dominance'] = clean_for_json(defi_dom)
        
        return result

