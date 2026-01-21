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
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 16px 24px;
        background: var(--bg-secondary, #1e293b);
        border-radius: 16px;
        border: 1px solid var(--border-color, #334155);
        flex-wrap: wrap;
    }

    .regime-status-bar:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15);
        border-color: var(--accent-secondary);
    }

    .regime-score-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .regime-score-ring {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: conic-gradient(
            var(--color) calc(var(--score) * 1%),
            var(--bg-tertiary, #334155) 0
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .regime-score-ring::before {
        content: "";
        position: absolute;
        width: 52px;
        height: 52px;
        background: var(--bg-secondary, #1e293b);
        border-radius: 50%;
    }

    .score-inner {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .score-value {
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-primary, #f1f5f9);
        line-height: 1.1;
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
        font-size: 1.1rem;
        font-weight: 700;
    }
    .regime-label.bullish {
        color: #10b981;
    }
    .regime-label.bearish {
        color: #ef4444;
    }
    .regime-label.neutral {
        color: #6b7280;
    }

    .regime-trend {
        font-size: 0.75rem;
    }

    .regime-trend.positive {
        color: var(--positive-color);
    }

    .regime-trend.negative {
        color: var(--negative-color);
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
        color: var(--positive-color);
    }

    .comp-value.negative {
        color: var(--negative-color);
    }

    .fomc-section {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        padding: 10px 16px;
        background: var(--bg-tertiary, #334155);
        border-radius: 10px;
        border: 1px solid var(--border-color, #475569);
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
        color: var(--negative-color);
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
        font-weight: 700;
        font-size: 1rem;
    }

    .rate-value.target {
        color: #10b981; /* Green for target */
    }

    .rate-value.sofr {
        color: #3b82f6; /* Blue for SOFR */
    }

    .probs-group {
        display: flex;
        gap: 8px;
        padding: 8px;
        background: rgba(0, 0, 0, 0.15);
        border-radius: 8px;
    }

    .prob-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 6px 10px;
        border-radius: 6px;
        background: var(--bg-tertiary, #334155);
        min-width: 50px;
    }

    .prob-item.cut {
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .prob-item.cut .prob-value {
        color: #10b981;
        font-weight: 700;
    }

    .prob-item.hold {
        background: rgba(107, 114, 128, 0.2);
        border: 1px solid rgba(107, 114, 128, 0.3);
    }

    .prob-item.hold .prob-value {
        color: #9ca3af;
        font-weight: 700;
    }

    .prob-item.hike {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .prob-item.hike .prob-value {
        color: #ef4444;
        font-weight: 700;
    }

    .prob-item.cut .prob-value {
        color: var(--signal-ok);
    }

    .prob-item.hike .prob-value {
        color: var(--signal-bearish);
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
        color: var(--positive-color);
    }

    .prob-change.down {
        color: var(--negative-color);
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
        background: var(--signal-ok-bg);
        color: var(--signal-ok);
    }

    .net-count.negative {
        background: var(--signal-bearish-bg);
        color: var(--signal-bearish);
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
