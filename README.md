# GLI & CLI Liquidity Dashboard

A premium, real-time macro liquidity monitoring dashboard that tracks the Global Liquidity Index (GLI) and Credit Liquidity Index (CLI) across **16 central banks** and **14 M2 money supply economies**.

## 🚀 Features

-   **Hybrid Data Sourcing**: Combines 50+ years of FRED historical depth with TradingView's sub-weekly freshness.
-   **Dual-Source Toggle**: Switch between **FRED Baseline** (M3 money supply proxies) and **TV Hybrid** (Central Bank Balance Sheets).
-   **16 Central Banks**: FED, ECB, BoJ, BoE, PBoC, BoC, RBA, RBI, SNB, CBR, BCB, BoK, RBNZ, Riksbank, BNM.
-   **14 M2 Economies**: US, EU, China, Japan, UK, Canada, Australia, India, Switzerland, Russia, Brazil, Korea, Mexico, Indonesia, South Africa, Malaysia, Sweden.
-   **Multi-Timeframe Impact Analysis**: High-density 1M, 3M, and 1Y impact metrics for every GLI constituent, M2 economy, and US system component.
-   **US System Plumbing**: Dedicated charts for **Reverse Repo (RRP)** and **Treasury General Account (TGA)** to track the precise distribution of US liquidity.
-   **US Net Liquidity Matrix**: Breakdown of Fed Assets, RRP, and TGA contributions to the total net liquidity change.
-   **Time Range Controls**: 1M, 3M, 6M, 1Y, 3Y, ALL buttons for each chart for flexible visualization.
-   **Inter-Market Analysis**: Integrated Risk Model with VIX and High-Yield Spread monitoring.
-   **₿ Bitcoin Analysis**: Fair value model based on GLI/CLI regression with deviation bands and correlation analysis.
-   **Responsive Design**: Modern, glassmorphism-inspired UI with high-density quantitative metrics.

## 📊 Data & Formulas

### 1. Global Liquidity Index (GLI)
Measures the aggregated balance sheets of **16 central banks** converted to USD.

**Banks included**: FED, ECB, BoJ, BoE, PBoC + BoC (Canada), RBA (Australia), RBI (India), SNB (Switzerland), CBR (Russia), BCB (Brazil), BoK (Korea), RBNZ (New Zealand), Riksbank (Sweden), BNM (Malaysia).

-   **TV Hybrid Mode**: Uses direct **Central Bank Assets** (ECONOMICS symbols). Total magnitude: **~$30T+**.
-   **FRED Mode**: Uses **Money Supply (M3)** proxies where assets are stale.

### 2. Global M2 Money Supply
Aggregated M2 money supply from **14 major economies** converted to USD trillions.

### 3. US Net Liquidity
The "Real" liquidity available to the US market:
$$Net Liquidity = Fed Assets - TGA (Treasury General Account) - RRP (Reverse Repo)$$

### 4. Credit Liquidity Index (CLI)
A Z-Score based index measuring credit conditions:
-   Components: HY Spread, IG Spread, NFCI Credit/Risk, Lending Standards, and VIX.

### 5. Bitcoin Fair Value Model
Two distinct quantitative models for Bitcoin valuation:

1.  **Macro-Only Model**: 
    - **Formula**: `log(BTC) ~ β₁·GLI + β₂·CLI + β₃·VIX + β₄·NetLiq`

2.  **Adoption-Adjusted Model (Power Law)**:
    - **Formula**: `log(BTC) ~ β₀·log(DaysSinceGenesis) + β₁·GLI + β₂·CLI + β₃·VIX + β₄·NetLiq`

## 🛠️ Setup & Usage

### Prerequisites
-   Python 3.10+
-   Node.js & npm

### Backend Setup
1.  Install dependencies: `pip install pandas fredapi tvdatafeed python-dotenv`
2.  Configure `.env`:
    ```env
    FRED_API_KEY=your_key
    TV_USERNAME=your_username
    TV_PASSWORD=your_password
    ```
3.  Run the pipeline: `python backend/data_pipeline.py`

### Frontend Setup
1.  Install dependencies: `npm install`
2.  Sync data and start dev server: `npm run dev`

## 📦 Data Pipeline

The data pipeline supports:
- **Smart interval fallback**: Daily → Weekly → Monthly for ECONOMICS data
- **Pre-1970 timestamp protection**: Caps n_bars to avoid Windows OSError
- **Automatic relogin**: Retries with exponential backoff
- **Data freshness checking**: Cache system to avoid redundant API calls

## 🔒 Security
No API keys or credentials are stored in the repository. All secrets are managed via `.env` files which are ignored by Git.

## 📄 License
MIT
