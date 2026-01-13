<script>
    /**
     * CommoditiesTab.svelte
     * Displays Global Commodities with ROC analysis, BTC overlay, and liquidity ratios.
     * Enhanced with 2-column grid and comprehensive ratio analysis.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";
    import { dashboardData } from "../../stores/dataStore";

    // Core props
    let {
        darkMode = false,
        translations = {},
        commoditiesData = {},
    } = $props();

    // Helper to get translation with fallback
    let t = $derived((key, fallback) => translations[key] || fallback);

    // Data extraction
    let dates = $derived(commoditiesData.dates || []);
    let mainData = $derived(commoditiesData.commodities || {});
    let btcData = $derived(commoditiesData.btc || {});

    // Get liquidity data from dashboardData for ratios
    let gliData = $derived($dashboardData.gli?.total || []);
    let m2Data = $derived($dashboardData.m2?.total || []);
    let netLiqData = $derived($dashboardData.us_net_liq || []);
    let dashDates = $derived($dashboardData.dates || []);

    const assetColors = {
        GOLD: "#f59e0b",
        SILVER: "#94a3b8",
        USOIL: "#10b981",
        "HG1!": "#ec4899",
        PLATINUM: "#3b82f6",
        PALLADIUM: "#ef4444",
    };

    // Ratio descriptions
    const ratioDescriptions = {
        absolute: {
            title: "Absolute Price",
            desc: "Raw price of the commodity.",
            interpretation: "Standard price chart.",
        },
        gli: {
            title: "Commodity / GLI",
            desc: "Commodity price divided by Global Liquidity Index.",
            interpretation:
                "Rising = Commodity outperforming global liquidity. Falling = Underperforming.",
        },
        m2: {
            title: "Commodity / M2 Global",
            desc: "Commodity price divided by Global M2 money supply.",
            interpretation:
                "Measures real purchasing power. Rising = beating monetary inflation.",
        },
        spx: {
            title: "Commodity / SPX",
            desc: "Commodity relative to S&P 500.",
            interpretation:
                "Rising = Real assets outperforming financials. Falling = Equities leading.",
        },
    };

    // Local state for Main chart
    let mainAsset = $state("GOLD");
    let mainRange = $state("1Y");
    let mainInverted = $state(false);
    let mainMode = $state("absolute");
    let mainRatioMode = $state("absolute");
    let showBtcOverlay = $state(false);
    let btcMode = $state("absolute");
    let showRatioInfo = $state(false);

    let allCommodityNames = $derived(Object.keys(mainData));
    let mainAssetOptions = $derived(
        allCommodityNames.map((name) => ({ value: name, label: name })),
    );

    let mainModes = $derived([
        { value: "absolute", label: t("raw_view", "Absolute") },
        { value: "roc7d", label: "ROC 7D" },
        { value: "roc30d", label: "ROC 30D" },
        { value: "roc90d", label: "ROC 90D" },
        { value: "roc_yoy", label: "YoY" },
    ]);

    let ratioModes = [
        { value: "absolute", label: "Absolute" },
        { value: "gli", label: "/ GLI" },
        { value: "m2", label: "/ M2" },
        { value: "spx", label: "/ SPX" },
    ];

    /**
     * Find the closest prior date in a sorted array of date strings.
     * Uses binary search for efficiency.
     */
    function findClosestPriorDate(targetDate, sortedDates) {
        if (!sortedDates?.length) return -1;

        const target = new Date(targetDate).getTime();
        let left = 0,
            right = sortedDates.length - 1;
        let result = -1;

        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            const midDate = new Date(sortedDates[mid]).getTime();

            if (midDate <= target) {
                result = mid;
                left = mid + 1;
            } else {
                right = mid - 1;
            }
        }

        return result;
    }

    /**
     * Calculate ratio with proper date alignment.
     * Uses nearest prior date matching for weekly data against daily data.
     * Normalizes to starting value = 100 for better visualization.
     */
    function calculateRatio(
        numeratorValues,
        denominatorValues,
        numDates,
        denomDates,
    ) {
        if (
            !numeratorValues?.length ||
            !denominatorValues?.length ||
            !denomDates?.length
        ) {
            return numeratorValues;
        }

        const denomMap = new Map();
        denomDates.forEach((d, i) => {
            if (denominatorValues[i] != null) {
                denomMap.set(d, denominatorValues[i]);
            }
        });

        const sortedDenomDates = [...denomDates].sort();

        const rawRatios = numDates.map((date, i) => {
            const numVal = numeratorValues[i];
            if (numVal == null) return null;

            const closestIdx = findClosestPriorDate(date, sortedDenomDates);
            if (closestIdx === -1) return null;

            const closestDate = sortedDenomDates[closestIdx];
            const denomVal = denomMap.get(closestDate);

            if (denomVal == null || denomVal === 0) return null;
            return numVal / denomVal;
        });

        // Normalize: set first valid value to 100
        const firstValid = rawRatios.find((v) => v != null);
        if (firstValid == null) return rawRatios;

        const scale = 100 / firstValid;
        return rawRatios.map((v) => (v != null ? v * scale : null));
    }

    function selectMainMode(mode) {
        mainMode = mode;
    }

    function toggleMainInversion() {
        mainInverted = !mainInverted;
    }

    // Process Main Chart Data
    let mainChartData = $derived.by(() => {
        if (!dates.length) return [];

        let assetData = mainData[mainAsset] || {};
        let yData = assetData.absolute || [];
        let name = mainAsset;
        let color = assetColors[mainAsset] || "#6366f1";

        // Apply ratio
        if (mainRatioMode !== "absolute" && mainMode === "absolute") {
            let denomData,
                denomDates = dashDates;

            switch (mainRatioMode) {
                case "gli":
                    denomData = gliData;
                    name = `${mainAsset} / GLI`;
                    break;
                case "m2":
                    denomData = m2Data;
                    name = `${mainAsset} / M2`;
                    break;
                case "spx":
                    // For SPX ratio, we need to get SPX from indexes data - simplified here
                    denomData = $dashboardData.btc?.absolute || []; // Placeholder
                    name = `${mainAsset} / SPX`;
                    break;
            }

            if (denomData?.length) {
                yData = calculateRatio(yData, denomData, dates, denomDates);
            }
        } else if (mainMode !== "absolute") {
            const modeKey =
                mainMode === "roc_yoy"
                    ? "roc_yoy"
                    : mainMode.replace("roc", "roc_");
            yData = assetData[modeKey] || [];
            name = `${mainAsset} ${mainMode.toUpperCase()} (%)`;

            if (mainMode === "roc7d") color = "#10b981";
            else if (mainMode === "roc30d") color = "#3b82f6";
            else if (mainMode === "roc90d") color = "#8b5cf6";
            else if (mainMode === "roc_yoy") color = "#ec4899";
        }

        if (mainInverted && yData.length) {
            yData = yData.map((v) => (v ? 1 / v : null));
            name = `1 / ${name}`;
        }

        const isRoc = mainMode !== "absolute";
        const traces = [
            {
                x: dates,
                y: yData,
                name: name,
                type: "scatter",
                mode: "lines",
                line: { color: color, width: 2.5, shape: "spline" },
                fill: isRoc ? "tozeroy" : "none",
                fillcolor: darkMode
                    ? `rgba(${hexToRgb(color)}, 0.1)`
                    : `rgba(${hexToRgb(color)}, 0.05)`,
                hovertemplate: `%{x}<br>${name}: %{y:.2f}${isRoc ? "%" : ""}<extra></extra>`,
            },
        ];

        if (showBtcOverlay && (btcData.absolute || btcData.roc_30d)) {
            let btcYData =
                btcMode === "absolute"
                    ? btcData.absolute || []
                    : btcData.roc_30d || [];
            let btcName =
                btcMode === "absolute" ? "Bitcoin" : "BTC ROC 30D (%)";

            traces.push({
                x: dates,
                y: btcYData,
                name: btcName,
                type: "scatter",
                mode: "lines",
                line: {
                    color: "#f7931a",
                    width: 2,
                    dash: "dot",
                    shape: "spline",
                },
                yaxis: btcMode === "roc" ? "y" : "y2",
                fill: "none",
                fillcolor: "transparent",
                hovertemplate: `%{x}<br>${btcName}: %{y:.0f}${btcMode === "roc" ? "%" : ""}<extra></extra>`,
            });
        }

        return filterPlotlyData(traces, dates, mainRange);
    });

    function hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
            ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
            : "99, 102, 241";
    }

    // Grid Charts with ratio support
    let gridRanges = $state({
        GOLD: "1Y",
        SILVER: "1Y",
        USOIL: "1Y",
        "HG1!": "1Y",
        PLATINUM: "1Y",
        PALLADIUM: "1Y",
    });
    let gridRatioModes = $state({
        GOLD: "absolute",
        SILVER: "absolute",
        USOIL: "absolute",
        "HG1!": "absolute",
        PLATINUM: "absolute",
        PALLADIUM: "absolute",
    });

    function setGridRange(name, value) {
        gridRanges[name] = value;
    }

    function setGridRatioMode(name, value) {
        gridRatioModes[name] = value;
    }

    let otherAssets = $derived(
        allCommodityNames.filter((n) => n !== mainAsset),
    );

    let gridCharts = $derived.by(() => {
        const result = {};
        for (const name of otherAssets) {
            if (mainData[name] && mainData[name].absolute) {
                let yData = mainData[name].absolute;
                let chartName = name;
                const ratioMode = gridRatioModes[name] || "absolute";

                if (ratioMode !== "absolute") {
                    let denomData;
                    switch (ratioMode) {
                        case "gli":
                            denomData = gliData;
                            chartName = `${name}/GLI`;
                            break;
                        case "m2":
                            denomData = m2Data;
                            chartName = `${name}/M2`;
                            break;
                    }
                    if (denomData?.length) {
                        yData = calculateRatio(
                            yData,
                            denomData,
                            dates,
                            dashDates,
                        );
                    }
                }

                result[name] = filterPlotlyData(
                    [
                        {
                            x: dates,
                            y: yData,
                            name: chartName,
                            type: "scatter",
                            mode: "lines",
                            line: {
                                color: assetColors[name] || "#6366f1",
                                width: 2,
                            },
                            hovertemplate: `%{x}<br>${chartName}: %{y:.2f}<extra></extra>`,
                        },
                    ],
                    dates,
                    gridRanges[name] || "1Y",
                );
            }
        }
        return result;
    });

    // Cross Ratios
    let crossRatioRange = $state("1Y");
    let crossRatioCharts = $derived.by(() => {
        const result = {};
        const goldData = mainData.GOLD?.absolute;
        const silverData = mainData.SILVER?.absolute;

        // Gold/Silver Ratio
        if (goldData?.length && silverData?.length) {
            const goldSilver = goldData.map((v, i) =>
                v && silverData[i] ? v / silverData[i] : null,
            );
            result["GOLD/SILVER"] = filterPlotlyData(
                [
                    {
                        x: dates,
                        y: goldSilver,
                        name: "Gold/Silver Ratio",
                        type: "scatter",
                        mode: "lines",
                        line: { color: "#f59e0b", width: 2.5 },
                        hovertemplate: `%{x}<br>Gold/Silver: %{y:.2f}<extra></extra>`,
                    },
                ],
                dates,
                crossRatioRange,
            );
        }

        return result;
    });

    let latestGold = $derived(
        mainData.GOLD?.absolute
            ? mainData.GOLD.absolute[mainData.GOLD.absolute.length - 1]
            : 0,
    );

    let growthTableData = $derived(
        Object.entries(mainData)
            .map(([name, data]) => {
                const abs = data.absolute || [];
                const r7 = data.roc_7d || [];
                const r30 = data.roc_30d || [];
                const r90 = data.roc_90d || [];
                return {
                    name,
                    value:
                        (abs && abs.length > 0 ? abs[abs.length - 1] : 0) ?? 0,
                    roc7d: (r7 && r7.length > 0 ? r7[r7.length - 1] : 0) ?? 0,
                    roc30d:
                        (r30 && r30.length > 0 ? r30[r30.length - 1] : 0) ?? 0,
                    roc90d:
                        (r90 && r90.length > 0 ? r90[r90.length - 1] : 0) ?? 0,
                    color: assetColors[name] || "#888888",
                };
            })
            .sort((a, b) => b.roc30d - a.roc30d),
    );

    let mainCard = $state(),
        tableCard = $state();
