<script>
    /**
     * ComponentsTab.svelte
     * Validation page for the enhanced chart abstraction system.
     * Demonstrates: Interactive Legend, ChartStack, Flexible Table, Centered Signals.
     */
    import ChartCardV2 from "../components/ChartCardV2.svelte";
    import ChartStack from "../components/ChartStack.svelte";
    import Chart from "../components/Chart.svelte";
    import {
        SignalBadge,
        SignalTable,
        SignalSummary,
        SignalLegend,
    } from "../components/signals";
    import { SERIES_CONFIG, createTrace } from "../utils/seriesConfig.js";
    import {
        filterWithCache,
        buildRangeIndicesCache,
    } from "../utils/chartHelpers.js";

    export let dashboardData = {};
    export let darkMode = true;

    // State for each chart
    let cliRange = "1Y";
    let corridorRange = "1Y";
    let divergenceRange = "3M";

    // Interactive legend state - which series are visible
    let visibleCorridorSeries = ["SOFR", "IORB", "SRF", "RRP"];

    // Reactive dates from real data
    $: dates = dashboardData.dates || [];

    // Build range cache for filtering
    $: rangeIndicesCache = buildRangeIndicesCache(dates);

    // === CHART 1: CLI with real data ===
    $: cliRaw = [createTrace("CLI", dates, dashboardData.cli?.total || [])];
    $: cliData = filterWithCache(cliRaw, cliRange, rangeIndicesCache, dates);
    $: cliSignal = dashboardData.signal_metrics?.cli?.latest;

    // === CHART 2: Fed Rate Corridor - MAIN CHART (Rates Only) ===
    $: corridorMainRaw = [
        {
            key: "SOFR",
            x: dates,
            y: dashboardData.repo_stress?.sofr || [],
            name: "SOFR",
            type: "scatter",
            mode: "lines",
            line: { color: "#38bdf8", width: 2.5 },
        },
        {
            key: "IORB",
            x: dates,
            y: dashboardData.repo_stress?.iorb || [],
            name: "IORB (Floor)",
            type: "scatter",
            mode: "lines",
            line: { color: "#10b981", width: 1.5, dash: "dash" },
        },
        {
            key: "SRF",
            x: dates,
            y: dashboardData.repo_stress?.srf_rate || [],
            name: "SRF (Ceiling)",
            type: "scatter",
            mode: "lines",
            line: { color: "#ef4444", width: 1.5, dash: "dash" },
        },
        {
            key: "RRP",
            x: dates,
            y: dashboardData.repo_stress?.rrp_award || [],
            name: "RRP Award",
            type: "scatter",
            mode: "lines",
            line: { color: "#a855f7", width: 1, dash: "dot" },
        },
    ];

    // Filter main chart by range AND visibility
    $: corridorMainFiltered = filterWithCache(
        corridorMainRaw.filter((trace) =>
            visibleCorridorSeries.includes(trace.key),
        ),
        corridorRange,
        rangeIndicesCache,
        dates,
    );

    // === CHART 2: Fed Rate Corridor - SUBCHART (SRF Usage) ===
    $: srfUsageRaw = [
        {
            x: dates,
            y: dashboardData.repo_stress?.srf_usage || [],
            name: "SRF Usage",
            type: "bar",
            marker: { color: "rgba(239, 68, 68, 0.7)" },
        },
    ];
    $: srfUsageFiltered = filterWithCache(
        srfUsageRaw,
        corridorRange,
        rangeIndicesCache,
        dates,
    );

    // Subchart configuration for Plotly domain subplots
    $: corridorSubcharts = [
        {
            key: "srf_usage",
            data: srfUsageFiltered,
            yaxisTitle: "SRF ($B)",
            showGrid: false,
        },
    ];

    // SOFR corridor signals
    $: corridorSignals = dashboardData.signals?.repo || {};
    $: sofrIorbSpread = corridorSignals?.value?.toFixed(1) || "N/A";
    $: corridorStatus = corridorSignals?.state || "neutral";
    $: gapToCeiling =
        ((dashboardData.repo_stress?.srf_rate?.slice(-1)[0] || 0) -
            (dashboardData.repo_stress?.sofr?.slice(-1)[0] || 0)) *
        100;

    // Interactive legend items with line styles
    /** @type {{ key: string; label: string; color: string; lineStyle?: "solid" | "dash" | "dot" }[]} */
    const corridorLegendItems = [
        {
            key: "SRF",
            label: "SRF Rate (Ceiling)",
            color: "#ef4444",
            lineStyle: /** @type {"dash"} */ ("dash"),
        },
        {
            key: "SOFR",
            label: "SOFR",
            color: "#38bdf8",
            lineStyle: /** @type {"solid"} */ ("solid"),
        },
        {
            key: "IORB",
            label: "IORB (Floor)",
            color: "#10b981",
            lineStyle: /** @type {"dash"} */ ("dash"),
        },
        {
            key: "RRP",
            label: "RRP Award",
            color: "#a855f7",
            lineStyle: /** @type {"dot"} */ ("dot"),
        },
        {
            key: "SRF_USAGE",
            label: "SRF Usage ($B)",
            color: "rgba(239, 68, 68, 0.7)",
        },
    ];

    // Toggle series visibility
    function toggleCorridorSeries(key) {
        if (visibleCorridorSeries.includes(key)) {
            visibleCorridorSeries = visibleCorridorSeries.filter(
                (k) => k !== key,
            );
        } else {
            visibleCorridorSeries = [...visibleCorridorSeries, key];
        }
    }

    // Table configuration for footer
    /** @type {{ key: string; label: string; width?: string; align?: "left" | "center" | "right" }[]} */
    $: corridorTableColumns = [
        {
            key: "rate",
            label: "RATE",
            width: "140px",
            align: /** @type {"left"} */ ("left"),
        },
        {
            key: "value",
            label: "VALUE",
            width: "80px",
            align: /** @type {"right"} */ ("right"),
        },
        // NOTE: SPREAD/SIGNAL column is rendered by the summary prop (rowspan)
    ];

    $: corridorTableRows = [
        {
            rate: "SRF (Ceiling)",
            value: dashboardData.repo_stress?.srf_rate?.slice(-1)[0],
            _color: "#ef4444",
        },
        {
            rate: "SOFR",
            value: dashboardData.repo_stress?.sofr?.slice(-1)[0],
            _color: "#38bdf8",
        },
        {
            rate: "IORB (Floor)",
            value: dashboardData.repo_stress?.iorb?.slice(-1)[0],
            _color: "#10b981",
        },
        {
            rate: "RRP Award",
            value: dashboardData.repo_stress?.rrp_award?.slice(-1)[0],
            _color: "#a855f7",
        },
    ].map((row) => ({
        ...row,
        value: row.value?.toFixed(2) + "%" || "N/A",
        spread: "",
    }));

    /** @type {{ value: string; label: string; signal: string; size: "small" | "medium" | "large" }} */
    $: corridorTableSummary = {
        value: `${sofrIorbSpread} bps`,
        label: "SOFR-IORB",
        signal: corridorStatus,
        size: /** @type {"large"} */ ("large"),
    };

    // === CHART 3: CLI-GLI Divergence ===
    $: divergenceRaw = [
        createTrace("CLI", dates, dashboardData.cli?.total || []),
        {
            x: dates,
            y: dashboardData.regime_v2a?.liquidity_z || [],
            name: "GLI Z-Score",
            type: "scatter",
            mode: "lines",
            line: { color: "#a855f7", width: 2 },
            yaxis: "y2",
        },
    ];
    $: divergenceData = filterWithCache(
        divergenceRaw,
        divergenceRange,
        rangeIndicesCache,
        dates,
    );

    const divergenceLegend = [
        {
            key: "near0",
            label: "Near 0",
            description: "Coupled",
            color: "#6b7280",
        },
        {
            key: "negative",
            label: "Negative",
            description: "CLI lagging",
            color: "#ef4444",
        },
        {
            key: "positive",
            label: "Positive",
            description: "CLI leading",
            color: "#22c55e",
        },
    ];

    // === CHART 4: SOFR Volume (Repo Market Depth) ===
    let sofrVolumeRange = "3Y";
    $: sofrVolumeRaw = [
        {
            x: dates,
            y: dashboardData.repo_stress?.sofr_volume || [],
            name: "SOFR Volume ($B)",
            type: "scatter",
            mode: "lines",
            line: { color: "#06b6d4", width: 2 },
            fill: "tozeroy",
            fillcolor: "rgba(6, 182, 212, 0.15)",
        },
    ];
    $: sofrVolumeData = filterWithCache(
        sofrVolumeRaw,
        sofrVolumeRange,
        rangeIndicesCache,
        dates,
    );

    // Latest SOFR Volume value
    $: latestSofrVolume =
        dashboardData.repo_stress?.sofr_volume?.slice(-1)[0] || 0;
    $: sofrVolumeStatus = latestSofrVolume > 500 ? "ok" : "warning";

    // Table for inline signal (NO summary prop = no rowspan)
    /** @type {{ key: string; label: string; width?: string; align?: "left" | "center" | "right" }[]} */
    const sofrVolumeTableColumns = [
        {
            key: "indicator",
            label: "INDICATOR",
            align: /** @type {"left"} */ ("left"),
        },
        {
            key: "value",
            label: "VALUE",
            align: /** @type {"right"} */ ("right"),
        },
        {
            key: "status",
            label: "SIGNAL STATUS",
            align: /** @type {"center"} */ ("center"),
        },
    ];

    $: sofrVolumeTableRows = [
        {
            indicator: "SOFR Volume",
            value: `$${latestSofrVolume.toFixed(1)}B`,
            status: sofrVolumeStatus === "ok" ? "✅ OK" : "⚠️ LOW",
            _color: "#06b6d4",
        },
    ];
