# GLI & CLI Liquidity Dashboard

A premium, real-time macro liquidity monitoring dashboard that tracks the **Global Liquidity Index (GLI)** and **Credit Liquidity Index (CLI)** across **15+ central banks** and **14+ M2 money supply economies**.

Built with **Svelte + Vite** frontend and **Python** modular domain architecture, featuring FRED and TradingView data sources for comprehensive market coverage.

---

## 🚀 Key Features

### Core Analytics
- **Hybrid Data Sourcing**: Combines 50+ years of FRED historical depth with TradingView's sub-weekly freshness
- **Modular Domain Architecture**: Independently testable data domains for scalability
- **Regime Optimization**: Automated offset (lead) optimization using walk-forward validation for Bitcoin regime prediction
- **Signal Framework**: Unified signal configuration with single source of truth thresholds

### Tabs & Views

| Tab | Description |
|-----|-------------|
| **Dashboard** | Main overview with GLI/CLI metrics and regime status |
| **Global Flows (CB)** | Central bank balance sheets across 15+ economies |
| **Global M2** | M2 money supply tracking for 14+ currencies |
| **US System** | Fed balance sheet, RRP, TGA, Bank Reserves, Net Liquidity |
| **US Debt** | Treasury maturity tracker and refinancing metrics |
| **Risk Model** | CLI components, Fed Rate Corridor, credit spreads, volatility |
| **Fed Forecasts** | FOMC calendar, dot plot, macro indicators |
| **Regimes** | CLI V1/V2 comparison, regime scoring |
| **Offshore Liquidity** | Eurodollar stress, XCCY basis, CB swap lines |
| **Stablecoins** | Crypto stablecoin supply, SFAI regimes, depeg events |
| **Currencies** | DXY analysis, major currency pairs |
| **BTC Analysis** | Fair value models, correlation with liquidity |
| **Chart Explorer** | TradingView-powered multi-indicator charting |

---

## 📊 Data Architecture

### Backend Structure

```
backend/
├── domains/                    # Modular data processors (NEW)
│   ├── base.py                 # BaseDomain + utilities
│   ├── core/                   # CLI, GLI, US System, M2
│   ├── currencies/             # FX analytics
│   ├── stablecoins/            # Crypto stables + SFAI
│   ├── crypto/                 # BTC/ETH analysis
│   ├── macro_regime/           # Regime V2 calculations
│   ├── offshore/               # Eurodollar liquidity
│   ├── treasury/               # US debt maturities
│   └── fed_forecasts/          # FOMC, dot plot
│
├── analytics/                  # Calculation modules
│   ├── regime_v2.py            # Regime detection
│   ├── offshore_liquidity.py   # XCCY basis
│   └── crypto_analytics.py     # Fear & Greed, narratives
│
├── config/                     # Configuration
│   └── signal_config.py        # Single source of truth for thresholds
│
├── connectors/                 # External data
│   ├── etf_data.py             # BTC ETF flows
│   └── db_adapter.py           # Database connection
│
├── treasury/                   # Treasury-specific
│   ├── treasury_data.py
│   ├── treasury_auction_demand.py
│   └── treasury_refinancing_signal.py
│
├── orchestrator.py             # Domain orchestration
├── data_pipeline.py            # Main data processing
└── tests/                      # Domain tests
```

### Frontend Structure

```
frontend/src/lib/
├── components/                 # Reusable UI
│   ├── Chart.svelte            # Plotly wrapper
│   ├── LightweightChart.svelte # TradingView charts
│   ├── TimeRangeSelector.svelte
│   ├── StatsCard.svelte
│   └── StressPanel.svelte
│
├── tabs/                       # View components
│   ├── Dashboard2.svelte
│   ├── RiskModelTab.svelte
│   ├── UsSystemTab.svelte
│   └── ... (20 tabs)
│
└── utils/
    ├── domainLoader.js         # Modular data loading
    ├── helpers.js              # Shared utilities
    └── signalSchema.js         # Signal constants
```

### Data Sources

| Source | Coverage | Frequency | Use Case |
|--------|----------|-----------|----------|
| **FRED API** | 50+ years | Daily | Baseline economic data |
| **TradingView** | Real-time | Sub-weekly | Central bank balance sheets |
| **Fed Calendar** | Scraped | Daily | FOMC meeting dates |
| **Treasury API** | FiscalData.gov | Daily | Debt maturities, auctions |
| **BoJ XLSX** | 2000-present | Daily | JPY call rate for XCCY |

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- FRED API Key (free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html))

### Installation

```bash
# Clone
git clone https://github.com/0xJJphy/GLI-CLI-Estimation.git
cd GLI-CLI-Estimation

# Backend
cd backend
pip install -r requirements.txt
echo "FRED_API_KEY=your_key" > .env

# Frontend
cd ../frontend
npm install
```

### Running

```bash
# Sync data (fetches all sources + optimizes regime params)
cd frontend
npm run data:sync

# Development server
npm run dev

# Production build
npm run build && npm run preview
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | Yes | FRED API key |
| `TV_USERNAME` | No | TradingView login |
| `TV_PASSWORD` | No | TradingView password |
| `SUPABASE_URL` | No | Database URL |
| `SUPABASE_KEY` | No | Database key |

### Key Formulas

**Global Liquidity Index (GLI):**
```
GLI = Σ(Central Bank Assets × FX Rate) for 15 CBs
Breadth = % CBs expanding over 13 weeks
```

**US Net Liquidity:**
```
Net Liquidity = Fed Assets - TGA - RRP
```

**Fed Rate Corridor:**
```
SRF Rate (Ceiling) ─── Fed lending rate
       │
   SOFR ─────────── Market rate
       │
   IORB ─────────── Fed deposit rate (floor)
```

---

## 📁 Documentation

See `/docs` for detailed documentation:
- [DATA_ARCHITECTURE.md](docs/DATA_ARCHITECTURE.md) - Domain architecture details
- [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) - Complete file reference
- [ETF_DATABASE.md](docs/ETF_DATABASE.md) - ETF data schema

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 📧 Contact

- **GitHub**: [@0xJJphy](https://github.com/0xJJphy)
- **Project**: [github.com/0xJJphy/GLI-CLI-Estimation](https://github.com/0xJJphy/GLI-CLI-Estimation)
