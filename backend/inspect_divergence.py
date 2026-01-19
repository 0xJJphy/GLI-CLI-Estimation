import json
import os
import pandas as pd
import numpy as np

def get_last_valid(arr):
    if not arr: return "Empty"
    # Find last non-null non-zero
    for x in reversed(arr):
        if x is not None and x != 0:
            return x
    return "All Zeros/Nulls"

def inspect():
    base = 'c:/Users/Pedro/Documents/GitHub/GLI-CLI-Estimation/backend/data'
    legacy_path = os.path.join(base, 'dashboard_data.json')
    modular_path = os.path.join(base, 'domains/macro_regime.json')

    print(f"--- LEAGCY: {legacy_path} ---")
    if os.path.exists(legacy_path):
        with open(legacy_path, 'r') as f:
            d = json.load(f)
            # Legacy path usually: macro_regime.cli_gli_divergence OR cli_gli_divergence
            val = d.get('macro_regime', {}).get('cli_gli_divergence')
            print(f"Legacy (macro_regime.cli_gli_divergence) Last Valid: {get_last_valid(val)}")
            print(f"Legacy (macro_regime.cli_gli_divergence) Tail: {val[-5:] if val else 'None'}")
    else:
        print("Legacy file not found")

    print(f"\n--- MODULAR: {modular_path} ---")
    if os.path.exists(modular_path):
        with open(modular_path, 'r') as f:
            d = json.load(f)
            # Modular path: cli_gli_divergence (top level)
            val = d.get('cli_gli_divergence')
            print(f"Modular (cli_gli_divergence) Last Valid: {get_last_valid(val)}")
            print(f"Modular (cli_gli_divergence) Tail: {val[-5:] if val else 'None'}")
    else:
        print("Modular file not found")

if __name__ == "__main__":
    inspect()
