<script>
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";

    // Core props only
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges (no longer props)
    let cpiRange = "5Y";
    let pceRange = "5Y";
    let pmiRange = "5Y";
    let unemploymentRange = "5Y";
    let fedFundsRange = "5Y";
    let nfpRange = "5Y";
    let joltsRange = "5Y";
    let inflationExpectationsRange = "5Y";

    // --- Internal Chart Data Processing ---

    // CPI Chart
    $: cpiData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.cpi_yoy || [],
                name: translations.headline_cpi || "CPI YoY",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.core_cpi_yoy || [],
                name: translations.core_cpi || "Core CPI YoY",
                type: "scatter",
                mode: "lines",
                line: { color: "#f97316", width: 2, dash: "dash" },
            },
        ],
        dashboardData.dates,
        cpiRange,
    );

    // PCE Chart
    $: pceData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.pce_yoy || [],
                name: translations.headline_pce || "PCE YoY",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.core_pce_yoy || [],
                name: translations.core_pce || "Core PCE YoY",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 2, dash: "dash" },
            },
        ],
        dashboardData.dates,
        pceRange,
    );

    // PMI Chart
    $: pmiData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.ism_mfg || [],
                name: translations.manufacturing || "ISM Manufacturing",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.ism_svc || [],
                name: translations.services || "ISM Services",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2, dash: "dash" },
            },
        ],
        dashboardData.dates,
        pmiRange,
    );

    // Unemployment Chart
    $: unemploymentData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.unemployment || [],
                name: translations.nav_unemployment || "Unemployment Rate",
                type: "scatter",
                mode: "lines",
                line: { color: "#6b7280", width: 2 },
                fill: "tozeroy",
                fillcolor: "rgba(107, 114, 128, 0.1)",
            },
        ],
        dashboardData.dates,
        unemploymentRange,
    );

    // Fed Funds Rate Chart
    $: fedFundsData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.fed_funds_rate || [],
                name: translations.fed_funds_rate || "Fed Funds Rate",
                type: "scatter",
                mode: "lines",
                line: { color: "#1e40af", width: 3 },
                fill: "tozeroy",
                fillcolor: "rgba(30, 64, 175, 0.1)",
            },
        ],
        dashboardData.dates,
        fedFundsRange,
    );

    // NFP Charts (Raw, Z-Score, Percentile)
    $: nfpData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.nfp_change || [],
                name: "NFP Change (Raw)",
                type: "bar",
                marker: {
                    color: (dashboardData.fed_forecasts?.nfp_change || []).map(
                        (v) => {
                            if (v === null || v === undefined)
                                return "rgba(0,0,0,0)";
                            return v >= 0 ? "#10b981" : "#ef4444";
                        },
                    ),
                },
            },
        ],
        dashboardData.dates,
        nfpRange,
    );

    $: nfpZData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfp?.zscore || [],
                name: "NFP Change (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        nfpRange,
    );

    $: nfpPctData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfp?.percentile || [],
                name: "NFP Change (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        nfpRange,
    );

    // JOLTS Charts (Raw, Z-Score, Percentile)
    $: joltsData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.jolts || [],
                name: "JOLTS (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
            },
        ],
        dashboardData.dates,
        joltsRange,
    );

    $: joltsZData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.jolts?.zscore || [],
                name: "JOLTS (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
            },
        ],
        dashboardData.dates,
        joltsRange,
    );

    $: joltsPctData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.jolts?.percentile || [],
                name: "JOLTS (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
            },
        ],
        dashboardData.dates,
        joltsRange,
    );

    // Inflation Expectations Chart
    $: inflationExpectationsData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.inflation_expect_5y || [],
                name: "5Y TIPS Breakeven",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.inflation_expect_10y || [],
                name: "10Y TIPS Breakeven",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2, dash: "dash" },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.cpi_yoy || [],
                name: "CPI YoY (Actual)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 1.5, dash: "dot" },
            },
        ],
        dashboardData.dates,
        inflationExpectationsRange,
    );

    // FOMC Meeting Dates - dynamically loaded from data pipeline or fallback to static
    // The pipeline scrapes dates from federalreserve.gov/monetarypolicy/fomccalendars.htm
    $: FOMC_DATES = (dashboardData.fed_forecasts?.fomc_dates || []).map(
        (m) => ({
            date: new Date(m.date),
            label: m.label,
            hasSEP: m.hasSEP || false,
            probs: m.probs || null,
        }),
    );

    // Fallback dates if dynamic fetch fails
    const FALLBACK_FOMC_DATES = [
        {
            date: new Date(Date.UTC(2025, 0, 29)),
            label: "Jan 28-29",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 2, 19)),
            label: "Mar 18-19",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 4, 7)),
            label: "May 6-7",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 5, 18)),
            label: "Jun 17-18",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 6, 30)),
            label: "Jul 29-30",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 8, 17)),
            label: "Sep 16-17",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 9, 29)),
            label: "Oct 28-29",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 11, 10)),
            label: "Dec 9-10",
            hasSEP: true,
        },
    ];

    // Use dynamic dates if available, fallback otherwise
    $: fomcDates = FOMC_DATES.length > 0 ? FOMC_DATES : FALLBACK_FOMC_DATES;

    // Fed Rate Probabilities Chart logic
    let selectedMeetingIndex = 0;

    // Treasury Settlements pagination, view toggle, and filters
    let settlementPage = 0;
    const settlementsPerPage = 10;
    let groupedView = false; // Default to individual view

    // Filters
    let filterSecurityType = "all"; // all, Bill, Note, Bond, TIPS, FRN, CMB
    let filterTermMin = ""; // Term filter min (e.g., 4 for 4-Week)
    let filterTermMax = ""; // Term filter max (e.g., 52 for 52-Week)
    let filterAmountMin = "";
    let filterAmountMax = "";

    // View Modes
    let nfpViewMode = "raw"; // raw, zscore, percentile
    let joltsViewMode = "raw";

    // Helper to extract term weeks/years from type string (e.g., "17-Week Bill" -> 17, "10-Year Note" -> 520)
    function extractTermWeeks(typeStr) {
        if (!typeStr) return null;
        const weekMatch = typeStr.match(/(\d+)-Week/i);
        if (weekMatch) return parseInt(weekMatch[1]);
        const monthMatch = typeStr.match(/(\d+)-Month/i);
        if (monthMatch) return parseInt(monthMatch[1]) * 4; // Convert months to weeks
        const yearMatch = typeStr.match(/(\d+)-Year/i);
        if (yearMatch) return parseInt(yearMatch[1]) * 52; // Convert years to weeks
        const dayMatch = typeStr.match(/(\d+)-Day/i);
        if (dayMatch) return Math.ceil(parseInt(dayMatch[1]) / 7); // Convert days to weeks
        return null;
    }

    // Treasury settlements are at root level, not inside fed_forecasts
    $: settlementData = dashboardData.treasury_settlements || {};
    $: currentRrp = settlementData.current_rrp || 0;
    $: rawSettlements = groupedView
        ? settlementData.grouped || []
        : settlementData.individual || [];

    // Apply filters
    $: filteredSettlements = rawSettlements.filter((s) => {
        // Security type filter
        const typeStr = s.type || s.types || "";
        if (
            filterSecurityType !== "all" &&
            !typeStr.toLowerCase().includes(filterSecurityType.toLowerCase())
        ) {
            return false;
        }
        // Term min filter (in weeks)
        if (filterTermMin) {
            const termWeeks = extractTermWeeks(typeStr);
            if (termWeeks === null || termWeeks < parseInt(filterTermMin)) {
                return false;
            }
        }
        // Term max filter (in weeks)
        if (filterTermMax) {
            const termWeeks = extractTermWeeks(typeStr);
            if (termWeeks === null || termWeeks > parseInt(filterTermMax)) {
                return false;
            }
        }
        // Amount min filter
        if (filterAmountMin && s.amount < parseFloat(filterAmountMin)) {
            return false;
        }
        // Amount max filter
        if (filterAmountMax && s.amount > parseFloat(filterAmountMax)) {
            return false;
        }
        return true;
    });

    $: allSettlements = filteredSettlements;
    $: totalSettlementPages = Math.ceil(
        allSettlements.length / settlementsPerPage,
    );
    $: paginatedSettlements = allSettlements.slice(
        settlementPage * settlementsPerPage,
        (settlementPage + 1) * settlementsPerPage,
    );

    // Reset pagination when filters change
    function resetPagination() {
        settlementPage = 0;
    }

    $: selectedMeeting = fomcDates[selectedMeetingIndex] || fomcDates[0];

    $: probChartData =
        selectedMeeting && selectedMeeting.probs
            ? [
                  {
                      x: [
                          translations.prob_cut || "Cut",
                          translations.no_change || "Hold",
                          translations.prob_hike || "Hike",
                      ],
                      y: [
                          selectedMeeting.probs.cut,
                          selectedMeeting.probs.hold,
                          selectedMeeting.probs.hike,
                      ],
                      type: "bar",
                      marker: {
                          color: ["#10b981", "#f59e0b", "#ef4444"],
                      },
                      text: [
                          `${selectedMeeting.probs.cut}%`,
                          `${selectedMeeting.probs.hold}%`,
                          `${selectedMeeting.probs.hike}%`,
                      ],
                      textposition: "auto",
                      hoverinfo: "none",
                  },
              ]
            : [];

    $: probChartLayout = {
        title: {
            text: selectedMeeting
                ? `${selectedMeeting.label} (${selectedMeeting.date.getFullYear()})`
                : "",
            font: { size: 13, color: darkMode ? "#e5e7eb" : "#374151" },
        },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: darkMode ? "#e5e7eb" : "#374151" },
        showlegend: false,
        margin: { t: 40, b: 40, l: 40, r: 20 },
        height: 300,
        xaxis: { gridcolor: darkMode ? "#374151" : "#e5e7eb" },
        yaxis: {
            gridcolor: darkMode ? "#374151" : "#e5e7eb",
            range: [0, 105],
            title: "% Probability",
        },
    };

    // Dot Plot data - dynamically loaded from pipeline or fallback
    // Source: palewire/fed-dot-plot-scraper (scraped from Fed website)
    const FALLBACK_DOT_PLOT = {
        year: 2024,
        meeting: "December 2024",
        projections: {
            2024: [
                4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375,
                4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375,
                4.375,
            ],
            2025: [
                3.625, 3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125,
                4.125, 4.125, 4.125, 4.375, 4.375, 4.375, 4.375, 4.375, 4.625,
                4.625,
            ],
            2026: [
                2.875, 3.125, 3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625,
                3.625, 3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125,
                4.125,
            ],
            2027: [
                2.625, 2.875, 2.875, 2.875, 2.875, 3.125, 3.125, 3.125, 3.125,
                3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625, 3.625, 3.875,
                3.875,
            ],
            longerRun: [
                2.625, 2.625, 2.875, 2.875, 2.875, 2.875, 2.875, 3.0, 3.0, 3.0,
                3.0, 3.0, 3.0, 3.0, 3.125, 3.125, 3.25, 3.25, 3.5,
            ],
        },
        currentRate: 4.375,
    };

    // Use dynamic Dot Plot if available from data pipeline
    $: DOT_PLOT_DATA =
        dashboardData.fed_forecasts?.dot_plot || FALLBACK_DOT_PLOT;

    // Calculate next FOMC meeting
    $: nextFOMC = (() => {
        const now = new Date();
        return fomcDates.find((m) => m.date > now) || fomcDates[0];
    })();

    // Countdown calculation (using UTC to avoid timezone issues)
    $: countdown = (() => {
        if (!nextFOMC) return { days: 0, hours: 0, mins: 0 };
        const now = new Date();
        const diff = nextFOMC.date.getTime() - now.getTime();
        // Ensure positive values
        const absDiff = Math.abs(diff);
        const days = Math.floor(absDiff / (1000 * 60 * 60 * 24));
        const hours = Math.floor(
            (absDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
        );
        const mins = Math.floor((absDiff % (1000 * 60 * 60)) / (1000 * 60));
        return { days, hours, mins };
    })();

    // Dot plot aggregation for visualization (Filtering out 'longerRun' as requested)
    $: dotPlotAggregated = Object.entries(DOT_PLOT_DATA.projections)
        .filter(([key]) => key !== "longerRun")
        .map(([year, dots]) => {
            const counts = {};
            dots.forEach((d) => {
                counts[d] = (counts[d] || 0) + 1;
            });
            const median = dots.sort((a, b) => a - b)[
                Math.floor(dots.length / 2)
            ];
            return {
                year,
                counts,
                median,
                min: Math.min(...dots),
                max: Math.max(...dots),
            };
        });

    // Chart layouts
    $: cpiLayout = {
        yaxis: { title: "YoY %", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
        shapes: [
            {
                type: "line",
                y0: 2,
                y1: 2,
                x0: 0,
                x1: 1,
                xref: "paper",
                line: { color: "#10b981", width: 2, dash: "dash" },
                layer: "below",
            },
        ],
        annotations: [
            {
                y: 2,
                xref: "paper",
                yref: "y",
                text: `${translations.fed_target_label || "Fed Target"}: 2%`,
                showarrow: false,
                font: { size: 10, color: "#10b981" },
            },
        ],
    };

    $: pmiLayout = {
        yaxis: { title: "PMI Index", range: [35, 70], dtick: 5 },
        margin: { l: 50, r: 20, t: 20, b: 40 },
        shapes: [
            {
                type: "line",
                y0: 50,
                y1: 50,
                x0: 0,
                x1: 1,
                xref: "paper",
                line: { color: "#f59e0b", width: 2, dash: "dash" },
                layer: "below",
            },
        ],
        annotations: [
            {
                x: 1.02,
                y: 50,
                xref: "paper",
                yref: "y",
                text:
                    translations.expansion_contraction ||
                    "Expansion/Contraction",
                showarrow: false,
                font: { size: 9, color: "#f59e0b" },
            },
        ],
    };

    $: unemploymentLayout = {
        yaxis: { title: "Rate (%)", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    $: fedFundsLayout = {
        yaxis: { title: "Rate (%)", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    // Get latest values helper
    function getLatest(arr) {
        if (!arr || arr.length === 0) return null;
        for (let i = arr.length - 1; i >= 0; i--) {
            if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i]))
                return arr[i];
        }
        return null;
    }

    // Get value N periods ago (for ROC calculation)
    function getValueAgo(arr, periods = 22) {
        if (!arr || arr.length < periods + 1) return null;
        let count = 0;
        for (let i = arr.length - 1; i >= 0; i--) {
            if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i])) {
                if (count === periods) return arr[i];
                count++;
            }
        }
        return null;
    }

    // Calculate ROC (change from N periods ago)
    function calcRoc(arr, periods = 22) {
        const latest = getLatest(arr);
        const previous = getValueAgo(arr, periods);
        if (latest === null || previous === null) return null;
        return latest - previous;
    }

    // Latest values
    $: latestCPI = getLatest(dashboardData.fed_forecasts?.cpi_yoy);
    $: latestCoreCPI = getLatest(dashboardData.fed_forecasts?.core_cpi_yoy);
    $: latestPCE = getLatest(dashboardData.fed_forecasts?.pce_yoy);
    $: latestCorePCE = getLatest(dashboardData.fed_forecasts?.core_pce_yoy);
    $: latestISMMfg = getLatest(dashboardData.fed_forecasts?.ism_mfg);
    $: latestISMSvc = getLatest(dashboardData.fed_forecasts?.ism_svc);
    $: latestUnemployment = getLatest(
        dashboardData.fed_forecasts?.unemployment,
    );
    $: latestFedFunds = getLatest(dashboardData.fed_forecasts?.fed_funds_rate);
    $: latestInflationExpect5Y = getLatest(
        dashboardData.fed_forecasts?.inflation_expect_5y,
    );
    $: latestInflationExpect10Y = getLatest(
        dashboardData.fed_forecasts?.inflation_expect_10y,
    );

    // ROC calculations (1 month = ~22 trading days for monthly data, use 1 for monthly)
    $: rocFedFunds = calcRoc(dashboardData.fed_forecasts?.fed_funds_rate, 1);
    $: rocCorePCE = calcRoc(dashboardData.fed_forecasts?.core_pce_yoy, 1);
    $: rocUnemployment = calcRoc(dashboardData.fed_forecasts?.unemployment, 1);
    $: rocISMMfg = calcRoc(dashboardData.fed_forecasts?.ism_mfg, 1);
