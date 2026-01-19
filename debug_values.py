
import json
import os

# Use correct paths found by find_by_name
DOMAINS_DIR = r"c:\Users\Pedro\Documents\GitHub\GLI-CLI-Estimation\backend\data\domains"
DASHBOARD_DATA = r"c:\Users\Pedro\Documents\GitHub\GLI-CLI-Estimation\backend\data\dashboard_data.json"

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def get_latest(series):
    if not series or not isinstance(series, list):
        return None
    # Find last non-null
    for val in reversed(series):
        if val is not None:
            return val
    return None

def inspect_treasury():
    print("\n--- TREASURY DOMAIN (at backend/data/domains/treasury.json) ---")
    data = load_json(os.path.join(DOMAINS_DIR, "treasury.json"))
    if not data: return

    # Check Corporate
    corp = data.get('corporate', {})
    baa = get_latest(corp.get('baa_yield'))
    aaa = get_latest(corp.get('aaa_yield'))
    spread = get_latest(corp.get('baa_aaa_spread'))
    
    print(f"BAA Yield (Latest): {baa}")
    print(f"AAA Yield (Latest): {aaa}")
    print(f"BAA-AAA Spread (Latest): {spread}")
    
    if spread:
        print(f"Spread Value: {spread} (If 5900 -> 5900 bps, If 59 -> 59 bps, If 0.59 -> 0.59 bps or 59 bps?)")

def inspect_macro_regime():
    print("\n--- MACRO REGIME DOMAIN (at backend/data/domains/macro_regime.json) ---")
    data = load_json(os.path.join(DOMAINS_DIR, "macro_regime.json"))
    if not data: return

    # Check top level
    print(f"Top-level keys: {list(data.keys())}")
    
    div = data.get('cli_gli_divergence')
    latest_div = get_latest(div)
    print(f"CLI-GLI Divergence (Latest, from macro_regime.json): {latest_div}")
    
    # Check v2a nested
    v2a = data.get('v2a', {})
    v2a_div = get_latest(v2a.get('cli_gli_divergence'))
    print(f"V2A Divergence (Latest): {v2a_div}")

def inspect_dashboard_data():
    print("\n--- DASHBOARD DATA (at backend/data/dashboard_data.json) ---")
    data = load_json(DASHBOARD_DATA)
    if not data: return
    
    # Check top level divergence
    div = data.get('cli_gli_divergence')
    latest = get_latest(div)
    print(f"CLI-GLI Divergence (Latest, from dashboard_data.json): {latest}")
    
    # Check macro_regime key
    mr = data.get('macro_regime', {})
    mr_div = get_latest(mr.get('cli_gli_divergence'))
    print(f"macro_regime.cli_gli_divergence (Latest): {mr_div}")

if __name__ == "__main__":
    inspect_treasury()
    inspect_macro_regime()
    inspect_dashboard_data()
