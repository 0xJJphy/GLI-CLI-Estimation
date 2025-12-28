<script>
    /**
     * UsSystemTab.svelte
     * Displays US Federal Reserve system liquidity components.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};

    // Chart data
    export let netLiqData = [];
    export let bankReservesData = [];
    export let bankReservesLayout = {};
    export let fedData = [];
    export let rrpData = [];
    export let tgaData = [];

    // Metrics
    export let usSystemMetrics = [];
    export let usSystemTotal = { delta1: 0, imp1: 0, imp3: 0, imp1y: 0 };

    // Helper functions
    export let getLastDate = (bank) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;

    // Time range states - managed locally
    let netLiqRange = "ALL";
    let reservesRange = "ALL";
    let fedRange = "ALL";
    let rrpRange = "ALL";
    let tgaRange = "ALL";
</script>

<div class="main-charts">
    <!-- Net Liquidity Chart with Metrics Sidebar -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_us_net_liq ||
                            "US Net Liquidity Trends"}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={netLiqRange}
                            onRangeChange={(r) => (netLiqRange = r)}
                        />
                        <span class="last-date"
                            >{translations.last_data || "Last Data:"}
                            {getLastDate("FED")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.net_liq ||
                        "Fed Balance Sheet minus TGA and RRP."}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={netLiqData} />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.chart_us_comp ||
                            "US System Components Impact"}
                    </h4>
                    <table class="metrics-table">
                        <thead>
                            <tr>
                                <th>{translations.account || "Account"}</th>
                                <th>1M</th>
                                <th title="Absolute change in Billions USD"
                                    >$ Δ1M</th
                                >
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                                <th>3M</th>
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                                <th>1Y</th>
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            {#each usSystemMetrics as item}
                                <tr>
                                    <td>{item.name}</td>
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.m1 > 0) ||
                                            (item.isLiability && item.m1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.m1 < 0) ||
                                            (item.isLiability && item.m1 > 0)}
                                        >{item.m1.toFixed(1)}%</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.delta1 > 0) ||
                                            (item.isLiability &&
                                                item.delta1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.delta1 < 0) ||
                                            (item.isLiability &&
                                                item.delta1 > 0)}
                                        >{item.delta1 > 0
                                            ? "+"
                                            : ""}{item.delta1.toFixed(0)}B</td
                                    >
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp1 > 0}
                                        class:negative={item.imp1 < 0}
                                        >{item.imp1.toFixed(2)}%</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.m3 > 0) ||
                                            (item.isLiability && item.m3 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.m3 < 0) ||
                                            (item.isLiability && item.m3 > 0)}
                                        >{item.m3.toFixed(1)}%</td
                                    >
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp3 > 0}
                                        class:negative={item.imp3 < 0}
                                        >{item.imp3.toFixed(2)}%</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.y1 > 0) ||
                                            (item.isLiability && item.y1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.y1 < 0) ||
                                            (item.isLiability && item.y1 > 0)}
                                        >{item.y1.toFixed(1)}%</td
                                    >
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp1y > 0}
                                        class:negative={item.imp1y < 0}
                                        >{item.imp1y.toFixed(2)}%</td
                                    >
                                </tr>
                            {/each}
                            <tr class="total-row">
                                <td><strong>TOTAL</strong></td>
                                <td>-</td>
                                <td
                                    class="roc-val"
                                    class:positive={usSystemTotal.delta1 > 0}
                                    class:negative={usSystemTotal.delta1 < 0}
                                    >{usSystemTotal.delta1 > 0
                                        ? "+"
                                        : ""}{usSystemTotal.delta1.toFixed(
                                        0,
                                    )}B</td
                                >
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp1 > 0}
                                    class:negative={usSystemTotal.imp1 < 0}
                                    >{usSystemTotal.imp1.toFixed(2)}%</td
                                >
                                <td>-</td>
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp3 > 0}
                                    class:negative={usSystemTotal.imp3 < 0}
                                    >{usSystemTotal.imp3.toFixed(2)}%</td
                                >
                                <td>-</td>
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp1y > 0}
                                    class:negative={usSystemTotal.imp1y < 0}
                                    >{usSystemTotal.imp1y.toFixed(2)}%</td
                                >
                            </tr>
                        </tbody>
                    </table>
                    <p
                        style="font-size: 10px; color: #94a3b8; margin-top: 8px;"
                    >
                        {translations.impact_note_us ||
                            "* Imp = Contribution to US Net Liquidity change."}
                    </p>
                </div>

                <!-- Composite Liquidity Metrics -->
                <div
                    class="metrics-section"
                    style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(148, 163, 184, 0.2);"
                >
                    <h4>{translations.liquidity_score || "Liquidity Score"}</h4>
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Value</th>
                                <th>Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td
                                    >{translations.liquidity_score ||
                                        "Liquidity Score"}</td
                                >
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.liquidity_score,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.liquidity_score,
                                    ) < 0}
                                    >{(
                                        getLatestValue(
                                            dashboardData.us_system_metrics
                                                ?.liquidity_score,
                                        ) ?? 0
                                    ).toFixed(2)}</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.liquidity_score,
                                    ) > 1}
                                    class:minus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.liquidity_score,
                                    ) < -1}
                                    >{getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.liquidity_score,
                                    ) > 1
                                        ? translations.liquid_env || "Liquid"
                                        : getLatestValue(
                                                dashboardData.us_system_metrics
                                                    ?.liquidity_score,
                                            ) < -1
                                          ? translations.dry_env || "Dry"
                                          : "—"}</td
                                >
                            </tr>
                            <tr>
                                <td
                                    >{translations.netliq_roc ||
                                        "Net Liq ROC"}</td
                                >
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_roc_20d,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_roc_20d,
                                    ) < 0}
                                    >{(
                                        getLatestValue(
                                            dashboardData.us_system_metrics
                                                ?.netliq_roc_20d,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_roc_20d,
                                    ) > 2}
                                    class:minus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_roc_20d,
                                    ) < -2}
                                    >{getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_roc_20d,
                                    ) > 2
                                        ? "Risk-ON"
                                        : getLatestValue(
                                                dashboardData.us_system_metrics
                                                    ?.netliq_roc_20d,
                                            ) < -2
                                          ? "Risk-OFF"
                                          : "—"}</td
                                >
                            </tr>
                            <tr>
                                <td>Δ4W NetLiq</td>
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_delta_4w,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_delta_4w,
                                    ) < 0}
                                    >{(
                                        (getLatestValue(
                                            dashboardData.us_system_metrics
                                                ?.netliq_delta_4w,
                                        ) ?? 0) * 1000
                                    ).toFixed(0)}B</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_delta_4w,
                                    ) > 0.1}
                                    class:minus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_delta_4w,
                                    ) < -0.1}
                                    >{getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.netliq_delta_4w,
                                    ) > 0.1
                                        ? "Bullish"
                                        : getLatestValue(
                                                dashboardData.us_system_metrics
                                                    ?.netliq_delta_4w,
                                            ) < -0.1
                                          ? "Bearish"
                                          : "—"}</td
                                >
                            </tr>
                            <tr>
                                <td
                                    >{translations.fed_momentum_label ||
                                        "Fed Momentum"}</td
                                >
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.fed_momentum,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.fed_momentum,
                                    ) < 0}
                                    >{(
                                        getLatestValue(
                                            dashboardData.us_system_metrics
                                                ?.fed_momentum,
                                        ) ?? 0
                                    ).toFixed(3)}T</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.fed_momentum,
                                    ) > 0}
                                    class:minus={getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.fed_momentum,
                                    ) < 0}
                                    >{getLatestValue(
                                        dashboardData.us_system_metrics
                                            ?.fed_momentum,
                                    ) > 0
                                        ? translations.regime_qe || "QE Mode"
                                        : translations.regime_qt ||
                                          "QT Mode"}</td
                                >
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Bank Reserves Chart -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_bank_reserves ||
                            "Bank Reserves vs Net Liquidity"}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={reservesRange}
                            onRangeChange={(r) => (reservesRange = r)}
                        />
                        <span class="last-date"
                            >{translations.last_data || "Last Data:"}
                            {getLastDate("RESBALNS")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.bank_reserves ||
                        "Total reserves at Federal Reserve Banks."}
                </p>
                <div class="chart-content">
                    <Chart
                        {darkMode}
                        data={bankReservesData}
                        layout={bankReservesLayout}
                    />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.reserves_velocity || "Reserves Velocity"}
                    </h4>
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Value</th>
                                <th>Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{translations.roc_3m || "3M ROC"} (Res)</td>
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.reserves_roc_3m,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.reserves_roc_3m,
                                    ) < 0}
                                    >{(
                                        getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.reserves_roc_3m,
                                    ) > 0}
                                    class:minus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.reserves_roc_3m,
                                    ) < 0}
                                    >{getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.reserves_roc_3m,
                                    ) > 0
                                        ? "QE"
                                        : "QT"}</td
                                >
                            </tr>
                            <tr>
                                <td
                                    >{translations.spread_zscore ||
                                        "Spread Z-Score"}</td
                                >
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.spread_zscore,
                                    ) < -1}
                                    class:negative={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.spread_zscore,
                                    ) > 2}
                                    >{(
                                        getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) ?? 0
                                    ).toFixed(2)}</td
                                >
                                <td
                                    class="signal-cell"
                                    class:minus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.spread_zscore,
                                    ) > 2}
                                    class:plus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.spread_zscore,
                                    ) < -1}
                                    >{getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.spread_zscore,
                                    ) > 2
                                        ? translations.reserves_high_stress ||
                                          "High Stress"
                                        : getLatestValue(
                                                dashboardData.reserves_metrics
                                                    ?.spread_zscore,
                                            ) < -1
                                          ? translations.reserves_low_stress ||
                                            "Low Stress"
                                          : translations.reserves_normal ||
                                            "Normal"}</td
                                >
                            </tr>
                            <tr>
                                <td>{translations.momentum || "Momentum"}</td>
                                <td
                                    class="roc-val"
                                    class:positive={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.momentum,
                                    ) > 0}
                                    class:negative={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.momentum,
                                    ) < 0}
                                    >{(
                                        getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) ?? 0
                                    ).toFixed(4)}T</td
                                >
                                <td
                                    class="signal-cell"
                                    class:plus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.momentum,
                                    ) > 0}
                                    class:minus={getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.momentum,
                                    ) < 0}
                                    >{getLatestValue(
                                        dashboardData.reserves_metrics
                                            ?.momentum,
                                    ) > 0
                                        ? translations.reserves_bullish ||
                                          "Bullish"
                                        : translations.reserves_bearish ||
                                          "Bearish"}</td
                                >
                            </tr>
                            <tr>
                                <td>{translations.lcr || "LCR"}</td>
                                <td class="roc-val"
                                    >{(
                                        getLatestValue(
                                            dashboardData.reserves_metrics?.lcr,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td class="signal-cell"
                                    >{getLatestValue(
                                        dashboardData.reserves_metrics?.lcr,
                                    ) < 30
                                        ? "⚠️"
                                        : "✓"}</td
                                >
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <!-- Fed Assets Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>
                {translations.chart_fed_assets || "Fed Assets (USD Trillion)"}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={fedRange}
                    onRangeChange={(r) => (fedRange = r)}
                />
                <span class="last-date"
                    >{translations.last_data || "Last Data:"}
                    {getLastDate("FED")}</span
                >
            </div>
        </div>
        <p class="chart-description">
            {translations.gli_cb || "Fed balance sheet assets."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={fedData} />
        </div>
        <div
            class="roc-inline"
            style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
        >
            <span>ROC:</span>
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["1M"],
                ) > 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["1M"],
                ) < 0}
                >1M: {(
                    getLatestValue(dashboardData.us_system_rocs?.fed?.["1M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["3M"],
                ) > 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["3M"],
                ) < 0}
                >3M: {(
                    getLatestValue(dashboardData.us_system_rocs?.fed?.["3M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["1Y"],
                ) > 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["1Y"],
                ) < 0}
                >1Y: {(
                    getLatestValue(dashboardData.us_system_rocs?.fed?.["1Y"]) ??
                    0
                ).toFixed(1)}%</span
            >
        </div>
    </div>

    <!-- RRP Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>{translations.chart_rrp || "Fed RRP Facility"}</h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={rrpRange}
                    onRangeChange={(r) => (rrpRange = r)}
                />
                <span class="last-date"
                    >{translations.last_data || "Last Data:"}
                    {getLastDate("RRP")}</span
                >
            </div>
        </div>
        <p class="chart-description">
            {translations.rrp || "Reverse Repo drains liquidity."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={rrpData} />
        </div>
        <div
            class="roc-inline"
            style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
        >
            <span>ROC:</span>
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["1M"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["1M"],
                ) > 0}
                >1M: {(
                    getLatestValue(dashboardData.us_system_rocs?.rrp?.["1M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["3M"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["3M"],
                ) > 0}
                >3M: {(
                    getLatestValue(dashboardData.us_system_rocs?.rrp?.["3M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["1Y"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["1Y"],
                ) > 0}
                >1Y: {(
                    getLatestValue(dashboardData.us_system_rocs?.rrp?.["1Y"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span style="margin-left: auto; color: #94a3b8;"
                >{getLatestValue(dashboardData.us_system_rocs?.rrp?.["1M"]) < 0
                    ? language === "en"
                        ? "↓ Draining (bullish)"
                        : "↓ Drenando (alcista)"
                    : language === "en"
                      ? "↑ Filling (bearish)"
                      : "↑ Llenando (bajista)"}</span
            >
        </div>
    </div>

    <!-- TGA Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>
                {translations.chart_tga || "Treasury General Account (TGA)"}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={tgaRange}
                    onRangeChange={(r) => (tgaRange = r)}
                />
                <span class="last-date"
                    >{translations.last_data || "Last Data:"}
                    {getLastDate("TGA")}</span
                >
            </div>
        </div>
        <p class="chart-description">
            {translations.tga || "TGA spending = liquidity injection."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={tgaData} />
        </div>
        <div
            class="roc-inline"
            style="display: flex; gap: 12px; margin-top: 8px; font-size: 11px;"
        >
            <span>ROC:</span>
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["1M"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["1M"],
                ) > 0}
                >1M: {(
                    getLatestValue(dashboardData.us_system_rocs?.tga?.["1M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["3M"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["3M"],
                ) > 0}
                >3M: {(
                    getLatestValue(dashboardData.us_system_rocs?.tga?.["3M"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span
                class:positive={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["1Y"],
                ) < 0}
                class:negative={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["1Y"],
                ) > 0}
                >1Y: {(
                    getLatestValue(dashboardData.us_system_rocs?.tga?.["1Y"]) ??
                    0
                ).toFixed(1)}%</span
            >
            <span style="margin-left: auto; color: #94a3b8;"
                >{getLatestValue(dashboardData.us_system_rocs?.tga?.["1M"]) < 0
                    ? language === "en"
                        ? "↓ Spending (bullish)"
                        : "↓ Gastando (alcista)"
                    : language === "en"
                      ? "↑ Accumulating (bearish)"
                      : "↑ Acumulando (bajista)"}</span
            >
        </div>
    </div>
</div>
