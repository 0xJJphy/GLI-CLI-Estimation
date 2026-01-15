<!--
  ChartDemo.svelte - Visual test for new chart components
-->
<script>
    import ChartCardV2 from "./ChartCardV2.svelte";
    import {
        SignalBadge,
        SignalTable,
        SignalSummary,
        SignalLegend,
    } from "./signals";

    export let darkMode = true;

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

<div class="demo" class:dark={darkMode}>
    <h1>Chart Component Demo</h1>

    <section>
        <h2>SignalBadge</h2>
        <div class="row">
            <SignalBadge state="bullish" />
            <SignalBadge state="bearish" />
            <SignalBadge state="neutral" />
            <SignalBadge state="warning" value="11 bps" />
            <SignalBadge state="ok" value="NORMAL" />
        </div>
    </section>

    <section>
        <h2>SignalTable</h2>
        <SignalTable rows={tableRows} {darkMode} />
    </section>

    <section>
        <h2>SignalSummary</h2>
        <div class="row">
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
    </section>

    <section>
        <h2>SignalLegend</h2>
        <SignalLegend items={legendItems} layout="horizontal" {darkMode} />
    </section>

    <section>
        <h2>ChartCardV2 with Signals</h2>
        <ChartCardV2
            title="Fed Rate Corridor"
            description="SOFR vs bounds"
            {darkMode}
        >
            <svelte:fragment slot="signal">
                <SignalBadge state="ok" value="NORMAL" />
            </svelte:fragment>
            <svelte:fragment slot="chart">
                <div class="placeholder">Chart Area</div>
            </svelte:fragment>
            <svelte:fragment slot="footer">
                <SignalTable rows={tableRows} compact {darkMode} />
            </svelte:fragment>
        </ChartCardV2>
    </section>
</div>

<style>
    .demo {
        padding: 24px;
        max-width: 800px;
    }
    .demo.dark {
        background: #0f172a;
        color: #e2e8f0;
    }
    h1 {
        font-size: 1.25rem;
        margin-bottom: 24px;
    }
    h2 {
        font-size: 0.875rem;
        opacity: 0.6;
        margin: 24px 0 12px;
    }
    section {
        margin-bottom: 24px;
    }
    .row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .placeholder {
        height: 150px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        opacity: 0.5;
    }
</style>
