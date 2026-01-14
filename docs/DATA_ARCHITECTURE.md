# Data Architecture Documentation

## Overview

This document describes the modular data architecture for the GLI-CLI Dashboard backend. The architecture replaces a monolithic 5,000+ line `data_pipeline.py` with domain-based processors that generate independent JSON outputs.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                   │
├──────────────────┬──────────────────┬───────────────────────────────────┤
│    FRED API      │   TradingView    │         External APIs             │
│  (Macro data)    │   (Price data)   │   (FOMC, Fear&Greed, etc.)       │
└────────┬─────────┴────────┬─────────┴───────────────┬───────────────────┘
         │                  │                         │
         ▼                  ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        data_pipeline.py                                  │
│                    (Data fetching & caching)                             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        orchestrator.py                                   │
│                   (Coordinates domain processing)                        │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  SharedDomain   │  │   GLIDomain     │  │   M2Domain      │
│  (dates, BTC,   │  │   (Global       │  │   (Money        │
│   CB sheets)    │  │   Liquidity)    │  │   Supply)       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ├────────────────────┼────────────────────┤
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         data/domains/                                    │
│   shared.json | gli.json | m2.json | cli.json | treasury.json | ...     │
└────────────────────────────────────────────────────────────────────────┬┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              dashboard_data.json (Backward Compatibility)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
backend/
├── analytics/              # Data analytics modules
│   ├── crypto_analytics.py # Crypto regimes, CAI, narratives
│   ├── offshore_liquidity.py # Eurodollar stress metrics
│   ├── regime_v2.py        # CLI V2, macro regime calculations
│   └── train_regime_offset.py # Regime training utils
├── config/                 # Configuration modules
│   ├── signal_config.py    # Signal computation and scoring
│   └── rates_sources.py    # Rate source configurations
├── connectors/             # External data connectors
│   ├── db_adapter.py       # Supabase/PostgreSQL adapter
│   └── etf_data.py         # ETF data fetcher
├── domains/                # Domain processors (new architecture)
│   ├── base.py             # BaseDomain + utilities
│   ├── schemas/            # JSON schemas (→ PostgreSQL)
│   ├── core/               # SharedDomain, GLI, M2, USSystem
│   ├── cli/                # Credit Liquidity Index
│   ├── treasury/           # Treasury domain (yields, curves)
│   ├── stablecoins/        # Stablecoin analytics
│   ├── currencies/         # DXY, FX pairs
│   ├── crypto/             # Regimes, CAI, narratives
│   ├── fed_forecasts/      # FOMC, inflation, labor
│   ├── macro_regime/       # Combined regime scoring
│   └── offshore/           # Offshore liquidity
├── scrapers/               # Data scrapers
│   ├── scraper_commodities.py
│   └── scraper_indexes.py
├── tests/                  # Test suite
│   ├── test_domains.py     # Domain processor tests
│   ├── test_etf_data_v2.py
│   └── test_offshore.py
├── treasury/               # Treasury data modules (external)
│   ├── treasury_data.py    # Treasury maturity data
│   ├── treasury_auction_demand.py # Auction demand metrics
│   └── treasury_refinancing_signal.py # QRA analysis
├── utils/                  # Utilities and diagnostics
│   ├── tv_client.py        # TradingView client
│   ├── generate_mock_data.py
│   └── check_*.py          # Diagnostic scripts
├── data_pipeline.py        # Main data processing script
├── orchestrator.py         # Domain coordination
└── data/
    └── domains/            # Domain JSON outputs
