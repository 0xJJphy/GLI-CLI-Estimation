"""
Treasury Domain - Yields, Auctions, Settlements, Maturities

Contains:
- Treasury yields (2Y, 5Y, 10Y, 30Y)
- Yield curve spreads
- Treasury maturities schedule
- Auction demand data
- Refinancing signal
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json, calculate_rocs, rolling_percentile, calculate_zscore

# Import treasury data functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from treasury.treasury_data import get_treasury_maturity_data
    from treasury.treasury_auction_demand import get_auction_demand_for_pipeline
    HAS_TREASURY_FUNCS = True
except ImportError as e:
    HAS_TREASURY_FUNCS = False
    print(f"[TreasuryDomain] Warning: Could not import treasury functions: {e}")


class TreasuryDomain(BaseDomain):
    """Treasury yields, curves, maturities, and auctions domain."""
    
    @property
    def name(self) -> str:
        return "treasury"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process treasury data including maturities and auctions."""
        result = {}
        
        # Yields
        yield_cols = {
            '2y': 'TREASURY_2Y_YIELD',
            '5y': 'TREASURY_5Y_YIELD',
            '10y': 'TREASURY_10Y_YIELD',
            '30y': 'TREASURY_30Y_YIELD'
        }
        
        result['yields'] = {}
        for name, col in yield_cols.items():
            if col in df.columns:
                series = df[col].ffill()
                result['yields'][name] = clean_for_json(series)
                # Calculate percentile (5-year window approx)
                result['yields'][f'{name}_pct'] = clean_for_json(rolling_percentile(series, window=1260))
                # Calculate z-score (1-year window approx)
                result['yields'][f'{name}_z'] = clean_for_json(calculate_zscore(series, window=252))
        
        # Yield curves (spreads)
        result['curves'] = {}
        
        curve_definitions = [
            ('10y_2y', 'TREASURY_10Y_YIELD', 'TREASURY_2Y_YIELD'),
            ('30y_10y', 'TREASURY_30Y_YIELD', 'TREASURY_10Y_YIELD'),
            ('30y_2y', 'TREASURY_30Y_YIELD', 'TREASURY_2Y_YIELD'),
            ('10y_5y', 'TREASURY_10Y_YIELD', 'TREASURY_5Y_YIELD')
        ]
        
        for name, long_col, short_col in curve_definitions:
            if long_col in df.columns and short_col in df.columns:
                long_val = df[long_col].ffill()
                short_val = df[short_col].ffill()
                spread = long_val - short_val
                
                result['curves'][name] = clean_for_json(spread)
                result['curves'][f'{name}_pct'] = clean_for_json(rolling_percentile(spread, window=1260))
                result['curves'][f'{name}_z'] = clean_for_json(calculate_zscore(spread, window=252))
        
        # Corporate spreads (Moody's)
        if 'BAA_YIELD' in df.columns and 'AAA_YIELD' in df.columns:
            baa = df['BAA_YIELD'].ffill()
            aaa = df['AAA_YIELD'].ffill()
            result['corporate'] = {
                'baa_yield': clean_for_json(baa),
                'aaa_yield': clean_for_json(aaa),
                'baa_aaa_spread': clean_for_json(baa - aaa)
            }
        
        # Treasury Maturities (actual data, not just reference)
        if HAS_TREASURY_FUNCS:
            try:
                maturity_data = get_treasury_maturity_data(120)  # 10 years ahead
                result['maturities'] = maturity_data
                print(f"[TreasuryDomain] Maturities: {len(maturity_data.get('schedule', {}).get('months', []))} months")
            except Exception as e:
                print(f"[TreasuryDomain] Error loading maturities: {e}")
                result['maturities'] = None
            
            # Treasury Auction Demand
            try:
                auction_data = get_auction_demand_for_pipeline()
                result['auction_demand'] = auction_data
                auctions_count = len(auction_data.get('raw_auctions', []))
                print(f"[TreasuryDomain] Auction demand: {auctions_count} auctions")
            except Exception as e:
                print(f"[TreasuryDomain] Error loading auction demand: {e}")
                result['auction_demand'] = None
            
            # Refinancing Signal is complex - requires multiple inputs
            # For now, just reference it from legacy data_pipeline
            result['refinancing_signal_ref'] = 'treasury_refinancing_signal'
        else:
            # Fallback to references if functions not available
            result['maturities_ref'] = 'treasury_maturities'
            result['auction_data_ref'] = 'treasury_auction_demand'
            result['refinancing_signal_ref'] = 'treasury_refinancing_signal'
        
        return result


