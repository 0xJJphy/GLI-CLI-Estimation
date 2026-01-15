<script>
    /**
     * SystemicStressPanel.svelte
     * Extracted from UsSystemTab. Consolidates Bank Reserves, Risk Assessment,
     * and Net Repo Operations into a unified "Stress" view.
     */
    import Chart from "./Chart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import MetricCard from "./MetricCard.svelte";
    import { getLatestValue } from "../utils/helpers.js";

    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Reserves Props
    export let reservesData = [];
    export let reservesLayout = {};
    export let reservesRange = "ALL";
    export let onReservesRangeChange = (r) => {};
    export let latestReserves = 0;
    export let lastReservesDate = "N/A";

    // Risk Assessment Props
    export let riskAssessment = {
        score: 0,
        level: "LOW",
        color: "#22c55e",
        summary: "",
        risks: [],
    };

    // Net Repo Props
    export let latestNet = 0;
    export let latestRepoSRF = 0;
    export let latestRepoRRP = 0;
    export let regime = "NEUTRAL";
    export let regimeColor = "#6b7280";
    export let netRepoChartData = [];
    export let netRepoLayout = {};
    export let netRepoRange = "ALL";
    export let onNetRepoRangeChange = (r) => {};
    export let lastNetRepoDate = "N/A";

    let reservesCard, netRepoCard;
</script>

