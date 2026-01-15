"""
Stablecoins Domain - Stablecoin market analytics

Contains:
- Individual stablecoin market caps (USDT, USDC, DAI, etc.)
- Aggregate supply and dominance
- Depeg detection
- Flow indicators (SFAI)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

from ..base import BaseDomain, clean_for_json, calculate_rocs, calculate_zscore


class StablecoinsDomain(BaseDomain):
    """Stablecoin analytics domain."""
    
    @property
    def name(self) -> str:
        return "stablecoins"
    
    def _detect_depeg(self, price_series: pd.Series, threshold: float = 0.005) -> List[Dict]:
        """Detect depeg events where price deviates from $1."""
        events = []
        if price_series is None or price_series.empty:
            return events
        
        for date, price in price_series.items():
            if pd.isna(price):
                continue
            if abs(price - 1.0) > threshold:
                events.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': float(price),
                    'deviation_pct': float((price - 1.0) * 100)
                })
        
        return events[-100:]  # Last 100 events
    
    def _calc_roc(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate ROC as percentage."""
        return ((series / series.shift(period) - 1) * 100)
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process stablecoin data."""
        result = {
            'btc_ref': 'shared.btc',  # Reference BTC from shared domain
        }
        
        # Stablecoin market caps
        stables = {
            'USDT': 'USDT_MCAP',
            'USDC': 'USDC_MCAP',
            'DAI': 'DAI_MCAP',
            'TUSD': 'TUSD_MCAP',
            'USDD': 'USDD_MCAP',
            'USDP': 'USDP_MCAP',
            'PYUSD': 'PYUSD_MCAP',
            'FDUSD': 'FDUSD_MCAP',
            'USDE': 'USDEE_MCAP',
            'USDG': 'USDGG_MCAP',
            'RLUSD': 'RLUSD_MCAP',
        }
        
        # Market caps (in billions)
        result['market_caps'] = {}
        total_supply = pd.Series(0.0, index=df.index)
        
        for name, col in stables.items():
            if col in df.columns:
                mcap = df[col].ffill() / 1e9  # Convert to billions
                result['market_caps'][name] = clean_for_json(mcap)
                total_supply += mcap.fillna(0)
        
        result['total'] = clean_for_json(total_supply)
        
        # Total supply ROCs
        result['total_rocs'] = {
            '7d': clean_for_json(self._calc_roc(total_supply, 7)),
            '30d': clean_for_json(self._calc_roc(total_supply, 30)),
            '90d': clean_for_json(self._calc_roc(total_supply, 90)),
            '180d': clean_for_json(self._calc_roc(total_supply, 180)),
            'yoy': clean_for_json(self._calc_roc(total_supply, 365)),
        }
        
        # Z-scores for ROCs
        result['total_rocs_z'] = {
            '7d': clean_for_json(calculate_zscore(self._calc_roc(total_supply, 7), 252)),
            '30d': clean_for_json(calculate_zscore(self._calc_roc(total_supply, 30), 252)),
            '90d': clean_for_json(calculate_zscore(self._calc_roc(total_supply, 90), 252)),
        }
        
        # Prices and depeg detection
        price_cols = {
            'USDT': 'USDT_PRICE',
            'USDC': 'USDC_PRICE',
            'DAI': 'DAI_PRICE',
            'PYUSD': 'PYUSD_PRICE',
            'FDUSD': 'FDUSD_PRICE',
            'USDE': 'USDE_PRICE',
        }
        
        result['prices'] = {}
        result['depeg_events'] = {}
        
        for name, col in price_cols.items():
            if col in df.columns:
                price = df[col].ffill()
                result['prices'][name] = clean_for_json(price)
                result['depeg_events'][name] = self._detect_depeg(price)
        
        # Dominance (share of total stablecoin supply)
        result['dominance'] = {}
        result['growth'] = {}
        
        for name, mcap_data in result['market_caps'].items():
            mcap_series = pd.Series(mcap_data, index=df.index)
            # Dominance
            dom = (mcap_series / total_supply.replace(0, np.nan)) * 100
            result['dominance'][name] = clean_for_json(dom)
            # Growth
            result['growth'][name] = {
                '7d': float(self._calc_roc(mcap_series, 7).iloc[-1]) if len(mcap_series) > 7 else 0,
                '30d': float(self._calc_roc(mcap_series, 30).iloc[-1]) if len(mcap_series) > 30 else 0,
                '90d': float(self._calc_roc(mcap_series, 90).iloc[-1]) if len(mcap_series) > 90 else 0,
            }
        
        # Total crypto market cap dominance
        if 'TOTAL_MCAP' in df.columns:
            total_crypto = df['TOTAL_MCAP'].ffill() / 1e9
            result['dominance_total'] = {} # For the "Mkt Dom %" column
            for name, mcap_data in result['market_caps'].items():
                mcap_series = pd.Series(mcap_data, index=df.index)
                dom_total = (mcap_series / total_crypto.replace(0, np.nan)) * 100
                result['dominance_total'][name] = clean_for_json(dom_total)
            
            result['crypto_dominance'] = clean_for_json((total_supply / total_crypto.replace(0, np.nan)) * 100)
            result['total_crypto_mcap'] = clean_for_json(total_crypto)
        
        # SFAI (Stablecoin Flow Attribution Index)
        # SFAI uses total stablecoin ROC vs BTC performance
        if 'BTC' in df.columns:
            btc_ret = df['BTC'].pct_change(1)
            stables_roc = total_supply.pct_change(1)
            
            # Simple SFAI logic (V1)
            # 1: Inflow (Stables up, BTC neutral/up)
            # 2: Profit Taking (Stables up, BTC down)
            # 3: Buying Pressure (Stables down, BTC up)
            # 4: Capitulation (Stables down, BTC down)
            
            sfai_index = (stables_roc * 100).rolling(7).mean()
            sfai_velocity = sfai_index.diff(7)
            
            regime = pd.Series(0, index=df.index)
            regime.loc[(stables_roc > 0) & (btc_ret >= 0)] = 1
            regime.loc[(stables_roc > 0) & (btc_ret < 0)] = 2
            regime.loc[(stables_roc <= 0) & (btc_ret > 0)] = 3
            regime.loc[(stables_roc <= 0) & (btc_ret < 0)] = 4
            
            result['sfai_regime'] = clean_for_json(regime)
            result['sfai_continuous'] = clean_for_json(sfai_index)
            result['sfai_velocity'] = clean_for_json(sfai_velocity)
        
        # TradingView stablecoin indices (STABLE.C.D)
        if 'STABLE_INDEX_MCAP' in df.columns:
            # This is often used for the Dominance chart
            stable_idx = df['STABLE_INDEX_MCAP'].ffill() / 1e9
            result['stable_index_dom'] = clean_for_json(df.get('STABLE_INDEX_DOM', pd.Series(0, index=df.index)))
            result['custom_stables_dom'] = clean_for_json((total_supply / total_crypto.replace(0, np.nan)) * 100 if 'TOTAL_MCAP' in df.columns else pd.Series(0, index=df.index))
        
        return result
