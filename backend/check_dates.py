"""Check offshore liquidity date range."""
import json

with open('data/dashboard_data.json', 'r') as f:
    d = json.load(f)

ol = d.get('offshore_liquidity', {})
c1 = ol.get('chart1_fred_proxy', {})
dates = c1.get('dates', [])
spread = c1.get('obfr_effr_spread', [])
swaps = c1.get('cb_swaps_b', [])

print(f"Total dates: {len(dates)}")
print(f"First date: {dates[0] if dates else 'N/A'}")
print(f"Last date: {dates[-1] if dates else 'N/A'}")
print(f"Spread values count: {len(spread)}")
print(f"Swaps values count: {len(swaps)}")

# Check for null values
spread_nulls = sum(1 for x in spread if x is None)
swaps_nulls = sum(1 for x in swaps if x is None)
print(f"Spread nulls: {spread_nulls}")
print(f"Swaps nulls: {swaps_nulls}")

# Check first non-null spread
for i, (date, val) in enumerate(zip(dates, spread)):
    if val is not None:
        print(f"First non-null spread: {date} = {val}")
        break
