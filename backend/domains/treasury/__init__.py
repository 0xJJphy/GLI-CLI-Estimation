"""
Treasury Domain - Yields, Auctions, Settlements

Contains:
- Treasury yields (2Y, 5Y, 10Y, 30Y)
- Yield curve spreads
- Auction data (referenced from existing modules)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from ..base import BaseDomain, clean_for_json, calculate_rocs


class TreasuryDomain(BaseDomain):
    """Treasury yields and curves domain."""
    
    @property
    def name(self) -> str:
        return "treasury"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process treasury data."""
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
        
        # Note: Auction data and settlements are fetched separately
        # via existing treasury_data.py and treasury_auction_demand.py
        # Those are referenced, not duplicated
        result['auction_data_ref'] = 'treasury_auction_demand'
        result['settlements_ref'] = 'treasury_settlements'
        result['maturities_ref'] = 'treasury_maturities'
        
        return result
