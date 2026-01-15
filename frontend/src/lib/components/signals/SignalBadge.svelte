<!--
  SignalBadge.svelte
  
  A compact badge component for displaying signal states (bullish/bearish/neutral/etc.)
  
  Props:
  - state: "bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger"
  - value: string | number (optional, shown instead of state text if provided)
  - label: string (optional, shown before value)
  - size: "sm" | "md" | "lg"
  - showDot: boolean (show colored dot indicator)
  
  Usage:
  <SignalBadge state="bullish" />
  <SignalBadge state="warning" value="-1.0 bps" label="Spread" />
-->
<script>
    /** @type {"bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger"} */
    export let state = "neutral";

    /** @type {string | number | null} */
    export let value = null;

    /** @type {string | null} */
    export let label = null;

    /** @type {"sm" | "md" | "lg"} */
    export let size = "md";

    /** @type {boolean} */
    export let showDot = true;

    /** @type {boolean} */
    export let uppercase = true;

    // Display text: use value if provided, otherwise state name
    $: displayText = value !== null ? String(value) : state.toUpperCase();
</script>

<div class="signal-badge {state} {size}" class:uppercase>
    {#if showDot}
        <span class="dot"></span>
    {/if}
    {#if label}
        <span class="label">{label}</span>
    {/if}
    <span class="value">{displayText}</span>
</div>

<style>
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: 600;
        white-space: nowrap;
        transition: background-color 0.2s ease;
    }

    .uppercase .value {
        text-transform: uppercase;
    }

    /* Sizes */
    .signal-badge.sm {
        font-size: 0.65rem;
        padding: 2px 6px;
        gap: 4px;
    }

    .signal-badge.md {
        font-size: 0.75rem;
        padding: 4px 10px;
    }

    .signal-badge.lg {
        font-size: 0.875rem;
        padding: 6px 12px;
    }

    /* Dot indicator */
    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    .sm .dot {
        width: 6px;
        height: 6px;
    }

    .lg .dot {
        width: 10px;
        height: 10px;
    }

    /* Label styling */
    .label {
        opacity: 0.7;
        font-weight: 500;
    }

    /* State: Bullish */
    .signal-badge.bullish {
        background: var(--signal-bullish-bg, rgba(34, 197, 94, 0.15));
        color: var(--signal-bullish, #22c55e);
    }
    .signal-badge.bullish .dot {
        background: var(--signal-bullish, #22c55e);
    }

    /* State: Bearish */
    .signal-badge.bearish {
        background: var(--signal-bearish-bg, rgba(239, 68, 68, 0.15));
        color: var(--signal-bearish, #ef4444);
    }
    .signal-badge.bearish .dot {
        background: var(--signal-bearish, #ef4444);
    }

    /* State: Neutral */
    .signal-badge.neutral {
        background: var(--signal-neutral-bg, rgba(107, 114, 128, 0.15));
        color: var(--signal-neutral, #6b7280);
    }
    .signal-badge.neutral .dot {
        background: var(--signal-neutral, #6b7280);
    }

    /* State: Warning */
    .signal-badge.warning {
        background: var(--signal-warning-bg, rgba(245, 158, 11, 0.15));
        color: var(--signal-warning, #f59e0b);
    }
    .signal-badge.warning .dot {
        background: var(--signal-warning, #f59e0b);
    }

    /* State: OK */
    .signal-badge.ok {
        background: var(--signal-ok-bg, rgba(16, 185, 129, 0.15));
        color: var(--signal-ok, #10b981);
    }
    .signal-badge.ok .dot {
        background: var(--signal-ok, #10b981);
    }

    /* State: Danger */
    .signal-badge.danger {
        background: var(--signal-danger-bg, rgba(220, 38, 38, 0.15));
        color: var(--signal-danger, #dc2626);
    }
    .signal-badge.danger .dot {
        background: var(--signal-danger, #dc2626);
    }
</style>
