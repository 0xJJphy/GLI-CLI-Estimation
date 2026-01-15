<script>
    import Chart from "./Chart.svelte";
    import MetricAnalysisCard from "./MetricAnalysisCard.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import { filterWithCache, getLatestValue } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State
    let divergenceRange = "ALL";
    let divergenceViewMode = "raw";

    let inflationExpectRange = "5Y";
    let creditCompareRange = "ALL";
    let creditCompareViewMode = "raw";

    let divergenceCard;
    let inflationExpectCard;
    let creditCompareCard;

    // Divergence Processing (CLI vs GLI)
    $: divergenceZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.cli_gli_divergence?.zscore ||
                    [],
                name: "Divergence (Z-Score)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2 },
            },
        ],
        dashboardData.dates,
        divergenceRange,
        rangeIndicesCache,
    );

    $: divergencePctData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y:
                    dashboardData.signal_metrics?.cli_gli_divergence
                        ?.percentile || [],
                name: "Divergence (Percentile)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2 },
            },
        ],
        dashboardData.dates,
        divergenceRange,
        rangeIndicesCache,
    );

    $: divergenceRawData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.macro_regime?.cli_gli_divergence || [],
                name: "CLI-GLI Divergence (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 2.5 },
                fill: "tozeroy",
                fillcolor: "rgba(244, 63, 94, 0.1)",
            },
        ],
        dashboardData.dates,
        divergenceRange,
        rangeIndicesCache,
    );

    // Inflation Expectations (Cleveland Fed)
    $: inflationData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_1y || [],
                name: "1Y Expectation (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2.5 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.inflation_swaps?.cleveland_10y || [],
                name: "10Y Expectation (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.tips?.fwd_5y5y || [],
                name: "5Y5Y Fwd (%)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2, dash: "dash" },
            },
        ],
        dashboardData.dates,
        inflationExpectRange,
        rangeIndicesCache,
    );

    $: inflationSignal = (() => {
        const last1y = getLatestValue(
            dashboardData.inflation_swaps?.cleveland_1y,
        );
        const last2y = getLatestValue(
            dashboardData.inflation_swaps?.cleveland_2y,
        );
        if (last1y < last2y - 0.05) return "bearish"; // Inverted = cooldown
        if (last1y > last2y + 0.05) return "bullish"; // Rising = inflationary
        return "neutral";
    })();

    // Credit Comparison (HY vs IG)
    $: creditCompareData = filterWithCache(
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
        dashboardData.dates,
        creditCompareRange,
        rangeIndicesCache,
    );

    $: creditCompareZData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.hy_spread?.zscore || [],
                name: "HY Z-Score",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.signal_metrics?.ig_spread?.zscore || [],
                name: "IG Z-Score",
                type: "scatter",
                mode: "lines",
                line: { color: "#38bdf8", width: 2 },
            },
        ],
        dashboardData.dates,
        creditCompareRange,
        rangeIndicesCache,
    );
</script>

<div class="grid-2">
    <MetricAnalysisCard
        title="CLI-GLI Divergence"
        description="Measures leads/lags between US (CLI) and Global (GLI) liquidity cycles."
        zData={divergenceZData}
        pctData={divergencePctData}
        rawData={divergenceRawData}
        range={divergenceRange}
        viewMode={divergenceViewMode}
        lastDate={dashboardData.last_dates?.LIQUIDITY_DIVERGENCE || "N/A"}
        signal={dashboardData.signal_metrics?.cli_gli_divergence}
        {translations}
        {darkMode}
        cardId="liquidity_divergence"
        onRangeChange={(r) => (divergenceRange = r)}
        onViewModeChange={(m) => (divergenceViewMode = m)}
    />

    <!-- Inflation Expectations Card -->
    <div class="chart-card" bind:this={inflationExpectCard}>
        <div class="chart-header">
            <h3>Cleveland Fed Inflation Expectations</h3>
            <div class="header-controls">
                <button
                    class="download-card-btn"
                    on:click={() =>
                        downloadCardAsImage(
                            inflationExpectCard,
                            "inflation_exp",
                        )}>📷</button
                >
                <TimeRangeSelector
                    selectedRange={inflationExpectRange}
                    onRangeChange={(r) => (inflationExpectRange = r)}
                />
            </div>
        </div>
        <p class="chart-description">
            Market-based expected inflation rates across different horizons.
        </p>
        <div class="chart-content" style="height: 300px;">
            <Chart
                {darkMode}
                data={inflationData}
                layout={{ yaxis: { title: "Rate (%)" } }}
            />
        </div>
        <div class="metrics-section">
            <div class="signal-item">
                <span class="signal-label">Term Structure Signal</span>
                <span class="signal-status text-{inflationSignal}">
                    <span class="signal-dot"></span>
                    {inflationSignal === "bullish"
                        ? "EXPANSIONARY"
                        : inflationSignal === "bearish"
                          ? "COOLDOWN / INVERTED"
                          : "STABLE"}
                </span>
            </div>
        </div>
    </div>

    <!-- Credit Spreads Comparison -->
    <div class="chart-card wide" bind:this={creditCompareCard}>
        <div class="chart-header">
            <h3>Credit Spread Comparison (HY vs IG)</h3>
            <div class="header-controls">
                <button
                    class="download-card-btn"
                    on:click={() =>
                        downloadCardAsImage(
                            creditCompareCard,
                            "credit_compare",
                        )}>📷</button
                >
                <div class="view-mode-toggle">
                    <button
                        class:active={creditCompareViewMode === "zscore"}
                        on:click={() => (creditCompareViewMode = "zscore")}
                        >Z</button
                    >
                    <button
                        class:active={creditCompareViewMode === "raw"}
                        on:click={() => (creditCompareViewMode = "raw")}
                        >📊</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={creditCompareRange}
                    onRangeChange={(r) => (creditCompareRange = r)}
                />
            </div>
        </div>
        <div class="chart-content" style="height: 400px;">
            <Chart
                {darkMode}
                data={creditCompareViewMode === "raw"
                    ? creditCompareData
                    : creditCompareZData}
                layout={{
                    yaxis: { title: "HY Spread (bps)", side: "left" },
                    yaxis2: {
                        title: "IG Spread (bps)",
                        overlaying: "y",
                        side: "right",
                    },
                    showlegend: true,
                }}
            />
        </div>
    </div>
</div>

<style>
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
        margin-top: 24px;
    }

    .chart-card.wide {
        grid-column: span 2;
    }

    .view-mode-toggle {
        display: flex;
        background: rgba(0, 0, 0, 0.1);
        padding: 2px;
        border-radius: 6px;
    }

    .view-mode-toggle button {
        padding: 2px 8px;
        font-size: 11px;
        border: none;
        background: transparent;
        color: var(--text-muted);
        cursor: pointer;
        border-radius: 4px;
        font-weight: 600;
    }

    .view-mode-toggle button.active {
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    .text-bullish {
        color: #10b981;
    }
    .text-bearish {
        color: #ef4444;
    }
    .text-neutral {
        color: #6b7280;
    }

    .signal-item {
        display: flex;
        align-items: center;
        gap: 16px;
        background: rgba(0, 0, 0, 0.05);
        padding: 12px 16px;
        border-radius: 8px;
    }

    .signal-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }

    @media (max-width: 1024px) {
        .grid-2,
        .chart-card.wide {
            grid-template-columns: 1fr;
            grid-column: span 1;
        }
    }
</style>
