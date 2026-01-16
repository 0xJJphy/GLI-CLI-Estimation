<!--
  ChartCardV2.svelte
  
  A composable chart card container with slots for flexible layouts.
  
  Slots:
  - header: Custom header content (default: title + description)
  - controls: Custom controls (default: TimeRangeSelector)
  - signal: Signal indicators area (no default)
  - chart: The chart content (required)
  - footer: Footer content (no default)
  
  Props:
  - title: string
  - description: string
  - darkMode: boolean
  - showDownload: boolean
  - range: current time range
  - onRangeChange: callback for range changes
  
  Usage:
  <ChartCardV2 title="VIX" {darkMode}>
    <svelte:fragment slot="signal">
      <SignalBadge state="bullish" />
    </svelte:fragment>
    <svelte:fragment slot="chart">
      <Chart data={vixData} />
    </svelte:fragment>
  </ChartCardV2>
-->
<script>
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    /** @type {string} */
    export let title = "";

    /** @type {string} */
    export let description = "";

    /** @type {boolean} */
    export let darkMode = false;

    /** @type {boolean} */
    export let showDownload = true;

    /** @type {string} */
    export let range = "ALL";

    /** @type {(range: string) => void} */
    export let onRangeChange = () => {};

    /** @type {boolean} */
    export let showRangeSelector = true;

    /** @type {string} */
    export let lastDate = "";

    /** @type {string} */
    export let cardId = "";

    /** @type {HTMLElement} */
    let cardElement;

    // Handle range change
    function handleRangeChange(newRange) {
        range = newRange;
        onRangeChange(newRange);
    }

    // Download functionality
    async function handleDownload() {
        if (cardElement) {
            await downloadCardAsImage(cardElement, title || cardId || "chart");
        }
    }

    // Check if slots are provided
    let hasSignalSlot = false;
    let hasFooterSlot = false;
    let hasControlsSlot = false;
    let hasHeaderSlot = false;
</script>

<div
    class="chart-card-v2"
    class:dark={darkMode}
    bind:this={cardElement}
    data-card-id={cardId}
>
    <!-- Header Section -->
    <div class="card-header">
        <div class="header-left">
            <slot name="header">
                {#if title}
                    <h3 class="title">{title}</h3>
                {/if}
            </slot>
        </div>

        <div class="header-right">
            <!-- Controls Slot or Default Range Selector -->
            <slot name="controls">
                {#if showRangeSelector}
                    <TimeRangeSelector
                        selectedRange={range}
                        onRangeChange={handleRangeChange}
                    />
                {/if}
            </slot>

            {#if lastDate}
                <span class="last-date">Last: {lastDate}</span>
            {/if}

            {#if showDownload}
                <button
                    class="download-btn"
                    on:click={handleDownload}
                    aria-label="Download chart"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                    >
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7,10 12,15 17,10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                </button>
            {/if}
        </div>
    </div>

    <!-- Description (if provided) -->
    {#if description}
        <p class="description">{description}</p>
    {/if}

    <!-- Signal Slot -->
    <slot name="signal"></slot>

    <!-- Chart Content (required) -->
    <div class="chart-container">
        <slot name="chart">
            <div class="placeholder">No chart provided</div>
        </slot>
    </div>

    <!-- Footer Slot -->
    <div class="footer-wrapper">
        <slot name="footer"></slot>
    </div>
</div>

<style>
    .chart-card-v2 {
        background: var(--bg-secondary, #ffffff);
        border: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
        border-radius: var(--card-border-radius, 12px);
        padding: var(--card-padding, 1.25rem);
        display: flex;
        flex-direction: column;
        gap: 12px;
        box-shadow: var(--card-shadow, 0 1px 3px rgba(0, 0, 0, 0.1));
    }

    .chart-card-v2.dark {
        background: var(--bg-secondary);
        border-color: var(--border-color, rgba(255, 255, 255, 0.05));
    }

    /* Header */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 1;
        min-width: 0;
    }

    .header-right {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-shrink: 0;
    }

    .title {
        margin: 0;
        font-size: 0.95rem;
        font-weight: 600;
        color: inherit;
    }

    .description {
        margin: 0;
        font-size: 0.75rem;
        opacity: 0.7;
        line-height: 1.4;
    }

    .last-date {
        font-size: 0.7rem;
        opacity: 0.6;
        white-space: nowrap;
    }

    /* Download button */
    .download-btn {
        background: transparent;
        border: none;
        padding: 6px;
        cursor: pointer;
        opacity: 0.6;
        transition: opacity 0.2s;
        color: inherit;
        border-radius: 4px;
    }

    .download-btn:hover {
        opacity: 1;
        background: rgba(255, 255, 255, 0.1);
    }

    /* Chart container */
    .chart-container {
        min-height: 200px;
        position: relative;
    }

    .placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        opacity: 0.5;
        font-size: 0.875rem;
    }

    /* Footer wrapper */
    .footer-wrapper {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.06));
    }

    .footer-wrapper:empty {
        display: none;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .card-header {
            flex-direction: column;
            align-items: flex-start;
        }

        .header-right {
            width: 100%;
            justify-content: flex-start;
        }
    }
</style>
