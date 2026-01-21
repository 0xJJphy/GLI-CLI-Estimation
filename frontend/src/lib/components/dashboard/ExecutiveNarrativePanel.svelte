<script>
    /**
     * ExecutiveNarrativePanel.svelte
     * Market assessment with headline, risks, positives, and 7-day catalysts
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations, t } from "../../../stores/settingsStore";
    import { formatValue } from "../../utils/dashboardHelpers.js";

    /** @type {{headline: string, key_risks: string[], key_positives: string[], recommendation: string}} */
    export let assessment = {
        headline: "MARKET IN TRANSITION",
        key_risks: [],
        key_positives: [],
        recommendation: "Monitor closely",
    };

    /** @type {Array<{date: string, types: string, amount: number, risk_level: string}>} */
    export let next7dSettlements = [];

    /** @type {number} */
    export let totalNext7dAmount = 0;

    /** @type {number} */
    export let rrpBuffer = 0;

    /** @type {boolean} */
    export let dark = false;

    // Helper to translate structured backend assessment items
    function getAssessmentText(item) {
        if (!item) return "";
        if (typeof item === "object") {
            return t($currentTranslations, item.key || item.text || "");
        }
        return t($currentTranslations, item);
    }
</script>

<div class="narrative-assessment" class:dark>
    <div class="narrative-main">
        <div class="narrative-headline">
            <span class="label"
                >{$currentTranslations.market_assessment ||
                    "MARKET ASSESSMENT"}</span
            >
            <h2>{getAssessmentText(assessment.headline)}</h2>
            <div class="recommendation-badge">
                {getAssessmentText(assessment.recommendation)}
            </div>
        </div>
        <div class="narrative-details">
            <div class="detail-group risks">
                <span class="group-title"
                    >⚠️ {$currentTranslations.top_risks || "TOP RISKS"}</span
                >
                <ul>
                    {#each assessment.key_risks as risk}
                        <li>{getAssessmentText(risk)}</li>
                    {/each}
                </ul>
            </div>
            <div class="detail-group positives">
                <span class="group-title"
                    >✅ {$currentTranslations.supportive_factors ||
                        "SUPPORTIVE FACTORS"}</span
                >
                <ul>
                    {#each assessment.key_positives as positive}
                        <li>{getAssessmentText(positive)}</li>
                    {/each}
                </ul>
            </div>
        </div>
    </div>

    <div class="catalyst-next-7d">
        <div class="panel-header">
            <h3>
                🗓️ {$currentTranslations.next_7d_catalysts ||
                    "Next 7 Days Catalysts"}
            </h3>
        </div>
        {#if next7dSettlements.length > 0}
            <div class="catalyst-summary">
                <div class="summ-item">
                    <span class="l"
                        >{$currentTranslations.settlements ||
                            "Settlements"}</span
                    >
                    <span class="v"
                        >{formatValue(totalNext7dAmount, 1, "B")}</span
                    >
                </div>
                <div class="summ-item">
                    <span class="l"
                        >{$currentTranslations.rrp_buffer || "RRP Buffer"}</span
                    >
                    <span class="v">{formatValue(rrpBuffer, 0, "B")}</span>
                </div>
            </div>
            <div class="settlement-mini-table">
                {#each next7dSettlements as s}
                    <div class="s-row">
                        <span class="s-date"
                            >{new Date(s.date).toLocaleDateString(undefined, {
                                month: "short",
                                day: "numeric",
                            })}</span
                        >
                        <span class="s-type">{s.types}</span>
                        <span class="s-amt">${s.amount}B</span>
                        <span class="s-risk {s.risk_level}"
                            >{s.risk_level.toUpperCase()}</span
                        >
                    </div>
                {/each}
            </div>
        {:else}
            <div class="no-catalysts">
                {$currentTranslations.no_major_settlements ||
                    "No major settlements next 7d"}
            </div>
        {/if}
    </div>
</div>

<style>
    .narrative-assessment {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 20px;
        background: linear-gradient(
            135deg,
            var(--bg-secondary, #1e293b) 0%,
            var(--bg-tertiary, #334155) 100%
        );
        border-radius: 20px;
        border: 1px solid var(--border-color, #475569);
        overflow: hidden;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .narrative-assessment:hover {
        transform: translateY(-4px);
        box-shadow: 0 15px 30px -5px rgba(0, 0, 0, 0.4);
        border-color: var(--accent-secondary);
    }

    .narrative-main {
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .narrative-headline {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .narrative-headline .label {
        font-size: 0.75rem;
        font-weight: 800;
        color: #60a5fa;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .narrative-headline h2 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--text-primary, #f1f5f9);
        line-height: 1.2;
    }

    .recommendation-badge {
        display: inline-block;
        align-self: flex-start;
        margin-top: 8px;
        padding: 6px 14px;
        background: rgba(96, 165, 250, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .narrative-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
    }

    .detail-group {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .group-title {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        color: var(--text-secondary);
    }

    .detail-group ul {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .detail-group ul li {
        font-size: 0.9rem;
        color: var(--text-secondary, #cbd5e1);
        padding-left: 12px;
        position: relative;
    }

    .detail-group.risks ul li {
        border-left: 2px solid #ef4444;
    }

    .detail-group.positives ul li {
        border-left: 2px solid #10b981;
    }

    .catalyst-next-7d {
        background: rgba(0, 0, 0, 0.2);
        padding: 24px;
        border-left: 1px solid var(--border-color, #475569);
    }

    .catalyst-next-7d .panel-header h3 {
        margin: 0 0 0.75rem 0;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .catalyst-summary {
        display: flex;
        gap: 1rem;
        margin-bottom: 0.75rem;
    }

    .summ-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
        background: var(--bg-secondary, #1e293b);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--border-color, #334155);
    }

    .summ-item .l {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .summ-item .v {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.9rem;
        color: var(--text-primary);
    }

    .settlement-mini-table {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }

    .s-row {
        display: grid;
        grid-template-columns: 60px 1fr 55px 60px;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        padding: 0.3rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .s-date {
        color: var(--text-muted);
    }

    .s-type {
        color: var(--text-secondary);
        font-size: 0.7rem;
    }

    .s-amt {
        font-family: var(--font-mono);
        font-weight: 500;
        text-align: right;
    }

    .s-risk {
        font-size: 0.6rem;
        padding: 0.15rem 0.3rem;
        border-radius: var(--radius-sm);
        text-align: center;
        font-weight: 600;
    }

    .s-risk.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    .s-risk.medium {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }

    .s-risk.high {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .no-catalysts {
        font-size: 0.8rem;
        color: var(--text-muted);
        text-align: center;
        padding: 1rem;
    }

    @media (max-width: 900px) {
        .narrative-assessment {
            grid-template-columns: 1fr;
        }
        .narrative-details {
            grid-template-columns: 1fr;
        }
    }
</style>
