<script>
    /**
     * RegimeStatusBar.svelte
     * Top status bar showing regime, FOMC countdown, and signal summary
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations, t } from "../../../stores/settingsStore";
    import {
        formatValue,
        formatDelta,
        getRegimeColor,
    } from "../../utils/dashboardHelpers.js";

    // Regime data
    /** @type {number} */
    export let regimeScore = 50;

    /** @type {number} */
    export let regimeCode = 0; // 1 = bullish, -1 = bearish, 0 = neutral

    /** @type {{liquidity_z: number, credit_z: number, brakes_z: number, total_z: number, confidence: number}} */
    export let regimeDiagnostics = {
        liquidity_z: 0,
        credit_z: 0,
        brakes_z: 0,
        total_z: 0,
        confidence: 0,
    };

    /** @type {{label: string, class: string}} */
    export let regimeTrend = { label: "→", class: "neutral" };

    // FOMC data
    /** @type {{days: number, hours: number, isToday: boolean}} */
    export let fomcCountdown = { days: 0, hours: 0, isToday: false };

    /** @type {boolean} */
    export let nextFomcHasSEP = false;

    /** @type {{cut: number, hold: number, hike: number, roc1m?: {cut: number}}|null} */
    export let nextMeetingProbs = null;

    // Rate data
    /** @type {number|null} */
    export let currentFedRate = null;

    /** @type {number|null} */
    export let currentSOFR = null;

    // Signal summary
    /** @type {number} */
    export let bullCount = 0;

    /** @type {number} */
    export let bearCount = 0;

    $: netSignal = bullCount - bearCount;

    $: regimeLabel =
        regimeCode === 1
            ? $currentTranslations.status_bullish
            : regimeCode === -1
              ? $currentTranslations.status_bearish
              : $currentTranslations.status_neutral;

    $: regimeEmoji = regimeCode === 1 ? "🟢" : regimeCode === -1 ? "🔴" : "⚪";

    $: regimeColor =
        regimeCode === 1
            ? "bullish"
            : regimeCode === -1
              ? "bearish"
              : "neutral";
</script>

