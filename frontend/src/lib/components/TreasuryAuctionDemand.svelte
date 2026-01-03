<script>
    /**
     * TreasuryAuctionDemand.svelte
     * Displays Treasury auction demand metrics (Bid-to-Cover, Indirect %, etc.)
     */

    // Props from parent
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    let showMethodology = false;

    // --- Computed Data ---
    $: auctionData = dashboardData.treasury_auction_demand || {
        demand_score: {},
        time_series: {},
        raw_auctions: [],
    };

    $: demandScore = auctionData.demand_score || {};
    $: overallScore = demandScore.overall_score || 0;
    $: signal = demandScore.signal || "NO_DATA";
    $: signalColor = getSignalColor(signal);
    $: byType = demandScore.by_type || {};
    $: recentAuctions = (auctionData.raw_auctions || []).slice(0, 20);

    // Signal color mapping
    function getSignalColor(signal) {
        const colors = {
            STRONG_DEMAND: "#22c55e",
            SOLID_DEMAND: "#86efac",
            NEUTRAL: "#6b7280",
            SOFT_DEMAND: "#fbbf24",
            WEAK_DEMAND: "#ef4444",
            NO_DATA: "#6b7280",
        };
        return colors[signal] || "#6b7280";
    }

    // Format percentage
    function formatPct(value) {
        if (value === null || value === undefined) return "—";
        return `${value.toFixed(1)}%`;
    }

    // Format bid-to-cover
    function formatBtc(value) {
        if (value === null || value === undefined) return "—";
        return `${value.toFixed(2)}x`;
    }

    // Get demand level color
    function getDemandLevelColor(score) {
        if (score >= 30) return "#22c55e";
        if (score >= 10) return "#86efac";
        if (score >= -10) return "#6b7280";
        if (score >= -30) return "#fbbf24";
        return "#ef4444";
    }

    // Map signal to display text
    $: signalDisplay =
        {
            STRONG_DEMAND: translations.strong_demand || "Strong Demand",
            SOLID_DEMAND: translations.solid_demand || "Solid Demand",
            NEUTRAL: translations.neutral || "Neutral",
            SOFT_DEMAND: translations.soft_demand || "Soft Demand",
            WEAK_DEMAND: translations.weak_demand || "Weak Demand",
            NO_DATA: translations.no_data || "No Data",
        }[signal] || signal;
</script>

