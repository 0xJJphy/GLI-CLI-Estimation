<!--
  SignalLegend.svelte
  
  A legend component with colored indicators and descriptions.
  Used for regime explanations like CLI-GLI Divergence.
  
  Props:
  - items: Array<{ label, description?, color, state? }>
  - layout: "horizontal" | "vertical"
  - compact: boolean
  
  Usage:
  <SignalLegend items={[
    { label: "Near 0", description: "Equilibrium", color: "#6b7280" },
    { label: "Negative", description: "Liquidity Trap", color: "#ef4444" },
    { label: "Positive", description: "Credit Excess", color: "#22c55e" }
  ]} />
-->
<script>
    /**
     * @typedef {Object} LegendItem
     * @property {string} label - Short label
     * @property {string} [description] - Longer description
     * @property {string} [color] - Custom color (hex or CSS variable)
     * @property {string} [state] - Signal state (alternative to color)
     */

    /** @type {LegendItem[]} */
    export let items = [];

    /** @type {"horizontal" | "vertical"} */
    export let layout = "horizontal";

    /** @type {boolean} */
    export let compact = false;

    /** @type {boolean} */
    export let darkMode = false;

    // State to color mapping
    const stateColors = {
        bullish: "var(--signal-bullish, #22c55e)",
        bearish: "var(--signal-bearish, #ef4444)",
        neutral: "var(--signal-neutral, #6b7280)",
        warning: "var(--signal-warning, #f59e0b)",
        ok: "var(--signal-ok, #10b981)",
        danger: "var(--signal-danger, #dc2626)",
    };

    function getItemColor(item) {
        if (item.color) return item.color;
        if (item.state) return stateColors[item.state] || stateColors.neutral;
        return stateColors.neutral;
    }
</script>

<div class="signal-legend {layout}" class:compact class:dark={darkMode}>
    {#each items as item}
        <div class="legend-item">
            <span class="color-box" style:background={getItemColor(item)}
            ></span>
            <div class="text">
                <span class="label" style:color={getItemColor(item)}
                    >{item.label}</span
                >
                {#if item.description}
                    <span class="description">{item.description}</span>
                {/if}
            </div>
        </div>
    {/each}
</div>

<style>
    .signal-legend {
        display: flex;
        gap: 16px;
    }

    .signal-legend.vertical {
        flex-direction: column;
        gap: 8px;
    }

    .signal-legend.horizontal {
        flex-wrap: wrap;
    }

    .legend-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    .color-box {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        flex-shrink: 0;
        margin-top: 2px;
    }

    .compact .color-box {
        width: 10px;
        height: 10px;
    }

    .text {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .signal-legend.horizontal .text {
        flex-direction: row;
        gap: 6px;
        align-items: baseline;
    }

    .label {
        font-size: 0.75rem;
        font-weight: 600;
    }

    .compact .label {
        font-size: 0.7rem;
    }

    .description {
        font-size: 0.7rem;
        opacity: 0.7;
    }

    .compact .description {
        font-size: 0.65rem;
    }

    /* Dark mode adjustments */
    .dark .description {
        color: #94a3b8;
    }
</style>