</script>

<div class="fed-forecasts-tab">
    <!-- Key Metrics Cards -->
    <div class="metrics-section">
        <div class="metrics-row">
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label"
                        >{translations.fed_funds_rate || "Fed Funds Rate"}</span
                    >
                    {#if rocFedFunds !== null}
                        <span
                            class="roc-badge"
                            class:positive={rocFedFunds > 0}
                            class:negative={rocFedFunds < 0}
                            class:neutral={rocFedFunds === 0}
                        >
                            {rocFedFunds > 0
                                ? "▲"
                                : rocFedFunds < 0
                                  ? "▼"
                                  : "●"}
                            {Math.abs(rocFedFunds).toFixed(2)}% (1M)
                        </span>
                    {/if}
                </div>
                <span class="metric-value"
                    >{latestFedFunds?.toFixed(2) ?? "—"}%</span
                >
                <div class="metric-bar">
                    <div
                        class="bar-fill bar-neutral"
                        style="width: {Math.min(
                            ((latestFedFunds ?? 0) / 6) * 100,
                            100,
                        )}%"
                    ></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label"
                        >{translations.core_pce_yoy || "Core PCE YoY"}</span
                    >
                    {#if rocCorePCE !== null}
                        <span
                            class="roc-badge"
                            class:positive={rocCorePCE < 0}
                            class:negative={rocCorePCE > 0}
                            class:neutral={rocCorePCE === 0}
                        >
                            {rocCorePCE > 0 ? "▲" : rocCorePCE < 0 ? "▼" : "●"}
                            {Math.abs(rocCorePCE).toFixed(2)}% (1M)
                        </span>
                    {/if}
                </div>
                <span
                    class="metric-value"
                    class:above-target={latestCorePCE > 2}
                    >{latestCorePCE?.toFixed(2) ?? "—"}%</span
                >
                <div class="metric-bar">
                    <div
                        class="bar-fill"
                        class:bar-bullish={latestCorePCE <= 2.5}
                        class:bar-bearish={latestCorePCE > 2.5}
                        style="width: {Math.min(
                            ((latestCorePCE ?? 0) / 5) * 100,
                            100,
                        )}%"
                    ></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label"
                        >{translations.unemployment_rate ||
                            "Unemployment"}</span
                    >
                    {#if rocUnemployment !== null}
                        <span
                            class="roc-badge"
                            class:positive={rocUnemployment < 0}
                            class:negative={rocUnemployment > 0}
                            class:neutral={rocUnemployment === 0}
                        >
                            {rocUnemployment > 0
                                ? "▲"
                                : rocUnemployment < 0
                                  ? "▼"
                                  : "●"}
                            {Math.abs(rocUnemployment).toFixed(1)}% (1M)
                        </span>
                    {/if}
                </div>
                <span class="metric-value"
                    >{latestUnemployment?.toFixed(1) ?? "—"}%</span
                >
                <div class="metric-bar">
                    <div
                        class="bar-fill"
                        class:bar-bullish={latestUnemployment <= 4.5}
                        class:bar-neutral={latestUnemployment > 4.5 &&
                            latestUnemployment <= 5.5}
                        class:bar-bearish={latestUnemployment > 5.5}
                        style="width: {Math.min(
                            ((latestUnemployment ?? 0) / 10) * 100,
                            100,
                        )}%"
                    ></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-header">
                    <span class="metric-label"
                        >{translations.ism_mfg_pmi || "ISM Mfg PMI"}</span
                    >
                    {#if rocISMMfg !== null}
                        <span
                            class="roc-badge"
                            class:positive={rocISMMfg > 0}
                            class:negative={rocISMMfg < 0}
                            class:neutral={rocISMMfg === 0}
                        >
                            {rocISMMfg > 0 ? "▲" : rocISMMfg < 0 ? "▼" : "●"}
                            {Math.abs(rocISMMfg).toFixed(1)} (1M)
                        </span>
                    {/if}
                </div>
                <span class="metric-value" class:below-50={latestISMMfg < 50}
                    >{latestISMMfg?.toFixed(1) ?? "—"}</span
                >
                <div class="metric-bar">
                    <div
                        class="bar-fill"
                        class:bar-bullish={latestISMMfg >= 50}
                        class:bar-bearish={latestISMMfg < 50}
                        style="width: {Math.min(
                            ((latestISMMfg ?? 0) / 70) * 100,
                            100,
                        )}%"
                    ></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Dot Plot Section + FOMC Calendar -->
    <div class="dot-plot-section">
        <div class="left-stats-column">
            <!-- Dot Plot Card -->
            <div class="chart-card dot-plot-card">
                <div class="chart-header">
                    <h3>
                        🎯 {translations.fed_dot_plot || "Fed Dot Plot"} ({DOT_PLOT_DATA.meeting})
                    </h3>
                </div>
                <p class="chart-description">
                    {translations.fomc_projections_description ||
                        "FOMC participants' projections for the federal funds rate. Each dot represents one official's view."}
                </p>
                <div class="dot-plot-container">
                    <div class="dot-plot-grid">
                        {#each dotPlotAggregated as yearData}
                            <div class="dot-plot-column">
                                <div class="dot-plot-year">
                                    {yearData.year === "longerRun"
                                        ? translations.long_run || "Long Run"
                                        : yearData.year}
                                </div>
                                <div class="dot-plot-dots">
                                    {#each Object.entries(yearData.counts).sort((a, b) => Number(b[0]) - Number(a[0])) as [rate, count]}
                                        <div class="dot-row">
                                            <span class="dot-rate">{rate}%</span
                                            >
                                            <div class="dots">
                                                {#each Array(count) as _}
                                                    <span
                                                        class="dot"
                                                        class:median={Number(
                                                            rate,
                                                        ) === yearData.median}
                                                    ></span>
                                                {/each}
                                            </div>
                                        </div>
                                    {/each}
                                </div>
                                <div class="dot-plot-median">
                                    {translations.median || "Median"}: {yearData.median}%
                                </div>
                            </div>
                        {/each}
                    </div>
                    <div class="dot-plot-legend">
                        <span class="legend-item"
                            ><span class="dot"></span>
                            {translations.individual_projection ||
                                "Individual Projection"}</span
                        >
                        <span class="legend-item"
                            ><span class="dot median"></span>
                            {translations.median || "Median"}</span
                        >
                        <span class="legend-item current-rate"
                            >{translations.current_rate || "Current Rate"}: {DOT_PLOT_DATA.currentRate}%</span
                        >
                    </div>
                </div>
            </div>

            {#if probChartData.length > 0}
                <div class="chart-card prob-chart-card">
                    <div class="chart-header">
                        <h3>
                            📊 {translations.target_rate ||
                                "Target Rate Probabilities"}
                        </h3>
                    </div>
                    <div class="chart-content">
                        <Chart
                            {darkMode}
                            data={probChartData}
                            layout={probChartLayout}
                        />
                    </div>
                    {#if selectedMeeting && selectedMeeting.probs}
                        <div class="prob-footer">
                            <span class="implied-info">
                                {translations.implied_rate || "Implied Rate"}:
                                <b>{selectedMeeting.probs.implied_rate}%</b>
                            </span>
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- FOMC Calendar Card -->
        <div class="chart-card fomc-calendar-card">
            <div class="chart-header">
                <h3>
                    📅 {translations.upcoming_fomc_meetings ||
                        "Upcoming FOMC Meetings"}
                </h3>
            </div>
            <div class="fomc-meetings-list">
                {#each fomcDates.slice(0, 8) as meeting, i}
                    <div
                        class="fomc-meeting-item"
                        class:next-meeting={i === 0}
                        class:selected={selectedMeetingIndex === i}
                        on:click={() => (selectedMeetingIndex = i)}
                        on:keydown={(e) =>
                            e.key === "Enter" && (selectedMeetingIndex = i)}
                        role="button"
                        tabindex="0"
                    >
                        <div class="meeting-date-badge">
                            <span class="meeting-month"
                                >{meeting.label.split(" ")[0]}</span
                            >
                            <span class="meeting-days"
                                >{meeting.label.split(" ")[1]}</span
                            >
                        </div>
                        <div class="meeting-info">
                            <span class="meeting-year"
                                >{meeting.date.getFullYear()}</span
                            >
                            {#if meeting.probs}
                                <div class="market-target">
                                    <span class="target-label"
                                        >{translations.target ||
                                            "Target"}:</span
                                    >
                                    <span class="target-value"
                                        >{meeting.probs.implied_rate}%</span
                                    >
                                </div>
                            {/if}
                            {#if meeting.hasSEP}
                                <span class="sep-badge">SEP</span>
                            {/if}
                        </div>

                        {#if meeting.probs}
                            <div class="meeting-probs">
                                <div class="prob-row">
                                    <div class="prob-label-group">
                                        <span class="prob-label"
                                            >{translations.prob_cut ||
                                                "Cut"}</span
                                        >
                                        <div class="roc-container">
                                            {#if meeting.probs.roc1d}
                                                <span
                                                    class="roc-value"
                                                    title="1-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc1d.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc1d.cut < 0}
                                                >
                                                    1D: {meeting.probs.roc1d
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1d.cut}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc5d}
                                                <span
                                                    class="roc-value"
                                                    title="5-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc5d.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc5d.cut < 0}
                                                >
                                                    5D: {meeting.probs.roc5d
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc5d.cut}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc1m}
                                                <span
                                                    class="roc-value"
                                                    title="1-Month Trend"
                                                    class:up={meeting.probs
                                                        .roc1m.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc1m.cut < 0}
                                                >
                                                    1M: {meeting.probs.roc1m
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1m.cut}%
                                                </span>
                                            {/if}
                                        </div>
                                    </div>
                                    <span
                                        class="prob-value"
                                        class:high={meeting.probs.cut > 60}
                                        class:med={meeting.probs.cut > 30 &&
                                            meeting.probs.cut <= 60}
                                        class:low={meeting.probs.cut <= 30}
                                    >
                                        {meeting.probs.cut}%
                                    </span>
                                </div>
                                <div class="prob-row">
                                    <div class="prob-label-group">
                                        <span class="prob-label"
                                            >{translations.prob_hold ||
                                                "Hold"}</span
                                        >
                                        <div class="roc-container">
                                            {#if meeting.probs.roc1d}
                                                <span
                                                    class="roc-value"
                                                    title="1-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc1d.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc1d.hold < 0}
                                                >
                                                    1D: {meeting.probs.roc1d
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1d.hold}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc5d}
                                                <span
                                                    class="roc-value"
                                                    title="5-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc5d.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc5d.hold < 0}
                                                >
                                                    5D: {meeting.probs.roc5d
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc5d.hold}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc1m}
                                                <span
                                                    class="roc-value"
                                                    title="1-Month Trend"
                                                    class:up={meeting.probs
                                                        .roc1m.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc1m.hold < 0}
                                                >
                                                    1M: {meeting.probs.roc1m
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1m.hold}%
                                                </span>
                                            {/if}
                                        </div>
                                    </div>
                                    <span
                                        class="prob-value"
                                        class:high={meeting.probs.hold > 60}
                                        class:med={meeting.probs.hold > 30 &&
                                            meeting.probs.hold <= 60}
                                        class:low={meeting.probs.hold <= 30}
                                    >
                                        {meeting.probs.hold}%
                                    </span>
                                </div>
                                {#if meeting.probs.hike > 0}
                                    <div class="prob-row">
                                        <div class="prob-label-group">
                                            <span class="prob-label"
                                                >{translations.prob_hike ||
                                                    "Hike"}</span
                                            >
                                            <div class="roc-container">
                                                {#if meeting.probs.roc1d}
                                                    <span
                                                        class="roc-value"
                                                        title="1-Day Trend"
                                                        class:up={meeting.probs
                                                            .roc1d.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc1d.hike <
                                                            0}
                                                    >
                                                        1D: {meeting.probs.roc1d
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc1d.hike}%
                                                    </span>
                                                {/if}
                                                {#if meeting.probs.roc5d}
                                                    <span
                                                        class="roc-value"
                                                        title="5-Day Trend"
                                                        class:up={meeting.probs
                                                            .roc5d.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc5d.hike <
                                                            0}
                                                    >
                                                        5D: {meeting.probs.roc5d
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc5d.hike}%
                                                    </span>
                                                {/if}
                                                {#if meeting.probs.roc1m}
                                                    <span
                                                        class="roc-value"
                                                        title="1-Month Trend"
                                                        class:up={meeting.probs
                                                            .roc1m.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc1m.hike <
                                                            0}
                                                    >
                                                        1M: {meeting.probs.roc1m
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc1m.hike}%
                                                    </span>
                                                {/if}
                                            </div>
                                        </div>
                                        <span
                                            class="prob-value"
                                            class:high={meeting.probs.hike > 60}
                                            class:med={meeting.probs.hike >
                                                30 && meeting.probs.hike <= 60}
                                            class:low={meeting.probs.hike <= 30}
                                        >
                                            {meeting.probs.hike}%
                                        </span>
                                    </div>
                                {/if}
                                {#if meeting.probs.cumulative_cuts > 0}
                                    <div class="cumulative-info">
                                        Σ {meeting.probs.cumulative_cuts}
                                        {translations.cumulative_cuts || "Cuts"}
                                    </div>
                                {/if}
                            </div>
                        {/if}

                        {#if i === 0}
                            <div class="next-badge">
                                {translations.next || "NEXT"}
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
            <div class="fomc-legend">
                <span class="legend-note">
                    <span class="sep-badge-small">SEP</span> = {translations.summary_of_projections ||
                        "Summary of Economic Projections"}
                </span>
            </div>
        </div>
    </div>

    <!-- Treasury Settlements with RRP Liquidity Coverage -->
    {#if allSettlements.length > 0 || settlementData.individual?.length > 0}
        <div class="chart-card treasury-settlements-card">
            <div class="chart-header">
                <h3>
                    🏛️ {translations.treasury_settlements ||
                        "Treasury Settlements"}
                </h3>
                <div class="header-controls-right">
                    <label class="view-toggle">
                        <input
                            type="checkbox"
                            bind:checked={groupedView}
                            on:change={resetPagination}
                        />
                        <span class="toggle-label"
                            >{groupedView
                                ? translations.view_grouped || "Grouped"
                                : translations.view_individual ||
                                  "Individual"}</span
                        >
                    </label>
                    <span class="rrp-indicator">
                        RRP: <b>${currentRrp.toFixed(1)}B</b>
                    </span>
                </div>
            </div>

            <!-- Filters Row -->
            <div class="settlements-filters">
                <div class="filter-group">
                    <label for="filter-security-type"
                        >{translations.type || "Type"}:</label
                    >
                    <select
                        id="filter-security-type"
                        bind:value={filterSecurityType}
                        on:change={resetPagination}
                    >
                        <option value="all">{translations.all || "All"}</option>
                        <option value="Bill">Bills</option>
                        <option value="Note">Notes</option>
                        <option value="Bond">Bonds</option>
                        <option value="TIPS">TIPS</option>
                        <option value="FRN">FRN</option>
                        <option value="CMB">CMB</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-term-min"
                        >{translations.term_min || "Term Min"}:</label
                    >
                    <select
                        id="filter-term-min"
                        bind:value={filterTermMin}
                        on:change={resetPagination}
                    >
                        <option value="">{translations.any || "Any"}</option>
                        <option value="4">4-Week</option>
                        <option value="8">8-Week</option>
                        <option value="13">13-Week</option>
                        <option value="17">17-Week</option>
                        <option value="26">26-Week</option>
                        <option value="52">52-Week</option>
                        <option value="104">2-Year</option>
                        <option value="156">3-Year</option>
                        <option value="260">5-Year</option>
                        <option value="364">7-Year</option>
                        <option value="520">10-Year</option>
                        <option value="1040">20-Year</option>
                        <option value="1560">30-Year</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-term-max"
                        >{translations.term_max || "Term Max"}:</label
                    >
                    <select
                        id="filter-term-max"
                        bind:value={filterTermMax}
                        on:change={resetPagination}
                    >
                        <option value="">{translations.any || "Any"}</option>
                        <option value="4">4-Week</option>
                        <option value="8">8-Week</option>
                        <option value="13">13-Week</option>
                        <option value="17">17-Week</option>
                        <option value="26">26-Week</option>
                        <option value="52">52-Week</option>
                        <option value="104">2-Year</option>
                        <option value="156">3-Year</option>
                        <option value="260">5-Year</option>
                        <option value="364">7-Year</option>
                        <option value="520">10-Year</option>
                        <option value="1040">20-Year</option>
                        <option value="1560">30-Year</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="filter-amount-min"
                        >{translations.min_amount || "Min $B"}:</label
                    >
                    <input
                        id="filter-amount-min"
                        type="number"
                        placeholder="0"
                        bind:value={filterAmountMin}
                        on:input={resetPagination}
                        min="0"
                        step="10"
                    />
                </div>
                <div class="filter-group">
                    <label for="filter-amount-max"
                        >{translations.max_amount || "Max $B"}:</label
                    >
                    <input
                        id="filter-amount-max"
                        type="number"
                        placeholder="∞"
                        bind:value={filterAmountMax}
                        on:input={resetPagination}
                        min="0"
                        step="10"
                    />
                </div>
                <button
                    class="clear-filters-btn"
                    on:click={() => {
                        filterSecurityType = "all";
                        filterTermMin = "";
                        filterTermMax = "";
                        filterAmountMin = "";
                        filterAmountMax = "";
                        resetPagination();
                    }}>{translations.clear || "Clear"}</button
                >
            </div>

            <div class="settlements-table-container">
                <table class="settlements-table">
                    <thead>
                        <tr>
                            <th>{translations.date || "Date"}</th>
                            <th>{translations.status || "Status"}</th>
                            <th>{translations.type || "Type"}</th>
                            <th>{translations.amount || "Amount"}</th>
                            <th>{translations.rrp_balance || "RRP Balance"}</th>
                            <th>{translations.rrp_coverage || "Coverage"}</th>
                            <th>{translations.risk || "Risk"}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each paginatedSettlements as settlement}
                            <tr
                                class="settlement-row"
                                class:high-risk={settlement.risk_level ===
                                    "high"}
                                class:medium-risk={settlement.risk_level ===
                                    "medium"}
                                class:future-row={settlement.is_future}
                            >
                                <td class="settlement-date"
                                    >{settlement.date}</td
                                >
                                <td class="settlement-status">
                                    {#if settlement.is_future}
                                        <span class="status-badge future"
                                            >📅 {translations.upcoming ||
                                                "Upcoming"}</span
                                        >
                                    {:else}
                                        <span class="status-badge past"
                                            >✓ {translations.settled ||
                                                "Settled"}</span
                                        >
                                    {/if}
                                </td>
                                <td class="settlement-type"
                                    >{settlement.type || settlement.types}</td
                                >
                                <td class="settlement-amount"
                                    >${settlement.amount}B</td
                                >
                                <td class="settlement-rrp"
                                    >${settlement.rrp_balance}B</td
                                >
                                <td class="settlement-coverage"
                                    >{settlement.coverage_ratio}x</td
                                >
                                <td class="settlement-risk">
                                    {#if settlement.risk_level === "low"}
                                        <span class="risk-badge low">🟢</span>
                                    {:else if settlement.risk_level === "medium"}
                                        <span class="risk-badge medium">🟡</span
                                        >
                                    {:else}
                                        <span class="risk-badge high">🔴</span>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
            <!-- Pagination Controls -->
            {#if totalSettlementPages > 1}
                <div class="pagination-controls">
                    <button
                        class="pagination-btn"
                        disabled={settlementPage === 0}
                        on:click={() => settlementPage--}
                    >
                        ← {translations.prev || "Prev"}
                    </button>
                    <span class="pagination-info">
                        {translations.page || "Page"}
                        {settlementPage + 1}
                        {translations.of || "of"}
                        {totalSettlementPages}
                    </span>
                    <button
                        class="pagination-btn"
                        disabled={settlementPage >= totalSettlementPages - 1}
                        on:click={() => settlementPage++}
                    >
                        {translations.next || "Next"} →
                    </button>
                </div>
            {/if}
            <div class="settlements-legend">
                <span
                    >🟢 {translations.rrp_coverage_safe ||
                        "RRP ≥ 3x Settlement (Safe)"}</span
                >
                <span
                    >🟡 {translations.rrp_coverage_caution ||
                        "RRP 1.5-3x (Caution)"}</span
                >
                <span
                    >🔴 {translations.rrp_coverage_stress ||
                        "RRP < 1.5x (Liquidity Stress)"}</span
                >
            </div>
        </div>
    {/if}

    <!-- Inflation Charts -->
    <div class="charts-grid">
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    📊 {translations.cpi_inflation_yoy || "CPI Inflation (YoY)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cpiRange}
                        onRangeChange={(r) => (cpiRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.cpi_description ||
                    "Consumer Price Index year-over-year change. Target: 2%"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cpiData} layout={cpiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.headline_cpi || "Headline CPI"}:
                    <b>{latestCPI?.toFixed(2) ?? "—"}%</b></span
                >
                <span
                    >{translations.core_cpi || "Core CPI"}:
                    <b>{latestCoreCPI?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    📊 {translations.pce_inflation_yoy || "PCE Inflation (YoY)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={pceRange}
                        onRangeChange={(r) => (pceRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.pce_description ||
                    "Personal Consumption Expenditures (Fed's preferred gauge). Target: 2%"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={pceData} layout={cpiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.headline_pce || "Headline PCE"}:
                    <b>{latestPCE?.toFixed(2) ?? "—"}%</b></span
                >
                <span
                    >{translations.core_pce || "Core PCE"}:
                    <b>{latestCorePCE?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>🏭 {translations.ism_pmi || "ISM PMI"}</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={pmiRange}
                        onRangeChange={(r) => (pmiRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.pmi_description ||
                    "Manufacturing & Services PMI. Above 50 = Expansion, Below 50 = Contraction"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={pmiData} layout={pmiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.manufacturing || "Manufacturing"}:
                    <b class:below-50={latestISMMfg < 50}
                        >{latestISMMfg?.toFixed(1) ?? "—"}</b
                    ></span
                >
                <span
                    >{translations.services || "Services"}:
                    <b class:below-50={latestISMSvc < 50}
                        >{latestISMSvc?.toFixed(1) ?? "—"}</b
                    ></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    👷 {translations.unemployment_rate || "Unemployment Rate"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={unemploymentRange}
                        onRangeChange={(r) => (unemploymentRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.unemployment_description ||
                    "U.S. unemployment rate. Key indicator for Fed dual mandate."}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={unemploymentData}
                    layout={unemploymentLayout}
                />
            </div>
            <div class="latest-values">
                <span
                    >{translations.current || "Current"}:
                    <b>{latestUnemployment?.toFixed(1) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    💼 {translations.nfp_change || "Non-Farm Payrolls (Change)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={nfpViewMode === "raw"}
                            on:click={() => (nfpViewMode = "raw")}
                            >{translations.view_raw || "Raw"}</button
                        >
                        <button
                            class:active={nfpViewMode === "zscore"}
                            on:click={() => (nfpViewMode = "zscore")}
                            >{translations.view_zscore || "Z-Score"}</button
                        >
                        <button
                            class:active={nfpViewMode === "percentile"}
                            on:click={() => (nfpViewMode = "percentile")}
                            >{translations.view_percentile ||
                                "Percentile"}</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={nfpRange}
                        onRangeChange={(r) => (nfpRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {@html translations.nfp_desc || translations.nfp_description}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={nfpViewMode === "zscore"
                        ? nfpZData
                        : nfpViewMode === "percentile"
                          ? nfpPctData
                          : nfpData}
                    layout={{
                        yaxis: {
                            title:
                                nfpViewMode === "zscore"
                                    ? "Z-Score"
                                    : nfpViewMode === "percentile"
                                      ? "Percentile (%)"
                                      : "Jobs (k)",
                            range:
                                nfpViewMode === "zscore"
                                    ? [-4, 4]
                                    : nfpViewMode === "percentile"
                                      ? [0, 100]
                                      : undefined,
                            dtick:
                                nfpViewMode === "percentile" ? 20 : undefined,
                        },
                        shapes:
                            nfpViewMode === "zscore"
                                ? [
                                      {
                                          type: "line",
                                          xref: "paper",
                                          yref: "y",
                                          x0: 0,
                                          x1: 1,
                                          y0: 2,
                                          y1: 2,
                                          line: {
                                              color: "rgba(16, 185, 129, 0.5)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                      {
                                          type: "line",
                                          xref: "paper",
                                          yref: "y",
                                          x0: 0,
                                          x1: 1,
                                          y0: -2,
                                          y1: -2,
                                          line: {
                                              color: "rgba(239, 68, 68, 0.5)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                  ]
                                : nfpViewMode === "percentile"
                                  ? [
                                        {
                                            type: "line",
                                            xref: "paper",
                                            yref: "y",
                                            x0: 0,
                                            x1: 1,
                                            y0: 80,
                                            y1: 80,
                                            line: {
                                                color: "rgba(16, 185, 129, 0.5)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                        {
                                            type: "line",
                                            xref: "paper",
                                            yref: "y",
                                            x0: 0,
                                            x1: 1,
                                            y0: 20,
                                            y1: 20,
                                            line: {
                                                color: "rgba(239, 68, 68, 0.5)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                    ]
                                  : [],
                        margin: { l: 50, r: 20, t: 20, b: 40 },
                    }}
                />
            </div>
            <div class="latest-values">
                <span
                    >{translations.latest_change || "Latest Change"}:
                    <b>
                        {getLatest(
                            dashboardData.fed_forecasts?.nfp_change,
                        )?.toFixed(0) ?? "—"}k</b
                    ></span
                >
                {#if nfpViewMode !== "raw"}
                    <span class="view-mode-badge">
                        {nfpViewMode.toUpperCase()}:
                        <b
                            >{getLatest(
                                dashboardData.signal_metrics?.nfp?.[
                                    nfpViewMode
                                ],
                            )?.toFixed(2) ?? "—"}{nfpViewMode === "percentile"
                                ? "%"
                                : ""}</b
                        >
                    </span>
                {/if}
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    🔍 {translations.jolts_openings || "Job Openings (JOLTS)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={joltsViewMode === "raw"}
                            on:click={() => (joltsViewMode = "raw")}
                            >{translations.view_raw || "Raw"}</button
                        >
                        <button
                            class:active={joltsViewMode === "zscore"}
                            on:click={() => (joltsViewMode = "zscore")}
                            >{translations.view_zscore || "Z-Score"}</button
                        >
                        <button
                            class:active={joltsViewMode === "percentile"}
                            on:click={() => (joltsViewMode = "percentile")}
                            >{translations.view_percentile ||
                                "Percentile"}</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={joltsRange}
                        onRangeChange={(r) => (joltsRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {@html translations.jolts_desc ||
                    translations.jolts_description}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={joltsViewMode === "zscore"
                        ? joltsZData
                        : joltsViewMode === "percentile"
                          ? joltsPctData
                          : joltsData}
                    layout={{
                        yaxis: {
                            title:
                                joltsViewMode === "zscore"
                                    ? "Z-Score"
                                    : joltsViewMode === "percentile"
                                      ? "Percentile (%)"
                                      : "Millions",
                            range:
                                joltsViewMode === "zscore"
                                    ? [-4, 4]
                                    : joltsViewMode === "percentile"
                                      ? [0, 100]
                                      : undefined,
                            dtick:
                                joltsViewMode === "percentile" ? 20 : undefined,
                            autorange: joltsViewMode === "raw",
                        },
                        shapes:
                            joltsViewMode === "zscore"
                                ? [
                                      {
                                          type: "line",
                                          xref: "paper",
                                          yref: "y",
                                          x0: 0,
                                          x1: 1,
                                          y0: 2,
                                          y1: 2,
                                          line: {
                                              color: "rgba(16, 185, 129, 0.5)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                      {
                                          type: "line",
                                          xref: "paper",
                                          yref: "y",
                                          x0: 0,
                                          x1: 1,
                                          y0: -2,
                                          y1: -2,
                                          line: {
                                              color: "rgba(239, 68, 68, 0.5)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                  ]
                                : joltsViewMode === "percentile"
                                  ? [
                                        {
                                            type: "line",
                                            xref: "paper",
                                            yref: "y",
                                            x0: 0,
                                            x1: 1,
                                            y0: 80,
                                            y1: 80,
                                            line: {
                                                color: "rgba(16, 185, 129, 0.5)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                        {
                                            type: "line",
                                            xref: "paper",
                                            yref: "y",
                                            x0: 0,
                                            x1: 1,
                                            y0: 20,
                                            y1: 20,
                                            line: {
                                                color: "rgba(239, 68, 68, 0.5)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                    ]
                                  : [],
                        margin: { l: 50, r: 20, t: 20, b: 40 },
                    }}
                />
            </div>
            <div class="latest-values">
                <span
                    >{translations.total_openings || "Total Openings"}:
                    <b
                        >{(
                            getLatest(dashboardData.fed_forecasts?.jolts) / 1000
                        )?.toFixed(2) ?? "—"}M</b
                    ></span
                >
                {#if joltsViewMode !== "raw"}
                    <span class="view-mode-badge">
                        {joltsViewMode.toUpperCase()}:
                        <b
                            >{getLatest(
                                dashboardData.signal_metrics?.jolts?.[
                                    joltsViewMode
                                ],
                            )?.toFixed(2) ?? "—"}{joltsViewMode === "percentile"
                                ? "%"
                                : ""}</b
                        >
                    </span>
                {/if}
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    🏦 {translations.fed_funds_rate || "Federal Funds Rate"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={fedFundsRange}
                        onRangeChange={(r) => (fedFundsRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.fed_funds_description ||
                    "Effective Federal Funds Rate. Primary tool for monetary policy."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={fedFundsData} layout={fedFundsLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.current_rate || "Current Rate"}:
                    <b>{latestFedFunds?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>
    </div>

    <!-- Inflation Expectations Chart -->
    <div class="chart-section">
        <div class="chart-header">
            <h3>
                💹 {translations.inflation_expectations ||
                    "Inflation Expectations (TIPS Breakeven)"}
            </h3>
            <p class="chart-description">
                {translations.inflation_expectations_description ||
                    "Market-implied inflation expectations vs actual CPI. Divergence signals potential policy shifts."}
            </p>
        </div>
        <div class="chart-container">
            <TimeRangeSelector
                bind:selectedRange={inflationExpectationsRange}
            />
            <Chart data={inflationExpectationsData} layout={cpiLayout} />
            <div class="chart-footer">
                <div class="latest-values">
                    <div class="value-item">
                        <span class="value-label">5Y Breakeven:</span>
                        <span class="value-number">
                            {latestInflationExpect5Y !== null
                                ? `${latestInflationExpect5Y.toFixed(2)}%`
                                : "N/A"}
                        </span>
                    </div>
                    <div class="value-item">
                        <span class="value-label">10Y Breakeven:</span>
                        <span class="value-number">
                            {latestInflationExpect10Y !== null
                                ? `${latestInflationExpect10Y.toFixed(2)}%`
                                : "N/A"}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .fed-forecasts-tab {
        padding: 20px;
    }

    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        border: 1px solid var(--border-color);
    }

    .metric-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .metric-value.above-target {
        color: #ef4444;
    }

    .metric-value.below-50 {
        color: #f59e0b;
    }

    /* ROC Badge Styles */
    .metric-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
        margin-bottom: 4px;
    }

    .roc-badge {
        font-size: 0.68rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
    }

    .roc-badge.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }

    .roc-badge.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    .roc-badge.neutral {
        background: rgba(156, 163, 175, 0.15);
        color: #9ca3af;
    }

    /* Metric Bar */
    .metric-bar {
        width: 100%;
        height: 4px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2px;
        margin-top: 8px;
        overflow: hidden;
    }

    .bar-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.5s ease;
    }

    .bar-fill.bar-bullish {
        background: linear-gradient(90deg, #10b981, #34d399);
    }

    .bar-fill.bar-bearish {
        background: linear-gradient(90deg, #ef4444, #f87171);
    }

    .bar-fill.bar-neutral {
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
    }

    /* Dot Plot Section - Two Column Layout */
    /* Dot Plot Section - Two Column Layout */
    .dot-plot-section {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 25px;
        align-items: stretch;
    }

    .left-stats-column {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .dot-plot-card,
    .prob-chart-card,
    .fomc-calendar-card {
        min-width: 0;
        display: flex;
        flex-direction: column;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }

    .dot-plot-card,
    .prob-chart-card {
        flex: 1;
    }

    .fomc-meetings-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 15px;
    }

    .fomc-meeting-item {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 8px;
        margin-bottom: 8px;
        position: relative;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .fomc-meeting-item:hover {
        background: rgba(0, 0, 0, 0.06);
        border-color: var(--accent-primary);
    }

    .fomc-meeting-item.selected {
        background: rgba(59, 130, 246, 0.1);
        border-color: #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
    }

    .fomc-meeting-item.next-meeting {
        background: rgba(16, 185, 129, 0.05);
        border-left: 4px solid #10b981;
    }

    .prob-footer {
        padding: 10px;
        text-align: center;
        border-top: 1px solid var(--border-color);
        margin-top: 10px;
    }

    .implied-info {
        font-size: 0.9rem;
        color: var(--text-muted);
    }

    .implied-info b {
        color: var(--accent-primary);
    }

    .meeting-date-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 50px;
        width: 50px;
        height: 50px;
        flex-shrink: 0;
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 6px;
        margin-right: 12px;
    }

    .meeting-month {
        font-size: 0.7rem;
        font-weight: 800;
        line-height: 1;
        text-transform: uppercase;
        color: #ffc107;
        margin-bottom: 2px;
    }

    .meeting-days {
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1;
        color: var(--text-primary);
    }

    .meeting-info {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        position: relative;
    }

    .meeting-year {
        font-size: 0.85rem;
        opacity: 0.8;
        min-width: 35px;
    }

    .market-target {
        display: flex;
        flex-direction: column;
        align-items: center;
        background: rgba(59, 130, 246, 0.1);
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .target-label {
        font-size: 0.6rem;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.5px;
        line-height: 1;
        margin-bottom: 1px;
    }

    .target-value {
        font-size: 0.9rem;
        font-weight: 800;
        color: var(--accent-primary);
        line-height: 1;
    }

    .sep-badge {
        position: absolute;
        top: -8px;
        right: -5px;
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        font-size: 0.55rem;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
    }

    .sep-badge-small {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 3px;
    }

    .next-badge {
        position: absolute;
        left: -10px;
        top: -10px;
        background: linear-gradient(135deg, #4caf50, #45a049);
        color: white;
        font-size: 0.55rem;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        z-index: 10;
        letter-spacing: 0.5px;
    }

    /* Rate Probabilities */
    .meeting-probs {
        display: flex;
        flex-direction: column;
        gap: 3px;
        margin-left: auto;
        padding-left: 15px;
        border-left: 1px solid var(--border-color);
        min-width: 240px;
        position: relative;
        z-index: 1;
    }

    .prob-label-group {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .roc-container {
        display: flex;
        gap: 5px;
        flex-wrap: wrap;
    }

    .roc-value {
        font-size: 0.62rem;
        font-weight: 700;
        white-space: nowrap;
        background: rgba(0, 0, 0, 0.03);
        padding: 1px 3px;
        border-radius: 3px;
        color: var(--text-muted);
    }

    .roc-value.up {
        color: #10b981;
    }

    .roc-value.down {
        color: #ef4444;
    }

    .prob-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        gap: 8px;
    }

    .prob-label {
        color: var(--text-muted);
    }

    .prob-value {
        font-weight: 600;
        font-family: "Monaco", monospace;
    }

    .prob-value.high {
        color: #10b981;
    }

    .prob-value.med {
        color: #f59e0b;
    }

    .prob-value.low {
        color: var(--text-muted);
    }

    .cumulative-info {
        margin-top: 4px;
        font-size: 0.65rem;
        color: #3b82f6;
        font-weight: 600;
        text-align: right;
    }

    .fomc-legend {
        padding: 10px 15px;
        border-top: 1px solid rgba(100, 100, 100, 0.2);
        font-size: 0.75rem;
        opacity: 0.8;
    }

    .legend-note {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    @media (max-width: 1200px) {
        .dot-plot-section {
            grid-template-columns: 1fr;
        }
    }

    .dot-plot-container {
        padding: 20px;
    }

    .dot-plot-grid {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        flex-wrap: wrap;
    }

    .dot-plot-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 120px;
    }

    .dot-plot-year {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 10px;
        color: var(--text-primary);
    }

    .dot-plot-dots {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .dot-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .dot-rate {
        font-size: 0.75rem;
        color: var(--text-muted);
        width: 40px;
        text-align: right;
    }

    .dots {
        display: flex;
        gap: 3px;
    }

    .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #3b82f6;
    }

    .dot.median {
        background: #10b981;
        box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
    }

    .dot-plot-median {
        margin-top: 10px;
        font-size: 0.85rem;
        color: #10b981;
        font-weight: 600;
    }

    .dot-plot-legend {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: var(--text-muted);
    }

    .current-rate {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* Charts Grid */
    .charts-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--border-color);
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }

    .chart-header h3 {
        margin: 0;
        font-size: 1.1rem;
    }

    .chart-description {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0 0 15px 0;
        padding: 10px;
        background: var(--chart-description-bg);
        border-radius: 8px;
        border-left: 3px solid var(--accent-primary);
    }

    .chart-content {
        height: 300px;
    }

    .latest-values {
        display: flex;
        justify-content: space-around;
        padding: 12px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.9rem;
    }

    .latest-values b.below-50 {
        color: #f59e0b;
    }

    @media (max-width: 1200px) {
        .charts-grid {
            grid-template-columns: 1fr;
        }

        .metrics-row {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .metrics-row {
            grid-template-columns: 1fr;
        }

        .dot-plot-grid {
            flex-direction: column;
            align-items: center;
        }
    }

    /* Treasury Settlements Table */
    .treasury-settlements-card {
        margin-bottom: 25px;
    }

    .treasury-settlements-card .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .rrp-indicator {
        font-size: 0.85rem;
        color: var(--text-muted);
        background: rgba(59, 130, 246, 0.1);
        padding: 4px 10px;
        border-radius: 6px;
    }

    .rrp-indicator b {
        color: var(--accent-primary);
    }

    .settlements-table-container {
        overflow-x: auto;
        padding: 15px;
    }

    .settlements-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }

    .settlements-table th {
        text-align: left;
        padding: 8px 12px;
        border-bottom: 2px solid var(--border-color);
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }

    .settlements-table td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border-color);
    }

    .settlement-row:hover {
        background: rgba(59, 130, 246, 0.05);
    }

    .settlement-row.high-risk {
        background: rgba(239, 68, 68, 0.08);
    }

    .settlement-row.medium-risk {
        background: rgba(245, 158, 11, 0.08);
    }

    .settlement-date {
        font-weight: 600;
        color: var(--text-primary);
    }

    .settlement-type {
        color: var(--text-muted);
        font-size: 0.8rem;
    }

    .settlement-amount {
        font-weight: 700;
        color: var(--accent-primary);
    }

    .settlement-rrp {
        font-weight: 600;
        color: #22c55e;
    }

    .settlement-coverage {
        font-weight: 600;
    }

    .settlement-risk {
        text-align: center;
    }

    .risk-badge {
        font-size: 1rem;
    }

    .settlements-legend {
        display: flex;
        justify-content: center;
        gap: 20px;
        padding: 10px;
        font-size: 0.75rem;
        color: var(--text-muted);
        border-top: 1px solid var(--border-color);
    }

    /* Pagination Controls */
    .pagination-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 15px;
        padding: 12px;
        border-top: 1px solid var(--border-color);
    }

    .pagination-btn {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.8rem;
        transition: all 0.2s ease;
    }

    .pagination-btn:hover:not(:disabled) {
        background: var(--accent-primary);
        color: white;
    }

    .pagination-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    .pagination-info {
        font-size: 0.8rem;
        color: var(--text-muted);
    }

    /* Status Badges */
    .status-badge {
        font-size: 0.7rem;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 600;
    }

    .status-badge.future {
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
    }

    .status-badge.past {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
    }

    .settlement-row.future-row {
        background: rgba(59, 130, 246, 0.03);
    }

    .settlement-row.future-row:hover {
        background: rgba(59, 130, 246, 0.08);
    }

    /* Header Controls Right */
    .header-controls-right {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    /* View Toggle */
    .view-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-size: 0.8rem;
    }

    .view-toggle input[type="checkbox"] {
        width: 16px;
        height: 16px;
        cursor: pointer;
        accent-color: var(--accent-primary);
    }

    .toggle-label {
        color: var(--text-muted);
        font-size: 0.75rem;
        white-space: nowrap;
    }

    /* Settlements Filters */
    .settlements-filters {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        padding: 12px 15px;
        background: rgba(0, 0, 0, 0.03);
        border-bottom: 1px solid var(--border-color);
        align-items: center;
    }

    .filter-group {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .filter-group label {
        font-size: 0.75rem;
        color: var(--text-muted);
        white-space: nowrap;
    }

    .filter-group select,
    .filter-group input[type="number"] {
        font-size: 0.75rem;
        padding: 4px 8px;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    .filter-group select {
        min-width: 80px;
    }

    .filter-group input[type="number"] {
        width: 70px;
    }

    .clear-filters-btn {
        font-size: 0.75rem;
        padding: 4px 10px;
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 4px;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .clear-filters-btn:hover {
        background: var(--accent-primary);
        color: white;
        border-color: var(--accent-primary);
    }

    @media (max-width: 768px) {
        .settlements-filters {
            gap: 8px;
        }

        .filter-group {
            width: 100%;
            justify-content: space-between;
        }
    }
    /* Mode selector styling */
    .mode-selector {
        display: inline-flex;
        gap: 2px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 6px;
        padding: 2px;
        margin-right: 12px;
    }
    :global([data-theme="dark"]) .mode-selector {
        background: rgba(255, 255, 255, 0.05);
    }
    .mode-selector button {
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: transparent;
        color: var(--text-muted);
    }
    .mode-selector button:hover {
        color: var(--text-primary);
    }
    .mode-selector button.active {
        background: linear-gradient(
            135deg,
            var(--accent-primary) 0%,
            var(--accent-secondary) 100%
        );
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .view-mode-badge {
        font-size: 11px;
        background: rgba(59, 130, 246, 0.1);
        color: var(--accent-secondary);
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 10px;
        font-weight: 600;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
</style>