```

---

## Domain Processors

### Core Domains

| Domain | File | Purpose | References |
|--------|------|---------|------------|
| **SharedDomain** | `core/__init__.py` | Dates, BTC price, CB balance sheets | - |
| **GLIDomain** | `core/__init__.py` | Global Liquidity Index aggregation | `shared.central_banks` |
| **M2Domain** | `core/__init__.py` | Global M2 Money Supply | `shared` (FX rates) |
| **USSystemDomain** | `core/__init__.py` | Fed, TGA, RRP, Net Liquidity | `shared.central_banks.fed` |

### Feature Domains

| Domain | File | Purpose | References |
|--------|------|---------|------------|
| **CLIDomain** | `cli/__init__.py` | Credit Liquidity Index | - |
| **TreasuryDomain** | `treasury/__init__.py` | Yields, curves, spreads | - |
| **StablecoinsDomain** | `stablecoins/__init__.py` | Stablecoin supply, depegs | `shared.btc` |
| **CurrenciesDomain** | `currencies/__init__.py` | DXY, FX pairs | `shared.btc` |
| **CryptoDomain** | `crypto/__init__.py` | Regimes, CAI, narratives | `shared.btc`, `stablecoins.total` |
| **FedForecastsDomain** | `fed_forecasts/__init__.py` | Inflation, labor, Fed policy | `treasury.tips` |
| **MacroRegimeDomain** | `macro_regime/__init__.py` | Combined regime scoring | `cli.total`, `gli.total` |
| **OffshoreDomain** | `offshore/__init__.py` | Eurodollar stress | - |

---

## Key Files

### `base.py` - Core Utilities

```python
# Utility functions
clean_for_json(obj)           # Convert Pandas/NumPy to JSON-serializable
calculate_rocs(series)        # Multi-period ROC (1M, 3M, 6M, 1Y)
calculate_zscore(series)      # Rolling Z-score
rolling_percentile(series)    # Rolling percentile rank

# Base class
class BaseDomain:
    name: str                 # Domain identifier
    process(df, **kwargs)     # Main processing logic
    validate(data)            # Schema validation
    save_json(data, dir)      # Save to file
```

### `orchestrator.py` - Coordination

```python
class DataOrchestrator:
    def __init__(self, output_dir):
        # Register domains in dependency order
        self._domains = [
            MetadataDomain(),
            SharedDomain(),      # Must be first (shared data)
            GLIDomain(),
            M2Domain(),
            USSystemDomain(),
            CLIDomain(),
            TreasuryDomain(),
            StablecoinsDomain(),
            CurrenciesDomain(),
            CryptoDomain(),
            FedForecastsDomain(),
            MacroRegimeDomain(),
            OffshoreDomain(),
        ]
    
    def run(self, df):
        # Process all domains
        for domain in self._domains:
            data = domain.process(df, **self._results)
            domain.save_json(data, self.output_dir)
```

### `db_adapter.py` - Database Client

```python
class SupabaseAdapter:
    def upsert_domain_data(table, data, on_conflict='date')
    def get_latest_date(table) -> str
    def query_domain(table, start_date, end_date) -> List[Dict]
```

---

## Data Deduplication Strategy

To avoid duplicating data across domains:

| Shared Data | Source | Used By |
|-------------|--------|---------|
| `dates` | SharedDomain | All domains |
| `btc.price` | SharedDomain | Currencies, Stablecoins, Crypto |
| `central_banks.*` | SharedDomain | GLI, USSystem, M2 |
| `cli.total` | CLIDomain | MacroRegime |
| `stablecoins.total` | StablecoinsDomain | Crypto |

Domains use **references** instead of copying:

```python
result = {
    'btc_price_ref': 'shared.btc',  # Reference, not duplicate
    'calculated_data': ...          # Domain-specific calculations
}
```

---

## Migration Path to PostgreSQL

Each domain has a corresponding JSON schema that maps to PostgreSQL:

```python
# domains/schemas/currencies.py

CURRENCIES_DDL = """
CREATE TABLE domain_currencies_dxy (
    date DATE PRIMARY KEY,
    absolute DECIMAL(10, 4),
    roc_7d DECIMAL(8, 4),
    ...
);
"""
```

Migration steps:
1. Generate DDL from schemas
2. Create tables in Supabase
3. Modify `save_json()` → `save_to_db()`
4. Add API endpoints

---

## Running Tests

```bash
cd backend
python -m pytest tests/test_domains.py -v
```

---

## Adding a New Domain

1. Create folder: `domains/new_domain/__init__.py`
2. Implement `BaseDomain` subclass
3. Add to `domains/__init__.py` exports
4. Register in `orchestrator.py`
5. Add tests to `tests/test_domains.py`

Example:

```python
from ..base import BaseDomain, clean_for_json

class NewDomain(BaseDomain):
    @property
    def name(self) -> str:
        return "new_domain"
    
    def process(self, df, **kwargs):
        return {
            'metric': clean_for_json(df['COLUMN'].ffill()),
        }
```
