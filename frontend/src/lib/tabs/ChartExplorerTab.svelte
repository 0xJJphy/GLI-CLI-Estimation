<script>
    /**
     * ChartExplorerTab.svelte
     * Advanced data exploration and ROC analysis.
     */
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import {
        calculateROC,
        alignSeries,
        shiftSeries,
        formatForTV,
    } from "../utils/analytics.js";
    import { getFilteredIndices } from "../utils/helpers.js";

    // Core props
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state
    let selectedSource = "us_net_liq";
    let selectedRocPeriod = 21; // Default 21 days (~1M)
    let selectedOffset = 0; // Default 0 days
    let showBtcOverlay = false;
    let timeRange = "ALL";

    // Second chart state (Absolute)
    let selectedSourceAbs = "us_net_liq";
    let selectedOffsetAbs = 0;
    let showBtcOverlayAbs = true;
    let timeRangeAbs = "ALL";

    // Component bindings
    let momentumChart;
    let absoluteChart;

    // Sources configuration
    const sources = [
        { id: "us_net_liq", name: "US Net Liquidity", color: "#10b981" },
        { id: "us_net_liq_reserves", name: "Bank Reserves", color: "#22c55e" },
        { id: "gli_fed", name: "Fed Assets", color: "#3b82f6" },
        { id: "us_net_liq_tga", name: "Treasury TGA", color: "#f59e0b" },
        { id: "us_net_liq_rrp", name: "Fed RRP", color: "#ef4444" },
    ];

    const rocPeriods = [
        { label: "7D", value: 7 },
        { label: "14D", value: 14 },
        { label: "21D", value: 21 },
        { label: "30D", value: 30 },
        { label: "60D", value: 60 },
        { label: "90D", value: 90 },
        { label: "180D", value: 180 },
    ];

    // Reactive calculations
    $: sourceConfig = sources.find((s) => s.id === selectedSource);

    $: rawSourceData = (() => {
        let values = [];
        if (selectedSource === "gli_fed") {
            values = dashboardData.gli?.fed || [];
        } else {
            values = dashboardData[selectedSource] || [];
        }
        return calculateROC(dashboardData.dates, values, selectedRocPeriod);
    })();

    // Apply offset to source data
    $: sourceData = shiftSeries(
        rawSourceData.x,
        rawSourceData.y,
        selectedOffset,
    );

    $: btcRocData = showBtcOverlay
        ? calculateROC(
              dashboardData.dates,
              dashboardData.btc?.price || [],
              selectedRocPeriod,
          )
        : { x: [], y: [] };

    // Master timescale for the chart (includes future dates if offset > 0)
    $: masterDates = (() => {
        if (selectedOffset <= 0) return dashboardData.dates;
        const dates = [...dashboardData.dates];
        const lastDateStr = dates[dates.length - 1];
        if (!lastDateStr) return dates;
        const lastDate = new Date(lastDateStr);
        for (let i = 1; i <= selectedOffset; i++) {
            const next = new Date(lastDate);
            next.setDate(next.getDate() + i);
            dates.push(next.toISOString().split("T")[0]);
        }
        return dates;
    })();

    // Filter masterDates based on timeRange
    $: filteredIndices = getFilteredIndices(masterDates, timeRange);

    $: chartDataTV = (() => {
        // Aligned Source Data
        const alignedSource = alignSeries(
            { x: masterDates, y: [] },
            sourceData,
        );
        // Filter by indicators
        const filteredSourceX = filteredIndices.map((i) => alignedSource.x[i]);
        const filteredSourceY = filteredIndices.map(
            (i) => alignedSource.yOverlay[i],
        );

        const seriesArr = [
            {
                name: `${sourceConfig.name} ROC`,
                type: "area",
                color: sourceConfig.color,
                data: formatForTV({ x: filteredSourceX, y: filteredSourceY }),
                priceScaleId: "left",
                topColor: `${sourceConfig.color}40`,
                bottomColor: "transparent",
            },
        ];

        if (showBtcOverlay && btcRocData.x.length > 0) {
            const alignedBtc = alignSeries(
                { x: masterDates, y: [] },
                btcRocData,
            );
            const filteredBtcX = filteredIndices.map((i) => alignedBtc.x[i]);
            const filteredBtcY = filteredIndices.map(
                (i) => alignedBtc.yOverlay[i],
            );

            seriesArr.push({
                name: `BTC ROC`,
                type: "line",
                color: "#f59e0b",
                data: formatForTV({ x: filteredBtcX, y: filteredBtcY }),
                priceScaleId: "right",
                topColor: "transparent",
                bottomColor: "transparent",
            });
        }

        return seriesArr;
    })();

    // --- SECOND CHART: ABSOLUTE ---

    $: rawSourceDataAbs = (() => {
        let values = [];
        if (selectedSourceAbs === "gli_fed") {
            values = dashboardData.gli?.fed || [];
        } else {
            values = dashboardData[selectedSourceAbs] || [];
        }
        return { x: dashboardData.dates || [], y: values };
    })();

    $: sourceDataAbs = shiftSeries(
        rawSourceDataAbs.x,
        rawSourceDataAbs.y,
        selectedOffsetAbs,
    );

    $: btcPriceData = showBtcOverlayAbs
        ? { x: dashboardData.dates || [], y: dashboardData.btc?.price || [] }
        : { x: [], y: [] };

    $: masterDatesAbs = (() => {
        if (selectedOffsetAbs <= 0) return dashboardData.dates;
        const dates = [...dashboardData.dates];
        const lastDateStr = dates[dates.length - 1];
        if (!lastDateStr) return dates;
        const lastDate = new Date(lastDateStr);
        for (let i = 1; i <= selectedOffsetAbs; i++) {
            const next = new Date(lastDate);
            next.setDate(next.getDate() + i);
            dates.push(next.toISOString().split("T")[0]);
        }
        return dates;
    })();

    $: filteredIndicesAbs = getFilteredIndices(masterDatesAbs, timeRangeAbs);

    $: chartDataAbsTV = (() => {
        const sourceCfg = sources.find((s) => s.id === selectedSourceAbs);

        // Aligned Source Data
        const alignedSource = alignSeries(
            { x: masterDatesAbs, y: [] },
            sourceDataAbs,
        );
        const filteredX = filteredIndicesAbs.map((i) => alignedSource.x[i]);
        const filteredY = filteredIndicesAbs.map(
            (i) => alignedSource.yOverlay[i],
        );

        const seriesArr = [
            {
                name: sourceCfg.name,
                type: "area",
                color: sourceCfg.color,
                data: formatForTV({ x: filteredX, y: filteredY }),
                priceScaleId: "left",
                topColor: `${sourceCfg.color}40`,
                bottomColor: "transparent",
            },
        ];

        if (showBtcOverlayAbs && btcPriceData.x.length > 0) {
            const alignedBtc = alignSeries(
                { x: masterDatesAbs, y: [] },
                btcPriceData,
            );
            const filteredBtcX = filteredIndicesAbs.map((i) => alignedBtc.x[i]);
            const filteredBtcY = filteredIndicesAbs.map(
                (i) => alignedBtc.yOverlay[i],
            );

            seriesArr.push({
                name: `BTC Price`,
                type: "line",
                color: "#f59e0b",
                data: formatForTV({ x: filteredBtcX, y: filteredBtcY }),
                priceScaleId: "right",
                topColor: "transparent",
                bottomColor: "transparent",
            });
        }
        return seriesArr;
    })();

    function handleSourceChange(e) {
        selectedSource = e.target.value;
    }

    function handleRocChange(value) {
        selectedRocPeriod = value;
    }

    function resetMomentum() {
        if (momentumChart) momentumChart.resetScales();
    }

    function resetAbsolute() {
        if (absoluteChart) absoluteChart.resetScales();
    }

    function downloadChart(chart) {
        if (chart) chart.downloadChart();
    }

    function toggleFullscreen(chart) {
        if (chart) chart.toggleFullscreen();
    }
