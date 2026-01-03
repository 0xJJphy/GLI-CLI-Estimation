<script>
    /**
     * Treasury Refinancing Impact Signal Component
     * =============================================
     * Displays a composite signal gauge combining:
     * - Auction Demand (35%)
     * - TGA Dynamics (25%)
     * - Net Liquidity (20%)
     * - Funding Stress (20%)
     *
     * Includes regime detection and trading implications.
     */
    export let darkMode = true;
    export let translations = {};
    export let signalData = {};

    // Reactive data
    $: score = signalData.overall_score || 0;
    $: regime = signalData.regime || "UNKNOWN";
    $: regimeEmoji = signalData.regime_emoji || "❓";
    $: regimeSignal = signalData.regime_signal || "UNKNOWN";
    $: regimeDescription = signalData.regime_description || "";
    $: components = signalData.components || {};
    $: alerts = signalData.alerts || [];
    $: alertStatus = signalData.alert_status || "UNKNOWN";
    $: tradingImplications = signalData.trading_implications || {};

    // Gauge calculation
    $: gaugeRotation = ((score + 100) / 200) * 180 - 90; // -90 to 90 degrees
    $: gaugeColor = getGaugeColor(score);

    function getGaugeColor(score) {
        if (score >= 40) return "#22c55e"; // Green - Surplus
        if (score >= 10) return "#3b82f6"; // Blue - Healthy
        if (score >= -20) return "#eab308"; // Yellow - Mild pressure
        if (score >= -50) return "#f97316"; // Orange - Stress
        return "#ef4444"; // Red - Crisis
    }

    function getStatusColor(status) {
        if (status === "positive") return "#22c55e";
        if (status === "negative") return "#ef4444";
        return "#94a3b8";
    }

    function getAlertStatusClass(status) {
        if (status === "CRITICAL") return "alert-critical";
        if (status === "WARNING") return "alert-warning";
        if (status === "CAUTION") return "alert-caution";
        return "alert-clear";
    }

    function formatComponentName(key) {
        const names = {
            auction_demand: "Auction Demand",
            tga_dynamics: "TGA Dynamics",
            net_liquidity: "Net Liquidity",
            funding_stress: "Funding Stress",
        };
        return translations[key] || names[key] || key;
    }

    function formatImplicationKey(key) {
        const names = {
            duration: "Duration",
            curve: "Curve",
            credit: "Credit",
            equity: "Equity",
            fx: "FX/USD",
        };
        return names[key] || key;
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
            <span class="alert-badge {getAlertStatusClass(alertStatus)}">
                {alertStatus}
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
                    stroke={gaugeColor}
                    stroke-width="3"
                    stroke-linecap="round"
                    transform="rotate({gaugeRotation}, 100, 100)"
                />
                <circle cx="100" cy="100" r="8" fill={gaugeColor} />
            </svg>
            <div class="gauge-labels">
                <span class="gauge-min">-100</span>
                <span class="gauge-center">0</span>
                <span class="gauge-max">+100</span>
            </div>
        </div>
        <div class="score-display">
            <span class="score-value" style="color: {gaugeColor}"
                >{score.toFixed(1)}</span
            >
            <div
                class="regime-badge"
                style="background-color: {gaugeColor}20; border-color: {gaugeColor}"
            >
                <span class="regime-emoji">{regimeEmoji}</span>
                <span class="regime-text">{regime.replace(/_/g, " ")}</span>
            </div>
            <p class="regime-description">{regimeDescription}</p>
        </div>
    </div>

    <!-- Component Breakdown -->
    <div class="components-section">
        <h4 class="section-title">
            {translations.component_breakdown || "Component Breakdown"}
        </h4>
        <div class="components-grid">
            {#each Object.entries(components) as [key, comp]}
                <div class="component-card">
                    <div class="component-header">
                        <span class="component-name"
                            >{formatComponentName(key)}</span
                        >
                        <span class="component-weight"
                            >{(comp.weight * 100).toFixed(0)}%</span
                        >
                    </div>
                    <div class="component-scores">
                        <span
                            class="raw-score"
                            style="color: {getStatusColor(comp.status)}"
                        >
                            {comp.raw_score > 0 ? "+" : ""}{comp.raw_score}
                        </span>
                        <span class="weighted-score">
                            → {comp.weighted_score > 0
                                ? "+"
                                : ""}{comp.weighted_score.toFixed(1)}
                        </span>
                    </div>
                    <p class="component-description">{comp.description}</p>
                </div>
            {/each}
        </div>
    </div>

    <!-- Alerts Section -->
    {#if alerts.length > 0}
        <div class="alerts-section">
            <h4 class="section-title">
                {translations.active_alerts || "Active Alerts"}
            </h4>
            <div class="alerts-list">
                {#each alerts as alert}
                    <div class="alert-item">
                        {alert}
                    </div>
                {/each}
            </div>
        </div>
    {/if}

    <!-- Trading Implications -->
    {#if Object.keys(tradingImplications).length > 0}
        <div class="implications-section">
            <h4 class="section-title">
                {translations.trading_implications || "Trading Implications"}
            </h4>
            <div class="implications-grid">
                {#each Object.entries(tradingImplications) as [key, value]}
                    <div class="implication-item">
                        <span class="implication-key"
                            >{formatImplicationKey(key)}</span
                        >
                        <span class="implication-value">{value}</span>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
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
    }

    .alert-critical {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .alert-warning {
        background: rgba(249, 115, 22, 0.2);
        color: #f97316;
        border: 1px solid rgba(249, 115, 22, 0.3);
    }

    .alert-caution {
        background: rgba(234, 179, 8, 0.2);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }

    .alert-clear {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
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

    .regime-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 24px;
        border: 1px solid;
        margin-top: 12px;
    }

    .regime-emoji {
        font-size: 18px;
    }

    .regime-text {
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

    /* Alerts Section */
    .alerts-section {
        margin-bottom: 24px;
    }

    .alerts-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .alert-item {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13px;
        color: #f8fafc;
    }

    /* Implications Section */
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
