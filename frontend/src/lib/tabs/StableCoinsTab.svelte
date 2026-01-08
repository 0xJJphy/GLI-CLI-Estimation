<script>
    /**
     * StableCoinsTab.svelte
     * Displays stablecoin market caps, growth trends, and depeg monitoring.
     * Part of the Macro section under Liquidity.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import SFAIChart from "../components/SFAIChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import { filterPlotlyData, getCutoffDate } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    // Core props
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges and modes
    let aggregateRange = "1Y";
    let individualRange = "1Y";
    let aggregateMode = "absolute"; // Modes: absolute, roc1m, roc3m, yoy, accel_z
    let normMode = "raw"; // Normalization: raw, zscore, percentile

    // Check if current mode supports normalization
    $: isRocMode = ["roc7d", "roc1m", "roc3m"].includes(aggregateMode);

    // Normalization mode options
    $: normModes = [
        { value: "raw", label: t("raw_view", "Raw (%)") },
        { value: "zscore", label: "Z-Score" },
        { value: "percentile", label: t("percentile_view", "Percentile") },
    ];

    function selectNormMode(mode) {
        normMode = mode;
    }

    // Pagination for depegs
    let currentPage = 1;
    let itemsPerPage = 10;

    $: aggregateModes = [
        { value: "absolute", label: t("raw_view", "Absolute") },
        { value: "roc7d", label: t("roc_7d_col", "ROC 7D") },
        { value: "roc1m", label: t("roc_1m_col", "ROC 1M") },
        { value: "roc3m", label: t("roc_3m_col", "ROC 3M") },
        { value: "yoy", label: t("yoy_change", "YoY %") },
        {
            value: "dominance",
            label: t("stablecoins_mkt_dom", "Stables Dominance %"),
        },
        { value: "accel_z", label: t("accel_col", "Accel Z-Score") },
    ];

    function selectMode(mode) {
        aggregateMode = mode;
    }

    // Existing aggregate chart logic...

    // Existing aggregate chart logic...

    // Card container references for download feature
    let aggregateCard;
    let growthCard;
    let depegCard;

    // Helper to get translation with fallback
    $: t = (key, fallback) => translations[key] || fallback;

    // Stablecoin colors
    const stablecoinColors = {
        USDT: "#26A17B", // Tether green
        USDC: "#2775CA", // Circle blue
        DAI: "#F5AC37", // MakerDAO gold
        TUSD: "#1A5AFF", // TrueUSD blue
        USDD: "#00D395", // USDD teal
        USDP: "#00A3FF", // Pax blue
        USDE: "#00FFD1", // Ethena teal
        PYUSD: "#0070BA", // PayPal blue
        FDUSD: "#F1B500", // FDUSD gold
        RLUSD: "#00AAE4", // Ripple blue
        USDG: "#4F46E5", // Global Dollar
        USD1W: "#8B5CF6", // USD1W violet
    };

    // Get stablecoin data from dashboardData
    $: stablecoinsData = dashboardData.stablecoins || {};
    $: stableDates = stablecoinsData.dates || [];
    $: marketCaps = stablecoinsData.market_caps || {};
    $: totalSupply = stablecoinsData.total || [];
    $: prices = stablecoinsData.prices || {};
    $: growth = stablecoinsData.growth || {};
    $: dominance = stablecoinsData.dominance || {};
    $: dominanceTotal = stablecoinsData.dominance_total || {};
    $: depegEvents = stablecoinsData.depeg_events || [];

    // Dominance data (STABLE.C.D and custom)
    $: stableIndexDom = stablecoinsData.stable_index_dom || [];
    $: customStablesDom = stablecoinsData.custom_stables_dom || [];
    $: individualDoms = stablecoinsData.individual_doms || {};

    // STABLE.C.D Dominance ROCs
    $: stableIndexDomRoc7d = stablecoinsData.stable_index_dom_roc_7d || [];
    $: stableIndexDomRoc30d = stablecoinsData.stable_index_dom_roc_30d || [];
    $: stableIndexDomRoc90d = stablecoinsData.stable_index_dom_roc_90d || [];
    $: stableIndexDomRoc180d = stablecoinsData.stable_index_dom_roc_180d || [];
    $: stableIndexDomRocYoy = stablecoinsData.stable_index_dom_roc_yoy || [];
    // STABLE.C.D Dominance ROC Z-scores and Percentiles
    $: stableIndexDomRoc7dZ = stablecoinsData.stable_index_dom_roc_7d_z || [];
    $: stableIndexDomRoc30dZ = stablecoinsData.stable_index_dom_roc_30d_z || [];
    $: stableIndexDomRoc90dZ = stablecoinsData.stable_index_dom_roc_90d_z || [];
    $: stableIndexDomRoc7dPct =
        stablecoinsData.stable_index_dom_roc_7d_pct || [];
    $: stableIndexDomRoc30dPct =
        stablecoinsData.stable_index_dom_roc_30d_pct || [];
    $: stableIndexDomRoc90dPct =
        stablecoinsData.stable_index_dom_roc_90d_pct || [];

    // Custom Stables Dominance ROCs
    $: customStablesDomRoc7d = stablecoinsData.custom_stables_dom_roc_7d || [];
    $: customStablesDomRoc30d =
        stablecoinsData.custom_stables_dom_roc_30d || [];
    $: customStablesDomRoc90d =
        stablecoinsData.custom_stables_dom_roc_90d || [];
    $: customStablesDomRoc180d =
        stablecoinsData.custom_stables_dom_roc_180d || [];
    $: customStablesDomRocYoy =
        stablecoinsData.custom_stables_dom_roc_yoy || [];
    // Custom Dominance ROC Z-scores and Percentiles
    $: customStablesDomRoc7dZ =
        stablecoinsData.custom_stables_dom_roc_7d_z || [];
    $: customStablesDomRoc30dZ =
        stablecoinsData.custom_stables_dom_roc_30d_z || [];
    $: customStablesDomRoc90dZ =
        stablecoinsData.custom_stables_dom_roc_90d_z || [];
    $: customStablesDomRoc7dPct =
        stablecoinsData.custom_stables_dom_roc_7d_pct || [];
    $: customStablesDomRoc30dPct =
        stablecoinsData.custom_stables_dom_roc_30d_pct || [];
    $: customStablesDomRoc90dPct =
        stablecoinsData.custom_stables_dom_roc_90d_pct || [];

    let indexDomRocRange = "1Y";

    // Dominance ROC chart state - Two selectors like Total Stablecoin Supply
    // Dominance Analytics chart state - Two selectors like Total Stablecoin Supply
    $: domRocPeriods = [
        { value: "absolute", label: "Dominance (%)" },
        { value: "7d", label: "ROC 7D" },
        { value: "30d", label: "ROC 30D" },
        { value: "90d", label: "ROC 90D" },
        { value: "180d", label: "ROC 180D" },
        { value: "yoy", label: "YoY" },
    ];

    $: domRocViewModes = [
        { value: "raw", label: t("raw_view", "Raw (%)") },
        { value: "zscore", label: "Z-Score" },
        { value: "percentile", label: "Percentile" },
    ];

    let selectedDomRocPeriod = "absolute"; // absolute, 7d, 30d, 90d, 180d, yoy
    let selectedDomRocViewMode = "raw"; // raw, zscore, percentile

    function selectDomRocPeriod(period) {
        selectedDomRocPeriod = period;
    }

    function selectDomRocViewMode(mode) {
        selectedDomRocViewMode = mode;
    }

    // BTC data for SFAI chart
    $: btcData = dashboardData.btc?.price || [];
    $: btcDates = dashboardData.dates || [];

    // SFAI Chart state
    let sfaiRange = "1Y";
    let sfaiMode = "regime"; // regime, index, velocity

    $: sfaiModes = [
        { value: "regime", label: "Regime" },
        { value: "index", label: "SFAI Index" },
        { value: "velocity", label: "Velocity" },
    ];

    function selectSfaiMode(mode) {
        sfaiMode = mode;
    }

    // SFAI Regime data
    $: sfaiRegime = stablecoinsData.sfai_regime || [];
    $: sfaiContinuous = stablecoinsData.sfai_continuous || [];
    $: sfaiVelocity = stablecoinsData.sfai_velocity || [];

    // Regime color mapping for backgrounds
    const sfaiRegimeColors = {
        0: { base: "rgba(107, 114, 128, 0.15)", solid: "#6b7280" }, // Neutral
        1: { base: "rgba(34, 197, 94, 0.25)", solid: "#22c55e" }, // Fresh Inflow
        2: { base: "rgba(239, 68, 68, 0.25)", solid: "#ef4444" }, // Profit Taking
        3: { base: "rgba(59, 130, 246, 0.25)", solid: "#3b82f6" }, // Buying Pressure
        4: { base: "rgba(139, 92, 246, 0.25)", solid: "#8b5cf6" }, // Capitulation
    };

    // Filter data by range (simplified)
    function filterSfaiByRange(arr, range) {
        if (!stableDates.length) return arr;
        if (range === "ALL") return arr;
        const cutoff = getCutoffDate(range);
        if (!cutoff) return arr;
        const indices = [];
        for (let i = 0; i < stableDates.length; i++) {
            if (new Date(stableDates[i]) >= cutoff) indices.push(i);
        }
        return indices.map((i) => arr[i]);
    }

    function getSfaiFilteredDates(range) {
        return filterSfaiByRange(stableDates, range);
    }

    // Create SFAI regime background shapes (like RegimesTab)
    function createSfaiShapes(regimes, range, isDarkMode) {
        if (!regimes || !stableDates.length) return [];
        const filteredDates = getSfaiFilteredDates(range);
        const filteredRegimes = filterSfaiByRange(regimes, range);
        if (!filteredDates.length || !filteredRegimes.length) return [];

        // Find first valid BTC data point to start from
        const btcFiltered = filterSfaiByRange(
            btcData.slice(-stableDates.length),
            range,
        );
        let firstValidIdx = 0;
        for (let i = 0; i < btcFiltered.length; i++) {
            if (
                btcFiltered[i] !== null &&
                btcFiltered[i] !== undefined &&
                btcFiltered[i] > 0
            ) {
                firstValidIdx = i;
                break;
            }
        }

        const shapes = [];
        let currentRegime = null;
        let blockStartIdx = firstValidIdx;

        for (let i = firstValidIdx; i <= filteredDates.length; i++) {
            const regime =
                i < filteredRegimes.length ? filteredRegimes[i] : null;

            if (regime !== currentRegime || i === filteredDates.length) {
                // Close previous block
                if (currentRegime !== null && currentRegime !== 0) {
                    const d0 = filteredDates[blockStartIdx];
                    const d1 =
                        filteredDates[
                            Math.min(i - 1, filteredDates.length - 1)
                        ];
                    if (d0 && d1) {
                        const color =
                            sfaiRegimeColors[currentRegime]?.base ||
                            sfaiRegimeColors[0].base;
                        shapes.push({
                            type: "rect",
                            xref: "x",
                            yref: "paper",
                            x0: d0,
                            x1: d1,
                            y0: 0.25, // Start above the indicator panel
                            y1: 1,
                            fillcolor: color,
                            line: { width: 0 },
                            layer: "below",
                        });
                    }
                }
                currentRegime = regime;
                blockStartIdx = i;
            }
        }
        return shapes;
    }

    // Build Plotly SFAI chart data
    $: sfaiPlotlyData = (() => {
        if (!stableDates.length || !btcData.length) return [];

        const filteredDates = getSfaiFilteredDates(sfaiRange);
        const btcAligned = btcData.slice(-stableDates.length);
        const btcFiltered = filterSfaiByRange(btcAligned, sfaiRange);

        // Find first valid BTC index
        let firstValidIdx = 0;
        for (let i = 0; i < btcFiltered.length; i++) {
            if (
                btcFiltered[i] !== null &&
                btcFiltered[i] !== undefined &&
                btcFiltered[i] > 0
            ) {
                firstValidIdx = i;
                break;
            }
        }

        // Trim dates and data from first valid BTC
        const trimmedDates = filteredDates.slice(firstValidIdx);
        const trimmedBtc = btcFiltered.slice(firstValidIdx);

        // BTC trace (upper panel, log scale)
        const btcTrace = {
            x: trimmedDates,
            y: trimmedBtc,
            name: "BTC Price",
            type: "scatter",
            mode: "lines",
            line: { color: "#f7931a", width: 2 },
            yaxis: "y2",
            hovertemplate: "%{x}<br>BTC: $%{y:,.0f}<extra></extra>",
        };

        // Indicator trace (lower panel)
        let indicatorTrace;
        if (sfaiMode === "regime") {
            const regimeFiltered = filterSfaiByRange(
                sfaiRegime,
                sfaiRange,
            ).slice(firstValidIdx);
            indicatorTrace = {
                x: trimmedDates,
                y: regimeFiltered,
                name: "Regime",
                type: "bar",
                marker: {
                    color: regimeFiltered.map(
                        (r) => sfaiRegimeColors[r]?.solid || "#6b7280",
                    ),
                },
                yaxis: "y3",
                hovertemplate: "%{x}<br>Regime: %{y}<extra></extra>",
            };
        } else if (sfaiMode === "index") {
            const indexFiltered = filterSfaiByRange(
                sfaiContinuous,
                sfaiRange,
            ).slice(firstValidIdx);
            indicatorTrace = {
                x: trimmedDates,
                y: indexFiltered,
                name: "SFAI Index",
                type: "bar",
                marker: {
                    color: indexFiltered.map((v) =>
                        v >= 0 ? "#22c55e" : "#ef4444",
                    ),
                },
                yaxis: "y3",
                hovertemplate: "%{x}<br>SFAI: %{y:.2f}<extra></extra>",
            };
        } else {
            const velocityFiltered = filterSfaiByRange(
                sfaiVelocity,
                sfaiRange,
            ).slice(firstValidIdx);
            indicatorTrace = {
                x: trimmedDates,
                y: velocityFiltered,
                name: "Velocity",
                type: "scatter",
                mode: "lines",
                line: { color: "#f97316", width: 1.5 },
                fill: "tozeroy",
                fillcolor: "rgba(249, 115, 22, 0.2)",
                yaxis: "y3",
                hovertemplate: "%{x}<br>Velocity: %{y:.2f}<extra></extra>",
            };
        }

        return [btcTrace, indicatorTrace];
    })();

    // SFAI Plotly layout with dual-axis and background shapes
    $: sfaiPlotlyLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
        },
        yaxis: { visible: false, domain: [0.25, 1] },
        yaxis2: {
            title: "",
            type: "log",
            side: "right",
            overlaying: "y",
            showgrid: true,
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            color: darkMode ? "#94a3b8" : "#475569",
            domain: [0.25, 1],
            tickformat: "$,.0f",
        },
        yaxis3: {
            title: "",
            side: "left",
            anchor: "x",
            domain: [0, 0.22],
            color: darkMode ? "#94a3b8" : "#475569",
            showgrid: false,
            zeroline: false,
        },
        shapes:
            sfaiMode === "regime"
                ? createSfaiShapes(sfaiRegime, sfaiRange, darkMode)
                : [],
        margin: { t: 20, b: 40, l: 50, r: 60 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: false,
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Calculate latest values
    $: latestTotal =
        totalSupply.length > 0 ? totalSupply[totalSupply.length - 1] : 0;
    $: latestTotalFormatted = latestTotal
        ? `$${latestTotal.toFixed(1)}B`
        : "N/A";

    // Aggregate chart data
    $: aggregateChartData = filterPlotlyData(
        [
            (() => {
                let yData = totalSupply;
                let name = t(
                    "stablecoins_aggregate",
                    "Total Stablecoin Supply",
                );
                let type = "scatter";
                let fill = "tozeroy";
                let color = "#6366f1";

                if (aggregateMode === "roc7d") {
                    if (normMode === "zscore") {
                        yData = stablecoinsData.total_roc_7d_z || [];
                        name = t("roc_7d_col", "ROC 7D") + " Z";
                    } else if (normMode === "percentile") {
                        yData = stablecoinsData.total_roc_7d_pct || [];
                        name = t("roc_7d_col", "ROC 7D") + " Pctl";
                    } else {
                        yData = stablecoinsData.total_roc_7d || [];
                        name = t("roc_7d_col", "ROC 7D (%)");
                    }
                    color = "#2DD4BF"; // teal
                } else if (aggregateMode === "roc1m") {
                    if (normMode === "zscore") {
                        yData = stablecoinsData.total_roc_1m_z || [];
                        name = t("roc_1m_col", "ROC 1M") + " Z";
                    } else if (normMode === "percentile") {
                        yData = stablecoinsData.total_roc_1m_pct || [];
                        name = t("roc_1m_col", "ROC 1M") + " Pctl";
                    } else {
                        yData = stablecoinsData.total_roc_1m || [];
                        name = t("roc_1m_col", "ROC 1M (%)");
                    }
                    color = "#10b981"; // emerald
                } else if (aggregateMode === "roc3m") {
                    if (normMode === "zscore") {
                        yData = stablecoinsData.total_roc_3m_z || [];
                        name = t("roc_3m_col", "ROC 3M") + " Z";
                    } else if (normMode === "percentile") {
                        yData = stablecoinsData.total_roc_3m_pct || [];
                        name = t("roc_3m_col", "ROC 3M") + " Pctl";
                    } else {
                        yData = stablecoinsData.total_roc_3m || [];
                        name = t("roc_3m_col", "ROC 3M (%)");
                    }
                    color = "#3b82f6"; // blue
                } else if (aggregateMode === "yoy") {
                    yData = stablecoinsData.total_yoy || [];
                    name = t("yoy_change", "YoY Change (%)");
                    color = "#f43f5e"; // rose
                } else if (aggregateMode === "dominance") {
                    yData = stablecoinsData.total_dominance || [];
                    name = t(
                        "stablecoins_mkt_dom",
                        "Total Stables Dominance (%)",
                    );
                    color = "#fbbf24"; // amber
                } else if (aggregateMode === "accel_z") {
                    yData = stablecoinsData.total_accel_z || [];
                    name = t("accel_col", "Acceleration Z-Score");
                    type = "bar";
                    fill = "none";
                    color = "#8b5cf6"; // violet
                }

                const trace = {
                    x: stableDates,
                    y: yData,
                    name: name,
                    type: type,
                };

                if (type === "bar") {
                    trace.marker = { color: color };
                } else {
                    trace.mode = "lines";
                    trace.fill = fill;
                    trace.line = { color: color, width: 2, shape: "spline" };
                    if (darkMode) {
                        // Simple hex to rgba conversion for the fill
                        const r = parseInt(color.slice(1, 3), 16);
                        const g = parseInt(color.slice(3, 5), 16);
                        const b = parseInt(color.slice(5, 7), 16);
                        trace.fillcolor = `rgba(${r}, ${g}, ${b}, 0.15)`;
                    } else {
                        trace.fillcolor = "rgba(99, 102, 241, 0.1)";
                    }
                }

                return trace;
            })(),
        ],
        stableDates,
        aggregateRange,
    );

    // Individual stablecoin traces
    $: individualTraces = Object.entries(marketCaps).map(([name, values]) => ({
        x: stableDates,
        y: values,
        name: name,
        type: "scatter",
        mode: "lines",
        line: {
            color: stablecoinColors[name] || "#888888",
            width: 2,
            shape: "spline",
        },
    }));

    $: individualChartData = filterPlotlyData(
        individualTraces,
        stableDates,
        individualRange,
    );

    // Dominance ROC Chart (based on selected period and view mode)
    // Helper to get the right data based on period and view mode
    $: getStableIndexDomData = (period, viewMode) => {
        if (period === "absolute") return stableIndexDom;
        if (viewMode === "raw") {
            return period === "7d"
                ? stableIndexDomRoc7d
                : period === "30d"
                  ? stableIndexDomRoc30d
                  : period === "90d"
                    ? stableIndexDomRoc90d
                    : period === "180d"
                      ? stableIndexDomRoc180d
                      : stableIndexDomRocYoy;
        } else if (viewMode === "zscore") {
            // Z-scores only available for 7d, 30d, 90d
            return period === "7d"
                ? stableIndexDomRoc7dZ
                : period === "90d"
                  ? stableIndexDomRoc90dZ
                  : stableIndexDomRoc30dZ; // default to 30d for 180d/yoy
        } else {
            // Percentiles only available for 7d, 30d, 90d
            return period === "7d"
                ? stableIndexDomRoc7dPct
                : period === "90d"
                  ? stableIndexDomRoc90dPct
                  : stableIndexDomRoc30dPct; // default to 30d for 180d/yoy
        }
    };

    $: getCustomStablesDomData = (period, viewMode) => {
        if (period === "absolute") return customStablesDom;
        if (viewMode === "raw") {
            return period === "7d"
                ? customStablesDomRoc7d
                : period === "30d"
                  ? customStablesDomRoc30d
                  : period === "90d"
                    ? customStablesDomRoc90d
                    : period === "180d"
                      ? customStablesDomRoc180d
                      : customStablesDomRocYoy;
        } else if (viewMode === "zscore") {
            return period === "7d"
                ? customStablesDomRoc7dZ
                : period === "90d"
                  ? customStablesDomRoc90dZ
                  : customStablesDomRoc30dZ;
        } else {
            return period === "7d"
                ? customStablesDomRoc7dPct
                : period === "90d"
                  ? customStablesDomRoc90dPct
                  : customStablesDomRoc30dPct;
        }
    };

    $: selectedStableRoc = getStableIndexDomData(
        selectedDomRocPeriod,
        selectedDomRocViewMode,
    );
    $: selectedCustomStablesRoc = getCustomStablesDomData(
        selectedDomRocPeriod,
        selectedDomRocViewMode,
    );

    $: domRocYAxisLabel =
        selectedDomRocPeriod === "absolute"
            ? "Dominance (%)"
            : selectedDomRocViewMode === "zscore"
              ? "Z-Score"
              : selectedDomRocViewMode === "percentile"
                ? "Percentile"
                : "%";

    $: domRocPeriodLabel =
        domRocPeriods.find((p) => p.value === selectedDomRocPeriod)?.label ||
        "";

    $: indexDomRocChartData = filterPlotlyData(
        [
            {
                x: stableDates,
                y: selectedStableRoc,
                name:
                    selectedDomRocPeriod === "absolute"
                        ? "STABLE.C.D (%)"
                        : `STABLE.C.D ${domRocPeriodLabel}`,
                type: "scatter",
                mode: "lines",
                line: {
                    color: "#6366f1",
                    width: selectedDomRocPeriod === "absolute" ? 2.5 : 2,
                    shape: "spline",
                },
                fill:
                    selectedDomRocPeriod === "absolute" ? undefined : "tozeroy",
                fillcolor:
                    selectedDomRocPeriod === "absolute"
                        ? undefined
                        : "rgba(99, 102, 241, 0.1)",
                visible: "legendonly",
            },
            {
                x: stableDates,
                y: selectedCustomStablesRoc,
                name:
                    selectedDomRocPeriod === "absolute"
                        ? "Custom Stables Dom (%)"
                        : `Custom Dom ${domRocPeriodLabel}`,
                type: "scatter",
                mode: "lines",
                line: {
                    color: "#10b981",
                    width: selectedDomRocPeriod === "absolute" ? 2.5 : 2,
                    shape: "spline",
                },
            },
        ],
        stableDates,
        indexDomRocRange,
    );

    // Growth table data (sorted by 30d growth)
    $: growthTableData = Object.entries(growth)
        .map(([name, g]) => ({
            name,
            color: stablecoinColors[name] || "#888888",
            mcap:
                marketCaps[name]?.length > 0
                    ? marketCaps[name][marketCaps[name].length - 1]
                    : 0,
            dom:
                dominance[name]?.length > 0
                    ? dominance[name][dominance[name].length - 1]
                    : 0,
            domTotal:
                dominanceTotal[name]?.length > 0
                    ? dominanceTotal[name][dominanceTotal[name].length - 1]
                    : 0,
            growth7d: g["7d"] || 0,
            growth30d: g["30d"] || 0,
            growth90d: g["90d"] || 0,
        }))
        .sort((a, b) => b.growth30d - a.growth30d);

    // Current depeg status
    $: currentDepegs = Object.entries(prices).map(([name, priceArr]) => {
        const lastPrice =
            priceArr.length > 0 ? priceArr[priceArr.length - 1] : 1.0;
        const deviation = (lastPrice - 1.0) * 100;
        const isDepegged = Math.abs(deviation) > 1.0;
        return {
            name,
            price: lastPrice,
            deviation,
            isDepegged,
            color: stablecoinColors[name] || "#888888",
        };
    });

    // Recent depeg events (paginated)
    $: sortedDepegs = [...depegEvents].reverse();
    $: totalPages = Math.ceil(sortedDepegs.length / itemsPerPage);
    $: paginatedDepegs = sortedDepegs.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage,
    );

    function setPage(page) {
        if (page >= 1 && page <= totalPages) {
            currentPage = page;
        }
    }

    // Format number with color
    const formatGrowth = (val) => {
        if (val === undefined || val === null) return "N/A";
        const sign = val >= 0 ? "+" : "";
        return `${sign}${val.toFixed(2)}%`;
    };

    const getGrowthClass = (val) => {
        if (val === undefined || val === null) return "";
        return val >= 0 ? "positive" : "negative";
    };
</script>

<!-- Header -->
<div class="tab-header" class:light={!darkMode}>
    <div class="header-content">
        <h2>{t("stablecoins_title", "Stablecoin Market Overview")}</h2>
        <p class="description">
            {t(
                "stablecoins_desc",
                "Track stablecoin market caps, growth trends, and depeg events.",
            )}
        </p>
    </div>
    <div class="header-stats">
        <div class="stat-item">
            <span class="stat-label"
                >{t("stablecoins_aggregate", "Total Supply")}</span
            >
            <span class="stat-value">{latestTotalFormatted}</span>
        </div>
    </div>
</div>

<!-- Main Grid -->
<div class="stablecoins-grid" class:light={!darkMode}>
    <!-- Aggregate Supply Chart -->
    <div class="chart-card full-width" bind:this={aggregateCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_aggregate", "Total Stablecoin Supply")}</h3>
            <div class="header-controls">
                <Dropdown
                    options={aggregateModes}
                    bind:value={aggregateMode}
                    onSelect={selectMode}
                    {darkMode}
                    small={true}
                />
                {#if isRocMode}
                    <Dropdown
                        options={normModes}
                        bind:value={normMode}
                        onSelect={selectNormMode}
                        {darkMode}
                        small={true}
                    />
                {/if}
                <TimeRangeSelector
                    selectedRange={aggregateRange}
                    onRangeChange={(r) => (aggregateRange = r)}
                />
                <button
                    class="download-btn"
                    title="Download Chart"
                    on:click={() =>
                        downloadCardAsImage(
                            aggregateCard,
                            "stablecoin_aggregate",
                        )}
                >
                    📥
                </button>
            </div>
        </div>
        <div class="chart-content">
            {#if aggregateChartData && aggregateChartData.length > 0}
                <Chart
                    data={aggregateChartData}
                    layout={{ title: "" }}
                    {darkMode}
                />
            {:else}
                <div class="no-data">
                    {t("stablecoins_no_data", "No stablecoin data available")}
                </div>
            {/if}
        </div>
    </div>

    <!-- Individual Stablecoins Chart -->
    <div class="chart-card full-width">
        <div class="chart-header">
            <h3>{t("stablecoins_individual", "Individual Stablecoins")}</h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={individualRange}
                    onRangeChange={(r) => (individualRange = r)}
                />
            </div>
        </div>
        <div class="chart-content">
            {#if individualChartData && individualChartData.length > 0}
                <Chart
                    data={individualChartData}
                    layout={{ title: "" }}
                    {darkMode}
                />
            {:else}
                <div class="no-data">
                    {t(
                        "stablecoins_no_individual_data",
                        "No individual stablecoin data",
                    )}
                </div>
            {/if}
        </div>
    </div>

    <!-- Dominance Analytics Chart -->
    <div class="chart-card full-width">
        <div class="chart-header">
            <h3>
                {selectedDomRocPeriod === "absolute"
                    ? t("stablecoins_index_dom", "Stablecoin Index Dominance")
                    : t("stablecoins_dom_roc", "Dominance Rate of Change")}
            </h3>
            <div class="header-controls">
                <!-- Data Mode Dropdown (Absolute vs ROC) -->
                <Dropdown
                    options={domRocPeriods}
                    bind:value={selectedDomRocPeriod}
                    onSelect={selectDomRocPeriod}
                    {darkMode}
                    small={true}
                />
                <!-- View Mode Dropdown (Raw, Z-Score, Percentile) - Only for ROC modes -->
                {#if selectedDomRocPeriod !== "absolute"}
                    <Dropdown
                        options={domRocViewModes}
                        bind:value={selectedDomRocViewMode}
                        onSelect={selectDomRocViewMode}
                        {darkMode}
                        small={true}
                    />
                {/if}
                <TimeRangeSelector
                    selectedRange={indexDomRocRange}
                    onRangeChange={(r) => (indexDomRocRange = r)}
                />
            </div>
        </div>
        <div class="chart-content">
            {#if indexDomRocChartData && indexDomRocChartData.length > 0}
                <Chart
                    data={indexDomRocChartData}
                    layout={{
                        title: "",
                        yaxis: { title: domRocYAxisLabel },
                    }}
                    {darkMode}
                />
            {:else}
                <div class="no-data">
                    {t("stablecoins_no_roc_data", "No data available")}
                </div>
            {/if}
        </div>
    </div>

    <!-- SFAI Flow Attribution Chart -->
    <div class="chart-card full-width sfai-card">
        <div class="chart-header">
            <h3>Flow Attribution (SFAI)</h3>
            <div class="header-controls">
                <!-- Mode dropdown -->
                <Dropdown
                    options={sfaiModes}
                    bind:value={sfaiMode}
                    onSelect={selectSfaiMode}
                    {darkMode}
                    small={true}
                />
                <!-- Time Range Selector -->
                <TimeRangeSelector
                    selectedRange={sfaiRange}
                    onRangeChange={(r) => (sfaiRange = r)}
                    ranges={[
                        { value: "7D", label: "7D" },
                        { value: "21D", label: "21D" },
                        { value: "1M", label: "1M" },
                        { value: "3M", label: "3M" },
                        { value: "6M", label: "6M" },
                        { value: "1Y", label: "1Y" },
                        { value: "2Y", label: "2Y" },
                        { value: "3Y", label: "3Y" },
                        { value: "5Y", label: "5Y" },
                        { value: "ALL", label: "ALL" },
                    ]}
                />
            </div>
        </div>
        {#if sfaiMode === "regime"}
            <div class="sfai-legend">
                <span class="legend-item"
                    ><span class="legend-dot" style="background:#22c55e"
                    ></span>Fresh Inflow</span
                >
                <span class="legend-item"
                    ><span class="legend-dot" style="background:#ef4444"
                    ></span>Profit Taking</span
                >
                <span class="legend-item"
                    ><span class="legend-dot" style="background:#3b82f6"
                    ></span>Buying Pressure</span
                >
                <span class="legend-item"
                    ><span class="legend-dot" style="background:#8b5cf6"
                    ></span>Capitulation</span
                >
            </div>
        {/if}
        <div class="chart-content sfai-chart-content">
            {#if sfaiPlotlyData.length > 0 && btcData.length > 0}
                <Chart
                    data={sfaiPlotlyData}
                    layout={sfaiPlotlyLayout}
                    {darkMode}
                />
            {:else}
                <div class="no-data">
                    {t("stablecoins_no_data", "No SFAI data available")}
                </div>
            {/if}
        </div>
    </div>

    <!-- Growth Analysis Table -->
    <div class="chart-card" bind:this={growthCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_growth_table", "Growth Analysis")}</h3>
            <button
                class="download-btn"
                title="Download Table"
                on:click={() =>
                    downloadCardAsImage(growthCard, "stablecoin_growth")}
            >
                📥
            </button>
        </div>
        <div class="table-container">
            <table class="growth-table">
                <thead>
                    <tr>
                        <th>{t("stablecoins_name", "Stablecoin")}</th>
                        <th>{t("stablecoins_market_cap", "Market Cap")}</th>
                        <th>{t("stablecoins_dominance", "Dom.")}</th>
                        <th
                            title={t(
                                "stablecoins_mkt_dom_desc",
                                "Dominance relative to Total Crypto Market Cap",
                            )}>{t("stablecoins_mkt_dom", "Mkt Dom %")}</th
                        >
                        <th>{t("stablecoins_7d_change", "7D")}</th>
                        <th>{t("stablecoins_30d_change", "30D")}</th>
                        <th>{t("stablecoins_90d_change", "90D")}</th>
                    </tr>
                </thead>
                <tbody>
                    {#each growthTableData as item}
                        <tr>
                            <td class="name-cell">
                                <span
                                    class="color-dot"
                                    style="background: {item.color}"
                                ></span>
                                {item.name}
                            </td>
                            <td>${item.mcap?.toFixed(1) || 0}B</td>
                            <td>{item.dom?.toFixed(1) || 0}%</td>
                            <td style="color: #94a3b8; font-size: 0.85rem;"
                                >{item.domTotal?.toFixed(2) || 0}%</td
                            >
                            <td class={getGrowthClass(item.growth7d)}
                                >{formatGrowth(item.growth7d)}</td
                            >
                            <td class={getGrowthClass(item.growth30d)}
                                >{formatGrowth(item.growth30d)}</td
                            >
                            <td class={getGrowthClass(item.growth90d)}
                                >{formatGrowth(item.growth90d)}</td
                            >
                        </tr>
                    {:else}
                        <tr
                            ><td colspan="7" class="no-data"
                                >{t(
                                    "stablecoins_no_growth_data",
                                    "No growth data available",
                                )}</td
                            ></tr
                        >
                    {/each}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Depeg Monitor -->
    <div class="chart-card" bind:this={depegCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_depeg_monitor", "Depeg Monitor")}</h3>
            <button
                class="download-btn"
                title="Download Monitor"
                on:click={() => downloadCardAsImage(depegCard, "depeg_monitor")}
            >
                📥
            </button>
        </div>
        <div class="depeg-content">
            <!-- Current Status -->
            <div class="depeg-current">
                <h4>{t("stablecoins_current_status", "Current Status")}</h4>
                <div class="depeg-grid">
                    {#each currentDepegs as dp}
                        <div class="depeg-item" class:depegged={dp.isDepegged}>
                            <span class="depeg-name" style="color: {dp.color}"
                                >{dp.name}</span
                            >
                            <span class="depeg-price"
                                >${dp.price?.toFixed(4) || "1.0000"}</span
                            >
                            <span
                                class="depeg-deviation"
                                class:positive={dp.deviation > 0}
                                class:negative={dp.deviation < 0}
                            >
                                {dp.deviation >= 0
                                    ? "+"
                                    : ""}{dp.deviation?.toFixed(2) || 0}%
                            </span>
                            <span class="depeg-status">
                                {dp.isDepegged
                                    ? t("stablecoins_depeg_alert", "⚠️ DEPEG")
                                    : t("stablecoins_stable", "✅ Stable")}
                            </span>
                        </div>
                    {:else}
                        <div class="no-data">
                            {t(
                                "stablecoins_no_price_data",
                                "No price data available",
                            )}
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Recent Events -->
            {#if paginatedDepegs.length > 0}
                <div class="depeg-history">
                    <div class="history-header">
                        <h4>
                            {t(
                                "stablecoins_recent_events",
                                "Recent Depeg Events",
                            )}
                        </h4>

                        <!-- Pagination Controls -->
                        {#if totalPages > 1}
                            <div
                                class="pagination-controls"
                                class:light={!darkMode}
                            >
                                <button
                                    class="page-btn"
                                    disabled={currentPage === 1}
                                    on:click={() => setPage(currentPage - 1)}
                                >
                                    {t("pagination_prev", "Prev")}
                                </button>
                                <span class="page-info">
                                    {t("pagination_page", "Page")}
                                    {currentPage} / {totalPages}
                                </span>
                                <button
                                    class="page-btn"
                                    disabled={currentPage === totalPages}
                                    on:click={() => setPage(currentPage + 1)}
                                >
                                    {t("pagination_next", "Next")}
                                </button>
                            </div>
                        {/if}
                    </div>

                    <div class="events-list">
                        {#each paginatedDepegs as event}
                            <div class="event-item">
                                <span class="event-date">{event.date}</span>
                                <span
                                    class="event-stable"
                                    style="color: {stablecoinColors[
                                        event.stablecoin
                                    ]}">{event.stablecoin}</span
                                >
                                <span class="event-price"
                                    >${event.price?.toFixed(4)}</span
                                >
                                <span
                                    class="event-dev"
                                    class:negative={event.deviation_pct < 0}
                                >
                                    {event.deviation_pct?.toFixed(2)}%
                                </span>
                            </div>
                        {/each}
                    </div>
                </div>
            {:else}
                <div class="depeg-history">
                    <h4>
                        {t("stablecoins_recent_events", "Recent Depeg Events")}
                    </h4>
                    <div class="no-data">
                        {t("stablecoins_no_events", "No depeg events detected")}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        margin-bottom: 20px;
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    .tab-header.light {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .header-content h2 {
        margin: 0 0 8px 0;
        font-size: 1.5rem;
        color: var(--text-primary);
    }
    .light .header-content h2 {
        color: #1e293b;
    }
    .description {
        margin: 0;
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    .header-stats {
        display: flex;
        gap: 24px;
    }
    .stat-item {
        text-align: right;
    }
    .stat-label {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #6366f1;
        font-family: "JetBrains Mono", monospace;
    }

    .stablecoins-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
    }
    .chart-card.full-width {
        grid-column: 1 / -1;
    }
    .light .chart-card {
        background: #ffffff;
        border-color: #e2e8f0;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .chart-header h3 {
        margin: 0;
        font-size: 1rem;
        color: var(--text-primary);
    }
    .light .chart-header h3 {
        color: #1e293b;
    }
    .header-controls {
        display: flex;
        gap: 12px;
        align-items: center;
    }

    /* Removing legacy custom dropdown styles - now handled by Dropdown component */

    .download-btn {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .download-btn:hover {
        background: var(--bg-tertiary);
    }

    .chart-content {
        min-height: 300px;
    }

    .no-data {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        color: var(--text-muted);
        font-style: italic;
    }

    /* SFAI Chart Styles */
    .sfai-card .chart-header {
        flex-wrap: wrap;
    }

    .sfai-legend {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 3px;
    }

    .sfai-chart-content {
        min-height: 400px;
    }

    /* Growth Table */
    .table-container {
        overflow-x: auto;
    }
    .growth-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .growth-table th,
    .growth-table td {
        padding: 10px 12px;
        text-align: right;
        border-bottom: 1px solid var(--border-color);
    }
    .growth-table th {
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    .growth-table td {
        color: var(--text-secondary);
        font-family: "JetBrains Mono", monospace;
    }
    .name-cell {
        text-align: left !important;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
    }
    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .positive {
        color: #10b981 !important;
    }
    .negative {
        color: #ef4444 !important;
    }

    /* Depeg Monitor */
    .depeg-content {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    .depeg-current h4 {
        margin: 0 0 12px 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .depeg-history {
        display: flex;
        flex-direction: column;
        gap: 16px;
        margin-top: 10px;
    }

    .history-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .history-header h4 {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .depeg-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
    }
    .depeg-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px;
        background: var(--bg-tertiary);
        border-radius: 8px;
        border: 1px solid transparent;
    }
    .depeg-item.depegged {
        border-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    .depeg-name {
        font-weight: 700;
        font-size: 0.9rem;
    }
    .depeg-price {
        font-family: "JetBrains Mono", monospace;
        font-size: 1rem;
        color: var(--text-primary);
    }
    .depeg-deviation {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.8rem;
    }
    .depeg-status {
        font-size: 0.75rem;
        margin-top: 4px;
    }

    .pagination-controls {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(255, 255, 255, 0.05);
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .pagination-controls.light {
        background: rgba(0, 0, 0, 0.05);
        border-color: rgba(0, 0, 0, 0.1);
    }

    .page-btn {
        background: transparent;
        border: none;
        color: #6366f1;
        font-weight: 600;
        font-size: 0.85rem;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }

    .page-btn:hover:not(:disabled) {
        background: rgba(99, 102, 241, 0.1);
    }

    .page-btn:disabled {
        color: #64748b;
        cursor: not-allowed;
        opacity: 0.5;
    }

    .page-info {
        font-size: 0.85rem;
        color: #94a3b8;
        font-family: var(--font-mono, monospace);
    }

    .pagination-controls.light .page-info {
        color: #64748b;
    }

    .events-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 480px;
        overflow-y: auto;
        padding-right: 4px;
    }
    .event-item {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 8px 12px;
        background: var(--bg-tertiary);
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .event-date {
        color: var(--text-muted);
        font-family: "JetBrains Mono", monospace;
    }
    .event-stable {
        font-weight: 600;
    }
    .event-price,
    .event-dev {
        font-family: "JetBrains Mono", monospace;
    }

    @media (max-width: 1024px) {
        .stablecoins-grid {
            grid-template-columns: 1fr;
        }
        .tab-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 16px;
        }
        .header-stats {
            width: 100%;
            justify-content: flex-start;
        }
    }
</style>
