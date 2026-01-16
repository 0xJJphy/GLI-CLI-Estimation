<!--
  SignalTable.svelte
  
  A flexible table component for displaying metrics with configurable columns.
  Uses HTML table with rowspan for integrated signal display (like RiskModelTab).
  
  Props:
  - columns: Array<{ key, label, width?, align?, format?, color? }>
  - rows: Array<{ [key]: value, _signal?, _color? }>
  - summary: { value, label, signal?, size? } - Optional summary in last column (rowspan)
  - showHeader: boolean
  - compact: boolean
  
  Usage:
  <SignalTable
    columns={[
      { key: "rate", label: "RATE" },
      { key: "value", label: "VALUE" }
    ]}
    rows={[
      { rate: "SOFR", value: 3.64, _color: "#38bdf8" }
    ]}
    summary={{ value: "-1.0 bps", label: "SOFR-IORB", signal: "ok" }}
    showHeader
  />
-->
<script context="module">
    /**
     * @typedef {Object} TableColumn
     * @property {string} key
     * @property {string} label
     * @property {string} [width]
     * @property {"left" | "center" | "right"} [align]
     * @property {"text" | "percent" | "bps" | "currency"} [format]
     */

    /**
     * @typedef {Object} SummaryBox
     * @property {string|number} value
     * @property {string} label
     * @property {string} [signal]
     * @property {"small" | "medium" | "large"} [size]
     */
</script>

<script>
    /** @type {TableColumn[]} */
    export let columns = [];

    /** @type {any[]} */
    export let rows = [];

    /** @type {SummaryBox|null} */
    export let summary = null;

    /** @type {boolean} */
    export let showHeader = false;

    /** @type {boolean} */
    export let compact = false;

    /** @type {boolean} */
    export let darkMode = false;

    const stateColors = {
        bullish: "#22c55e",
        bearish: "#ef4444",
        neutral: "#6b7280",
        warning: "#f59e0b",
        ok: "#10b981",
        danger: "#dc2626",
    };

    function getSignalColor(signal) {
        return stateColors[signal] || stateColors.neutral;
    }

    function formatValue(value, format) {
        if (value === undefined || value === null || value === "") return "";
        switch (format) {
            case "percent":
                return typeof value === "number"
                    ? `${value.toFixed(2)}%`
                    : value;
            case "bps":
                return typeof value === "number"
                    ? `${value.toFixed(1)} bps`
                    : value;
            case "currency":
                return typeof value === "number"
                    ? `$${value.toFixed(2)}`
                    : value;
            default:
                return String(value);
        }
    }

    function getColumnStyle(col, isHeader = false) {
        const styles = [];
        if (col.width) styles.push(`width: ${col.width}`);
        if (col.align) styles.push(`text-align: ${col.align}`);
        return styles.join("; ");
    }
</script>

<table class="signal-table" class:compact class:dark={darkMode}>
    {#if showHeader && columns.length > 0}
        <thead>
            <tr>
                {#each columns as col}
                    <th style={getColumnStyle(col, true)}>{col.label}</th>
                {/each}
                {#if summary}
                    <th class="signal-col-header">SPREAD/SIGNAL</th>
                {/if}
            </tr>
        </thead>
    {/if}
    <tbody>
        {#each rows as row, rowIndex}
            <tr class="table-row">
                {#each columns as col, colIndex}
                    <td
                        style="{getColumnStyle(col)}; {row._color &&
                        colIndex === 0
                            ? `color: ${row._color}; font-weight: 600;`
                            : ''}"
                    >
                        {formatValue(row[col.key], col.format)}
                    </td>
                {/each}

                {#if summary && rowIndex === 0}
                    <td
                        class="signal-cell {summary.signal || 'neutral'}"
                        rowspan={rows.length}
                    >
                        <div class="signal-content">
                            <div
                                class="signal-value"
                                style:color={getSignalColor(summary.signal)}
                            >
                                {summary.value}
                            </div>
                            <div class="signal-label">{summary.label}</div>
                            {#if summary.signal}
                                <div
                                    class="signal-status"
                                    style:color={getSignalColor(summary.signal)}
                                >
                                    {#if summary.signal === "ok" || summary.signal === "bullish"}
                                        ✅ OK
                                    {:else if summary.signal === "warning"}
                                        ⚠️ ELEVATED
                                    {:else}
                                        🚨 {summary.signal.toUpperCase()}
                                    {/if}
                                </div>
                            {/if}
                        </div>
                    </td>
                {/if}
            </tr>
        {/each}
    </tbody>
</table>

<style>
    .signal-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
        table-layout: fixed;
    }

    /* Data columns take 70%, signal column takes 30% */
    .signal-table thead th:not(.signal-col-header) {
        width: 35%; /* Split 70% between 2 columns */
    }

    .signal-table thead th.signal-col-header {
        width: 30%;
    }

    .signal-table thead th {
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.7rem;
        opacity: 0.7;
        letter-spacing: 0.05em;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(255, 255, 255, 0.03);
        color: #94a3b8;
    }

    .signal-table thead th.signal-col-header {
        text-align: center;
    }

    .signal-table tbody tr {
        transition: background 0.15s ease;
    }

    .signal-table tbody tr:hover {
        background: rgba(255, 255, 255, 0.03);
    }

    .signal-table tbody td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        font-family: "JetBrains Mono", monospace;
    }

    .signal-table tbody tr:last-child td {
        border-bottom: none;
    }

    .compact tbody td {
        padding: 6px 10px;
    }

    /* Signal cell (rowspan) */
    .signal-cell {
        vertical-align: middle;
        text-align: center;
        background: rgba(0, 0, 0, 0.15);
        border-left: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 0 8px 8px 0;
        min-width: 140px;
    }

    .signal-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 8px;
    }

    .signal-value {
        font-size: 1.2rem;
        font-weight: 800;
        font-family: "JetBrains Mono", monospace;
    }

    .signal-label {
        font-size: 0.7rem;
        opacity: 0.6;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }

    .signal-status {
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 4px;
    }

    /* Dark mode adjustments */
    .dark thead th {
        border-color: rgba(255, 255, 255, 0.06);
    }

    .dark tbody tr:hover {
        background: rgba(255, 255, 255, 0.04);
    }
</style>
