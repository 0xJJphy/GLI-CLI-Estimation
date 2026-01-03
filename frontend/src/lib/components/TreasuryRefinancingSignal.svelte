<script>
    /**
     * Treasury Refinancing Impact Signal Component v2.0
     * ==================================================
     * Displays a composite signal gauge combining:
     * - Auction Demand (35%)
     * - TGA Dynamics (25%)
     * - Net Liquidity (20%)
     * - Funding Stress (20%)
     *
     * Enhanced to display:
     * - Regime with description
     * - Signal direction with color
     * - Component breakdown with alert levels
     * - Trading implications with opportunities and risks
     */
    export let darkMode = true;
    export let translations = {};
    export let signalData = {};

    // Reactive data - handle v2.0 nested structure
    $: score = signalData.score || 0;
    $: regime = signalData.regime || {};
    $: regimeCode = regime.code || "unknown";
    $: regimeName = translations[regime.name_key] || regime.name || "Unknown";
    $: regimeDescription =
        translations[regime.description_key] || regime.description || "";
    $: regimeColor = regime.color || "#6b7280";

    $: signal = signalData.signal || {};
    $: signalName = translations[signal.name_key] || signal.name || "Unknown";
    $: signalColor = signal.color || "#6b7280";

    $: components = signalData.components || [];
    $: alertStatus = signalData.alert_status || {};
    $: alertStatusText =
        translations[alertStatus.status_key] || alertStatus.status || "UNKNOWN";
    $: alertColor = alertStatus.color || "#6b7280";

    $: implications = signalData.implications || {};
    $: keyRisks = implications.key_risks || [];
    $: opportunities = implications.opportunities || [];

    // Gauge calculation
    $: gaugeRotation = ((score + 100) / 200) * 180 - 90; // -90 to 90 degrees

    // Regime emoji based on code
    $: regimeEmoji = getRegimeEmoji(regimeCode);

    function getRegimeEmoji(code) {
        const emojis = {
            liquidity_surplus: "💧",
            healthy_absorption: "✅",
            mild_pressure: "⚡",
            supply_stress: "📉",
            funding_crisis: "🚨",
        };
        return emojis[code] || "❓";
    }

    function getAlertLevelColor(level) {
        const colors = {
            critical: "#ef4444",
            warning: "#f97316",
            caution: "#eab308",
            normal: "#22c55e",
        };
        return colors[level] || "#94a3b8";
    }

    function getAlertLevelIcon(level) {
        const icons = {
            critical: "🔴",
            warning: "🟠",
            caution: "🟡",
            normal: "🟢",
        };
        return icons[level] || "⚪";
    }

    function getAlertStatusClass(status) {
        if (status === "CRITICAL") return "alert-critical";
        if (status === "ELEVATED") return "alert-elevated";
        if (status === "CAUTION") return "alert-caution";
        if (status === "NORMAL") return "alert-normal";
        return "alert-unknown";
    }

    function formatImplicationKey(key) {
        const names = {
            duration: "Duration",
            curve: "Curve",
            credit: "Credit",
            equity: "Equity",
            fx: "FX/USD",
        };
        return translations[`impl_${key}`] || names[key] || key;
    }
</script>

