<script>
    /**
     * OffshoreLiquidityTab.svelte
     * Monitors offshore USD funding stress (Eurodollar market, shadow banking)
     *
     * Chart 1: FRED Proxy - OBFR-EFFR spread + CB Swap Lines
     * Chart 2: XCCY Basis - DIY cross-currency basis calculation
     */
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    export let darkMode = true;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};

    // Reactive data extraction
    $: offshoreData = dashboardData.offshore_liquidity || {};
    $: chart1 = offshoreData.chart1_fred_proxy || {};
    $: chart2 = offshoreData.chart2_xccy_diy || null;
    $: thresholds = offshoreData.thresholds || {};

    // Time range state
    let selectedRange = "365";
    const timeRanges = [
        { label: "30D", value: "30" },
        { label: "90D", value: "90" },
        { label: "1Y", value: "365" },
        { label: "2Y", value: "730" },
        { label: "All", value: "9999" },
    ];

    // Filter and transform function
    function getFilteredData(dates, values, rangeStr) {
        if (!dates || !values || dates.length === 0) return [];

        const range = parseInt(rangeStr);
        let startIndex = 0;
        if (range < 9999) {
            const lastDate = new Date(dates[dates.length - 1]);
            const cutoffDate = new Date(lastDate);
            cutoffDate.setDate(cutoffDate.getDate() - range);
            const cutoffStr = cutoffDate.toISOString().split("T")[0];
            startIndex = dates.findIndex((d) => d >= cutoffStr);
            if (startIndex === -1) startIndex = 0;
        }

        const filteredDates = dates.slice(startIndex);
        const filteredValues = values.slice(startIndex);

        return filteredDates
            .map((date, i) => ({
                time: date,
                value: filteredValues[i] ?? null,
            }))
            .filter((d) => d.value !== null);
    }

    // Chart 1: FRED Proxy - Reactive Data
    $: spreadChartData = [
        {
            name: translations.obfr_effr_title || "OBFR-EFFR Spread",
            data: getFilteredData(
                chart1.dates,
                chart1.obfr_effr_spread,
                selectedRange,
            ),
            color: "#60a5fa",
            type: "line",
        },
    ];

    $: swapsChartData = [
        {
            name: translations.cb_swaps_title || "CB Swaps",
            data: getFilteredData(
                chart1.dates,
                chart1.cb_swaps_b,
                selectedRange,
            ),
            color: "#f59e0b",
            type: "histogram",
        },
    ];

    // Chart 2: XCCY Basis - Reactive Data
    $: xccyChartData = chart2
        ? [
              {
                  name: "EUR/USD",
                  data: getFilteredData(
                      chart2.dates,
                      chart2.xccy_eurusd,
                      selectedRange,
                  ),
                  color: "#3b82f6",
                  type: "line",
              },
              {
                  name: "USD/JPY",
                  data: getFilteredData(
                      chart2.dates,
                      chart2.xccy_usdjpy,
                      selectedRange,
                  ),
                  color: "#ef4444",
                  type: "line",
              },
              {
                  name: "GBP/USD",
                  data: getFilteredData(
                      chart2.dates,
                      chart2.xccy_gbpusd,
                      selectedRange,
                  ),
                  color: "#10b981",
                  type: "line",
              },
          ]
        : [];

    // Stress level badge styling
    function getStressColor(level) {
        const colors = {
            normal: "#22c55e",
            elevated: "#f59e0b",
            stressed: "#ef4444",
            critical: "#dc2626",
        };
        return colors[level] || "#6b7280";
    }

    function getStressLabel(level) {
        const key = `offshore_stress_${level}`;
        return (
            translations[key] ||
            level?.charAt(0).toUpperCase() + level?.slice(1) ||
            "Unknown"
        );
    }

    // Format helpers
    function formatBp(val) {
        if (val == null) return "—";
        return `${val >= 0 ? "+" : ""}${val.toFixed(1)} bp`;
    }

    function formatBn(val) {
        if (val == null) return "—";
        return `$${val.toFixed(1)}B`;
    }

    function formatZ(val) {
        if (val == null) return "—";
        return `${val >= 0 ? "+" : ""}${val.toFixed(2)}σ`;
    }

    // Determine current language
    $: lang = language || translations.current_language || "en";

    // Show methodology toggle
    let showMethodology = false;
</script>