</script>

<div class="components-tab" class:dark={darkMode}>
    <header class="tab-header">
        <h1>📦 Chart Components V2</h1>
        <p class="subtitle">
            <strong>New Features:</strong> Interactive Legend • Stacked Subcharts
            • Flexible Table • Centered Signals
        </p>
    </header>

    <!-- Section 1: Signal Primitives -->
    <section>
        <div class="section-header">
            <h2>Signal Primitives</h2>
            <p>Stand-alone UI components for metrics and alerts</p>
        </div>

        <div class="signals-grid">
            <div class="demo-box">
                <h3>SignalBadge</h3>
                <div class="badge-gallery">
                    <SignalBadge state="bullish" value="Bullish" />
                    <SignalBadge state="bearish" value="Bearish" />
                    <SignalBadge state="neutral" value="Neutral" />
                    <SignalBadge
                        state="warning"
                        value="11 bps"
                        label="Caution"
                    />
                    <SignalBadge state="ok" value="NORMAL" />
                    <SignalBadge state="danger" value="ALERT" />
                </div>
            </div>

            <div class="demo-box">
                <h3>SignalTable V2 (Flexible Columns + Summary)</h3>
                <SignalTable
                    columns={corridorTableColumns}
                    rows={corridorTableRows.slice(0, 3)}
                    summary={{
                        value: "-1.0 bps",
                        label: "Demo",
                        signal: "ok",
                        size: "small",
                    }}
                    showHeader
                    {darkMode}
                />
            </div>

            <div class="demo-box">
                <h3>Interactive Legend (Click to Toggle)</h3>
                <SignalLegend
                    items={corridorLegendItems}
                    layout="horizontal"
                    interactive
                    visibleKeys={visibleCorridorSeries}
                    onToggle={toggleCorridorSeries}
                    {darkMode}
                />
                <p class="demo-hint">
                    Visible: {visibleCorridorSeries.join(", ") || "None"}
                </p>
            </div>

            <div class="demo-box">
                <h3>SignalSummary (Large)</h3>
                <div class="summary-gallery">
                    <SignalSummary
                        value="{sofrIorbSpread} bps"
                        label="SOFR-IORB"
                        state={corridorStatus}
                        {darkMode}
                        size="large"
                    />
                </div>
            </div>
        </div>
    </section>

    <!-- Section 2: Fed Rate Corridor - FULL DEMO -->
    <section class="full-width">
        <div class="section-header">
            <h2>Fed Rate Corridor (Full Layout Demo)</h2>
            <p>Interactive Legend • Stacked Subchart • Table with Summary</p>
        </div>

        <ChartCardV2
            title="Fed Rate Corridor (SOFR vs Bounds)"
            {darkMode}
            range={corridorRange}
            onRangeChange={(r) => (corridorRange = r)}
            lastDate={dashboardData.last_dates?.SOFR || ""}
        >
            <svelte:fragment slot="signal">
                <div class="signal-row centered">
                    <SignalSummary
                        value="{sofrIorbSpread} bps"
                        label="SOFR-IORB Spread"
                        state={corridorStatus}
                        {darkMode}
                        size="large"
                    />
                    <SignalSummary
                        value="{gapToCeiling.toFixed(1)} bps"
                        label="Gap to Ceiling (SRF)"
                        state="neutral"
                        {darkMode}
                        size="large"
                    />
                    <div class="status-box {corridorStatus}">
                        <span class="status-label">Status</span>
                        <span class="status-value"
                            >{corridorStatus === "ok" ||
                            corridorStatus === "bullish"
                                ? "NORMAL"
                                : corridorStatus.toUpperCase()}</span
                        >
                    </div>
                </div>
                <p class="description-text">
                    SOFR should trade between IORB (floor) and SRF Rate
                    (ceiling). Approaching ceiling or SRF usage signals funding
                    stress.
                </p>
                <div class="legend-container">
                    <SignalLegend
                        items={corridorLegendItems}
                        layout="horizontal"
                        compact
                        interactive
                        visibleKeys={visibleCorridorSeries}
                        onToggle={toggleCorridorSeries}
                        {darkMode}
                    />
                </div>
            </svelte:fragment>

            <svelte:fragment slot="chart">
                <ChartStack
                    mainData={corridorMainFiltered}
                    height={450}
                    mainRatio={0.72}
                    subcharts={corridorSubcharts}
                    {darkMode}
                />
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={corridorTableColumns}
                    rows={corridorTableRows}
                    summary={corridorTableSummary}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>
    </section>

    <!-- Section: SOFR Volume (Repo Market Depth) - Demo with inline signal table -->
    <section class="full-width">
        <div class="section-header">
            <h2>Repo Market Depth (SOFR Volume)</h2>
            <p>Demo with inline signal in table (no rowspan summary)</p>
        </div>

        <ChartCardV2
            title="SOFR Volume"
            description="SOFR transaction volume measures repo market depth. Falling volume = early warning of dysfunction."
            {darkMode}
            range={sofrVolumeRange}
            onRangeChange={(r) => (sofrVolumeRange = r)}
            lastDate={dashboardData.last_dates?.SOFR || ""}
        >
            <svelte:fragment slot="chart">
                <Chart data={sofrVolumeData} {darkMode} />
            </svelte:fragment>

            <svelte:fragment slot="footer">
                <SignalTable
                    columns={sofrVolumeTableColumns}
                    rows={sofrVolumeTableRows}
                    showHeader
                    {darkMode}
                />
            </svelte:fragment>
        </ChartCardV2>
    </section>

    <!-- Section 3: Other Charts -->
    <section>
        <div class="section-header">
            <h2>Additional Charts</h2>
            <p>Using the same component system</p>
        </div>

        <div class="charts-grid">
            <ChartCardV2
                title="CLI Index"
                description="Credit Liquidity Index - Aggregate of credit spreads"
                {darkMode}
                range={cliRange}
                onRangeChange={(r) => (cliRange = r)}
                lastDate={dashboardData.last_dates?.CLI || ""}
            >
                <svelte:fragment slot="signal">
                    <SignalBadge
                        state={cliSignal?.state || "neutral"}
                        value="{cliSignal?.percentile?.toFixed(0) || 'N/A'}%"
                        label="Percentile"
                    />
                </svelte:fragment>
                <svelte:fragment slot="chart">
                    <Chart data={cliData} {darkMode} />
                </svelte:fragment>
            </ChartCardV2>

            <ChartCardV2
                title="CLI-GLI Divergence"
                description="Credit vs Global Liquidity coupling"
                {darkMode}
                range={divergenceRange}
                onRangeChange={(r) => (divergenceRange = r)}
            >
                <svelte:fragment slot="signal">
                    <SignalLegend
                        items={divergenceLegend}
                        layout="horizontal"
                        compact
                        {darkMode}
                    />
                </svelte:fragment>
                <svelte:fragment slot="chart">
                    <Chart
                        data={divergenceData}
                        {darkMode}
                        layout={{
                            yaxis2: {
                                overlaying: "y",
                                side: "right",
                                title: "GLI Z",
                            },
                            showlegend: false,
                        }}
                    />
                </svelte:fragment>
                <svelte:fragment slot="footer">
                    <SignalSummary
                        value={dashboardData.regime_v2a?.cli_gli_divergence
                            ?.slice(-1)[0]
                            ?.toFixed(2) || "N/A"}
                        label="Current Divergence"
                        state={dashboardData.regime_v2a?.cli_gli_divergence?.slice(
                            -1,
                        )[0] > 0
                            ? "bullish"
                            : "bearish"}
                        {darkMode}
                    />
                </svelte:fragment>
            </ChartCardV2>
        </div>
    </section>

    <!-- Section 4: Series Config -->
    <section>
        <div class="section-header">
            <h2>Series Configuration</h2>
            <p>Unified design tokens from <code>seriesConfig.js</code></p>
        </div>
        <div class="color-grid">
            {#each Object.entries(SERIES_CONFIG).slice(0, 15) as [key, config]}
                <div class="color-chip">
                    <span class="swatch" style="background: {config.color}"
                    ></span>
                    <span class="key">{key}</span>
                </div>
            {/each}
        </div>
    </section>
</div>

<style>
    .components-tab {
        padding: 24px;
        max-width: 1600px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        gap: 32px;
    }

    .tab-header {
        margin-bottom: 16px;
        text-align: center;
    }

    h1 {
        font-size: 1.6rem;
        margin-bottom: 8px;
        font-weight: 700;
    }

    .subtitle {
        opacity: 0.6;
        font-size: 0.85rem;
    }

    .subtitle strong {
        color: #10b981;
    }

    .section-header {
        margin-bottom: 24px;
    }

    h2 {
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .section-header p {
        font-size: 0.8rem;
        opacity: 0.5;
        margin: 0;
    }

    h3 {
        font-size: 0.7rem;
        margin-bottom: 16px;
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }

    section {
        padding: 28px;
        background: var(--bg-secondary, rgba(15, 23, 42, 0.5));
        border-radius: 16px;
        border: 1px solid var(--border-color, rgba(255, 255, 255, 0.06));
    }

    section.full-width {
        max-width: none;
    }

    /* ===== SIGNAL PRIMITIVES GRID ===== */
    .signals-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
    }

    @media (max-width: 1200px) {
        .signals-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .signals-grid {
            grid-template-columns: 1fr;
        }
    }

    .demo-box {
        background: rgba(0, 0, 0, 0.2);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.04);
        min-height: 140px;
        display: flex;
        flex-direction: column;
    }

    .badge-gallery {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: flex-start;
    }

    .summary-gallery {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        justify-content: center;
        align-items: center;
        flex: 1;
    }

    .demo-hint {
        margin-top: auto;
        padding-top: 12px;
        font-size: 0.7rem;
        opacity: 0.4;
        font-family: "JetBrains Mono", monospace;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* ===== CHARTS GRID ===== */
    .charts-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
    }

    @media (max-width: 1000px) {
        .charts-grid {
            grid-template-columns: 1fr;
        }
    }

    /* ===== FED CORRIDOR SIGNAL ROW ===== */
    .signal-row {
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
        margin-bottom: 20px;
        padding: 16px 0;
    }

    .signal-row.centered {
        justify-content: center;
        align-items: stretch;
    }

    .status-box {
        background: rgba(0, 0, 0, 0.25);
        padding: 20px 32px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        align-items: center;
        justify-content: center;
        min-width: 140px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }

    .status-label {
        font-size: 0.7rem;
        opacity: 0.5;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-value {
        font-size: 1.2rem;
        font-weight: 700;
    }

    .status-box.ok .status-value,
    .status-box.bullish .status-value {
        color: #10b981;
    }

    .status-box.warning .status-value {
        color: #f59e0b;
    }

    .status-box.bearish .status-value,
    .status-box.danger .status-value {
        color: #ef4444;
    }

    .status-box.neutral .status-value {
        color: #94a3b8;
    }

    .description-text {
        font-size: 0.8rem;
        line-height: 1.7;
        opacity: 0.7;
        padding: 12px 16px;
        border-left: 3px solid #3b82f6;
        margin: 12px 0 20px 0;
        background: rgba(59, 130, 246, 0.05);
        border-radius: 0 8px 8px 0;
        max-width: 900px;
    }

    .legend-container {
        display: flex;
        justify-content: center;
        padding: 16px 0;
        margin-bottom: 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        background: rgba(0, 0, 0, 0.1);
        border-radius: 8px;
    }

    /* ===== COLOR GRID ===== */
    .color-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
    }

    .color-chip {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        font-size: 0.75rem;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }

    .swatch {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1);
    }

    .key {
        font-family: "JetBrains Mono", monospace;
        opacity: 0.85;
    }
</style>
