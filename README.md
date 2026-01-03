# GLI & CLI Liquidity Dashboard

A premium, real-time macro liquidity monitoring dashboard that tracks the **Global Liquidity Index (GLI)** and **Credit Liquidity Index (CLI)** across **15+ central banks** and **14+ M2 money supply economies**.

Built with **Svelte + Vite** frontend and **Python** data pipeline, featuring FRED and TradingView data sources for comprehensive market coverage.

---

## 🚀 Key Features

### Core Analytics
- **Hybrid Data Sourcing**: Combines 50+ years of FRED historical depth with TradingView's sub-weekly freshness
- **Dual-Source Toggle**: Switch between **FRED Baseline** (M3 money supply proxies) and **TV Hybrid** (Central Bank Balance Sheets)
- **Regime Optimization**: Automated offset (lead) optimization using walk-forward validation for Bitcoin regime prediction
- **Central Bank Breadth & Concentration**: Track "% of Central Banks expanding" (Breadth) and HHI-based concentration metrics

### Market Stress Analysis (Risk Model Tab)
- **Multi-Dimensional Stress Scoring**: Automated scoring across 27 indicators in 4 dimensions:
  - **Inflation Stress** (5 indicators): CPI, PCE, TIPS Breakeven, Inflation Expectations
  - **Liquidity Stress** (7 indicators): RRP, TGA, Bank Reserves, Net Liquidity, Fed Momentum
  - **Credit Stress** (8 indicators): HY/IG Spreads, BAA-AAA Spread, NFCI components, Lending Standards
  - **Volatility Stress** (7 indicators): VIX, MOVE, FX Vol, Treasury Yield Volatility, Swap Spreads

- **Fed Rate Corridor (NEW)**:
  - Standing Repo Facility (SRF) Rate as the lending ceiling
  - Interest on Reserve Balances (IORB) as the primary floor
  - Overnight RRP Award Rate as the absolute floor
  - **SRF Usage Indicator Panel**: Separate bar chart showing Fed backstop operations volume
  - Real-time spread calculations (SOFR-IORB, Gap to Ceiling)
  - Stress level detection: NORMAL / ELEVATED / HIGH

- **Credit Spreads Dashboard**: HY Spread, IG Spread, BAA-AAA Yield Spread with Z-Score normalization
- **Yield Curve Analysis**: 10Y-2Y, 30Y-10Y, 30Y-2Y spreads with inversion detection
- **TIPS Analysis**: Real rates, breakeven inflation, 5Y5Y forward expectations

### Fed Forecasts Tab
- **FOMC Calendar**: Scraped from Federal Reserve with live countdown to next meeting
- **Dot Plot Visualization**: Fed rate projections from palewire/fed-dot-plot-scraper
- **Macro Indicators**: CPI, Core CPI, PCE, Core PCE, ISM PMI (Mfg/Svc), Unemployment, Fed Funds Rate
- **Rate of Change (ROC) Badges**: 1-month momentum indicators on key metrics
- **Treasury Bond Settlements Table**: Upcoming Treasury issuance with RRP coverage ratios and risk levels

- **US System Tab (NEW)**:
- **Current Value Labels**: Each chart now displays current balance in **$T (Trillions)**:
  - Net Liquidity: Green badge
  - Bank Reserves: Green badge
  - Fed Assets: Blue badge
  - Fed RRP: Red badge
  - Treasury TGA: Amber badge
- **Component Impact Table**: 1M/3M/1Y ROC with liquidity impact percentages
- **Liquidity Score**: Composite metric for regime detection

### US Debt Tab (NEW)
- **Treasury Maturity Tracker**: Real-time visualization of upcoming US debt maturities
- **Debt Categorization**: Detailed breakdown by security type: Bills, Notes, Bonds, TIPS, and FRN
- **Key Refinancing Metrics**:
  - **Peak Maturity Month**: Identifies upcoming refinancing "cliffs"
  - **Refinancing Volume**: Next 12 months' mandatory rollover amount
  - **Bills Outstanding**: Short-term debt concentration tracking
- **Dual-View Charting**: Toggle between **Stacked Bar** (composition) and **Multi-Line** (trend) views
- **Monthly Schedule Table**: Tabular breakdown of the next 12 months' maturities in $B (Billions)

### Bitcoin Analysis
- **Quant V2 Model**: ElasticNet with automatic feature selection, PCA liquidity factors, 52-week rolling volatility bands
- **Fair Value Estimation**: Quarterly reset to avoid cumulative drift
- **Correlation Analysis**: Optimal lag detection between liquidity signals and BTC returns