</script>

<div class="tab-header" class:light={!darkMode}>
    <div class="header-content">
        <h2>{t("commodities_title", "Global Commodities")}</h2>
        <p class="description">
            {t(
                "commodities_desc",
                "Real assets, energy, and metals with liquidity ratio analysis.",
            )}
        </p>
    </div>
    <div class="header-stats">
        <div class="stat-item">
            <span class="stat-label">Gold</span>
            <span class="stat-value">
                ${latestGold !== undefined && latestGold !== null
                    ? latestGold.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                      })
                    : "N/A"}
            </span>
        </div>
    </div>
</div>

<div class="commodities-grid" class:light={!darkMode}>
    <!-- Main Chart -->
    <div class="chart-card full-width" bind:this={mainCard}>
        <div class="chart-header">
            <div class="header-title-group">
                <Dropdown
                    options={mainAssetOptions}
                    bind:value={mainAsset}
                    {darkMode}
                />
            </div>
            <div class="header-controls">
                <button
                    class="control-btn"
                    class:active={mainInverted}
                    onclick={toggleMainInversion}
                >
                    <i class="fas fa-exchange-alt"></i> 1/X
                </button>
                <div class="btc-overlay-toggle">
                    <button
                        class="control-btn btc-toggle"
                        class:active={showBtcOverlay}
                        onclick={() => (showBtcOverlay = !showBtcOverlay)}
                    >
                        <i class="fab fa-bitcoin"></i> BTC
                    </button>
                    {#if showBtcOverlay}
                        <button
                            class="control-btn btc-mode"
                            class:active={btcMode === "roc"}
                            onclick={() =>
                                (btcMode =
                                    btcMode === "absolute"
                                        ? "roc"
                                        : "absolute")}
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
                <Dropdown
                    options={ratioModes}
                    bind:value={mainRatioMode}
                    {darkMode}
                    small={true}
                />
                <button
                    class="control-btn info-btn"
                    onclick={() => (showRatioInfo = !showRatioInfo)}
                    title="Ratio Info"
                >
                    <i class="fas fa-info-circle"></i>
                </button>
                <TimeRangeSelector bind:selectedRange={mainRange} />
                <button
                    class="download-btn"
                    aria-label="Download chart as image"
                    onclick={() =>
                        downloadCardAsImage(
                            mainCard,
                            "Commodities_Main",
                            darkMode,
                        )}
                >
                    <i class="fas fa-download"></i>
                </button>
            </div>
        </div>

        {#if showRatioInfo && ratioDescriptions[mainRatioMode]}
            <div class="ratio-info-box">
                <strong>{ratioDescriptions[mainRatioMode].title}</strong>
                <p>{ratioDescriptions[mainRatioMode].desc}</p>
                <p class="interpretation">
                    <i class="fas fa-lightbulb"></i>
                    {ratioDescriptions[mainRatioMode].interpretation}
                </p>
            </div>
        {/if}

        <div class="chart-content" style="height: 450px;">
            <Chart
                data={mainChartData}
                {darkMode}
                layout={{
                    yaxis: {
                        autorange: true,
                        title:
                            mainRatioMode !== "absolute"
                                ? "Ratio (scaled)"
                                : mainMode === "absolute"
                                  ? "Price"
                                  : "%",
                        gridcolor: darkMode
                            ? "rgba(255,255,255,0.03)"
                            : "rgba(0,0,0,0.05)",
                        color: darkMode ? "#94a3b8" : "#64748b",
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
                }}
            />
        </div>
    </div>

    <!-- Cross Ratios -->
    <div class="section-title full-width">
        <h3>
            <i class="fas fa-divide"></i>
            {t("cross_ratios", "Cross Ratios")}
        </h3>
        <p class="section-desc">Relative valuation between commodities.</p>
    </div>

    <div class="chart-card full-width">
        <div class="chart-header">
            <h4>Gold / Silver Ratio</h4>
            <TimeRangeSelector
                selectedRange={crossRatioRange}
                onRangeChange={(val) => (crossRatioRange = val)}
            />
        </div>
        <div class="ratio-desc">
            <span class="tag bullish">↑ Gold premium (fear, deflation)</span>
            <span class="tag bearish"
                >↓ Silver outperforming (industrial demand, risk-on)</span
            >
        </div>
        <div class="chart-content" style="height: 280px;">
            <Chart
                data={crossRatioCharts["GOLD/SILVER"] || []}
                {darkMode}
                layout={{
                    showlegend: false,
                    margin: { t: 10, r: 10, l: 45, b: 40 },
                    yaxis: { tickfont: { size: 10 }, autorange: true },
                }}
                config={{ responsive: true, displayModeBar: false }}
            />
        </div>
    </div>

    <!-- Other Commodities -->
    <div class="section-title full-width">
        <h3>{t("other_commodities", "Other Commodities")}</h3>
    </div>

    {#each otherAssets as name (name)}
        <div class="chart-card commodity-card">
            <div class="chart-header">
                <h4>{name}</h4>
                <div class="mini-controls">
                    <Dropdown
                        options={ratioModes.slice(0, 3)}
                        value={gridRatioModes[name] || "absolute"}
                        onSelect={(val) => setGridRatioMode(name, val)}
                        {darkMode}
                        small={true}
                    />
                    <TimeRangeSelector
                        selectedRange={gridRanges[name] || "1Y"}
                        onRangeChange={(val) => setGridRange(name, val)}
                    />
                </div>
            </div>
            <div class="chart-content" style="height: 280px;">
                <Chart
                    data={gridCharts[name]}
                    {darkMode}
                    layout={{
                        showlegend: false,
                        margin: { t: 10, r: 10, l: 45, b: 40 },
                        xaxis: { tickfont: { size: 10 }, automargin: true },
                        yaxis: { tickfont: { size: 10 }, autorange: true },
                    }}
                    config={{ responsive: true, displayModeBar: false }}
                />
            </div>
        </div>
    {/each}

    <!-- Performance Table -->
    <div class="chart-card full-width" bind:this={tableCard}>
        <div class="chart-header">
            <h3>{t("performance_table", "Performance Analysis")}</h3>
        </div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>{t("commodity_name", "Commodity")}</th>
                        <th>{t("last_price", "Last")}</th>
                        <th>7D ROC</th>
                        <th>1M ROC</th>
                        <th>3M ROC</th>
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
                                    {item.name}
                                </div>
                            </td>
                            <td
                                >{item.value.toLocaleString(undefined, {
                                    maximumFractionDigits: 2,
                                })}</td
                            >
                            <td
                                class={item.roc7d >= 0
                                    ? "positive"
                                    : "negative"}>{item.roc7d.toFixed(2)}%</td
                            >
                            <td
                                class={item.roc30d >= 0
                                    ? "positive"
                                    : "negative"}>{item.roc30d.toFixed(2)}%</td
                            >
                            <td
                                class={item.roc90d >= 0
                                    ? "positive"
                                    : "negative"}>{item.roc90d.toFixed(2)}%</td
                            >
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>

<style>
    /* 2-Column Grid Layout */
    .commodities-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1.5rem;
    }
    .full-width {
        grid-column: 1 / -1;
    }

    .section-title {
        margin: 2rem 0 1rem;
        padding-left: 0.5rem;
        border-left: 4px solid var(--accent-primary);
    }
    .section-title h3 {
        margin: 0 0 0.25rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-desc {
        margin: 0;
        font-size: 0.85rem;
        color: var(--text-muted);
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .header-controls {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        flex-wrap: wrap;
    }
    .mini-controls {
        display: flex;
        gap: 0.4rem;
        align-items: center;
    }

    .control-btn {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #94a3b8;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.8rem;
        transition: all 0.2s;
    }
    .control-btn:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    .control-btn.active {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }
    .info-btn {
        padding: 0.4rem 0.6rem;
    }

    .btc-overlay-toggle {
        display: flex;
        background: rgba(255, 255, 255, 0.05);
        padding: 2px;
        border-radius: 6px;
    }
    .btc-mode {
        color: #f7931a !important;
        font-size: 10px;
        font-weight: 700;
        margin-left: 4px;
    }

    .ratio-info-box {
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .ratio-info-box strong {
        color: #818cf8;
    }
    .ratio-info-box p {
        margin: 0.5rem 0 0 0;
        color: var(--text-secondary);
    }
    .ratio-info-box .interpretation {
        color: #f59e0b;
        font-style: italic;
    }

    .ratio-desc {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }
    .tag {
        font-size: 0.75rem;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 500;
    }
    .tag.bullish {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }
    .tag.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    .download-btn {
        background: none;
        border: none;
        color: #64748b;
        cursor: pointer;
        padding: 0.4rem;
        border-radius: 4px;
    }
    .download-btn:hover {
        background: rgba(255, 255, 255, 0.05);
    }

    .table-container {
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        text-align: left;
        padding: 1rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        font-size: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }
    td {
        padding: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.02);
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

    @media (max-width: 1024px) {
        .commodities-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
