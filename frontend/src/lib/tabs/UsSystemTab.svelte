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
    let netRepoRange = "2Y";

    // Card container references for full-card download feature
    let netLiqCard;
    let reservesCard;
    let fedAssetsCard;
    let rrpCard;
    let tgaCard;
    let netRepoCard;

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
                name: translations.reserves_t || "Bank Reserves (T)",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(34, 197, 94, 0.05)",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.us_net_liq,
                name: translations.net_liq_t || "Net Liquidity (T)",
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
        yaxis: {
            title: translations.reserves_axis || "Reserves (T)",
            side: "left",
            showgrid: false,
            autorange: true,
        },
        yaxis2: {
            title: translations.net_liq_axis || "Net Liq (T)",
            overlaying: "y",
            side: "right",
            showgrid: false,
            autorange: true,
        },
        legend: { orientation: "h", y: 1.1 },
        shapes: [
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 3.0,
                y1: 3.0,
                line: {
                    color: "rgba(34, 197, 94, 0.4)",
                    width: 2,
                    dash: "dash",
                },
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 2.5,
                y1: 2.5,
                line: {
                    color: "rgba(239, 68, 68, 0.4)",
                    width: 2,
                    dash: "dash",
                },
            },
        ],
        annotations: [
            {
                xref: "paper",
                yref: "y",
                x: 0.95,
                y: 3.05,
                text: "Ample ($3.0T)",
                showarrow: false,
                font: { size: 10, color: "#22c55e" },
                bgcolor: "rgba(0,0,0,0.3)",
            },
            {
                xref: "paper",
                yref: "y",
                x: 0.95,
                y: 2.55,
                text: "Scarce ($2.5T)",
                showarrow: false,
                font: { size: 10, color: "#ef4444" },
                bgcolor: "rgba(0,0,0,0.3)",
            },
        ],
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

    // Net Repo Operations Latest Values
    $: latestNet = dashboardData.repo_operations?.net_repo?.slice(-1)[0] || 0;
    $: latestRepoSRF =
        dashboardData.repo_operations?.srf_usage?.slice(-1)[0] || 0;
    $: latestRepoRRP =
        dashboardData.repo_operations?.rrp_usage?.slice(-1)[0] || 0;

    // Repo rates for spread calculation
    $: latestSOFR = getLatestValue(dashboardData.repo_stress?.sofr);
    $: latestIORB = getLatestValue(dashboardData.repo_stress?.iorb);
    $: sofrIorbSpread = (latestSOFR - latestIORB) * 100; // bps

    // Composite Liquidity Risk Assessment
    $: liquidityRiskAssessment = (() => {
        let score = 0;
        let risks = [];

        if (latestReserves < 2.5) {
            score += 3;
            risks.push(
                translations.risk_reserves_critical ||
                    "Critical Reserves Scarce (<$2.5T)",
            );
        } else if (latestReserves < 2.8) {
            score += 1.5;
            risks.push(
                translations.risk_reserves_low ||
                    "Reserves approaching comfortable floor (<$2.8T)",
            );
        }

        if (sofrIorbSpread > 5) {
            score += 2;
            risks.push(
                translations.risk_sofr_stress ||
                    "Severe funding stress (SOFR >> IORB)",
            );
        } else if (sofrIorbSpread > 0) {
            score += 1;
            risks.push(
                translations.risk_sofr_decoupling ||
                    "Market rate decoupling from Fed floor",
            );
        }

        if (latestRepoSRF > 0) {
            score += 2;
            risks.push(
                `${translations.risk_srf_active || "Active SRF Usage"} ($${latestRepoSRF.toFixed(1)}B)`,
            );
        }

        let level = translations.risk_level_low || "LOW";
        let color = "#22c55e";
        let summary =
            translations.risk_summary_low ||
            "Adequate liquidity. System functioning correctly.";

        if (score >= 4) {
            level = translations.risk_level_critical || "CRITICAL";
            color = "#dc2626";
            summary =
                translations.risk_summary_critical ||
                "High risk of funding crunch. Immediate Fed intervention likely needed.";
        } else if (score >= 2) {
            level = translations.risk_level_moderate || "MODERATE";
            color = "#f59e0b";
            summary =
                translations.risk_summary_moderate ||
                "Evolving stress detected. Monitor rate decoupling and SRF usage.";
        } else if (score >= 1) {
            level = translations.risk_level_caution || "CAUTION";
            color = "rgba(245, 158, 11, 0.7)";
            summary =
                translations.risk_summary_caution ||
                "Liquidity buffer narrowing. Watch RRP depletion.";
        }

        return { score, level, color, summary, risks };
    })();

    // Determine regime
    $: regime =
        latestNet > 10
            ? "INJECTION"
            : latestNet < -100
              ? "HEAVY DRAIN"
              : latestNet < -10
                ? "DRAIN"
                : "NEUTRAL";

    $: regimeColor =
        regime === "INJECTION"
            ? "#22c55e"
            : regime === "HEAVY DRAIN"
              ? "#dc2626"
              : regime === "DRAIN"
                ? "#f59e0b"
                : "#6b7280";

    // Chart data for Net Repo
    $: netRepoChartDataRaw = [
        // Net Repo as area chart
        {
            x: dashboardData.dates,
            y: dashboardData.repo_operations?.net_repo,
            name: translations.net_repo_operations || "Net Repo Operations",
            type: "scatter",
            mode: "lines",
            fill: "tozeroy",
            line: { color: "#3b82f6", width: 2 },
            fillcolor: "rgba(59, 130, 246, 0.2)",
        },
        // Zero line reference
        {
            x: dashboardData.dates,
            y: dashboardData.dates?.map(() => 0),
            name: "Zero (Neutral)",
            type: "scatter",
            mode: "lines",
            line: { color: "#6b7280", width: 1, dash: "dash" },
            showlegend: false,
        },
        // SRF Usage (secondary, legendonly)
        {
            x: dashboardData.dates,
            y: dashboardData.repo_operations?.srf_usage,
            name: "SRF Usage (Injection)",
            type: "bar",
            marker: { color: "#22c55e", opacity: 0.6 },
            visible: "legendonly",
            yaxis: "y2",
        },
    ];

    $: netRepoChartData = filterPlotlyData(
        netRepoChartDataRaw,
        dashboardData.dates,
        netRepoRange,
    );

    $: netRepoLayout = {
        showlegend: true,
        legend: { orientation: "h", y: 1.1 },
        xaxis: { type: "date" },
        yaxis: {
            title: "Net Repo ($B)",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            zeroline: true,
            zerolinecolor: "#6b7280",
            zerolinewidth: 2,
        },
        yaxis2: {
            title: "SRF Usage ($B)",
            overlaying: "y",
            side: "right",
            showgrid: false,
        },
        margin: { t: 30, r: 60, b: 40, l: 60 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#fff" : "#000" },
        // Shade injection zone (above 0)
        shapes: [
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 100,
                fillcolor: "rgba(34, 197, 94, 0.05)",
                line: { width: 0 },
                layer: "below",
            },
        ],
        annotations: [
            {
                x: 0.02,
                y: 50,
                xref: "paper",
                yref: "y",
                text: "← Injection Zone",
                showarrow: false,
                font: { size: 10, color: "#22c55e" },
            },
            {
                x: 0.02,
                y: -200,
                xref: "paper",
                yref: "y",
                text: "← Drain Zone",
                showarrow: false,
                font: { size: 10, color: "#ef4444" },
            },
        ],
    };
