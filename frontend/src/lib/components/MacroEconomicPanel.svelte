<script>
    import MetricAnalysisCard from "./MetricAnalysisCard.svelte";
    import { filterWithCache } from "../utils/helpers.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State
    let tipsRange = "ALL";
    let tipsViewMode = "zscore";

    let nfpRange = "5Y";
    let nfpViewMode = "raw";

    let joltsRange = "5Y";
    let joltsViewMode = "raw";

    // Reactive Data Processing
    $: tipsZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.tips?.zscore || [],
                name: "TIPS (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        tipsRange,
        rangeIndicesCache,
    );

    $: tipsPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.tips?.percentile || [],
                name: "TIPS (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        tipsRange,
        rangeIndicesCache,
    );

    $: tipsRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.tips_market || [],
                name: "TIPS Break-even (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        tipsRange,
        rangeIndicesCache,
    );

    $: nfpRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.nfp?.total || [],
                name: "NFP Change (k)",
                type: "bar",
                marker: { color: "#10b981" },
            },
        ],
        dashboardData.dates,
        nfpRange,
        rangeIndicesCache,
    );

    $: joltsRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.jolts?.total || [],
                name: "JOLTS Job Openings (M)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        joltsRange,
        rangeIndicesCache,
    );
</script>

<div class="grid-2">
    <MetricAnalysisCard
        title="Inflation Expectations (TIPS)"
        description="Market-implied inflation from Treasury Inflation-Protected Securities."
        zData={tipsZData}
        pctData={tipsPctData}
        rawData={tipsRawData}
        range={tipsRange}
        viewMode={tipsViewMode}
        lastDate={dashboardData.last_dates?.TIPS || "N/A"}
        signal={dashboardData.signal_metrics?.tips}
        {translations}
        {darkMode}
        cardId="tips_inflation"
        onRangeChange={(r) => (tipsRange = r)}
        onViewModeChange={(m) => (tipsViewMode = m)}
    />

    <MetricAnalysisCard
        title="Non-Farm Payrolls (NFP)"
        description="Monthly change in US employment. Key indicator of economic health."
        rawData={nfpRawData}
        range={nfpRange}
        viewMode={nfpViewMode}
        lastDate={dashboardData.last_dates?.NFP || "N/A"}
        {translations}
        {darkMode}
        cardId="nfp_employment"
        onRangeChange={(r) => (nfpRange = r)}
        onViewModeChange={(m) => (nfpViewMode = m)}
    />

    <MetricAnalysisCard
        title="JOLTS Job Openings"
        description="Job Openings and Labor Turnover Survey. Measures labor demand."
        rawData={joltsRawData}
        range={joltsRange}
        viewMode={joltsViewMode}
        lastDate={dashboardData.last_dates?.JOLTS || "N/A"}
        {translations}
        {darkMode}
        cardId="jolts_openings"
        onRangeChange={(r) => (joltsRange = r)}
        onViewModeChange={(m) => (joltsViewMode = m)}
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
