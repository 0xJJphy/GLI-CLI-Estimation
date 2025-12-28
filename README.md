# GLI & CLI Liquidity Dashboard

A premium, real-time macro liquidity monitoring dashboard that tracks the Global Liquidity Index (GLI) and Credit Liquidity Index (CLI) across **15+ central banks** and **14+ M2 money supply economies**.

## 🚀 Features

-   **Hybrid Data Sourcing**: Combines 50+ years of FRED historical depth with TradingView's sub-weekly freshness.
-   **Dual-Source Toggle**: Switch between **FRED Baseline** (M3 money supply proxies) and **TV Hybrid** (Central Bank Balance Sheets).
-   **Regime Optimization (New)**: Automated offset (lead) optimization using walk-forward validation to identify the most predictive lead-time for Bitcoin regimes.
-   **Central Bank Breadth & Concentration**: Track "% of Central Banks expanding" (Breadth) and HHI-based concentration metrics to identify global liquidity synchronization.
-   **Quant V2 Strategy**: Enhanced Bitcoin fair value model using ElasticNet (automatic feature selection), PCA-based liquidity factors, and rolling volatility bands.
-   **Bilingual Support (EN/ES)**: Integrated English and Spanish translations with persistent language selection.
-   **Premium Dark Mode**: High-contrast, accessibility-aware dark theme for all charts and UI components.
-   **15 Central Banks**: FED, ECB, BoJ, BoE, PBoC, BoC, RBA, RBI, SNB, CBR, BCB, BoK, RBNZ, SR, BNM.
-   **14 M2 Economies**: US, EU, China, Japan, UK, Canada, Australia, India, Switzerland, Russia, Brazil, Korea, Mexico, Malaysia (and others).

## 📊 Data & Formulas

### 1. Global Liquidity Index (GLI)
Measures the aggregated balance sheets of **15 central banks** converted to USD.

**Advanced Metrics**:
-   **Breadth (Diffusion)**: Percentage of central banks whose balance sheets are expanding over a 13-week period.
-   **Concentration (HHI)**: Herfindahl-Hirschman Index applied to liquidity contributions to detect "Liquidity Fragility" (over-reliance on one CB).
-   **Impulse & Acceleration**: 13-week velocity and change in velocity of liquidity flows.

### 2. Macro Regime Score
The "Heart" of the dashboard, centered at 50 (Neutral):
$$Score = 50 + 15 \times Total\_Z$$
-   **Liquidity (70%)**: GLI, US Net Liquidity, M2, Breadth, and HHI.
-   **Credit (30%)**: CLI Level and Momentum.
-   **Brakes (Negative)**: Real Rate Shocks, Repo Stress, and Reserves Scarcity.

### 3. US Net Liquidity Matrix
The "Real" liquidity available to the US market:
$$Net Liquidity = Fed Assets - TGA (Treasury General Account) - RRP (Reverse Repo)$$

### 4. Bitcoin Quant V2 Model
Advanced predictive model for BTC valuation:
-   **ElasticNet CV**: Automatic selection of lags (1-8 weeks) for Macro features.
-   **PCA Liquidity Factor**: Reduces dimensionality and collinearity between different central banks.
-   **Adaptive Bands**: 1σ and 2σ bands based on 52-week rolling volatility instead of fixed history.
-   **Quarterly Reset**: Fair value rebalanced every 13 weeks to avoid cumulative drift while remaining tradeable.

## 🛠️ Setup & Usage

### Prerequisites
-   Python 3.10+
-   Node.js & npm

### Installation
1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/0xJJphy/GLI-CLI-Estimation.git
    cd GLI-CLI-Estimation
    ```
2.  **Backend Setup**:
    ```bash
    cd backend
    pip install -r requirements.txt
    # Configure .env with FRED_API_KEY, TV_USERNAME, TV_PASSWORD
    ```
3.  **Frontend Setup**:
    ```bash
    cd ../frontend
    npm install
    ```

### Running the Dashboard
1.  **Data Synchronization**:
    ```bash
    cd frontend
    npm run data:sync
    ```
    *This runs the data pipeline AND the regime optimization script automatically.*
2.  **Start Dev Server**:
    ```bash
    npm run dev
    ```

## 📦 Pipeline Automation
The project includes a robust automation flow:
1.  `data_pipeline.py`: Fetches and processes cross-border liquidity data.
2.  `train_regime_offset.py`: Optimizes the lead-time for the regime indicators.
3.  `data:sync`: Ensures all processed data and optimization parameters are correctly positioned for the Svelte frontend.

## 📄 License
MIT