<div class="stress-panel-container">
    <!-- Bank Reserves Chart -->
    <div class="chart-card wide" bind:this={reservesCard}>
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_bank_reserves ||
                            "Bank Reserves vs Net Liquidity"}
                        <span class="current-value-badge reserves">
                            ${latestReserves.toFixed(2)}T
                        </span>
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={reservesRange}
                            onRangeChange={onReservesRangeChange}
                        />
                        <span class="last-date">
                            {translations.last_data || "Last Data:"}
                            {lastReservesDate}
                        </span>
                    </div>
                </div>
                <p class="chart-description">
                    {translations.bank_reserves ||
                        "Total reserves at Federal Reserve Banks."}
                </p>
                <div class="chart-content">
                    <Chart
                        {darkMode}
                        data={reservesData}
                        layout={reservesLayout}
                        cardContainer={reservesCard}
                        cardTitle="bank_reserves"
                    />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.reserves_indicators ||
                            "Reserves Indicators"}
                    </h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table compact">
                            <thead>
                                <tr>
                                    <th>Metric</th>
                                    <th>Value</th>
                                    <th>Signal</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>{translations.roc_3m || "3M ROC"}</td>
                                    <td
                                        class="roc-val"
                                        class:positive={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) > 0}
                                        class:negative={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) < 0}
                                    >
                                        {(
                                            getLatestValue(
                                                dashboardData.reserves_metrics
                                                    ?.reserves_roc_3m,
                                            ) ?? 0
                                        ).toFixed(2)}%
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:plus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) > 0}
                                        class:minus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) < 0}
                                    >
                                        {getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.reserves_roc_3m,
                                        ) > 0
                                            ? "QE"
                                            : "QT"}
                                    </td>
                                </tr>
                                <tr>
                                    <td
                                        >{translations.spread_zscore ||
                                            "Spread Z-Score"}</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:positive={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) < -1}
                                        class:negative={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) > 2}
                                    >
                                        {(
                                            getLatestValue(
                                                dashboardData.reserves_metrics
                                                    ?.spread_zscore,
                                            ) ?? 0
                                        ).toFixed(2)}
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:minus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) > 2}
                                        class:plus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) < -1}
                                    >
                                        {getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.spread_zscore,
                                        ) > 2
                                            ? translations.reserves_high_stress ||
                                              "High Stress"
                                            : getLatestValue(
                                                    dashboardData
                                                        .reserves_metrics
                                                        ?.spread_zscore,
                                                ) < -1
                                              ? translations.reserves_low_stress ||
                                                "Low Stress"
                                              : "Normal"}
                                    </td>
                                </tr>
                                <tr>
                                    <td
                                        >{translations.momentum ||
                                            "Momentum"}</td
                                    >
                                    <td
                                        class="roc-val"
                                        class:positive={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) > 0}
                                        class:negative={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) < 0}
                                    >
                                        {(
                                            getLatestValue(
                                                dashboardData.reserves_metrics
                                                    ?.momentum,
                                            ) ?? 0
                                        ).toFixed(4)}T
                                    </td>
                                    <td
                                        class="signal-cell"
                                        class:plus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) > 0}
                                        class:minus={getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) < 0}
                                    >
                                        {getLatestValue(
                                            dashboardData.reserves_metrics
                                                ?.momentum,
                                        ) > 0
                                            ? "Bullish"
                                            : "Bearish"}
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>

                    <!-- Risk Assessment Panel -->
                    <div
                        class="risk-assessment-box"
                        style="border-left-color: {riskAssessment.color}"
                    >
                        <div class="risk-header">
                            <span class="risk-label"
                                >{translations.overall_risk_level ||
                                    "Overall Risk Level"}</span
                            >
                            <span
                                class="risk-level"
                                style="color: {riskAssessment.color}"
                                >{riskAssessment.level}</span
                            >
                        </div>
                        <p class="risk-summary">{riskAssessment.summary}</p>
                        {#if riskAssessment.risks.length > 0}
                            <ul class="risk-list">
                                {#each riskAssessment.risks as risk}
                                    <li>{risk}</li>
                                {/each}
                            </ul>
                        {/if}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Net Repo Operations Chart -->
    <div class="chart-card wide" bind:this={netRepoCard}>
        <div class="chart-header">
            <h3>
                {translations.chart_net_repo_ops || "Fed Net Repo Operations"}
                <span
                    class="current-value-badge repo"
                    style="color: {latestNet > 0
                        ? '#22c55e'
                        : '#ef4444'}; background: {latestNet > 0
                        ? 'rgba(34, 197, 94, 0.15)'
                        : 'rgba(239, 68, 68, 0.15)'}"
                >
                    {latestNet > 0 ? "+" : ""}{latestNet.toFixed(1)}B
                </span>
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={netRepoRange}
                    onRangeChange={onNetRepoRangeChange}
                />
                <span class="last-date">
                    {translations.last_data || "Last Data:"}
                    {lastNetRepoDate}
                </span>
            </div>
        </div>

        <div class="repo-metrics-grid">
            <MetricCard
                variant="box"
                size="small"
                label={translations.net_pos || "Net Position"}
                value={(latestNet > 0 ? "+" : "") + latestNet.toFixed(1) + "B"}
                status={latestNet > 0 ? "positive" : "negative"}
                {darkMode}
            />
            <MetricCard
                variant="box"
                size="small"
                label={translations.regime_label || "Regime"}
                value={regime}
                status={regime === "INJECTION"
                    ? "positive"
                    : regime.includes("DRAIN")
                      ? "negative"
                      : "neutral"}
                {darkMode}
            />
            <MetricCard
                variant="box"
                size="small"
                label={translations.srf_inject_label || "SRF (Inject)"}
                value={"+" + latestRepoSRF.toFixed(1) + "B"}
                status="positive"
                {darkMode}
            />
            <MetricCard
                variant="box"
                size="small"
                label={translations.rrp_drain_label || "RRP (Drain)"}
                value={"-" + latestRepoRRP.toFixed(1) + "B"}
                status="negative"
                {darkMode}
            />
        </div>

        <p class="chart-description">
            {translations.net_repo_desc ||
                "Net = SRF Usage (injection) - RRP Usage (drain)."}
        </p>

        <div class="chart-content repo-chart">
            <Chart
                {darkMode}
                data={netRepoChartData}
                layout={netRepoLayout}
                cardContainer={netRepoCard}
                cardTitle="fed_net_repo"
            />
        </div>
    </div>
</div>

<style>
    .stress-panel-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
    }

    .chart-card.wide {
        grid-column: span 2;
    }

    .gli-layout {
        display: grid;
        grid-template-columns: 1fr 350px;
        gap: 24px;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 8px;
    }

    .chart-header h3 {
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 16px;
    }

    .current-value-badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
    }

    .current-value-badge.reserves {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
    }

    .header-controls {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 4px;
    }

    .last-date {
        font-size: 11px;
        color: var(--text-muted);
    }

    .chart-description {
        font-size: 13px;
        color: var(--text-muted);
        margin: 0 0 16px 0;
    }

    .chart-content {
        height: 350px;
    }

    .chart-content.repo-chart {
        height: 300px;
    }

    .metrics-sidebar {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .metrics-section h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
    }

    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
    }

    .metrics-table th,
    .metrics-table td {
        padding: 8px 4px;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }

    .roc-val {
        font-weight: 600;
    }
    .roc-val.positive {
        color: var(--positive-color);
    }
    .roc-val.negative {
        color: var(--negative-color);
    }

    .signal-cell {
        font-weight: 700;
        text-align: center;
    }
    .signal-cell.plus {
        color: var(--positive-color);
    }
    .signal-cell.minus {
        color: var(--negative-color);
    }

    .risk-assessment-box {
        margin-top: 16px;
        padding: 12px;
        border-radius: 8px;
        background: rgba(0, 0, 0, 0.05);
        border-left: 4px solid #ccc;
    }

    .risk-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .risk-label {
        font-size: 10px;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .risk-level {
        font-size: 13px;
        font-weight: 800;
    }

    .risk-summary {
        font-size: 12px;
        margin: 0;
        line-height: 1.4;
    }

    .risk-list {
        margin: 8px 0 0 0;
        padding-left: 18px;
        font-size: 11px;
        color: var(--text-muted);
    }

    .repo-metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
        margin: 16px 0;
    }

    @media (max-width: 1200px) {
        .gli-layout {
            grid-template-columns: 1fr;
        }
    }
</style>
