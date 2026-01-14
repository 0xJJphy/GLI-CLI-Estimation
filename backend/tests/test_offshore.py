"""Quick test for offshore liquidity module."""
from offshore_liquidity import get_offshore_liquidity_output
import pandas as pd
import numpy as np

dates = pd.date_range('2024-01-01', periods=50, freq='D')
df = pd.DataFrame({
    'OBFR': 4.35 + np.random.randn(50)*0.01,
    'EFFR': 4.33 + np.random.randn(50)*0.01,
    'FED_CB_SWAPS': np.abs(np.random.randn(50)*100)
}, index=dates)

result = get_offshore_liquidity_output(df)
chart1 = result['offshore_liquidity']['chart1_fred_proxy']

print(f"Dates count: {len(chart1['dates'])}")
print(f"Spread count: {len(chart1['obfr_effr_spread'])}")
print(f"CB Swaps count: {len(chart1['cb_swaps_b'])}")
print(f"Latest values: {chart1['latest']}")
print(f"Stress level: {chart1['stress_level']}")
print(f"First 3 dates: {chart1['dates'][:3]}")