<div class="offshore-tab" class:dark={darkMode}>
    <!-- Header -->
    <div class="tab-header">
        <div class="header-left">
            <span class="icon">🌊</span>
            <div class="header-text">
                <h2>
                    {translations.offshore_title ||
                        "Offshore Dollar Liquidity & Shadow Banking"}
                </h2>
                <p class="subtitle">
                    {translations.offshore_desc ||
                        "Monitors USD funding stress outside the Fed system"}
                </p>
            </div>
        </div>
        <TimeRangeSelector bind:selectedRange ranges={timeRanges} />
    </div>

    <!-- Professional Analysis Section -->
    {#if offshoreData.analysis && offshoreData.analysis[lang]}
        <div class="analysis-section">
            <div class="analysis-grid">
                {#each offshoreData.analysis[lang] as item}
                    <div class="analysis-item {item.level}">
                        <div class="item-header">
                            <span class="item-icon">{item.icon}</span>
                            <div class="item-meta">
                                <span class="item-title">{item.title}</span>
                                <span class="item-badge"
                                    >{item.level.toUpperCase()}</span
                                >
                            </div>
                        </div>
                        <p class="item-text">{item.text}</p>
                    </div>
                {/each}
            </div>
        </div>
    {/if}

    <!-- Chart 1: FRED Proxy -->
    <div class="chart-card">
        <div class="card-header">
            <div class="card-title-row">
                <h3>
                    {translations.fred_proxy_title || "FRED Proxy Indicators"}
                </h3>
                <span
                    class="stress-badge"
                    style="background-color: {getStressColor(
                        chart1.stress_level,
                    )};"
                >
                    {getStressLabel(chart1.stress_level)}
                </span>
            </div>
            <p class="card-desc">
                {translations.obfr_effr_desc ||
                    "Offshore vs onshore funding cost differential (bp)"}
            </p>
        </div>

        <div class="metrics-row">
            <div class="metric">
                <span class="metric-label"
                    >{translations.obfr_effr_title || "OBFR-EFFR Spread"}</span
                >
                <span
                    class="metric-value"
                    style="color: {chart1.latest?.obfr_effr_spread > 6
                        ? '#ef4444'
                        : '#22c55e'}"
                >
                    {formatBp(chart1.latest?.obfr_effr_spread)}
                </span>
                <span class="metric-sub"
                    >{formatZ(chart1.latest?.spread_zscore)} ({chart1.latest?.spread_percentile?.toFixed(
                        0,
                    )}%)</span
                >
            </div>
            <div class="metric">
                <span class="metric-label"
                    >{translations.cb_swaps_title || "CB Swaps"}</span
                >
                <span
                    class="metric-value"
                    style="color: {chart1.latest?.cb_swaps_b > 10
                        ? '#f59e0b'
                        : '#6b7280'}"
                >
                    {formatBn(chart1.latest?.cb_swaps_b)}
                </span>
                <span class="metric-sub"
                    >{chart1.latest?.swaps_percentile > 0
                        ? `Pct: ${chart1.latest.swaps_percentile.toFixed(0)}%`
                        : "Inactive"}</span
                >
            </div>
            <div class="metric">
                <span class="metric-label"
                    >{translations.stress_level_label || "Stress Level"}</span
                >
                <span
                    class="metric-value"
                    style="color: {getStressColor(chart1.stress_level)}"
                >
                    {chart1.stress_score?.toFixed(0) || 0}/100
                </span>
                <span class="metric-sub"
                    >{getStressLabel(chart1.stress_level)}</span
                >
            </div>
        </div>

        {#if spreadChartData[0].data.length > 0}
            <div class="chart-container">
                <LightweightChart {darkMode} data={spreadChartData} />
            </div>

            {#if chart1.latest?.cb_swaps_b > 0.1 || swapsChartData[0].data.some((d) => d.value > 0)}
                <div class="chart-container" style="margin-top: 16px;">
                    <h4
                        style="margin: 0 0 8px 0; color: #94a3b8; font-size: 13px;"
                    >
                        {translations.cb_swaps_title || "Fed CB Swap Lines"} ($B)
                    </h4>
                    <LightweightChart {darkMode} data={swapsChartData} />
                </div>
            {/if}
        {:else}
            <p class="no-data">
                {translations.no_data || "No data available for this range"}
            </p>
        {/if}
    </div>

    <!-- Chart 2: XCCY Basis (Conditional) -->
    {#if chart2 && xccyChartData && xccyChartData.length > 0 && xccyChartData[0].data.length > 0}
        <div class="chart-card">
            <div class="card-header">
                <div class="card-title-row">
                    <h3>{translations.xccy_title || "Cross-Currency Basis"}</h3>
                    <span
                        class="stress-badge"
                        style="background-color: {getStressColor(
                            chart2.stress_level,
                        )};"
                    >
                        {getStressLabel(chart2.stress_level)}
                    </span>
                </div>
                <p class="card-desc">
                    {translations.xccy_desc ||
                        "CIP deviation for major currency pairs (bp)"}
                </p>
            </div>

            <div class="metrics-row">
                <div class="metric">
                    <span class="metric-label">EUR/USD Basis</span>
                    <span
                        class="metric-value"
                        style="color: {(chart2.latest?.xccy_eurusd || 0) < -25
                            ? '#ef4444'
                            : '#22c55e'}"
                    >
                        {formatBp(chart2.latest?.xccy_eurusd)}
                    </span>
                    <span class="metric-sub"
                        >{translations.xccy_label || "Cross-Currency"}</span
                    >
                </div>
                <div class="metric">
                    <span class="metric-label">USD/JPY Basis</span>
                    <span
                        class="metric-value"
                        style="color: {(chart2.latest?.xccy_usdjpy || 0) >
                            100 || (chart2.latest?.xccy_usdjpy || 0) < -40
                            ? '#f59e0b'
                            : '#22c55e'}"
                    >
                        {formatBp(chart2.latest?.xccy_usdjpy)}
                    </span>
                    <span class="metric-sub"
                        >{chart2.latest?.xccy_usdjpy > 100
                            ? "Wide Basis"
                            : "Stable"}</span
                    >
                </div>
                <div class="metric">
                    <span class="metric-label"
                        >{translations.stress_level_label ||
                            "Composite Stress"}</span
                    >
                    <span
                        class="metric-value"
                        style="color: {getStressColor(chart2.stress_level)}"
                    >
                        {formatZ(chart2.latest?.zscore)}
                    </span>
                    <span class="metric-sub"
                        >Pct: {chart2.latest?.percentile?.toFixed(0)}%</span
                    >
                </div>
            </div>

            <div class="chart-container">
                <LightweightChart {darkMode} data={xccyChartData} />
            </div>
        </div>
    {/if}

    <!-- Methodology Section -->
    <div class="methodology-section">
        <button
            class="methodology-toggle"
            on:click={() => (showMethodology = !showMethodology)}
        >
            <span class="toggle-icon">{showMethodology ? "−" : "ℹ️"}</span>
            {translations.offshore_methodology_title || "Methodology"}
        </button>

        {#if showMethodology}
            <div class="methodology-content">
                <p>
                    {translations.offshore_methodology_desc ||
                        "OBFR includes Eurodollar transactions (offshore USD). Negative XCCY basis indicates USD funding premium. Higher stress = global dollar shortage."}
                </p>

                <div class="thresholds-grid">
                    <div class="threshold-item">
                        <h5>OBFR-EFFR Spread</h5>
                        <ul>
                            <li>
                                <span class="dot normal"></span> Normal: &lt; 3bp
                            </li>
                            <li>
                                <span class="dot elevated"></span> Elevated: 3-6bp
                            </li>
                            <li>
                                <span class="dot stressed"></span> Stressed: 6-10bp
                            </li>
                            <li>
                                <span class="dot critical"></span> Critical: &gt;
                                15bp
                            </li>
                        </ul>
                    </div>
                    <div class="threshold-item">
                        <h5>CB Swap Lines</h5>
                        <ul>
                            <li>
                                <span class="dot normal"></span> Inactive: $0
                            </li>
                            <li>
                                <span class="dot elevated"></span> Active: $10-50B
                            </li>
                            <li>
                                <span class="dot stressed"></span> Stressed: $50-100B
                            </li>
                            <li>
                                <span class="dot critical"></span> Crisis: &gt; $100B
                            </li>
                        </ul>
                    </div>
                    <div class="threshold-item">
                        <h5>XCCY Basis</h5>
                        <ul>
                            <li>
                                <span class="dot normal"></span> Normal: &gt; -10bp
                            </li>
                            <li>
                                <span class="dot elevated"></span> Elevated: -10
                                to -20bp
                            </li>
                            <li>
                                <span class="dot stressed"></span> Stressed: -20
                                to -35bp
                            </li>
                            <li>
                                <span class="dot critical"></span> Crisis: &lt; -50bp
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    .offshore-tab {
        padding: 24px;
        color: #f1f5f9;
        min-height: 100vh;
    }

    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 16px;
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .icon {
        font-size: 32px;
    }

    .header-text h2 {
        font-size: 22px;
        font-weight: 700;
        margin: 0;
        color: #f8fafc;
    }

    .subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin: 4px 0 0 0;
    }

    .chart-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
    }

    .card-header {
        margin-bottom: 20px;
    }

    .card-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }

    /* Analysis Section & Grid */
    .analysis-section {
        margin-bottom: 32px;
    }

    .analysis-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
    }

    .analysis-item {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-left: 4px solid #64748b;
        border-radius: 12px;
        padding: 16px;
        transition: all 0.2s ease;
    }

    .analysis-item:hover {
        transform: translateY(-2px);
        background: rgba(15, 23, 42, 0.6);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }

    .analysis-item.critical {
        border-left-color: #ef4444;
        background: linear-gradient(
            90deg,
            rgba(239, 68, 68, 0.05),
            transparent
        );
    }
    .analysis-item.warning {
        border-left-color: #f59e0b;
        background: linear-gradient(
            90deg,
            rgba(245, 158, 11, 0.05),
            transparent
        );
    }
    .analysis-item.info {
        border-left-color: #3b82f6;
        background: linear-gradient(
            90deg,
            rgba(59, 130, 246, 0.05),
            transparent
        );
    }
    .analysis-item.success {
        border-left-color: #10b981;
        background: linear-gradient(
            90deg,
            rgba(16, 185, 129, 0.05),
            transparent
        );
    }

    .item-header {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 10px;
    }

    .item-icon {
        font-size: 20px;
        padding-top: 2px;
    }

    .item-meta {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .item-title {
        font-size: 14px;
        font-weight: 700;
        color: #f1f5f9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .item-badge {
        font-size: 9px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        width: fit-content;
        letter-spacing: 0.5px;
    }

    .critical .item-badge {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }
    .warning .item-badge {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
    }
    .info .item-badge {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
    }
    .success .item-badge {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
    }

    .item-text {
        font-size: 13.5px;
        line-height: 1.5;
        color: #cbd5e1;
        margin: 0;
    }

    .card-header h3 {
        font-size: 18px;
        font-weight: 600;
        margin: 0;
        color: #f8fafc;
    }

    .card-desc {
        font-size: 13px;
        color: #64748b;
        margin: 0;
    }

    .stress-badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        color: #0f172a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .metrics-row {
        display: flex;
        gap: 24px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }

    .metric {
        display: flex;
        flex-direction: column;
        gap: 4px;
        min-width: 120px;
    }

    .metric-label {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
    }

    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #f8fafc;
        margin: 2px 0;
    }

    .metric-sub {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
    }

    .chart-container {
        width: 100%;
    }

    .no-data {
        text-align: center;
        color: #64748b;
        padding: 40px 0;
    }

    /* Methodology Section */
    .methodology-section {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
    }

    .methodology-toggle {
        display: flex;
        align-items: center;
        gap: 10px;
        background: transparent;
        border: none;
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        padding: 4px 8px;
        border-radius: 8px;
        transition: all 0.2s;
    }

    .methodology-toggle:hover {
        color: #f8fafc;
        background: rgba(255, 255, 255, 0.04);
    }

    .toggle-icon {
        font-size: 16px;
    }

    .methodology-content {
        padding-top: 16px;
        animation: fadeIn 0.3s ease-out;
    }

    .methodology-content p {
        color: #cbd5e1;
        font-size: 14px;
        line-height: 1.6;
        margin: 0 0 20px 0;
    }

    .thresholds-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 20px;
    }

    .threshold-item h5 {
        font-size: 12px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin: 0 0 10px 0;
    }

    .threshold-item ul {
        list-style: none;
        margin: 0;
        padding: 0;
    }

    .threshold-item li {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: #cbd5e1;
        margin-bottom: 6px;
    }

    .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }

    .dot.normal {
        background: #22c55e;
    }
    .dot.elevated {
        background: #f59e0b;
    }
    .dot.stressed {
        background: #ef4444;
    }
    .dot.critical {
        background: #dc2626;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
