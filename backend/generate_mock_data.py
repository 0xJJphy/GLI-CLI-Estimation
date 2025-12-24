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

    def calculate_roc(series, window):
        arr = np.array(series)
        roc = np.zeros_like(arr)
        roc[window:] = ((arr[window:] / arr[:-window]) - 1) * 100
        return roc.tolist()

    gli_total = random_walk(25, 365, 0.005)
    fed_assets = [v * 0.4 for v in gli_total]
    ecb_assets = [v * 0.3 for v in gli_total]
    boj_assets = [v * 0.2 for v in gli_total]
    boe_assets = [v * 0.06 for v in gli_total]
    pboc_assets = [v * 0.04 for v in gli_total]

    us_net_liq = random_walk(6, 365, 0.008)
    cli = random_walk(0, 365, 0.1) # CLI around 0 (Z-score)
    vix = random_walk(15, 365, 0.05)
    hy_spread = random_walk(400, 365, 0.02)

    # Bitcoin with correlation to GLI (lagged +45 days)
    btc_base = random_walk(30000, 365, 0.015)
    gli_influence = np.array([25] * 45 + gli_total[:-45])
    btc_price = (btc_base + gli_influence * 1000).tolist()

    # Fair value model (simple linear combination)
    btc_fair = [(gli * 1200) + (cli * -500) + 25000 for gli, cli in zip([25] * 45 + gli_total[:-45], [0] * 45 + cli[:-45])]
    btc_std = np.std(np.array(btc_price) - np.array(btc_fair))

    # Mock correlations (lag -> correlation)
    correlations = {
        'gli_btc': {str(lag): 0.7 * np.exp(-(lag-45)**2/500) for lag in range(-90, 91)},
        'cli_btc': {str(lag): -0.5 * np.exp(-(lag-14)**2/300) for lag in range(-90, 91)},
        'vix_btc': {str(lag): -0.4 * np.exp(-(lag+7)**2/200) for lag in range(-90, 91)},
        'netliq_btc': {str(lag): 0.6 * np.exp(-(lag-30)**2/400) for lag in range(-90, 91)}
    }

    data = {
        'dates': dates,
        'last_dates': {},
        'gli': {
            'total': gli_total,
            'fed': fed_assets,
            'ecb': ecb_assets,
            'boj': boj_assets,
            'boe': boe_assets,
            'pboc': pboc_assets,
            'rocs': {
                '1M': calculate_roc(gli_total, 21),
                '3M': calculate_roc(gli_total, 63),
                '6M': calculate_roc(gli_total, 126),
                '1Y': calculate_roc(gli_total, 252)
            }
        },
        'us_net_liq': us_net_liq,
        'us_net_liq_rocs': {
            '1M': calculate_roc(us_net_liq, 21),
            '3M': calculate_roc(us_net_liq, 63),
            '6M': calculate_roc(us_net_liq, 126),
            '1Y': calculate_roc(us_net_liq, 252)
        },
        'bank_rocs': {
            'fed': {
                '1M': calculate_roc(fed_assets, 21),
                '3M': calculate_roc(fed_assets, 63),
                '6M': calculate_roc(fed_assets, 126),
                '1Y': calculate_roc(fed_assets, 252)
            },
            'ecb': {
                '1M': calculate_roc(ecb_assets, 21),
                '3M': calculate_roc(ecb_assets, 63),
                '6M': calculate_roc(ecb_assets, 126),
                '1Y': calculate_roc(ecb_assets, 252)
            },
            'boj': {
                '1M': calculate_roc(boj_assets, 21),
                '3M': calculate_roc(boj_assets, 63),
                '6M': calculate_roc(boj_assets, 126),
                '1Y': calculate_roc(boj_assets, 252)
            },
            'boe': {
                '1M': calculate_roc(boe_assets, 21),
                '3M': calculate_roc(boe_assets, 63),
                '6M': calculate_roc(boe_assets, 126),
                '1Y': calculate_roc(boe_assets, 252)
            },
            'pboc': {
                '1M': calculate_roc(pboc_assets, 21),
                '3M': calculate_roc(pboc_assets, 63),
                '6M': calculate_roc(pboc_assets, 126),
                '1Y': calculate_roc(pboc_assets, 252)
            }
        },
        'cli': cli,
        'vix': vix,
        'hy_spread': hy_spread,
        'btc': {
            'price': btc_price,
            'fair_value': btc_fair,
            'upper_1sd': (np.array(btc_fair) + btc_std).tolist(),
            'lower_1sd': (np.array(btc_fair) - btc_std).tolist(),
            'upper_2sd': (np.array(btc_fair) + 2*btc_std).tolist(),
            'lower_2sd': (np.array(btc_fair) - 2*btc_std).tolist(),
            'deviation_pct': (((np.array(btc_price) - np.array(btc_fair)) / np.array(btc_fair)) * 100).tolist(),
            'deviation_zscore': ((np.array(btc_price) - np.array(btc_fair)) / btc_std).tolist(),
            'rocs': {
                '1M': calculate_roc(btc_price, 21),
                '3M': calculate_roc(btc_price, 63),
                '6M': calculate_roc(btc_price, 126),
                '1Y': calculate_roc(btc_price, 252)
            }
        },
        'correlations': correlations
    }

    output_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'dashboard_data.json')
    
    with open(output_path, 'w') as f:
        json.dump(data, f)
    
    print(f"Mock data generated at {output_path}")

if __name__ == "__main__":
    generate_mock_data()
