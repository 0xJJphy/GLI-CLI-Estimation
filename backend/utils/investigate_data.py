"""Deep investigation of offshore liquidity data source."""
import json
from collections import Counter

with open('data/dashboard_data.json', 'r') as f:
    d = json.load(f)

ol = d.get('offshore_liquidity', {})

# Chart 1
c1 = ol.get('chart1_fred_proxy', {})
dates1 = c1.get('dates', [])
spread = c1.get('obfr_effr_spread', [])

print("=== CHART 1: FRED PROXY (OBFR-EFFR) ===")
print(f"Total dates: {len(dates1)}")
print(f"Total spread values: {len(spread)}")
print(f"First 5 dates: {dates1[:5]}")
print(f"Last 5 dates: {dates1[-5:]}")
print(f"First 5 spread values: {spread[:5]}")
print(f"Last 5 spread values: {spread[-5:]}")

# Count nulls in spread
null_count = sum(1 for x in spread if x is None)
print(f"Null values in spread: {null_count}")

# Check years distribution
years = [d[:4] for d in dates1]
year_count = Counter(years)
print(f"\nYears distribution: {dict(sorted(year_count.items()))}")

# Chart 2
c2 = ol.get('chart2_xccy_diy', {})
if c2:
    dates2 = c2.get('dates', [])
    eurusd = c2.get('xccy_eurusd', [])
    
    print("\n=== CHART 2: XCCY DIY ===")
    print(f"Total dates: {len(dates2)}")
    print(f"First 5 dates: {dates2[:5] if dates2 else 'N/A'}")
    print(f"Last 5 dates: {dates2[-5:] if dates2 else 'N/A'}")
    print(f"First 5 EUR/USD values: {eurusd[:5] if eurusd else 'N/A'}")
    
    # Check years distribution
    if dates2:
        years2 = [d[:4] for d in dates2]
        year_count2 = Counter(years2)
        print(f"\nYears distribution: {dict(sorted(year_count2.items()))}")
else:
    print("\n=== CHART 2: NOT AVAILABLE ===")
