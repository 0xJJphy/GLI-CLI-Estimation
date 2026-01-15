<script>
    import MetricAnalysisCard from "./MetricAnalysisCard.svelte";
    import { filterWithCache } from "../utils/helpers.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State for each metric
    let cliRange = "ALL";
    let cliViewMode = "zscore";

    let hyRange = "ALL";
    let hyViewMode = "zscore";

    let igRange = "ALL";
    let igViewMode = "zscore";

    let nfciCreditRange = "ALL";
    let nfciCreditViewMode = "zscore";

    let nfciRiskRange = "ALL";
    let nfciRiskViewMode = "zscore";

    let lendingRange = "ALL";
    let lendingViewMode = "zscore";

    // Reactive Data Processing
    $: cliZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.cli_z || [],
                name: translations.chart_cli_z || "CLI (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3 },
            },
        ],
        dashboardData.dates,
        cliRange,
        rangeIndicesCache,
    );

    $: cliPctData = filterWithCache(
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
        dashboardData.dates,
        cliRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        hyRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        hyRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        hyRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        igRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        igRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        igRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        nfciCreditRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        nfciCreditRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        nfciCreditRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        nfciRiskRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        nfciRiskRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        nfciRiskRange,
        rangeIndicesCache,
    );

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
        dashboardData.dates,
        lendingRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        lendingRange,
        rangeIndicesCache,
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
        dashboardData.dates,
        lendingRange,
        rangeIndicesCache,
    );
</script>

<div class="grid-2">
    <MetricAnalysisCard
        title={translations.chart_cli_title || "Credit Liquidity Index (CLI)"}
        description={translations.chart_cli_desc ||
            "Aggregate measure of US credit and liquidity conditions."}
        zData={cliZData}
        pctData={cliPctData}
        range={cliRange}
        viewMode={cliViewMode}
        lastDate={dashboardData.last_dates?.CLI || "N/A"}
        signal={dashboardData.signal_metrics?.cli}
        {translations}
        {darkMode}
        cardId="cli_main"
        onRangeChange={(r) => (cliRange = r)}
        onViewModeChange={(m) => (cliViewMode = m)}
    />

    <MetricAnalysisCard
        title={translations.credit_hy_name || "High Yield (HY) Spread"}
        description={translations.credit_hy_desc ||
            "HY spread vs Treasury. Higher = Risk-off."}
        zData={hyZData}
        pctData={hyPctData}
        rawData={hyRawData}
        range={hyRange}
        viewMode={hyViewMode}
        lastDate={dashboardData.last_dates?.HY_SPREAD || "N/A"}
        signal={dashboardData.signal_metrics?.hy_spread}
        {translations}
        {darkMode}
        cardId="hy_spread"
        onRangeChange={(r) => (hyRange = r)}
        onViewModeChange={(m) => (hyViewMode = m)}
    />

    <MetricAnalysisCard
        title={translations.credit_ig_name || "Investment Grade (IG) Spread"}
        description={translations.credit_ig_desc ||
            "IG spread vs Treasury. Higher = Stress."}
        zData={igZData}
        pctData={igPctData}
        rawData={igRawData}
        range={igRange}
        viewMode={igViewMode}
        lastDate={dashboardData.last_dates?.IG_SPREAD || "N/A"}
        signal={dashboardData.signal_metrics?.ig_spread}
        {translations}
        {darkMode}
        cardId="ig_spread"
        onRangeChange={(r) => (igRange = r)}
        onViewModeChange={(m) => (igViewMode = m)}
    />

    <MetricAnalysisCard
        title="NFCI Credit Subindex"
        description="Fed Chicago NFCI Credit. Positive = Tighter conditions."
        zData={nfciCreditZData}
        pctData={nfciCreditPctData}
        rawData={nfciCreditRawData}
        range={nfciCreditRange}
        viewMode={nfciCreditViewMode}
        lastDate={dashboardData.last_dates?.NFCI_CREDIT || "N/A"}
        signal={dashboardData.signal_metrics?.nfci_credit}
        {translations}
        {darkMode}
        cardId="nfci_credit"
        onRangeChange={(r) => (nfciCreditRange = r)}
        onViewModeChange={(m) => (nfciCreditViewMode = m)}
    />

    <MetricAnalysisCard
        title="NFCI Risk Subindex"
        description="Fed Chicago NFCI Risk. Positive = Higher systemic risk."
        zData={nfciRiskZData}
        pctData={nfciRiskPctData}
        rawData={nfciRiskRawData}
        range={nfciRiskRange}
        viewMode={nfciRiskViewMode}
        lastDate={dashboardData.last_dates?.NFCI_RISK || "N/A"}
        signal={dashboardData.signal_metrics?.nfci_risk}
        {translations}
        {darkMode}
        cardId="nfci_risk"
        onRangeChange={(r) => (nfciRiskRange = r)}
        onViewModeChange={(m) => (nfciRiskViewMode = m)}
    />

    <MetricAnalysisCard
        title="Lending Standards (SLOOS)"
        description="Fed Senior Loan Officer Survey. % Net Tightening."
        zData={lendingZData}
        pctData={lendingPctData}
        rawData={lendingRawData}
        range={lendingRange}
        viewMode={lendingViewMode}
        lastDate={dashboardData.last_dates?.LENDING_STD || "N/A"}
        signal={dashboardData.signal_metrics?.lending}
        {translations}
        {darkMode}
        cardId="lending_standards"
        onRangeChange={(r) => (lendingRange = r)}
        onViewModeChange={(m) => (lendingViewMode = m)}
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
