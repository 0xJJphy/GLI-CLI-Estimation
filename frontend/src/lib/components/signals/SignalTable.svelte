<!--
  SignalTable.svelte
  
  A table component for displaying multiple metrics with optional signal status.
  
  Props:
  - rows: Array<{ label, value, signal?, color? }>
  - columns: Array<string> (header labels, optional)
  - compact: boolean
  - showHeader: boolean
  
  Usage:
  <SignalTable rows={[
    { label: "SOFR", value: "3.64%", signal: "ok" },
    { label: "IORB", value: "3.65%", signal: "ok" }
  ]} />
-->
<script>
    /**
     * @typedef {Object} TableRow
     * @property {string} label - Row label
     * @property {string|number} value - Row value
     * @property {string} [signal] - Optional signal state
     * @property {string} [color] - Optional custom color
     */

    /** @type {TableRow[]} */
    export let rows = [];

    /** @type {string[]} */
    export let columns = ["Indicator", "Value", "Status"];

    /** @type {boolean} */
    export let compact = false;

    /** @type {boolean} */
    export let showHeader = false;

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

    function getSignalColor(signal) {
        return stateColors[signal] || stateColors.neutral;
    }

    function formatSignalText(signal) {
        if (!signal) return "";
        return signal.toUpperCase();
    }
</script>

<div class="signal-table" class:compact class:dark={darkMode}>
    {#if showHeader && columns.length > 0}
        <div class="table-header">
            {#each columns as col}
                <span class="header-cell">{col}</span>
            {/each}
        </div>
    {/if}

    <div class="table-body">
        {#each rows as row}
            <div class="table-row">
                <span class="cell label" style:color={row.color || "inherit"}>
                    {row.label}
                </span>
                <span class="cell value">
                    {row.value}
                </span>
                {#if row.signal}
                    <span
                        class="cell status"
                        style:color={getSignalColor(row.signal)}
                    >
                        <span
                            class="dot"
                            style:background={getSignalColor(row.signal)}
                        ></span>
                        {formatSignalText(row.signal)}
                    </span>
                {/if}
            </div>
        {/each}
    </div>
</div>

<style>
    .signal-table {
        width: 100%;
        font-size: 0.75rem;
    }

    .table-header {
        display: flex;
        gap: 16px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.65rem;
        opacity: 0.7;
    }

    .header-cell {
        flex: 1;
    }

    .table-body {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .table-row {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 6px 0;
    }

    .compact .table-row {
        padding: 4px 0;
        gap: 12px;
    }

    .cell {
        flex: 1;
    }

    .cell.label {
        font-weight: 500;
    }

    .cell.value {
        font-family: "JetBrains Mono", monospace;
        text-align: right;
    }

    .cell.status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 600;
        text-align: right;
        justify-content: flex-end;
    }

    .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }

    /* Dark mode */
    .dark .table-header {
        border-color: rgba(255, 255, 255, 0.05);
    }

    /* Compact mode */
    .compact {
        font-size: 0.7rem;
    }

    .compact .cell.status {
        font-size: 0.65rem;
    }
</style>
