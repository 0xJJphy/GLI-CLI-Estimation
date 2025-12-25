# GLI & CLI Liquidity Dashboard

A premium, real-time macro liquidity monitoring dashboard that tracks the Global Liquidity Index (GLI) and Credit Liquidity Index (CLI) across 5 major central banks.

![Dashboard Preview](file:///C:/Users/Pedro/.gemini/antigravity/brain/a3e247ba-0844-4ed9-afa4-fc3ad7a3b656/uploaded_image_1766599141852.png)

## 🚀 Features

-   **Hybrid Data Sourcing**: Combines 50+ years of FRED historical depth with TradingView's sub-weekly freshness.
-   **Dual-Source Toggle**: Switch between **FRED Baseline** (M3 money supply proxies) and **TV Hybrid** (Central Bank Balance Sheets).
-   **US Net Liquidity**: Real-time monitoring of the Fed's impact on markets ($FED Assets - TGA - RRP$).
-   **Inter-Market Analysis**: Integrated Risk Model with VIX and High-Yield Spread monitoring.
-   **₿ Bitcoin Analysis**: Fair value model based on GLI/CLI regression with deviation bands and correlation analysis.
-   **Responsive Design**: Modern, glassmorphism-inspired UI with smooth micro-animations.

## 📊 Data & Formulas

### 1. Global Liquidity Index (GLI)
Measures the aggregated balance sheets of the big 5 central banks (FED, ECB, BoJ, BoE, PBoC) converted to USD.

-   **TV Hybrid Mode**: Uses direct **Central Bank Assets** (ECONOMICS symbols). Total magnitude: **~$26T**.
-   **FRED Mode**: Uses **Money Supply (M3)** proxies where assets are stale. Total magnitude: **~$60T**.

### 2. US Net Liquidity
The "Real" liquidity available to the US market:
$$Net Liquidity = Fed Assets - TGA (Treasury General Account) - RRP (Reverse Repo)$$

### 3. Credit Liquidity Index (CLI)
A Z-Score based index measuring credit conditions:
-   Components: HY Spread, IG Spread, NFCI Credit/Risk, Lending Standards, and VIX.

### 4. Bitcoin Fair Value Model
The dashboard provides two distinct quantitative models for Bitcoin valuation:

1.  **Macro-Only Model**: 
    - **Formula**: `log(BTC) ~ β₁·GLI + β₂·CLI + β₃·VIX + β₄·NetLiq`
    - **Focus**: Pure liquidity-driven valuation. It identifies how much of Bitcoin's price is explained solely by global monetary expansion and risk conditions.

2.  **Adoption-Adjusted Model (Power Law)**:
    - **Formula**: `log(BTC) ~ β₀·log(DaysSinceGenesis) + β₁·GLI + β₂·CLI + β₃·VIX + β₄·NetLiq`
    - **Focus**: Combines the secular adoption trend (Power Law) with macro cyclicality. Uses **Ridge Regression** to handle the interplay between time and liquidity.

**Features**:
- **12+ Years of Data**: Models trained on daily data since 2012.
- **Log-Space Analysis**: Ensures percentage-based accuracy across orders of magnitude.
- **Dynamic Deviation Bands**: Proportional ±1σ and ±2σ Standard Deviation zones.
- **Institutional Charting**: Interactive charts powered by **TradingView Lightweight Charts** (featuring log-scale and fluid zoom).

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

## 🔒 Security
No API keys or credentials are stored in the repository. All secrets are managed via `.env` files which are ignored by Git.

## 📄 License
MIT
