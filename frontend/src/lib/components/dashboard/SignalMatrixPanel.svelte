<script>
    /**
     * SignalMatrixPanel.svelte
     * Signal Matrix with weighted scoring and indicator table
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";
    import {
        formatValue,
        formatDelta,
        getSignalClass,
        getSignalEmoji,
    } from "../../utils/dashboardHelpers.js";

    /**
     * @type {Array<{
     *   id: string,
     *   label: string,
     *   icon: string,
     *   state: string,
     *   value: number|null,
     *   percentile: number|null,
     *   delta: number|null
     * }>}
     */
    export let signalMatrix = [];

    /** @type {{score: number, topDrivers: Array<{id: string, label: string, impact: number, state: string}>}} */
    export let weightedScoreInfo = { score: 0, topDrivers: [] };

    /** @type {"bullish"|"bearish"|"neutral"} */
    export let aggregateSignal = "neutral";
</script>

<div class="panel signal-panel">
    <div class="panel-header">
        <div class="title-with-score">
            <h3>
                📡 {$currentTranslations.signal_matrix_title || "Signal Matrix"}
            </h3>
            <div class="weighted-score-pill {aggregateSignal}">
                {weightedScoreInfo.score > 0
                    ? "+"
                    : ""}{weightedScoreInfo.score}
            </div>
        </div>
        <div class="top-drivers-mini">
            {#each weightedScoreInfo.topDrivers as driver}
                <div class="driver-tag {driver.state}">
                    {driver.label}
                </div>
            {/each}
        </div>
        <div class="aggregate-badge {aggregateSignal}">
            {aggregateSignal === "bullish"
                ? `🟢 ${$currentTranslations.risk_on_label || "RISK-ON"}`
                : aggregateSignal === "bearish"
                  ? `🔴 ${$currentTranslations.risk_off_label || "RISK-OFF"}`
                  : `⚪ ${$currentTranslations.neutral_label || "NEUTRAL"}`}
        </div>
    </div>
    <div class="signal-table-container">
        <table class="signal-table">
            <thead>
                <tr>
                    <th>{$currentTranslations.indicator_col || "Indicator"}</th>
                    <th>{$currentTranslations.value_col || "Value"}</th>
                    <th>{$currentTranslations.delta_col || "Δ1M"}</th>
                    <th>{$currentTranslations.signal_col || "Signal"}</th>
                </tr>
            </thead>
            <tbody>
                {#each signalMatrix as signal}
                    <tr>
                        <td class="indicator-cell">
                            <span class="indicator-icon">{signal.icon}</span>
                            <span class="indicator-name">{signal.label}</span>
                        </td>
                        <td class="value-cell">
                            {formatValue(signal.value, 2)}
                            {#if signal.percentile !== null}
                                <span class="percentile"
                                    >P{signal.percentile.toFixed(0)}</span
                                >
                            {/if}
                        </td>
                        <td
                            class="delta-cell"
                            class:positive={signal.delta > 0}
                            class:negative={signal.delta < 0}
                        >
                            {signal.delta !== null
                                ? formatDelta(signal.delta)
                                : "—"}
                        </td>
                        <td class="signal-cell {getSignalClass(signal.state)}">
                            {getSignalEmoji(signal.state)}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>

<style>
    .panel {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .panel-header h3 {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
    }

    .title-with-score {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .weighted-score-pill {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        font-weight: 700;
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
    }

    .weighted-score-pill.bullish {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    .weighted-score-pill.bearish {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .weighted-score-pill.neutral {
        background: rgba(107, 114, 128, 0.2);
        color: var(--text-secondary);
    }

    .top-drivers-mini {
        display: flex;
        gap: 0.4rem;
        flex-wrap: wrap;
    }

    .driver-tag {
        font-size: 0.65rem;
        padding: 0.15rem 0.4rem;
        border-radius: var(--radius-sm);
        font-weight: 500;
    }

    .driver-tag.bullish {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }

    .driver-tag.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    .aggregate-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.25rem 0.6rem;
        border-radius: var(--radius-md);
    }

    .aggregate-badge.bullish {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    .aggregate-badge.bearish {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .aggregate-badge.neutral {
        background: var(--bg-elevated);
        color: var(--text-secondary);
    }

    .signal-table-container {
        overflow-x: auto;
    }

    .signal-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
    }

    .signal-table th,
    .signal-table td {
        padding: 0.5rem 0.75rem;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }

    .signal-table th {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
    }

    .indicator-cell {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .indicator-icon {
        font-size: 1rem;
    }

    .indicator-name {
        color: var(--text-primary);
    }

    .value-cell {
        font-family: var(--font-mono);
        color: var(--text-secondary);
    }

    .percentile {
        margin-left: 0.4rem;
        font-size: 0.65rem;
        color: var(--text-muted);
        background: var(--bg-elevated);
        padding: 0.1rem 0.3rem;
        border-radius: 3px;
    }

    .delta-cell {
        font-family: var(--font-mono);
    }

    .delta-cell.positive {
        color: #10b981;
    }

    .delta-cell.negative {
        color: #ef4444;
    }

    .signal-cell {
        font-size: 1rem;
        text-align: center;
    }
</style>
