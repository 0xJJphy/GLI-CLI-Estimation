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

from ..base import BaseDomain, clean_for_json, calculate_rocs

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
        
        # Yield curves (spreads)
        result['curves'] = {}
        
        if 'TREASURY_10Y_YIELD' in df.columns and 'TREASURY_2Y_YIELD' in df.columns:
            y10 = df['TREASURY_10Y_YIELD'].ffill()
            y2 = df['TREASURY_2Y_YIELD'].ffill()
            result['curves']['10y_2y'] = clean_for_json(y10 - y2)
        
        if 'TREASURY_30Y_YIELD' in df.columns and 'TREASURY_10Y_YIELD' in df.columns:
            y30 = df['TREASURY_30Y_YIELD'].ffill()
            y10 = df['TREASURY_10Y_YIELD'].ffill()
            result['curves']['30y_10y'] = clean_for_json(y30 - y10)
        
        if 'TREASURY_30Y_YIELD' in df.columns and 'TREASURY_2Y_YIELD' in df.columns:
            y30 = df['TREASURY_30Y_YIELD'].ffill()
            y2 = df['TREASURY_2Y_YIELD'].ffill()
            result['curves']['30y_2y'] = clean_for_json(y30 - y2)
        
        if 'TREASURY_10Y_YIELD' in df.columns and 'TREASURY_5Y_YIELD' in df.columns:
            y10 = df['TREASURY_10Y_YIELD'].ffill()
            y5 = df['TREASURY_5Y_YIELD'].ffill()
            result['curves']['10y_5y'] = clean_for_json(y10 - y5)
        
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


