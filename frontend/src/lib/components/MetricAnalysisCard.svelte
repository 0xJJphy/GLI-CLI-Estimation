<script>
    /**
     * MetricAnalysisCard.svelte
     * A powerful, standardized card for quantitative metric analysis.
     * Supports three view modes: Raw, Z-Score, and Percentile.
     * Includes time range selection, download, and status indicators.
     */
    import Chart from "./Chart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import { downloadCardAsImage } from "../utils/downloadCard.js";
    import {
        createZScoreBands,
        createPercentileBands,
    } from "../utils/chartHelpers.js";

    // Props
    export let title = "";
    export let description = "";
    export let rawData = [];
    export let zData = [];
    export let pctData = [];
    export let range = "ALL";
    export let viewMode = "zscore"; // 'raw', 'zscore', 'percentile'
    export let lastDate = "N/A";

    /** @type {any} */
    export let signal = null;

    export let translations = {};
    export let darkMode = false;
    export let cardId = "metric_chart";
    export let height = "300px";

    // Percentile config defaults
    export let pBullish = 30;
    export let pBearish = 70;
    export let pInvert = false;

    // Callbacks
    export let onRangeChange = (r) => {};
    export let onViewModeChange = (m) => {};

    let cardRef;

    // Reactive layout based on viewMode
    $: chartData =
        viewMode === "raw"
            ? rawData
            : viewMode === "percentile"
              ? pctData
              : zData;

    $: chartLayout =
        viewMode === "raw"
            ? { yaxis: { autorange: true } }
            : viewMode === "percentile"
              ? {
                    shapes: createPercentileBands(darkMode, {
                        bullishPct: pBullish,
                        bearishPct: pBearish,
                        invert: pInvert,
                    }),
                    yaxis: { range: [-5, 105], title: "Percentile" },
                }
              : {
                    shapes: createZScoreBands(darkMode),
                    yaxis: { title: "Z-Score" },
                };

    function getStatusLabel(state) {
        if (!state) return translations.status_neutral || "NEUTRAL";
        const key = `status_${state.toLowerCase()}`;
        return translations[key] || state.toUpperCase();
    }
</script>

<div class="chart-card" bind:this={cardRef}>
    <div class="chart-header">
        <h3>{title}</h3>
        <div class="header-controls">
            <button
                class="download-card-btn"
                title="Download Full Card"
                on:click={() => downloadCardAsImage(cardRef, cardId)}
            >
                📷
            </button>

            <div class="view-mode-toggle">
                {#if zData && zData.length > 0}
                    <button
                        class:active={viewMode === "zscore"}
                        on:click={() => onViewModeChange("zscore")}
                        title="Z-Score">Z</button
                    >
                {/if}
                {#if pctData && pctData.length > 0}
                    <button
                        class:active={viewMode === "percentile"}
                        on:click={() => onViewModeChange("percentile")}
                        title="Percentile">%</button
                    >
                {/if}
                <button
                    class:active={viewMode === "raw"}
                    on:click={() => onViewModeChange("raw")}
                    title="Raw Values">📊</button
                >
            </div>

            <TimeRangeSelector selectedRange={range} {onRangeChange} />
            <span class="last-date">
                {translations.last_data || "Last Data:"}
                {lastDate}
            </span>
        </div>
    </div>

    {#if description}
        <p class="chart-description">{description}</p>
    {/if}

    <div class="chart-content" style="height: {height};">
        <Chart
            {darkMode}
            data={chartData}
            layout={chartLayout}
            cardContainer={cardRef}
            cardTitle={cardId}
        />
    </div>

    {#if signal && signal.latest}
        {@const s = signal.latest}
        <div class="metrics-section">
            <div class="signal-item">
                <div class="signal-label">
                    {translations.signal_status || "Signal Status"}
                </div>
                <div class="signal-status text-{s.state}">
                    <span class="signal-dot"></span>
                    {getStatusLabel(s.state)}
                </div>
                <div class="signal-value">
                    {translations.current || "Current"}:
                    <b>{s.value?.toFixed(2)}</b>
                    {#if s.percentile !== undefined}
                        | {translations.percentile || "Percentile"}:
                        <b>P{s.percentile?.toFixed(0)}</b>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        display: flex;
        flex-direction: column;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }

    .chart-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .header-controls {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 8px;
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
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }

    .download-card-btn {
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 16px;
        opacity: 0.6;
        transition: opacity 0.2s;
    }

    .download-card-btn:hover {
        opacity: 1;
    }

    .last-date {
        font-size: 11px;
        color: var(--text-muted);
    }

    .chart-description {
        font-size: 13px;
        color: var(--text-muted);
        margin: 0 0 16px 0;
        line-height: 1.4;
    }

    .chart-content {
        width: 100%;
    }

    .metrics-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color);
    }

    .signal-item {
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 16px;
        background: rgba(0, 0, 0, 0.05);
        padding: 10px 16px;
        border-radius: 8px;
    }

    .signal-label {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-muted);
    }

    .signal-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 800;
        text-transform: uppercase;
        font-size: 13px;
    }

    .signal-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }

    .signal-value {
        font-size: 12px;
        color: var(--text-muted);
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
    .text-warning {
        color: #f59e0b;
    }

    @media (max-width: 768px) {
        .signal-item {
            grid-template-columns: 1fr;
            text-align: center;
        }
        .signal-status {
            justify-content: center;
        }
    }
</style>