</script>

<div class="main-charts chart-explorer">
    <div class="chart-card wide">
        <div class="chart-header">
            <div>
                <h3 class="chart-title" style="font-family: var(--font-mono);">
                    {translations.nav_chart_explorer || "Chart Explorer"}
                </h3>
                <p
                    class="description"
                    style="margin: 4px 0 0 0; font-size: 0.85rem; color: var(--text-muted);"
                >
                    {translations.chart_explorer_desc ||
                        "Explore US System momentum and correlations."}
                </p>
            </div>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={timeRange}
                    onRangeChange={(r) => (timeRange = r)}
                />
            </div>
        </div>

        <div class="explorer-controls">
            <div class="control-group">
                <label for="explorer-source">
                    {translations.source_label || "Source"}
                </label>
                <select
                    id="explorer-source"
                    bind:value={selectedSource}
                    class="styled-select"
                >
                    {#each sources as source}
                        <option value={source.id}>{source.name}</option>
                    {/each}
                </select>
            </div>

            <div class="control-group">
                <span class="control-label"
                    >{translations.roc_period_label || "ROC Period"}</span
                >
                <div class="roc-buttons">
                    {#each rocPeriods as period}
                        <button
                            class="period-btn"
                            class:active={selectedRocPeriod === period.value}
                            on:click={() => handleRocChange(period.value)}
                        >
                            {period.label}
                        </button>
                    {/each}
                </div>
            </div>

            <div class="control-group">
                <label for="explorer-offset">
                    {translations.offset_label || "Offset"}: {selectedOffset > 0
                        ? "+"
                        : ""}{selectedOffset}d
                </label>
                <input
                    id="explorer-offset"
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    bind:value={selectedOffset}
                    class="styled-range"
                />
            </div>

            <div class="control-group inline">
                <label class="checkbox-container" for="btc-overlay-toggle">
                    <input
                        type="checkbox"
                        id="btc-overlay-toggle"
                        bind:checked={showBtcOverlay}
                    />
                    <span class="checkmark"></span>
                    {translations.btc_overlay_label || "Overlay BTC ROC"}
                </label>
            </div>
        </div>

        <div class="chart-content relative">
            <LightweightChart
                bind:this={momentumChart}
                {darkMode}
                data={chartDataTV}
                title={translations.momentum_vs_btc || "Momentum vs Bitcoin"}
            />
            <div class="chart-actions">
                <button
                    class="action-btn"
                    title={translations.download_chart}
                    on:click={() => downloadChart(momentumChart)}
                >
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path
                            fill="currentColor"
                            d="M12 16l-5-5h3V4h4v7h3l-5 5zm-9 4h18v-2H3v2z"
                        />
                    </svg>
                </button>
                <button
                    class="action-btn"
                    title={translations.fullscreen}
                    on:click={() => toggleFullscreen(momentumChart)}
                >
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path
                            fill="currentColor"
                            d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
                        />
                    </svg>
                </button>
                <button class="reset-btn" on:click={resetMomentum}>
                    {translations.reset_view || "Reset"}
                </button>
            </div>
        </div>
    </div>

    <!-- ABSOLUTE CHART SECTION -->
    <div class="chart-card wide">
        <div class="chart-header">
            <div>
                <h3 class="chart-title" style="font-family: var(--font-mono);">
                    {translations.abs_chart_title || "Absolute Explorer"}
                </h3>
                <p
                    class="description"
                    style="margin: 4px 0 0 0; font-size: 0.85rem; color: var(--text-muted);"
                >
                    {translations.abs_chart_desc ||
                        "Explore levels and price relationships."}
                </p>
            </div>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={timeRangeAbs}
                    onRangeChange={(r) => (timeRangeAbs = r)}
                />
            </div>
        </div>

        <div class="explorer-controls">
            <div class="control-group">
                <label for="explorer-source-abs">
                    {translations.source_label || "Source"}
                </label>
                <select
                    id="explorer-source-abs"
                    bind:value={selectedSourceAbs}
                    class="styled-select"
                >
                    {#each sources as source}
                        <option value={source.id}>{source.name}</option>
                    {/each}
                </select>
            </div>

            <div class="control-group">
                <label for="explorer-offset-abs">
                    {translations.offset_label || "Offset"}: {selectedOffsetAbs >
                    0
                        ? "+"
                        : ""}{selectedOffsetAbs}d
                </label>
                <input
                    id="explorer-offset-abs"
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    bind:value={selectedOffsetAbs}
                    class="styled-range"
                />
            </div>

            <div class="control-group inline">
                <label class="checkbox-container" for="btc-price-toggle">
                    <input
                        type="checkbox"
                        id="btc-price-toggle"
                        bind:checked={showBtcOverlayAbs}
                    />
                    <span class="checkmark"></span>
                    {translations.btc_price_overlay || "Overlay BTC Price"}
                </label>
            </div>
        </div>

        <div class="chart-content relative">
            <LightweightChart
                bind:this={absoluteChart}
                {darkMode}
                data={chartDataAbsTV}
                title={translations.abs_vs_btc || "Levels vs Bitcoin"}
            />
            <div class="chart-actions">
                <button
                    class="action-btn"
                    title={translations.download_chart}
                    on:click={() => downloadChart(absoluteChart)}
                >
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path
                            fill="currentColor"
                            d="M12 16l-5-5h3V4h4v7h3l-5 5zm-9 4h18v-2H3v2z"
                        />
                    </svg>
                </button>
                <button
                    class="action-btn"
                    title={translations.fullscreen}
                    on:click={() => toggleFullscreen(absoluteChart)}
                >
                    <svg viewBox="0 0 24 24" width="14" height="14">
                        <path
                            fill="currentColor"
                            d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
                        />
                    </svg>
                </button>
                <button class="reset-btn" on:click={resetAbsolute}>
                    {translations.reset_view || "Reset"}
                </button>
            </div>
        </div>
    </div>
</div>

<style>
    .chart-content.relative {
        position: relative;
    }

    .chart-actions {
        position: absolute;
        top: 10px;
        right: 10px;
        display: flex;
        gap: 6px;
        z-index: 10;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: 6px;
        backdrop-filter: blur(4px);
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
    }

    .action-btn {
        background: transparent;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .action-btn:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .reset-btn {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        color: var(--accent-primary);
        padding: 2px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.75rem;
        font-weight: 600;
        transition: all 0.2s;
        margin-left: 4px;
    }

    .reset-btn:hover {
        background: var(--accent-primary);
        color: white;
        border-color: var(--accent-primary);
    }

    .explorer-controls {
        display: flex;
        flex-wrap: wrap;
        gap: 24px;
        margin-bottom: 24px;
        padding: 16px;
        background: var(--bg-tertiary);
        border-radius: 12px;
        align-items: flex-end;
    }

    .control-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .control-group.inline {
        flex-direction: row;
        align-items: center;
        padding-bottom: 8px;
    }

    .control-group label,
    .control-label {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .styled-select,
    .styled-range {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        color: var(--text-primary);
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 0.9rem;
        cursor: pointer;
        outline: none;
    }

    .styled-range {
        padding: 4px;
        width: 150px;
    }

    .roc-buttons {
        display: flex;
        gap: 4px;
        background: var(--bg-secondary);
        padding: 4px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }

    .period-btn {
        background: transparent;
        border: none;
        color: var(--text-muted);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }

    .period-btn:hover {
        color: var(--text-primary);
        background: var(--bg-tertiary);
    }

    .period-btn.active {
        background: var(--accent-primary);
        color: white;
    }

    /* Styled Checkbox */
    .checkbox-container {
        display: flex;
        align-items: center;
        position: relative;
        padding-left: 28px;
        cursor: pointer;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
        user-select: none;
    }

    .checkbox-container input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
        height: 0;
        width: 0;
    }

    .checkmark {
        position: absolute;
        top: 50%;
        left: 0;
        transform: translateY(-50%);
        height: 18px;
        width: 18px;
        background-color: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }

    .checkbox-container:hover input ~ .checkmark {
        background-color: var(--bg-tertiary);
    }

    .checkbox-container input:checked ~ .checkmark {
        background-color: var(--accent-primary);
        border-color: var(--accent-primary);
    }

    .checkmark:after {
        content: "";
        position: absolute;
        display: none;
    }

    .checkbox-container input:checked ~ .checkmark:after {
        display: block;
    }

    .checkbox-container .checkmark:after {
        left: 6px;
        top: 2px;
        width: 5px;
        height: 10px;
        border: solid white;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
    }
</style>
