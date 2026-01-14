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
            'usdt': 'USDT_MCAP',
            'usdc': 'USDC_MCAP',
            'dai': 'DAI_MCAP',
            'tusd': 'TUSD_MCAP',
            'usdd': 'USDD_MCAP',
            'usdp': 'USDP_MCAP',
            'pyusd': 'PYUSD_MCAP',
            'fdusd': 'FDUSD_MCAP',
            'usde': 'USDEE_MCAP',
            'usdg': 'USDGG_MCAP',
            'rlusd': 'RLUSD_MCAP',
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
            'usdt': 'USDT_PRICE',
            'usdc': 'USDC_PRICE',
            'dai': 'DAI_PRICE',
            'pyusd': 'PYUSD_PRICE',
            'fdusd': 'FDUSD_PRICE',
            'usde': 'USDE_PRICE',
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
        for name in result['market_caps'].keys():
            if name in result['market_caps']:
                mcap_series = pd.Series(result['market_caps'][name], index=df.index)
                dom = (mcap_series / total_supply) * 100
                result['dominance'][name] = clean_for_json(dom)
        
        # Total crypto market cap dominance
        if 'TOTAL_MCAP' in df.columns:
            total_crypto = df['TOTAL_MCAP'].ffill() / 1e9
            result['crypto_dominance'] = clean_for_json((total_supply / total_crypto) * 100)
            result['total_crypto_mcap'] = clean_for_json(total_crypto)
        
        # TradingView stablecoin indices
        if 'STABLE_INDEX_MCAP' in df.columns:
            stable_idx = df['STABLE_INDEX_MCAP'].ffill() / 1e9
            result['stable_index'] = clean_for_json(stable_idx)
            result['stable_index_rocs'] = {
                '7d': clean_for_json(self._calc_roc(stable_idx, 7)),
                '30d': clean_for_json(self._calc_roc(stable_idx, 30)),
                '90d': clean_for_json(self._calc_roc(stable_idx, 90)),
            }
        
        return result
