<script>
    /**
     * ChartCard.svelte
     * Reusable composite component for chart display cards.
     * Combines: header, time range controls, description, chart, and optional footer.
     */
    import Chart from "./Chart.svelte";
    import LightweightChart from "./LightweightChart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import Dropdown from "./Dropdown.svelte";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    // --- Required Props ---
    /** Chart title displayed in header */
    export let title = "";

    /** Chart data for Plotly or LightweightChart */
    export let data = [];

    /** Dark mode toggle */
    export let darkMode = false;

    // --- Optional Props ---
    /** Chart description text below title */
    export let description = "";

    /** Current time range selection */
    export let selectedRange = "ALL";

    /** Callback when range changes - parent must update data reactively */
    export let onRangeChange = () => {};

    /** Available time range options */
    export let ranges = ["1M", "3M", "6M", "1Y", "3Y", "5Y", "ALL"];

    /** Whether to show time range selector */
    export let showRangeSelector = true;

    /** Whether to show download button */
    export let showDownload = true;

    /** Card style: "normal" or "wide" (full width) */
    export let cardStyle = "normal";

    /** Chart height: "short", "normal", or custom CSS value */
    export let chartHeight = "normal";

    /** Chart type: "plotly" or "lightweight" */
    export let chartType = "plotly";

    /** For Plotly: custom layout options */
    export let layout = {};

    /** For Plotly: background shapes (e.g., regime shading) */
    export let shapes = [];

    /** For LightweightChart: log scale */
    export let logScale = false;

    /** Download filename prefix */
    export let downloadName = "";

    /** Last update date to display */
    export let lastDate = "";

    /** Custom dropdown options (for mode selectors) */
    export let dropdownOptions = null;

    /** Current dropdown value */
    export let dropdownValue = null;

    /** Dropdown change callback */
    export let onDropdownChange = null;

    // Card container reference for download
    let cardContainer;

    // Handle download
    function handleDownload() {
        downloadCardAsImage(
            cardContainer,
            downloadName || title.toLowerCase().replace(/\s+/g, "_"),
        );
    }

    // Determine chart height class
    $: heightClass =
        chartHeight === "short" ? "short" : chartHeight === "normal" ? "" : "";
    $: customHeight =
        chartHeight !== "short" && chartHeight !== "normal"
            ? chartHeight
            : null;
</script>

<div
    class="chart-card"
    class:wide={cardStyle === "wide"}
    bind:this={cardContainer}
>
    <div class="chart-header">
        <h3>{title}</h3>
        <div class="header-controls">
            {#if dropdownOptions && onDropdownChange}
                <Dropdown
                    options={dropdownOptions}
                    value={dropdownValue}
                    onSelect={onDropdownChange}
                    {darkMode}
                    small={true}
                />
            {/if}
            {#if showRangeSelector}
                <TimeRangeSelector {selectedRange} {onRangeChange} {ranges} />
            {/if}
            {#if lastDate}
                <span class="last-date">{lastDate}</span>
            {/if}
            {#if showDownload}
                <button
                    class="download-btn"
                    title="Download Chart"
                    on:click={handleDownload}
                    aria-label="Download chart as image"
                >
                    📥
                </button>
            {/if}
        </div>
    </div>

    {#if description}
        <p class="chart-description">{description}</p>
    {/if}

    <div
        class="chart-content"
        class:short={chartHeight === "short"}
        style={customHeight ? `height: ${customHeight}` : ""}
    >
        {#if chartType === "plotly"}
            <Chart
                {darkMode}
                {data}
                {layout}
                {shapes}
                {cardContainer}
                cardTitle={downloadName || title}
            />
        {:else}
            <LightweightChart {darkMode} {data} {title} {logScale} />
        {/if}
    </div>

    <!-- Optional slot for footer content (ROC indicators, etc.) -->
    <slot name="footer"></slot>
</div>

<style>
    .chart-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        box-shadow: var(--card-shadow, 0 1px 3px rgba(0, 0, 0, 0.1));
        border: 1px solid var(--border-color, rgba(255, 255, 255, 0.05));
    }

    .chart-card.wide {
        grid-column: 1 / -1;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .chart-header h3 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .header-controls {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .chart-description {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin: 0;
        line-height: 1.4;
    }

    .chart-content {
        min-height: 280px;
        flex: 1;
    }

    .chart-content.short {
        min-height: 200px;
    }

    .last-date {
        font-size: 0.75rem;
        color: var(--text-muted);
        opacity: 0.7;
    }

    .download-btn {
        background: transparent;
        border: 1px solid var(--border-color, rgba(255, 255, 255, 0.1));
        border-radius: 6px;
        padding: 0.25rem 0.5rem;
        cursor: pointer;
        font-size: 0.875rem;
        transition: all 0.2s ease;
        color: var(--text-primary);
    }

    .download-btn:hover {
        background: var(--bg-tertiary);
        transform: translateY(-1px);
    }

    /* Responsive */
    @media (max-width: 768px) {
        .chart-header {
            flex-direction: column;
            align-items: flex-start;
        }

        .header-controls {
            width: 100%;
            justify-content: flex-start;
        }
    }
</style>
