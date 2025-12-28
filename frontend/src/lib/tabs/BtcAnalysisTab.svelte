<script>
    /**
     * BtcAnalysisTab.svelte
     * Displays BTC Fair Value Model and lag correlation analysis.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let translations = {};
    export let latestStats = {};
    export let dashboardData = {};

    // Chart data
    export let btcFairValueData = [];
    export let lagCorrelationChartData = {};
    export let correlationData = {};

    // Helper function
    export let getLatestROC = (rocs, period) =>
        rocs?.[period]?.[rocs?.[period]?.length - 1] ?? 0;

    // Local state (exported for binding)
    export let btcRange = "ALL";
    export let selectedBtcModel = "macro";
    export let selectedLagWindow = "7d";

    $: formattedLagData = lagCorrelationChartData?.[selectedLagWindow]
        ? [
              {
                  x: lagCorrelationChartData[selectedLagWindow].lags,
                  y: lagCorrelationChartData[
                      selectedLagWindow
                  ].correlations.map((c) => (c !== null ? c * 100 : null)),
                  name: `${selectedLagWindow.toUpperCase()} ROC Lag Correlation`,
                  type: "bar",
                  marker: {
                      color: lagCorrelationChartData?.[
                          selectedLagWindow
                      ]?.lags?.map((l) =>
                          l ===
                          lagCorrelationChartData?.[selectedLagWindow]
                              ?.optimal_lag
                              ? "#10b981"
                              : "#6366f1",
                      ),
                  },
              },
          ]
        : [];
    $: formattedCorrData = Array.isArray(correlationData)
        ? correlationData
        : Object.values(correlationData || {});
</script>

<div class="main-charts btc-analysis-view">
    <!-- Header -->
    <div class="analysis-header">
        <h2>{translations.btc_analysis_title || "BTC Fair Value Model"}</h2>
        <p class="description">
            {translations.btc_analysis_desc ||
                "Bitcoin fair value derived from global liquidity, M2, and credit conditions."}
        </p>
    </div>

    <!-- BTC Stats -->
    <div class="btc-stats">
        <div
            class="btc-stat-item"
            class:signal-bullish={latestStats?.btc?.deviation_pct < -5}
            class:signal-bearish={latestStats?.btc?.deviation_pct > 5}
        >
            <span class="btc-label"
                >{translations.current_valuation || "Current Valuation"}</span
            >
            <div
                class="btc-value"
                class:text-bearish={latestStats?.btc?.deviation_pct > 5}
                class:text-bullish={latestStats?.btc?.deviation_pct < -5}
            >
                {((latestStats?.btc?.deviation_pct || 0) > 0 ? "+" : "") +
                    (latestStats?.btc?.deviation_pct || 0).toFixed(1)}%
            </div>
        </div>
        <div class="btc-stat-item">
            <span class="btc-label"
                >{translations.btc_price || "BTC Price"}</span
            >
            <span class="btc-value"
                >${Math.round(
                    latestStats?.btc?.price || 0,
                ).toLocaleString()}</span
            >
        </div>
        <div class="btc-stat-item">
            <span class="btc-label"
                >{translations.fair_value || "Fair Value"}</span
            >
            <span class="btc-value"
                >${Math.round(
                    latestStats?.btc?.fair_value || 0,
                ).toLocaleString()}</span
            >
        </div>
        <div
            class="btc-stat-item"
            class:signal-bullish={latestStats?.btc?.deviation_zscore < -1}
            class:signal-bearish={latestStats?.btc?.deviation_zscore > 1}
        >
            <span class="btc-label">{translations.zscore || "Z-Score"}</span>
            <span
                class="btc-value"
                class:text-bearish={latestStats?.btc?.deviation_zscore > 1}
                class:text-bullish={latestStats?.btc?.deviation_zscore < -1}
                >{(latestStats?.btc?.deviation_zscore || 0).toFixed(2)}σ</span
            >
        </div>
    </div>

    <!-- Fair Value Chart -->
    <div
        class="chart-card wide"
        class:signal-bullish={latestStats?.btc?.deviation_pct < -5}
        class:signal-bearish={latestStats?.btc?.deviation_pct > 5}
    >
        <div class="chart-header">
            <h3>{translations.btc_analysis_title || "BTC Fair Value Model"}</h3>
            <div class="header-controls">
                <div class="model-toggle">
                    <button
                        class="toggle-btn"
                        class:active={selectedBtcModel === "macro"}
                        on:click={() => (selectedBtcModel = "macro")}
                        >Macro Liquidity</button
                    >
                    <button
                        class="toggle-btn"
                        class:active={selectedBtcModel === "adoption"}
                        on:click={() => (selectedBtcModel = "adoption")}
                        >Macro + Adoption</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={btcRange}
                    onRangeChange={(r) => (btcRange = r)}
                />
            </div>
        </div>
        <p class="chart-description">
            {translations.btc_fair ||
                "BTC fair value derived from macro liquidity factors."}
        </p>
        <div class="chart-content tv-chart-wrap">
            <LightweightChart
                {darkMode}
                data={btcFairValueData}
                logScale={true}
            />
            <div class="debug-chart-info">
                Points: {btcFairValueData[0]?.data?.length || 0}
            </div>
        </div>
    </div>

    <!-- Lag Analysis Chart -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>
                {translations.lag_analysis ||
                    "Predictive Signals: CLI → BTC Lag Analysis"}
            </h3>
            <div class="header-controls">
                <div class="model-toggle">
                    <button
                        class="toggle-btn"
                        class:active={selectedLagWindow === "7d"}
                        on:click={() => (selectedLagWindow = "7d")}
                        >7-Day</button
                    >
                    <button
                        class="toggle-btn"
                        class:active={selectedLagWindow === "14d"}
                        on:click={() => (selectedLagWindow = "14d")}
                        >14-Day</button
                    >
                    <button
                        class="toggle-btn"
                        class:active={selectedLagWindow === "30d"}
                        on:click={() => (selectedLagWindow = "30d")}
                        >30-Day</button
                    >
                </div>
            </div>
        </div>
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-content" style="height: 350px;">
                    <Chart {darkMode} data={formattedLagData} />
                </div>
            </div>
            <div class="metrics-sidebar">
                <div class="interp-card">
                    <h4>{translations.interpretation || "Interpretation"}</h4>
                    <div class="metric-row">
                        <span>{translations.optimal_lag || "Optimal Lag"}</span>
                        <span class="val"
                            >{dashboardData.predictive?.lag_correlations?.[
                                selectedLagWindow
                            ]?.optimal_lag || 0}W</span
                        >
                    </div>
                    <div class="metric-row">
                        <span
                            >{translations.max_correlation ||
                                "Max Correlation"}</span
                        >
                        <span class="val"
                            >{(
                                (dashboardData.predictive?.lag_correlations?.[
                                    selectedLagWindow
                                ]?.max_correlation || 0) * 100
                            ).toFixed(1)}%</span
                        >
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Cross-Correlation Chart -->
    <div class="chart-card wide">
        <div class="chart-header">
            <h3>Cross-Correlation Analysis (90-Day Window)</h3>
            <span class="last-date"
                >Negative lag = indicator leads BTC | Positive lag = BTC leads
                indicator</span
            >
        </div>
        <div class="chart-content">
            <Chart {darkMode} data={formattedCorrData} />
        </div>
    </div>

    <!-- ROC Comparison -->
    <div class="chart-card wide">
        <h4 style="margin-top: 0;">Momentum Comparison (ROC %)</h4>
        <div class="metrics-table-container">
            <div class="roc-grid">
                <div class="roc-row header">
                    <div class="roc-col">Asset</div>
                    <div class="roc-col">1M</div>
                    <div class="roc-col">3M</div>
                    <div class="roc-col">6M</div>
                    <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.btc_price || "BTC Price"}
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.btc?.rocs, "1M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.btc?.rocs, "3M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.btc?.rocs, "6M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class:plus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.btc?.rocs,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.btc?.rocs, "1Y").toFixed(
                            2,
                        )}%
                    </div>
                </div>
                <!-- ... other rows ... -->
                <div class="roc-row">
                    <div class="roc-col label">Global GLI</div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "1M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "3M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "6M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "1Y").toFixed(
                            2,
                        )}%
                    </div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        US {translations.stat_us_net || "Net Liquidity"}
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ).toFixed(2)}%
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Interpretation Panel -->
    <div class="interp-section wide">
        <h4>📊 {translations.interpretation || "Interpretation"}</h4>
        <div class="interp-grid">
            <div class="interp-item">
                <span class="interp-label"
                    >{translations.fair_value || "Fair Value"} Model</span
                >
                <span class="interp-val">
                    {translations.interp_regression || "Regression using:"}<br
                    />
                    • {translations.interp_gli_lag || "GLI (45-day lag)"}<br />
                    • {translations.interp_cli_lag || "CLI (14-day lag)"}<br />
                    • {translations.interp_vix_coin || "VIX (coincident)"}<br />
                    • {translations.interp_netliq_lag ||
                        "US Net Liq (30-day lag)"}
                </span>
            </div>
            <div class="interp-item">
                <span class="interp-label"
                    >{translations.interp_zones || "Deviation Zones"}</span
                >
                <span class="interp-val">
                    • <span
                        class="extreme-zone"
                        style="color: #ef4444; font-weight: 600;"
                        >{translations.interp_extreme ||
                            "±2σ: Extreme over/undervaluation"}</span
                    ><br />
                    •
                    <span
                        class="moderate-zone"
                        style="color: #f59e0b; font-weight: 600;"
                        >{translations.interp_moderate ||
                            "±1σ: Moderate deviation"}</span
                    ><br />
                    • {translations.interp_fair_range ||
                        "Within ±1σ: Fair value range"}
                </span>
            </div>
            <div class="interp-item">
                <span class="interp-label"
                    >{translations.interp_signals || "Trading Signals"}</span
                >
                <span class="interp-val">
                    • <strong style="color: #10b981;"
                        >{translations.interp_profittaking ||
                            "Z > +2: Consider profit-taking"}</strong
                    ><br />
                    •
                    <strong style="color: #10b981;"
                        >{translations.interp_accumulation ||
                            "Z < -2: Potential accumulation"}</strong
                    ><br />
                    •
                    <strong style="color: #6366f1;"
                        >{translations.interp_divergence ||
                            "ROC divergence: Momentum shifts"}</strong
                    >
                </span>
            </div>
        </div>
    </div>
</div>
