import pandas as pd
import numpy as np
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from domains.macro_regime import MacroRegimeDomain

def test_macro_regime_divergence():
    # Create mock data (300 days)
    dates = pd.date_range(start='2023-01-01', periods=300, freq='B')
    df = pd.DataFrame(index=dates)
    
    # Fill with random data simulating series
    df['GLI_TOTAL'] = np.random.randn(len(df)).cumsum()
    df['NET_LIQUIDITY'] = np.random.randn(len(df)).cumsum()
    df['M2_TOTAL'] = np.random.randn(len(df)).cumsum()
    df['CLI'] = np.random.randn(len(df)).cumsum()
    df['CLI_V2'] = np.random.randn(len(df)).cumsum() # Pre-calculated CLI
    
    # Add other required by v2a
    for col in ['TIPS_REAL_RATE', 'SOFR', 'IORB', 'BANK_RESERVES', 'MOVE', 'FX_VOL', 
                'YIELD_CURVE', 'TREASURY_10Y_YIELD', 'TREASURY_2Y_YIELD', 'TIPS_BREAKEVEN', 
                'CLEV_EXPINF_10Y', 'VIX']:
        df[col] = np.random.randn(len(df))

    # Padding with None at the end to simulate GLI lag
    # Last 5 days GLI is NaN
    df.iloc[-5:, df.columns.get_loc('GLI_TOTAL')] = np.nan

    print("--- Running MacroRegimeDomain ---")
    domain = MacroRegimeDomain()
    
    try:
        out = domain.process(df)
        div = out.get('cli_gli_divergence')
        
        print(f"Divergence present: {div is not None}")
        if div is not None:
            print(f"Divergence Length: {len(div)}")
            print(f"Divergence Last 10: {div[-10:]}")
            
            # Check if trailing Nones are present (my fix) or Zeros (ffill)
            # Since I passed NaN in GLI, ffill logic in v2a (regime_v2.py line 235) will fill them!
            # _safe_ffill_only fills NaNs.
            # So the calculation will produce values.
            
            # What if I explicitly set trailing values to 0?
            # df.iloc[-5:, df.columns.get_loc('GLI_TOTAL')] = 0.0 # Simulate bad fill?
            
            # My fix checks for LAST NON ZERO. 
            # If calculation produces valid values, last_valid_idx is the end.
            
            # The issue in Production was "All Zeros/Nulls".
            # This happens if GLI_TOTAL is MISSING.
             
        # Check if GLI_TOTAL check passed
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_macro_regime_divergence()
