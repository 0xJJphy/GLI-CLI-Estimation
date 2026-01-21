<script>
    /**
     * InflationPanel.svelte
     * Inflation expectations with actual CPI/PCE and breakevens table
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";
    import { formatValue, formatDelta } from "../../utils/dashboardHelpers.js";

    /** @type {{cpi: number|null, coreCpi: number|null, pce: number|null, corePce: number|null}} */
    export let actualInflation = {
        cpi: null,
        coreCpi: null,
        pce: null,
        corePce: null,
    };

    /** @type {{label: string, class: string, spread: number, desc: string}} */
    export let inflationCurveSignal = {
        label: "Flat",
        class: "neutral",
        spread: 0,
        desc: "",
    };

    /**
     * @type {Array<{
     *   label: string,
     *   source: string,
     *   value: number|null,
     *   delta1m: number|null,
     *   roc1m: number|null,
     *   roc3m: number|null
     * }>}
     */
    export let inflationMetrics = [];
</script>

<div class="panel inflation-panel wide">
    <div class="panel-header">
        <h3 class="panel-title">
            🔥 {$currentTranslations.inflation_expect_title ||
                "Inflation Expectations"}
        </h3>
        <div class="inflation-signal {inflationCurveSignal.class}">
            {$currentTranslations.curve_label || "Curve"}: {inflationCurveSignal.label}
            ({formatDelta(inflationCurveSignal.spread, 2)}pp)
        </div>
    </div>

    <div class="actual-inflation">
        <div class="actual-item">
            <span class="actual-label">CPI YoY</span>
            <span class="actual-value"
                >{formatValue(actualInflation.cpi, 2, "%")}</span
            >
        </div>
        <div class="actual-item">
            <span class="actual-label">Core CPI</span>
            <span class="actual-value"
                >{formatValue(actualInflation.coreCpi, 2, "%")}</span
            >
        </div>
        <div class="actual-item">
            <span class="actual-label">PCE YoY</span>
            <span class="actual-value"
                >{formatValue(actualInflation.pce, 2, "%")}</span
            >
        </div>
        <div class="actual-item target">
            <span class="actual-label">Core PCE</span>
            <span class="actual-value"
                >{formatValue(actualInflation.corePce, 2, "%")}</span
            >
            <span class="target-badge"
                >{$currentTranslations.fed_target_label || "Fed Target"}: 2%</span
            >
        </div>
    </div>

    <table class="inflation-table">
        <thead>
            <tr>
                <th>{$currentTranslations.metric_col || "Metric"}</th>
                <th>{$currentTranslations.source_col || "Source"}</th>
                <th>{$currentTranslations.value_col || "Value"}</th>
                <th>{$currentTranslations.delta_pp_col || "Δ1M (pp)"}</th>
                <th>{$currentTranslations.roc_1m_col || "ROC 1M"}</th>
                <th>{$currentTranslations.roc_3m_col || "ROC 3M"}</th>
            </tr>
        </thead>
        <tbody>
            {#each inflationMetrics as metric}
                <tr>
                    <td class="metric-name">{metric.label}</td>
                    <td class="metric-source">{metric.source}</td>
                    <td class="metric-val"
                        >{formatValue(metric.value, 2, "%")}</td
                    >
                    <td
                        class="metric-delta"
                        class:positive={metric.delta1m > 0}
                        class:negative={metric.delta1m < 0}
                    >
                        {formatDelta(metric.delta1m, 2)}
                    </td>
                    <td
                        class="metric-roc"
                        class:positive={metric.roc1m > 0}
                        class:negative={metric.roc1m < 0}
                    >
                        {formatDelta(metric.roc1m, 1)}%
                    </td>
                    <td
                        class="metric-roc"
                        class:positive={metric.roc3m > 0}
                        class:negative={metric.roc3m < 0}
                    >
                        {formatDelta(metric.roc3m, 1)}%
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>
    <p class="inflation-note">
        {inflationCurveSignal.desc || "Inflation expectations curve analysis"}
    </p>
</div>

<style>
    .panel {
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
    }

    .panel.wide {
        grid-column: 1 / -1;
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .panel-title {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
        font-family: var(--font-mono);
    }

    .inflation-signal {
        font-size: 0.75rem;
        font-weight: 500;
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
        background: var(--bg-elevated);
    }

    .inflation-signal.steepening {
        color: var(--signal-warning);
    }

    .inflation-signal.flattening {
        color: var(--signal-ok);
    }

    .inflation-signal.neutral {
        color: var(--text-secondary);
    }

    .actual-inflation {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .actual-item {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        padding: 0.5rem 0.75rem;
        background: var(--bg-elevated);
        border-radius: var(--radius-sm);
    }

    .actual-item.target {
        border: 1px solid var(--accent-primary);
    }

    .actual-label {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .actual-value {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
    }

    .target-badge {
        font-size: 0.6rem;
        color: var(--accent-primary);
    }

    .inflation-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
    }

    .inflation-table th,
    .inflation-table td {
        padding: 0.5rem 0.75rem;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }

    .inflation-table th {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
    }

    .metric-name {
        font-weight: 500;
        color: var(--text-primary);
    }

    .metric-source {
        font-size: 0.7rem;
        color: var(--text-muted);
    }

    .metric-val {
        font-family: var(--font-mono);
        color: var(--text-secondary);
    }

    .metric-delta,
    .metric-roc {
        font-family: var(--font-mono);
        font-size: 0.75rem;
    }

    .metric-delta.positive,
    .metric-roc.positive {
        color: var(--signal-bearish);
    }

    .metric-delta.negative,
    .metric-roc.negative {
        color: var(--signal-ok);
    }

    .inflation-note {
        margin: 0.75rem 0 0 0;
        font-size: 0.75rem;
        color: var(--text-muted);
        font-style: italic;
    }
</style>
