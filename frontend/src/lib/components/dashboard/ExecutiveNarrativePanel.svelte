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
        grid-template-columns: 1fr 300px;
        gap: 1.5rem;
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        margin-bottom: 1rem;
    }

    .narrative-main {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    .narrative-headline {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .narrative-headline .label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.5px;
    }

    .narrative-headline h2 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .recommendation-badge {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        background: var(--bg-tertiary);
        border-radius: var(--radius-sm);
        font-size: 0.75rem;
        color: var(--accent-primary);
        font-weight: 500;
        width: fit-content;
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
        padding-left: 1.2rem;
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .detail-group ul li {
        margin-bottom: 0.25rem;
    }

    .detail-group.risks ul li {
        color: var(--signal-warning);
    }

    .detail-group.positives ul li {
        color: var(--signal-ok);
    }

    .catalyst-next-7d {
        background: var(--bg-elevated);
        border-radius: var(--radius-md);
        padding: 1rem;
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
        gap: 0.15rem;
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
        background: var(--signal-ok-bg);
        color: var(--signal-ok);
    }

    .s-risk.medium {
        background: var(--signal-warning-bg);
        color: var(--signal-warning);
    }

    .s-risk.high {
        background: var(--signal-danger-bg);
        color: var(--signal-danger);
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