</script>

<div class="main-charts">
    <!-- Net Liquidity Chart with Metrics Sidebar -->
    <div class="chart-card wide" bind:this={netLiqCard}>
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
                    <Chart
                        {darkMode}
                        data={netLiqData}
                        cardContainer={netLiqCard}
                        cardTitle="us_net_liquidity"
                    />
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
    <div class="chart-card wide" bind:this={reservesCard}>
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
                            {getLastDate("BANK_RESERVES")}</span
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
                        cardContainer={reservesCard}
                        cardTitle="bank_reserves"
                    />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.reserves_velocity_title ||
                            "Reserves Velocity"}
                    </h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table compact">
                            <thead>
                                <tr>
                                    <th
                                        >{translations.metric_header ||
                                            "Metric"}</th
                                    >
                                    <th
                                        >{translations.value_header ||
                                            "Value"}</th
                                    >
                                    <th
                                        >{translations.signal_header ||
                                            "Signal"}</th
                                    >
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
                                <!-- Added Liquidity Stress Signals -->
                                <tr
                                    style="border-top: 1px solid rgba(148, 163, 184, 0.1);"
                                >
                                    <td title="SOFR vs IORB Spread"
                                        >SOFR-IORB</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:negative={sofrIorbSpread > 0}
                                    >
                                        {sofrIorbSpread > 0
                                            ? "+"
                                            : ""}{sofrIorbSpread.toFixed(1)} bps
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:minus={sofrIorbSpread > 5}
                                        class:plus={sofrIorbSpread <= 0}
                                    >
                                        {sofrIorbSpread > 5
                                            ? "⚠️"
                                            : sofrIorbSpread > 0
                                              ? "🔶"
                                              : "✓"}
                                    </td>
                                </tr>
                                <tr>
                                    <td
                                        title={translations.net_repo_srf_usage ||
                                            "Standing Repo Facility Usage"}
                                        >{translations.srf_usage_label ||
                                            "SRF Usage"}</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:negative={latestRepoSRF > 0}
                                    >
                                        ${latestRepoSRF.toFixed(1)}B
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:minus={latestRepoSRF > 0}
                                    >
                                        {latestRepoSRF > 0 ? "⚠️" : "✓"}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- New Risk Assessment Panel -->
                    <div
                        class="risk-assessment-box"
                        style="margin-top: 16px; padding: 12px; border-radius: 8px; background: rgba(0,0,0,0.2); border-left: 4px solid {liquidityRiskAssessment.color};"
                    >
                        <div
                            style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;"
                        >
                            <span
                                style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase;"
                                >{translations.overall_risk_level ||
                                    "Overall Risk Level"}</span
                            >
                            <span
                                style="font-size: 12px; font-weight: 800; color: {liquidityRiskAssessment.color};"
                                >{liquidityRiskAssessment.level}</span
                            >
                        </div>
                        <p
                            style="font-size: 12px; color: #f8fafc; line-height: 1.4; margin: 0;"
                        >
                            {liquidityRiskAssessment.summary}
                        </p>
                        {#if liquidityRiskAssessment.risks.length > 0}
                            <div
                                style="margin-top: 8px; font-size: 10px; color: #94a3b8;"
                            >
                                <ul style="margin: 4px 0 0 16px; padding: 0;">
                                    {#each liquidityRiskAssessment.risks as risk}
                                        <li>{risk}</li>
                                    {/each}
                                </ul>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Fed Assets Chart -->
    <div class="chart-card" bind:this={fedAssetsCard}>
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
            <Chart
                {darkMode}
                data={fedData}
                cardContainer={fedAssetsCard}
                cardTitle="fed_assets"
            />
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
    <div class="chart-card" bind:this={rrpCard}>
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
            <Chart
                {darkMode}
                data={rrpData}
                cardContainer={rrpCard}
                cardTitle="fed_rrp"
            />
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
    <div class="chart-card" bind:this={tgaCard}>
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
            <Chart
                {darkMode}
                data={tgaData}
                cardContainer={tgaCard}
                cardTitle="treasury_tga"
            />
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

    <!-- Net Repo Operations Chart -->
    <div class="chart-card wide" bind:this={netRepoCard}>
        <div class="chart-header">
            <h3>
                {translations.chart_net_repo_ops || "Fed Net Repo Operations"}
                <span
                    class="current-value-badge"
                    style="margin-left: 12px; background: {latestNet > 0
                        ? 'rgba(34, 197, 94, 0.15)'
                        : 'rgba(239, 68, 68, 0.15)'}; color: {latestNet > 0
                        ? '#22c55e'
                        : '#ef4444'}; padding: 3px 8px; border-radius: 4px; font-size: 13px; font-weight: 600;"
                >
                    {latestNet > 0 ? "+" : ""}{latestNet.toFixed(1)}B
                </span>
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={netRepoRange}
                    onRangeChange={(r) => (netRepoRange = r)}
                />
                <span class="last-date"
                    >{translations.last_data || "Last Data:"}
                    {getLastDate("RRP")}</span
                >
            </div>
        </div>

        <!-- Key Metrics Panel -->
        <div
            class="net-repo-metrics"
            style="display: flex; gap: 15px; margin-bottom: 12px; flex-wrap: wrap; margin-top: 15px;"
        >
            <div
                class="metric-box"
                style="padding: 8px 12px; border-radius: 6px; background: {darkMode
                    ? 'rgba(255,255,255,0.05)'
                    : 'rgba(0,0,0,0.03)'}; border: 1px solid {darkMode
                    ? 'rgba(255,255,255,0.1)'
                    : 'rgba(0,0,0,0.05)'}; min-width: 120px;"
            >
                <span
                    style="font-size: 11px; opacity: 0.7; display: block; margin-bottom: 4px;"
                    >{translations.net_pos || "Net Position"}</span
                >
                <div
                    style="font-size: 18px; font-weight: 700; color: {latestNet >
                    0
                        ? '#22c55e'
                        : '#ef4444'};"
                >
                    {latestNet > 0 ? "+" : ""}{latestNet.toFixed(1)}B
                </div>
            </div>
            <div
                class="metric-box"
                style="padding: 8px 12px; border-radius: 6px; background: {darkMode
                    ? 'rgba(255,255,255,0.05)'
                    : 'rgba(0,0,0,0.03)'}; border: 1px solid {darkMode
                    ? 'rgba(255,255,255,0.1)'
                    : 'rgba(0,0,0,0.05)'}; min-width: 120px;"
            >
                <span
                    style="font-size: 11px; opacity: 0.7; display: block; margin-bottom: 4px;"
                    >{translations.regime_label || "Regime"}</span
                >
                <div
                    style="font-size: 14px; font-weight: 600; color: {regimeColor};"
                >
                    {regime}
                </div>
            </div>
            <div
                class="metric-box"
                style="padding: 8px 12px; border-radius: 6px; background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.2); min-width: 120px;"
            >
                <span
                    style="font-size: 11px; opacity: 0.7; display: block; margin-bottom: 4px;"
                    >{translations.srf_inject_label || "SRF (Inject)"}</span
                >
                <div style="font-size: 14px; font-weight: 600; color: #22c55e;">
                    +${latestRepoSRF.toFixed(1)}B
                </div>
            </div>
            <div
                class="metric-box"
                style="padding: 8px 12px; border-radius: 6px; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); min-width: 120px;"
            >
                <span
                    style="font-size: 11px; opacity: 0.7; display: block; margin-bottom: 4px;"
                    >{translations.rrp_drain_label || "RRP (Drain)"}</span
                >
                <div style="font-size: 14px; font-weight: 600; color: #ef4444;">
                    -${latestRepoRRP.toFixed(1)}B
                </div>
            </div>
        </div>

        <p class="chart-description" style="margin-top: 5px;">
            {translations.net_repo_desc ||
                "Net = SRF Usage (injection) - RRP Usage (drain). Positive = Fed adding liquidity. Negative = Fed removing liquidity."}
        </p>

        <div class="chart-content">
            <Chart
                {darkMode}
                data={netRepoChartData}
                layout={netRepoLayout}
                cardContainer={netRepoCard}
                cardTitle="fed_net_repo"
            />
        </div>
    </div>
</div>
