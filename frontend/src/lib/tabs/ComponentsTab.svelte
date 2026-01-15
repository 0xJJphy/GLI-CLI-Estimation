<script>
    /**
     * ComponentsTab.svelte
     * Validation page for new chart abstraction components.
     */
    import ChartCardV2 from "../components/ChartCardV2.svelte";
    import Chart from "../components/Chart.svelte";
    import {
        SignalBadge,
        SignalTable,
        SignalSummary,
        SignalLegend,
    } from "../components/signals";
    import { SERIES_CONFIG, createTrace } from "../utils/seriesConfig.js";

    export let dashboardData = {};
    export let darkMode = true;

    // Sample data generation
    const dates =
        dashboardData.dates ||
        Array.from({ length: 100 }, (_, i) => {
            const d = new Date();
            d.setDate(d.getDate() - (100 - i));
            return d.toISOString().split("T")[0];
        });

    const sampleSeries = dates.map(
        (_, i) => Math.sin(i / 10) * 20 + 50 + Math.random() * 5,
    );

    // State
    let range1 = "ALL";
    let range2 = "1Y";
    let range3 = "3M";

    // Chart data using seriesConfig
    $: cliData = [
        createTrace("CLI", dates, dashboardData.cli_z || sampleSeries),
    ];
    $: hyData = [
        createTrace(
            "HY_SPREAD",
            dates,
            dashboardData.hy_spread || sampleSeries,
        ),
    ];

    // Signal examples
    const tableRows = [
        { label: "SOFR", value: "3.64%", signal: "ok" },
        { label: "IORB", value: "3.65%", signal: "ok" },
        { label: "SRF", value: "3.75%", signal: "neutral" },
    ];

    const legendItems = [
        { label: "Near 0", description: "Equilibrium", color: "#6b7280" },
        { label: "Negative", description: "Liquidity Trap", color: "#ef4444" },
        { label: "Positive", description: "Credit Excess", color: "#22c55e" },
    ];
</script>

<div class="components-tab" class:dark={darkMode}>
    <h1>📦 Chart Components Validation</h1>
    <p class="subtitle">
        Testing new abstraction system: ChartCardV2, Signal primitives,
        seriesConfig
    </p>

    <!-- Section 1: Signal Primitives -->
    <section>
        <h2>Signal Primitives</h2>
        <div class="signals-grid">
            <div class="demo-box">
                <h3>SignalBadge</h3>
                <div class="row">
                    <SignalBadge state="bullish" />
                    <SignalBadge state="bearish" />
                    <SignalBadge state="neutral" />
                    <SignalBadge state="warning" value="11 bps" />
                    <SignalBadge state="ok" value="NORMAL" />
                    <SignalBadge state="danger" value="ALERT" />
                </div>
            </div>

            <div class="demo-box">
                <h3>SignalTable</h3>
                <SignalTable rows={tableRows} {darkMode} />
            </div>

            <div class="demo-box">
                <h3>SignalSummary</h3>
                <SignalSummary
                    value="-1.0 bps"
                    label="SOFR-IORB"
                    state="ok"
                    {darkMode}
                />
                <SignalSummary
                    value="+2.5%"
                    label="HY Spread"
                    state="warning"
                    {darkMode}
                />
            </div>

            <div class="demo-box">
                <h3>SignalLegend</h3>
                <SignalLegend
                    items={legendItems}
                    layout="vertical"
                    {darkMode}
                />
            </div>
        </div>
    </section>

    <!-- Section 2: ChartCardV2 Variants -->
    <section>
        <h2>ChartCardV2 Variants</h2>

        <div class="charts-grid">
            <!-- Variant 1: Basic with SignalBadge -->
            <ChartCardV2
                title="CLI Index"
                description="Credit Liquidity Index with badge"
                {darkMode}
                range={range1}
                onRangeChange={(r) => (range1 = r)}
            >
                <svelte:fragment slot="signal">
                    <SignalBadge
                        state="bullish"
                        value="72%"
                        label="Percentile"
                    />
                </svelte:fragment>
                <svelte:fragment slot="chart">
                    <Chart data={cliData} {darkMode} />
                </svelte:fragment>
            </ChartCardV2>

            <!-- Variant 2: With SignalTable in footer -->
            <ChartCardV2
                title="Fed Rate Corridor"
                description="SOFR vs floor/ceiling"
                {darkMode}
                range={range2}
                onRangeChange={(r) => (range2 = r)}
            >
                <svelte:fragment slot="signal">
                    <div class="badge-row">
                        <SignalBadge state="ok" value="NORMAL" />
                        <SignalBadge
                            state="warning"
                            value="-1.0 bps"
                            label="Spread"
                        />
                    </div>
                </svelte:fragment>
                <svelte:fragment slot="chart">
                    <Chart data={hyData} {darkMode} />
                </svelte:fragment>
                <svelte:fragment slot="footer">
                    <SignalTable rows={tableRows} compact {darkMode} />
                </svelte:fragment>
            </ChartCardV2>

            <!-- Variant 3: With SignalSummary and Legend -->
            <ChartCardV2
                title="CLI-GLI Divergence"
                description="Credit vs Global Liquidity coupling"
                {darkMode}
                range={range3}
                onRangeChange={(r) => (range3 = r)}
            >
                <svelte:fragment slot="signal">
                    <SignalLegend
                        items={legendItems}
                        layout="horizontal"
                        compact
                        {darkMode}
                    />
                </svelte:fragment>
                <svelte:fragment slot="chart">
                    <Chart data={cliData} {darkMode} />
                </svelte:fragment>
                <svelte:fragment slot="footer">
                    <SignalSummary
                        value="-0.42"
                        label="Current Value"
                        state="bearish"
                        {darkMode}
                    />
                </svelte:fragment>
            </ChartCardV2>
        </div>
    </section>

    <!-- Section 3: Series Config Test -->
    <section>
        <h2>Series Config Colors</h2>
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
        max-width: 1400px;
        margin: 0 auto;
    }

    .components-tab.dark {
        background: var(--bg-primary, #0f172a);
        color: var(--text-primary, #e2e8f0);
    }

    h1 {
        font-size: 1.5rem;
        margin-bottom: 8px;
    }
    .subtitle {
        opacity: 0.6;
        font-size: 0.875rem;
        margin-bottom: 32px;
    }
    h2 {
        font-size: 1.1rem;
        margin: 32px 0 16px;
        opacity: 0.8;
    }
    h3 {
        font-size: 0.8rem;
        margin-bottom: 12px;
        opacity: 0.6;
    }

    section {
        margin-bottom: 40px;
    }

    .signals-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 16px;
    }

    .demo-box {
        background: rgba(255, 255, 255, 0.03);
        padding: 16px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .badge-row {
        display: flex;
        gap: 8px;
    }

    .charts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        gap: 24px;
    }

    .color-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .color-chip {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 4px 10px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 4px;
        font-size: 0.7rem;
    }

    .swatch {
        width: 12px;
        height: 12px;
        border-radius: 2px;
    }

    .key {
        font-family: monospace;
        opacity: 0.8;
    }

    @media (max-width: 768px) {
        .charts-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
