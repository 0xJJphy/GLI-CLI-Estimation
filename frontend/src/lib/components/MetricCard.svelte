<script>
    /**
     * MetricCard.svelte
     * Standardized component for displaying KPIs and metrics.
     * Supports "box" (card-like) and "flat" (compact) variants.
     */
    export let label = "";
    export let value = "";
    export let trend = ""; // Optional, e.g. "+1.2%"
    export let status = "neutral"; // "positive" | "negative" | "warning" | "neutral"
    export let variant = "box"; // "box" | "flat"
    export let size = "medium"; // "small" | "medium" | "large"
    export let darkMode = false;
    export let interactive = false;

    // Map status to semantic colors
    const statusColors = {
        positive: "var(--positive-color, #10b981)",
        negative: "var(--negative-color, #ef4444)",
        warning: "var(--warning-color, #f59e0b)",
        neutral: "var(--text-muted, #94a3b8)",
    };

    $: color = statusColors[status] || statusColors.neutral;
    $: isFlat = variant === "flat";
</script>

<div
    class="metric-card {variant} size-{size}"
    class:dark={darkMode}
    class:interactive
    class:status-active={status !== "neutral"}
    style="--status-color: {color}"
>
    {#if variant === "box"}
        <div class="label">{label}</div>
        <div class="value-group">
            <span class="value">{value}</span>
            {#if trend}
                <span class="trend" class:has-status={status !== "neutral"}>
                    {trend}
                </span>
            {/if}
        </div>
    {:else}
        <!-- Flat / Compact Variant -->
        <span class="label">{label}</span>
        <span class="value">{value}</span>
        {#if trend}
            <span class="trend">{trend}</span>
        {/if}
    {/if}
</div>

<style>
    .metric-card {
        display: flex;
        transition: all 0.2s ease;
    }

    /* Box Variant Styling */
    .metric-card.box {
        flex-direction: column;
        padding: 16px;
        background: var(--bg-secondary, #ffffff);
        border: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
        border-radius: 12px;
        gap: 8px;
    }

    .metric-card.box.dark {
        background: #111827;
        border-color: rgba(255, 255, 255, 0.05);
    }

    .metric-card.box.interactive:hover {
        transform: translateY(-2px);
        border-color: var(--status-color);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    /* Flat Variant Styling */
    .metric-card.flat {
        flex-direction: column;
        align-items: center;
        padding: 6px 12px;
        background: transparent;
        border: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
        border-radius: 6px;
        min-width: 60px;
    }

    .metric-card.flat.status-active {
        border-color: var(--status-color);
        background: color-mix(in srgb, var(--status-color) 10%, transparent);
    }

    /* Size Variations */
    .size-small.box {
        padding: 10px;
        gap: 4px;
    }
    .size-small .label {
        font-size: 0.7rem;
    }
    .size-small .value {
        font-size: 1rem;
    }

    .size-large.box {
        padding: 24px;
        gap: 12px;
    }
    .size-large .label {
        font-size: 1rem;
    }
    .size-large .value {
        font-size: 2.5rem;
    }

    /* Parts Styling */
    .label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-muted, #64748b);
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }

    .value-group {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }

    .value {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary, #1e293b);
    }

    .metric-card.dark .value {
        color: #f3f4f6;
    }

    .trend {
        font-size: 0.85rem;
        font-weight: 600;
    }

    .status-active .value,
    .status-active .trend.has-status {
        color: var(--status-color);
    }

    /* Flat specific parts overrides */
    .flat .label {
        font-size: 0.65rem;
        margin-bottom: 2px;
    }

    .flat .value {
        font-size: 0.9rem;
    }

    .flat.status-active .value {
        color: var(--status-color);
    }
</style>
