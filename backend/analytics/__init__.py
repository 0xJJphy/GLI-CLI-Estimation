# Analytics Package

"""
Data analytics and calculation modules.

Contains:
- crypto_analytics: Crypto market regimes, CAI, narratives
- regime_v2: CLI V2 and macro regime calculations
- offshore_liquidity: Eurodollar stress metrics
"""

from .crypto_analytics import (
    fetch_fear_and_greed,
    calculate_crypto_regimes,
    calculate_narratives,
    calculate_fng_analytics
)

from .regime_v2 import (
    calculate_cli_v2,
    calculate_macro_regime_v2a,
    calculate_macro_regime_v2b,
    calculate_stress_historical,
    clean_series_for_json as clean_series_v2
)
