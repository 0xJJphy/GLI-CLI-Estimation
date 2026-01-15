<script>
    import MetricAnalysisCard from "./MetricAnalysisCard.svelte";
    import { filterWithCache } from "../utils/helpers.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State
    let t10yRange = "ALL";
    let t10yViewMode = "raw";

    let t2yRange = "ALL";
    let t2yViewMode = "raw";

    let t30yRange = "ALL";
    let t30yViewMode = "raw";

    let yc10y2yRange = "ALL";
    let yc10y2yViewMode = "raw";

    let yc30y2yRange = "ALL";
    let yc30y2yViewMode = "raw";

    let yc30y10yRange = "ALL";
    let yc30y10yViewMode = "raw";

    // Reactive Data Processing
    $: t10yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_10y?.zscore || [],
                name: "10Y (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        t10yRange,
        rangeIndicesCache,
    );

    $: t10yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_10y?.percentile || [],
                name: "10Y (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        t10yRange,
        rangeIndicesCache,
    );

    $: t10yRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.treasury_10y || [],
                name: "10Y Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        t10yRange,
        rangeIndicesCache,
    );

    $: t2yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_2y?.zscore || [],
                name: "2Y (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 2 },
            },
        ],
        dashboardData.dates,
        t2yRange,
        rangeIndicesCache,
    );

    $: t2yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.treasury_2y?.percentile || [],
                name: "2Y (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 2 },
            },
        ],
        dashboardData.dates,
        t2yRange,
        rangeIndicesCache,
    );

    $: t2yRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.treasury_2y || [],
                name: "2Y Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 2 },
            },
        ],
        dashboardData.dates,
        t2yRange,
        rangeIndicesCache,
    );

    $: yc10y2yZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.yield_curve?.zscore || [],
                name: "10Y-2Y (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2 },
            },
        ],
        dashboardData.dates,
        yc10y2yRange,
        rangeIndicesCache,
    );

    $: yc10y2yPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.yield_curve?.percentile || [],
                name: "10Y-2Y (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 2 },
            },
        ],
        dashboardData.dates,
        yc10y2yRange,
        rangeIndicesCache,
    );

    $: yc10y2yRawData = filterWithCache(
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
        dashboardData.dates,
        yc10y2yRange,
        rangeIndicesCache,
    );

    $: t30yRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.treasury_30y || [],
                name: "30Y Yield (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#dc2626", width: 2 },
            },
        ],
        dashboardData.dates,
        t30yRange,
        rangeIndicesCache,
    );

    $: yc30y10yRawData = filterWithCache(
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
        dashboardData.dates,
        yc30y10yRange,
        rangeIndicesCache,
    );

    $: yc30y2yRawData = filterWithCache(
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
        dashboardData.dates,
        yc30y2yRange,
        rangeIndicesCache,
    );
</script>

<div class="grid-2">
    <MetricAnalysisCard
        title="10-Year Treasury Yield"
        description="Benchmark US 10Y rate. Defines long-term borrowing costs."
        zData={t10yZData}
        pctData={t10yPctData}
        rawData={t10yRawData}
        range={t10yRange}
        viewMode={t10yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_10Y_YIELD || "N/A"}
        signal={dashboardData.signal_metrics?.treasury_10y}
        {translations}
        {darkMode}
        cardId="t10y_yield"
        onRangeChange={(r) => (t10yRange = r)}
        onViewModeChange={(m) => (t10yViewMode = m)}
        pInvert={true}
    />

    <MetricAnalysisCard
        title="2-Year Treasury Yield"
        description="Reflects short-term Fed interest rate expectations."
        zData={t2yZData}
        pctData={t2yPctData}
        rawData={t2yRawData}
        range={t2yRange}
        viewMode={t2yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_2Y_YIELD || "N/A"}
        signal={dashboardData.signal_metrics?.treasury_2y}
        {translations}
        {darkMode}
        cardId="t2y_yield"
        onRangeChange={(r) => (t2yRange = r)}
        onViewModeChange={(m) => (t2yViewMode = m)}
        pInvert={true}
    />

    <MetricAnalysisCard
        title="30-Year Treasury Yield"
        description="Reflects long-term inflation and growth expectations."
        rawData={t30yRawData}
        range={t30yRange}
        viewMode={t30yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_30Y_YIELD || "N/A"}
        {translations}
        {darkMode}
        cardId="t30y_yield"
        onRangeChange={(r) => (t30yRange = r)}
        onViewModeChange={(m) => (t30yViewMode = m)}
    />

    <MetricAnalysisCard
        title="10Y-2Y Yield Curve"
        description="Spread between 10Y and 2Y yields. Inversion often precedes recession."
        zData={yc10y2yZData}
        pctData={yc10y2yPctData}
        rawData={yc10y2yRawData}
        range={yc10y2yRange}
        viewMode={yc10y2yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_10Y_YIELD || "N/A"}
        signal={dashboardData.signal_metrics?.yield_curve}
        {translations}
        {darkMode}
        cardId="yc_10y_2y"
        onRangeChange={(r) => (yc10y2yRange = r)}
        onViewModeChange={(m) => (yc10y2yViewMode = m)}
    />

    <MetricAnalysisCard
        title="30Y-10Y Yield Curve"
        description="Spread between 30Y and 10Y yields. Reflects long-term curve shape."
        rawData={yc30y10yRawData}
        range={yc30y10yRange}
        viewMode={yc30y10yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_30Y_YIELD || "N/A"}
        {translations}
        {darkMode}
        cardId="yc_30y_10y"
        onRangeChange={(r) => (yc30y10yRange = r)}
        onViewModeChange={(m) => (yc30y10yViewMode = m)}
    />

    <MetricAnalysisCard
        title="30Y-2Y Yield Curve"
        description="Spread between 30Y and 2Y yields. Full curve slope measure."
        rawData={yc30y2yRawData}
        range={yc30y2yRange}
        viewMode={yc30y2yViewMode}
        lastDate={dashboardData.last_dates?.TREASURY_30Y_YIELD || "N/A"}
        {translations}
        {darkMode}
        cardId="yc_30y_2y"
        onRangeChange={(r) => (yc30y2yRange = r)}
        onViewModeChange={(m) => (yc30y2yViewMode = m)}
    />
</div>

<style>
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
        margin-top: 24px;
    }

    @media (max-width: 1024px) {
        .grid-2 {
            grid-template-columns: 1fr;
        }
    }
</style>
