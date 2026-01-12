<script>
    import { onMount } from "svelte";
    import {
        t,
        currentTranslations,
        darkMode,
    } from "../../stores/settingsStore";
    import {
        etfData,
        etfLoading,
        dashboardData,
        fetchEtfData,
    } from "../../stores/dataStore";
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import Dropdown from "../components/Dropdown.svelte";

    // Data is now fetched locally to avoid bloating main dashboard_data.json
    $: summary = $etfData?.summary || [];
    $: flowsAgg = $etfData?.flows_agg || {};
    $: individualDaily = $etfData?.individual_daily || {};
    $: dates = $etfData?.dates || [];

    let selectedTicker = "IBIT";
    let chartTimeframe = "1D"; // 1D, 7D, 30D, 90D
    let showMA = true;
    let showBtcOverlay = false;

    /**
     * Helper to calculate simple moving average
     */
    function calculateSMA(data, window) {
        if (!data || data.length === 0) return [];
        let results = [];
        for (let i = 0; i < data.length; i++) {
            if (i < window - 1) {
                results.push(null);
                continue;
            }
            let sum = 0;
            for (let j = 0; j < window; j++) {
                sum += data[i - j] || 0;
            }
            results.push(sum / window);
        }
        return results;
    }

    $: tickerOptions = summary.map((s) => ({
        value: s.ticker,
        label: s.ticker,
    }));

    // Aggregated Stats
    $: lastIdx = (flowsAgg.total_flow_usd || []).length - 1;
    $: lastAggFlow = lastIdx >= 0 ? flowsAgg.total_flow_usd[lastIdx] : 0;
    $: totalCumFlow = (flowsAgg.cum_flow_usd || [])[lastIdx] || 0;
    $: totalAUM = summary.reduce((acc, curr) => acc + (curr.aum_usd || 0), 0);

    $: statsCards = [
        {
            label: `${t($currentTranslations, "etf_7d_flow")}`,
            value: flowsAgg.flow_usd_7d ? flowsAgg.flow_usd_7d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_30d_flow")}`,
            value: flowsAgg.flow_usd_30d ? flowsAgg.flow_usd_30d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_90d_flow")}`,
            value: flowsAgg.flow_usd_90d ? flowsAgg.flow_usd_90d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 7d`,
            value: flowsAgg.aum_roc_7d ? flowsAgg.aum_roc_7d[lastIdx] : 0,
            isPct: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 30d`,
            value: flowsAgg.aum_roc_30d ? flowsAgg.aum_roc_30d[lastIdx] : 0,
            isPct: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 90d`,
            value: flowsAgg.aum_roc_90d ? flowsAgg.aum_roc_90d[lastIdx] : 0,
            isPct: true,
        },
    ];

    // Main Chart Data Mapping
    $: currentFlowData =
        chartTimeframe === "1D"
            ? flowsAgg.total_flow_usd || []
            : chartTimeframe === "7D"
              ? flowsAgg.flow_usd_7d || []
              : chartTimeframe === "30D"
                ? flowsAgg.flow_usd_30d || []
                : flowsAgg.flow_usd_90d || [];

    $: barColors = currentFlowData.map((val) =>
        val >= 0 ? "#10b981" : "#ef4444",
    );

    // MA Area Logic: Calculated in Frontend, handles zero-crossings for clean fill
    $: maDataRaw = calculateSMA(currentFlowData, 20);
    $: maProcessed = (() => {
        if (!maDataRaw || maDataRaw.length === 0)
            return { dates: [], pos: [], neg: [], line: [] };

        let pDates = [];
        let pPos = [];
        let pNeg = [];
        let pLine = [];

        for (let i = 0; i < maDataRaw.length; i++) {
            const curr = maDataRaw[i];
            const prev = i > 0 ? maDataRaw[i - 1] : null;

            // Handle zero crossing for clean fill areas
            if (
                prev !== null &&
                curr !== null &&
                ((prev > 0 && curr < 0) || (prev < 0 && curr > 0))
            ) {
                // Interpolate precisely for linear sharp transitions
                // x2 = x1 + (0 - y1) * (x1 - x2) / (y1 - y2)
                // But for discrete dates, we can just push a zero point at the current date
                // or a mid-point if we want to be fancy. For Plotly bar/line blend,
                // pushing the zero at the current date index works well with 'linear' shape.
                pDates.push(dates[i]);
                pPos.push(0);
                pNeg.push(0);
                pLine.push(0);
            }

            pDates.push(dates[i]);
            pLine.push(curr);
            pPos.push(curr !== null && curr >= 0 ? curr : null);
            pNeg.push(curr !== null && curr < 0 ? curr : null);
        }
        return { dates: pDates, pos: pPos, neg: pNeg, line: pLine };
    })();

    $: maDates = maProcessed.dates;
    $: maPos = maProcessed.pos;
    $: maNeg = maProcessed.neg;
    $: maLine = maProcessed.line;

    $: mainChartData = [
        {
            x: dates,
            y: currentFlowData,
            name: t($currentTranslations, "etf_net_flows"),
            type: "bar",
            marker: { color: barColors },
            opacity: 0.8,
        },
        ...(showMA
            ? [
                  {
                      x: maDates,
                      y: maPos,
                      name: t($currentTranslations, "etf_ma"),
                      legendgroup: "ma",
                      type: "scatter",
                      mode: "lines",
                      fill: "tozeroy",
                      fillcolor: "rgba(16, 185, 129, 0.25)",
                      line: { color: "#10b981", width: 2, shape: "linear" },
                      connectgaps: false,
                  },
                  {
                      x: maDates,
                      y: maNeg,
                      name: t($currentTranslations, "etf_ma"),
                      legendgroup: "ma",
                      showlegend: false,
                      type: "scatter",
                      mode: "lines",
                      fill: "tozeroy",
                      fillcolor: "rgba(239, 68, 68, 0.25)",
                      line: { color: "#ef4444", width: 2, shape: "linear" },
                      connectgaps: false,
                  },
              ]
            : []),
        {
            x: dates,
            y: flowsAgg.cum_flow_usd,
            name: t($currentTranslations, "etf_cum_flows"),
            type: "scatter",
            mode: "lines",
            yaxis: "y2",
            line: { color: "#10b981", width: 3 },
        },
        ...(showBtcOverlay && $dashboardData.btc?.price && dates.length > 0
            ? [
                  {
                      x: dates,
                      y: (() => {
                          const btcPrices = $dashboardData.btc.price;
                          const gDates = $dashboardData.dates;
                          const firstEtfDate = dates[0];
                          const startIdx = gDates.indexOf(firstEtfDate);
                          if (startIdx === -1)
                              return btcPrices.slice(-dates.length);
                          return btcPrices.slice(
                              startIdx,
                              startIdx + dates.length,
                          );
                      })(),
                      name: "BTC Price",
                      type: "scatter",
                      mode: "lines",
                      yaxis: "y3",
                      line: { color: "#f59e0b", width: 1.5, dash: "dot" },
                  },
              ]
            : []),
    ];

    $: mainChartLayout = {
        title: `${t($currentTranslations, "etf_title")} (${chartTimeframe})`,
        yaxis: {
            title: "Net Flow ($)",
            gridcolor: $darkMode ? "#334155" : "#e2e8f0",
        },
        yaxis2: {
            title: "Cumulative Flow ($)",
            overlaying: "y",
            side: "right",
            showgrid: false,
        },
        yaxis3: {
            title: "BTC Price ($)",
            overlaying: "y",
            side: "right",
            anchor: "free",
            position: 0.95,
            showgrid: false,
            visible: showBtcOverlay,
        },
        height: 480,
        margin: { l: 60, r: 80, t: 80, b: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: true,
        legend: { orientation: "h", y: -0.2 },
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Ticker Analysis State
    let tickerMetric = "flow"; // "flow" or "prem_disc"
    let tickerMode = "individual"; // "individual" or "aggregate"
    let normalizationMode = "raw"; // "raw", "zscore", "percentile"

    $: tickerDataRaw =
        tickerMode === "aggregate"
            ? flowsAgg
            : individualDaily[selectedTicker] || {};

    $: tickerX = tickerMode === "aggregate" ? dates : tickerDataRaw.date || [];
    $: tickerY =
        tickerMetric === "flow"
            ? tickerDataRaw.total_flow_usd || tickerDataRaw.flow_usd || []
            : normalizationMode === "zscore"
              ? tickerDataRaw.pd_zscore_1y || []
              : normalizationMode === "percentile"
                ? tickerDataRaw.pd_percentile_1y || []
                : tickerDataRaw.avg_premium_discount ||
                  tickerDataRaw.premium_discount ||
                  [];

    $: tickerChartData = [
        {
            x: tickerX,
            y: tickerY,
            name: `${tickerMode === "aggregate" ? "Aggregate" : selectedTicker} ${tickerMetric === "flow" ? "Flow" : "P/D"}`,
            type: tickerMetric === "flow" ? "bar" : "scatter",
            mode: tickerMetric === "flow" ? undefined : "lines",
            marker: { color: tickerMetric === "flow" ? "#f59e0b" : undefined },
            line: {
                color: tickerMetric === "flow" ? undefined : "#3b82f6",
                width: 2,
            },
            fill: tickerMetric === "prem_disc" ? "tozeroy" : undefined,
            fillcolor:
                tickerMetric === "prem_disc"
                    ? "rgba(59, 130, 246, 0.1)"
                    : undefined,
        },
        ...(tickerMetric === "flow"
            ? [
                  {
                      x: tickerX,
                      y: (tickerY || []).reduce((acc, curr, i) => {
                          const prev = acc.length > 0 ? acc[acc.length - 1] : 0;
                          acc.push(prev + (curr || 0));
                          return acc;
                      }, []),
                      name: "Cumulative",
                      type: "scatter",
                      mode: "lines",
                      yaxis: "y2",
                      line: { color: "#8b5cf6", width: 2 },
                  },
              ]
            : []),
    ];

    $: tickerChartLayout = {
        title: `${tickerMode === "aggregate" ? "Aggregate" : selectedTicker} - ${tickerMetric === "flow" ? "Flow Analysis" : "Premium/Discount Analysis"} (${normalizationMode.toUpperCase()})`,
        yaxis: {
            title:
                tickerMetric === "flow"
                    ? "Flow ($)"
                    : normalizationMode === "raw"
                      ? "Prem/Disc (%)"
                      : normalizationMode.toUpperCase(),
            gridcolor: $darkMode ? "#334155" : "#e2e8f0",
        },
        ...(tickerMetric === "flow"
            ? {
                  yaxis2: {
                      title: "Cumulative ($)",
                      overlaying: "y",
                      side: "right",
                      showgrid: false,
                  },
              }
            : {}),
        height: 380,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b" },
        margin: { t: 40, b: 40, l: 60, r: 60 },
    };

    function formatNumber(num, decimals = 2) {
        if (num === undefined || num === null) return "0.00";
        if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(decimals) + "B";
        if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(decimals) + "M";
        return num.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    }

    onMount(() => {
        if (!$etfData) {
            fetchEtfData();
        }
    });
</script>

<div class="etfs-tab">
    {#if $etfLoading}
        <div class="loading-overlay">
            <div class="spinner"></div>
            <p>Loading ETF Data...</p>
        </div>
    {:else if !$etfData}
        <div class="error-msg">
            <p>Failed to load ETF data. Is the backend pipeline running?</p>
            <button on:click={fetchEtfData}>Retry</button>
        </div>
    {:else}
        <!-- Summary Header -->
        <div class="tab-header" class:light={!$darkMode}>
            <div class="header-content">
                <h2>{t($currentTranslations, "etf_title")}</h2>
                <p class="description">
                    Track Spot Bitcoin ETF flows, AUM growth, and market
                    premiums.
                </p>
            </div>
            <div class="header-stats">
                <div class="stat-item main">
                    <span class="stat-label"
                        >{t($currentTranslations, "etf_aum")}</span
                    >
                    <span class="stat-value">${formatNumber(totalAUM)}</span>
                </div>
                {#each statsCards as card}
                    <div class="stat-item">
                        <span class="stat-label">{card.label}</span>
                        <span
                            class="stat-value"
                            class:pos={card.value > 0}
                            class:neg={card.value < 0}
                        >
                            {card.isCurrency ? "$" : ""}{formatNumber(
                                card.value,
                                card.isPct ? 2 : 0,
                            )}{card.isPct ? "%" : ""}
                        </span>
                    </div>
                {/each}
            </div>
        </div>

        <!-- Main Chart Section -->
        <div class="chart-card full-width" class:light={!$darkMode}>
            <div class="chart-header">
                <div class="timeframe-toggles">
                    <button
                        class:active={chartTimeframe === "1D"}
                        on:click={() => (chartTimeframe = "1D")}>1D</button
                    >
                    <button
                        class:active={chartTimeframe === "7D"}
                        on:click={() => (chartTimeframe = "7D")}
                        >{t($currentTranslations, "etf_weekly")}</button
                    >
                    <button
                        class:active={chartTimeframe === "30D"}
                        on:click={() => (chartTimeframe = "30D")}
                        >{t($currentTranslations, "etf_monthly")}</button
                    >
                    <button
                        class:active={chartTimeframe === "90D"}
                        on:click={() => (chartTimeframe = "90D")}
                        >{t($currentTranslations, "etf_quarterly")}</button
                    >
                </div>
                <div class="ma-toggle">
                    <label>
                        <input type="checkbox" bind:checked={showMA} />
                        {t($currentTranslations, "etf_ma")}
                    </label>
                    <label>
                        <input type="checkbox" bind:checked={showBtcOverlay} />
                        {t($currentTranslations, "etf_btc_overlay")}
                    </label>
                </div>
            </div>
            <Chart
                data={mainChartData}
                layout={mainChartLayout}
                darkMode={$darkMode}
            />
        </div>

        <div class="bottom-grid">
            <!-- Individual Ticker Section -->
            <div class="card ticker-section">
                <div class="card-header">
                    <div class="header-main">
                        <h3>
                            {t($currentTranslations, "etf_ticker")} Analysis
                        </h3>
                        <div class="ticker-mode-selector">
                            <button
                                class:active={tickerMetric === "flow"}
                                on:click={() => (tickerMetric = "flow")}
                            >
                                {t($currentTranslations, "etf_net_flows")}
                            </button>
                            <button
                                class:active={tickerMetric === "prem_disc"}
                                on:click={() => (tickerMetric = "prem_disc")}
                            >
                                {t($currentTranslations, "etf_prem_disc")}
                            </button>
                        </div>
                    </div>
                    <div class="ticker-controls">
                        <label class="agg-checkbox">
                            <input
                                type="checkbox"
                                checked={tickerMode === "aggregate"}
                                on:change={(e) =>
                                    (tickerMode = e.currentTarget.checked
                                        ? "aggregate"
                                        : "individual")}
                            />
                            {t($currentTranslations, "etf_aggregate") ||
                                "Aggregate"}
                        </label>

                        {#if tickerMetric === "prem_disc"}
                            <div class="ticker-mode-selector">
                                <button
                                    class:active={normalizationMode === "raw"}
                                    on:click={() => (normalizationMode = "raw")}
                                >
                                    {t($currentTranslations, "view_raw") ||
                                        "Raw"}
                                </button>
                                <button
                                    class:active={normalizationMode ===
                                        "zscore"}
                                    on:click={() =>
                                        (normalizationMode = "zscore")}
                                >
                                    Z-Score
                                </button>
                                <button
                                    class:active={normalizationMode ===
                                        "percentile"}
                                    on:click={() =>
                                        (normalizationMode = "percentile")}
                                >
                                    %ile
                                </button>
                            </div>
                        {/if}

                        {#if tickerMode === "individual"}
                            <Dropdown
                                options={tickerOptions}
                                bind:value={selectedTicker}
                                darkMode={$darkMode}
                            />
                        {/if}
                    </div>
                </div>
                <div class="ticker-chart-wrapper">
                    <Chart
                        data={tickerChartData}
                        layout={tickerChartLayout}
                        darkMode={$darkMode}
                    />
                </div>
            </div>

            <!-- summary Table -->
            <div class="card table-card">
                <div class="card-header">
                    <h3>{t($currentTranslations, "etf_summary_all")}</h3>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>{t($currentTranslations, "etf_ticker")}</th>
                                <th class="text-right"
                                    >{t($currentTranslations, "etf_aum")}</th
                                >
                                <th class="text-right"
                                    >{t(
                                        $currentTranslations,
                                        "etf_prem_disc",
                                    )}</th
                                >
                                <th class="text-right"
                                    >{t($currentTranslations, "etf_nav")}</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            {#each summary as row}
                                <tr>
                                    <td>
                                        <div class="ticker-cell">
                                            <span class="ticker-badge"
                                                >{row.ticker}</span
                                            >
                                            <span class="provider"
                                                >{row.provider_name ||
                                                    row.issuer}</span
                                            >
                                        </div>
                                    </td>
                                    <td class="text-right"
                                        >${formatNumber(row.aum_usd)}</td
                                    >
                                    <td
                                        class="text-right"
                                        class:pos={row.premium_discount > 0}
                                        class:neg={row.premium_discount < 0}
                                        >{formatNumber(
                                            row.premium_discount,
                                            2,
                                        )}%</td
                                    >
                                    <td class="text-right"
                                        >${formatNumber(row.nav)}</td
                                    >
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .etfs-tab {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        padding: 1rem;
        color: var(--text-color);
        min-height: 400px;
        position: relative;
    }

    .loading-overlay {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        height: 400px;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(59, 130, 246, 0.1);
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* Dashboard Standard Styles */
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }

    .header-content h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .header-content .description {
        margin: 4px 0 0 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .header-stats {
        display: flex;
        gap: 20px;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }

    .stat-item.main .stat-value {
        color: #3b82f6;
        font-size: 1.5rem;
    }

    .stat-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .pos {
        color: #10b981;
    }
    .neg {
        color: #ef4444;
    }

    .chart-card {
        background: var(--card-bg);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .full-width {
        grid-column: 1 / -1;
    }

    .card {
        background: var(--card-bg);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 20px;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
    }

    .card-header h3 {
        margin: 0;
        font-size: 1.125rem;
        font-weight: 600;
    }

    .bottom-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
    }

    @media (max-width: 1024px) {
        .bottom-grid {
            grid-template-columns: 1fr;
        }
    }

    .table-wrapper {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th {
        text-align: left;
        padding: 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border-color);
        text-transform: uppercase;
    }

    td {
        padding: 1rem 0.75rem;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.875rem;
    }

    .text-right {
        text-align: right;
    }

    .ticker-cell {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .ticker-badge {
        background: #3b82f620;
        color: #3b82f6;
        padding: 0.125rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 700;
        font-family: monospace;
        width: fit-content;
    }

    .provider {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    :global(.dark) .chart-card,
    :global(.dark) .card {
        background: #0f172a;
        border-color: #1e293b;
    }

    :global(.dark) .ticker-badge {
        background: #3b82f630;
    }

    .timeframe-toggles {
        display: flex;
        gap: 0.5rem;
    }

    .timeframe-toggles button {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 0.35rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        color: var(--text-muted);
    }

    .timeframe-toggles button.active {
        background: #3b82f6;
        color: #f8fafc;
        border-color: #3b82f6;
    }

    .ma-toggle {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        font-weight: 600;
    }

    .ma-toggle input {
        cursor: pointer;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .header-main {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .ticker-mode-selector {
        display: flex;
        background: var(--bg-secondary);
        padding: 2px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }

    .ticker-mode-selector button {
        padding: 4px 12px;
        font-size: 0.75rem;
        background: transparent;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .ticker-mode-selector button.active {
        background: var(--card-bg);
        color: var(--text-color);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .ticker-controls {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .agg-checkbox {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        color: var(--text-muted);
        cursor: pointer;
        padding: 4px 8px;
        background: var(--bg-secondary);
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }

    .agg-checkbox input {
        cursor: pointer;
    }

    .ticker-chart-wrapper {
        min-height: 380px;
    }
</style>
