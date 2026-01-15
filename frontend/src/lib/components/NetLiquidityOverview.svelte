<script>
    /**
     * NetLiquidityOverview.svelte
     * Extracted from UsSystemTab. Provides a detailed view of US Net Liquidity
     * and its constituent components' impact.
     */
    import Chart from "./Chart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import MetricCard from "./MetricCard.svelte";
    import { getLatestValue } from "../utils/helpers.js";

    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};
    export let effectiveData = {};

    // Props for chart data and controls
    export let netLiqData = [];
    export let netLiqRange = "ALL";
    export let onRangeChange = (r) => {};
    export let usSystemMetrics = [];
    export let usSystemTotal = {};
    export let latestNetLiq = 0;
    export let lastFedDate = "N/A";

    let netLiqCard;
</script>

<div class="chart-card wide" bind:this={netLiqCard}>
    <div class="gli-layout">
        <div class="chart-main">
            <div class="chart-header">
                <h3>
                    {translations.chart_us_net_liq || "US Net Liquidity Trends"}
                    <span class="current-value-badge">
                        ${latestNetLiq.toFixed(2)}T
                    </span>
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={netLiqRange}
                        {onRangeChange}
                    />
                    <span class="last-date">
                        {translations.last_data || "Last Data:"}
                        {lastFedDate}
                    </span>
                </div>
            </div>
            <p class="chart-description">
                {translations.net_liq || "Fed Balance Sheet minus TGA and RRP."}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={netLiqData}
                    cardContainer={netLiqCard}
                    cardTitle="us_net_liquidity"
                />
            </div>
        </div>

        <div class="metrics-sidebar">
            <div class="metrics-section">
                <h4>
                    {translations.chart_us_comp ||
                        "US System Components Impact"}
                </h4>
                <div class="metrics-table-container">
                    <table class="metrics-table">
                        <thead>
                            <tr>
                                <th>Acc</th>
                                <th>1M</th>
                                <th title="Absolute change in Billions USD"
                                    >Δ$1M</th
                                >
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                                <th>3M</th>
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                                <th>1Y</th>
                                <th
                                    title={translations.impact_us ||
                                        "Impact on Net Liq"}>Imp</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            {#each usSystemMetrics as item}
                                <tr>
                                    <td>{item.name}</td>
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.m1 > 0) ||
                                            (item.isLiability && item.m1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.m1 < 0) ||
                                            (item.isLiability && item.m1 > 0)}
                                    >
                                        {item.m1.toFixed(1)}%
                                    </td>
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.delta1 > 0) ||
                                            (item.isLiability &&
                                                item.delta1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.delta1 < 0) ||
                                            (item.isLiability &&
                                                item.delta1 > 0)}
                                    >
                                        {item.delta1 > 0
                                            ? "+"
                                            : ""}{item.delta1.toFixed(0)}B
                                    </td>
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp1 > 0}
                                        class:negative={item.imp1 < 0}
                                    >
                                        {item.imp1.toFixed(2)}%
                                    </td>
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.m3 > 0) ||
                                            (item.isLiability && item.m3 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.m3 < 0) ||
                                            (item.isLiability && item.m3 > 0)}
                                    >
                                        {item.m3.toFixed(1)}%
                                    </td>
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp3 > 0}
                                        class:negative={item.imp3 < 0}
                                    >
                                        {item.imp3.toFixed(2)}%
                                    </td>
                                    <td
                                        class="roc-val"
                                        class:positive={(!item.isLiability &&
                                            item.y1 > 0) ||
                                            (item.isLiability && item.y1 < 0)}
                                        class:negative={(!item.isLiability &&
                                            item.y1 < 0) ||
                                            (item.isLiability && item.y1 > 0)}
                                    >
                                        {item.y1.toFixed(1)}%
                                    </td>
                                    <td
                                        class="roc-val impact-cell"
                                        class:positive={item.imp1y > 0}
                                        class:negative={item.imp1y < 0}
                                    >
                                        {item.imp1y.toFixed(2)}%
                                    </td>
                                </tr>
                            {/each}
                            <tr class="total-row">
                                <td><strong>TOTAL</strong></td>
                                <td>-</td>
                                <td
                                    class="roc-val"
                                    class:positive={usSystemTotal.delta1 > 0}
                                    class:negative={usSystemTotal.delta1 < 0}
                                >
                                    {usSystemTotal.delta1 > 0
                                        ? "+"
                                        : ""}{usSystemTotal.delta1.toFixed(0)}B
                                </td>
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp1 > 0}
                                    class:negative={usSystemTotal.imp1 < 0}
                                >
                                    {usSystemTotal.imp1.toFixed(2)}%
                                </td>
                                <td>-</td>
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp3 > 0}
                                    class:negative={usSystemTotal.imp3 < 0}
                                >
                                    {usSystemTotal.imp3.toFixed(2)}%
                                </td>
                                <td>-</td>
                                <td
                                    class="roc-val impact-cell"
                                    class:positive={usSystemTotal.imp1y > 0}
                                    class:negative={usSystemTotal.imp1y < 0}
                                >
                                    {usSystemTotal.imp1y.toFixed(2)}%
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p class="impact-note">
                    {translations.impact_note_us ||
                        "* Imp = Contribution to US Net Liquidity change."}
                </p>
            </div>

            <!-- Composite Liquidity Metrics -->
            <div class="metrics-section score-section">
                <h4>{translations.liquidity_score || "Liquidity Score"}</h4>
                <div class="metrics-grid">
                    <MetricCard
                        variant="flat"
                        size="small"
                        label={translations.liquidity_score ||
                            "Liquidity Score"}
                        value={(
                            getLatestValue(
                                dashboardData.us_system_metrics
                                    ?.liquidity_score,
                            ) ?? 0
                        ).toFixed(2)}
                        trend={getLatestValue(
                            dashboardData.us_system_metrics?.liquidity_score,
                        ) > 1
                            ? translations.liquid_env || "Liquid"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.liquidity_score,
                                ) < -1
                              ? translations.dry_env || "Dry"
                              : "—"}
                        status={getLatestValue(
                            dashboardData.us_system_metrics?.liquidity_score,
                        ) > 0
                            ? "positive"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.liquidity_score,
                                ) < 0
                              ? "negative"
                              : "neutral"}
                        {darkMode}
                    />
                    <MetricCard
                        variant="flat"
                        size="small"
                        label={translations.netliq_roc || "Net Liq ROC"}
                        value={(
                            getLatestValue(
                                dashboardData.us_system_metrics?.netliq_roc_20d,
                            ) ?? 0
                        ).toFixed(2) + "%"}
                        trend={getLatestValue(
                            dashboardData.us_system_metrics?.netliq_roc_20d,
                        ) > 2
                            ? "Risk-ON"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.netliq_roc_20d,
                                ) < -2
                              ? "Risk-OFF"
                              : "—"}
                        status={getLatestValue(
                            dashboardData.us_system_metrics?.netliq_roc_20d,
                        ) > 0
                            ? "positive"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.netliq_roc_20d,
                                ) < 0
                              ? "negative"
                              : "neutral"}
                        {darkMode}
                    />
                    <MetricCard
                        variant="flat"
                        size="small"
                        label="Δ4W NetLiq"
                        value={(
                            (getLatestValue(
                                dashboardData.us_system_metrics
                                    ?.netliq_delta_4w,
                            ) ?? 0) * 1000
                        ).toFixed(0) + "B"}
                        trend={getLatestValue(
                            dashboardData.us_system_metrics?.netliq_delta_4w,
                        ) > 0.1
                            ? "Bullish"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.netliq_delta_4w,
                                ) < -0.1
                              ? "Bearish"
                              : "—"}
                        status={getLatestValue(
                            dashboardData.us_system_metrics?.netliq_delta_4w,
                        ) > 0
                            ? "positive"
                            : getLatestValue(
                                    dashboardData.us_system_metrics
                                        ?.netliq_delta_4w,
                                ) < 0
                              ? "negative"
                              : "neutral"}
                        {darkMode}
                    />
                    <MetricCard
                        variant="flat"
                        size="small"
                        label={translations.fed_momentum_label ||
                            "Fed Momentum"}
                        value={(
                            getLatestValue(
                                dashboardData.us_system_metrics?.fed_momentum,
                            ) ?? 0
                        ).toFixed(3) + "T"}
                        trend={getLatestValue(
                            dashboardData.us_system_metrics?.fed_momentum,
                        ) > 0
                            ? translations.regime_qe || "QE Mode"
                            : translations.regime_qt || "QT Mode"}
                        status={getLatestValue(
                            dashboardData.us_system_metrics?.fed_momentum,
                        ) > 0
                            ? "positive"
                            : "negative"}
                        {darkMode}
                    />
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
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
    }

    .current-value-badge {
        background: rgba(16, 185, 129, 0.15);
        color: var(--positive-color);
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
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

    .metrics-sidebar {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .metrics-section h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: var(--text-primary);
    }

    .metrics-table-container {
        overflow-x: auto;
    }

    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px;
    }

    .metrics-table th,
    .metrics-table td {
        padding: 6px 4px;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
    }

    .metrics-table th {
        color: var(--text-muted);
        font-weight: 500;
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

    .impact-cell {
        background: rgba(0, 0, 0, 0.02);
    }

    .total-row td {
        border-top: 2px solid var(--border-color);
        border-bottom: none;
    }

    .impact-note {
        font-size: 10px;
        color: var(--text-muted);
        margin-top: 8px;
    }

    .score-section {
        padding-top: 16px;
        border-top: 1px solid var(--border-color);
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
    }

    @media (max-width: 1200px) {
        .gli-layout {
            grid-template-columns: 1fr;
        }
        .chart-card.wide {
            grid-column: span 1;
        }
    }
</style>
