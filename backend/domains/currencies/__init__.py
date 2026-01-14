"""
Currencies Domain Processor

Handles:
- DXY (US Dollar Index)
- Major currency pairs (EUR, JPY, GBP, AUD, CAD, CHF, CNY)
- Bitcoin overlay for comparison
- ROC metrics, Z-scores, percentiles, volatility
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json


class CurrenciesDomain(BaseDomain):
    """
    Currencies data domain.
    
    Produces currencies.json with DXY, major pairs, and BTC overlay.
    """
    
    @property
    def name(self) -> str:
        return "currencies"
    
    def _calc_roc(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate Rate of Change as percentage."""
        return ((series / series.shift(period) - 1) * 100)
    
    def _calc_zscore(self, series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling Z-score."""
        mean = series.rolling(window, min_periods=window // 2).mean()
        std = series.rolling(window, min_periods=window // 2).std()
        return ((series - mean) / std.replace(0, np.nan))
    
    def _calc_percentile(self, series: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling percentile rank."""
        def percentile_rank(arr):
            if len(arr) < window // 2:
                return np.nan
            current = arr[-1]
            if np.isnan(current):
                return np.nan
            valid = arr[~np.isnan(arr)]
            if len(valid) < window // 2:
                return np.nan
            rank = (valid < current).sum() + 0.5 * (valid == current).sum()
            return 100 * rank / len(valid)
        return series.rolling(window, min_periods=window // 2).apply(percentile_rank, raw=True)
    
    def _calc_volatility(self, series: pd.Series, window: int = 21) -> pd.Series:
        """Calculate annualized realized volatility."""
        pct_change = series.pct_change()
        return pct_change.rolling(window).std() * np.sqrt(252) * 100
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Process currencies data.
        
        Args:
            df: Main DataFrame with DXY, FX pairs, and BTC columns
        
        Returns:
            Dict with dxy, pairs, btc sections
        """
        result = {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'dxy': {},
            'pairs': {},
            'btc': {}
        }
        
        # 1. Process DXY
        if 'DXY' in df.columns:
            dxy = df['DXY'].ffill()
            
            result['dxy'] = {
                'absolute': clean_for_json(dxy),
                # ROC Metrics
                'roc_7d': clean_for_json(self._calc_roc(dxy, 7)),
                'roc_30d': clean_for_json(self._calc_roc(dxy, 30)),
                'roc_90d': clean_for_json(self._calc_roc(dxy, 90)),
                'roc_180d': clean_for_json(self._calc_roc(dxy, 180)),
                'roc_yoy': clean_for_json(self._calc_roc(dxy, 365)),
                # Z-Scores for ROCs
                'roc_7d_z': clean_for_json(self._calc_zscore(self._calc_roc(dxy, 7), 252)),
                'roc_30d_z': clean_for_json(self._calc_zscore(self._calc_roc(dxy, 30), 252)),
                'roc_90d_z': clean_for_json(self._calc_zscore(self._calc_roc(dxy, 90), 252)),
                'roc_180d_z': clean_for_json(self._calc_zscore(self._calc_roc(dxy, 180), 252)),
                # Percentiles for ROCs
                'roc_7d_pct': clean_for_json(self._calc_percentile(self._calc_roc(dxy, 7), 252)),
                'roc_30d_pct': clean_for_json(self._calc_percentile(self._calc_roc(dxy, 30), 252)),
                'roc_90d_pct': clean_for_json(self._calc_percentile(self._calc_roc(dxy, 90), 252)),
                'roc_180d_pct': clean_for_json(self._calc_percentile(self._calc_roc(dxy, 180), 252)),
                # Volatility
                'volatility': clean_for_json(self._calc_volatility(dxy, 21))
            }
        
        # 2. Process Major Pairs
        major_pairs = {
            'EURUSD': 'EUR',
            'JPYUSD': 'JPY',
            'GBPUSD': 'GBP',
            'AUDUSD': 'AUD',
            'CADUSD': 'CAD',
            'CHFUSD': 'CHF',
            'CNYUSD': 'CNY'
        }
        
        for col, name in major_pairs.items():
            if col in df.columns:
                pair_series = df[col].ffill()
                result['pairs'][name] = {
                    'absolute': clean_for_json(pair_series),
                    'roc_7d': clean_for_json(self._calc_roc(pair_series, 7)),
                    'roc_30d': clean_for_json(self._calc_roc(pair_series, 30)),
                    'roc_90d': clean_for_json(self._calc_roc(pair_series, 90)),
                    'roc_180d': clean_for_json(self._calc_roc(pair_series, 180)),
                    'roc_yoy': clean_for_json(self._calc_roc(pair_series, 365)),
                }
        
        # 3. Process Bitcoin for overlay
        if 'BTC' in df.columns:
            btc = df['BTC'].ffill()
            result['btc'] = {
                'absolute': clean_for_json(btc),
                'roc_7d': clean_for_json(self._calc_roc(btc, 7)),
                'roc_30d': clean_for_json(self._calc_roc(btc, 30)),
                'roc_90d': clean_for_json(self._calc_roc(btc, 90)),
                'roc_180d': clean_for_json(self._calc_roc(btc, 180)),
                'roc_yoy': clean_for_json(self._calc_roc(btc, 365)),
            }
        
        return result
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate currencies output."""
        super().validate(data)
        
        required_keys = ['dates', 'dxy', 'pairs', 'btc']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
        
        return True
