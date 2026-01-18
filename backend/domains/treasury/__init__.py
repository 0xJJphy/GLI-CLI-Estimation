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
        
        # CRITICAL: Filter pre-2000 data for stats to match Modern Regime
        stats_cutoff = pd.Timestamp('2000-01-01')

        result['yields'] = {}
        for name, col in yield_cols.items():
            if col in df.columns:
                series = df[col].ffill()
                result['yields'][name] = clean_for_json(series)
                
                # Create stats context series (NaN before 2000 so expanding starts there)
                stats_series = series.copy()
                stats_series.loc[stats_series.index < stats_cutoff] = np.nan
                
                # Calculate percentile (Post-2000 Expanding)
                result['yields'][f'{name}_pct'] = clean_for_json(rolling_percentile(stats_series, min_periods=100, expanding=True))
                # Calculate z-score (Post-2000 Expanding)
                result['yields'][f'{name}_z'] = clean_for_json(calculate_zscore(stats_series, min_periods=100, expanding=True))
        
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
                
                # Apply same 2000 cutoff for curve stats
                stats_series = spread.copy()
                stats_series.loc[stats_series.index < stats_cutoff] = np.nan
                
                # Calculate percentile (Post-2000 Expanding)
                result['curves'][f'{name}_pct'] = clean_for_json(rolling_percentile(stats_series, min_periods=100, expanding=True))
                # Calculate z-score (Post-2000 Expanding)
                result['curves'][f'{name}_z'] = clean_for_json(calculate_zscore(stats_series, min_periods=100, expanding=True))
        
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
        
        # --- PHASE 2: SIGNAL MIGRATION ---
        result['signals'] = {}

        # 1. Inflation Expectations Signal (Cleveland Fed)
        # Using 1Y vs 2Y Swap Rate
        if 'INFLATION_EXPECT_1Y' in df.columns and 'INFLATION_EXPECT_2Y' in df.columns:
            result['signals']['inflation'] = self._calc_inflation_regime(
                df['INFLATION_EXPECT_1Y'], 
                df['INFLATION_EXPECT_2Y']
            )

        # 2. TIPS Regime (Breakeven vs Real Rates)
        # Using 10Y Breakeven and 10Y Real Rate
        if 'TIPS_BREAKEVEN' in df.columns and 'TIPS_REAL_RATE' in df.columns:
            result['signals']['tips'] = self._calc_tips_regime(
                df['TIPS_BREAKEVEN'], 
                df['TIPS_REAL_RATE']
            )

        # 3. Yield Curve Regime (10Y-2Y)
        # Uses Spread and 10Y Rate Change
        if 'TREASURY_10Y_YIELD' in df.columns and 'TREASURY_2Y_YIELD' in df.columns:
            result['signals']['yield_curve'] = self._calc_yield_curve_regime(
                df['TREASURY_10Y_YIELD'], 
                df['TREASURY_2Y_YIELD']
            )

        return result

    def _calc_inflation_regime(self, s1y: pd.Series, s2y: pd.Series) -> Dict[str, Any]:
        """
        Calculate Inflation Expectations Regime.
        Logic:
        - Inverted (1Y < 2Y): Bearish (Disinflation/Recession imminent)
        - Normal (1Y > 2Y): Bullish/Neutral (Healthy inflation expectations)
        """
        s1 = s1y.ffill()
        s2 = s2y.ffill()
        
        if s1.empty or s2.empty:
            return {'state': 'neutral', 'value': 0, 'reason': 'No Data'}
        
        last1 = s1.iloc[-1]
        last2 = s2.iloc[-1]
        
        if pd.isna(last1) or pd.isna(last2):
            return {'state': 'neutral', 'label': 'NO DATA', 'desc': 'Insufficient Data', 'value': 0}
            
        spread = last1 - last2
        
        # Thresholds from Analyst validation
        if spread < -0.05:
            return {
                'state': 'bearish', 
                'label': 'INVERTED', 
                'desc': '1Y > 2Y Expectations. Disinflation/Recession imminent.', 
                'value': float(spread)
            }
        elif spread > 0.05:
            return {
                'state': 'bullish', 
                'label': 'NORMAL', 
                'desc': '1Y < 2Y Expectations. Healthy rising term structure.', 
                'value': float(spread)
            }
        else:
            return {
                'state': 'neutral', 
                'label': 'FLAT', 
                'desc': 'Inflation expectations curve is flat.', 
                'value': float(spread)
            }

    def _calc_tips_regime(self, be_series: pd.Series, rr_series: pd.Series) -> Dict[str, Any]:
        """
        Calculate TIPS Regime based on Breakeven (Inflation) and Real Rates (Cost of Money).
        Uses Expanding Window Z-Scores/Averages for structural comparison.
        """
        be = be_series.ffill()
        rr = rr_series.ffill()
        
        if be.empty or rr.empty:
            return {'state': 'neutral', 'label': 'NO DATA', 'desc': 'No Data', 'value': 0}
            
        # Stats (using 1Y rolling for momentum comparison, or expanding for regime?
        # Plan specified unifying to structural regime. Let's use 252d MA for baseline.)
        be_avg = be.rolling(252, min_periods=60).mean().iloc[-1]
        rr_avg = rr.rolling(252, min_periods=60).mean().iloc[-1]
        
        last_be = be.iloc[-1]
        last_rr = rr.iloc[-1]
        
        if pd.isna(be_avg) or pd.isna(rr_avg):
            return {'state': 'neutral', 'label': 'NO DATA', 'desc': 'NaN Data', 'value': float(last_rr)}

        be_high = last_be > be_avg * 1.1
        rr_high = last_rr > rr_avg + 0.5
        be_low = last_be < be_avg * 0.9
        rr_low = last_rr < rr_avg - 0.3
        
        state = "neutral"
        label = "STABLE"
        desc = "Real Rates and Inflation Expectations are stable."
        
        if be_high and rr_high:
            state = "warning"
            label = "TIGHTENING"
            desc = "Rising Real Rates with High Inflation Expectations."
        elif be_high and not rr_high:
            state = "bullish"
            label = "REFLATION"
            desc = "High Inflation Expectations with Low Real Rates (Risk-On)."
        elif rr_high and not be_high:
            state = "bearish"
            label = "BEAR TIGHTENING"
            desc = "High Real Rates choking economic activity."
        elif be_low and rr_low:
            state = "neutral" 
            label = "DISINFLATION"
            desc = "Falling Rates and Inflation Expectations."
            
        return {'state': state, 'label': label, 'desc': desc, 'value': float(last_rr)}

    def _calc_yield_curve_regime(self, long_yield: pd.Series, short_yield: pd.Series) -> Dict[str, Any]:
        """
        Calculate Yield Curve Regime (Bull/Bear Steepener/Flattener).
        """
        l = long_yield.ffill()
        s = short_yield.ffill()
        spread = l - s
        
        if spread.empty:
            return {'state': 'neutral'}
            
        last_spread = spread.iloc[-1]
        last_long = l.iloc[-1]
        
        # 1-Month Changes (22 trading days)
        prev_spread = spread.iloc[-23] if len(spread) > 22 else last_spread
        prev_long = l.iloc[-23] if len(l) > 22 else last_long
        
        spread_chg = last_spread - prev_spread
        rate_chg = last_long - prev_long
        
        # Regime Logic
        if last_spread < 0:
            return {'state': 'bearish', 'label': 'INVERTED', 'desc': 'Yield curve inverted. Recession risk.', 'value': float(last_spread)}

        # Rate Change Direction (Threshold 5bps to avoid noise)
        rates_up = rate_chg > 0.05
        rates_down = rate_chg < -0.05
        spread_up = spread_chg > 0.05
        spread_down = spread_chg < -0.05

        if spread_up:
            if rates_up:
                return {'state': 'bearish', 'label': 'BEAR STEEPENER', 'desc': 'Rates rising faster at long end. Inflation fears.', 'value': float(last_spread)}
            elif rates_down:
                return {'state': 'bullish', 'label': 'BULL STEEPENER', 'desc': 'Short rates falling faster. Fed easing priced in.', 'value': float(last_spread)}
            else:
                return {'state': 'neutral', 'label': 'STEEPENING', 'desc': 'Curve steepening with stable rates.', 'value': float(last_spread)}
        elif spread_down:
            if rates_up:
                return {'state': 'bearish', 'label': 'BEAR FLATTENER', 'desc': 'Short rates rising faster. Fed hiking checks.', 'value': float(last_spread)}
            elif rates_down:
                return {'state': 'warning', 'label': 'BULL FLATTENER', 'desc': 'Long rates falling faster. Growth slowing.', 'value': float(last_spread)}
            else:
                return {'state': 'neutral', 'label': 'FLATTENING', 'desc': 'Curve flattening with stable rates.', 'value': float(last_spread)}
        
        return {'state': 'neutral', 'label': 'NORMAL', 'desc': 'Normal upward sloping curve.', 'value': float(last_spread)}

            
        label = "HOLD"
        state = "neutral"
        desc = "Little Change"
        
        if spread_chg > 0.05: # Steepening
            if rate_chg < 0: # Bull Steepener (Rates Falling)
                label = "BULL STEEPENER"
                state = "bullish"
                desc = "Rates ↓, Spread ↑ (Reflation/Cut Hopes)"
            else: # Bear Steepener (Rates Rising)
                label = "BEAR STEEPENER"
                state = "warning"
                desc = "Rates ↑, Spread ↑ (Inflation Fear)"
        elif spread_chg < -0.05: # Flattening
            if rate_chg < 0: # Bull Flattener (Long Rates Falling faster? No, usually short rates stick)
                # Usually Bull Flattener is rare, but let's stick to simple logic
                label = "BULL FLATTENER"
                state = "neutral"
                desc = "Rates ↓, Spread ↓"
            else: # Bear Flattener (Short Rates Rising)
                label = "BEAR FLATTENER"
                state = "bearish"
                desc = "Rates ↑, Spread ↓ (Fed Tightening)"
                
        return {'state': state, 'label': label, 'desc': desc, 'value': float(last_spread)}


