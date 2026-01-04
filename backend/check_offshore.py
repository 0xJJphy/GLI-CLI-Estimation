"""Check offshore liquidity data in dashboard_data.json."""
import json

with open('data/dashboard_data.json', 'r') as f:
    data = json.load(f)

ol = data.get('offshore_liquidity', {})
c1 = ol.get('chart1_fred_proxy', {})

print(f"Dates: {len(c1.get('dates', []))}")
print(f"Spread: {len(c1.get('obfr_effr_spread', []))}")
print(f"Swaps: {len(c1.get('cb_swaps_b', []))}")
print(f"Latest: {c1.get('latest', {})}")
print(f"First 3 dates: {c1.get('dates', [])[:3] if c1.get('dates') else 'NONE'}")
print(f"Stress level: {c1.get('stress_level', 'UNKNOWN')}")
print(f"Stress score: {c1.get('stress_score', 'UNKNOWN')}")
