<script>
    /**
     * BtcFundamentalsPanel.svelte
     * BTC valuation metrics with z-score and signal
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";
    import { formatValue, formatDelta } from "../../utils/dashboardHelpers.js";

    /** @type {number|null} */
    export let btcZscore = null;

    /** @type {number|null} */
    export let btcDeviation = null;

    /** @type {number|null} */
    export let drawdown = null;

    /** @type {number|null} */
    export let realizedVol = null;

    $: valuationLabel =
        btcZscore > 1
            ? $currentTranslations.valuation_premium || "PREMIUM"
            : btcZscore < -1
              ? $currentTranslations.valuation_discount || "DISCOUNT"
              : $currentTranslations.valuation_fair || "FAIR VALUE";
</script>

<div class="panel btc-panel">
    <div class="panel-header">
        <h3 class="panel-title">
            ₿ {$currentTranslations.btc_fundamentals_title ||
                "BTC Fundamentals-Lite"}
        </h3>
        <div
            class="btc-signal-badge"
            class:cheap={btcZscore < -1}
            class:expensive={btcZscore > 1}
        >
            {valuationLabel}
        </div>
    </div>
    <div class="btc-quant-grid">
        <div class="btc-q-item">
            <span class="l"
                >{$currentTranslations.price_vs_fair || "Price vs Fair"}</span
            >
            <span
                class="v"
                class:positive={btcDeviation > 0}
                class:negative={btcDeviation < 0}
            >
                {formatDelta(btcDeviation, 1)}%
            </span>
        </div>
        <div class="btc-q-item">
            <span class="l"
                >{$currentTranslations.valuation_z || "Valuation Z"}</span
            >
            <span class="v">{formatValue(btcZscore, 2, "σ")}</span>
        </div>
        <div class="btc-q-item">
            <span class="l">{$currentTranslations.drawdown || "Drawdown"}</span>
            <span class="v">{formatValue(drawdown, 1, "%")}</span>
        </div>
        <div class="btc-q-item">
            <span class="l"
                >{$currentTranslations.realized_vol || "Realized Vol"}</span
            >
            <span class="v">{formatValue(realizedVol, 1, "%")}</span>
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
        gap: 0.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color, #334155);
    }

    .panel-title {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
        font-family: var(--font-mono);
    }

    .btc-signal-badge {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
        background: var(--bg-elevated);
        color: var(--text-secondary);
    }

    .btc-signal-badge.cheap {
        background: var(--signal-ok-bg);
        color: var(--signal-ok);
    }

    .btc-signal-badge.expensive {
        background: var(--signal-bearish-bg);
        color: var(--signal-bearish);
    }

    .btc-quant-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.75rem;
    }

    .btc-q-item {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 0.6rem;
        background: var(--bg-elevated);
        border-radius: var(--radius-sm);
    }

    .btc-q-item .l {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .btc-q-item .v {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
    }

    .btc-q-item .v.positive {
        color: var(--signal-ok);
    }

    .btc-q-item .v.negative {
        color: var(--signal-bearish);
    }
</style>
