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

    // Range props
    export let cliRange = "ALL";
    export let hyRange = "ALL";
    export let igRange = "ALL";
    export let nfciCreditRange = "ALL";
    export let nfciRiskRange = "ALL";
    export let lendingRange = "ALL";
    export let vixRange = "ALL";
    export let moveRange = "ALL";
    export let fxVolRange = "ALL";
    export let treasury10yRange = "ALL";
    export let treasury2yRange = "ALL";
    export let yieldCurveRange = "ALL";
    export let divergenceRange = "ALL";
    export let repoStressRange = "ALL";
    export let tipsRange = "ALL";
    export let creditSpreadsRange = "ALL";

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
    let yieldCurveViewMode = "raw";
    let divergenceViewMode = "raw";

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
                name: "CLI Aggregate (Z-Score)",
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
                name: "CLI (Percentile)",
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
                name: "HY Spread (Z-Score)",
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
                name: "HY Spread (Percentile)",
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
                name: "HY Spread (bps)",
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
                name: "IG Spread (Z-Score)",
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
                name: "IG Spread (Percentile)",
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
                name: "IG Spread (bps)",
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
                name: "VIX (Z-Score)",
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
                name: "VIX (Percentile)",
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
                name: "10Y UST Yield (%)",
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
                name: "10Y Yield (Z-Score)",
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
                name: "10Y Yield (Percentile)",
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
                name: "2Y UST Yield (%)",
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
                name: "2Y Yield (Z-Score)",
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
                name: "2Y Yield (Percentile)",
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
                name: "10Y-2Y Spread (%)",
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
                name: "Yield Curve (Z-Score)",
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

    $: divergenceData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.macro_regime?.cli_gli_divergence || [],
                name: "CLI-GLI Divergence",
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
                name: "CLI-GLI Divergence (Z-Score)",
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
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr || [],
                name: "SOFR",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.iorb || [],
                name: "IORB",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2, dash: "dash" },
            },
        ],
        repoStressRange,
        true,
    );

    $: tipsData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.breakeven || [],
                name: "10Y Breakeven (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2.5 },
                yaxis: "y",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.real_rate || [],
                name: "10Y Real Rate (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2, dash: "dash" },
                yaxis: "y",
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.fwd_5y5y || [],
                name: "5Y5Y Forward (%)",
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

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;
    export let getLatestROC = (rocs, period) =>
        rocs?.[period]?.[rocs?.[period]?.length - 1] ?? 0;

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
        yaxis: { title: "NFCI Credit", autorange: true },
    };
    $: nfciRiskRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "NFCI Risk", autorange: true },
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

    // Repo Regime - corrected logic
    // SOFR ≈ IORB (within 5bps) = Normal/Bullish (adequate liquidity)
    // SOFR >> IORB (>10bps above) = Bearish (liquidity stress, like Sept 2019)
    // SOFR << IORB (significantly below) = Warning (excess liquidity, unusual)
    $: repoRegimeSignals = (() => {
        const sofr = dashboardData.repo_stress?.sofr;
        const iorb = dashboardData.repo_stress?.iorb;
        if (!sofr || !iorb) return [];
        return sofr.map((s, i) => {
            const spread = (s - (iorb[i] || 0)) * 100; // Convert to bps
            if (!Number.isFinite(spread)) return "neutral";
            if (spread > 10) return "bearish"; // SOFR >> IORB = liquidity stress
            if (spread < -5) return "neutral"; // Excess liquidity
            if (Math.abs(spread) <= 5) return "bullish"; // Normal range
            return "neutral";
        });
    })();

    $: repoStressLayout = {
        title: "Repo Stress (SOFR vs IORB)",
        xaxis: {
            title: "Date",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
        },
        yaxis: {
            title: "Rate (%)",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
        },
        margin: { t: 30, r: 20, b: 40, l: 50 },
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
        shapes: createRegimeShapes(
            repoStressData[0]?.x || [],
            dashboardData.dates,
            repoRegimeSignals,
            darkMode,
        ),
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
    $: stressAnalysis = dashboardData.fed_forecasts?.stress_analysis || {};
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

        <!-- Repo Stress Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_repo_stress ||
                        "Repo Market Stress (SOFR vs IORB)"}
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
            <p class="chart-description">
                {translations.repo_stress ||
                    "SOFR vs IORB spread indicates funding stress."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={repoStressData}
                    layout={repoStressLayout}
                />
            </div>

            <!-- Compact Metrics Sidebar Replacement -->
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
                                <td style="color: #f59e0b; font-weight: 600;"
                                    >SOFR</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td
                                    rowspan="2"
                                    style="vertical-align: middle; text-align: center; background: rgba(0,0,0,0.1); border-radius: 8px;"
                                >
                                    <div
                                        class:text-bullish={signalsFromMetrics
                                            .repo?.latest?.state === "bullish"}
                                        class:text-bearish={signalsFromMetrics
                                            .repo?.latest?.state === "bearish"}
                                        style="font-weight: 800; font-size: 1.1rem;"
                                    >
                                        {(
                                            (getLatestValue(
                                                dashboardData.repo_stress?.sofr,
                                            ) -
                                                getLatestValue(
                                                    dashboardData.repo_stress
                                                        ?.iorb,
                                                )) *
                                            100
                                        ).toFixed(1)} bps
                                    </div>
                                    <div
                                        style="font-size: 14px; margin-top: 4px;"
                                    >
                                        {#if signalsFromMetrics.repo?.latest?.state === "bullish" || signalsFromMetrics.repo?.latest?.state === "neutral"}
                                            ✅ {translations.status_ok || "OK"}
                                        {:else}
                                            ⚠️ {translations.status_stress ||
                                                "STRESS"}
                                        {/if}
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="color: #8b5cf6; font-weight: 600;"
                                    >IORB</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.iorb,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
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
            <div class="chart-container">
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
                <div class="signal-box" style="margin-top: 15px;">
                    <div
                        class="signal-badge {lastSpread < 0
                            ? 'bearish'
                            : lastSpread < 0.2 && lastSpread > prevSpread
                              ? 'warning'
                              : 'bullish'}"
                    >
                        {#if lastSpread < 0}
                            🔴 {translations.yc_inverted || "INVERTED"}
                        {:else if lastSpread < 0.2 && lastSpread > prevSpread}
                            ⚠️ {translations.yc_de_inverting ||
                                "DE-INVERTING (DANGER)"}
                        {:else}
                            🟢 {translations.yc_normal || "NORMAL"}
                        {/if}
                    </div>
                    <div class="signal-details" style="font-size: 13px;">
                        {translations.current || "Current"}:
                        <b>{lastSpread?.toFixed(2)}%</b>
                        | {translations.change_1m || "1M Change"}:
                        <b>{(lastSpread - prevSpread).toFixed(2)}%</b>
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

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_credit_spreads ||
                        "Credit Spreads (HY vs IG)"}
                </h3>
                <div class="header-controls">
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
                    data={creditSpreadsData}
                    layout={{
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
