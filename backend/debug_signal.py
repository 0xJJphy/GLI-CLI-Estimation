import json

d = json.load(open('backend/data/dashboard_data.json'))
sig = d.get('treasury_refinancing_signal', {})

print('=== SIGNAL VERIFICATION ===')
print(f"Score: {sig.get('score')}")
print(f"Regime: {sig.get('regime', {}).get('name')}")
print(f"Signal: {sig.get('signal', {}).get('name')}")

print()
print('=== ALL COMPONENTS ===')
for c in sig.get('components', []):
    print(f"  {c['name']}: score={c['score']:.1f}, alert={c['alert_level']}")
    print(f"    desc: {c['description'][:95]}...")
    print(f"    raw_value: {c.get('raw_value')}")

print()
print('=== ALERT STATUS ===')
alert = sig.get('alert_status', {})
print(f"Status: {alert.get('status')}")
print(f"Critical count: {alert.get('critical_count')}")
print(f"Warning count: {alert.get('warning_count')}")

print()
print('=== IMPLICATIONS ===')
impl = sig.get('implications', {})
print(f"Duration: {impl.get('duration', 'N/A')[:60]}...")
print(f"Opportunities: {impl.get('opportunities', [])}")
print(f"Key Risks: {len(impl.get('key_risks', []))} items")
