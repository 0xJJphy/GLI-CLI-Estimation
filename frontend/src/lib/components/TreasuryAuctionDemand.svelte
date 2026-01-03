<script>
    /**
     * TreasuryAuctionDemand.svelte
     * Displays Treasury auction demand metrics (Bid-to-Cover, Indirect %, etc.)
     */

    // Props from parent
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

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
    $: recentAuctions = (auctionData.raw_auctions || []).slice(0, 8);

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
                    <span class="type-name">{type}</span>
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
                            >{formatPct(data.indirect_pct)}</span
                        >
                    </div>
                </div>
            </div>
        {/each}
    </div>

    <!-- Recent Auctions Table -->
    {#if recentAuctions.length > 0}
        <div class="recent-auctions">
            <h4>{translations.recent_auctions || "Recent Auctions"}</h4>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>{translations.date || "Date"}</th>
                            <th>{translations.security || "Security"}</th>
                            <th>{translations.bid_to_cover || "BTC"}</th>
                            <th>{translations.indirect || "Indirect"}</th>
                            <th>{translations.direct || "Direct"}</th>
                            <th>{translations.dealer || "Dealer"}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each recentAuctions as auction}
                            <tr>
                                <td class="date-cell"
                                    >{auction.auction_date ||
                                        auction.issue_date ||
                                        "—"}</td
                                >
                                <td class="security-cell"
                                    >{auction.security_term || ""}
                                    {auction.security_type || ""}</td
                                >
                                <td
                                    class="btc-cell"
                                    class:strong={auction.bid_to_cover >= 2.7}
                                    class:weak={auction.bid_to_cover < 2.3}
                                >
                                    {formatBtc(auction.bid_to_cover)}
                                </td>
                                <td>{formatPct(auction.indirect_pct)}</td>
                                <td>{formatPct(auction.direct_pct)}</td>
                                <td class:concerning={auction.dealer_pct > 25}
                                    >{formatPct(auction.dealer_pct)}</td
                                >
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>
    {/if}
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

    .recent-auctions h4 {
        font-size: 14px;
        font-weight: 600;
        color: #f8fafc;
        margin: 0 0 12px 0;
    }

    .table-container {
        overflow-x: auto;
        max-height: 280px;
        overflow-y: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    thead {
        position: sticky;
        top: 0;
        z-index: 10;
    }

    thead th {
        text-align: left;
        padding: 10px 12px;
        background: rgba(0, 0, 0, 0.3);
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.5px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    tbody td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        color: #cbd5e1;
    }

    .date-cell {
        color: #94a3b8;
        font-family: monospace;
        font-size: 11px;
    }

    .security-cell {
        color: #f8fafc;
        font-weight: 500;
    }

    .btc-cell.strong {
        color: #22c55e;
        font-weight: 600;
    }

    .btc-cell.weak {
        color: #ef4444;
        font-weight: 600;
    }

    td.concerning {
        color: #fbbf24;
    }

    /* Dark mode already default, light mode adjustments */
    .auction-demand:not(.dark) {
        background: rgba(0, 0, 0, 0.02);
        border-color: rgba(0, 0, 0, 0.08);
    }
</style>