<div class="signal-container" class:dark={darkMode}>
    <!-- Header -->
    <div class="signal-header">
        <div class="header-left">
            <span class="header-icon">📊</span>
            <h3 class="header-title">
                {translations.refinancing_signal_title ||
                    "Treasury Refinancing Impact Signal"}
            </h3>
        </div>
        <div class="header-right">
            <span
                class="alert-badge {getAlertStatusClass(alertStatusText)}"
                style="background-color: {alertColor}20; border-color: {alertColor}; color: {alertColor};"
            >
                {alertStatusText}
            </span>
        </div>
    </div>

    <!-- Main Score Gauge -->
    <div class="gauge-section">
        <div class="gauge-container">
            <svg viewBox="0 0 200 120" class="gauge-svg">
                <!-- Background arc -->
                <path
                    d="M 20 100 A 80 80 0 0 1 180 100"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    stroke-width="12"
                    stroke-linecap="round"
                />
                <!-- Colored arc segments -->
                <path
                    d="M 20 100 A 80 80 0 0 1 56 38"
                    fill="none"
                    stroke="#ef4444"
                    stroke-width="12"
                    stroke-linecap="round"
                    opacity="0.3"
                />
                <path
                    d="M 56 38 A 80 80 0 0 1 100 20"
                    fill="none"
                    stroke="#f97316"
                    stroke-width="12"
                    opacity="0.3"
                />
                <path
                    d="M 100 20 A 80 80 0 0 1 144 38"
                    fill="none"
                    stroke="#eab308"
                    stroke-width="12"
                    opacity="0.3"
                />
                <path
                    d="M 144 38 A 80 80 0 0 1 180 100"
                    fill="none"
                    stroke="#22c55e"
                    stroke-width="12"
                    stroke-linecap="round"
                    opacity="0.3"
                />
                <!-- Needle -->
                <line
                    x1="100"
                    y1="100"
                    x2="100"
                    y2="35"
                    stroke={regimeColor}
                    stroke-width="3"
                    stroke-linecap="round"
                    transform="rotate({gaugeRotation}, 100, 100)"
                />
                <circle cx="100" cy="100" r="8" fill={regimeColor} />
            </svg>
            <div class="gauge-labels">
                <span class="gauge-min">-100</span>
                <span class="gauge-center">0</span>
                <span class="gauge-max">+100</span>
            </div>
        </div>
        <div class="score-display">
            <span class="score-value" style="color: {regimeColor}">
                {typeof score === "number" ? score.toFixed(1) : "0.0"}
            </span>
            <div
                class="regime-badge"
                style="background-color: {regimeColor}20; border-color: {regimeColor}"
            >
                <span class="regime-emoji">{regimeEmoji}</span>
                <span class="regime-text">{regimeName}</span>
            </div>
            <div
                class="signal-badge"
                style="background-color: {signalColor}15; border-color: {signalColor}"
            >
                <span class="signal-text" style="color: {signalColor}"
                    >{signalName}</span
                >
            </div>
            <p class="regime-description">{regimeDescription}</p>
        </div>
    </div>

    <!-- Component Breakdown -->
    <div class="components-section">
        <h4 class="section-title">
            {translations.rs_component_breakdown || "Component Breakdown"}
        </h4>
        <div class="components-grid">
            {#each components as comp}
                <div
                    class="component-card"
                    style="border-left: 3px solid {getAlertLevelColor(
                        comp.alert_level,
                    )}"
                >
                    <div class="component-header">
                        <span class="component-name">
                            <span class="alert-icon"
                                >{getAlertLevelIcon(comp.alert_level)}</span
                            >
                            {translations[comp.name_key] || comp.name}
                        </span>
                        <span class="component-weight"
                            >{(comp.weight * 100).toFixed(0)}%</span
                        >
                    </div>
                    <div class="component-scores">
                        <span
                            class="raw-score"
                            style="color: {getAlertLevelColor(
                                comp.alert_level,
                            )}"
                        >
                            {comp.score > 0 ? "+" : ""}{comp.score}
                        </span>
                        <span class="weighted-score">
                            → {comp.weighted_score > 0
                                ? "+"
                                : ""}{comp.weighted_score.toFixed(1)}
                        </span>
                    </div>
                    <p class="component-description">
                        {translations[comp.description_key] || comp.description}
                    </p>
                    {#if comp.threshold_breached}
                        <span class="threshold-tag"
                            >{comp.threshold_breached.replace(/_/g, " ")}</span
                        >
                    {/if}
                </div>
            {/each}
        </div>
    </div>

    <!-- Trading Implications -->
    <div class="implications-section">
        <h4 class="section-title">
            {translations.rs_trading_implications || "Trading Implications"}
        </h4>
        <div class="implications-grid">
            {#each ["duration", "curve", "credit", "equity", "fx"] as key}
                {#if implications[key]}
                    <div class="implication-item">
                        <span class="implication-key"
                            >{formatImplicationKey(key)}</span
                        >
                        <span class="implication-value"
                            >{translations[implications[key].key] ||
                                implications[key].text}</span
                        >
                    </div>
                {/if}
            {/each}
        </div>

        <!-- Opportunities -->
        {#if opportunities.length > 0}
            <div class="opportunities-section">
                <h5 class="subsection-title">
                    💡 {translations.rs_opportunities || "Opportunities"}
                </h5>
                <div class="tag-list">
                    {#each opportunities as opp}
                        <span class="opportunity-tag"
                            >{translations[opp.key] || opp.text}</span
                        >
                    {/each}
                </div>
            </div>
        {/if}

        <!-- Key Risks -->
        {#if keyRisks.length > 0}
            <div class="risks-section">
                <h5 class="subsection-title">
                    ⚠️ {translations.rs_key_risks || "Key Risks"}
                </h5>
                <div class="risks-list">
                    {#each keyRisks as risk}
                        <div class="risk-item">
                            {translations[risk.key] || risk.text}
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    .signal-container {
        background: linear-gradient(
            135deg,
            rgba(15, 23, 42, 0.95),
            rgba(30, 41, 59, 0.9)
        );
        border-radius: 16px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 24px;
    }

    .signal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-icon {
        font-size: 24px;
    }

    .header-title {
        font-size: 20px;
        font-weight: 700;
        color: #f8fafc;
        margin: 0;
    }

    .alert-badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        border: 1px solid;
    }

    /* Gauge Section */
    .gauge-section {
        display: flex;
        align-items: center;
        gap: 32px;
        margin-bottom: 24px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
    }

    .gauge-container {
        flex-shrink: 0;
        width: 200px;
    }

    .gauge-svg {
        width: 100%;
        height: auto;
    }

    .gauge-labels {
        display: flex;
        justify-content: space-between;
        font-size: 10px;
        color: #64748b;
        margin-top: -10px;
        padding: 0 10px;
    }

    .score-display {
        flex: 1;
    }

    .score-value {
        font-size: 48px;
        font-weight: 800;
        display: block;
        line-height: 1;
    }

    .regime-badge,
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 24px;
        border: 1px solid;
        margin-top: 12px;
        margin-right: 8px;
    }

    .regime-emoji {
        font-size: 18px;
    }

    .regime-text,
    .signal-text {
        font-size: 13px;
        font-weight: 600;
        color: #f8fafc;
        text-transform: capitalize;
    }

    .regime-description {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 12px;
        line-height: 1.5;
    }

    /* Section Titles */
    .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 16px;
    }

    .subsection-title {
        font-size: 13px;
        font-weight: 600;
        color: #cbd5e1;
        margin: 16px 0 12px 0;
    }

    /* Components Grid */
    .components-section {
        margin-bottom: 24px;
    }

    .components-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
    }

    .component-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
    }

    .component-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .component-name {
        font-size: 13px;
        font-weight: 600;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .alert-icon {
        font-size: 12px;
    }

    .component-weight {
        font-size: 11px;
        color: #64748b;
        background: rgba(255, 255, 255, 0.05);
        padding: 2px 8px;
        border-radius: 12px;
    }

    .component-scores {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }

    .raw-score {
        font-size: 20px;
        font-weight: 700;
    }

    .weighted-score {
        font-size: 12px;
        color: #64748b;
    }

    .component-description {
        font-size: 12px;
        color: #94a3b8;
        line-height: 1.4;
        margin: 0;
    }

    .threshold-tag {
        display: inline-block;
        margin-top: 8px;
        font-size: 10px;
        padding: 2px 8px;
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border-radius: 8px;
        text-transform: uppercase;
    }

    /* Implications Section */
    .implications-section {
        margin-bottom: 16px;
    }

    .implications-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .implication-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        padding: 12px;
    }

    .implication-key {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
    }

    .implication-value {
        font-size: 12px;
        color: #f8fafc;
        line-height: 1.4;
    }

    /* Opportunities */
    .opportunities-section,
    .risks-section {
        margin-top: 16px;
    }

    .tag-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .opportunity-tag {
        font-size: 12px;
        padding: 6px 12px;
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 16px;
    }

    .risks-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .risk-item {
        font-size: 12px;
        padding: 10px 14px;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px;
        color: #fca5a5;
        line-height: 1.4;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .gauge-section {
            flex-direction: column;
            text-align: center;
        }

        .components-grid,
        .implications-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
