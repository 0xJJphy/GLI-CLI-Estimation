<script>
    /**
     * RiskModelTab.svelte
     * Displays Credit Liquidity Index (CLI) and risk metrics.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import StressPanel from "../components/StressPanel.svelte";

    // --- Background Shading Helpers ---

    function createZScoreBands(
        darkMode,
        {
            bullishThreshold = 1.0,
            bearishThreshold = -1.0,
            invertColors = false,
        } = {},
    ) {
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.08)"
            : "rgba(16, 185, 129, 0.12)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.08)"
            : "rgba(239, 68, 68, 0.12)";

        const bullishColor = invertColors ? redColor : greenColor;
        const bearishColor = invertColors ? greenColor : redColor;

        return [
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: bullishThreshold,
                y1: 6,
                fillcolor: bullishColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: -6,
                y1: bearishThreshold,
                fillcolor: bearishColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 0,
                line: {
                    color: darkMode
                        ? "rgba(148, 163, 184, 0.3)"
                        : "rgba(100, 116, 139, 0.3)",
                    width: 1,
                    dash: "dot",
                },
                layer: "below",
            },
        ];
    }

    function createRegimeShapes(filteredDates, allDates, allSignals, darkMode) {
        if (
            !filteredDates ||
            !allDates ||
            !allSignals ||
            filteredDates.length === 0
        )
            return [];

        // Find the start and end indices of the filtered range in the original data
        // Optimized: searching for strings is fast, but we can do better if we know they are sorted
        const startIdx = allDates.indexOf(filteredDates[0]);
        const endIdx = allDates.indexOf(
            filteredDates[filteredDates.length - 1],
        );

        if (startIdx === -1 || endIdx === -1) return [];

        const dates = allDates.slice(startIdx, endIdx + 1);
        const signals = allSignals.slice(startIdx, endIdx + 1);

        const shapes = [];
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.12)"
            : "rgba(16, 185, 129, 0.15)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.12)"
            : "rgba(239, 68, 68, 0.15)";

        let currentRegime = null;
        let blockStartIdx = 0;

        // Iterate once and merge identical adjacent regimes
        for (let i = 0; i <= dates.length; i++) {
            const regime = i < dates.length ? signals[i] : null;
            if (regime !== currentRegime || i === dates.length) {
                if (
                    currentRegime === "bullish" ||
                    currentRegime === "bearish"
                ) {
                    const d0 = dates[blockStartIdx];
                    const d1 = dates[Math.min(i, dates.length - 1)];
                    if (d0 && d1) {
                        shapes.push({
                            type: "rect",
                            xref: "x",
                            yref: "paper",
                            x0: d0,
                            x1: d1,
                            y0: 0,
                            y1: 1,
                            fillcolor:
                                currentRegime === "bullish"
                                    ? greenColor
                                    : redColor,
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

    function createPercentileBands(
        darkMode,
        { bullishPct = 70, bearishPct = 30, invert = false } = {},
    ) {
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.10)"
            : "rgba(16, 185, 129, 0.12)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.10)"
            : "rgba(239, 68, 68, 0.12)";

        // For inverted series (VIX, spreads): low = green
        const topColor = invert ? redColor : greenColor;
        const bottomColor = invert ? greenColor : redColor;

        return [
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: bullishPct,
                y1: 100,
                fillcolor: topColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: bearishPct,
                fillcolor: bottomColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 50,
                y1: 50,
                line: {
                    color: darkMode
                        ? "rgba(148, 163, 184, 0.4)"
                        : "rgba(100, 116, 139, 0.4)",
                    width: 1,
                    dash: "dot",
                },
                layer: "below",
            },
        ];
    }

    const PERCENTILE_CONFIG = {
        cli: { bullishPct: 70, bearishPct: 30, invert: false },
        hy_spread: { bullishPct: 30, bearishPct: 70, invert: true },
        ig_spread: { bullishPct: 30, bearishPct: 70, invert: true },
        nfci_credit: { bullishPct: 30, bearishPct: 60, invert: true },
        nfci_risk: { bullishPct: 30, bearishPct: 80, invert: true },
        lending: { bullishPct: 40, bearishPct: 60, invert: true },
        vix: { bullishPct: 25, bearishPct: 90, invert: true },
        move: { bullishPct: 30, bearishPct: 80, invert: true },
        fx_vol: { bullishPct: 30, bearishPct: 70, invert: true },
        tips_real: { bullishPct: 30, bearishPct: 75, invert: true },
    };

    // Unified Props
    export let dashboardData = {};
    export let darkMode = false;
    export let language = "en";
    export let translations = {};

    // Local state for time range selectors (no longer props)
    let cliRange = "ALL";
    let hyRange = "ALL";
    let igRange = "ALL";
    let nfciCreditRange = "ALL";
    let nfciRiskRange = "ALL";
    let lendingRange = "ALL";
    let vixRange = "ALL";
    let moveRange = "ALL";
    let fxVolRange = "ALL";
    let treasury10yRange = "ALL";
    let treasury2yRange = "ALL";
    let treasury30yRange = "ALL";
    let treasury5yRange = "ALL";
    let yieldCurveRange = "ALL";
    let yieldCurve30y10yRange = "ALL";
    let yieldCurve30y2yRange = "ALL";
    let divergenceRange = "ALL";
    let repoStressRange = "1Y"; // Default to 1Y since SRF Rate data starts from 2021-07
    let sofrVolumeRange = "ALL";
    let tipsRange = "ALL";
    let creditSpreadsRange = "ALL";
    let inflationExpectRange = "5Y";
    // New: Stress Indices and Corporate Yields
    let stLouisStressRange = "ALL";
    let kansasCityStressRange = "ALL";
    let baaAaaRange = "ALL";

    // Imports
    import { filterPlotlyData } from "../utils/helpers.js";

    // Satisfy lint for unused language prop
    $: _lang = language;

    // View mode per chart: 'zscore', 'percentile', or 'raw'
    let cliViewMode = "zscore";
    let hyViewMode = "zscore";
    let igViewMode = "zscore";
    let nfciCreditViewMode = "zscore";
    let nfciRiskViewMode = "zscore";
    let lendingViewMode = "zscore";
    let vixViewMode = "zscore";
    let moveViewMode = "zscore";
    let fxVolViewMode = "zscore";
    let treasury10yViewMode = "raw";
    let treasury2yViewMode = "raw";
    let treasury30yViewMode = "raw";
    let treasury5yViewMode = "raw";
    let yieldCurveViewMode = "raw";
    let yieldCurve30y10yViewMode = "raw";
    let yieldCurve30y2yViewMode = "raw";
    let divergenceViewMode = "raw";
    // New: Stress Indices
    let stLouisStressViewMode = "zscore";
    let kansasCityStressViewMode = "zscore";
    let baaAaaViewMode = "raw";
    // New: NFP and JOLTS
    let nfpRange = "5Y";
    let nfpViewMode = "raw";
    let joltsRange = "5Y";
    let joltsViewMode = "raw";
    // New: Credit Spreads and SOFR Volume view modes
    let creditSpreadsViewMode = "raw"; // 'raw', 'zscore', 'percentile'
    let sofrVolumeViewMode = "raw"; // 'raw', 'roc_5d', 'roc_20d'

    // --- Performance Optimization: Cached Indices ---
    import { getCutoffDate } from "../utils/helpers.js";

    $: rangeIndicesCache = (() => {
        const d = dashboardData.dates;
        if (!d || !Array.isArray(d)) return {};
        const ranges = ["1M", "3M", "6M", "1Y", "3Y", "5Y"];

        // Fix: Ignore dates before 1990 to prevent the "1970" x-axis issue
        const minDate = new Date("1990-01-01");
        const allValidIndices = d
            .map((dateStr, i) => ({ date: new Date(dateStr), index: i }))
            .filter((item) => item.date >= minDate)
            .map((item) => item.index);

        const cache = { ALL: allValidIndices };

        ranges.forEach((r) => {
            const cutoff = getCutoffDate(r);
            if (!cutoff) {
                cache[r] = cache.ALL;
                return;
            }
            const indices = [];
            for (let i = 0; i < d.length; i++) {
                const dateObj = new Date(d[i]);
                if (dateObj >= cutoff && dateObj >= minDate) indices.push(i);
            }
            cache[r] = indices;
        });
        return cache;
    })();

    // Optimized filter function using the cache
    function filterWithCache(traceArray, range, autoTrim = true) {
        if (!traceArray || !dashboardData.dates) return traceArray;
        let indices =
            rangeIndicesCache[range] || rangeIndicesCache["ALL"] || [];

        if (range === "ALL" && autoTrim) {
            let firstValidIdx = -1;
            const fullDates = dashboardData.dates;
            for (let i = 0; i < fullDates.length; i++) {
                const hasData = traceArray.some((t) => {
                    const val = t.y ? t.y[i] : undefined;
                    return val !== null && val !== undefined && val !== 0;
                });
                if (hasData) {
                    firstValidIdx = i;
                    break;
                }
            }
            if (firstValidIdx !== -1) {
                indices = indices.filter((idx) => idx >= firstValidIdx);
            }
        }

        if (indices.length === 0) return traceArray;

        return traceArray.map((trace) => ({
            ...trace,
            x: indices.map((i) => dashboardData.dates[i]),
            y: indices.map((i) => (trace.y ? trace.y[i] : undefined)),
        }));
    }

    // --- Internal Reactive Data Processing ---

    let cliPercentileData = [];
    let hyZData = [],
        hyPctData = [],
        hyRawData = [];
    let igZData = [],
        igPctData = [],
        igRawData = [];
    let nfciCreditZData = [],
        nfciCreditPctData = [],
        nfciCreditRawData = [];
    let nfciRiskZData = [],
        nfciRiskPctData = [],
        nfciRiskRawData = [];
    let lendingZData = [],
        lendingPctData = [],
        lendingRawData = [];
    let vixZData = [],
        vixPctData = [],
        vixRawData = [];
    let moveZData = [],
        movePctData = [],
        moveRawData = [];
    let fxVolZData = [],
        fxVolPctData = [],
        fxVolRawData = [];
    let treasury10yData = [],
        treasury10yZData = [],
        treasury10yPctData = [];
    let treasury2yData = [],
        treasury2yZData = [],
        treasury2yPctData = [];
    let divergenceData = [],
        divergenceZData = [],
        divergencePctData = [];
    let repoStressData = [];
    let creditSpreadsData = [];
    let creditIndicators = [];
    let cliChartData = [];
    let cliLayout = {};
    let tipsLayout = {};
    let tipsLayoutWithBands = {};
    let repoStressLayout = {};
    let creditSpreadsLayout = {};
    let tipsRegimeSignals = [];
    let repoRegimeSignals = [];
    let signalsFromMetrics = {};
    let computedTipsSignal = null;
    let tipsData = [];

    // CLI Aggregate
    $: cliData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.cli?.total || [],
                name: translations.chart_cli_z || "CLI Aggregate (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3 },
                fill: "tozeroy",
                fillcolor: "rgba(16, 185, 129, 0.1)",
            },
        ],
        cliRange,
    );

    $: cliPercentileData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.cli?.percentile || [],
                name: translations.chart_cli_pct || "CLI (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3 },
            },
        ],
        cliRange,
    );

    // HY Spread
    $: hyZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.cli_components?.hy_z || [],
                name: translations.chart_hy_z || "HY Spread (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
        ],
        hyRange,
    );

    $: hyPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.hy_spread?.percentile || [],
                name: translations.chart_hy_pct || "HY Spread (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
        ],
        hyRange,
    );

    $: hyRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.hy_spread || [],
                name: translations.chart_hy_raw || "HY Spread (bps)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
        ],
        hyRange,
    );

    // IG Spread
    $: igZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.cli_components?.ig_z || [],
                name: translations.chart_ig_z || "IG Spread (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        igRange,
    );

    $: igPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.ig_spread?.percentile || [],
                name: translations.chart_ig_pct || "IG Spread (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        igRange,
    );

    $: igRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.ig_spread || [],
                name: translations.chart_ig_raw || "IG Spread (bps)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        igRange,
    );

    // NFCI Credit
    $: nfciCreditZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfci_credit?.zscore || [],
                name: "NFCI Credit (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        nfciCreditRange,
    );

    $: nfciCreditPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfci_credit?.percentile || [],
                name: "NFCI Credit (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        nfciCreditRange,
    );

    $: nfciCreditRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.nfci_credit?.raw ||
                    dashboardData.nfci_credit ||
                    [],
                name: "NFCI Credit (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        nfciCreditRange,
    );

    // NFCI Risk
    $: nfciRiskZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfci_risk?.zscore || [],
                name: "NFCI Risk (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 2 },
            },
        ],
        nfciRiskRange,
    );

    $: nfciRiskPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfci_risk?.percentile || [],
                name: "NFCI Risk (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 2 },
            },
        ],
        nfciRiskRange,
    );

    $: nfciRiskRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.nfci_risk?.raw ||
                    dashboardData.nfci_risk ||
                    [],
                name: "NFCI Risk (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 2 },
            },
        ],
        nfciRiskRange,
    );

    // Lending
    $: lendingZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.lending?.zscore || [],
                name: "Lending Standards (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        lendingRange,
    );

    $: lendingPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.lending?.percentile || [],
                name: "Lending Standards (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        lendingRange,
    );

    $: lendingRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.lending?.raw ||
                    dashboardData.lending ||
                    [],
                name: "Lending Standards (% Net Tightening)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        lendingRange,
    );

    // VIX
    $: vixZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.vix?.zscore || [],
                name: translations.chart_vix_z || "VIX (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        vixRange,
    );

    $: vixPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.vix?.percentile || [],
                name: translations.chart_vix_pct || "VIX (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        vixRange,
    );

    $: vixRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.vix?.total || [],
                name: "VIX (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        vixRange,
    );

    // MOVE
    $: moveZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.move?.zscore || [],
                name: "MOVE (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        moveRange,
    );

    $: movePctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.move?.percentile || [],
                name: "MOVE (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        moveRange,
    );

    $: moveRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.move?.total || [],
                name: "MOVE Index",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        moveRange,
    );

    // FX Vol
    $: fxVolZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.fx_vol?.zscore || [],
                name: "DXY Realized Vol (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 2 },
            },
        ],
        fxVolRange,
    );

    $: fxVolPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.fx_vol?.percentile || [],
                name: "DXY Realized Vol (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 2 },
            },
        ],
        fxVolRange,
    );

    $: fxVolRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fx_vol?.total || [],
                name: "DXY Realized Vol (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 2 },
            },
        ],
        fxVolRange,
    );

    // Treasuries
    $: treasury10yData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.treasury_10y?.raw ||
                    dashboardData.treasury_10y ||
                    [],
                name: translations.chart_treasury_10y || "10Y UST Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        treasury10yRange,
    );

    $: treasury10yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_10y?.zscore || [],
                name:
                    translations.chart_treasury_10y_z || "10Y Yield (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        treasury10yRange,
    );

    $: treasury10yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_10y?.percentile || [],
                name:
                    translations.chart_treasury_10y_pct ||
                    "10Y Yield (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        treasury10yRange,
    );

    $: treasury2yData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.treasury_2y?.raw ||
                    dashboardData.treasury_2y ||
                    [],
                name: translations.chart_treasury_2y || "2Y UST Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#60a5fa", width: 2 },
            },
        ],
        treasury2yRange,
    );

    $: treasury2yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_2y?.zscore || [],
                name: translations.chart_treasury_2y_z || "2Y Yield (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#60a5fa", width: 2 },
            },
        ],
        treasury2yRange,
    );

    $: treasury2yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_2y?.percentile || [],
                name:
                    translations.chart_treasury_2y_pct ||
                    "2Y Yield (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#60a5fa", width: 2 },
            },
        ],
        treasury2yRange,
    );

    $: yieldCurveRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.yield_curve || [],
                name: translations.chart_yield_curve || "10Y-2Y Spread (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2.5 },
                fill: "tozeroy",
                fillcolor: "rgba(139, 92, 246, 0.1)",
            },
        ],
        yieldCurveRange,
    );

    $: yieldCurveZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.yield_curve?.zscore || [],
                name:
                    translations.chart_yield_curve_z || "Yield Curve (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2 },
            },
        ],
        yieldCurveRange,
    );

    $: yieldCurvePctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.yield_curve?.percentile || [],
                name: "Yield Curve (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2 },
            },
        ],
        yieldCurveRange,
    );

    // === NEW: 30Y Treasury ===
    $: treasury30yData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.treasury_30y || [],
                name: "30Y UST Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        treasury30yRange,
    );

    $: treasury30yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_30y?.zscore || [],
                name: "30Y Yield (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        treasury30yRange,
    );

    $: treasury30yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_30y?.percentile || [],
                name: "30Y Yield (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        treasury30yRange,
    );

    // === NEW: 30Y-10Y Yield Curve ===
    $: yieldCurve30y10yRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.yield_curve_30y_10y || [],
                name: "30Y-10Y Spread (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ea580c", width: 2.5 },
                fill: "tozeroy",
                fillcolor: "rgba(234, 88, 12, 0.1)",
            },
        ],
        yieldCurve30y10yRange,
    );

    $: yieldCurve30y10yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.yield_curve_30y_10y?.zscore ||
                    [],
                name: "30Y-10Y (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ea580c", width: 2 },
            },
        ],
        yieldCurve30y10yRange,
    );

    $: yieldCurve30y10yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.yield_curve_30y_10y
                        ?.percentile || [],
                name: "30Y-10Y (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ea580c", width: 2 },
            },
        ],
        yieldCurve30y10yRange,
    );

    // === NEW: 30Y-2Y Yield Curve (Full Curve) ===
    $: yieldCurve30y2yRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.yield_curve_30y_2y || [],
                name: "30Y-2Y Spread (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#0891b2", width: 2.5 },
                fill: "tozeroy",
                fillcolor: "rgba(8, 145, 178, 0.1)",
            },
        ],
        yieldCurve30y2yRange,
    );

    $: yieldCurve30y2yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.yield_curve_30y_2y?.zscore ||
                    [],
                name: "30Y-2Y (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#0891b2", width: 2 },
            },
        ],
        yieldCurve30y2yRange,
    );

    $: yieldCurve30y2yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.yield_curve_30y_2y
                        ?.percentile || [],
                name: "30Y-2Y (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#0891b2", width: 2 },
            },
        ],
        yieldCurve30y2yRange,
    );

    // === NEW: St. Louis Financial Stress Index ===
    $: stLouisStressRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.st_louis_stress || [],
                name: translations.chart_stlfsi4_raw || "STLFSI4 (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#7c3aed", width: 2 },
            },
        ],
        stLouisStressRange,
    );

    $: stLouisStressZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.st_louis_stress?.zscore || [],
                name: "STLFSI4 (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#7c3aed", width: 2 },
            },
        ],
        stLouisStressRange,
    );

    $: stLouisStressPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.st_louis_stress?.percentile ||
                    [],
                name: "STLFSI4 (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#7c3aed", width: 2 },
            },
        ],
        stLouisStressRange,
    );

    // === NEW: Kansas City Financial Stress Index ===
    $: kansasCityStressRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.kansas_city_stress || [],
                name: translations.chart_kcfsi_raw || "KCFSI (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#c026d3", width: 2 },
            },
        ],
        kansasCityStressRange,
    );

    $: kansasCityStressZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.kansas_city_stress?.zscore ||
                    [],
                name: "KCFSI (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#c026d3", width: 2 },
            },
        ],
        kansasCityStressRange,
    );

    $: kansasCityStressPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.kansas_city_stress
                        ?.percentile || [],
                name: "KCFSI (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#c026d3", width: 2 },
            },
        ],
        kansasCityStressRange,
    );

    // === NEW: BAA/AAA Corporate Yields ===
    $: baaAaaData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.baa_yield || [],
                name: "BAA Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.aaa_yield || [],
                name: "AAA Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 2 },
                yaxis: "y2",
            },
        ],
        baaAaaRange,
    );

    $: baaAaaSpreadData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.baa_aaa_spread || [],
                name: "BAA-AAA Spread (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2.5 },
                fill: "tozeroy",
                fillcolor: "rgba(245, 158, 11, 0.1)",
            },
        ],
        baaAaaRange,
    );

    // === NEW: NFP Charts ===
    $: nfpRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.nfp_change || [],
                name: "NFP MoM Change (k)",
                type: "bar",
                marker: {
                    color: (dashboardData.fed_forecasts?.nfp_change || []).map(
                        (v) =>
                            v === null || v === undefined
                                ? "rgba(0,0,0,0)"
                                : v >= 0
                                  ? "#10b981"
                                  : "#ef4444",
                    ),
                },
            },
        ],
        nfpRange,
    );

    $: nfpZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfp?.zscore || [],
                name: "NFP (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        nfpRange,
    );

    $: nfpPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.nfp?.percentile || [],
                name: "NFP (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        nfpRange,
    );

    // === NEW: JOLTS Charts ===
    $: joltsRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.fed_forecasts?.jolts || [],
                name: "JOLTS (M)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
                fill: "tozeroy",
                fillcolor: "rgba(16, 185, 129, 0.1)",
            },
        ],
        joltsRange,
    );

    $: joltsZData = filterWithCache(
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
        joltsRange,
    );

    $: joltsPctData = filterWithCache(
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
        joltsRange,
    );

    $: divergenceData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.macro_regime?.cli_gli_divergence || [],
                name: translations.chart_divergence || "CLI-GLI Divergence",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2.5 },
            },
        ],
        divergenceRange,
    );

    $: divergenceZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.cli_gli_divergence?.zscore ||
                    [],
                name:
                    translations.divergence_z_axis ||
                    "CLI-GLI Divergence (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2 },
            },
        ],
        divergenceRange,
    );

    $: divergencePctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.cli_gli_divergence
                        ?.percentile || [],
                name: "CLI-GLI Divergence (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2 },
            },
        ],
        divergenceRange,
    );

    $: repoStressData = filterWithCache(
        [
            // SRF Rate (Ceiling) - red dashed line at top
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.srf_rate || [],
                name: translations.repo_srf_ceiling || "SRF Rate (Ceiling)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 1.5, dash: "dash" },
                hovertemplate: "SRF: %{y:.3f}%<extra></extra>",
            },
            // SOFR (main rate we track) - prominent blue line
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr || [],
                name: "SOFR",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2.5 },
                hovertemplate: "SOFR: %{y:.3f}%<extra></extra>",
            },
            // IORB (Floor) - green dashed line
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.iorb || [],
                name: translations.repo_iorb_floor || "IORB (Floor)",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 1.5, dash: "dash" },
                hovertemplate: "IORB: %{y:.3f}%<extra></extra>",
            },
            // ON RRP Award (Lower Floor) - purple dotted
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.rrp_award || [],
                name: "RRP Award (Lower Floor)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 1, dash: "dot" },
                hovertemplate: "RRP Award: %{y:.3f}%<extra></extra>",
            },
        ],
        repoStressRange,
        true,
    );

    // SRF Usage separate panel data (indicator below main chart)
    $: srfUsageData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.srf_usage || [],
                name: "SRF Usage ($B)",
                type: "bar",
                marker: {
                    color: (dashboardData.repo_stress?.srf_usage || []).map(
                        (v) =>
                            v > 50 ? "#dc2626" : v > 20 ? "#f59e0b" : "#ef4444",
                    ),
                },
                hovertemplate: "SRF Usage: $%{y:.1f}B<extra></extra>",
            },
        ],
        repoStressRange,
        true,
    );

    $: srfUsageLayout = {
        xaxis: {
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            showticklabels: false,
        },
        yaxis: {
            title: "$B",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            rangemode: "tozero",
            fixedrange: true,
        },
        margin: { t: 5, r: 20, b: 20, l: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#fff" : "#000" },
        showlegend: false,
        height: 80,
    };

    // SOFR Volume Chart Data (repo market depth indicator)
    $: sofrVolumeData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr_volume || [],
                name: "SOFR Volume ($B)",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 2 },
                fill: "tozeroy",
                fillcolor: "rgba(6, 182, 212, 0.1)",
            },
        ],
        sofrVolumeRange,
        true,
    );

    $: tipsData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.breakeven || [],
                name: translations.tips_breakeven || "10Y Breakeven (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2.5 },
                yaxis: "y",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.real_rate || [],
                name: translations.tips_real_rate || "10Y Real Rate (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2, dash: "dash" },
                yaxis: "y",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.fwd_5y5y || [],
                name: translations.tips_fwd || "5Y5Y Forward (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
                yaxis: "y",
            },
        ],
        tipsRange,
    );

    $: tipsLayout = {
        title: translations.chart_tips_title || "TIPS Real Yield",
        yaxis: { title: "Breakeven (%)", side: "left" },
        yaxis2: { title: "Real Rate (%)", overlaying: "y", side: "right" },
    };

    $: creditSpreadsData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.hy_spread || [],
                name: "HY Spread (bps)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
                yaxis: "y",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.ig_spread || [],
                name: "IG Spread (bps)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
                yaxis: "y2",
            },
        ],
        creditSpreadsRange,
    );

    // Credit Spreads Z-Score variant
    $: creditSpreadsZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.hy_spread?.zscore || [],
                name: "HY Spread (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.ig_spread?.zscore || [],
                name: "IG Spread (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        creditSpreadsRange,
    );

    // Credit Spreads Percentile variant
    $: creditSpreadsPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.hy_spread?.percentile || [],
                name: "HY Spread (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.ig_spread?.percentile || [],
                name: "IG Spread (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        creditSpreadsRange,
    );

    // SOFR Volume ROC variants
    $: sofrVolumeRoc5dData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr_volume_roc_5d || [],
                name: "SOFR Volume ROC 5D (%)",
                type: "scatter",
                mode: "lines",
                fill: "tozeroy",
                line: { color: "#06b6d4", width: 1.5 },
            },
        ],
        sofrVolumeRange,
        true,
    );

    $: sofrVolumeRoc20dData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr_volume_roc_20d || [],
                name: "SOFR Volume ROC 20D (%)",
                type: "scatter",
                mode: "lines",
                fill: "tozeroy",
                line: { color: "#a855f7", width: 1.5 },
            },
        ],
        sofrVolumeRange,
        true,
    );

    // Inflation Expectations Chart (Cleveland Fed Expected Inflation)
    $: inflationExpectData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_1y || [],
                name:
                    translations.chart_inflation_exp_1y ||
                    "1Y Inflation Exp. (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2.5 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_2y || [],
                name:
                    translations.chart_inflation_exp_2y ||
                    "2Y Inflation Exp. (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#1e3a8a", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_5y || [],
                name:
                    translations.chart_inflation_exp_5y ||
                    "5Y Inflation Exp. (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_10y || [],
                name:
                    translations.chart_inflation_exp_10y ||
                    "10Y Inflation Exp. (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.fwd_5y5y || [],
                name: translations.tips_fwd || "5Y5Y Forward (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2, dash: "dash" },
            },
        ],
        inflationExpectRange,
    );

    // Inflation Expectations Signal (1Y < 2Y = Inverted = Bearish)
    $: inflationExpectSignal = (() => {
        const clev1y = dashboardData.inflation_swaps?.cleveland_1y;
        const clev2y = dashboardData.inflation_swaps?.cleveland_2y;
        if (!clev1y || !clev2y || clev1y.length === 0 || clev2y.length === 0)
            return "neutral";

        const last1y = clev1y[clev1y.length - 1];
        const last2y = clev2y[clev2y.length - 1];

        if (last1y === null || last2y === null) return "neutral";

        // Inverted: 1Y < 2Y by more than 0.05pp = bearish (cooldown imminent)
        if (last1y < last2y - 0.05) return "bearish";
        // Normal: 1Y > 2Y = bullish (rising inflation expectations)
        if (last1y > last2y + 0.05) return "bullish";
        return "neutral";
    })();

    $: inflationExpectInversionSpread = (() => {
        const clev1y = dashboardData.inflation_swaps?.cleveland_1y;
        const clev2y = dashboardData.inflation_swaps?.cleveland_2y;
        if (!clev1y || !clev2y || clev1y.length === 0 || clev2y.length === 0)
            return 0;

        const last1y = clev1y[clev1y.length - 1];
        const last2y = clev2y[clev2y.length - 1];

        if (last1y === null || last2y === null) return 0;
        return last1y - last2y;
    })();

    // Local helper functions (no longer props)
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

    function getLatestROC(rocsObj, window) {
        if (!rocsObj || !rocsObj[window] || !Array.isArray(rocsObj[window]))
            return 0;
        const series = rocsObj[window];
        if (series.length === 0) return 0;
        const val = series[series.length - 1];
        return val === null || val === undefined ? 0 : val;
    }

    // Signal justification text - uses translation keys
    function getSignalReason(signalKey, state) {
        // Map signalKey to translation prefix
        const keyMap = {
            hy_spread: "hy",
            ig_spread: "ig",
            nfci_credit: "nfci_credit",
            nfci_risk: "nfci_risk",
            lending: "lending",
            vix: "vix",
            cli: "cli",
            repo: "repo",
            tips: "tips",
        };
        const prefix = keyMap[signalKey] || signalKey;
        const translationKey = `signal_${prefix}_${state}`;
        return (
            translations[translationKey] ||
            translations[`signal_${prefix}_neutral`] ||
            "—"
        );
    }

    // Z-Score Layouts (using original createZScoreBands from line 20)
    $: hyZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: igZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciCreditZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciRiskZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: lendingZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: vixZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: moveZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: fxVolZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };

    $: creditSpreadsLayout = {
        title: translations.chart_credit_spreads_title || "Credit Spreads",
        yaxis: {
            title: "HY Spread (bps)",
            titlefont: { color: "#ef4444" },
            tickfont: { color: "#ef4444" },
        },
        yaxis2: {
            title: "IG Spread (bps)",
            titlefont: { color: "#38bdf8" },
            tickfont: { color: "#38bdf8" },
            overlaying: "y",
            side: "right",
            autorange: true,
        },
    };

    // Percentile Layouts (when viewMode is 'percentile')
    $: hyLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.hy_spread),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: igLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.ig_spread),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: yieldCurveLayout = {
        title: translations.chart_yield_curve || "Yield Curve (10Y-2Y Spread)",
        xaxis: {
            title: "Date",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            zeroline: false,
        },
        yaxis: {
            title: translations.yield_curve_y || "Spread (%)",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            zeroline: true,
            zerolinecolor: "rgba(255,255,255,0.2)",
        },
        margin: { t: 30, r: 40, b: 40, l: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#fff" : "#000" },
        showlegend: false,
        shapes: [],
    };

    $: tipsLayout = {
        title:
            translations.chart_inflation_exp ||
            "Inflation Expectations (TIPS Market)",
        xaxis: {
            title: "Date",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            zeroline: false,
        },
        yaxis: {
            title: "Yield / Rate (%)",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            zeroline: true,
            side: "left",
        },
        margin: { t: 30, r: 50, b: 40, l: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#fff" : "#000" },
        showlegend: true,
        legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.02,
            xanchor: "right",
            x: 1,
        },
    };

    $: nfciCreditLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.nfci_credit),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: nfciRiskLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.nfci_risk),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: lendingLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.lending),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: vixLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.vix),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: moveLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.move),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: fxVolLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.fx_vol),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    // Raw Layouts (no bands, just autorange y-axis)
    const rawLayoutBase = {
        shapes: [],
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: hyRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "HY Spread (bps)", autorange: true },
    };
    $: igRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "IG Spread (bps)", autorange: true },
    };
    $: nfciCreditRawLayout = {
        ...rawLayoutBase,
        yaxis: {
            title: translations.chart_nfci_credit || "NFCI Credit",
            autorange: true,
        },
    };
    $: nfciRiskRawLayout = {
        ...rawLayoutBase,
        yaxis: {
            title: translations.chart_nfci_risk || "NFCI Risk",
            autorange: true,
        },
    };
    $: lendingRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "Net % Tightening", autorange: true },
    };
    $: vixRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "VIX Level", autorange: true },
    };
    $: moveRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "MOVE Index", autorange: true },
    };
    $: fxVolRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "DXY Realized Vol (%)", autorange: true },
    };

    // CLI Chart - use cliData for Z-score, or cliPercentileData for percentile
    $: cliChartData =
        cliViewMode === "percentile" ? cliPercentileData : cliData;
    $: cliLayout =
        cliViewMode === "percentile"
            ? {
                  shapes: createPercentileBands(
                      darkMode,
                      PERCENTILE_CONFIG.cli,
                  ),
                  yaxis: {
                      title: "Percentile",
                      range: [0, 100],
                      dtick: 25,
                  },
              }
            : {
                  shapes: createZScoreBands(darkMode),
                  yaxis: { title: "CLI Index", dtick: 2.5, autorange: true },
              };

    // TIPS Composite Regime
    $: tipsRegimeSignals = (() => {
        const dates = dashboardData.dates;
        const be = dashboardData.tips?.breakeven;
        const rr = dashboardData.tips?.real_rate;
        const fwd = dashboardData.tips?.fwd_5y5y;
        if (!dates || !be || !rr || !fwd) return [];
        return dates.map((_, i) => {
            if (i < 63) return "neutral";
            const rrNow = rr[i];
            const beNow = be[i];
            const fwdNow = fwd[i];
            const rr3mAgo = rr[i - 63];
            const be3mAgo = be[i - 63];
            const fwd3mAgo = fwd[i - 63];
            if (
                [rrNow, beNow, fwdNow, rr3mAgo, be3mAgo, fwd3mAgo].some(
                    (v) => !Number.isFinite(v),
                )
            )
                return "neutral";
            const rr3mDelta = rrNow - rr3mAgo;
            const be3mDelta = beNow - be3mAgo;
            const fwd3mDelta = fwdNow - fwd3mAgo;
            if (rrNow > 2.0 || rr3mDelta > 0.5) return "bearish";
            if (be3mDelta > 0.2 && rr3mDelta <= 0) return "bullish";
            if (fwd3mDelta < -0.2) return "bearish";
            return "neutral";
        });
    })();
    $: tipsLayoutWithBands = {
        ...tipsLayout,
        shapes: createRegimeShapes(
            tipsData[0]?.x || [],
            dashboardData.dates,
            tipsRegimeSignals,
            darkMode,
        ),
        yaxis: {
            ...tipsLayout.yaxis,
            title: "Yield / Rate (%)",
            dtick: 0.5,
            autorange: true,
        },
        margin: { l: 60, r: 60, t: 20, b: 40 },
    };

    // Computed TIPS signal from frontend data (fallback if backend signal_metrics.tips not populated)
    $: computedTipsSignal = (() => {
        const be = dashboardData.tips?.breakeven;
        const rr = dashboardData.tips?.real_rate;
        if (!be || !rr || be.length < 63) return null;

        const latestBE = be[be.length - 1];
        const latestRR = rr[rr.length - 1];
        const beAvg =
            be.slice(-252).reduce((a, b) => a + b, 0) /
            Math.min(252, be.length);
        const rrAvg =
            rr.slice(-252).reduce((a, b) => a + b, 0) /
            Math.min(252, rr.length);

        const beHigh = latestBE > beAvg * 1.1;
        const rrHigh = latestRR > rrAvg + 0.5;
        const beLow = latestBE < beAvg * 0.9;
        const rrLow = latestRR < rrAvg - 0.3;

        let state = "neutral";
        let reasonKey = "signal_tips_neutral";

        if (beHigh && rrHigh) {
            state = "warning";
            reasonKey = "signal_tips_warning";
        } else if (beHigh && !rrHigh) {
            state = "bullish";
            reasonKey = "signal_tips_bullish";
        } else if (rrHigh && !beHigh) {
            state = "bearish";
            reasonKey = "signal_tips_bearish";
        } else if (beLow && rrLow) {
            state = "neutral";
            reasonKey = "signal_tips_disinflation";
        }

        return { state, value: latestRR, valueBE: latestBE, reasonKey };
    })();

    // Repo Regime - enhanced with corridor bounds
    // SOFR ≈ IORB (within 5bps) = Normal/Bullish (adequate liquidity)
    // SOFR >> IORB (>10bps above) = Bearish (liquidity stress, like Sept 2019)
    // SOFR approaching SRF ceiling (<5bps) = High stress
    // SRF Usage > 0 = Alert (banks using backstop)
    $: repoRegimeSignals = (() => {
        const sofr = dashboardData.repo_stress?.sofr;
        const iorb = dashboardData.repo_stress?.iorb;
        const srfRate = dashboardData.repo_stress?.srf_rate;
        const srfUsage = dashboardData.repo_stress?.srf_usage;
        if (!sofr || !iorb) return [];
        return sofr.map((s, i) => {
            const spreadToFloor = (s - (iorb[i] || 0)) * 100; // bps above IORB
            const spreadToCeiling = srfRate
                ? ((srfRate[i] || 0) - s) * 100
                : 999; // bps below SRF
            const hasUsage = srfUsage && srfUsage[i] > 0;
            if (!Number.isFinite(spreadToFloor)) return "neutral";
            // High stress: approaching ceiling or SRF usage
            if (spreadToCeiling < 5 || hasUsage) return "bearish";
            if (spreadToFloor > 10) return "bearish"; // SOFR >> IORB = liquidity stress
            if (spreadToFloor < -5) return "neutral"; // Excess liquidity
            if (Math.abs(spreadToFloor) <= 5) return "bullish"; // Normal range
            return "neutral";
        });
    })();

    // Latest corridor metrics for display
    $: latestSofrToFloor = (() => {
        const arr = dashboardData.repo_stress?.sofr_to_floor;
        return arr && arr.length > 0 ? arr[arr.length - 1] || 0 : 0;
    })();
    $: latestSofrToCeiling = (() => {
        const arr = dashboardData.repo_stress?.sofr_to_ceiling;
        return arr && arr.length > 0 ? arr[arr.length - 1] || 0 : 0;
    })();
    $: latestSrfUsage = (() => {
        const arr = dashboardData.repo_stress?.srf_usage;
        return arr && arr.length > 0 ? arr[arr.length - 1] || 0 : 0;
    })();
    $: corridorStressLevel = (() => {
        if (latestSrfUsage > 0 || latestSofrToCeiling < 5) return "HIGH";
        if (latestSofrToFloor > 10 || latestSofrToCeiling < 10)
            return "ELEVATED";
        return "NORMAL";
    })();
    $: corridorStressColor =
        corridorStressLevel === "HIGH"
            ? "#ef4444"
            : corridorStressLevel === "ELEVATED"
              ? "#f59e0b"
              : "#22c55e";

    $: repoStressLayout = {
        title: "",
        xaxis: {
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
        },
        yaxis: {
            title: "Rate (%)",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            tickformat: ".2f",
        },
        margin: { t: 10, r: 20, b: 30, l: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#fff" : "#000" },
        showlegend: true,
        legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.02,
            xanchor: "center",
            x: 0.5,
        },
        shapes: [],
    };

    // Credit indicators configuration - each chart has independent viewMode
    $: creditIndicators = [
        {
            id: "hy",
            name: translations.credit_hy_name || "HY Spread Contrast",
            signalKey: "hy_spread",
            desc:
                translations.credit_hy_desc ||
                "High Yield spread vs Treasury. Higher = Risk-off, Lower = Risk-on.",
            data:
                hyViewMode === "raw"
                    ? hyRawData
                    : hyViewMode === "percentile"
                      ? hyPctData
                      : hyZData,
            range: hyRange,
            bank: "HY_SPREAD",
            layout:
                hyViewMode === "raw"
                    ? hyRawLayout
                    : hyViewMode === "percentile"
                      ? hyLayout
                      : hyZLayout,
            viewMode: hyViewMode,
            setViewMode: (m) => (hyViewMode = m),
        },
        {
            id: "ig",
            name: translations.credit_ig_name || "IG Spread Contrast",
            signalKey: "ig_spread",
            desc:
                translations.credit_ig_desc ||
                "Investment Grade spread vs Treasury. Higher = Stress, Lower = Calm.",
            data:
                igViewMode === "raw"
                    ? igRawData
                    : igViewMode === "percentile"
                      ? igPctData
                      : igZData,
            range: igRange,
            bank: "IG_SPREAD",
            layout:
                igViewMode === "raw"
                    ? igRawLayout
                    : igViewMode === "percentile"
                      ? igLayout
                      : igZLayout,
            viewMode: igViewMode,
            setViewMode: (m) => (igViewMode = m),
        },
        {
            id: "nfci_credit",
            name:
                translations.credit_nfci_credit_name || "NFCI Credit Contrast",
            signalKey: "nfci_credit",
            desc:
                translations.credit_nfci_credit_desc ||
                "Fed Chicago NFCI Credit subindex. Positive = Tighter, Negative = Easier.",
            data:
                nfciCreditViewMode === "raw"
                    ? nfciCreditRawData
                    : nfciCreditViewMode === "percentile"
                      ? nfciCreditPctData
                      : nfciCreditZData,
            range: nfciCreditRange,
            bank: "NFCI_CREDIT",
            layout:
                nfciCreditViewMode === "raw"
                    ? nfciCreditRawLayout
                    : nfciCreditViewMode === "percentile"
                      ? nfciCreditLayout
                      : nfciCreditZLayout,
            viewMode: nfciCreditViewMode,
            setViewMode: (m) => (nfciCreditViewMode = m),
        },
        {
            id: "nfci_risk",
            name: translations.credit_nfci_risk_name || "NFCI Risk Contrast",
            signalKey: "nfci_risk",
            desc:
                translations.credit_nfci_risk_desc ||
                "Fed Chicago NFCI Risk subindex. Positive = Higher risk, Negative = Lower risk.",
            data:
                nfciRiskViewMode === "raw"
                    ? nfciRiskRawData
                    : nfciRiskViewMode === "percentile"
                      ? nfciRiskPctData
                      : nfciRiskZData,
            range: nfciRiskRange,
            bank: "NFCI_RISK",
            layout:
                nfciRiskViewMode === "raw"
                    ? nfciRiskRawLayout
                    : nfciRiskViewMode === "percentile"
                      ? nfciRiskLayout
                      : nfciRiskZLayout,
            viewMode: nfciRiskViewMode,
            setViewMode: (m) => (nfciRiskViewMode = m),
        },
        {
            id: "lending",
            name:
                translations.credit_lending_name ||
                "Lending Standards Contrast",
            signalKey: "lending",
            desc:
                translations.credit_lending_desc ||
                "Fed SLOOS survey. Positive = Tighter lending, Negative = Easier lending.",
            data:
                lendingViewMode === "raw"
                    ? lendingRawData
                    : lendingViewMode === "percentile"
                      ? lendingPctData
                      : lendingZData,
            range: lendingRange,
            bank: "LENDING_STD",
            layout:
                lendingViewMode === "raw"
                    ? lendingRawLayout
                    : lendingViewMode === "percentile"
                      ? lendingLayout
                      : lendingZLayout,
            viewMode: lendingViewMode,
            setViewMode: (m) => (lendingViewMode = m),
        },
        {
            id: "vix",
            name: translations.credit_vix_name || "VIX Contrast",
            signalKey: "vix",
            desc:
                translations.credit_vix_desc ||
                "CBOE Volatility Index. Higher = Fear/Stress, Lower = Complacency.",
            data:
                vixViewMode === "raw"
                    ? vixRawData
                    : vixViewMode === "percentile"
                      ? vixPctData
                      : vixZData,
            range: vixRange,
            bank: "VIX",
            layout:
                vixViewMode === "raw"
                    ? vixRawLayout
                    : vixViewMode === "percentile"
                      ? vixLayout
                      : vixZLayout,
            viewMode: vixViewMode,
            setViewMode: (m) => (vixViewMode = m),
        },
        {
            id: "move",
            name: translations.indicator_move_name || "MOVE Index Contrast",
            signalKey: "move",
            desc:
                translations.indicator_move_desc ||
                "ICE BofA MOVE Index. Measures implied bond volatility. Higher = Stress.",
            data:
                moveViewMode === "raw"
                    ? moveRawData
                    : moveViewMode === "percentile"
                      ? movePctData
                      : moveZData,
            range: moveRange,
            bank: "MOVE",
            layout:
                moveViewMode === "raw"
                    ? moveRawLayout
                    : moveViewMode === "percentile"
                      ? moveLayout
                      : moveZLayout,
            viewMode: moveViewMode,
            setViewMode: (m) => (moveViewMode = m),
        },
        {
            id: "fx_vol",
            name:
                translations.indicator_fx_vol_name || "DXY Realized Volatility",
            signalKey: "fx_vol",
            desc:
                translations.indicator_fx_vol_desc ||
                "21-day realized volatility of the US Dollar Index. Measures currency market stress.",
            data:
                fxVolViewMode === "raw"
                    ? fxVolRawData
                    : fxVolViewMode === "percentile"
                      ? fxVolPctData
                      : fxVolZData,
            range: fxVolRange,
            bank: "FX_VOL",
            layout:
                fxVolViewMode === "raw"
                    ? fxVolRawLayout
                    : fxVolViewMode === "percentile"
                      ? fxVolLayout
                      : fxVolZLayout,
            viewMode: fxVolViewMode,
            setViewMode: (m) => (fxVolViewMode = m),
        },
    ];

    function handleRangeChange(id, range) {
        if (id === "hy") hyRange = range;
        else if (id === "ig") igRange = range;
        else if (id === "nfci_credit") nfciCreditRange = range;
        else if (id === "nfci_risk") nfciRiskRange = range;
        else if (id === "lending") lendingRange = range;
        else if (id === "vix") vixRange = range;
        else if (id === "move") moveRange = range;
        else if (id === "fx_vol") fxVolRange = range;
    }

    // Unified signal derived from signal_metrics
    $: signalsFromMetrics = dashboardData.signal_metrics || {};

    const signalConfig = [
        { id: "cli", label: "CLI Stance" },
        { id: "hy", label: "HY Momentum" },
        { id: "ig", label: "IG Momentum" },
        { id: "nfci_credit", label: "Credit (NFCI)" },
        { id: "nfci_risk", label: "Risk (NFCI)" },
        { id: "lending", label: "Lending (SLOOS)" },
        { id: "vix", label: "Volatility (VIX)" },
        { id: "move", label: "MOVE Index" },
        { id: "fx_vol", label: "FX Volatility" },
        { id: "tips", label: "Macro (TIPS)" },
        { id: "repo", label: "Liquidity (SOFR)" },
    ];

    function getStatusLabel(state) {
        if (!state) return translations.status_neutral || "NEUTRAL";
        const key = `status_${state.toLowerCase()}`;
        return translations[key] || state.toUpperCase();
    }

    $: bullCount = Object.values(signalsFromMetrics).filter(
        (s) => s.latest?.state === "bullish",
    ).length;
    $: bearCount = Object.values(signalsFromMetrics).filter(
        (s) => s.latest?.state === "bearish",
    ).length;
    $: aggregateState =
        bullCount > bearCount + 1
            ? "bullish"
            : bearCount > bullCount + 1
              ? "bearish"
              : "neutral";

    // Stress Analysis reactive variable
    $: stressAnalysis = dashboardData.stress_analysis || {};
</script>

<!-- Header with Aggregate Stance & View Mode Toggle -->
<div class="risk-header-summary">
    <div class="regime-badge bg-{aggregateState}">
        <span style="font-size: 1.2rem;"
            >{aggregateState === "bullish"
                ? "🚀"
                : aggregateState === "bearish"
                  ? "⚠️"
                  : "⚖️"}</span
        >
        {getStatusLabel(aggregateState)}
        {translations.risk_stance || "STANCE"}
    </div>
    <div class="stance-details">
        {bullCount}
        {translations.risk_bullish || "Bullish"} | {bearCount}
        {translations.risk_bearish || "Bearish"} | {signalConfig.length}
        {translations.risk_factors || "Factors"}
    </div>
</div>

<!-- Market Stress Dashboard -->
<div class="stress-dashboard-row" style="margin-bottom: 25px;">
    <StressPanel {stressAnalysis} {darkMode} {translations} />
</div>

<div class="main-charts">
    <div class="grid-2">
        <!-- Inflation Expectations (Swap Rates / Cleveland Fed) Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_inflation_swap_title ||
                        "USD Inflation Swap Rates (Cleveland Fed)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={inflationExpectRange}
                        onRangeChange={(r) => (inflationExpectRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("INFLATION_EXPECT_1Y")}</span
                    >
                </div>
            </div>
            <div
                class="chart-legend"
                style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;"
            >
                <span class="legend-item">
                    <span class="legend-dot" style="background: #3b82f6"></span>
                    <span class="legend-label"
                        >{translations.legend_1y || "1Y"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #1e3a8a"></span>
                    <span class="legend-label"
                        >{translations.legend_2y || "2Y"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #f59e0b"></span>
                    <span class="legend-label"
                        >{translations.legend_5y || "5Y"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #ef4444"></span>
                    <span class="legend-label"
                        >{translations.legend_10y || "10Y"}</span
                    >
                </span>
                <span class="legend-item">
                    <span
                        class="legend-dot"
                        style="background: #10b981; border: 1px dashed rgba(255,255,255,0.5)"
                    ></span>
                    <span class="legend-label"
                        >{translations.tips_fwd || "5Y5Y Fwd"}</span
                    >
                </span>
            </div>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={inflationExpectData}
                    layout={{
                        yaxis: {
                            title: translations.inflation_rate_y || "Rate (%)",
                            autorange: true,
                        },
                        margin: { l: 50, r: 20, t: 10, b: 40 },
                        showlegend: false,
                    }}
                />
            </div>

            <!-- Inflation Inversion Signal -->
            <div
                class="metrics-section"
                style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
            >
                <div
                    class="signal-item"
                    style="background: rgba(0,0,0,0.15); border: none;"
                >
                    <div class="signal-label">
                        {translations.inflation_curve_signal ||
                            "Inflation Curve Signal (1Y-2Y)"}
                    </div>
                    <div class="signal-status text-{inflationExpectSignal}">
                        <span class="signal-dot"></span>
                        {#if inflationExpectSignal === "bearish"}
                            🚫 {translations.signal_inverted ||
                                "INVERTED (Bearish)"}
                        {:else if inflationExpectSignal === "bullish"}
                            🐂 {translations.signal_normal ||
                                "NORMAL (Bullish)"}
                        {:else}
                            ⚖️ {translations.signal_neutral || "NEUTRAL"}
                        {/if}
                    </div>
                    <div class="signal-value">
                        {translations.spread_1y_2y || "Spread (1Y-2Y)"}:
                        <b>{inflationExpectInversionSpread.toFixed(2)}%</b>
                    </div>
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                    >
                        {#if inflationExpectSignal === "bearish"}
                            {translations.inflation_inverted_desc ||
                                "1Y Swap below 2Y Swap: Market expects imminent cooldown/disinflation."}
                        {:else if inflationExpectSignal === "bullish"}
                            {translations.inflation_normal_desc ||
                                "1Y Swap above 2Y Swap: Market expects near-term inflation to remain elevated."}
                        {:else}
                            {translations.inflation_neutral_desc ||
                                "Curve is flat or mixed."}
                        {/if}
                    </div>
                </div>
            </div>
        </div>

        <!-- TIPS / Inflation Expectations Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_inflation_exp ||
                        "Inflation Expectations (TIPS Market)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={tipsRange}
                        onRangeChange={(r) => (tipsRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("TIPS_BREAKEVEN")}</span
                    >
                </div>
            </div>
            <div class="chart-legend">
                <span class="legend-item">
                    <span class="legend-dot" style="background: #f59e0b"></span>
                    <span class="legend-label"
                        >{translations.tips_breakeven || "Breakeven"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_be_desc ||
                            "Inflation expectations"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #3b82f6"></span>
                    <span class="legend-label"
                        >{translations.tips_real_rate || "Real Rate"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_rr_desc || "Cost of money"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #10b981"></span>
                    <span class="legend-label"
                        >{translations.tips_fwd || "5Y5Y Forward"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_fwd_desc ||
                            "Long-term anchor"}</span
                    >
                </span>
            </div>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={tipsData}
                    layout={tipsLayoutWithBands}
                />
            </div>

            {#if signalsFromMetrics.tips?.latest}
                {@const s = signalsFromMetrics.tips.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            {translations.repo_value || "Value"}: {s.value?.toFixed(
                                2,
                            ) ?? "N/A"} | {translations.percentile ||
                                "Percentile"}: P{s.percentile?.toFixed(0) ??
                                "N/A"}
                        </div>
                    </div>
                </div>
            {:else if computedTipsSignal}
                {@const s = computedTipsSignal}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {s.state === "warning"
                                ? "⚠️ WARNING"
                                : getStatusLabel(s.state)}
                        </div>
                        <div
                            class="signal-value"
                            style="display: flex; gap: 12px;"
                        >
                            <span>BE: {s.valueBE?.toFixed(2) ?? "N/A"}%</span>
                            <span>RR: {s.value?.toFixed(2) ?? "N/A"}%</span>
                        </div>
                        <div
                            class="signal-reason"
                            style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                        >
                            {translations[s.reasonKey] || s.reasonKey}
                        </div>
                    </div>
                </div>
            {:else}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-neutral">
                            <span class="signal-dot"></span>
                            {translations.refresh_data || "Loading..."}
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- CLI Aggregate Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_cli_title ||
                        "Credit Liquidity Index (CLI Aggregate)"}
                </h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={cliViewMode === "zscore"}
                            on:click={() => (cliViewMode = "zscore")}>Z</button
                        >
                        <button
                            class:active={cliViewMode === "percentile"}
                            on:click={() => (cliViewMode = "percentile")}
                            >%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={cliRange}
                        onRangeChange={(r) => (cliRange = r)}
                    />
                    <span class="last-date"
                        >Last Data: {getLastDate("NFCI")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.cli ||
                    "Aggregates credit conditions, volatility, and lending."}
                {cliViewMode === "percentile"
                    ? translations.cli_desc_ext ||
                      "↑ CLI = Easier credit (bullish) ↓ Contraction = Tighter (bearish)"
                    : ""}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cliChartData} layout={cliLayout} />
            </div>

            <!-- Signal Box -->
            {#if dashboardData.signal_metrics?.cli?.latest}
                {@const s = dashboardData.signal_metrics.cli.latest}
                <div class="signal-box">
                    <div class="signal-header">
                        {translations.cli_stance || "CLI STANCE"}
                    </div>
                    <div class="signal-badge {s.state}">
                        {s.state === "bullish"
                            ? "🟢"
                            : s.state === "bearish"
                              ? "🔴"
                              : "⚪"}
                        {getStatusLabel(s.state)}
                    </div>
                    <div class="signal-details">
                        {translations.percentile || "Percentile"}: {s.percentile?.toFixed(
                            0,
                        ) ?? "N/A"}
                        <span class="signal-hint">
                            ({s.percentile >= 70
                                ? translations.cli_top_30 || "Top 30%"
                                : s.percentile <= 30
                                  ? translations.cli_bottom_30 || "Bottom 30%"
                                  : translations.cli_mid_range ||
                                    "Middle range"})
                        </span>
                    </div>
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                    >
                        {getSignalReason("cli", s.state)}
                    </div>
                </div>
            {/if}
        </div>

        <!-- CLI-GLI Divergence Analysis (Macro Coupling) -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_divergence ||
                        "CLI-GLI Divergence (Macro Coupling)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={divergenceViewMode === "raw"}
                            on:click={() => (divergenceViewMode = "raw")}
                            >{translations.view_raw || "Raw"}</button
                        >
                        <button
                            class:active={divergenceViewMode === "zscore"}
                            on:click={() => (divergenceViewMode = "zscore")}
                            >{translations.view_zscore || "Z-Score"}</button
                        >
                        <button
                            class:active={divergenceViewMode === "percentile"}
                            on:click={() => (divergenceViewMode = "percentile")}
                            >{translations.view_percentile ||
                                "Percentile"}</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={divergenceRange}
                        onRangeChange={(r) => (divergenceRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {@html translations.divergence_desc}
            </p>
            <div
                class="divergence-guide"
                style="font-size: 11px; margin: 10px 0 20px 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; opacity: 0.9;"
            >
                <div
                    style="border-left: 3px solid #10b981; padding: 2px 0 2px 10px; line-height: 1.4;"
                >
                    <b style="color: #10b981;"
                        >{translations.div_guide_eq.split(":")[0]}:</b
                    >
                    {translations.div_guide_eq.split(":")[1] || ""}
                </div>
                <div
                    style="border-left: 3px solid #ef4444; padding: 2px 0 2px 10px; line-height: 1.4;"
                >
                    <b style="color: #ef4444;"
                        >{translations.div_guide_trap.split(":")[0]}:</b
                    >
                    {translations.div_guide_trap.split(":")[1] || ""}
                </div>
                <div
                    style="border-left: 3px solid #f59e0b; padding: 2px 0 2px 10px; line-height: 1.4;"
                >
                    <b style="color: #f59e0b;"
                        >{translations.div_guide_excess.split(":")[0]}:</b
                    >
                    {translations.div_guide_excess.split(":")[1] || ""}
                </div>
            </div>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={divergenceViewMode === "zscore"
                        ? divergenceZData
                        : divergenceViewMode === "percentile"
                          ? divergencePctData
                          : divergenceData}
                    layout={{
                        yaxis: {
                            title:
                                divergenceViewMode === "zscore"
                                    ? "Z-Score"
                                    : divergenceViewMode === "percentile"
                                      ? "Percentile (%)"
                                      : "Divergence (Z)",
                            zeroline: true,
                            zerolinecolor: darkMode ? "#ffffff" : "#000000",
                            range:
                                divergenceViewMode === "zscore"
                                    ? [-4, 4]
                                    : divergenceViewMode === "percentile"
                                      ? [0, 100]
                                      : undefined,
                        },
                        shapes:
                            divergenceViewMode === "zscore"
                                ? [
                                      {
                                          type: "line",
                                          xref: "paper",
                                          yref: "y",
                                          x0: 0,
                                          x1: 1,
                                          y0: 1.5,
                                          y1: 1.5,
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
                                          y0: -1.5,
                                          y1: -1.5,
                                          line: {
                                              color: "rgba(239, 68, 68, 0.5)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                  ]
                                : divergenceViewMode === "percentile"
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
                    >{translations.latest_value || "Latest Value"}:
                    <b
                        >{getLatestValue(
                            dashboardData.macro_regime?.cli_gli_divergence,
                        )?.toFixed(2) ?? "—"}</b
                    ></span
                >
                {#if divergenceViewMode !== "raw"}
                    <span class="view-mode-badge">
                        {divergenceViewMode.toUpperCase()}:
                        <b
                            >{getLatestValue(
                                dashboardData.signal_metrics
                                    ?.cli_gli_divergence?.[divergenceViewMode],
                            )?.toFixed(2) ?? "—"}{divergenceViewMode ===
                            "percentile"
                                ? "%"
                                : ""}</b
                        >
                    </span>
                {/if}
            </div>
            {#if (getLatestValue(dashboardData.macro_regime?.cli_gli_divergence) ?? 0) < -1}
                <div
                    class="signal-box warning"
                    style="margin-top: 15px; border-left: 4px solid #ef4444; background: rgba(239, 68, 68, 0.1); padding: 12px;"
                >
                    <div
                        style="font-weight: 700; color: #ef4444; margin-bottom: 4px;"
                    >
                        {translations.stat_liq_trap_title}
                    </div>
                    <div
                        style="font-size: 12px; opacity: 0.9; line-height: 1.4;"
                    >
                        {translations.stat_liq_trap_desc}
                    </div>
                </div>
            {/if}
        </div>

        <!-- Repo Stress Chart (Fed Rate Corridor) -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_repo_corridor ||
                        "Fed Rate Corridor (SOFR vs Bounds)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={repoStressRange}
                        onRangeChange={(r) => (repoStressRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("SOFR")}</span
                    >
                </div>
            </div>

            <!-- Corridor Metrics Header -->
            <div
                class="corridor-metrics"
                style="display: flex; gap: 15px; margin-bottom: 12px; flex-wrap: wrap;"
            >
                <div
                    class="metric-box"
                    style="background: {darkMode
                        ? 'rgba(255,255,255,0.05)'
                        : 'rgba(0,0,0,0.03)'}; padding: 8px 12px; border-radius: 6px;"
                >
                    <span style="font-size: 11px; opacity: 0.7;"
                        >{translations.sofr_iorb_spread ||
                            "SOFR-IORB Spread"}</span
                    >
                    <div
                        style="font-size: 16px; font-weight: 600; color: {corridorStressColor};"
                    >
                        {latestSofrToFloor.toFixed(1)} bps
                    </div>
                </div>
                <div
                    class="metric-box"
                    style="background: {darkMode
                        ? 'rgba(255,255,255,0.05)'
                        : 'rgba(0,0,0,0.03)'}; padding: 8px 12px; border-radius: 6px;"
                >
                    <span style="font-size: 11px; opacity: 0.7;"
                        >{translations.gap_to_ceiling || "Gap to Ceiling"}</span
                    >
                    <div style="font-size: 16px; font-weight: 600;">
                        {latestSofrToCeiling.toFixed(1)} bps
                    </div>
                </div>
                <div
                    class="metric-box"
                    style="background: {darkMode
                        ? 'rgba(255,255,255,0.05)'
                        : 'rgba(0,0,0,0.03)'}; padding: 8px 12px; border-radius: 6px;"
                >
                    <span style="font-size: 11px; opacity: 0.7;"
                        >{translations.status_label || "Status"}</span
                    >
                    <div
                        style="font-size: 14px; font-weight: 600; color: {corridorStressColor};"
                    >
                        {corridorStressLevel}
                    </div>
                </div>
                {#if latestSrfUsage > 0}
                    <div
                        class="metric-box"
                        style="background: rgba(239, 68, 68, 0.1); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #ef4444;"
                    >
                        <span style="font-size: 11px; opacity: 0.7;"
                            >⚠️ SRF Usage</span
                        >
                        <div
                            style="font-size: 16px; font-weight: 600; color: #ef4444;"
                        >
                            ${latestSrfUsage.toFixed(1)}B
                        </div>
                    </div>
                {/if}
            </div>

            <p class="chart-description">
                {translations.repo_corridor_desc ||
                    "SOFR should trade between IORB (floor) and SRF Rate (ceiling). Approaching ceiling or SRF usage signals funding stress."}
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={repoStressData}
                    layout={repoStressLayout}
                />
            </div>

            <!-- SRF Usage Indicator Panel (separate from main chart) -->
            <div
                class="srf-usage-panel"
                style="margin-top: 0; border-top: 1px solid {darkMode
                    ? 'rgba(255,255,255,0.1)'
                    : 'rgba(0,0,0,0.1)'};"
            >
                <div
                    style="display: flex; align-items: center; gap: 8px; padding: 4px 0;"
                >
                    <span
                        style="font-size: 11px; font-weight: 600; color: #ef4444;"
                        >SRF Usage ($B)</span
                    >
                    <span style="font-size: 10px; opacity: 0.6;"
                        >Fed backstop operations</span
                    >
                </div>
                <div style="height: 60px;">
                    <Chart
                        {darkMode}
                        data={srfUsageData}
                        layout={srfUsageLayout}
                    />
                </div>
            </div>

            <!-- Corridor Legend -->
            <div
                class="corridor-legend"
                style="display: flex; gap: 15px; margin-top: 10px; font-size: 11px; opacity: 0.8; flex-wrap: wrap;"
            >
                <span
                    ><span style="color: #ef4444;">━━</span> SRF Rate: Fed lending
                    ceiling</span
                >
                <span
                    ><span style="color: #3b82f6; font-weight: bold;">━━</span> SOFR:
                    Market rate</span
                >
                <span
                    ><span style="color: #22c55e;">━━</span> IORB: Fed deposit floor</span
                >
            </div>

            <!-- Compact Metrics Table -->
            <div
                class="metrics-section"
                style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;"
            >
                <div class="metrics-table-container">
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>{translations.repo_rate || "Rate"}</th>
                                <th>{translations.repo_value || "Value"}</th>
                                <th
                                    >{translations.repo_spread_sig ||
                                        "Spread/Signal"}</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color: #ef4444; font-weight: 600;"
                                    >SRF (Ceiling)</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.srf_rate,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td
                                    rowspan="4"
                                    style="vertical-align: middle; text-align: center; background: rgba(0,0,0,0.1); border-radius: 8px;"
                                >
                                    <div
                                        style="font-weight: 800; font-size: 1.1rem; color: {corridorStressColor};"
                                    >
                                        {latestSofrToFloor.toFixed(1)} bps
                                    </div>
                                    <div style="font-size: 12px; opacity: 0.7;">
                                        SOFR-IORB
                                    </div>
                                    <div
                                        style="font-size: 14px; margin-top: 4px; color: {corridorStressColor};"
                                    >
                                        {#if corridorStressLevel === "NORMAL"}
                                            ✅ OK
                                        {:else if corridorStressLevel === "ELEVATED"}
                                            ⚠️ ELEVATED
                                        {:else}
                                            🚨 STRESS
                                        {/if}
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="color: #3b82f6; font-weight: 600;"
                                    >SOFR</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                            </tr>
                            <tr>
                                <td style="color: #22c55e; font-weight: 600;"
                                    >IORB (Floor)</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.iorb,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                            </tr>
                            <tr>
                                <td style="color: #8b5cf6; font-weight: 600;"
                                    >RRP Award</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress
                                                ?.rrp_award,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- SOFR Volume Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_sofr_volume ||
                        "Repo Market Depth (SOFR Volume)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={sofrVolumeViewMode === "raw"}
                            on:click={() => (sofrVolumeViewMode = "raw")}
                            >Raw</button
                        >
                        <button
                            class:active={sofrVolumeViewMode === "roc_5d"}
                            on:click={() => (sofrVolumeViewMode = "roc_5d")}
                            title="5-Day Rate of Change">ROC 5d</button
                        >
                        <button
                            class:active={sofrVolumeViewMode === "roc_20d"}
                            on:click={() => (sofrVolumeViewMode = "roc_20d")}
                            title="20-Day Rate of Change">ROC 20d</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={sofrVolumeRange}
                        onRangeChange={(r) => (sofrVolumeRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("SOFR_VOLUME")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {sofrVolumeViewMode === "raw"
                    ? translations.sofr_volume_desc ||
                      "SOFR transaction volume measures repo market depth. Falling volume = early warning of dysfunction."
                    : "Rate of Change shows momentum. Sharp drops (<-10%) may signal stress."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={sofrVolumeViewMode === "roc_5d"
                        ? sofrVolumeRoc5dData
                        : sofrVolumeViewMode === "roc_20d"
                          ? sofrVolumeRoc20dData
                          : sofrVolumeData}
                    layout={sofrVolumeViewMode === "raw"
                        ? { yaxis: { title: "SOFR Volume ($B)" } }
                        : {
                              yaxis: { title: "ROC (%)" },
                              shapes: [
                                  {
                                      type: "line",
                                      x0: 0,
                                      x1: 1,
                                      xref: "paper",
                                      y0: 0,
                                      y1: 0,
                                      line: {
                                          color: "rgba(255,255,255,0.3)",
                                          width: 1,
                                          dash: "dash",
                                      },
                                  },
                                  {
                                      type: "line",
                                      x0: 0,
                                      x1: 1,
                                      xref: "paper",
                                      y0: -10,
                                      y1: -10,
                                      line: {
                                          color: "rgba(239, 68, 68, 0.5)",
                                          width: 1,
                                          dash: "dash",
                                      },
                                  },
                              ],
                          }}
                />
            </div>

            <!-- SOFR Volume Metrics -->
            <div
                class="metrics-section"
                style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;"
            >
                <div class="metrics-table-container">
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>{translations.indicator || "Indicator"}</th>
                                <th>{translations.repo_value || "Value"}</th>
                                <th>{translations.signal_status || "Status"}</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color: #06b6d4; font-weight: 600;"
                                    >SOFR Volume</td
                                >
                                <td
                                    >${(
                                        getLatestValue(
                                            dashboardData.repo_stress
                                                ?.sofr_volume,
                                        ) ?? 0
                                    ).toFixed(1)}B</td
                                >
                                <td>
                                    {#if getLatestValue(dashboardData.repo_stress?.sofr_volume) > 1000}
                                        ✅ {translations.status_ok || "DEEP"}
                                    {:else if getLatestValue(dashboardData.repo_stress?.sofr_volume) > 500}
                                        🔶 {translations.status_neutral ||
                                            "MODERATE"}
                                    {:else}
                                        ⚠️ {translations.status_stress ||
                                            "THIN"}
                                    {/if}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Treasury 10Y Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_treasury_10y ||
                        "10-Year Treasury Yield"}
                </h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={treasury10yViewMode === "zscore"}
                            on:click={() => (treasury10yViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={treasury10yViewMode === "percentile"}
                            on:click={() =>
                                (treasury10yViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                        <button
                            class:active={treasury10yViewMode === "raw"}
                            on:click={() => (treasury10yViewMode = "raw")}
                            title="Raw Values">📊</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={treasury10yRange}
                        onRangeChange={(r) => (treasury10yRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("TREASURY_10Y_YIELD")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.treasury_10y_desc ||
                    "10-Year Treasury Constant Maturity Yield. Key benchmark rate."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={treasury10yViewMode === "raw"
                        ? treasury10yData
                        : treasury10yViewMode === "percentile"
                          ? treasury10yPctData
                          : treasury10yZData}
                    layout={treasury10yViewMode === "raw"
                        ? {
                              yaxis: { title: "10Y Yield (%)" },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : treasury10yViewMode === "percentile"
                          ? {
                                shapes: createPercentileBands(darkMode, {
                                    bullishPct: 30,
                                    bearishPct: 70,
                                    invert: true,
                                }),
                                yaxis: {
                                    title: "Percentile",
                                    range: [-5, 105],
                                },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }
                          : {
                                shapes: createZScoreBands(darkMode),
                                yaxis: { title: "Z-Score" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }}
                />
            </div>
            {#if signalsFromMetrics.treasury_10y?.latest}
                {@const s = signalsFromMetrics.treasury_10y.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.signal_status || "Signal Status"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            {translations.current || "Current"}:
                            <b>{s.value?.toFixed(2)}%</b>
                            | {translations.percentile || "Percentile"}:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Treasury 2Y Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_treasury_2y || "2-Year Treasury Yield"}
                </h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={treasury2yViewMode === "zscore"}
                            on:click={() => (treasury2yViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={treasury2yViewMode === "percentile"}
                            on:click={() => (treasury2yViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                        <button
                            class:active={treasury2yViewMode === "raw"}
                            on:click={() => (treasury2yViewMode = "raw")}
                            title="Raw Values">📊</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={treasury2yRange}
                        onRangeChange={(r) => (treasury2yRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("TREASURY_2Y_YIELD")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.treasury_2y_desc ||
                    "2-Year Treasury Constant Maturity Yield. Short-term rate."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={treasury2yViewMode === "raw"
                        ? treasury2yData
                        : treasury2yViewMode === "percentile"
                          ? treasury2yPctData
                          : treasury2yZData}
                    layout={treasury2yViewMode === "raw"
                        ? {
                              yaxis: { title: "2Y Yield (%)" },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : treasury2yViewMode === "percentile"
                          ? {
                                shapes: createPercentileBands(darkMode, {
                                    bullishPct: 30,
                                    bearishPct: 70,
                                    invert: true,
                                }),
                                yaxis: {
                                    title: "Percentile",
                                    range: [-5, 105],
                                },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }
                          : {
                                shapes: createZScoreBands(darkMode),
                                yaxis: { title: "Z-Score" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }}
                />
            </div>
            {#if signalsFromMetrics.treasury_2y?.latest}
                {@const s = signalsFromMetrics.treasury_2y.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.signal_status || "Signal Status"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            {translations.current || "Current"}:
                            <b>{s.value?.toFixed(2)}%</b>
                            | {translations.percentile || "Percentile"}:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Yield Curve Spread (10Y - 2Y) Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_yield_curve ||
                        "Yield Curve (10Y-2Y Spread)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={yieldCurveViewMode === "raw"}
                            on:click={() => (yieldCurveViewMode = "raw")}
                            >{translations.view_raw || "Raw"}</button
                        >
                        <button
                            class:active={yieldCurveViewMode === "zscore"}
                            on:click={() => (yieldCurveViewMode = "zscore")}
                            >{translations.view_zscore || "Z-Score"}</button
                        >
                        <button
                            class:active={yieldCurveViewMode === "percentile"}
                            on:click={() => (yieldCurveViewMode = "percentile")}
                            >{translations.view_percentile ||
                                "Percentile"}</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={yieldCurveRange}
                        onRangeChange={(r) => (yieldCurveRange = r)}
                    />
                </div>
            </div>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={yieldCurveViewMode === "zscore"
                        ? yieldCurveZData
                        : yieldCurveViewMode === "percentile"
                          ? yieldCurvePctData
                          : yieldCurveRawData}
                    layout={{
                        ...yieldCurveLayout,
                        yaxis: {
                            ...yieldCurveLayout.yaxis,
                            title:
                                yieldCurveViewMode === "zscore"
                                    ? "Z-Score"
                                    : yieldCurveViewMode === "percentile"
                                      ? "Percentile"
                                      : translations.yield_curve_y ||
                                        "Spread (%)",
                            range:
                                yieldCurveViewMode === "percentile"
                                    ? [0, 100]
                                    : undefined,
                        },
                        shapes:
                            yieldCurveViewMode === "zscore"
                                ? [
                                      {
                                          type: "line",
                                          x0: 0,
                                          x1: 1,
                                          xref: "paper",
                                          y0: 1.5,
                                          y1: 1.5,
                                          line: {
                                              color: "rgba(220, 38, 38, 0.4)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                      {
                                          type: "line",
                                          x0: 0,
                                          x1: 1,
                                          xref: "paper",
                                          y0: -1.5,
                                          y1: -1.5,
                                          line: {
                                              color: "rgba(16, 185, 129, 0.4)",
                                              width: 1,
                                              dash: "dash",
                                          },
                                      },
                                      ...(yieldCurveLayout.shapes || []),
                                  ]
                                : yieldCurveViewMode === "percentile"
                                  ? [
                                        {
                                            type: "line",
                                            x0: 0,
                                            x1: 1,
                                            xref: "paper",
                                            y0: 80,
                                            y1: 80,
                                            line: {
                                                color: "rgba(220, 38, 38, 0.4)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                        {
                                            type: "line",
                                            x0: 0,
                                            x1: 1,
                                            xref: "paper",
                                            y0: 20,
                                            y1: 20,
                                            line: {
                                                color: "rgba(16, 185, 129, 0.4)",
                                                width: 1,
                                                dash: "dash",
                                            },
                                        },
                                        ...(yieldCurveLayout.shapes || []),
                                    ]
                                  : yieldCurveLayout.shapes,
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                />
            </div>

            <!-- Yield Curve Signal -->
            {#if dashboardData.yield_curve?.length > 0}
                {@const lastSpread = getLatestValue(dashboardData.yield_curve)}
                {@const prevSpread =
                    dashboardData.yield_curve?.[
                        dashboardData.yield_curve?.length - 22
                    ] ?? lastSpread}
                {@const spreadChange = lastSpread - prevSpread}
                {@const last10y = getLatestValue(dashboardData.treasury_10y)}
                {@const prev10y =
                    dashboardData.treasury_10y?.[
                        dashboardData.treasury_10y?.length - 22
                    ] ?? last10y}
                {@const rateChange = last10y - prev10y}
                {@const curveRegime = (() => {
                    if (spreadChange > 0.05 && rateChange < 0)
                        return {
                            label: "BULL STEEPENING",
                            class: "bullish",
                            emoji: "🟢",
                            desc: "Rates down, curve steepening - Risk-on for growth",
                        };
                    if (spreadChange > 0.05 && rateChange >= 0)
                        return {
                            label: "BEAR STEEPENING",
                            class: "warning",
                            emoji: "⚠️",
                            desc: "Rates up, curve steepening - Inflation concerns",
                        };
                    if (spreadChange < -0.05 && rateChange < 0)
                        return {
                            label: "BULL FLATTENING",
                            class: "neutral",
                            emoji: "🔵",
                            desc: "Rates down, curve flattening - Flight to safety",
                        };
                    if (spreadChange < -0.05 && rateChange >= 0)
                        return {
                            label: "BEAR FLATTENING",
                            class: "bearish",
                            emoji: "🔴",
                            desc: "Rates up, curve flattening - Policy tightening",
                        };
                    return {
                        label: "NEUTRAL",
                        class: "neutral",
                        emoji: "●",
                        desc: "Minimal curve movement",
                    };
                })()}
                <div class="signal-box" style="margin-top: 15px;">
                    <div
                        class="signal-badge {lastSpread < 0
                            ? 'bearish'
                            : curveRegime.class}"
                    >
                        {#if lastSpread < 0}
                            🔴 {translations.yc_inverted || "INVERTED"}
                        {:else}
                            {curveRegime.emoji} {curveRegime.label}
                        {/if}
                    </div>
                    <div
                        class="signal-details"
                        style="font-size: 12px; margin-top: 6px;"
                    >
                        <div style="margin-bottom: 4px;">
                            <b>Spread:</b>
                            {lastSpread?.toFixed(2)}% |
                            <b>Δ1M:</b>
                            <span
                                class:text-bullish={spreadChange > 0}
                                class:text-bearish={spreadChange < 0}
                                >{spreadChange > 0
                                    ? "+"
                                    : ""}{spreadChange.toFixed(2)}%</span
                            >
                            |
                            <b>10Y Δ:</b>
                            <span
                                class:text-bearish={rateChange > 0}
                                class:text-bullish={rateChange < 0}
                                >{rateChange > 0 ? "+" : ""}{rateChange.toFixed(
                                    2,
                                )}%</span
                            >
                        </div>
                        <div style="color: var(--text-muted); font-size: 11px;">
                            {curveRegime.desc}
                        </div>
                    </div>
                </div>
            {/if}

            {#if signalsFromMetrics.yield_curve?.latest}
                {@const s = signalsFromMetrics.yield_curve.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.chart_yield_curve ||
                                "Yield Curve Signal"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            {translations.current || "Current"}:
                            <b>{s.value?.toFixed(2)}%</b>
                            | {translations.percentile || "Percentile"}:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- 30Y-10Y Yield Curve -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Yield Curve (30Y-10Y Spread)</h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={yieldCurve30y10yViewMode === "raw"}
                            on:click={() => (yieldCurve30y10yViewMode = "raw")}
                            >Raw</button
                        >
                        <button
                            class:active={yieldCurve30y10yViewMode === "zscore"}
                            on:click={() =>
                                (yieldCurve30y10yViewMode = "zscore")}>Z</button
                        >
                        <button
                            class:active={yieldCurve30y10yViewMode ===
                                "percentile"}
                            on:click={() =>
                                (yieldCurve30y10yViewMode = "percentile")}
                            >%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={yieldCurve30y10yRange}
                        onRangeChange={(r) => (yieldCurve30y10yRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.yield_curve_30y10y_desc ||
                    "Long term curve steepness. Inversion = severe stress."}
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={yieldCurve30y10yViewMode === "zscore"
                        ? yieldCurve30y10yZData
                        : yieldCurve30y10yViewMode === "percentile"
                          ? yieldCurve30y10yPctData
                          : yieldCurve30y10yRawData}
                    layout={{
                        yaxis: {
                            title:
                                yieldCurve30y10yViewMode === "zscore"
                                    ? "Z-Score"
                                    : yieldCurve30y10yViewMode === "percentile"
                                      ? "Percentile"
                                      : "Spread (%)",
                            range:
                                yieldCurve30y10yViewMode === "percentile"
                                    ? [0, 100]
                                    : undefined,
                        },
                        margin: { l: 50, r: 20, t: 20, b: 40 },
                    }}
                />
            </div>
            {#if signalsFromMetrics.yield_curve_30y_10y?.latest && dashboardData.yield_curve_30y_10y?.length > 0}
                {@const s = signalsFromMetrics.yield_curve_30y_10y.latest}
                {@const lastSpread = s.value}
                {@const prevSpread =
                    dashboardData.yield_curve_30y_10y?.[
                        dashboardData.yield_curve_30y_10y?.length - 22
                    ] ?? lastSpread}
                {@const spreadChange = lastSpread - prevSpread}
                {@const last30y = getLatestValue(dashboardData.treasury_30y)}
                {@const prev30y =
                    dashboardData.treasury_30y?.[
                        dashboardData.treasury_30y?.length - 22
                    ] ?? last30y}
                {@const rateChange = (last30y ?? 0) - (prev30y ?? 0)}
                {@const curveRegime = (() => {
                    if (spreadChange > 0.03 && rateChange < 0)
                        return {
                            label: "BULL STEEP",
                            class: "bullish",
                            emoji: "🟢",
                        };
                    if (spreadChange > 0.03 && rateChange >= 0)
                        return {
                            label: "BEAR STEEP",
                            class: "warning",
                            emoji: "⚠️",
                        };
                    if (spreadChange < -0.03 && rateChange < 0)
                        return {
                            label: "BULL FLAT",
                            class: "neutral",
                            emoji: "🔵",
                        };
                    if (spreadChange < -0.03 && rateChange >= 0)
                        return {
                            label: "BEAR FLAT",
                            class: "bearish",
                            emoji: "🔴",
                        };
                    return { label: "HOLD", class: "neutral", emoji: "●" };
                })()}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            Curve Signal | {curveRegime.emoji}
                            {curveRegime.label}
                        </div>
                        <div
                            class="signal-status text-{lastSpread < 0
                                ? 'bearish'
                                : curveRegime.class}"
                        >
                            <span class="signal-dot"></span>
                            {lastSpread < 0
                                ? "INVERTED"
                                : getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Spread: <b>{s.value?.toFixed(2)}%</b> | Δ1M:
                            <span
                                class:text-bullish={spreadChange > 0}
                                class:text-bearish={spreadChange < 0}
                                >{spreadChange >= 0
                                    ? "+"
                                    : ""}{spreadChange.toFixed(2)}%</span
                            >
                            | P{s.percentile?.toFixed(0)}
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- 30Y-2Y Yield Curve (Full Spread) -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Yield Curve (30Y-2Y Full Spread)</h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={yieldCurve30y2yViewMode === "raw"}
                            on:click={() => (yieldCurve30y2yViewMode = "raw")}
                            >Raw</button
                        >
                        <button
                            class:active={yieldCurve30y2yViewMode === "zscore"}
                            on:click={() =>
                                (yieldCurve30y2yViewMode = "zscore")}>Z</button
                        >
                        <button
                            class:active={yieldCurve30y2yViewMode ===
                                "percentile"}
                            on:click={() =>
                                (yieldCurve30y2yViewMode = "percentile")}
                            >%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={yieldCurve30y2yRange}
                        onRangeChange={(r) => (yieldCurve30y2yRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                Full yield curve slope (2Y to 30Y). Deep inversion = severe
                recession signal.
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={yieldCurve30y2yViewMode === "zscore"
                        ? yieldCurve30y2yZData
                        : yieldCurve30y2yViewMode === "percentile"
                          ? yieldCurve30y2yPctData
                          : yieldCurve30y2yRawData}
                    layout={{
                        yaxis: {
                            title:
                                yieldCurve30y2yViewMode === "zscore"
                                    ? "Z-Score"
                                    : yieldCurve30y2yViewMode === "percentile"
                                      ? "Percentile"
                                      : "Spread (%)",
                            range:
                                yieldCurve30y2yViewMode === "percentile"
                                    ? [0, 100]
                                    : undefined,
                        },
                        margin: { l: 50, r: 20, t: 20, b: 40 },
                    }}
                />
            </div>
            {#if signalsFromMetrics.yield_curve_30y_2y?.latest && dashboardData.yield_curve_30y_2y?.length > 0}
                {@const s = signalsFromMetrics.yield_curve_30y_2y.latest}
                {@const lastSpread = s.value}
                {@const prevSpread =
                    dashboardData.yield_curve_30y_2y?.[
                        dashboardData.yield_curve_30y_2y?.length - 22
                    ] ?? lastSpread}
                {@const spreadChange = lastSpread - prevSpread}
                {@const last30y = getLatestValue(dashboardData.treasury_30y)}
                {@const prev30y =
                    dashboardData.treasury_30y?.[
                        dashboardData.treasury_30y?.length - 22
                    ] ?? last30y}
                {@const rateChange = (last30y ?? 0) - (prev30y ?? 0)}
                {@const curveRegime = (() => {
                    if (spreadChange > 0.05 && rateChange < 0)
                        return {
                            label: "BULL STEEP",
                            class: "bullish",
                            emoji: "🟢",
                        };
                    if (spreadChange > 0.05 && rateChange >= 0)
                        return {
                            label: "BEAR STEEP",
                            class: "warning",
                            emoji: "⚠️",
                        };
                    if (spreadChange < -0.05 && rateChange < 0)
                        return {
                            label: "BULL FLAT",
                            class: "neutral",
                            emoji: "🔵",
                        };
                    if (spreadChange < -0.05 && rateChange >= 0)
                        return {
                            label: "BEAR FLAT",
                            class: "bearish",
                            emoji: "🔴",
                        };
                    return { label: "HOLD", class: "neutral", emoji: "●" };
                })()}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            Full Curve | {curveRegime.emoji}
                            {curveRegime.label}
                        </div>
                        <div
                            class="signal-status text-{lastSpread < 0
                                ? 'bearish'
                                : curveRegime.class}"
                        >
                            <span class="signal-dot"></span>
                            {lastSpread < 0
                                ? "INVERTED"
                                : getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Spread: <b>{s.value?.toFixed(2)}%</b> | Δ1M:
                            <span
                                class:text-bullish={spreadChange > 0}
                                class:text-bearish={spreadChange < 0}
                                >{spreadChange >= 0
                                    ? "+"
                                    : ""}{spreadChange.toFixed(2)}%</span
                            >
                            | P{s.percentile?.toFixed(0)}
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_credit_spreads ||
                        "Credit Spreads (HY vs IG)"}
                </h3>
                <div class="header-controls">
                    <div class="mode-selector">
                        <button
                            class:active={creditSpreadsViewMode === "raw"}
                            on:click={() => (creditSpreadsViewMode = "raw")}
                            >Raw</button
                        >
                        <button
                            class:active={creditSpreadsViewMode === "zscore"}
                            on:click={() => (creditSpreadsViewMode = "zscore")}
                            >Z</button
                        >
                        <button
                            class:active={creditSpreadsViewMode ===
                                "percentile"}
                            on:click={() =>
                                (creditSpreadsViewMode = "percentile")}
                            >%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={creditSpreadsRange}
                        onRangeChange={(r) => (creditSpreadsRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("HY_SPREAD")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.credit_spreads_desc ||
                    "High Yield (red) and Investment Grade (Sky Blue) credit spreads. Higher spreads = more risk aversion."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={creditSpreadsViewMode === "zscore"
                        ? creditSpreadsZData
                        : creditSpreadsViewMode === "percentile"
                          ? creditSpreadsPctData
                          : creditSpreadsData}
                    layout={creditSpreadsViewMode === "raw"
                        ? {
                              yaxis: {
                                  title: "HY Spread (bps)",
                                  side: "left",
                                  autorange: true,
                              },
                              yaxis2: {
                                  title: "IG Spread (bps)",
                                  side: "right",
                                  overlaying: "y",
                                  autorange: true,
                              },
                              legend: {
                                  x: 0.01,
                                  y: 0.99,
                                  bgcolor: "rgba(0,0,0,0.0)",
                              },
                              margin: { l: 60, r: 60, t: 20, b: 40 },
                          }
                        : creditSpreadsViewMode === "percentile"
                          ? {
                                shapes: createPercentileBands(darkMode, {
                                    bullishPct: 30,
                                    bearishPct: 70,
                                    invert: true,
                                }),
                                yaxis: { title: "Percentile", range: [0, 100] },
                                legend: {
                                    x: 0.01,
                                    y: 0.99,
                                    bgcolor: "rgba(0,0,0,0.0)",
                                },
                                margin: { l: 60, r: 20, t: 20, b: 40 },
                            }
                          : {
                                shapes: createZScoreBands(darkMode),
                                yaxis: { title: "Z-Score" },
                                legend: {
                                    x: 0.01,
                                    y: 0.99,
                                    bgcolor: "rgba(0,0,0,0.0)",
                                },
                                margin: { l: 60, r: 20, t: 20, b: 40 },
                            }}
                />
            </div>

            <!-- Compact Metrics for Credit Spreads -->
            <div
                class="metrics-section"
                style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;"
            >
                <div class="metrics-table-container">
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>{translations.spread_type || "Spread"}</th>
                                <th
                                    >{translations.current_value ||
                                        "Current"}</th
                                >
                                <th>{translations.status || "Status"}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color: #ef4444; font-weight: 600;"
                                    >HY</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.hy_spread,
                                        ) ?? 0
                                    ).toFixed(0)} bps</td
                                >
                                <td>
                                    {#if getLatestValue(dashboardData.hy_spread) > 500}
                                        <span style="color: #ef4444;"
                                            >🔴 Stress</span
                                        >
                                    {:else if getLatestValue(dashboardData.hy_spread) > 400}
                                        <span style="color: #f59e0b;"
                                            >🔶 Elevated</span
                                        >
                                    {:else}
                                        <span style="color: #22c55e;"
                                            >✅ Normal</span
                                        >
                                    {/if}
                                </td>
                            </tr>
                            <tr>
                                <td style="color: #38bdf8; font-weight: 600;"
                                    >IG</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.ig_spread,
                                        ) ?? 0
                                    ).toFixed(0)} bps</td
                                >
                                <td>
                                    {#if getLatestValue(dashboardData.ig_spread) > 150}
                                        <span style="color: #ef4444;"
                                            >🔴 Stress</span
                                        >
                                    {:else if getLatestValue(dashboardData.ig_spread) > 100}
                                        <span style="color: #f59e0b;"
                                            >🔶 Elevated</span
                                        >
                                    {:else}
                                        <span style="color: #22c55e;"
                                            >✅ Normal</span
                                        >
                                    {/if}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- NEW: NFP (Non-Farm Payrolls) Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Non-Farm Payrolls (NFP)</h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={nfpViewMode === "raw"}
                            on:click={() => (nfpViewMode = "raw")}
                            title="Raw">📊</button
                        >
                        <button
                            class:active={nfpViewMode === "zscore"}
                            on:click={() => (nfpViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={nfpViewMode === "percentile"}
                            on:click={() => (nfpViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={nfpRange}
                        onRangeChange={(r) => (nfpRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                Monthly change in non-farm payrolls (thousands). Key labor
                market indicator. Above 150k = healthy, below 0 = contraction.
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={nfpViewMode === "raw"
                        ? nfpRawData
                        : nfpViewMode === "zscore"
                          ? nfpZData
                          : nfpPctData}
                    layout={nfpViewMode === "percentile"
                        ? {
                              shapes: createPercentileBands(darkMode, {
                                  bullishPct: 70,
                                  bearishPct: 30,
                                  invert: false,
                              }),
                              yaxis: { title: "Percentile", range: [-5, 105] },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : nfpViewMode === "zscore"
                          ? {
                                shapes: createZScoreBands(darkMode, {
                                    invertColors: false,
                                }),
                                yaxis: { title: "Z-Score" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }
                          : {
                                yaxis: { title: "Change (k)" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }}
                />
            </div>
            {#if signalsFromMetrics.nfp?.latest}
                {@const s = signalsFromMetrics.nfp.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Labor Market Signal</div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Change: <b>{s.value?.toFixed(0)}k</b> | Percentile:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- NEW: JOLTS Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Job Openings (JOLTS)</h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={joltsViewMode === "raw"}
                            on:click={() => (joltsViewMode = "raw")}
                            title="Raw">📊</button
                        >
                        <button
                            class:active={joltsViewMode === "zscore"}
                            on:click={() => (joltsViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={joltsViewMode === "percentile"}
                            on:click={() => (joltsViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={joltsRange}
                        onRangeChange={(r) => (joltsRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                Job openings in millions. Higher = tighter labor market. Watch
                for JOLTS/Unemployed ratio trends.
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={joltsViewMode === "raw"
                        ? joltsRawData
                        : joltsViewMode === "zscore"
                          ? joltsZData
                          : joltsPctData}
                    layout={joltsViewMode === "percentile"
                        ? {
                              shapes: createPercentileBands(darkMode, {
                                  bullishPct: 70,
                                  bearishPct: 30,
                                  invert: false,
                              }),
                              yaxis: { title: "Percentile", range: [-5, 105] },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : joltsViewMode === "zscore"
                          ? {
                                shapes: createZScoreBands(darkMode, {
                                    invertColors: false,
                                }),
                                yaxis: { title: "Z-Score" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }
                          : {
                                yaxis: { title: "Openings (M)" },
                                margin: { l: 50, r: 20, t: 20, b: 40 },
                            }}
                />
            </div>
            {#if signalsFromMetrics.jolts?.latest}
                {@const s = signalsFromMetrics.jolts.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Labor Demand Signal</div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Openings: <b>{s.value?.toFixed(1)}M</b> |
                            Percentile: <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- NEW: Financial Stress Indices Section -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>St. Louis Financial Stress Index (STLFSI4)</h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={stLouisStressViewMode === "zscore"}
                            on:click={() => (stLouisStressViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={stLouisStressViewMode ===
                                "percentile"}
                            on:click={() =>
                                (stLouisStressViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                        <button
                            class:active={stLouisStressViewMode === "raw"}
                            on:click={() => (stLouisStressViewMode = "raw")}
                            title="Raw Values">📊</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={stLouisStressRange}
                        onRangeChange={(r) => (stLouisStressRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                Weekly index measuring financial stress. Values above 0 =
                above-average stress.
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={stLouisStressViewMode === "raw"
                        ? stLouisStressRawData
                        : stLouisStressViewMode === "percentile"
                          ? stLouisStressPctData
                          : stLouisStressZData}
                    layout={stLouisStressViewMode === "percentile"
                        ? {
                              shapes: createPercentileBands(darkMode, {
                                  bullishPct: 30,
                                  bearishPct: 70,
                                  invert: true,
                              }),
                              yaxis: { title: "Percentile", range: [-5, 105] },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : {
                              shapes: createZScoreBands(darkMode, {
                                  invertColors: true,
                              }),
                              yaxis: {
                                  title:
                                      stLouisStressViewMode === "raw"
                                          ? "Index"
                                          : "Z-Score",
                              },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }}
                />
            </div>
            {#if signalsFromMetrics.st_louis_stress?.latest}
                {@const s = signalsFromMetrics.st_louis_stress.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Signal Status</div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Index: <b>{s.value?.toFixed(2)}</b> | Percentile:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>Kansas City Financial Stress Index (KCFSI)</h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={kansasCityStressViewMode === "zscore"}
                            on:click={() =>
                                (kansasCityStressViewMode = "zscore")}
                            title="Z-Score">Z</button
                        >
                        <button
                            class:active={kansasCityStressViewMode ===
                                "percentile"}
                            on:click={() =>
                                (kansasCityStressViewMode = "percentile")}
                            title="Percentile">%</button
                        >
                        <button
                            class:active={kansasCityStressViewMode === "raw"}
                            on:click={() => (kansasCityStressViewMode = "raw")}
                            title="Raw Values">📊</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={kansasCityStressRange}
                        onRangeChange={(r) => (kansasCityStressRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                Monthly index from Kansas City Fed. Positive = stress above
                typical.
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={kansasCityStressViewMode === "raw"
                        ? kansasCityStressRawData
                        : kansasCityStressViewMode === "percentile"
                          ? kansasCityStressPctData
                          : kansasCityStressZData}
                    layout={kansasCityStressViewMode === "percentile"
                        ? {
                              shapes: createPercentileBands(darkMode, {
                                  bullishPct: 30,
                                  bearishPct: 70,
                                  invert: true,
                              }),
                              yaxis: { title: "Percentile", range: [-5, 105] },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : {
                              shapes: createZScoreBands(darkMode, {
                                  invertColors: true,
                              }),
                              yaxis: {
                                  title:
                                      kansasCityStressViewMode === "raw"
                                          ? "Index"
                                          : "Z-Score",
                              },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }}
                />
            </div>
            {#if signalsFromMetrics.kansas_city_stress?.latest}
                {@const s = signalsFromMetrics.kansas_city_stress.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Signal Status</div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            Index: <b>{s.value?.toFixed(2)}</b> | Percentile:
                            <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- NEW: Corporate Bond Yields (BAA/AAA) -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Corporate Yields (BAA/AAA) & Credit Quality Spread</h3>
                <div class="header-controls">
                    <div class="view-mode-toggle">
                        <button
                            class:active={baaAaaViewMode === "raw"}
                            on:click={() => (baaAaaViewMode = "raw")}
                            title="Yields">📊</button
                        >
                        <button
                            class:active={baaAaaViewMode === "spread"}
                            on:click={() => (baaAaaViewMode = "spread")}
                            title="Spread">Δ</button
                        >
                    </div>
                    <TimeRangeSelector
                        selectedRange={baaAaaRange}
                        onRangeChange={(r) => (baaAaaRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {baaAaaViewMode === "spread"
                    ? "BAA-AAA spread = credit quality premium. Wider = more risk aversion."
                    : "BAA (red, lower quality IG) vs AAA (green, highest quality)."}
            </p>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    {darkMode}
                    data={baaAaaViewMode === "spread"
                        ? baaAaaSpreadData
                        : baaAaaData}
                    layout={baaAaaViewMode === "spread"
                        ? {
                              yaxis: { title: "Spread (%)" },
                              margin: { l: 50, r: 20, t: 20, b: 40 },
                          }
                        : {
                              yaxis: { title: "BAA Yield (%)", side: "left" },
                              yaxis2: {
                                  title: "AAA Yield (%)",
                                  side: "right",
                                  overlaying: "y",
                              },
                              legend: {
                                  x: 0.01,
                                  y: 0.99,
                                  bgcolor: "rgba(0,0,0,0.0)",
                              },
                              margin: { l: 60, r: 60, t: 20, b: 40 },
                          }}
                />
            </div>
            {#if signalsFromMetrics.baa_aaa_spread?.latest}
                {@const s = signalsFromMetrics.baa_aaa_spread.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Credit Quality Signal</div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            BAA-AAA Spread: <b>{s.value?.toFixed(2)}%</b> |
                            Percentile: <b>P{s.percentile?.toFixed(0)}</b>
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Individual Indicators -->
        {#each creditIndicators as item}
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{item.name}</h3>
                    <div class="header-controls">
                        <div class="view-mode-toggle">
                            <button
                                class:active={item.viewMode === "zscore"}
                                on:click={() => item.setViewMode("zscore")}
                                title="Z-Score">Z</button
                            >
                            <button
                                class:active={item.viewMode === "percentile"}
                                on:click={() => item.setViewMode("percentile")}
                                title="Percentile">%</button
                            >
                            <button
                                class:active={item.viewMode === "raw"}
                                on:click={() => item.setViewMode("raw")}
                                title="Raw Values">📊</button
                            >
                        </div>
                        <TimeRangeSelector
                            selectedRange={item.range}
                            onRangeChange={(r) => handleRangeChange(item.id, r)}
                        />
                        <span class="last-date"
                            >{translations.last || "Last"}: {getLastDate(
                                item.bank,
                            )}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {item.desc}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={item.data} layout={item.layout} />
                </div>

                {#if signalsFromMetrics[item.signalKey]?.latest}
                    {@const s = signalsFromMetrics[item.signalKey].latest}
                    <div
                        class="metrics-section"
                        style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                    >
                        <div
                            class="signal-item"
                            style="background: rgba(0,0,0,0.15); border: none;"
                        >
                            <div class="signal-label">
                                {translations.signal_status || "Signal Status"}
                            </div>
                            <div class="signal-status text-{s.state}">
                                <span class="signal-dot"></span>
                                {getStatusLabel(s.state)}
                            </div>
                            <div class="signal-value">
                                {translations.repo_value || "Value"}:
                                <b>{s.value?.toFixed(2) ?? "N/A"}</b>
                                | {translations.percentile || "Percentile"}:
                                <b>P{s.percentile?.toFixed(0) ?? "N/A"}</b>
                            </div>
                            <div
                                class="signal-reason"
                                style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                            >
                                {getSignalReason(item.signalKey, s.state)}
                            </div>
                        </div>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
</div>

<!-- ROC Section -->
<div class="roc-section">
    <div class="roc-card">
        <h4>{translations.roc_title || "Momentum Pulse (ROC)"}</h4>
        <div class="metrics-table-container">
            <div class="roc-grid">
                <div class="roc-row header">
                    <div class="roc-col">
                        {translations.roc_factor || "Factor"}
                    </div>
                    <div class="roc-col">1M</div>
                    <div class="roc-col">3M</div>
                    <div class="roc-col">6M</div>
                    <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_gli || "Global GLI"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_netliq || "US Net Liquidity"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <!-- Core Banks -->
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_fed || "Fed Assets"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_pboc || "PBoC Assets"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <!-- Macro Factors -->
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_cli || "Credit (CLI)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.cli?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.cli?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(dashboardData.cli?.rocs, period) ??
                                0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_real_rates || "Real Rates (5Y)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.tips?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.tips?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.tips?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_move || "MOVE Index (Bonds)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.move?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.move?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.move?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_fxvol || "FX Volatility (EVZ)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.fx_vol?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.fx_vol?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.fx_vol?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_vix || "Volatility (VIX)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            )?.toFixed(2) ?? "0.00"}%
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    /* Unified toggle button styling for mode selectors */
    .mode-selector,
    .view-mode-toggle {
        display: inline-flex;
        gap: 2px;
        background: rgba(0, 0, 0, 0.35);
        border-radius: 5px;
        padding: 2px;
        margin-right: 10px;
    }
    .mode-selector button,
    .view-mode-toggle button {
        padding: 3px 8px;
        font-size: 10px;
        font-weight: 700;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        transition: all 0.15s ease;
        background: transparent;
        color: rgba(255, 255, 255, 0.45);
        min-width: 22px;
        text-align: center;
    }
    .mode-selector button:hover,
    .view-mode-toggle button:hover {
        color: rgba(255, 255, 255, 0.85);
        background: rgba(255, 255, 255, 0.08);
    }
    .mode-selector button.active,
    .view-mode-toggle button.active {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.35);
    }

    /* Signal Box for CLI */
    .signal-box {
        margin-top: 15px;
        padding: 12px 16px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .signal-header {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        font-weight: 700;
        padding: 4px 0;
    }
    .signal-badge.bullish {
        color: #10b981;
    }
    .signal-badge.bearish {
        color: #ef4444;
    }
    .signal-badge.neutral {
        color: #94a3b8;
    }
    .signal-details {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 4px;
    }
    .signal-hint {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
        margin-left: 4px;
    }

    /* Signal Item - for credit indicators */
    .signal-item {
        padding: 10px 12px;
        border-radius: 6px;
    }
    .signal-label {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .signal-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 700;
    }
    .signal-status.text-bullish {
        color: #10b981;
    }
    .signal-status.text-bearish {
        color: #ef4444;
    }
    .signal-status.text-neutral {
        color: #94a3b8;
    }
    .signal-status.text-warning {
        color: #f59e0b;
    }
    .signal-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    .signal-value {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 4px;
    }

    /* Chart description styling */
    .chart-description {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.65);
        line-height: 1.5;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.15);
        border-radius: 6px;
        border-left: 3px solid rgba(99, 102, 241, 0.5);
        margin: 8px 0;
    }

    .view-mode-badge {
        font-size: 11px;
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 10px;
        font-weight: 600;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    .latest-values {
        display: flex;
        justify-content: space-around;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.15);
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.85rem;
    }

    /* Chart legend styling */
    .chart-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        padding: 10px 14px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        margin: 8px 0 12px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .legend-label {
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
    }
    .legend-desc {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.45);
        font-style: italic;
    }
</style>
