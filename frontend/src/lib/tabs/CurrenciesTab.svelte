<script>
    /**
     * CurrenciesTab.svelte
     * Displays DXY Index and major currency pairs with inversion and ROC analysis.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import { filterPlotlyData, getCutoffDate } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    // Core props
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Helper to get translation with fallback
    $: t = (key, fallback) => translations[key] || fallback;

    // Currency Data from dashboardData
    $: currenciesData = dashboardData.currencies || {};
    $: dxyData = currenciesData.dxy || {};
    $: pairsData = currenciesData.pairs || {};
    $: dates = currenciesData.dates || [];

    // Local state for Main chart
    let mainAsset = "DXY"; // DXY or EUR, JPY, etc.
    let mainRange = "1Y";
    let mainInverted = false;
    let mainMode = "absolute"; // absolute, roc7d, roc30d, roc90d, roc180d, volatility
    let showBtcOverlay = false;
    let btcMode = "absolute"; // absolute, roc

    $: mainAssetOptions = [
        { value: "DXY", label: "DXY Index" },
        ...majorPairNames.map((p) => ({ value: p, label: `${p}/USD` })),
    ];

    $: mainModes = [
        { value: "absolute", label: t("raw_view", "Absolute") },
        { value: "roc7d", label: "ROC 7D" },
        { value: "roc30d", label: "ROC 30D" },
        { value: "roc90d", label: "ROC 90D" },
        { value: "roc180d", label: "ROC 180D" },
        { value: "roc_yoy", label: "YoY" },
        { value: "volatility", label: t("currency_volatility", "Volatility") },
    ];

    function selectMainMode(mode) {
        mainMode = mode;
    }

    function toggleMainInversion() {
        mainInverted = !mainInverted;
    }

    // Process Main Chart Data
    $: mainChartData = (() => {
        if (!dates.length) return [];

        let assetData =
            mainAsset === "DXY" ? dxyData : pairsData[mainAsset] || {};
        let yData = [];
        let name = mainAsset === "DXY" ? "DXY" : `${mainAsset}/USD`;
        let color = mainAsset === "DXY" ? "#6366f1" : pairColors[mainAsset];

        if (mainMode === "absolute") {
            yData = assetData.absolute || [];
            if (mainInverted) {
                yData = yData.map((v) => (v ? 1 / v : null));
                name = mainAsset === "DXY" ? "1 / DXY" : `1 / (${name})`;
            }
        } else {
            // ROC or Volatility modes
            const modeKey =
                mainMode === "volatility"
                    ? "volatility"
                    : mainMode === "roc_yoy"
                      ? "roc_yoy"
                      : mainMode.replace("roc", "roc_");

            yData = assetData[modeKey] || [];

            if (mainInverted) {
                if (mainMode === "volatility") {
                    // Volatility is absolute value, inversion doesn't change it much but for UX we keep it same
                    name = `Inverted ${name}`;
                } else {
                    // ROC(1/X) = (1 / (1 + ROC/100) - 1) * 100
                    yData = yData.map((v) =>
                        v !== null ? (1 / (1 + v / 100) - 1) * 100 : null,
                    );
                    name =
                        mainAsset === "DXY"
                            ? `1/DXY ${mainMode.toUpperCase()}`
                            : `1/(${mainAsset}) ${mainMode.toUpperCase()}`;
                }
            } else {
                name = `${name} ${mainMode.toUpperCase()} (%)`;
            }

            // Color coding (keep defined colors)
            if (mainMode === "roc7d") color = "#10b981";
            else if (mainMode === "roc30d") color = "#3b82f6";
            else if (mainMode === "roc90d") color = "#8b5cf6";
            else if (mainMode === "roc180d") color = "#f59e0b";
            else if (mainMode === "roc_yoy") color = "#ec4899";
            else if (mainMode === "volatility") color = "#ef4444";
        }

        const traces = [
            {
                x: dates,
                y: yData,
                name: name,
                type: "scatter",
                mode: "lines",
                line: { color: color, width: 2.5, shape: "spline" },
                fill: mainMode === "absolute" ? "none" : "tozeroy",
                fillcolor: darkMode
                    ? `rgba(${hexToRgb(color)}, 0.1)`
                    : `rgba(${hexToRgb(color)}, 0.05)`,
                hovertemplate: `%{x}<br>${name}: %{y:.2f}${mainMode === "absolute" ? "" : "%"}<extra></extra>`,
            },
        ];

        // Bitcoin Overlay
        const btcData = currenciesData.btc || {};
        if (showBtcOverlay && (btcData.absolute || btcData.roc_30d)) {
            let btcYData = [];
            let btcName = "Bitcoin";
            let btcColor = "#f7931a"; // BTC Orange

            if (btcMode === "absolute") {
                btcYData = btcData.absolute || [];
            } else {
                // Determine which ROC to use for BTC based on main chart mode
                const btcRocKey = mainMode.startsWith("roc")
                    ? mainMode
                    : "roc_30d";
                btcYData = btcData[btcRocKey] || btcData.roc_30d || [];
                btcName = `BTC ${btcRocKey.replace("roc_", "ROC ").toUpperCase()} (%)`;
            }

            traces.push({
                x: dates,
                y: btcYData,
                name: btcName,
                type: "scatter",
                mode: "lines",
                line: {
                    color: btcColor,
                    width: 2.5, // Increased width for better visibility
                    dash: "dot",
                    shape: "spline",
                },
                yaxis: btcMode === "roc" ? "y" : "y2", // Merge if both are ROC, separate if price
                fill: "none",
                fillcolor: "transparent",
                hovertemplate: `%{x}<br>${btcName}: %{y:.0f}${btcMode === "roc" ? "%" : ""}<extra></extra>`,
            });
        }

        return filterPlotlyData(traces, dates, mainRange);
    })();

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
            ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
            : "99, 102, 241";
    }

    // Grid Charts for Major Pairs
    let pairRanges = {
        EUR: "1Y",
        JPY: "1Y",
        GBP: "1Y",
        AUD: "1Y",
        CAD: "1Y",
        CHF: "1Y",
        CNY: "1Y",
    };
    $: majorPairNames = ["EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "CNY"];

    // Reactive data for pair charts to ensure proper reactivity with pairRanges
    $: pairCharts = majorPairNames.reduce((acc, pair) => {
        if (pairsData[pair]) {
            acc[pair] = filterPlotlyData(
                [
                    {
                        x: dates,
                        y: pairsData[pair].absolute,
                        name: `${pair}/USD`,
                        type: "scatter",
                        mode: "lines",
                        line: {
                            color: pairColors[pair] || "#6366f1",
                            width: 2,
                        },
                        hovertemplate: `%{x}<br>${pair}/USD: %{y:.4f}<extra></extra>`,
                    },
                ],
                dates,
                pairRanges[pair] || "1Y",
            );
        }
        return acc;
    }, {});

    // Pair colors (Quant v2 Palette)
    const pairColors = {
        EUR: "#3b82f6", // Blue (Notes)
        JPY: "#ef4444", // Red (Others)
        GBP: "#8b5cf6", // Purple (Bonds)
        AUD: "#10b981", // Green (Bills)
        CAD: "#f59e0b", // Amber (Others)
        CHF: "#94a3b8", // Muted Slate
        CNY: "#ec4899", // Pink (YoY)
    };

    // Calculate latest values for the header
    $: latestDxy = dxyData.absolute
        ? dxyData.absolute[dxyData.absolute.length - 1]
        : 0;

    // Growth table data
    $: growthTableData = Object.entries(pairsData)
        .map(([name, data]) => {
            const abs = data.absolute || [];
            const r7 = data.roc_7d || [];
            const r30 = data.roc_30d || [];
            const r90 = data.roc_90d || [];

            return {
                name,
                rate: abs.length > 0 ? abs[abs.length - 1] : 0,
                roc7d: r7.length > 0 ? r7[r7.length - 1] : 0,
                roc30d: r30.length > 0 ? r30[r30.length - 1] : 0,
                roc90d: r90.length > 0 ? r90[r90.length - 1] : 0,
                color: pairColors[name] || "#888888",
            };
        })
        .sort((a, b) => Math.abs(b.roc30d) - Math.abs(a.roc30d));

    // Card refs for download
    let dxyCard, pairsCard, tableCard;

    const getGrowthClass = (val) => (val >= 0 ? "positive" : "negative");
</script>

<div class="tab-header" class:light={!darkMode}>
    <div class="header-content">
        <h2>{t("currencies_title", "Global Currencies Overview")}</h2>
        <p class="description">
            {t(
                "currencies_desc",
                "Monitor the US Dollar Index (DXY) and major currency pairs.",
            )}
        </p>
    </div>
    <div class="header-stats">
        <div class="stat-item">
            <span class="stat-label">DXY Index</span>
            <span class="stat-value"
                >{latestDxy ? latestDxy.toFixed(2) : "N/A"}</span
            >
        </div>
    </div>
</div>

<div class="currencies-grid" class:light={!darkMode}>
    <!-- Main Chart -->
    <div class="chart-card full-width" bind:this={dxyCard}>
        <div class="chart-header">
            <div class="header-title-group asset-select-wrapper">
                <Dropdown
                    options={mainAssetOptions}
                    bind:value={mainAsset}
                    {darkMode}
                    small={false}
                />
            </div>
            <div class="header-controls">
                <button
                    class="control-btn"
                    class:active={mainInverted}
                    on:click={toggleMainInversion}
                    title={mainAsset === "DXY"
                        ? "Invert DXY (1/DXY)"
                        : `Invert ${mainAsset}`}
                >
                    <i class="fas fa-exchange-alt"></i>
                    {mainAsset === "DXY" ? "1/DXY" : `1/${mainAsset}`}
                </button>

                <div class="btc-overlay-toggle">
                    <button
                        class="control-btn btc-toggle"
                        class:active={showBtcOverlay}
                        on:click={() => (showBtcOverlay = !showBtcOverlay)}
                    >
                        <i class="fab fa-bitcoin"></i> BTC
                    </button>
                    {#if showBtcOverlay}
                        <button
                            class="control-btn btc-mode"
                            class:active={btcMode === "roc"}
                            on:click={() =>
                                (btcMode =
                                    btcMode === "absolute"
                                        ? "roc"
                                        : "absolute")}
                            title="Toggle BTC ROC/Price"
                        >
                            {btcMode === "roc" ? "ROC" : "Raw"}
                        </button>
                    {/if}
                </div>

                <Dropdown
                    options={mainModes}
                    bind:value={mainMode}
                    onSelect={selectMainMode}
                    {darkMode}
                    small={true}
                />
                <TimeRangeSelector bind:selectedRange={mainRange} />
                <button
                    class="download-btn"
                    on:click={() =>
                        downloadCardAsImage(
                            dxyCard,
                            "Currency_Main_Chart",
                            darkMode,
                        )}
                    aria-label="Download Chart"
                >
                    <i class="fas fa-download"></i>
                </button>
            </div>
        </div>
        <div class="chart-content" style="height: 450px;">
            <Chart
                data={mainChartData}
                {darkMode}
                layout={{
                    yaxis: {
                        autorange: true,
                        rangemode:
                            mainMode === "absolute" ? "normal" : "tozero",
                        title: mainMode === "absolute" ? "Rate" : "%",
                        gridcolor: darkMode
                            ? "rgba(255,255,255,0.03)"
                            : "rgba(0,0,0,0.05)",
                        color: darkMode ? "#94a3b8" : "#64748b",
                        zeroline: false,
                    },
                    yaxis2: {
                        title: "BTC Price",
                        overlaying: "y",
                        side: "right",
                        showgrid: false,
                        color: "#f7931a",
                        visible: showBtcOverlay && btcMode === "absolute",
                    },
                    margin: { t: 30, r: 60, l: 60, b: 100 },
                    legend: {
                        orientation: "v",
                        y: 0.5,
                        x: 1.05,
                        xanchor: "left",
                    },
                }}
            />
        </div>
    </div>

    <!-- Major Pairs Grid -->
    <div class="pairs-section-header full-width">
        <h3>{t("major_pairs_title", "Major Currency Pairs")}</h3>
    </div>

    {#each majorPairNames as pair}
        {#if pairsData[pair]}
            <div class="chart-card pair-card">
                <div class="chart-header">
                    <h4>{pair}/USD</h4>
                    <TimeRangeSelector bind:selectedRange={pairRanges[pair]} />
                </div>
                <div class="chart-content mini" style="height: 180px;">
                    <Chart
                        data={pairCharts[pair]}
                        {darkMode}
                        layout={{
                            showlegend: false,
                            xaxis: {
                                visible: true,
                                gridcolor: darkMode
                                    ? "rgba(255,255,255,0.03)"
                                    : "rgba(0,0,0,0.05)",
                                color: darkMode ? "#94a3b8" : "#64748b",
                                tickfont: { size: 9 },
                                automargin: true,
                            },
                            yaxis: {
                                autorange: true,
                                rangemode: "normal",
                                gridcolor: darkMode
                                    ? "rgba(255,255,255,0.03)"
                                    : "rgba(0,0,0,0.05)",
                                color: darkMode ? "#94a3b8" : "#64748b",
                                zeroline: false,
                                tickfont: { size: 9 },
                            },
                            margin: { t: 10, r: 10, l: 35, b: 35 },
                            paper_bgcolor: "transparent",
                            plot_bgcolor: "transparent",
                        }}
                        config={{
                            responsive: true,
                            displayModeBar: false,
                            scrollZoom: true,
                        }}
                    />
                </div>
            </div>
        {/if}
    {/each}

    <!-- Growth Table -->
    <div class="chart-card full-width" bind:this={tableCard}>
        <div class="chart-header">
            <h3>{t("stablecoins_growth_table", "Growth Analysis")}</h3>
            <button
                class="download-btn"
                on:click={() =>
                    downloadCardAsImage(
                        tableCard,
                        "Currencies_Growth",
                        darkMode,
                    )}
                aria-label="Download Growth Table"
            >
                <i class="fas fa-download"></i>
            </button>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>{t("stablecoins_name", "Currency")}</th>
                        <th>{t("rate_col", "Rate")}</th>
                        <th>{t("currency_roc_7d", "7D ROC")}</th>
                        <th>{t("currency_roc_1m", "1M ROC")}</th>
                        <th>{t("currency_roc_3m", "3M ROC")}</th>
                    </tr>
                </thead>
                <tbody>
                    {#each growthTableData as item}
                        <tr>
                            <td>
                                <div class="name-cell">
                                    <span
                                        class="color-dot"
                                        style="background-color: {item.color}"
                                    ></span>
                                    {item.name}/USD
                                </div>
                            </td>
                            <td>{item.rate.toFixed(4)}</td>
                            <td class={getGrowthClass(item.roc7d)}
                                >{item.roc7d.toFixed(2)}%</td
                            >
                            <td class={getGrowthClass(item.roc30d)}
                                >{item.roc30d.toFixed(2)}%</td
                            >
                            <td class={getGrowthClass(item.roc90d)}
                                >{item.roc90d.toFixed(2)}%</td
                            >
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* Local overrides only, base styles come from global app.css */
    .currencies-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.5rem;
        width: 100%;
        max-width: 100%;
    }

    .full-width {
        grid-column: 1 / -1;
    }

    .pairs-section-header {
        margin: 3rem 0 1.5rem 0;
        padding-left: 0.5rem;
        border-left: 4px solid var(--accent-primary);
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        position: relative;
        z-index: 10;
    }
    .chart-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: #f1f5f9;
    }
    .light .chart-header h3 {
        color: #334155;
    }
    .header-controls {
        display: flex;
        gap: 0.6rem;
        align-items: center;
    }

    .btc-overlay-toggle {
        display: flex;
        background: rgba(255, 255, 255, 0.05);
        padding: 2px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .btc-toggle {
        background: transparent !important;
        border: none !important;
        color: #94a3b8;
    }
    .btc-toggle.active {
        color: #f7931a !important;
    }
    .btc-mode {
        background: rgba(247, 147, 26, 0.15) !important;
        border: 1px solid rgba(247, 147, 26, 0.3) !important;
        color: #f7931a !important;
        padding: 2px 8px !important;
        margin-left: 4px;
        border-radius: 4px;
        font-family: var(--font-mono);
        font-weight: 700;
        font-size: 10px;
    }

    .control-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #94a3b8;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s;
    }
    .control-btn.active {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }

    .download-btn {
        background: none;
        border: none;
        color: #64748b;
        cursor: pointer;
        padding: 0.4rem;
        border-radius: 4px;
        transition: background 0.2s;
    }
    .download-btn:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .pairs-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 1rem;
        padding: 0 0.5rem;
    }
    .pairs-section-header h3 {
        font-size: 1.25rem;
        color: #f8fafc;
        margin: 0;
    }
    .light .pairs-section-header h3 {
        color: #1e293b;
    }

    .pair-card {
        padding: 1rem;
    }
    .pair-card .chart-header {
        margin-bottom: 0.75rem;
    }
    .pair-card h4 {
        margin: 0;
        font-size: 0.9rem;
        color: #94a3b8;
    }

    /* FIX: Force mini charts to respect container height and avoid global 500px blowup */
    .mini :global(.chart-content) {
        height: 100% !important;
        min-height: unset !important;
    }

    /* Table Styles */
    .table-container {
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.5rem;
    }
    th {
        text-align: left;
        padding: 1rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid var(--border-color);
    }
    .light th {
        border-bottom-color: #e2e8f0;
    }
    td {
        padding: 1rem;
        font-size: 0.95rem;
        color: #f1f5f9;
        border-bottom: 1px solid rgba(255, 255, 255, 0.02);
    }
    .light td {
        color: #334155;
        border-bottom-color: #f1f5f9;
    }

    .name-cell {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 600;
    }
    .color-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }

    .positive {
        color: #10b981;
    }
    .negative {
        color: #ef4444;
    }

    @media (max-width: 1200px) {
        .currencies-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    @media (max-width: 768px) {
        .currencies-grid {
            grid-template-columns: 1fr;
        }
        .tab-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        .stat-item {
            align-items: flex-start;
        }
    }
</style>
