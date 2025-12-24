import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_mock_data():
    dates = [(datetime(2023, 1, 1) + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(365)]
    
    # Simple random walks for mockup
    def random_walk(start, n, std=0.01):
        return (start * (1 + np.cumsum(np.random.normal(0, std, n)))).tolist()

    gli_total = random_walk(25, 365, 0.005)
    fed_assets = [v * 0.4 for v in gli_total]
    ecb_assets = [v * 0.3 for v in gli_total]
    boj_assets = [v * 0.2 for v in gli_total]
    
    us_net_liq = random_walk(6, 365, 0.008)
    cli = random_walk(0, 365, 0.1) # CLI around 0 (Z-score)
    vix = random_walk(15, 365, 0.05)
    hy_spread = random_walk(400, 365, 0.02)

    data = {
        'dates': dates,
        'gli': {
            'total': gli_total,
            'fed': fed_assets,
            'ecb': ecb_assets,
            'boj': boj_assets
        },
        'us_net_liq': us_net_liq,
        'cli': cli,
        'vix': vix,
        'hy_spread': hy_spread
    }

    output_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'dashboard_data.json')
    
    with open(output_path, 'w') as f:
        json.dump(data, f)
    
    print(f"Mock data generated at {output_path}")

if __name__ == "__main__":
    generate_mock_data()
