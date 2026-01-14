# Backend Domains Package

"""
Modular data domain processors.

Each domain is responsible for:
- Processing raw data into domain-specific output
- Validating output against schema
- Saving to domain-specific JSON file
"""

from .base import BaseDomain, MetadataDomain, clean_for_json, calculate_rocs, calculate_zscore, rolling_percentile
from .currencies import CurrenciesDomain
from .core import SharedDomain, GLIDomain, USSystemDomain, M2Domain
from .cli import CLIDomain
from .treasury import TreasuryDomain
from .stablecoins import StablecoinsDomain
from .crypto import CryptoDomain
from .fed_forecasts import FedForecastsDomain
from .macro_regime import MacroRegimeDomain
from .offshore import OffshoreDomain

__all__ = [
    # Base
    'BaseDomain', 'MetadataDomain', 'clean_for_json', 'calculate_rocs', 
    'calculate_zscore', 'rolling_percentile',
    # Core domains
    'SharedDomain', 'GLIDomain', 'USSystemDomain', 'M2Domain',
    # Feature domains
    'CurrenciesDomain', 'CLIDomain', 'TreasuryDomain', 'StablecoinsDomain',
    'CryptoDomain', 'FedForecastsDomain', 'MacroRegimeDomain', 'OffshoreDomain'
]
