<script>
    /**
     * RiskModelTab.svelte
     * Displays Credit Liquidity Index (CLI) and risk metrics.
     */

    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import StressPanel from "../components/StressPanel.svelte";
    import {
        STANCE_KEYS,
        STATE_SCORES,
        SIGNAL_CATEGORIES,
        getSignalWithFallback,
        calculateAggregateScore,
    } from "../utils/signalSchema.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";
    import {
        createZScoreBands,
        createPercentileBands,
        createRegimeShapes,
        PERCENTILE_CONFIG,
    } from "../utils/chartHelpers.js";
    import { getCutoffDate } from "../utils/helpers.js";
    import ChartCardV2 from "../components/ChartCardV2.svelte";
    import ChartStack from "../components/ChartStack.svelte";
    import { SignalBadge, SignalTable } from "../components/signals";

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

    // Card container references for full-card download feature
    let inflationExpectCard;
    let creditCompareCard;
    let cliCard;
    let tipsCard;
    let repoCorridorCard;
    let divergenceCard;
    let signalMatrixCard;
    let treasury10yCard;
    let treasury5yCard;
    let treasury2yCard;
    let sofrVolumeCard;
    let vixCard;
    let moveCard;
    let fxVolCard;
    let stLouisStressCard;
    let kansasCityStressCard;
    let baaAaaCard;
    let nfpCard;
    let joltsCard;
    let creditIndicatorCards = [];
    let yieldCurve2y10yCard;
    let yieldCurve5yCard;
    let yieldCurve30y10yCard;
    let yieldCurve30y2yCard;
    let creditSpreadsCard;

    // --- Performance Optimization: Cached Indices ---

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

    // Aggregate signal score: prefer backend signal_aggregate, fallback to client-side
    $: aggregateSignalScore = (() => {
        // Use backend-computed aggregate if available (single source of truth)
        if (dashboardData.signal_aggregate) {
            return dashboardData.signal_aggregate;
        }
        // Fallback to client-side calculation
        const signals = dashboardData.signals || {};
        return calculateAggregateScore(signals);
    })();

    // Bull/Bear counts from STANCE_KEYS only
    $: signalCounts = (() => {
        const signals = dashboardData.signals || {};
        let bullish = 0,
            bearish = 0,
            neutral = 0,
            warning = 0;

        for (const key of STANCE_KEYS) {
            const signal = getSignalWithFallback(signals, key);
            if (!signal || !signal.state) continue;

            const state = signal.state;
            if (state === "bullish") bullish++;
            else if (state === "bearish" || state === "danger") bearish++;
            else if (state === "warning") warning++;
            else neutral++;
        }

        return {
            bullish,
            bearish,
            neutral,
            warning,
            total: STANCE_KEYS.length,
        };
    })();

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

    // FUSED CHART: REPO RATES + SRF USAGE
    // SRF Usage data (filtered separately to match the range)
    $: srfUsageFiltered = filterWithCache(
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
                yaxis: "y2",
            },
        ],
        repoStressRange,
        true,
    );

    // Combine the already-filtered rate traces with the filtered SRF trace
    $: repoFusedData = [
        ...repoStressData.map((trace) => ({ ...trace, yaxis: "y" })),
        ...(srfUsageFiltered || []),
    ];

    $: repoFusedLayout = {
        title: "",
        xaxis: {
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            showticklabels: true,
        },
        // Main Rates Chart (Top ~75%)
        yaxis: {
            title: "Rate (%)",
            domain: [0.28, 1],
            anchor: "x",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            tickformat: ".2f",
        },
        // SRF Usage Bar Chart (Bottom ~20%)
        yaxis2: {
            title: "SRF ($B)",
            domain: [0, 0.2],
            anchor: "x",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            rangemode: "tozero",
            fixedrange: true,
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
        height: 500, // Taller to accommodate both
        shapes: [],
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

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: sofrVolumeTableColumns = [
        {
            key: "indicator",
            label: translations.indicator || "Indicator",
            align: "left",
        },
        {
            key: "value",
            label: translations.repo_value || "Value",
            align: "right",
        },
        {
            key: "status",
            label: translations.signal_status || "Status",
            align: "center",
        },
    ];

    $: sofrVolumeLatest =
        getLatestValue(dashboardData.repo_stress?.sofr_volume) ?? 0;
    $: sofrVolumeTableRows = [
        {
            indicator: "SOFR Volume",
            value: `$${sofrVolumeLatest.toFixed(1)}B`,
            status:
                sofrVolumeLatest > 1000
                    ? "✅ " + (translations.status_ok || "DEEP")
                    : sofrVolumeLatest > 500
                      ? "🔶 " + (translations.status_neutral || "MODERATE")
                      : "⚠️ " + (translations.status_stress || "THIN"),
            _color: "#06b6d4",
        },
    ];

    // Yield Curve Regime Logic
    $: yieldCurveLatestSpread = getLatestValue(dashboardData.yield_curve) ?? 0;
    $: yieldCurvePrevSpread =
        dashboardData.yield_curve?.[dashboardData.yield_curve?.length - 22] ??
        yieldCurveLatestSpread;
    $: yieldCurveSpreadChange = yieldCurveLatestSpread - yieldCurvePrevSpread;

    $: treasury10yLatestValue = getLatestValue(dashboardData.treasury_10y) ?? 0;
    $: treasury10yPrevValue =
        dashboardData.treasury_10y?.[dashboardData.treasury_10y?.length - 22] ??
        treasury10yLatestValue;
    $: treasury10yRateChange = treasury10yLatestValue - treasury10yPrevValue;

    /** @type {{ label: string, state: "bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger", emoji: string, desc: string }} */
    $: yieldCurveRegime = (() => {
        if (yieldCurveLatestSpread < 0)
            return {
                label: "INVERTED",
                state: "bearish",
                emoji: "🔴",
                desc: "Recession Signal",
            };

        if (yieldCurveSpreadChange > 0.05 && treasury10yRateChange < 0)
            return {
                label: "BULL STEEPENER",
                state: "bullish",
                emoji: "🟢",
                desc: "Rates ↓, Spread ↑",
            };
        if (yieldCurveSpreadChange > 0.05 && treasury10yRateChange >= 0)
            return {
                label: "BEAR STEEPENER",
                state: "warning",
                emoji: "🟠",
                desc: "Rates ↑, Spread ↑",
            };
        if (yieldCurveSpreadChange < -0.05 && treasury10yRateChange < 0)
            return {
                label: "BULL FLATTENER",
                state: "neutral",
                emoji: "🔵",
                desc: "Rates ↓, Spread ↓",
            };
        if (yieldCurveSpreadChange < -0.05 && treasury10yRateChange >= 0)
            return {
                label: "BEAR FLATTENER",
                state: "bearish",
                emoji: "🔴",
                desc: "Rates ↑, Spread ↓",
            };
        return {
            label: "HOLD",
            state: "neutral",
            emoji: "⚪",
            desc: "Little Change",
        };
    })();

    /**
     * Helper to determine yield curve regime for other curve pairs
     * @param {number} spreadChange
     * @param {number} rateChange
     * @returns {{ label: string, class: "bullish" | "bearish" | "neutral" | "warning" }}
     */
    function getCurveRegime(spreadChange, rateChange) {
        if (spreadChange > 0.03 && rateChange < 0)
            return { label: "BULL STEEP", class: "bullish" };
        if (spreadChange > 0.03 && rateChange >= 0)
            return { label: "BEAR STEEP", class: "warning" };
        if (spreadChange < -0.03 && rateChange < 0)
            return { label: "BULL FLAT", class: "neutral" };
        if (spreadChange < -0.03 && rateChange >= 0)
            return { label: "BEAR FLAT", class: "bearish" };
        return { label: "HOLD", class: "neutral" };
    }

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: yieldCurveTableColumns = [
        { key: "metric", label: "Metric", align: "left" },
        { key: "value", label: "Value", align: "right" },
        { key: "change", label: "1M Change", align: "right" },
    ];

    $: yieldCurveTableRows = [
        {
            metric: "10Y-2Y Spread",
            value: (yieldCurveLatestSpread * 100).toFixed(0) + " bps",
            change: (yieldCurveSpreadChange * 100).toFixed(0) + " bps",
        },
        {
            metric: "10Y Yield",
            value: treasury10yLatestValue.toFixed(2) + "%",
            change: (treasury10yRateChange * 100).toFixed(0) + " bps",
        },
    ];

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: repoCorridorTableColumns = [
        { key: "rate", label: translations.repo_rate || "Rate", align: "left" },
        {
            key: "value",
            label: translations.repo_value || "Value",
            align: "right",
        },
    ];

    $: repoCorridorTableRows = [
        {
            rate: "SRF (Ceiling)",
            value:
                (
                    getLatestValue(dashboardData.repo_stress?.srf_rate) ?? 0
                ).toFixed(2) + "%",
            _color: "#ef4444",
        },
        {
            rate: "SOFR",
            value:
                (getLatestValue(dashboardData.repo_stress?.sofr) ?? 0).toFixed(
                    2,
                ) + "%",
            _color: "#3b82f6",
        },
        {
            rate: "IORB (Floor)",
            value:
                (getLatestValue(dashboardData.repo_stress?.iorb) ?? 0).toFixed(
                    2,
                ) + "%",
            _color: "#22c55e",
        },
        {
            rate: "RRP Award",
            value:
                (
                    getLatestValue(dashboardData.repo_stress?.rrp_award) ?? 0
                ).toFixed(2) + "%",
            _color: "#8b5cf6",
        },
    ];

    /** @type {import('../components/signals/SignalTable.svelte').SummaryBox} */
    $: repoCorridorTableSummary = {
        value: `${latestSofrToFloor.toFixed(1)} bps`,
        label: "SOFR-IORB",
        signal:
            corridorStressLevel === "NORMAL"
                ? "bullish"
                : corridorStressLevel === "ELEVATED"
                  ? "warning"
                  : "bearish",
    };

    $: repoCorridorSubcharts = [
        {
            key: "srf",
            data: srfUsageFiltered || [],
            yaxisTitle: "SRF ($B)",
            showGrid: true,
        },
    ];

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: inflationExpectTableColumns = [
        { key: "tenor", label: "Tenor", align: "left" },
        { key: "value", label: "Value", align: "right" },
    ];

    $: inflationExpectTableRows = [
        {
            tenor: "1Y Expectation",
            value:
                (
                    getLatestValue(
                        dashboardData.inflation_expect?.Cleveland_1Y,
                    ) ?? 0
                ).toFixed(2) + "%",
            _color: "#3b82f6",
        },
        {
            tenor: "2Y Expectation",
            value:
                (
                    getLatestValue(
                        dashboardData.inflation_expect?.Cleveland_2Y,
                    ) ?? 0
                ).toFixed(2) + "%",
            _color: "#1e3a8a",
        },
        {
            tenor: "5Y Expectation",
            value:
                (
                    getLatestValue(
                        dashboardData.inflation_expect?.Cleveland_5Y,
                    ) ?? 0
                ).toFixed(2) + "%",
            _color: "#f59e0b",
        },
        {
            tenor: "10Y Expectation",
            value:
                (
                    getLatestValue(
                        dashboardData.inflation_expect?.Cleveland_10Y,
                    ) ?? 0
                ).toFixed(2) + "%",
            _color: "#ef4444",
        },
    ];

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: tipsMarketTableColumns = [
        { key: "label", label: "Metric", align: "left" },
        { key: "value", label: "Value", align: "right" },
    ];

    $: tipsMarketTableRows = (() => {
        if (!signalsFromMetrics.tips?.latest) return [];
        return [
            {
                label: "10Y Breakeven (%)",
                value: (
                    getLatestValue(dashboardData.tips?.breakeven) ?? 0
                ).toFixed(2),
            },
            {
                label: "10Y Real Rate (%)",
                value: (
                    getLatestValue(dashboardData.tips?.real_rate) ?? 0
                ).toFixed(2),
            },
            {
                label: "5Y5Y Forward (%)",
                value: (
                    getLatestValue(dashboardData.tips?.fwd_5y5y) ?? 0
                ).toFixed(2),
            },
        ];
    })();

    // --- STRESS INDICES ---
    /** @type {import("../components/signals/SignalTable.svelte").TableColumn[]} */
    const stressIndexTableColumns = [
        { key: "metric", label: "METRIC", align: "left" },
        { key: "value", label: "VALUE", align: "right" },
        { key: "percentile", label: "PCTL", align: "right" },
        { key: "zscore", label: "Z-SCR", align: "right" },
    ];

    $: stLouisStressTableRows = (() => {
        if (!signalsFromMetrics.st_louis_stress?.latest) return [];
        const s = signalsFromMetrics.st_louis_stress.latest;
        return [
            {
                metric: "STLFSI4 Index",
                value: s.value?.toFixed(2),
                percentile: `P${s.percentile?.toFixed(0)}`,
                zscore: s.zScore?.toFixed(2),
                _signal: {
                    value: getStatusLabel(s.state),
                    color: getSignalColor(s.state),
                },
            },
        ];
    })();

    $: kansasCityStressTableRows = (() => {
        if (!signalsFromMetrics.kansas_city_stress?.latest) return [];
        const s = signalsFromMetrics.kansas_city_stress.latest;
        return [
            {
                metric: "KCFSI Index",
                value: s.value?.toFixed(2),
                percentile: `P${s.percentile?.toFixed(0)}`,
                zscore: s.zScore?.toFixed(2),
                _signal: {
                    value: getStatusLabel(s.state),
                    color: getSignalColor(s.state),
                },
            },
        ];
    })();

    $: baaAaaTableRows = (() => {
        if (!signalsFromMetrics.baa_aaa_spread?.latest) return [];
        const s = signalsFromMetrics.baa_aaa_spread.latest;
        return [
            {
                metric: "BAA-AAA Spread",
                value: s.value ? `${s.value.toFixed(2)}%` : "-",
                percentile: `P${s.percentile?.toFixed(0)}`,
                zscore: s.zScore?.toFixed(2),
                _signal: {
                    value: getStatusLabel(s.state),
                    color: getSignalColor(s.state),
                },
            },
        ];
    })();

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: yieldCurve3010TableColumns = [
        { key: "label", label: "Metric" },
        { key: "value", label: "Value (%)", align: "right" },
        { key: "delta", label: "Δ1M (%)", align: "right" },
        { key: "pct", label: "Percentile", align: "right" },
    ];

    $: yieldCurve3010TableRows = (() => {
        if (!signalsFromMetrics.yield_curve_30y_10y?.latest) return [];
        const s = signalsFromMetrics.yield_curve_30y_10y.latest;
        const lastSpread = s.value;
        const prevSpread =
            dashboardData.yield_curve_30y_10y?.[
                dashboardData.yield_curve_30y_10y?.length - 22
            ] ?? lastSpread;
        const spreadChange = lastSpread - prevSpread;

        return [
            {
                label: "30Y-10Y Spread",
                value: s.value?.toFixed(2),
                delta: (spreadChange >= 0 ? "+" : "") + spreadChange.toFixed(2),
                pct: `P${s.percentile?.toFixed(0)}`,
            },
        ];
    })();

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: yieldCurve302TableColumns = [
        { key: "label", label: "Metric" },
        { key: "value", label: "Value (%)", align: "right" },
        { key: "delta", label: "Δ1M (%)", align: "right" },
        { key: "pct", label: "Percentile", align: "right" },
    ];

    $: yieldCurve302TableRows = (() => {
        if (!signalsFromMetrics.yield_curve_30y_2y?.latest) return [];
        const s = signalsFromMetrics.yield_curve_30y_2y.latest;
        const lastSpread = s.value;
        const prevSpread =
            dashboardData.yield_curve_30y_2y?.[
                dashboardData.yield_curve_30y_2y?.length - 22
            ] ?? lastSpread;
        const spreadChange = lastSpread - prevSpread;

        return [
            {
                label: "30Y-2Y Spread",
                value: s.value?.toFixed(2),
                delta: (spreadChange >= 0 ? "+" : "") + spreadChange.toFixed(2),
                pct: `P${s.percentile?.toFixed(0)}`,
            },
        ];
    })();

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: creditSpreadsTableColumns = [
        { key: "label", label: "Spread", align: "left" },
        { key: "value", label: "Current", align: "right" },
        { key: "status", label: "Status", align: "right" },
    ];

    $: creditSpreadsTableRows = (() => {
        const hyVal = getLatestValue(dashboardData.hy_spread);
        const igVal = getLatestValue(dashboardData.ig_spread);
        const hyStress =
            hyVal > 500
                ? "🔴 Stress"
                : hyVal > 400
                  ? "🔶 Elevated"
                  : "✅ Normal";
        const igStress =
            igVal > 150
                ? "🔴 Stress"
                : igVal > 120
                  ? "🔶 Elevated"
                  : "✅ Normal";

        return [
            {
                label: "HY Spread",
                value: hyVal ? `${hyVal.toFixed(0)} bps` : "N/A",
                status: hyStress,
                _color: "#ef4444",
            },
            {
                label: "IG Spread",
                value: igVal ? `${igVal.toFixed(0)} bps` : "N/A",
                status: igStress,
                _color: "#38bdf8",
            },
        ];
    })();

    /** @type {import('../components/signals/SignalTable.svelte').TableColumn[]} */
    $: laborTableColumns = [
        { key: "label", label: "Metric", align: "left" },
        { key: "value", label: "Value", align: "right" },
        { key: "pct", label: "Percentile", align: "right" },
    ];

    $: nfpTableRows = (() => {
        if (!signalsFromMetrics.nfp?.latest) return [];
        const s = signalsFromMetrics.nfp.latest;
        return [
            {
                label: "NFP Change",
                value: `${s.value?.toFixed(0)}k`,
                pct: `P${s.percentile?.toFixed(0)}`,
                _color: getSignalColor(s.state),
            },
        ];
    })();

    $: joltsTableRows = (() => {
        if (!signalsFromMetrics.jolts?.latest) return [];
        const s = signalsFromMetrics.jolts.latest;
        return [
            {
                label: "JOLTS Openings",
                value: `${s.value?.toFixed(2)}M`,
                pct: `P${s.percentile?.toFixed(0)}`,
                _color: getSignalColor(s.state),
            },
        ];
    })();

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
    /** @type {"bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger"} */
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

    function getSignalColor(signal) {
        const colors = {
            bullish: "#22c55e",
            bearish: "#ef4444",
            neutral: "#6b7280",
            warning: "#f59e0b",
            ok: "#10b981",
            danger: "#dc2626",
        };
        return colors[signal] || colors.neutral;
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

    $: creditSpreadsZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", autorange: true },
        margin: { l: 60, r: 20, t: 20, b: 40 },
        legend: { x: 0.01, y: 0.99, bgcolor: "rgba(0,0,0,0.0)" },
    };

    $: creditSpreadsPctLayout = {
        shapes: createPercentileBands(darkMode, {
            bullishPct: 30,
            bearishPct: 70,
            invert: true,
        }),
        yaxis: { title: "Percentile", range: [0, 100], autorange: false },
        margin: { l: 60, r: 20, t: 20, b: 40 },
        legend: { x: 0.01, y: 0.99, bgcolor: "rgba(0,0,0,0.0)" },
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
    // Fed Rate Corridor Stress Classification:
    // - HIGH: SRF usage > $1B (banks tapping backstop) OR SOFR within 5bps of ceiling
    // - ELEVATED: SOFR > 5bps above IORB floor OR < 10bps from ceiling
    // - NORMAL: SOFR trading near IORB (±5bps) with comfortable ceiling headroom
    // Note: Small SRF usage (<$1B) is normal operational noise, not stress
    $: corridorStressLevel = (() => {
        // HIGH stress: significant SRF usage or approaching ceiling
        if (latestSrfUsage > 1 || latestSofrToCeiling < 5) return "HIGH";
        // ELEVATED: SOFR drifting above floor or narrowing ceiling gap
        if (latestSofrToFloor > 5 || latestSofrToCeiling < 10)
            return "ELEVATED";
        // NORMAL: SOFR ≈ IORB (within ±5bps), adequate ceiling headroom
        return "NORMAL";
    })();
    $: corridorStressColor =
        corridorStressLevel === "HIGH"
            ? "#ef4444"
            : corridorStressLevel === "ELEVATED"
              ? "#f59e0b"
              : "#22c55e";

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
    /** @type {Record<string, { latest?: { state: "bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger", value?: number, percentile?: number, reason?: string } }>} */
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

<!-- Header with Aggregate Stance & Weighted Score -->
<div class="risk-header-summary">
    <div
        class="regime-badge bg-{aggregateSignalScore.state === 'bullish' ||
        aggregateSignalScore.state === 'leaning_bullish'
            ? 'bullish'
            : aggregateSignalScore.state === 'bearish' ||
                aggregateSignalScore.state === 'leaning_bearish'
              ? 'bearish'
              : 'neutral'}"
    >
        <span style="font-size: 1.2rem;"
            >{aggregateSignalScore.state === "bullish"
                ? "🚀"
                : aggregateSignalScore.state === "leaning_bullish"
                  ? "🐂"
                  : aggregateSignalScore.state === "bearish"
                    ? "⚠️"
                    : aggregateSignalScore.state === "leaning_bearish"
                      ? "🐻"
                      : "⚖️"}</span
        >
        {#if aggregateSignalScore.state === "bullish"}
            {translations.status_bullish || "BULLISH"}
        {:else if aggregateSignalScore.state === "leaning_bullish"}
            {translations.status_leaning_bullish || "LEANING BULLISH"}
        {:else if aggregateSignalScore.state === "bearish"}
            {translations.status_bearish || "BEARISH"}
        {:else if aggregateSignalScore.state === "leaning_bearish"}
            {translations.status_leaning_bearish || "LEANING BEARISH"}
        {:else}
            {translations.status_neutral || "NEUTRAL"}
        {/if}
    </div>
    <div class="stance-details">
        <span
            class="weighted-score"
            style="color: {aggregateSignalScore.score >= 0
                ? '#10b981'
                : '#ef4444'}; font-weight: 700; margin-right: 8px;"
        >
            {aggregateSignalScore.score >= 0
                ? "+"
                : ""}{aggregateSignalScore.score.toFixed(2)}
        </span>
        | {signalCounts.bullish}
        {translations.risk_bullish || "Bullish"}
        | {signalCounts.bearish + signalCounts.warning}
        {translations.risk_bearish || "Bearish"}
        | {signalCounts.total}
        {translations.risk_factors || "Factors"}
        {#if aggregateSignalScore.coverage < 1}
            <span style="color: #f59e0b; margin-left: 8px;"
                >({(aggregateSignalScore.coverage * 100).toFixed(0)}% {translations.coverage ||
                    "Coverage"})</span
            >
        {/if}
    </div>
</div>

<!-- Market Stress Dashboard -->
<div class="stress-dashboard-row" style="margin-bottom: 25px;">
    <StressPanel {stressAnalysis} {darkMode} {translations} />
</div>

<div class="main-charts">
    <div class="grid-2">
        <!-- Inflation Expectations (Swap Rates / Cleveland Fed) Chart -->
        <ChartCardV2
            title={translations.chart_inflation_swap_title ||
                "USD Inflation Swap Rates (Cleveland Fed)"}
            description={translations.repo_corridor_desc ||
                " Cleveland Fed inflation swap rates for various tenors. Inversion (1Y < 2Y) suggests market expectations of cooling inflation."}
            {darkMode}
            range={inflationExpectRange}
            onRangeChange={(r) => (inflationExpectRange = r)}
            lastDate={getLastDate("INFLATION_EXPECT_1Y")}
            cardId="inflation_expectations"
        >
            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                <SignalBadge
                    state={inflationExpectSignal}
                    value={inflationExpectSignal === "bearish"
                        ? translations.signal_inverted || "INVERTED"
                        : inflationExpectSignal === "bullish"
                          ? translations.signal_normal || "NORMAL"
                          : translations.signal_neutral || "NEUTRAL"}
                    label="Curve"
                />
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
                <Chart
                    {darkMode}
                    data={inflationExpectData}
                    layout={{
                        yaxis: {
                            title: translations.inflation_rate_y || "Rate (%)",
                            autorange: true,
                        },
                        margin: { l: 50, r: 20, t: 10, b: 40 },
                        showlegend: true,
                        legend: {
                            orientation: "h",
                            yanchor: "bottom",
                            y: 1.02,
                            xanchor: "center",
                            x: 0.5,
                        },
                    }}
                />
            </svelte:fragment>

            <!-- Footer Slot -->
            <svelte:fragment slot="footer">
                <div
                    style="display: flex; flex-direction: column; gap: 12px; width: 100%;"
                >
                    <SignalTable
                        columns={inflationExpectTableColumns}
                        rows={inflationExpectTableRows}
                        showHeader={false}
                        {darkMode}
                    />
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                    >
                        {#if inflationExpectSignal === "bearish"}
                            {translations.inflation_inverted_desc ||
                                "1Y Swap below 2Y Swap: Market expects imminent cooldown/disinflation."}
                        {:else if inflationExpectSignal === "bullish"}
                            {translations.inflation_normal_desc ||
                                "1Y Swap above 2Y Swap: Market expects near-term inflation to remain elevated."}
                        {:else}
                            Curve is flat or stable.
                        {/if}
                    </div>
                </div>
            </svelte:fragment>
        </ChartCardV2>

        <!-- TIPS / Inflation Expectations Chart -->
        <ChartCardV2
            title={translations.chart_inflation_exp ||
                "Inflation Expectations (TIPS Market)"}
            description={translations.tips_desc ||
                "Market-implied inflation (Breakeven) and cost of money (Real Rates)."}
            {darkMode}
            range={tipsRange}
            onRangeChange={(r) => (tipsRange = r)}
            lastDate={getLastDate("TIPS_BREAKEVEN")}
            cardId="tips_market_expectations"
        >
            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.tips?.latest}
                    {@const s = signalsFromMetrics.tips.latest}
                    <SignalBadge
                        state={s.state}
                        value={getStatusLabel(s.state)}
                        label="Macro"
                    />
                {:else}
                    <SignalBadge state="neutral" value="Loading..." />
                {/if}
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
                <Chart
                    {darkMode}
                    data={tipsData}
                    layout={tipsLayoutWithBands}
                />
            </svelte:fragment>

            <!-- Footer Slot -->
            <svelte:fragment slot="footer">
                <div
                    style="display: flex; flex-direction: column; gap: 12px; width: 100%;"
                >
                    <SignalTable
                        columns={tipsMarketTableColumns}
                        rows={tipsMarketTableRows}
                        showHeader={false}
                        {darkMode}
                    />
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                    >
                        {#if signalsFromMetrics.tips?.latest}
                            {@const s = signalsFromMetrics.tips.latest}
                            {getSignalReason("tips", s.state)}
                        {:else if computedTipsSignal}
                            {@const s = computedTipsSignal}
                            {translations[s.reasonKey] || s.reasonKey}
                        {:else}
                            No active signal alert.
                        {/if}
                    </div>
                </div>
            </svelte:fragment>
        </ChartCardV2>

        <!-- CLI Aggregate Chart -->
        <ChartCardV2
            title={translations.chart_cli_title ||
                "Credit Liquidity Index (CLI Aggregate)"}
            description={translations.cli ||
                "Aggregates credit conditions, volatility, and lending."}
            {darkMode}
            range={cliRange}
            onRangeChange={(r) => (cliRange = r)}
            lastDate={getLastDate("NFCI")}
            cardId="cli_aggregate"
        >
            <!-- Controls Slot -->
            <svelte:fragment slot="controls">
                <div class="view-mode-toggle">
                    <button
                        class:active={cliViewMode === "zscore"}
                        on:click={() => (cliViewMode = "zscore")}>Z</button
                    >
                    <button
                        class:active={cliViewMode === "percentile"}
                        on:click={() => (cliViewMode = "percentile")}>%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={cliRange}
                    onRangeChange={(r) => (cliRange = r)}
                />
            </svelte:fragment>

            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.cli?.latest}
                    {@const s = signalsFromMetrics.cli.latest}
                    <SignalBadge
                        state={s.state}
                        value={getStatusLabel(s.state)}
                        label="Stance"
                    />
                {/if}
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
                <Chart {darkMode} data={cliChartData} layout={cliLayout} />
            </svelte:fragment>

            <!-- Footer Slot -->
            <svelte:fragment slot="footer">
                {#if signalsFromMetrics.cli?.latest}
                    {@const s = signalsFromMetrics.cli.latest}
                    <div
                        style="display: flex; flex-direction: column; gap: 8px; width: 100%;"
                    >
                        <div
                            style="display: flex; justify-content: space-between; font-size: 13px; font-weight: 500;"
                        >
                            <span
                                >{translations.percentile || "Percentile"}</span
                            >
                            <span>P{s.percentile?.toFixed(0) ?? "N/A"}</span>
                        </div>
                        <div
                            class="signal-reason"
                            style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                        >
                            {getSignalReason("cli", s.state)}
                        </div>
                    </div>
                {/if}
            </svelte:fragment>
        </ChartCardV2>

        <!-- CLI-GLI Divergence Analysis (Macro Coupling) -->
        <ChartCardV2
            title={translations.chart_divergence_title ||
                "Liquidity-Activity Divergence"}
            description={translations.divergence_desc ||
                "Measures decoupling between credit liquidity (CLI) and economic activity (GLI)."}
            {darkMode}
            range={divergenceRange}
            onRangeChange={(r) => (divergenceRange = r)}
            cardId="cli_gli_divergence"
        >
            <!-- Controls Slot -->
            <svelte:fragment slot="controls">
                <div class="view-mode-toggle">
                    <button
                        class:active={divergenceViewMode === "zscore"}
                        on:click={() => (divergenceViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={divergenceViewMode === "percentile"}
                        on:click={() => (divergenceViewMode = "percentile")}
                        >%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={divergenceRange}
                    onRangeChange={(r) => (divergenceRange = r)}
                />
            </svelte:fragment>

            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                {@const lastDiv = getLatestValue(
                    dashboardData.macro_regime?.cli_gli_divergence,
                )}
                {#if lastDiv < -1}
                    <SignalBadge state="warning" value="TRAP" label="Signal" />
                {:else if lastDiv > 1}
                    <SignalBadge
                        state="bullish"
                        value="EQUITY"
                        label="Signal"
                    />
                {:else}
                    <SignalBadge state="neutral" value="COUPLED" />
                {/if}
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
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
                        },
                        margin: { l: 50, r: 20, t: 20, b: 40 },
                    }}
                />
            </svelte:fragment>

            <!-- Footer Slot -->
            <svelte:fragment slot="footer">
                <div
                    style="display: flex; flex-direction: column; gap: 12px; width: 100%;"
                >
                    <div
                        class="divergence-guide"
                        style="font-size: 11px; display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; opacity: 0.8;"
                    >
                        <div
                            style="border-left: 3px solid #10b981; padding-left: 8px; line-height: 1.3;"
                        >
                            <b style="color: #10b981;">EQUITY DRIVEN:</b> Activity
                            leads liquidity.
                        </div>
                        <div
                            style="border-left: 3px solid #ef4444; padding-left: 8px; line-height: 1.3;"
                        >
                            <b style="color: #ef4444;">LIQUIDITY TRAP:</b> Liquidity
                            up, activity down.
                        </div>
                        <div
                            style="border-left: 3px solid #f59e0b; padding-left: 8px; line-height: 1.3;"
                        >
                            <b style="color: #f59e0b;">EXCESS:</b> Asset inflation
                            potential.
                        </div>
                    </div>

                    {#if (getLatestValue(dashboardData.macro_regime?.cli_gli_divergence) ?? 0) < -1}
                        <div
                            class="signal-reason"
                            style="font-size: 11px; color: #ef4444; background: rgba(239, 68, 68, 0.05); padding: 8px; border-radius: 4px; border-left: 3px solid #ef4444; text-align: left;"
                        >
                            <b
                                >⚠️ {translations.divergence_alert ||
                                    "Divergence Alert"}</b
                            >:
                            {translations.divergence_alert_desc ||
                                "Liquidity is rising while activity contracts. Historically a sign of 'Liquidity Trap' before regime shifts."}
                        </div>
                    {/if}
                </div>
            </svelte:fragment>
        </ChartCardV2>

        <!-- Repo Stress Chart (Fed Rate Corridor) -->
        <ChartCardV2
            title={translations.chart_repo_corridor ||
                "Fed Rate Corridor (SOFR vs Bounds)"}
            description={translations.repo_corridor_desc ||
                "SOFR should trade between IORB (floor) and SRF Rate (ceiling). Approaching ceiling or SRF usage signals funding stress."}
            {darkMode}
            range={repoStressRange}
            onRangeChange={(r) => (repoStressRange = r)}
            lastDate={getLastDate("SOFR")}
            cardId="fed_rate_corridor"
        >
            <!-- Signal Slot: Status & SRF Warning -->
            <svelte:fragment slot="signal">
                <div style="display: flex; gap: 8px; align-items: center;">
                    {#if latestSrfUsage > 1}
                        <SignalBadge
                            state="bearish"
                            value={`$${latestSrfUsage.toFixed(1)}B`}
                            label="SRF Usage"
                        />
                    {/if}
                    <SignalBadge
                        state={corridorStressLevel === "NORMAL"
                            ? "bullish"
                            : corridorStressLevel === "ELEVATED"
                              ? "warning"
                              : "bearish"}
                        value={corridorStressLevel}
                        label="Status"
                    />
                </div>
            </svelte:fragment>

            <!-- Chart Slot: Multi-Axis Stack -->
            <svelte:fragment slot="chart">
                <ChartStack
                    {darkMode}
                    height={500}
                    mainRatio={0.72}
                    mainData={repoStressData.map((t) => ({ ...t, yaxis: "y" }))}
                    mainYAxisTitle="Rate (%)"
                    subcharts={repoCorridorSubcharts}
                />
            </svelte:fragment>

            <!-- Footer Slot: Rates Table with Integrated Signal -->
            <svelte:fragment slot="footer">
                <SignalTable
                    columns={repoCorridorTableColumns}
                    rows={repoCorridorTableRows}
                    summary={repoCorridorTableSummary}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- SOFR Volume Chart -->
        <ChartCardV2
            title={translations.chart_sofr_volume ||
                "Repo Market Depth (SOFR Volume)"}
            description={sofrVolumeViewMode === "raw"
                ? translations.sofr_volume_desc ||
                  "SOFR transaction volume measures repo market depth. Falling volume = early warning of dysfunction."
                : "Rate of Change shows momentum. Sharp drops (<-10%) may signal stress."}
            {darkMode}
            range={sofrVolumeRange}
            onRangeChange={(r) => (sofrVolumeRange = r)}
            lastDate={getLastDate("SOFR_VOLUME")}
            cardId="sofr_volume"
        >
            <!-- Controls Slot: View Mode Toggle -->
            <svelte:fragment slot="controls">
                <div class="view-mode-toggle">
                    <button
                        class:active={sofrVolumeViewMode === "raw"}
                        on:click={() => (sofrVolumeViewMode = "raw")}
                        title="Raw Values">📊</button
                    >
                    <button
                        class:active={sofrVolumeViewMode === "roc_5d"}
                        on:click={() => (sofrVolumeViewMode = "roc_5d")}
                        title="5-Day Rate of Change">5D</button
                    >
                    <button
                        class:active={sofrVolumeViewMode === "roc_20d"}
                        on:click={() => (sofrVolumeViewMode = "roc_20d")}
                        title="20-Day Rate of Change">20D</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={sofrVolumeRange}
                    onRangeChange={(r) => (sofrVolumeRange = r)}
                />
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <!-- Footer Slot: Metrics Table -->
            <svelte:fragment slot="footer">
                <SignalTable
                    columns={sofrVolumeTableColumns}
                    rows={sofrVolumeTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- Treasury 10Y Chart -->
        <!-- Treasury 10Y Chart -->
        <ChartCardV2
            title={translations.chart_treasury_10y || "10-Year Treasury Yield"}
            description={translations.treasury_10y_desc ||
                "10-Year Treasury Constant Maturity Yield. Key benchmark rate."}
            {darkMode}
            range={treasury10yRange}
            onRangeChange={(r) => (treasury10yRange = r)}
            lastDate={getLastDate("TREASURY_10Y_YIELD")}
            cardId="treasury_10y"
        >
            <!-- Controls Slot: View Mode Toggle -->
            <svelte:fragment slot="controls">
                <div class="view-mode-toggle">
                    <button
                        class:active={treasury10yViewMode === "zscore"}
                        on:click={() => (treasury10yViewMode = "zscore")}
                        title="Z-Score">Z</button
                    >
                    <button
                        class:active={treasury10yViewMode === "percentile"}
                        on:click={() => (treasury10yViewMode = "percentile")}
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
            </svelte:fragment>

            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.treasury_10y?.latest}
                    {@const s = signalsFromMetrics.treasury_10y.latest}
                    <SignalBadge
                        state={s.state}
                        value={treasury10yViewMode === "raw"
                            ? s.value?.toFixed(2)
                            : `P${s.percentile?.toFixed(0)}`}
                        label={treasury10yViewMode === "raw"
                            ? "Yield"
                            : "Percentile"}
                    />
                {/if}
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <!-- Footer Slot: Reason -->
            <svelte:fragment slot="footer">
                {#if signalsFromMetrics.treasury_10y?.latest}
                    {@const s = signalsFromMetrics.treasury_10y.latest}
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                    >
                        {getSignalReason("treasury_10y", s.state)}
                    </div>
                {/if}
            </svelte:fragment>
        </ChartCardV2>

        <!-- Treasury 2Y Chart -->
        <!-- Treasury 2Y Chart -->
        <ChartCardV2
            title={translations.chart_treasury_2y || "2-Year Treasury Yield"}
            description={translations.treasury_2y_desc ||
                "2-Year Treasury Constant Maturity Yield. Short-term rate."}
            {darkMode}
            range={treasury2yRange}
            onRangeChange={(r) => (treasury2yRange = r)}
            lastDate={getLastDate("TREASURY_2Y_YIELD")}
            cardId="treasury_2y"
        >
            <!-- Controls Slot: View Mode Toggle -->
            <svelte:fragment slot="controls">
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
            </svelte:fragment>

            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.treasury_2y?.latest}
                    {@const s = signalsFromMetrics.treasury_2y.latest}
                    <SignalBadge
                        state={s.state}
                        value={treasury2yViewMode === "raw"
                            ? s.value?.toFixed(2)
                            : `P${s.percentile?.toFixed(0)}`}
                        label={treasury2yViewMode === "raw"
                            ? "Yield"
                            : "Percentile"}
                    />
                {/if}
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <!-- Footer Slot: Reason -->
            <svelte:fragment slot="footer">
                {#if signalsFromMetrics.treasury_2y?.latest}
                    {@const s = signalsFromMetrics.treasury_2y.latest}
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                    >
                        {getSignalReason("treasury_2y", s.state)}
                    </div>
                {/if}
            </svelte:fragment>
        </ChartCardV2>

        <!-- Yield Curve Spread (10Y - 2Y) Chart -->
        <ChartCardV2
            title={translations.chart_yield_curve ||
                "Yield Curve (10Y-2Y Spread)"}
            description={translations.yield_curve_desc ||
                "Spread between 10-Year and 2-Year Treasury yields. Inversion often precedes recession."}
            {darkMode}
            range={yieldCurveRange}
            onRangeChange={(r) => (yieldCurveRange = r)}
            lastDate={getLastDate("TREASURY_10Y_YIELD")}
            cardId="yield_curve_2y_10y"
        >
            <!-- Controls Slot -->
            <svelte:fragment slot="controls">
                <div class="view-mode-toggle">
                    <button
                        class:active={yieldCurveViewMode === "zscore"}
                        on:click={() => (yieldCurveViewMode = "zscore")}
                        >{translations.view_zscore || "Z-Score"}</button
                    >
                    <button
                        class:active={yieldCurveViewMode === "percentile"}
                        on:click={() => (yieldCurveViewMode = "percentile")}
                        >{translations.view_percentile || "Percentile"}</button
                    >
                    <button
                        class:active={yieldCurveViewMode === "raw"}
                        on:click={() => (yieldCurveViewMode = "raw")}
                        title="Raw Values">📊</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={yieldCurveRange}
                    onRangeChange={(r) => (yieldCurveRange = r)}
                />
            </svelte:fragment>

            <!-- Signal Slot -->
            <svelte:fragment slot="signal">
                <SignalBadge
                    state={yieldCurveRegime.state}
                    value={yieldCurveRegime.label}
                    label="Regime"
                />
            </svelte:fragment>

            <!-- Chart Slot -->
            <svelte:fragment slot="chart">
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
                />
            </svelte:fragment>

            <!-- Footer Slot -->
            <svelte:fragment slot="footer">
                <div style="display: flex; flex-direction: column; gap: 15px;">
                    <SignalTable
                        columns={yieldCurveTableColumns}
                        rows={yieldCurveTableRows}
                        {darkMode}
                    />
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                    >
                        {yieldCurveRegime.desc}
                    </div>
                </div>
            </svelte:fragment>
        </ChartCardV2>

        <!-- 30Y-10Y Yield Curve -->
        <!-- 30Y-10Y Yield Curve -->
        <ChartCardV2
            bind:this={yieldCurve30y10yCard}
            title="Yield Curve (30Y-10Y Spread)"
            description={translations.yield_curve_30y10y_desc ||
                "Long term curve steepness. Inversion = severe stress."}
            {darkMode}
            cardId="yield_curve_30y_10y"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={yieldCurve30y10yViewMode === "raw"}
                        on:click={() => (yieldCurve30y10yViewMode = "raw")}
                        >Raw</button
                    >
                    <button
                        class:active={yieldCurve30y10yViewMode === "zscore"}
                        on:click={() => (yieldCurve30y10yViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={yieldCurve30y10yViewMode === "percentile"}
                        on:click={() =>
                            (yieldCurve30y10yViewMode = "percentile")}>%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={yieldCurve30y10yRange}
                    onRangeChange={(r) => (yieldCurve30y10yRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.yield_curve_30y_10y?.latest && dashboardData.yield_curve_30y_10y?.length > 0}
                    {@const s = signalsFromMetrics.yield_curve_30y_10y.latest}
                    {@const lastSpread = s.value}
                    {@const prevSpread =
                        dashboardData.yield_curve_30y_10y?.[
                            dashboardData.yield_curve_30y_10y?.length - 22
                        ] ?? lastSpread}
                    {@const spreadChange = lastSpread - prevSpread}
                    {@const last30y = getLatestValue(
                        dashboardData.treasury_30y,
                    )}
                    {@const prev30y =
                        dashboardData.treasury_30y?.[
                            dashboardData.treasury_30y?.length - 22
                        ] ?? last30y}
                    {@const rateChange = (last30y ?? 0) - (prev30y ?? 0)}
                    {@const curveRegime = getCurveRegime(
                        spreadChange,
                        rateChange,
                    )}
                    <SignalBadge
                        state={curveRegime.class}
                        label={curveRegime.label}
                    />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={yieldCurve3010TableColumns}
                    rows={yieldCurve3010TableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- 30Y-2Y Yield Curve (Full Spread) -->
        <ChartCardV2
            bind:this={yieldCurve30y2yCard}
            title="Yield Curve (30Y-2Y Spread)"
            description="Full yield curve slope (2Y to 30Y). Deep inversion = severe recession signal."
            {darkMode}
            cardId="yield_curve_30y_2y"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={yieldCurve30y2yViewMode === "raw"}
                        on:click={() => (yieldCurve30y2yViewMode = "raw")}
                        >Raw</button
                    >
                    <button
                        class:active={yieldCurve30y2yViewMode === "zscore"}
                        on:click={() => (yieldCurve30y2yViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={yieldCurve30y2yViewMode === "percentile"}
                        on:click={() =>
                            (yieldCurve30y2yViewMode = "percentile")}>%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={yieldCurve30y2yRange}
                    onRangeChange={(r) => (yieldCurve30y2yRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.yield_curve_30y_2y?.latest && dashboardData.yield_curve_30y_2y?.length > 0}
                    {@const s = signalsFromMetrics.yield_curve_30y_2y.latest}
                    {@const lastSpread = s.value}
                    {@const prevSpread =
                        dashboardData.yield_curve_30y_2y?.[
                            dashboardData.yield_curve_30y_2y?.length - 22
                        ] ?? lastSpread}
                    {@const spreadChange = lastSpread - prevSpread}
                    {@const last30y = getLatestValue(
                        dashboardData.treasury_30y,
                    )}
                    {@const prev30y =
                        dashboardData.treasury_30y?.[
                            dashboardData.treasury_30y?.length - 22
                        ] ?? last30y}
                    {@const rateChange = (last30y ?? 0) - (prev30y ?? 0)}
                    {@const curveRegime = getCurveRegime(
                        spreadChange,
                        rateChange,
                    )}
                    <SignalBadge
                        state={curveRegime.class}
                        label={curveRegime.label}
                    />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={yieldCurve302TableColumns}
                    rows={yieldCurve302TableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- Credit Spreads -->
        <ChartCardV2
            bind:this={creditSpreadsCard}
            title={translations.chart_credit_spreads ||
                "Credit Spreads (HY vs IG)"}
            description={translations.credit_spreads_desc ||
                "High Yield (red) and Investment Grade (Sky Blue) credit spreads. Higher spreads = more risk aversion."}
            {darkMode}
            cardId="credit_spreads"
            lastDate={getLastDate("HY_SPREAD")}
        >
            <svelte:fragment slot="controls">
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
                        class:active={creditSpreadsViewMode === "percentile"}
                        on:click={() => (creditSpreadsViewMode = "percentile")}
                        >%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={creditSpreadsRange}
                    onRangeChange={(r) => (creditSpreadsRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="chart">
                <Chart
                    {darkMode}
                    data={creditSpreadsViewMode === "zscore"
                        ? creditSpreadsZData
                        : creditSpreadsViewMode === "percentile"
                          ? creditSpreadsPctData
                          : creditSpreadsData}
                    layout={creditSpreadsViewMode === "raw"
                        ? creditSpreadsLayout
                        : creditSpreadsViewMode === "percentile"
                          ? creditSpreadsPctLayout
                          : creditSpreadsZLayout}
                />
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={creditSpreadsTableColumns}
                    rows={creditSpreadsTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- NEW: NFP (Non-Farm Payrolls) Chart -->
        <!-- NFP (Non-Farm Payrolls) Chart -->
        <ChartCardV2
            bind:this={nfpCard}
            title="Non-Farm Payrolls (NFP)"
            description="Monthly change in non-farm payrolls (thousands). Key labor market indicator. Above 150k = healthy, below 0 = contraction."
            {darkMode}
            cardId="nfp_employment"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={nfpViewMode === "raw"}
                        on:click={() => (nfpViewMode = "raw")}>Raw</button
                    >
                    <button
                        class:active={nfpViewMode === "zscore"}
                        on:click={() => (nfpViewMode = "zscore")}>Z</button
                    >
                    <button
                        class:active={nfpViewMode === "percentile"}
                        on:click={() => (nfpViewMode = "percentile")}>%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={nfpRange}
                    onRangeChange={(r) => (nfpRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.nfp?.latest}
                    {@const s = signalsFromMetrics.nfp.latest}
                    <SignalBadge state={s.state} label="Labor Market Signal" />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
                              yaxis: {
                                  title: "Percentile",
                                  range: [-5, 105],
                              },
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={laborTableColumns}
                    rows={nfpTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- NEW: JOLTS Chart -->
        <!-- JOLTS Chart -->
        <ChartCardV2
            bind:this={joltsCard}
            title="Job Openings (JOLTS)"
            description="Job openings in millions. Higher = tighter labor market. Watch for JOLTS/Unemployed ratio trends."
            {darkMode}
            cardId="jolts_openings"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={joltsViewMode === "raw"}
                        on:click={() => (joltsViewMode = "raw")}>Raw</button
                    >
                    <button
                        class:active={joltsViewMode === "zscore"}
                        on:click={() => (joltsViewMode = "zscore")}>Z</button
                    >
                    <button
                        class:active={joltsViewMode === "percentile"}
                        on:click={() => (joltsViewMode = "percentile")}
                        >%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={joltsRange}
                    onRangeChange={(r) => (joltsRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.jolts?.latest}
                    {@const s = signalsFromMetrics.jolts.latest}
                    <SignalBadge state={s.state} label="Labor Demand Signal" />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
                              yaxis: {
                                  title: "Percentile",
                                  range: [-5, 105],
                              },
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={laborTableColumns}
                    rows={joltsTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- NEW: Financial Stress Indices Section -->
        <!-- St. Louis Financial Stress Index -->
        <ChartCardV2
            bind:this={stLouisStressCard}
            title="St. Louis Financial Stress Index (STLFSI4)"
            description="Weekly index measuring financial stress. Values above 0 = above-average stress."
            {darkMode}
            cardId="st_louis_financial_stress"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={stLouisStressViewMode === "raw"}
                        on:click={() => (stLouisStressViewMode = "raw")}
                        >Raw</button
                    >
                    <button
                        class:active={stLouisStressViewMode === "zscore"}
                        on:click={() => (stLouisStressViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={stLouisStressViewMode === "percentile"}
                        on:click={() => (stLouisStressViewMode = "percentile")}
                        >%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={stLouisStressRange}
                    onRangeChange={(r) => (stLouisStressRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.st_louis_stress?.latest}
                    {@const s = signalsFromMetrics.st_louis_stress.latest}
                    <SignalBadge state={s.state} label="Signal Status" />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
                              yaxis: {
                                  title: "Percentile",
                                  range: [-5, 105],
                              },
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={stressIndexTableColumns}
                    rows={stLouisStressTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- Kansas City Financial Stress Index -->
        <ChartCardV2
            bind:this={kansasCityStressCard}
            title="Kansas City Financial Stress Index (KCFSI)"
            description="Monthly index from Kansas City Fed. Positive = stress above typical."
            {darkMode}
            cardId="kansas_city_financial_stress"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={kansasCityStressViewMode === "raw"}
                        on:click={() => (kansasCityStressViewMode = "raw")}
                        >Raw</button
                    >
                    <button
                        class:active={kansasCityStressViewMode === "zscore"}
                        on:click={() => (kansasCityStressViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={kansasCityStressViewMode === "percentile"}
                        on:click={() =>
                            (kansasCityStressViewMode = "percentile")}>%</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={kansasCityStressRange}
                    onRangeChange={(r) => (kansasCityStressRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.kansas_city_stress?.latest}
                    {@const s = signalsFromMetrics.kansas_city_stress.latest}
                    <SignalBadge state={s.state} label="Signal Status" />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
                              yaxis: {
                                  title: "Percentile",
                                  range: [-5, 105],
                              },
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={stressIndexTableColumns}
                    rows={kansasCityStressTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- NEW: Corporate Bond Yields (BAA/AAA) -->
        <!-- Corporate Bond Yields (BAA/AAA) -->
        <ChartCardV2
            bind:this={baaAaaCard}
            title="Corporate Yields (BAA/AAA) & Credit Quality Spread"
            description={baaAaaViewMode === "spread"
                ? "BAA-AAA spread = credit quality premium. Wider = more risk aversion."
                : "BAA (red, lower quality IG) vs AAA (green, highest quality)."}
            {darkMode}
            cardId="corp_yields_baa_aaa"
        >
            <svelte:fragment slot="controls">
                <div class="mode-selector">
                    <button
                        class:active={baaAaaViewMode === "raw"}
                        on:click={() => (baaAaaViewMode = "raw")}>Yields</button
                    >
                    <button
                        class:active={baaAaaViewMode === "spread"}
                        on:click={() => (baaAaaViewMode = "spread")}
                        >Spread</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={baaAaaRange}
                    onRangeChange={(r) => (baaAaaRange = r)}
                />
            </svelte:fragment>

            <svelte:fragment slot="signal">
                {#if signalsFromMetrics.baa_aaa_spread?.latest}
                    {@const s = signalsFromMetrics.baa_aaa_spread.latest}
                    <SignalBadge
                        state={s.state}
                        label="Credit Quality Signal"
                    />
                {/if}
            </svelte:fragment>

            <svelte:fragment slot="chart">
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
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={stressIndexTableColumns}
                    rows={baaAaaTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>

        <!-- Individual Indicators -->
        {#each creditIndicators as item, i}
            <ChartCardV2
                title={item.name}
                description={item.desc}
                {darkMode}
                range={item.range}
                onRangeChange={(r) => handleRangeChange(item.id, r)}
                lastDate={getLastDate(item.bank)}
                cardId={item.id}
            >
                <!-- Controls Slot: View Mode Toggle -->
                <svelte:fragment slot="controls">
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
                </svelte:fragment>

                <!-- Signal Slot -->
                <svelte:fragment slot="signal">
                    {#if signalsFromMetrics[item.signalKey]?.latest}
                        {@const s = signalsFromMetrics[item.signalKey].latest}
                        <SignalBadge
                            state={s.state}
                            value={item.viewMode === "raw"
                                ? s.value?.toFixed(2)
                                : `P${s.percentile?.toFixed(0)}`}
                            label={item.viewMode === "raw"
                                ? "Value"
                                : "Percentile"}
                        />
                    {/if}
                </svelte:fragment>

                <!-- Chart Slot -->
                <svelte:fragment slot="chart">
                    <Chart {darkMode} data={item.data} layout={item.layout} />
                </svelte:fragment>

                <!-- Footer Slot: Reason -->
                <svelte:fragment slot="footer">
                    {#if signalsFromMetrics[item.signalKey]?.latest}
                        {@const s = signalsFromMetrics[item.signalKey].latest}
                        <div
                            class="signal-reason"
                            style="font-size: 11px; color: var(--text-secondary); opacity: 0.7; font-style: italic; text-align: center;"
                        >
                            {getSignalReason(item.signalKey, s.state)}
                        </div>
                    {/if}
                </svelte:fragment>
            </ChartCardV2>
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
</style>