<div class="regime-status-bar">
    <div class="regime-score-container">
        <div
            class="regime-score-ring"
            style="--score: {regimeScore}; --color: {getRegimeColor(
                regimeCode,
            )}"
        >
            <div class="score-inner">
                <span class="score-value">{formatValue(regimeScore, 0)}</span>
                <span class="confidence-label">
                    {formatValue(regimeDiagnostics.confidence, 0)}% {$currentTranslations.confidence ||
                        "Conf."}
                </span>
            </div>
        </div>
        <div class="regime-info">
            <span class="regime-label {regimeColor}"
                >{regimeEmoji} {regimeLabel}</span
            >
            <span class="regime-trend {regimeTrend.class}"
                >{regimeTrend.label}</span
            >
        </div>
    </div>

    <div class="regime-components">
        <div class="component">
            <span class="comp-label"
                >{$currentTranslations.regime_liquidity}</span
            >
            <span
                class="comp-value"
                class:positive={regimeDiagnostics.liquidity_z > 0}
                class:negative={regimeDiagnostics.liquidity_z < 0}
            >
                {formatDelta(regimeDiagnostics.liquidity_z)}σ
            </span>
        </div>
        <div class="component">
            <span class="comp-label">{$currentTranslations.regime_credit}</span>
            <span
                class="comp-value"
                class:positive={regimeDiagnostics.credit_z > 0}
                class:negative={regimeDiagnostics.credit_z < 0}
            >
                {formatDelta(regimeDiagnostics.credit_z)}σ
            </span>
        </div>
        <div class="component">
            <span class="comp-label">{$currentTranslations.regime_brakes}</span>
            <span
                class="comp-value"
                class:positive={regimeDiagnostics.brakes_z < 0}
                class:negative={regimeDiagnostics.brakes_z > 0}
            >
                {formatDelta(regimeDiagnostics.brakes_z)}σ
            </span>
        </div>
    </div>

    <div class="fomc-section">
        <div class="fomc-countdown">
            <span class="fomc-label"
                >{$currentTranslations.next || "Next"} FOMC</span
            >
            {#if fomcCountdown.isToday}
                <span class="fomc-today"
                    >🔴 {$currentTranslations.today || "TODAY"}</span
                >
            {:else}
                <span class="fomc-time"
                    >{fomcCountdown.days}d {fomcCountdown.hours}h</span
                >
            {/if}
            {#if nextFomcHasSEP}
                <span class="fomc-sep">📊 SEP</span>
            {/if}
        </div>

        {#if currentFedRate || currentSOFR}
            <div class="rates-container">
                {#if currentFedRate}
                    <div class="fed-rate">
                        <span class="rate-label"
                            >{$currentTranslations.target || "Target"}</span
                        >
                        <span class="rate-value target"
                            >{formatValue(currentFedRate, 2, "%")}</span
                        >
                    </div>
                {/if}
                {#if currentSOFR}
                    <div class="fed-rate">
                        <span class="rate-label">SOFR</span>
                        <span class="rate-value sofr"
                            >{formatValue(currentSOFR, 2, "%")}</span
                        >
                    </div>
                {/if}
            </div>
        {/if}

        <div class="probs-group">
            <div class="prob-item cut" class:high={nextMeetingProbs?.cut > 50}>
                <span class="prob-label"
                    >{$currentTranslations.prob_cut || "Cut"}</span
                >
                <span class="prob-value">{nextMeetingProbs?.cut ?? "—"}%</span>
                {#if nextMeetingProbs?.roc1m?.cut !== undefined}
                    <span
                        class="prob-change"
                        class:up={nextMeetingProbs.roc1m.cut > 0}
                        class:down={nextMeetingProbs.roc1m.cut < 0}
                    >
                        {nextMeetingProbs.roc1m.cut > 0
                            ? "+"
                            : ""}{nextMeetingProbs.roc1m.cut.toFixed(0)}
                    </span>
                {/if}
            </div>
            <div
                class="prob-item hold"
                class:high={nextMeetingProbs?.hold > 50}
            >
                <span class="prob-label"
                    >{$currentTranslations.prob_hold || "Hold"}</span
                >
                <span class="prob-value">{nextMeetingProbs?.hold ?? "—"}%</span>
            </div>
            {#if nextMeetingProbs?.hike > 5}
                <div class="prob-item hike">
                    <span class="prob-label"
                        >{$currentTranslations.prob_hike || "Hike"}</span
                    >
                    <span class="prob-value">{nextMeetingProbs.hike}%</span>
                </div>
            {/if}
        </div>
    </div>

    <div class="signal-summary">
        <span class="summary-label"
            >{$currentTranslations.nav_regimes || "Signals"}</span
        >
        <span class="summary-value">
            <span class="bull-count">🟢 {bullCount}</span>
            <span class="bear-count">🔴 {bearCount}</span>
            <span
                class="net-count"
                class:positive={netSignal > 0}
                class:negative={netSignal < 0}
            >
                Net: {netSignal > 0 ? "+" : ""}{netSignal}
            </span>
        </span>
    </div>
</div>

<style>
    .regime-status-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 1rem 1.5rem;
        border: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }

    .regime-score-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .regime-score-ring {
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: conic-gradient(
            var(--color) calc(var(--score) * 1%),
            var(--bg-elevated) calc(var(--score) * 1%)
        );
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 5px;
    }

    .score-inner {
        width: 100%;
        height: 100%;
        background: var(--bg-card);
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .score-value {
        font-family: var(--font-mono);
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .confidence-label {
        font-size: 0.6rem;
        color: var(--text-muted);
    }

    .regime-info {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .regime-label {
        font-weight: 600;
        font-size: 0.9rem;
    }

    .regime-label.bullish {
        color: #10b981;
    }

    .regime-label.bearish {
        color: #ef4444;
    }

    .regime-label.neutral {
        color: var(--text-secondary);
    }

    .regime-trend {
        font-size: 0.75rem;
    }

    .regime-trend.positive {
        color: #10b981;
    }

    .regime-trend.negative {
        color: #ef4444;
    }

    .regime-trend.neutral {
        color: var(--text-muted);
    }

    .regime-components {
        display: flex;
        gap: 1.25rem;
    }

    .component {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
    }

    .comp-label {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .comp-value {
        font-family: var(--font-mono);
        font-size: 0.85rem;
        font-weight: 600;
    }

    .comp-value.positive {
        color: #10b981;
    }

    .comp-value.negative {
        color: #ef4444;
    }

    .fomc-section {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        align-items: flex-end;
    }

    .fomc-countdown {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .fomc-label {
        font-size: 0.7rem;
        color: var(--text-muted);
    }

    .fomc-time {
        font-family: var(--font-mono);
        font-weight: 600;
        color: var(--text-primary);
    }

    .fomc-today {
        font-weight: 700;
        color: #ef4444;
        animation: pulse 1.5s infinite;
    }

    @keyframes pulse {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    .fomc-sep {
        font-size: 0.7rem;
        background: rgba(139, 92, 246, 0.2);
        color: #8b5cf6;
        padding: 0.15rem 0.4rem;
        border-radius: var(--radius-sm);
    }

    .rates-container {
        display: flex;
        gap: 1rem;
    }

    .fed-rate {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.1rem;
    }

    .rate-label {
        font-size: 0.6rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .rate-value {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.85rem;
    }

    .rate-value.target {
        color: var(--color-primary);
    }

    .rate-value.sofr {
        color: var(--text-primary);
    }

    .probs-group {
        display: flex;
        gap: 0.75rem;
    }

    .prob-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0.4rem 0.6rem;
        border-radius: var(--radius-sm);
        background: var(--bg-elevated);
    }

    .prob-item.high {
        background: rgba(16, 185, 129, 0.15);
    }

    .prob-item.cut .prob-value {
        color: #10b981;
    }

    .prob-item.hike .prob-value {
        color: #ef4444;
    }

    .prob-label {
        font-size: 0.6rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .prob-value {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.8rem;
    }

    .prob-change {
        font-size: 0.6rem;
        font-family: var(--font-mono);
    }

    .prob-change.up {
        color: #10b981;
    }

    .prob-change.down {
        color: #ef4444;
    }

    .signal-summary {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.3rem;
    }

    .summary-label {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .summary-value {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
    }

    .bull-count,
    .bear-count {
        font-weight: 500;
    }

    .net-count {
        font-family: var(--font-mono);
        font-weight: 600;
        padding: 0.15rem 0.4rem;
        border-radius: var(--radius-sm);
        background: var(--bg-elevated);
    }

    .net-count.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }

    .net-count.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    @media (max-width: 900px) {
        .regime-status-bar {
            flex-direction: column;
            gap: 1rem;
        }

        .fomc-section {
            align-items: center;
        }

        .regime-components {
            justify-content: center;
        }
    }
</style>