### Offshore Liquidity Tab (NEW)
- **Offshore Dollar Stress Monitoring**: Tracks USD funding pressure in shadow banking & Eurodollar markets
- **FRED Proxy Indicators**:
  - **OBFR-EFFR Spread**: Offshore vs onshore funding cost differential
  - **Fed CB Swap Lines**: Central Bank USD liquidity swaps volume
- **DIY XCCY Basis**: Synthetic cross-currency basis from FX spot/futures pairs (EUR/USD, USD/JPY, GBP/USD)
- **Stress Scoring**: Composite 0-100 score with calibrated thresholds (Normal/Elevated/Stressed/Critical)

### UI/UX
- **Bilingual Support**: English and Spanish with persistent language selection
- **Premium Dark Mode**: High-contrast, accessibility-aware theme
- **Responsive Design**: Optimized for standard desktops without horizontal scrolling
- **Signal-Integrated Styling**: Dynamic color-coding for bullish/bearish indicators

---

## 📊 Data Architecture

### Data Sources

| Source | Coverage | Frequency | Use Case |
|--------|----------|-----------|----------|
| **FRED API** | 50+ years history | Daily | Baseline economic data |
| **TradingView** | Real-time | Sub-weekly | Central bank balance sheets |
| **Fed Calendar** | Scraped | Daily | FOMC meeting dates |
| **Dot Plot Scraper** | palewire | Per-meeting | Fed rate projections |
| **Treasury Fiscal Data** | API | Daily | Treasury settlements |

### FRED Series Configuration

```python
# Key Series (sample)
'SOFR': 'SOFR',                      # Secured Overnight Financing Rate
'IORB': 'IORB',                      # Interest on Reserve Balances
'SRFTSYD': 'SRF_RATE',               # Standing Repo Facility Rate (Ceiling)
'RRPONTSYAWARD': 'RRP_AWARD',        # ON RRP Award Rate (Floor)
'RPONTSYD': 'SRF_USAGE',             # SRF Operations Volume ($B)
'SOFRVOL': 'SOFR_VOLUME',            # SOFR Transaction Volume
# ... 50+ additional series
```

### Key Formulas

#### Global Liquidity Index (GLI)
Aggregated balance sheets of 15 central banks converted to USD:
- **Breadth (Diffusion)**: % of CBs expanding over 13 weeks
- **Concentration (HHI)**: Herfindahl-Hirschman Index for fragility detection
- **Impulse & Acceleration**: 13-week velocity and momentum

#### Macro Regime Score
Centered at 50 (Neutral):
```
Score = 50 + 15 × Total_Z
```
- **Liquidity (70%)**: GLI, US Net Liquidity, M2, Breadth, HHI
- **Credit (30%)**: CLI Level and Momentum
- **Brakes**: Real Rate Shocks, Repo Stress, Reserves Scarcity

#### US Net Liquidity
```
Net Liquidity = Fed Assets - TGA - RRP
```

#### Fed Rate Corridor
```
SRF Rate (Ceiling) ─── Fed lending rate
       │
   SOFR ─────────── Market rate (should stay in corridor)
       │
   IORB ─────────── Fed deposit rate (primary floor)
       │
RRP Award ────────── Absolute floor
```

**Stress Detection Logic:**
- Gap to ceiling < 5 bps → HIGH stress
- SOFR-IORB spread > 10 bps → ELEVATED stress
- SRF Usage > 0 → Immediate stress signal

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- FRED API Key (free at [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html))

### Installation

1. **Clone the Repository**:
```bash
git clone https://github.com/0xJJphy/GLI-CLI-Estimation.git
cd GLI-CLI-Estimation
```

2. **Backend Setup**:
```bash
cd backend
pip install -r requirements.txt

# Create .env file with credentials
echo "FRED_API_KEY=your_api_key_here" > .env
echo "TV_USERNAME=optional_tradingview_username" >> .env
echo "TV_PASSWORD=optional_tradingview_password" >> .env
```

3. **Frontend Setup**:
```bash
cd ../frontend
npm install
```

### Running the Dashboard

1. **Data Synchronization** (fetches all data and optimizes regime parameters):
```bash
cd frontend
npm run data:sync
```

2. **Start Development Server**:
```bash
npm run dev
```

3. **Build for Production**:
```bash
npm run build
npm run preview
```

---

## 📁 Project Structure

