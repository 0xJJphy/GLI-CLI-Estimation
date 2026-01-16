<!--
  SignalLegend.svelte
  
  A legend component with colored indicators and descriptions.
  Supports interactive click-to-toggle for showing/hiding chart series.
  
  Props:
  - items: Array<{ key, label, description?, color, state?, lineStyle? }>
  - layout: "horizontal" | "vertical"
  - compact: boolean
  - interactive: boolean - Enable click-to-toggle
  - visibleKeys: string[] - Which keys are currently visible (bindable)
  - onToggle: (key: string) => void - Callback when item clicked
  
  Usage:
  <SignalLegend 
    items={[
      { key: "SOFR", label: "SOFR", color: "#38bdf8", lineStyle: "solid" },
      { key: "IORB", label: "IORB (Floor)", color: "#10b981", lineStyle: "dash" }
    ]}
    interactive
    visibleKeys={["SOFR", "IORB"]}
    onToggle={(key) => toggleVisibility(key)}
  />
-->
<script>
    /**
     * @typedef {Object} LegendItem
     * @property {string} key - Unique identifier for toggling
     * @property {string} label - Short label
     * @property {string} [description] - Longer description
     * @property {string} [color] - Custom color (hex or CSS variable)
     * @property {string} [state] - Signal state (alternative to color)
     * @property {"solid" | "dash" | "dot"} [lineStyle] - Line style indicator
     */

    /** @type {LegendItem[]} */
    export let items = [];

    /** @type {"horizontal" | "vertical"} */
    export let layout = "horizontal";

    /** @type {boolean} */
    export let compact = false;

    /** @type {boolean} */
    export let darkMode = false;

    /** @type {boolean} */
    export let interactive = false;

    /** @type {string[]} */
    export let visibleKeys = [];

    /** @type {(key: string) => void} */
    export let onToggle = () => {};

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

    function isVisible(item) {
        if (!interactive) return true;
        if (visibleKeys.length === 0) return true; // All visible by default
        return visibleKeys.includes(item.key || item.label);
    }

    function handleClick(item) {
        if (!interactive) return;
        const key = item.key || item.label;
        onToggle(key);
    }

    function getLineStyleClass(style) {
        if (style === "dash") return "line-dash";
        if (style === "dot") return "line-dot";
        return "line-solid";
    }
</script>

<div
    class="signal-legend {layout}"
    class:compact
    class:dark={darkMode}
    class:interactive
>
    {#each items as item}
        <button
            class="legend-item"
            class:hidden={!isVisible(item)}
            on:click={() => handleClick(item)}
            disabled={!interactive}
            type="button"
        >
            {#if item.lineStyle}
                <span
                    class="line-indicator {getLineStyleClass(item.lineStyle)}"
                    style:background={item.lineStyle === "solid"
                        ? getItemColor(item)
                        : "transparent"}
                    style:border-color={getItemColor(item)}
                ></span>
            {:else}
                <span class="color-box" style:background={getItemColor(item)}
                ></span>
            {/if}
            <div class="text">
                <span
                    class="label"
                    style:color={isVisible(item)
                        ? getItemColor(item)
                        : "inherit"}
                >
                    {item.label}
                </span>
                {#if item.description}
                    <span class="description">{item.description}</span>
                {/if}
            </div>
        </button>
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
        align-items: center;
        gap: 8px;
        background: transparent;
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
        cursor: default;
        font-family: inherit;
        font-size: inherit;
        color: inherit;
        transition: all 0.2s ease;
    }

    .interactive .legend-item {
        cursor: pointer;
    }

    .interactive .legend-item:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .legend-item.hidden {
        opacity: 0.4;
    }

    .legend-item.hidden .label {
        text-decoration: line-through;
        color: var(--text-muted, #6b7280) !important;
    }

    .color-box {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        flex-shrink: 0;
    }

    .line-indicator {
        width: 20px;
        height: 3px;
        flex-shrink: 0;
        border-radius: 1px;
    }

    .line-indicator.line-dash {
        background: transparent;
        border-top: 2px dashed;
    }

    .line-indicator.line-dot {
        background: transparent;
        border-top: 2px dotted;
    }

    .compact .color-box {
        width: 10px;
        height: 10px;
    }

    .compact .line-indicator {
        width: 16px;
    }

    .text {
        display: flex;
        flex-direction: column;
        gap: 2px;
        text-align: left;
    }

    .signal-legend.horizontal .text {
        flex-direction: row;
        gap: 6px;
        align-items: baseline;
    }

    .label {
        font-size: 0.75rem;
        font-weight: 600;
        transition: color 0.2s ease;
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
