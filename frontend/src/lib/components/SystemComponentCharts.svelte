<script>
    /**
     * SystemComponentCharts.svelte
     * Extracted from UsSystemTab. Displays individual charts for
     * Fed Assets, TGA, and RRP with their respective ROCs.
     */
    import Chart from "./Chart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import MetricCard from "./MetricCard.svelte";
    import { getLatestValue } from "../utils/helpers.js";

    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};
    export let language = "en";

    // Fed Props
    export let fedData = [];
    export let fedRange = "ALL";
    export let onFedRangeChange = (r) => {};
    export let latestFedAssets = 0;
    export let lastFedDate = "N/A";

    // RRP Props
    export let rrpData = [];
    export let rrpRange = "ALL";
    export let onRrpRangeChange = (r) => {};
    export let latestRRP = 0;
    export let lastRrpDate = "N/A";

    // TGA Props
    export let tgaData = [];
    export let tgaRange = "ALL";
    export let onTgaRangeChange = (r) => {};
    export let latestTGA = 0;
    export let lastTgaDate = "N/A";

    let fedCard, rrpCard, tgaCard;
</script>

<div class="component-charts">
    <!-- Fed Assets Chart -->
    <div class="chart-card" bind:this={fedCard}>
        <div class="chart-header">
            <h3>
                {translations.fed_assets_label || "Federal Reserve Assets"}
                <span class="current-value-badge fed">
                    ${latestFedAssets.toFixed(2)}T
                </span>
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={fedRange}
                    onRangeChange={onFedRangeChange}
                />
                <span class="last-date">
                    {translations.last_data || "Last Data:"}
                    {lastFedDate}
                </span>
            </div>
        </div>
        <p class="chart-description">
            {translations.fed_assets_desc ||
                "Total assets held by the Federal Reserve. QT = falling assets."}
        </p>
        <div class="chart-content">
            <Chart
                {darkMode}
                data={fedData}
                cardContainer={fedCard}
                cardTitle="fed_assets"
            />
        </div>
        <div class="roc-footer">
            <MetricCard
                variant="flat"
                size="small"
                label="1M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.fed?.["1M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["1M"],
                ) > 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <MetricCard
                variant="flat"
                size="small"
                label="3M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.fed?.["3M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.fed?.["3M"],
                ) > 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <div class="regime-note">
                {getLatestValue(dashboardData.us_system_rocs?.fed?.["1M"]) > 0
                    ? language === "en"
                        ? "↑ Expansion (QE)"
                        : "↑ Expansión (QE)"
                    : language === "en"
                      ? "↓ Contraction (QT)"
                      : "↓ Contracción (QT)"}
            </div>
        </div>
    </div>

    <!-- RRP Chart -->
    <div class="chart-card" bind:this={rrpCard}>
        <div class="chart-header">
            <h3>
                {translations.chart_fed_rrp || "Fed Reverse Repo (RRP)"}
                <span class="current-value-badge rrp">
                    ${latestRRP.toFixed(2)}T
                </span>
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={rrpRange}
                    onRangeChange={onRrpRangeChange}
                />
                <span class="last-date">
                    {translations.last_data || "Last Data:"}
                    {lastRrpDate}
                </span>
            </div>
        </div>
        <p class="chart-description">
            {translations.rrp || "Reverse Repo drains liquidity."}
        </p>
        <div class="chart-content">
            <Chart
                {darkMode}
                data={rrpData}
                cardContainer={rrpCard}
                cardTitle="fed_rrp"
            />
        </div>
        <div class="roc-footer">
            <MetricCard
                variant="flat"
                size="small"
                label="1M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.rrp?.["1M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["1M"],
                ) < 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <MetricCard
                variant="flat"
                size="small"
                label="3M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.rrp?.["3M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.rrp?.["3M"],
                ) < 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <div class="regime-note">
                {getLatestValue(dashboardData.us_system_rocs?.rrp?.["1M"]) < 0
                    ? language === "en"
                        ? "↓ Draining (bullish)"
                        : "↓ Drenando (alcista)"
                    : language === "en"
                      ? "↑ Filling (bearish)"
                      : "↑ Llenando (bajista)"}
            </div>
        </div>
    </div>

    <!-- TGA Chart -->
    <div class="chart-card" bind:this={tgaCard}>
        <div class="chart-header">
            <h3>
                {translations.chart_tga || "Treasury General Account (TGA)"}
                <span class="current-value-badge tga">
                    ${latestTGA.toFixed(2)}T
                </span>
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={tgaRange}
                    onRangeChange={onTgaRangeChange}
                />
                <span class="last-date">
                    {translations.last_data || "Last Data:"}
                    {lastTgaDate}
                </span>
            </div>
        </div>
        <p class="chart-description">
            {translations.tga || "TGA spending = liquidity injection."}
        </p>
        <div class="chart-content">
            <Chart
                {darkMode}
                data={tgaData}
                cardContainer={tgaCard}
                cardTitle="treasury_tga"
            />
        </div>
        <div class="roc-footer">
            <MetricCard
                variant="flat"
                size="small"
                label="1M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.tga?.["1M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["1M"],
                ) < 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <MetricCard
                variant="flat"
                size="small"
                label="3M ROC"
                value={(
                    getLatestValue(dashboardData.us_system_rocs?.tga?.["3M"]) ??
                    0
                ).toFixed(1) + "%"}
                status={getLatestValue(
                    dashboardData.us_system_rocs?.tga?.["3M"],
                ) < 0
                    ? "positive"
                    : "negative"}
                {darkMode}
            />
            <div class="regime-note">
                {getLatestValue(dashboardData.us_system_rocs?.tga?.["1M"]) < 0
                    ? language === "en"
                        ? "↓ Spending (bullish)"
                        : "↓ Gastando (alcista)"
                    : language === "en"
                      ? "↑ Accumulating (bearish)"
                      : "↑ Acumulando (bajista)"}
            </div>
        </div>
    </div>
</div>

<style>
    .component-charts {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
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

    .current-value-badge.fed {
        background: rgba(59, 130, 246, 0.15);
        color: #3b82f6;
    }
    .current-value-badge.rrp {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }
    .current-value-badge.tga {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
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
        height: 250px;
    }

    .roc-footer {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--border-color);
    }

    .regime-note {
        margin-left: auto;
        font-size: 11px;
        color: var(--text-muted);
        font-weight: 500;
    }

    @media (max-width: 1200px) {
        .component-charts {
            grid-template-columns: 1fr;
        }
    }
</style>
