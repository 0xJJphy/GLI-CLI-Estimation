<!--
  SignalSummary.svelte
  
  A boxed summary component for displaying a highlighted metric with signal status.
  Used for prominent displays like "SOFR-IORB: -1.0 bps OK"
  
  Props:
  - value: string | number (the main value to display)
  - label: string (description of the value)
  - state: signal state
  - description: string (optional additional text)
  
  Usage:
  <SignalSummary value="-1.0 bps" label="SOFR-IORB" state="ok" />
-->
<script>
    /** @type {string | number} */
    export let value = "";

    /** @type {string} */
    export let label = "";

    /** @type {"bullish" | "bearish" | "neutral" | "warning" | "ok" | "danger"} */
    export let state = "neutral";

    /** @type {string} */
    export let description = "";

    /** @type {boolean} */
    export let darkMode = false;

    /** @type {"horizontal" | "vertical"} */
    export let layout = "horizontal";
</script>

<div class="signal-summary {state} {layout}" class:dark={darkMode}>
    <div class="content">
        <span class="value">{value}</span>
        <span class="label">{label}</span>
    </div>
    <div class="status">
        <span class="dot"></span>
        <span class="state-text">{state.toUpperCase()}</span>
    </div>
    {#if description}
        <p class="description">{description}</p>
    {/if}
</div>

<style>
    .signal-summary {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid;
        background: rgba(0, 0, 0, 0.2);
    }

    .signal-summary.vertical {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }

    .content {
        display: flex;
        align-items: baseline;
        gap: 8px;
    }

    .value {
        font-size: 1.1rem;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
    }

    .label {
        font-size: 0.75rem;
        opacity: 0.7;
    }

    .status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    .description {
        font-size: 0.7rem;
        opacity: 0.6;
        margin: 0;
        width: 100%;
    }

    /* State: Bullish */
    .signal-summary.bullish {
        border-color: var(--signal-bullish, #22c55e);
        background: var(--signal-bullish-bg, rgba(34, 197, 94, 0.1));
    }
    .signal-summary.bullish .value,
    .signal-summary.bullish .state-text {
        color: var(--signal-bullish, #22c55e);
    }
    .signal-summary.bullish .dot {
        background: var(--signal-bullish, #22c55e);
    }

    /* State: Bearish */
    .signal-summary.bearish {
        border-color: var(--signal-bearish, #ef4444);
        background: var(--signal-bearish-bg, rgba(239, 68, 68, 0.1));
    }
    .signal-summary.bearish .value,
    .signal-summary.bearish .state-text {
        color: var(--signal-bearish, #ef4444);
    }
    .signal-summary.bearish .dot {
        background: var(--signal-bearish, #ef4444);
    }

    /* State: Neutral */
    .signal-summary.neutral {
        border-color: var(--signal-neutral, #6b7280);
        background: var(--signal-neutral-bg, rgba(107, 114, 128, 0.1));
    }
    .signal-summary.neutral .value,
    .signal-summary.neutral .state-text {
        color: var(--signal-neutral, #6b7280);
    }
    .signal-summary.neutral .dot {
        background: var(--signal-neutral, #6b7280);
    }

    /* State: Warning */
    .signal-summary.warning {
        border-color: var(--signal-warning, #f59e0b);
        background: var(--signal-warning-bg, rgba(245, 158, 11, 0.1));
    }
    .signal-summary.warning .value,
    .signal-summary.warning .state-text {
        color: var(--signal-warning, #f59e0b);
    }
    .signal-summary.warning .dot {
        background: var(--signal-warning, #f59e0b);
    }

    /* State: OK */
    .signal-summary.ok {
        border-color: var(--signal-ok, #10b981);
        background: var(--signal-ok-bg, rgba(16, 185, 129, 0.1));
    }
    .signal-summary.ok .value,
    .signal-summary.ok .state-text {
        color: var(--signal-ok, #10b981);
    }
    .signal-summary.ok .dot {
        background: var(--signal-ok, #10b981);
    }

    /* State: Danger */
    .signal-summary.danger {
        border-color: var(--signal-danger, #dc2626);
        background: var(--signal-danger-bg, rgba(220, 38, 38, 0.1));
    }
    .signal-summary.danger .value,
    .signal-summary.danger .state-text {
        color: var(--signal-danger, #dc2626);
    }
    .signal-summary.danger .dot {
        background: var(--signal-danger, #dc2626);
    }
</style>
