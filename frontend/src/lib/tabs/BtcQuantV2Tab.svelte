<script>
    /**
     * BtcQuantV2Tab.svelte
     * Displays the Quant v2 Bitcoin fair value model with advanced econometric features.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";

    // Props
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Chart data
    export let quantV2ChartData = [];
    export let quantV2RebalancedData = [];
    export let quantV2ReturnsData = [];

    // Helper function
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;
</script>

<div class="main-charts">
    <!-- Model Description -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>
                🧪 {translations.quant_v2_title ||
                    "Quant v2: Enhanced Bitcoin Fair Value Model"}
            </h3>
            <span class="last-date"
                >Weekly Δlog returns + ElasticNet + PCA GLI Factor</span
            >
        </div>
        <div class="quant-description">
            <p>
                {translations.quant_v2_desc ||
                    "This model addresses econometric issues in the legacy model:"}
            </p>
            <ul>
                <li>
                    {translations.quant_v2_weekly ||
                        "Weekly frequency (W-FRI) instead of daily to avoid autocorrelation"}
                </li>
                <li>
                    {translations.quant_v2_log ||
                        "Δlog(BTC) returns instead of log levels (avoids spurious regression)"}
                </li>
                <li>
                    {translations.quant_v2_elastic ||
                        "ElasticNet with 1-8 week lags for automatic feature selection"}
                </li>
                <li>
                    {translations.quant_v2_pca ||
                        "PCA GLI factor instead of raw sum (handles colinearity)"}
                </li>
                <li>
                    {translations.quant_v2_vol ||
                        "Rolling 52-week volatility for adaptive bands"}
                </li>
            </ul>
        </div>
    </div>

    <!-- OOS Metrics Panel -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>📈 {translations.oos_metrics || "Out-of-Sample Metrics"}</h3>
        </div>
        <div class="quant-metrics">
            <div class="metric-item">
                <span class="metric-label">OOS RMSE</span>
                <span class="metric-value"
                    >{(
                        dashboardData.btc?.models?.quant_v2?.metrics
                            ?.oos_rmse || 0
                    ).toFixed(4)}</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">OOS MAE</span>
                <span class="metric-value"
                    >{(
                        dashboardData.btc?.models?.quant_v2?.metrics?.oos_mae ||
                        0
                    ).toFixed(4)}</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">Hit Rate</span>
                <span class="metric-value highlight"
                    >{(
                        (dashboardData.btc?.models?.quant_v2?.metrics
                            ?.hit_rate || 0) * 100
                    ).toFixed(2)}%</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">R² In-Sample</span>
                <span class="metric-value"
                    >{(
                        (dashboardData.btc?.models?.quant_v2?.metrics
                            ?.r2_insample || 0) * 100
                    ).toFixed(2)}%</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">Active Features</span>
                <span class="metric-value"
                    >{dashboardData.btc?.models?.quant_v2?.metrics
                        ?.n_active_features || 0}</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">Frequency</span>
                <span class="metric-value"
                    >{dashboardData.btc?.models?.quant_v2?.frequency ||
                        "weekly"}</span
                >
            </div>
        </div>
    </div>

    <!-- Model Parameters -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>⚙️ {translations.model_params || "Model Parameters"}</h3>
        </div>
        <div class="quant-metrics">
            <div class="metric-item">
                <span class="metric-label">Alpha (λ)</span>
                <span class="metric-value"
                    >{(
                        dashboardData.btc?.models?.quant_v2?.metrics?.alpha || 0
                    ).toFixed(6)}</span
                >
            </div>
            <div class="metric-item">
                <span class="metric-label">L1 Ratio</span>
                <span class="metric-value"
                    >{dashboardData.btc?.models?.quant_v2?.metrics?.l1_ratio ||
                        0}</span
                >
            </div>
        </div>
    </div>

    <!-- Fair Value Chart (Cumulative) -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>₿ Bitcoin: Quant v2 Fair Value (Weekly - Cumulative)</h3>
            <span class="last-date"
                >⚠️ Cumulative drift may cause divergence over time</span
            >
        </div>
        <div class="chart-content tv-chart-wrap">
            <LightweightChart
                {darkMode}
                data={quantV2ChartData}
                logScale={true}
            />
        </div>
    </div>

    <!-- Rebalanced Fair Value Chart -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>₿ Bitcoin: Rebalanced Fair Value (Quarterly Reset)</h3>
            <span class="last-date"
                >✅ Resets to actual price every 13 weeks to avoid drift</span
            >
        </div>
        <div class="chart-content tv-chart-wrap">
            <LightweightChart
                {darkMode}
                data={quantV2RebalancedData}
                logScale={true}
            />
        </div>
    </div>

    <!-- Returns Comparison Chart -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>📊 Weekly Returns: Predicted vs Actual (%)</h3>
            <span class="last-date"
                >Orange bars = Actual | Green line = Predicted</span
            >
        </div>
        <div class="chart-content">
            <Chart {darkMode} data={quantV2ReturnsData} />
        </div>
    </div>

    <!-- Active Features List -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>🎯 Active Features (Selected by ElasticNet)</h3>
        </div>
        <div class="features-grid">
            {#each Object.entries(dashboardData.btc?.models?.quant_v2?.active_features || {}) as [feature, coef]}
                <div
                    class="feature-item"
                    class:positive={coef > 0}
                    class:negative={coef < 0}
                >
                    <span class="feature-name">{feature}</span>
                    <span class="feature-coef">{coef.toFixed(4)}</span>
                </div>
            {/each}
        </div>
    </div>

    <!-- Current Valuation -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>📊 Current Valuation (Quant v2)</h3>
        </div>
        <div class="btc-stats">
            <div class="btc-stat-item">
                <span class="btc-label"
                    >{translations.btc_price || "BTC Price"}</span
                >
                <span class="btc-value price"
                    >${getLatestValue(
                        dashboardData.btc?.models?.quant_v2?.btc_price,
                    )?.toLocaleString() || "N/A"}</span
                >
            </div>
            <div class="btc-stat-item">
                <span class="btc-label"
                    >{translations.fair_value || "Fair Value"}</span
                >
                <span class="btc-value fair"
                    >${Math.round(
                        getLatestValue(
                            dashboardData.btc?.models?.quant_v2?.fair_value,
                        ) || 0,
                    ).toLocaleString()}</span
                >
            </div>
            <div class="btc-stat-item">
                <span class="btc-label"
                    >{translations.deviation || "Deviation"}</span
                >
                <span
                    class="btc-value deviation"
                    class:overvalued={getLatestValue(
                        dashboardData.btc?.models?.quant_v2?.deviation_pct,
                    ) > 0}
                    class:undervalued={getLatestValue(
                        dashboardData.btc?.models?.quant_v2?.deviation_pct,
                    ) < 0}
                >
                    {getLatestValue(
                        dashboardData.btc?.models?.quant_v2?.deviation_pct,
                    )?.toFixed(1) || "0"}%
                </span>
            </div>
            <div class="btc-stat-item">
                <span class="btc-label">{translations.zscore || "Z-Score"}</span
                >
                <span
                    class="btc-value zscore"
                    class:extreme={Math.abs(
                        getLatestValue(
                            dashboardData.btc?.models?.quant_v2
                                ?.deviation_zscore,
                        ) || 0,
                    ) > 2}
                >
                    {getLatestValue(
                        dashboardData.btc?.models?.quant_v2?.deviation_zscore,
                    )?.toFixed(2) || "0"}σ
                </span>
            </div>
        </div>
    </div>
</div>