```
GLI-CLI-Estimation/
├── backend/
│   ├── data_pipeline.py         # Main data processing (50+ FRED series)
│   ├── treasury_data.py         # US Debt maturity API integration
│   ├── train_regime_offset.py   # Regime walk-forward optimization
│   ├── regime_v2.py             # Regime detection logic
│   ├── requirements.txt         # Python dependencies
│   └── data/                    # Generated JSON data files
│       ├── dashboard_data.json
│       ├── fred_cache_data.json
│       ├── treasury_maturities_cache.json
│       ├── treasury_settlements_cache.json
│       └── regime_params.json
│
├── frontend/
│   ├── src/
│   │   ├── App.svelte           # Main application with tab routing
│   │   ├── app.css              # Global CSS variables and themes
│   │   ├── lib/
│   │   │   ├── components/      # Reusable UI components
│   │   │   │   ├── Chart.svelte
│   │   │   │   ├── LightweightChart.svelte
│   │   │   │   ├── TimeRangeSelector.svelte
│   │   │   │   └── StressPanel.svelte
│   │   │   ├── tabs/            # Tab view components
│   │   │   │   ├── DashboardTab.svelte
│   │   │   │   ├── GlobalFlowsCbTab.svelte
│   │   │   │   ├── GlobalM2Tab.svelte
│   │   │   │   ├── UsSystemTab.svelte
│   │   │   │   ├── UsDebtTab.svelte
│   │   │   │   ├── RiskModelTab.svelte
│   │   │   │   ├── BtcAnalysisTab.svelte
│   │   │   │   ├── BtcQuantV2Tab.svelte
│   │   │   │   └── FedForecastsTab.svelte
│   │   │   ├── utils/helpers.js # Shared utility functions
│   │   │   └── stores/          # Svelte stores
│   │   └── main.js              # Application entry point
│   ├── public/                  # Static assets
│   │   └── dashboard_data.json  # Copied from backend
│   ├── vite.config.js           # Vite build configuration
│   └── package.json             # NPM dependencies
│
├── docs/
│   └── PROJECT_STRUCTURE.md     # Detailed file documentation
│
└── README.md                    # This file
```

---

## 📦 Pipeline Automation

The data pipeline runs in sequence:

1. **`data_pipeline.py`**: 
   - Fetches 51 FRED series with 24-hour cache
   - Fetches 54 TradingView symbols with 6-hour cache
   - Scrapes FOMC calendar and Dot Plot
   - Calculates market stress analysis (27 indicators)
   - Generates Fed Rate Corridor metrics
   - Outputs to `dashboard_data.json`

2. **`train_regime_offset.py`**:
   - Walk-forward validation for regime parameters
   - Optimizes lead-time (offset) for BTC prediction
   - Outputs to `regime_params.json`

3. **`npm run data:sync`**:
   - Runs both scripts in sequence
   - Copies data to frontend/public/

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FRED_API_KEY` | Yes | FRED API key for economic data |
| `TV_USERNAME` | No | TradingView login (for additional data) |
| `TV_PASSWORD` | No | TradingView password |

### Cache Settings

| Data Type | Cache Duration | File |
|-----------|---------------|------|
| FRED Data | 24 hours | `fred_cache_data.json` |
| TradingView Data | 6 hours | `tv_cache_data.json` |
| Treasury Maturities | 24 hours | `treasury_maturities_cache.json` |
| Treasury Settlements | 24 hours | `treasury_settlements_cache.json` |
| Cache Timestamps | N/A | `data_cache_info.json` |

---

## 📈 Recent Updates (January 2026)

### Fed Rate Corridor Enhancement
- Added **SRFTSYD** (SRF Rate), **RRPONTSYAWARD** (RRP Award), **RPONTSYD** (SRF Usage) FRED series
- New SRF Usage indicator panel below main corridor chart
- Color-coded stress levels based on spread analysis
- Removed overlapping regime shading for cleaner visualization

### US System Tab Improvements
- Added current value labels ($T) to all chart headers
- Color-coded badges matching each chart's theme
- Reactive real-time updates

### US Debt Tab (NEW)
- **Treasury Maturity Tracker**: Integrated with FiscalData.Treasury.gov API
- **Refinancing Metrics**: Automated calculation of next 12-month rollover requirements
- **Multi-Line Analysis**: Visualize trend divergence between Bills, Notes, and Bonds
- **Performance Caching**: 24-hour persistent cache for Treasury maturity data

### Treasury Settlements
- Fixed data access path in FedForecastsTab
- Pagination, filtering, and grouped/individual view modes

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Contact

- **GitHub**: [@0xJJphy](https://github.com/0xJJphy)
- **Project Link**: [https://github.com/0xJJphy/GLI-CLI-Estimation](https://github.com/0xJJphy/GLI-CLI-Estimation)
