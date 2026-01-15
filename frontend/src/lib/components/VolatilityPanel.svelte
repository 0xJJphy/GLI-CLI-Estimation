<script>
    import MetricAnalysisCard from "./MetricAnalysisCard.svelte";
    import { filterWithCache } from "../utils/helpers.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State
    let vixRange = "ALL";
    let vixViewMode = "zscore";

    let moveRange = "ALL";
    let moveViewMode = "zscore";

    let fxVolRange = "ALL";
    let fxVolViewMode = "zscore";

    let stlRange = "ALL";
    let stlViewMode = "zscore";

    let kcfRange = "ALL";
    let kcfViewMode = "zscore";

    // Reactive Data Processing
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
        dashboardData.dates,
        vixRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        vixRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        vixRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        moveRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        moveRange,
        rangeIndicesCache,
    );

    $: moveRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.move || [],
                name: "MOVE Index (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
        ],
        dashboardData.dates,
        moveRange,
        rangeIndicesCache,
    );

    $: fxVolZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.fx_vol?.zscore || [],
                name: "FX Vol (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        fxVolRange,
        rangeIndicesCache,
    );

    $: fxVolPctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.fx_vol?.percentile || [],
                name: "FX Vol (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        fxVolRange,
        rangeIndicesCache,
    );

    $: fxVolRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.fx_vol?.raw ||
                    dashboardData.fx_vol ||
                    [],
                name: "DXY Realized Vol (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            },
        ],
        dashboardData.dates,
        fxVolRange,
        rangeIndicesCache,
    );

    $: stlZData = filterWithCache(
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
        dashboardData.dates,
        stlRange,
        rangeIndicesCache,
    );

    $: stlRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.st_louis_stress || [],
                name: "STLFSI4 (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#7c3aed", width: 2 },
            },
        ],
        dashboardData.dates,
        stlRange,
        rangeIndicesCache,
    );

    $: kcfZData = filterWithCache(
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
        dashboardData.dates,
        kcfRange,
        rangeIndicesCache,
    );

    $: kcfRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.kansas_city_stress || [],
                name: "KCFSI (Raw)",
                type: "scatter",
                mode: "lines",
                line: { color: "#c026d3", width: 2 },
            },
        ],
        dashboardData.dates,
        kcfRange,
        rangeIndicesCache,
    );
</script>

<div class="grid-2">
    <MetricAnalysisCard
        title={translations.credit_vix_name || "VIX (Equity Volatility)"}
        description={translations.credit_vix_desc ||
            "CBOE Volatility Index. Higher = Fear."}
        zData={vixZData}
        pctData={vixPctData}
        rawData={vixRawData}
        range={vixRange}
        viewMode={vixViewMode}
        lastDate={dashboardData.last_dates?.VIX || "N/A"}
        signal={dashboardData.signal_metrics?.vix}
        {translations}
        {darkMode}
        cardId="vix_vol"
        onRangeChange={(r) => (vixRange = r)}
        onViewModeChange={(m) => (vixViewMode = m)}
        pBullish={30}
        pBearish={70}
        pInvert={true}
    />

    <MetricAnalysisCard
        title={translations.indicator_move_name ||
            "MOVE Index (Bond Volatility)"}
        description={translations.indicator_move_desc ||
            "ICE BofA MOVE Index. Higher = Stress."}
        zData={moveZData}
        pctData={movePctData}
        rawData={moveRawData}
        range={moveRange}
        viewMode={moveViewMode}
        lastDate={dashboardData.last_dates?.MOVE || "N/A"}
        signal={dashboardData.signal_metrics?.move}
        {translations}
        {darkMode}
        cardId="move_vol"
        onRangeChange={(r) => (moveRange = r)}
        onViewModeChange={(m) => (moveViewMode = m)}
        pBullish={30}
        pBearish={70}
        pInvert={true}
    />

    <MetricAnalysisCard
        title={translations.indicator_fx_vol_name ||
            "FX Volatility (USD Stress)"}
        description={translations.indicator_fx_vol_desc ||
            "Realized volatility of the US Dollar Index."}
        zData={fxVolZData}
        pctData={fxVolPctData}
        rawData={fxVolRawData}
        range={fxVolRange}
        viewMode={fxVolViewMode}
        lastDate={dashboardData.last_dates?.FX_VOL || "N/A"}
        signal={dashboardData.signal_metrics?.fx_vol}
        {translations}
        {darkMode}
        cardId="fx_vol"
        onRangeChange={(r) => (fxVolRange = r)}
        onViewModeChange={(m) => (fxVolViewMode = m)}
        pBullish={30}
        pBearish={70}
        pInvert={true}
    />

    <MetricAnalysisCard
        title="St. Louis Financial Stress Index"
        description="Measures degree of financial stress in markets."
        zData={stlZData}
        rawData={stlRawData}
        range={stlRange}
        viewMode={stlViewMode}
        lastDate={dashboardData.last_dates?.STLFSI4 || "N/A"}
        signal={dashboardData.signal_metrics?.st_louis_stress}
        {translations}
        {darkMode}
        cardId="st_louis_stress"
        onRangeChange={(r) => (stlRange = r)}
        onViewModeChange={(m) => (stlViewMode = m)}
        pInvert={true}
    />

    <MetricAnalysisCard
        title="Kansas City Financial Stress Index"
        description="Comprehensive measure of US financial stress."
        zData={kcfZData}
        rawData={kcfRawData}
        range={kcfRange}
        viewMode={kcfViewMode}
        lastDate={dashboardData.last_dates?.KCFSI || "N/A"}
        signal={dashboardData.signal_metrics?.kansas_city_stress}
        {translations}
        {darkMode}
        cardId="kansas_city_stress"
        onRangeChange={(r) => (kcfRange = r)}
        onViewModeChange={(m) => (kcfViewMode = m)}
        pInvert={true}
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
