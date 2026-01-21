<script>
    /**
     * RepoPlumbingPanel.svelte
     * Repo & Fed Corridor monitoring panel
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";
    import {
        formatValue,
        formatDelta,
        calcDelta,
    } from "../../utils/dashboardHelpers.js";

    /**
     * @type {{
     *   srfUsage: number,
     *   rrpUsage: number,
     *   netRepo: number,
     *   netRepoZscore: number,
     *   cumulative30d: number,
     *   sofr: number,
     *   iorb: number,
     *   srfRate: number,
     *   rrpAward: number,
     *   sofrVolume: number
     * }}
     */
    export let repoMetrics = {
        srfUsage: 0,
        rrpUsage: 0,
        netRepo: 0,
        netRepoZscore: 0,
        cumulative30d: 0,
        sofr: 0,
        iorb: 0,
        srfRate: 0,
        rrpAward: 0,
        sofrVolume: 0,
    };

    /** @type {{label: string, class: string, key: string|null, desc: string}} */
    export let repoStressLevel = {
        label: "NORMAL",
        class: "low",
        key: null,
        desc: "",
    };

    /** @type {number[]|null} */
    export let rrpSeries = null;

    $: sofrIorbSpread =
        repoMetrics.sofr && repoMetrics.iorb
            ? ((repoMetrics.sofr - repoMetrics.iorb) * 100).toFixed(1)
            : null;

    $: gapToCeiling =
        repoMetrics.srfRate && repoMetrics.sofr
            ? ((repoMetrics.srfRate - repoMetrics.sofr) * 100).toFixed(1)
            : null;

    $: rrpDelta = rrpSeries ? calcDelta(rrpSeries, 5) : null;
</script>

<div class="panel repo-panel">
    <div class="panel-header">
        <h3 class="panel-title" style="font-family: var(--font-mono);">
            🏛️ {$currentTranslations.plumbing_title ||
                "Plumbing: Repo & Corridor"}
        </h3>
        <div class="repo-status {repoStressLevel.class}">
            {repoStressLevel.label}
        </div>
    </div>

    <div class="repo-split">
        <div class="repo-sub-section">
            <span class="sub-label">
                {$currentTranslations.corridor_status_bps ||
                    "CORRIDOR STATUS (BPS)"}
            </span>
            <div class="corridor-visual">
                <div class="c-line ceiling">
                    <span class="l">SRF</span>
                    <span class="v"
                        >{formatValue(repoMetrics.srfRate, 2, "%")}</span
                    >
                </div>
                <div class="c-line sofr">
                    <span class="l">SOFR</span>
                    <span class="v"
                        >{formatValue(repoMetrics.sofr, 3, "%")}</span
                    >
                    <span class="delta">
                        {$currentTranslations.gap_label || "Gap"}: {gapToCeiling ??
                            "—"}bps
                    </span>
                </div>
                <div class="c-line floor">
                    <span class="l">IORB</span>
                    <span class="v"
                        >{formatValue(repoMetrics.iorb, 2, "%")}</span
                    >
                    <span class="delta">
                        {$currentTranslations.spread_label || "Spr"}: {sofrIorbSpread ??
                            "—"}bps
                    </span>
                </div>
            </div>
        </div>

        <div class="repo-sub-section">
            <span class="sub-label">
                {$currentTranslations.liquidity_flows || "LIQUIDITY FLOWS"}
            </span>
            <div class="flow-metrics-grid">
                <div class="f-metric">
                    <span class="l"
                        >{$currentTranslations.rrp_1w_label ||
                            "ΔRRP (1w)"}</span
                    >
                    <span
                        class="v"
                        class:drain={rrpDelta > 0}
                        class:inject={rrpDelta < 0}
                    >
                        {formatDelta((rrpDelta ?? 0) * 1000, 0)}B
                    </span>
                </div>
                <div class="f-metric">
                    <span class="l"
                        >{$currentTranslations.srf_usage_label ||
                            "SRF Usage"}</span
                    >
                    <span class="v" class:warning={repoMetrics.srfUsage > 0}>
                        {formatValue(repoMetrics.srfUsage, 1, "B")}
                    </span>
                </div>
                <div class="f-metric">
                    <span class="l"
                        >{$currentTranslations.sofr_vol_label ||
                            "SOFR Vol"}</span
                    >
                    <span class="v">${repoMetrics.sofrVolume}B</span>
                </div>
                <div class="f-metric">
                    <span class="l"
                        >{$currentTranslations.net_repo_z_label ||
                            "Net Repo Z"}</span
                    >
                    <span class="v"
                        >{formatValue(repoMetrics.netRepoZscore, 2, "σ")}</span
                    >
                </div>
            </div>
        </div>
    </div>
    <p class="repo-desc">{repoStressLevel.desc}</p>
</div>

<style>
    .panel {
        background: var(--bg-card);
        border-radius: var(--radius-lg);
        padding: 1rem;
        border: 1px solid var(--border-color);
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        gap: 0.5rem;
    }

    .panel-title {
        margin: 0;
        font-size: 0.95rem;
        color: var(--text-primary);
        font-weight: 600;
    }

    .repo-status {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: var(--radius-sm);
        text-transform: uppercase;
    }

    .repo-status.low {
        background: rgba(22, 163, 74, 0.2);
        color: #16a34a;
    }

    .repo-status.moderate {
        background: rgba(202, 138, 4, 0.2);
        color: #ca8a04;
    }

    .repo-status.high {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .repo-split {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }

    .repo-sub-section {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .sub-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 500;
    }

    .corridor-visual {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .c-line {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.4rem 0.6rem;
        border-radius: var(--radius-sm);
        background: var(--bg-elevated);
    }

    .c-line.ceiling {
        border-left: 3px solid #ef4444;
    }

    .c-line.sofr {
        border-left: 3px solid var(--color-primary);
    }

    .c-line.floor {
        border-left: 3px solid #10b981;
    }

    .c-line .l {
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--text-secondary);
        min-width: 40px;
    }

    .c-line .v {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .c-line .delta {
        font-size: 0.65rem;
        color: var(--text-muted);
        margin-left: auto;
    }

    .flow-metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.5rem;
    }

    .f-metric {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        padding: 0.5rem;
        background: var(--bg-elevated);
        border-radius: var(--radius-sm);
    }

    .f-metric .l {
        font-size: 0.65rem;
        color: var(--text-muted);
    }

    .f-metric .v {
        font-family: var(--font-mono);
        font-weight: 600;
        font-size: 0.85rem;
        color: var(--text-primary);
    }

    .f-metric .v.drain {
        color: #ef4444;
    }

    .f-metric .v.inject {
        color: #10b981;
    }

    .f-metric .v.warning {
        color: #f59e0b;
    }

    .repo-desc {
        margin: 1rem 0 0 0;
        font-size: 0.75rem;
        color: var(--text-muted);
        font-style: italic;
    }

    @media (max-width: 600px) {
        .repo-split {
            grid-template-columns: 1fr;
        }
    }
</style>