<div class="auction-demand" class:dark={darkMode}>
    <!-- Header -->
    <div class="section-header">
        <span class="icon">📊</span>
        <h3>{translations.auction_demand || "Treasury Auction Demand"}</h3>
        <span class="signal-badge" style="background: {signalColor};">
            {signalDisplay}
        </span>
    </div>

    <!-- Overall Score -->
    <div class="score-panel">
        <div class="score-main">
            <span class="score-value" style="color: {signalColor};">
                {overallScore > 0 ? "+" : ""}{overallScore.toFixed(1)}
            </span>
            <span class="score-label"
                >{translations.demand_score || "Demand Score"}</span
            >
        </div>
        <div class="score-description">
            <p>
                {#if overallScore >= 30}
                    {translations.demand_desc_strong ||
                        "Strong foreign and domestic demand. Yields may compress."}
                {:else if overallScore >= 10}
                    {translations.demand_desc_solid ||
                        "Healthy auction absorption. Normal market conditions."}
                {:else if overallScore >= -10}
                    {translations.demand_desc_neutral ||
                        "Mixed demand signals. Watch for trend changes."}
                {:else if overallScore >= -30}
                    {translations.demand_desc_soft ||
                        "Softening demand. Potential yield pressure ahead."}
                {:else}
                    {translations.demand_desc_weak ||
                        "Weak auction demand. Risk-off signal for bonds."}
                {/if}
            </p>
        </div>
    </div>

    <!-- By Security Type -->
    <div class="type-grid">
        {#each Object.entries(byType) as [type, data]}
            <div class="type-card">
                <div class="type-header">
                    <span class="type-name"
                        >{translations[data.name_key] || type}</span
                    >

                    <span
                        class="type-score"
                        style="color: {getDemandLevelColor(data.score || 0)};"
                    >
                        {data.score > 0 ? "+" : ""}{data.score?.toFixed(0) || 0}
                    </span>
                </div>
                <div class="type-metrics">
                    <div class="metric">
                        <span class="metric-label"
                            >{translations.bid_to_cover || "BTC"}</span
                        >
                        <span class="metric-value"
                            >{formatBtc(data.avg_btc)}</span
                        >
                    </div>
                    <div class="metric">
                        <span class="metric-label"
                            >{translations.indirect_pct || "Indirect"}</span
                        >
                        <span class="metric-value"
                            >{formatPct(data.avg_indirect_pct)}</span
                        >
                    </div>
                    <div class="metric">
                        <span class="metric-label"
                            >{translations.dealer_pct || "Dealer"}</span
                        >
                        <span
                            class="metric-value"
                            class:concerning={data.avg_dealer_pct > 25}
                        >
                            {formatPct(data.avg_dealer_pct)}
                        </span>
                    </div>
                </div>
            </div>
        {/each}
    </div>

    <!-- Methodology Description -->
    <div class="methodology-section">
        <button
            class="methodology-toggle"
            on:click={() => (showMethodology = !showMethodology)}
        >
            <span class="toggle-icon">{showMethodology ? "−" : "ℹ️"}</span>
            {translations.auction_methodology_title ||
                "Methodology & Interpretation"}
        </button>

        {#if showMethodology}
            <div class="methodology-content">
                <div class="methodology-item">
                    <h5>
                        {translations.formula || "Formula"}
                    </h5>
                    <p>
                        {translations.auction_methodology_formula ||
                            "The Demand Score is calculated as a weighted average of BTC, Indirect Bidders, and Dealer Takedown."}
                    </p>
                </div>
                <div class="methodology-item">
                    <h5>
                        {translations.thresholds || "Thresholds"}
                    </h5>
                    <p>
                        {translations.auction_methodology_thresholds ||
                            "High BTC and Indirect participation signal strong demand. High Dealer takedown indicates forced absorption."}
                    </p>
                </div>
                <div class="methodology-item">
                    <h5>
                        {translations.interpretation || "Interpretation"}
                    </h5>
                    <p>
                        {translations.auction_methodology_interpretation ||
                            "Scores indicate healthy absorption vs supply/demand imbalance."}
                    </p>
                </div>
            </div>
        {/if}
    </div>

    <!-- Type grid ends here -->
</div>

<style>
    .auction-demand {
        padding: 24px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
    }

    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
    }

    .icon {
        font-size: 24px;
    }

    .section-header h3 {
        font-size: 18px;
        font-weight: 600;
        color: #f8fafc;
        margin: 0;
        flex: 1;
    }

    .signal-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .score-panel {
        display: flex;
        gap: 24px;
        padding: 20px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        margin-bottom: 20px;
    }

    .score-main {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 100px;
    }

    .score-value {
        font-size: 36px;
        font-weight: 700;
        line-height: 1;
    }

    .score-label {
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        margin-top: 8px;
    }

    .score-description {
        flex: 1;
        display: flex;
        align-items: center;
    }

    .score-description p {
        margin: 0;
        color: #94a3b8;
        font-size: 14px;
        line-height: 1.5;
    }

    .type-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
        margin-bottom: 20px;
    }

    .type-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 14px;
    }

    .type-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }

    .type-name {
        color: #f8fafc;
        font-weight: 600;
        font-size: 13px;
    }

    .type-score {
        font-weight: 700;
        font-size: 14px;
    }

    .type-metrics {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .metric {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
    }

    .metric-label {
        color: #64748b;
    }

    .metric-value {
        color: #f8fafc;
        font-weight: 500;
    }

    .type-metrics {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    /* Methodology Section */
    .methodology-section {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
    }

    .methodology-toggle {
        display: flex;
        align-items: center;
        gap: 8px;
        background: transparent;
        border: none;
        color: #64748b;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 6px;
        transition: all 0.2s;
        margin-bottom: 8px;
    }

    .methodology-toggle:hover {
        color: #f8fafc;
        background: rgba(255, 255, 255, 0.04);
    }

    .toggle-icon {
        font-size: 14px;
    }

    .methodology-content {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 16px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        animation: slideDown 0.3s ease-out;
    }

    .methodology-item h5 {
        margin: 0 0 6px 0;
        font-size: 12px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .methodology-item p {
        margin: 0;
        font-size: 13px;
        color: #cbd5e1;
        line-height: 1.5;
    }

    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Dark mode already default, light mode adjustments */
    .auction-demand:not(.dark) {
        background: rgba(0, 0, 0, 0.02);
        border-color: rgba(0, 0, 0, 0.08);
    }
</style>
