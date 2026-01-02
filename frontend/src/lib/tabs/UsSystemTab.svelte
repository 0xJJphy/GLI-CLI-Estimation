<script>
    /**
     * UsSystemTab.svelte
     * Displays US Federal Reserve system liquidity components.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";

    // Core props only
    export let darkMode = false;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges (no longer props)
    let netLiqRange = "ALL";
    let reservesRange = "ALL";
    let fedRange = "ALL";
    let rrpRange = "ALL";
    let tgaRange = "ALL";

    // --- Internal Helper Functions ---
    function getLastDate(seriesKey) {
        if (!dashboardData.last_dates) return "N/A";
        const key = seriesKey.toUpperCase();
        return (
            dashboardData.last_dates[key] ||
            dashboardData.last_dates[key + "_USD"] ||
            dashboardData.last_dates[seriesKey] ||
            "N/A"
        );
    }

    function getLatestValue(series) {
        if (!series || !Array.isArray(series) || series.length === 0) return 0;
        for (let i = series.length - 1; i >= 0; i--) {
            if (series[i] !== null && series[i] !== undefined) return series[i];
        }
        return 0;
    }

    // --- Internal Chart Data Processing ---

    // Net Liquidity Chart
    $: netLiqData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq,
                name: "US Net Liquidity",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        netLiqRange,
    );

    // Bank Reserves Chart
    $: bankReservesData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq_reserves,
                name: "Bank Reserves (T)",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(34, 197, 94, 0.05)",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq,
                name: "Net Liquidity (T)",
                type: "scatter",
                mode: "lines",
                line: {
                    color: "#3b82f6",
                    width: 2,
                    dash: "dot",
                    shape: "spline",
                },
                yaxis: "y2",
            },
        ],
        dashboardData.dates,
        reservesRange,
    );

    $: bankReservesLayout = {
        yaxis: { title: "Reserves (T)", side: "left", showgrid: false },
        yaxis2: {
            title: "Net Liq (T)",
            overlaying: "y",
            side: "right",
            showgrid: false,
        },
        legend: { orientation: "h", y: 1.1 },
    };

    // Fed Assets Chart
    $: fedData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.fed,
                name: "Fed Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        fedRange,
    );

    // RRP Chart
    $: rrpData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq_rrp,
                name: "Fed RRP (T)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(239, 68, 68, 0.05)",
            },
        ],
        dashboardData.dates,
        rrpRange,
    );

    // TGA Chart
    $: tgaData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq_tga,
                name: "TGA (T)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(245, 158, 11, 0.05)",
            },
        ],
        dashboardData.dates,
        tgaRange,
    );

    // US System Metrics (computed internally)
    $: usSystemMetrics = dashboardData.us_system_rocs
        ? Object.entries(dashboardData.us_system_rocs).map(([id, data]) => {
              const labels = {
                  fed: "Fed Assets",
                  rrp: "Fed RRP",
                  tga: "Treasury TGA",
              };
              return {
                  id,
                  name: labels[id] || id.toUpperCase(),
                  isLiability: id !== "fed",
                  m1: data["1M"]?.[data["1M"].length - 1] || 0,
                  m3: data["3M"]?.[data["3M"].length - 1] || 0,
                  y1: data["1Y"]?.[data["1Y"].length - 1] || 0,
                  imp1: data["impact_1m"]?.[data["impact_1m"].length - 1] || 0,
                  imp3: data["impact_3m"]?.[data["impact_3m"].length - 1] || 0,
                  imp1y: data["impact_1y"]?.[data["impact_1y"].length - 1] || 0,
                  delta1: data["delta_1m"]?.[data["delta_1m"].length - 1] || 0,
                  delta3: data["delta_3m"]?.[data["delta_3m"].length - 1] || 0,
                  delta1y: data["delta_1y"]?.[data["delta_1y"].length - 1] || 0,
              };
          })
        : [];

    $: usSystemTotal = usSystemMetrics.reduce(
        (acc, item) => {
            return {
                delta1: acc.delta1 + item.delta1,
                imp1: acc.imp1 + item.imp1,
                delta3: acc.delta3 + item.delta3,
                imp3: acc.imp3 + item.imp3,
                delta1y: acc.delta1y + item.delta1y,
                imp1y: acc.imp1y + item.imp1y,
            };
        },
        { delta1: 0, imp1: 0, delta3: 0, imp3: 0, delta1y: 0, imp1y: 0 },
    );

    // Current values in Trillions for chart labels
    $: latestNetLiq = getLatestValue(dashboardData.us_net_liq);
    $: latestFedAssets = getLatestValue(dashboardData.gli?.fed);
    $: latestRRP = getLatestValue(dashboardData.us_net_liq_rrp);
    $: latestTGA = getLatestValue(dashboardData.us_net_liq_tga);
    $: latestReserves = getLatestValue(dashboardData.us_net_liq_reserves);
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
                        <span
                            class="current-value-badge"
                            style="margin-left: 12px; background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                        >
                            ${latestNetLiq.toFixed(2)}T
                        </span>
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
                    <div class="metrics-table-container">
                        <table class="metrics-table">
                            <thead>
                                <tr>
                                    <th>Acc</th>
                                    <th>1M</th>
                                    <th title="Absolute change in Billions USD"
                                        >Δ$1M</th
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
                                                (item.isLiability &&
                                                    item.m1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m1 < 0) ||
                                                (item.isLiability &&
                                                    item.m1 > 0)}
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
                                                : ""}{item.delta1.toFixed(
                                                0,
                                            )}B</td
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
                                                (item.isLiability &&
                                                    item.m3 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m3 < 0) ||
                                                (item.isLiability &&
                                                    item.m3 > 0)}
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
                                                (item.isLiability &&
                                                    item.y1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.y1 < 0) ||
                                                (item.isLiability &&
                                                    item.y1 > 0)}
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
                                        class:positive={usSystemTotal.delta1 >
                                            0}
                                        class:negative={usSystemTotal.delta1 <
                                            0}
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
                    </div>
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
                    <div class="metrics-table-container">
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
                                            ? translations.liquid_env ||
                                              "Liquid"
                                            : getLatestValue(
                                                    dashboardData
                                                        .us_system_metrics
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
                                                    dashboardData
                                                        .us_system_metrics
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
                                                    dashboardData
                                                        .us_system_metrics
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
                                            ? translations.regime_qe ||
                                              "QE Mode"
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
    </div>

    <!-- Bank Reserves Chart -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_bank_reserves ||
                            "Bank Reserves vs Net Liquidity"}
                        <span
                            class="current-value-badge"
                            style="margin-left: 12px; background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                        >
                            ${latestReserves.toFixed(2)}T
                        </span>
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
                    <div class="metrics-table-container">
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
                                        >{translations.roc_3m || "3M ROC"} (Res)</td
                                    >
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
                                                    dashboardData
                                                        .reserves_metrics
                                                        ?.spread_zscore,
                                                ) < -1
                                              ? translations.reserves_low_stress ||
                                                "Low Stress"
                                              : translations.reserves_normal ||
                                                "Normal"}</td
                                    >
                                </tr>
                                <tr>
                                    <td
                                        >{translations.momentum ||
                                            "Momentum"}</td
                                    >
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
                                                dashboardData.reserves_metrics
                                                    ?.lcr,
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
    </div>

    <!-- Fed Assets Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>
                {translations.chart_fed_assets || "Fed Assets (USD Trillion)"}
                <span
                    class="current-value-badge"
                    style="margin-left: 12px; background: rgba(59, 130, 246, 0.15); color: #3b82f6; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                >
                    ${latestFedAssets.toFixed(2)}T
                </span>
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
            <h3>
                {translations.chart_rrp || "Fed RRP Facility"}
                <span
                    class="current-value-badge"
                    style="margin-left: 12px; background: rgba(239, 68, 68, 0.15); color: #ef4444; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                >
                    ${latestRRP.toFixed(2)}T
                </span>
            </h3>
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
                <span
                    class="current-value-badge"
                    style="margin-left: 12px; background: rgba(245, 158, 11, 0.15); color: #f59e0b; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                >
                    ${latestTGA.toFixed(2)}T
                </span>
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
