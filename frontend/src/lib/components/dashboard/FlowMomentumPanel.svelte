<script>
    /**
     * FlowMomentumPanel.svelte
     * Flow momentum table with CB contributions
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";
    import { formatValue } from "../../utils/dashboardHelpers.js";

    /**
     * @type {Array<{
     *   name: string,
     *   impulse4w: number|null,
     *   impulse13w: number|null,
     *   accel: number|null,
     *   zscore: number|null
     * }>}
     */
    export let flowData = [];

    /** @type {Array<{name: string, contrib: number|null}>} */
    export let cbContributions = [];
</script>

<div class="panel flow-panel">
    <div class="panel-header">
        <h3>
            ⚡ {$currentTranslations.flow_momentum_title || "Flow Momentum"}
        </h3>
    </div>
    <table class="flow-table">
        <thead>
            <tr>
                <th>{$currentTranslations.aggregate_col || "Aggregate"}</th>
                <th>{$currentTranslations.impulse_4w_col || "Impulse 4W"}</th>
                <th>{$currentTranslations.impulse_13w_col || "Impulse 13W"}</th>
                <th>{$currentTranslations.accel_col || "Accel"}</th>
                <th>{$currentTranslations.zscore_col || "Z-Score"}</th>
            </tr>
        </thead>
        <tbody>
            {#each flowData as flow}
                <tr>
                    <td class="flow-name">{flow.name}</td>
                    <td
                        class="flow-val"
                        class:positive={flow.impulse4w > 0}
                        class:negative={flow.impulse4w < 0}
                    >
                        {formatValue(flow.impulse4w, 2, "T")}
                    </td>
                    <td
                        class="flow-val"
                        class:positive={flow.impulse13w > 0}
                        class:negative={flow.impulse13w < 0}
                    >
                        {formatValue(flow.impulse13w, 2, "T")}
                    </td>
                    <td
                        class="flow-val"
                        class:positive={flow.accel > 0}
                        class:negative={flow.accel < 0}
                    >
                        {flow.accel !== null
                            ? formatValue(flow.accel, 2, "T")
                            : "—"}
                    </td>
                    <td
                        class="flow-zscore"
                        class:high={flow.zscore > 1}
                        class:low={flow.zscore < -1}
                    >
                        {formatValue(flow.zscore, 2, "σ")}
                    </td>
                </tr>
            {/each}
        </tbody>
    </table>

    <div class="cb-contributions">
        <h4>
            {$currentTranslations.cb_contrib_title ||
                "CB Contribution to ΔGLI (13W)"}
        </h4>
        <div class="contrib-bars">
            {#each cbContributions as cb}
                <div class="contrib-item">
                    <span class="cb-name">{cb.name}</span>
                    <div class="contrib-bar-wrapper">
                        <div
                            class="contrib-bar"
                            class:positive={cb.contrib > 0}
                            class:negative={cb.contrib < 0}
                            style="width: {Math.min(
                                Math.abs(cb.contrib || 0),
                                50,
                            )}%"
                        ></div>
                    </div>
                    <span
                        class="contrib-val"
                        class:positive={cb.contrib > 0}
                        class:negative={cb.contrib < 0}
                    >
                        {formatValue(cb.contrib, 1, "%")}
                    </span>
                </div>
            {/each}
        </div>
    </div>
</div>

<style>
    .panel {
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .panel:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15);
        border-color: var(--accent-secondary);
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color, #334155);
    }

    .panel-header h3 {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
    }

    .flow-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }

    .flow-table th,
    .flow-table td {
        padding: 0.5rem 0.75rem;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }

    .flow-table th {
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
    }

    .flow-name {
        font-weight: 500;
        color: var(--text-primary);
    }

    .flow-val {
        font-family: var(--font-mono);
        color: var(--text-secondary);
    }

    .flow-val.positive {
        color: var(--positive-color);
    }

    .flow-val.negative {
        color: var(--negative-color);
    }

    .flow-zscore {
        font-family: var(--font-mono);
        padding: 0.2rem 0.4rem;
        border-radius: var(--radius-sm);
        text-align: center;
    }

    .flow-zscore.high {
        background: var(--signal-ok-bg);
        color: var(--signal-ok);
    }

    .flow-zscore.low {
        background: var(--signal-bearish-bg);
        color: var(--signal-bearish);
    }

    .cb-contributions {
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }

    .cb-contributions h4 {
        margin: 0 0 0.75rem 0;
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    .contrib-bars {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .contrib-item {
        display: grid;
        grid-template-columns: 50px 1fr 50px;
        align-items: center;
        gap: 0.75rem;
    }

    .cb-name {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-secondary);
    }

    .contrib-bar-wrapper {
        height: 8px;
        background: var(--bg-elevated);
        border-radius: 4px;
        overflow: hidden;
    }

    .contrib-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .contrib-bar.positive {
        background: var(--positive-color);
    }

    .contrib-bar.negative {
        background: var(--negative-color);
    }

    .contrib-val {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        text-align: right;
    }

    .contrib-val.positive {
        color: var(--positive-color);
    }

    .contrib-val.negative {
        color: var(--negative-color);
    }
</style>
