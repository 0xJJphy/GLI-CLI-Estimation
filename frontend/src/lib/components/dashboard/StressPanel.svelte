<script>
    /**
     * StressPanel.svelte
     * Market Stress Dashboard with dimensional breakdown
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations, t } from "../../../stores/settingsStore";
    import {
        getStressLevelClass,
        getStressColor,
        formatValue,
    } from "../../utils/dashboardHelpers.js";

    /** @type {Array<{id: string, label: string, score: number, max: number, level: string}>} */
    export let stressDimensions = [];

    /** @type {number} */
    export let totalStress = 0;

    /** @type {number} */
    export let maxStress = 27;

    $: stressLevel =
        totalStress >= 15
            ? t($currentTranslations, "status_critical") || "CRITICAL"
            : totalStress >= 10
              ? t($currentTranslations, "status_high") || "HIGH"
              : totalStress >= 5
                ? t($currentTranslations, "status_moderate") || "MODERATE"
                : t($currentTranslations, "status_low") || "LOW";

    $: stressColor = getStressColor(totalStress);
</script>

<div class="panel stress-panel">
    <div class="panel-header">
        <h3>
            📊 {$currentTranslations.stress_panel_title ||
                "Market Stress Dashboard"}
        </h3>
        <div class="stress-total" style="--stress-color: {stressColor}">
            <span class="stress-score">{totalStress}/{maxStress}</span>
            <span class="stress-level {getStressLevelClass(stressLevel)}"
                >{stressLevel}</span
            >
        </div>
    </div>
    <div class="stress-grid">
        {#each stressDimensions as dim}
            <div class="stress-item">
                <span class="stress-label">{dim.label}</span>
                <div class="stress-bar-container">
                    <div
                        class="stress-bar"
                        style="width: {Math.max(
                            (dim.score / dim.max) * 100,
                            5,
                        )}%; background: {dim.score >= 4
                            ? '#ef4444'
                            : dim.score >= 2
                              ? '#f59e0b'
                              : '#10b981'};"
                    ></div>
                </div>
                <span class="stress-value">{dim.score}/{dim.max}</span>
                <span class="stress-badge {getStressLevelClass(dim.level)}"
                    >{dim.level}</span
                >
            </div>
        {/each}
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
        flex-wrap: wrap;
        gap: 0.5rem;
    }

    .panel-header h3 {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
    }

    .stress-total {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .stress-score {
        font-family: var(--font-mono);
        font-size: 1rem;
        font-weight: 700;
        color: var(--stress-color);
    }

    .stress-level {
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .stress-level.critical {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .stress-level.high {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }

    .stress-level.moderate {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
    }

    .stress-level.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    .stress-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .stress-item {
        display: grid;
        grid-template-columns: 120px 1fr 50px 80px;
        align-items: center;
        gap: 12px;
    }

    .stress-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
    }

    .stress-bar-container {
        height: 8px;
        background: #334155;
        border-radius: 4px;
        overflow: hidden;
    }

    .stress-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .stress-value {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary, #f1f5f9);
        text-align: right;
        font-family: monospace;
    }

    .stress-badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        text-align: center;
    }

    .stress-badge.critical {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .stress-badge.high {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }

    .stress-badge.moderate {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
    }

    .stress-badge.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }

    @media (max-width: 600px) {
        .stress-item {
            grid-template-columns: 80px 1fr 40px;
        }
        .stress-badge {
            display: none;
        }
    }
</style>
