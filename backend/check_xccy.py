"""Check XCCY basis data in dashboard_data.json."""
import json

with open('data/dashboard_data.json', 'r') as f:
    d = json.load(f)

ol = d.get('offshore_liquidity', {})

# Chart 1
c1 = ol.get('chart1_fred_proxy', {})
print("=== CHART 1: FRED PROXY ===")
print(f"Dates: {len(c1.get('dates', []))}")
print(f"Spread: {len(c1.get('obfr_effr_spread', []))}")
print(f"Latest: {c1.get('latest', {})}")

# Chart 2
c2 = ol.get('chart2_xccy_diy', {})
print("\n=== CHART 2: XCCY DIY ===")
if c2:
    print(f"Dates: {len(c2.get('dates', []))}")
    print(f"EUR/USD basis: {len(c2.get('xccy_eurusd', []))} values")
    print(f"USD/JPY basis: {len(c2.get('xccy_usdjpy', []))} values")
    print(f"GBP/USD basis: {len(c2.get('xccy_gbpusd', []))} values")
    print(f"Latest: {c2.get('latest', {})}")
    print(f"Stress level: {c2.get('stress_level')}")
    print(f"Stress score: {c2.get('stress_score')}")
    if c2.get('dates'):
        print(f"Date range: {c2['dates'][0]} to {c2['dates'][-1]}")
else:
    print("Chart 2 data NOT available")
