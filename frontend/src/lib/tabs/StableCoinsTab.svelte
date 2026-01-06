<script>
    /**
     * StableCoinsTab.svelte
     * Displays stablecoin market caps, growth trends, and depeg monitoring.
     * Part of the Macro section under Liquidity.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    // Core props
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges and modes
    let aggregateRange = "1Y";
    let individualRange = "1Y";
    let aggregateMode = "absolute"; // Modes: absolute, roc1m, roc3m, yoy, accel_z
    let showModeDropdown = false;

    const aggregateModes = [
        { value: "absolute", label: "Absolute" },
        { value: "roc1m", label: "ROC 1M" },
        { value: "roc3m", label: "ROC 3M" },
        { value: "yoy", label: "YoY %" },
        { value: "accel_z", label: "Accel Z-Score" },
    ];

    function selectMode(mode) {
        aggregateMode = mode;
        showModeDropdown = false;
    }

    // Close dropdown on click outside
    function handleClickOutside(event) {
        if (showModeDropdown && !event.target.closest(".custom-dropdown")) {
            showModeDropdown = false;
        }
    }

    import { onMount as onSvelteMount } from "svelte";
    onSvelteMount(() => {
        window.addEventListener("click", handleClickOutside);
        return () => window.removeEventListener("click", handleClickOutside);
    });

    // Existing aggregate chart logic...

    // Card container references for download feature
    let aggregateCard;
    let growthCard;
    let depegCard;

    // Helper to get translation with fallback
    const t = (key, fallback) => translations[key] || fallback;

    // Stablecoin colors
    const stablecoinColors = {
        USDT: "#26A17B", // Tether green
        USDC: "#2775CA", // Circle blue
        DAI: "#F5AC37", // MakerDAO gold
        TUSD: "#1A5AFF", // TrueUSD blue
        USDD: "#00D395", // USDD teal
        USDP: "#00A3FF", // Pax blue
        USDE: "#00FFD1", // Ethena teal
        PYUSD: "#0070BA", // PayPal blue
        FDUSD: "#F1B500", // FDUSD gold
        RLUSD: "#00AAE4", // Ripple blue
        USDG: "#4F46E5", // Global Dollar
        USD1W: "#8B5CF6", // USD1W violet
    };

    // Get stablecoin data from dashboardData
    $: stablecoinsData = dashboardData.stablecoins || {};
    $: stableDates = stablecoinsData.dates || [];
    $: marketCaps = stablecoinsData.market_caps || {};
    $: totalSupply = stablecoinsData.total || [];
    $: prices = stablecoinsData.prices || {};
    $: growth = stablecoinsData.growth || {};
    $: dominance = stablecoinsData.dominance || {};
    $: depegEvents = stablecoinsData.depeg_events || [];

    // Calculate latest values
    $: latestTotal =
        totalSupply.length > 0 ? totalSupply[totalSupply.length - 1] : 0;
    $: latestTotalFormatted = latestTotal
        ? `$${latestTotal.toFixed(1)}B`
        : "N/A";

    // Aggregate chart data
    $: aggregateChartData = filterPlotlyData(
        [
            (() => {
                let yData = totalSupply;
                let name = t(
                    "stablecoins_aggregate",
                    "Total Stablecoin Supply",
                );
                let type = "scatter";
                let fill = "tozeroy";
                let color = "#6366f1";

                if (aggregateMode === "roc1m") {
                    yData = stablecoinsData.total_roc_1m || [];
                    name = "ROC 1M (%)";
                    color = "#10b981"; // emerald
                } else if (aggregateMode === "roc3m") {
                    yData = stablecoinsData.total_roc_3m || [];
                    name = "ROC 3M (%)";
                    color = "#3b82f6"; // blue
                } else if (aggregateMode === "yoy") {
                    yData = stablecoinsData.total_yoy || [];
                    name = "YoY Change (%)";
                    color = "#f43f5e"; // rose
                } else if (aggregateMode === "accel_z") {
                    yData = stablecoinsData.total_accel_z || [];
                    name = "Acceleration Z-Score";
                    type = "bar";
                    fill = "none";
                    color = "#8b5cf6"; // violet
                }

                const trace = {
                    x: stableDates,
                    y: yData,
                    name: name,
                    type: type,
                };

                if (type === "bar") {
                    trace.marker = { color: color };
                } else {
                    trace.mode = "lines";
                    trace.fill = fill;
                    trace.line = { color: color, width: 2, shape: "spline" };
                    if (darkMode) {
                        // Simple hex to rgba conversion for the fill
                        const r = parseInt(color.slice(1, 3), 16);
                        const g = parseInt(color.slice(3, 5), 16);
                        const b = parseInt(color.slice(5, 7), 16);
                        trace.fillcolor = `rgba(${r}, ${g}, ${b}, 0.15)`;
                    } else {
                        trace.fillcolor = "rgba(99, 102, 241, 0.1)";
                    }
                }

                return trace;
            })(),
        ],
        stableDates,
        aggregateRange,
    );

    // Individual stablecoin traces
    $: individualTraces = Object.entries(marketCaps).map(([name, values]) => ({
        x: stableDates,
        y: values,
        name: name,
        type: "scatter",
        mode: "lines",
        line: {
            color: stablecoinColors[name] || "#888888",
            width: 2,
            shape: "spline",
        },
    }));

    $: individualChartData = filterPlotlyData(
        individualTraces,
        stableDates,
        individualRange,
    );

    // Growth table data (sorted by 30d growth)
    $: growthTableData = Object.entries(growth)
        .map(([name, g]) => ({
            name,
            color: stablecoinColors[name] || "#888888",
            mcap:
                marketCaps[name]?.length > 0
                    ? marketCaps[name][marketCaps[name].length - 1]
                    : 0,
            dom:
                dominance[name]?.length > 0
                    ? dominance[name][dominance[name].length - 1]
                    : 0,
            growth7d: g["7d"] || 0,
            growth30d: g["30d"] || 0,
            growth90d: g["90d"] || 0,
        }))
        .sort((a, b) => b.growth30d - a.growth30d);

    // Current depeg status
    $: currentDepegs = Object.entries(prices).map(([name, priceArr]) => {
        const lastPrice =
            priceArr.length > 0 ? priceArr[priceArr.length - 1] : 1.0;
        const deviation = (lastPrice - 1.0) * 100;
        const isDepegged = Math.abs(deviation) > 1.0;
        return {
            name,
            price: lastPrice,
            deviation,
            isDepegged,
            color: stablecoinColors[name] || "#888888",
        };
    });

    // Recent depeg events (last 10)
    $: recentDepegs = depegEvents.slice(-10).reverse();

    // Format number with color
    const formatGrowth = (val) => {
        if (val === undefined || val === null) return "N/A";
        const sign = val >= 0 ? "+" : "";
        return `${sign}${val.toFixed(2)}%`;
    };

    const getGrowthClass = (val) => {
        if (val === undefined || val === null) return "";
        return val >= 0 ? "positive" : "negative";
    };
</script>

<!-- Header -->
<div class="tab-header" class:light={!darkMode}>
    <div class="header-content">
        <h2>{t("stablecoins_title", "Stablecoin Market Overview")}</h2>
        <p class="description">
            {t(
                "stablecoins_desc",
                "Track stablecoin market caps, growth trends, and depeg events.",
            )}
        </p>
    </div>
    <div class="header-stats">
        <div class="stat-item">
            <span class="stat-label"
                >{t("stablecoins_aggregate", "Total Supply")}</span
            >
            <span class="stat-value">{latestTotalFormatted}</span>
        </div>
    </div>
</div>

<!-- Main Grid -->
<div class="stablecoins-grid" class:light={!darkMode}>
    <!-- Aggregate Supply Chart -->
    <div class="chart-card full-width" bind:this={aggregateCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_aggregate", "Total Stablecoin Supply")}</h3>
            <div class="header-controls">
                <div class="custom-dropdown" class:active={showModeDropdown}>
                    <button
                        class="dropdown-trigger"
                        class:light={!darkMode}
                        on:click={() => (showModeDropdown = !showModeDropdown)}
                    >
                        {aggregateModes.find((m) => m.value === aggregateMode)
                            ?.label}
                        <span class="arrow">▾</span>
                    </button>
                    {#if showModeDropdown}
                        <div class="dropdown-menu" class:light={!darkMode}>
                            {#each aggregateModes as mode}
                                <button
                                    class="dropdown-item"
                                    class:selected={aggregateMode ===
                                        mode.value}
                                    on:click={() => selectMode(mode.value)}
                                >
                                    {mode.label}
                                </button>
                            {/each}
                        </div>
                    {/if}
                </div>
                <TimeRangeSelector
                    selectedRange={aggregateRange}
                    onRangeChange={(r) => (aggregateRange = r)}
                />
                <button
                    class="download-btn"
                    title="Download Chart"
                    on:click={() =>
                        downloadCardAsImage(
                            aggregateCard,
                            "stablecoin_aggregate",
                        )}
                >
                    📥
                </button>
            </div>
        </div>
        <div class="chart-content">
            {#if aggregateChartData && aggregateChartData.length > 0}
                <Chart
                    data={aggregateChartData}
                    layout={{ title: "" }}
                    {darkMode}
                />
            {:else}
                <div class="no-data">No stablecoin data available</div>
            {/if}
        </div>
    </div>

    <!-- Individual Stablecoins Chart -->
    <div class="chart-card full-width">
        <div class="chart-header">
            <h3>{t("stablecoins_individual", "Individual Stablecoins")}</h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={individualRange}
                    onRangeChange={(r) => (individualRange = r)}
                />
            </div>
        </div>
        <div class="chart-content">
            {#if individualChartData && individualChartData.length > 0}
                <Chart
                    data={individualChartData}
                    layout={{ title: "" }}
                    {darkMode}
                />
            {:else}
                <div class="no-data">No individual stablecoin data</div>
            {/if}
        </div>
    </div>

    <!-- Growth Analysis Table -->
    <div class="chart-card" bind:this={growthCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_growth_table", "Growth Analysis")}</h3>
            <button
                class="download-btn"
                title="Download Table"
                on:click={() =>
                    downloadCardAsImage(growthCard, "stablecoin_growth")}
            >
                📥
            </button>
        </div>
        <div class="table-container">
            <table class="growth-table">
                <thead>
                    <tr>
                        <th>{t("stablecoins_name", "Stablecoin")}</th>
                        <th>{t("stablecoins_market_cap", "Market Cap")}</th>
                        <th>{t("stablecoins_dominance", "Dom.")}</th>
                        <th>{t("stablecoins_7d_change", "7D")}</th>
                        <th>{t("stablecoins_30d_change", "30D")}</th>
                        <th>{t("stablecoins_90d_change", "90D")}</th>
                    </tr>
                </thead>
                <tbody>
                    {#each growthTableData as item}
                        <tr>
                            <td class="name-cell">
                                <span
                                    class="color-dot"
                                    style="background: {item.color}"
                                ></span>
                                {item.name}
                            </td>
                            <td>${item.mcap?.toFixed(1) || 0}B</td>
                            <td>{item.dom?.toFixed(1) || 0}%</td>
                            <td class={getGrowthClass(item.growth7d)}
                                >{formatGrowth(item.growth7d)}</td
                            >
                            <td class={getGrowthClass(item.growth30d)}
                                >{formatGrowth(item.growth30d)}</td
                            >
                            <td class={getGrowthClass(item.growth90d)}
                                >{formatGrowth(item.growth90d)}</td
                            >
                        </tr>
                    {:else}
                        <tr
                            ><td colspan="6" class="no-data"
                                >No growth data available</td
                            ></tr
                        >
                    {/each}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Depeg Monitor -->
    <div class="chart-card" bind:this={depegCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_depeg_monitor", "Depeg Monitor")}</h3>
            <button
                class="download-btn"
                title="Download Monitor"
                on:click={() => downloadCardAsImage(depegCard, "depeg_monitor")}
            >
                📥
            </button>
        </div>
        <div class="depeg-content">
            <!-- Current Status -->
            <div class="depeg-current">
                <h4>{t("stablecoins_current_status", "Current Status")}</h4>
                <div class="depeg-grid">
                    {#each currentDepegs as dp}
                        <div class="depeg-item" class:depegged={dp.isDepegged}>
                            <span class="depeg-name" style="color: {dp.color}"
                                >{dp.name}</span
                            >
                            <span class="depeg-price"
                                >${dp.price?.toFixed(4) || "1.0000"}</span
                            >
                            <span
                                class="depeg-deviation"
                                class:positive={dp.deviation > 0}
                                class:negative={dp.deviation < 0}
                            >
                                {dp.deviation >= 0
                                    ? "+"
                                    : ""}{dp.deviation?.toFixed(2) || 0}%
                            </span>
                            <span class="depeg-status">
                                {dp.isDepegged
                                    ? t("stablecoins_depeg_alert", "⚠️ DEPEG")
                                    : t("stablecoins_stable", "✅ Stable")}
                            </span>
                        </div>
                    {:else}
                        <div class="no-data">No price data available</div>
                    {/each}
                </div>
            </div>

            <!-- Recent Events -->
            {#if recentDepegs.length > 0}
                <div class="depeg-history">
                    <h4>
                        {t("stablecoins_recent_events", "Recent Depeg Events")}
                    </h4>
                    <div class="events-list">
                        {#each recentDepegs as event}
                            <div class="event-item">
                                <span class="event-date">{event.date}</span>
                                <span
                                    class="event-stable"
                                    style="color: {stablecoinColors[
                                        event.stablecoin
                                    ]}">{event.stablecoin}</span
                                >
                                <span class="event-price"
                                    >${event.price?.toFixed(4)}</span
                                >
                                <span
                                    class="event-dev"
                                    class:negative={event.deviation_pct < 0}
                                >
                                    {event.deviation_pct?.toFixed(2)}%
                                </span>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        margin-bottom: 20px;
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    .tab-header.light {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .header-content h2 {
        margin: 0 0 8px 0;
        font-size: 1.5rem;
        color: var(--text-primary);
    }
    .light .header-content h2 {
        color: #1e293b;
    }
    .description {
        margin: 0;
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    .header-stats {
        display: flex;
        gap: 24px;
    }
    .stat-item {
        text-align: right;
    }
    .stat-label {
        display: block;
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #6366f1;
        font-family: "JetBrains Mono", monospace;
    }

    .stablecoins-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
    }
    .chart-card.full-width {
        grid-column: 1 / -1;
    }
    .light .chart-card {
        background: #ffffff;
        border-color: #e2e8f0;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .chart-header h3 {
        margin: 0;
        font-size: 1rem;
        color: var(--text-primary);
    }
    .light .chart-header h3 {
        color: #1e293b;
    }
    .header-controls {
        display: flex;
        gap: 12px;
        align-items: center;
    }

    /* Custom Dropdown */
    .custom-dropdown {
        position: relative;
        z-index: 100;
    }

    .dropdown-trigger {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: white;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.8rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s;
        min-width: 110px;
        justify-content: space-between;
    }

    .dropdown-trigger:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .dropdown-trigger.light {
        background: rgba(0, 0, 0, 0.03);
        border-color: rgba(0, 0, 0, 0.1);
        color: #1e293b;
    }

    .dropdown-trigger.light:hover {
        background: rgba(0, 0, 0, 0.05);
    }

    .dropdown-menu {
        position: absolute;
        top: calc(100% + 5px);
        left: 0;
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 4px;
        min-width: 140px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        gap: 2px;
        backdrop-filter: blur(12px);
    }

    .dropdown-menu.light {
        background: white;
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }

    .dropdown-item {
        background: transparent;
        border: none;
        color: #94a3b8;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 0.8rem;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }

    .dropdown-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: white;
    }

    .dropdown-item.selected {
        background: rgba(99, 102, 241, 0.1);
        color: #818cf8;
        font-weight: 600;
    }

    .dropdown-menu.light .dropdown-item {
        color: #64748b;
    }

    .dropdown-menu.light .dropdown-item:hover {
        background: rgba(0, 0, 0, 0.02);
        color: #1e293b;
    }

    .dropdown-menu.light .dropdown-item.selected {
        background: rgba(99, 102, 241, 0.05);
        color: #4f46e5;
    }

    .arrow {
        font-size: 0.7rem;
        transition: transform 0.2s;
        opacity: 0.6;
    }

    .active .arrow {
        transform: rotate(180deg);
    }

    .download-btn {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .download-btn:hover {
        background: var(--bg-tertiary);
    }

    .chart-content {
        min-height: 300px;
    }

    .no-data {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 200px;
        color: var(--text-muted);
        font-style: italic;
    }

    /* Growth Table */
    .table-container {
        overflow-x: auto;
    }
    .growth-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }
    .growth-table th,
    .growth-table td {
        padding: 10px 12px;
        text-align: right;
        border-bottom: 1px solid var(--border-color);
    }
    .growth-table th {
        color: var(--text-muted);
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }
    .growth-table td {
        color: var(--text-secondary);
        font-family: "JetBrains Mono", monospace;
    }
    .name-cell {
        text-align: left !important;
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
    }
    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .positive {
        color: #10b981 !important;
    }
    .negative {
        color: #ef4444 !important;
    }

    /* Depeg Monitor */
    .depeg-content {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    .depeg-current h4,
    .depeg-history h4 {
        margin: 0 0 12px 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }
    .depeg-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
    }
    .depeg-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 12px;
        background: var(--bg-tertiary);
        border-radius: 8px;
        border: 1px solid transparent;
    }
    .depeg-item.depegged {
        border-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    .depeg-name {
        font-weight: 700;
        font-size: 0.9rem;
    }
    .depeg-price {
        font-family: "JetBrains Mono", monospace;
        font-size: 1rem;
        color: var(--text-primary);
    }
    .depeg-deviation {
        font-family: "JetBrains Mono", monospace;
        font-size: 0.8rem;
    }
    .depeg-status {
        font-size: 0.75rem;
        margin-top: 4px;
    }

    .events-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        max-height: 200px;
        overflow-y: auto;
    }
    .event-item {
        display: flex;
        gap: 12px;
        align-items: center;
        padding: 8px 12px;
        background: var(--bg-tertiary);
        border-radius: 6px;
        font-size: 0.8rem;
    }
    .event-date {
        color: var(--text-muted);
        font-family: "JetBrains Mono", monospace;
    }
    .event-stable {
        font-weight: 600;
    }
    .event-price,
    .event-dev {
        font-family: "JetBrains Mono", monospace;
    }

    @media (max-width: 1024px) {
        .stablecoins-grid {
            grid-template-columns: 1fr;
        }
        .tab-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 16px;
        }
        .header-stats {
            width: 100%;
            justify-content: flex-start;
        }
    }
</style>
