<script>
    /**
     * GlobalFlowsCbTab.svelte
     * Displays individual central bank balance sheet charts with time range controls.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import {
        filterPlotlyData,
        getCutoffDate,
        calculateZScore,
        calculatePercentile,
        calculateRollingZScore,
    } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";
    import { loadGLITabData, loadDomain } from "../utils/domainLoader.js";
    import { onMount } from "svelte";

    // Core props only
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges (no longer props)
    let fedRange = "ALL";
    let ecbRange = "ALL";
    let bojRange = "ALL";
    let boeRange = "ALL";
    let pbocRange = "ALL";
    let bocRange = "ALL";
    let rbaRange = "ALL";
    let snbRange = "ALL";
    let bokRange = "ALL";
    let rbiRange = "ALL";
    let cbrRange = "ALL";
    let bcbRange = "ALL";
    let rbnzRange = "ALL";
    let srRange = "ALL";
    let bnmRange = "ALL";
    let gliRange = "ALL";
    let cbBreadthRange = "5Y";
    let cbConcentrationRange = "5Y";

    // Card container references for full-card download feature
    let gliAggregateCard;
    let cbBreadthCard;
    let cbConcentrationCard;

    // GLI Aggregate chart state - similar to StableCoinsTab
    let gliAggregateMode = "absolute"; // Modes: absolute, roc1m, roc3m, roc6m, yoy
    let gliNormMode = "raw"; // Normalization: raw, zscore, percentile
    let gliLookbackWindow = 252; // Lookback window for rolling calculations: 63, 126, 252

    // Helper to get translation with fallback
    $: t = (key, fallback) => translations[key] || fallback;

    // Check if current mode supports normalization
    $: isGliRocMode = ["roc1m", "roc3m", "roc6m"].includes(gliAggregateMode);
    // Check if normalization mode requires lookback window
    $: showGliLookbackWindow =
        isGliRocMode &&
        (gliNormMode === "zscore" || gliNormMode === "percentile");

    // Modular data loading
    let modularGliData = null;
    let modularMacroRegime = null;
    onMount(async () => {
        try {
            const [gliResult, macroRegime] = await Promise.all([
                loadGLITabData(dashboardData),
                loadDomain("macro_regime"),
            ]);
            modularGliData = gliResult;
            modularMacroRegime = macroRegime;
            console.log("Modular GLI data loaded");
        } catch (e) {
            console.error("Error loading modular GLI data:", e);
        }
    });

    // Merge modular data with dashboardData (modular takes precedence)
    $: effectiveData = {
        ...dashboardData,
        gli: modularGliData?.gli || dashboardData.gli || {},
        dates: modularGliData?.dates || dashboardData.dates || [],
        macro_regime: modularMacroRegime || dashboardData.macro_regime || {},
        bank_rocs:
            modularGliData?.gli?.bank_rocs || dashboardData.bank_rocs || {},
        last_dates: dashboardData.last_dates || {},
    };

    // GLI Aggregate mode options
    $: gliAggregateModes = [
        { value: "absolute", label: t("raw_view", "Absolute") },
        { value: "roc1m", label: t("roc_1m_col", "ROC 1M") },
        { value: "roc3m", label: t("roc_3m_col", "ROC 3M") },
        { value: "roc6m", label: t("roc_6m_col", "ROC 6M") },
        { value: "yoy", label: t("yoy_change", "YoY %") },
    ];

    // Normalization mode options
    $: gliNormModes = [
        { value: "raw", label: t("raw_view", "Raw (%)") },
        { value: "zscore", label: "Z-Score" },
        { value: "percentile", label: t("percentile_view", "Percentile") },
    ];

    // Lookback window options for rolling calculations
    $: gliLookbackOptions = [
        { value: 63, label: "63d (1Q)" },
        { value: 126, label: "126d (6M)" },
        { value: 252, label: "252d (1Y)" },
    ];

    function selectGliMode(mode) {
        gliAggregateMode = mode;
    }

    function selectGliNormMode(mode) {
        gliNormMode = mode;
    }

    function selectGliLookbackWindow(value) {
        gliLookbackWindow = value;
    }

    // --- Internal Helper Functions ---
    function getLastDate(seriesKey) {
        if (!effectiveData.last_dates) return "N/A";
        const key = seriesKey.toUpperCase();
        return (
            effectiveData.last_dates[key] ||
            effectiveData.last_dates[key + "_USD"] ||
            effectiveData.last_dates[seriesKey] ||
            "N/A"
        );
    }

    // --- Internal Chart Data Processing ---

    // Get GLI data based on selected mode
    function getGliDataForMode(mode, normMode, data, lookbackWindow) {
        const gli = data.gli || {};
        const rocs = gli.rocs || {};

        let rawData;
        switch (mode) {
            case "roc1m":
                rawData = rocs["1M"] || [];
                break;
            case "roc3m":
                rawData = rocs["3M"] || [];
                break;
            case "roc6m":
                rawData = rocs["6M"] || [];
                break;
            case "yoy":
                rawData = rocs["1Y"] || [];
                break;
            default:
                return gli.total || [];
        }

        // Apply normalization if in ROC mode
        if (normMode === "zscore") {
            return calculateRollingZScore(rawData, lookbackWindow);
        } else if (normMode === "percentile") {
            return calculatePercentile(rawData, lookbackWindow);
        }
        return rawData;
    }

    // Get chart label based on mode
    function getGliChartLabel(mode, normMode) {
        const base =
            translations.chart_gli_aggregate || "Global Liquidity Index (GLI)";
        switch (mode) {
            case "roc1m":
                return `${base} - ROC 1M ${normMode !== "raw" ? `(${normMode})` : ""}`;
            case "roc3m":
                return `${base} - ROC 3M ${normMode !== "raw" ? `(${normMode})` : ""}`;
            case "roc6m":
                return `${base} - ROC 6M ${normMode !== "raw" ? `(${normMode})` : ""}`;
            case "yoy":
                return `${base} - YoY`;
            default:
                return base;
        }
    }

    // Reactive data based on mode selection - explicitly depends on gliAggregateMode, gliNormMode, and gliLookbackWindow
    $: gliChartData = getGliDataForMode(
        gliAggregateMode,
        gliNormMode,
        effectiveData,
        gliLookbackWindow,
    );
    $: gliChartLabel = getGliChartLabel(gliAggregateMode, gliNormMode);

    $: gliTotalData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: gliChartData,
                name: gliChartLabel,
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        gliRange,
    );

    $: fedData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.fed,
                name: translations.indicator_fed || "Fed Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        fedRange,
    );
    $: ecbData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.ecb,
                name: translations.indicator_ecb || "ECB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        ecbRange,
    );
    $: bojData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.boj,
                name: translations.indicator_boj || "BoJ Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        bojRange,
    );
    $: boeData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.boe,
                name: translations.indicator_boe || "BoE Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        boeRange,
    );
    $: pbocData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.pboc,
                name: translations.indicator_pboc || "PBoC Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        pbocRange,
    );
    $: bocData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.boc,
                name: translations.indicator_boc || "BoC Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#34d399", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        bocRange,
    );
    $: rbaData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.rba,
                name: translations.indicator_rba || "RBA Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#14b8a6", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        rbaRange,
    );
    $: snbData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.snb,
                name: translations.indicator_snb || "SNB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        snbRange,
    );
    $: bokData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.bok,
                name: translations.indicator_bok || "BoK Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#0ea5e9", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        bokRange,
    );
    $: rbiData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.rbi,
                name: translations.indicator_rbi || "RBI Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        rbiRange,
    );
    $: cbrData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.cbr,
                name: translations.indicator_cbr || "CBR Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        cbrRange,
    );
    $: bcbData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.bcb,
                name: translations.indicator_bcb || "BCB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        bcbRange,
    );
    $: rbnzData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.rbnz,
                name: translations.indicator_rbnz || "RBNZ Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#d946ef", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        rbnzRange,
    );
    $: srData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.sr,
                name: translations.indicator_sr || "Sveriges Riksbank",
                type: "scatter",
                mode: "lines",
                line: { color: "#ec4899", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        srRange,
    );
    $: bnmData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.gli?.bnm,
                name: translations.indicator_bnm || "BNM Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#fb923c", width: 3, shape: "spline" },
            },
        ],
        effectiveData.dates,
        bnmRange,
    );

    // CB Breadth and Concentration data (Plotly format for better stability)
    // Now with time range filtering
    $: cbBreadthData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.macro_regime?.cb_diffusion_13w,
                name:
                    translations.indicator_cb_breadth ||
                    "CB Breadth (% Expanding)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(16, 185, 129, 0.1)",
            },
        ],
        effectiveData.dates,
        cbBreadthRange,
    );

    $: cbConcentrationData = filterPlotlyData(
        [
            {
                x: effectiveData.dates,
                y: effectiveData.macro_regime?.cb_hhi_13w,
                name: translations.indicator_cb_hhi || "CB Concentration (HHI)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2, shape: "spline" },
            },
        ],
        effectiveData.dates,
        cbConcentrationRange,
    );

    // Bank ROC lookup for indicators
    function getBankRocs(bankId) {
        const rocs = effectiveData.bank_rocs?.[bankId] || {};
        const getLatest = (arr) => arr?.[arr?.length - 1] ?? null;
        return {
            w1: getLatest(rocs["1W"]),
            m1: getLatest(rocs["1M"]),
            m3: getLatest(rocs["3M"]),
            m6: getLatest(rocs["6M"]),
        };
    }

    // GLI Total ROC helper for aggregate indicator
    function getGliTotalRocs() {
        const rocs = effectiveData.gli?.rocs || {};
        const getLatest = (arr) => arr?.[arr?.length - 1] ?? null;
        return {
            m1: getLatest(rocs["1M"]),
            m3: getLatest(rocs["3M"]),
            m6: getLatest(rocs["6M"]),
            y1: getLatest(rocs["1Y"]),
        };
    }

    // Bank configuration - STATIC to avoid cyclical dependencies
    const bankConfigs = [
        { id: "fed", name: "Federal Reserve (Fed)", bank: "FED" },
        { id: "ecb", name: "European Central Bank (ECB)", bank: "ECB" },
        { id: "boj", name: "Bank of Japan (BoJ)", bank: "BOJ" },
        { id: "boe", name: "Bank of England (BoE)", bank: "BOE" },
        { id: "pboc", name: "People's Bank of China (PBoC)", bank: "PBOC" },
        { id: "boc", name: "Bank of Canada (BoC)", bank: "BOC" },
        { id: "rba", name: "Reserve Bank of Australia (RBA)", bank: "RBA" },
        { id: "snb", name: "Swiss National Bank (SNB)", bank: "SNB" },
        { id: "bok", name: "Bank of Korea (BoK)", bank: "BOK" },
        { id: "rbi", name: "Reserve Bank of India (RBI)", bank: "RBI" },
        { id: "cbr", name: "Central Bank of Russia (CBR)", bank: "CBR" },
        { id: "bcb", name: "Central Bank of Brazil (BCB)", bank: "BCB" },
        {
            id: "rbnz",
            name: "Reserve Bank of New Zealand (RBNZ)",
            bank: "RBNZ",
        },
        { id: "sr", name: "Sveriges Riksbank (SR)", bank: "SR" },
        { id: "bnm", name: "Bank Negara Malaysia (BNM)", bank: "BNM" },
    ];

    // REACTIVE data and ranges map - Svelte tracks these objects for reactivity
    // When a range changes, the corresponding data is recomputed
    $: bankRanges = {
        fed: fedRange,
        ecb: ecbRange,
        boj: bojRange,
        boe: boeRange,
        pboc: pbocRange,
        boc: bocRange,
        rba: rbaRange,
        snb: snbRange,
        bok: bokRange,
        rbi: rbiRange,
        cbr: cbrRange,
        bcb: bcbRange,
        rbnz: rbnzRange,
        sr: srRange,
        bnm: bnmRange,
    };

    $: bankChartData = {
        fed: fedData,
        ecb: ecbData,
        boj: bojData,
        boe: boeData,
        pboc: pbocData,
        boc: bocData,
        rba: rbaData,
        snb: snbData,
        bok: bokData,
        rbi: rbiData,
        cbr: cbrData,
        bcb: bcbData,
        rbnz: rbnzData,
        sr: srData,
        bnm: bnmData,
    };

    function setRangeForBank(id, r) {
        if (id === "fed") fedRange = r;
        else if (id === "ecb") ecbRange = r;
        else if (id === "boj") bojRange = r;
        else if (id === "boe") boeRange = r;
        else if (id === "pboc") pbocRange = r;
        else if (id === "boc") bocRange = r;
        else if (id === "rba") rbaRange = r;
        else if (id === "snb") snbRange = r;
        else if (id === "bok") bokRange = r;
        else if (id === "rbi") rbiRange = r;
        else if (id === "cbr") cbrRange = r;
        else if (id === "bcb") bcbRange = r;
        else if (id === "rbnz") rbnzRange = r;
        else if (id === "sr") srRange = r;
        else if (id === "bnm") bnmRange = r;
        else if (id === "gli") gliRange = r;
    }
</script>

<div class="flows-container">
    <!-- All Charts in 2-column grid -->
    <div class="chart-grid">
        <!-- First Row: Aggregate GLI Chart -->
        <div class="chart-card wide" bind:this={gliAggregateCard}>
            <div class="chart-header">
                <h3>
                    {translations.chart_gli || "Global Liquidity Index (GLI)"}
                </h3>
                <div class="header-controls">
                    <Dropdown
                        options={gliAggregateModes}
                        bind:value={gliAggregateMode}
                        onSelect={selectGliMode}
                        {darkMode}
                        small={true}
                    />
                    {#if isGliRocMode}
                        <Dropdown
                            options={gliNormModes}
                            bind:value={gliNormMode}
                            onSelect={selectGliNormMode}
                            {darkMode}
                            small={true}
                        />
                    {/if}
                    {#if showGliLookbackWindow}
                        <Dropdown
                            options={gliLookbackOptions}
                            bind:value={gliLookbackWindow}
                            onSelect={selectGliLookbackWindow}
                            {darkMode}
                            small={true}
                        />
                    {/if}
                    <TimeRangeSelector
                        selectedRange={gliRange}
                        onRangeChange={(r) => setRangeForBank("gli", r)}
                    />
                    <button
                        class="download-btn"
                        title="Download Chart"
                        on:click={() =>
                            downloadCardAsImage(
                                gliAggregateCard,
                                "global_liquidity_index",
                            )}
                    >
                        📥
                    </button>
                </div>
            </div>
            <p class="chart-description">
                {translations.gli_desc ||
                    "Aggregate central bank balance sheets in USD. Larger = more weight in global liquidity."}
            </p>
            <div class="chart-content short">
                <Chart
                    {darkMode}
                    data={gliTotalData}
                    cardContainer={gliAggregateCard}
                    cardTitle="global_liquidity_index"
                />
            </div>

            <div class="card-divider"></div>
            <!-- Aggregate ROC Indicators -->
            {#if dashboardData.gli?.rocs}
                {@const totalRocs = getGliTotalRocs()}
                <div class="metrics-footer">
                    <div class="roc-bar">
                        <div
                            class="roc-item"
                            class:positive={totalRocs.m1 > 0}
                            class:negative={totalRocs.m1 < 0}
                        >
                            <span class="roc-label">1M</span>
                            <span class="roc-value"
                                >{totalRocs.m1 !== null
                                    ? totalRocs.m1.toFixed(1) + "%"
                                    : "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={totalRocs.m3 > 0}
                            class:negative={totalRocs.m3 < 0}
                        >
                            <span class="roc-label">3M</span>
                            <span class="roc-value"
                                >{totalRocs.m3 !== null
                                    ? totalRocs.m3.toFixed(1) + "%"
                                    : "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={totalRocs.m6 > 0}
                            class:negative={totalRocs.m6 < 0}
                        >
                            <span class="roc-label">6M</span>
                            <span class="roc-value"
                                >{totalRocs.m6 !== null
                                    ? totalRocs.m6.toFixed(1) + "%"
                                    : "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={totalRocs.y1 > 0}
                            class:negative={totalRocs.y1 < 0}
                        >
                            <span class="roc-label">1Y</span>
                            <span class="roc-value"
                                >{totalRocs.y1 !== null
                                    ? totalRocs.y1.toFixed(1) + "%"
                                    : "N/A"}</span
                            >
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- CB Breadth Chart -->
        <div class="chart-card" bind:this={cbBreadthCard}>
            <div class="chart-header">
                <h3>
                    {translations.indicator_cb_breadth ||
                        "Central Bank Breadth (% Expanding)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cbBreadthRange}
                        onRangeChange={(r) => (cbBreadthRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.cb_breadth_desc ||
                    "Percentage of CBs expanding (13-week basis). ↑ Bullish."}
            </p>
            <div class="chart-content short">
                <Chart
                    {darkMode}
                    data={cbBreadthData}
                    cardContainer={cbBreadthCard}
                    cardTitle="cb_breadth"
                />
            </div>
        </div>

        <!-- CB Concentration Chart -->
        <div class="chart-card" bind:this={cbConcentrationCard}>
            <div class="chart-header">
                <h3>
                    {translations.indicator_cb_hhi ||
                        "Central Bank Concentration (HHI)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cbConcentrationRange}
                        onRangeChange={(r) => (cbConcentrationRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.cb_hhi_desc ||
                    "HHI Index. High = few banks drive liquidity."}
            </p>
            <div class="chart-content short">
                <Chart
                    {darkMode}
                    data={cbConcentrationData}
                    cardContainer={cbConcentrationCard}
                    cardTitle="cb_concentration"
                />
            </div>
        </div>

        <!-- Individual Banks with ROC indicators -->
        {#each bankConfigs as item}
            {@const rocs = getBankRocs(item.id)}
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{item.name}</h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={bankRanges[item.id]}
                            onRangeChange={(r) => setRangeForBank(item.id, r)}
                        />
                        <span class="last-date">{getLastDate(item.bank)}</span>
                    </div>
                </div>
                <div class="chart-content short">
                    <Chart {darkMode} data={bankChartData[item.id]} />
                </div>
                <div class="card-divider"></div>
                <div class="metrics-footer">
                    <div class="roc-bar">
                        <div
                            class="roc-item"
                            class:positive={rocs.w1 > 0}
                            class:negative={rocs.w1 < 0}
                        >
                            <span class="roc-label"
                                >{translations.val_1w || "1W"}</span
                            >
                            <span class="roc-value"
                                >{rocs.w1 !== null
                                    ? rocs.w1.toFixed(1) + "%"
                                    : translations.na || "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={rocs.m1 > 0}
                            class:negative={rocs.m1 < 0}
                        >
                            <span class="roc-label"
                                >{translations.val_1m || "1M"}</span
                            >
                            <span class="roc-value"
                                >{rocs.m1 !== null
                                    ? rocs.m1.toFixed(1) + "%"
                                    : translations.na || "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={rocs.m3 > 0}
                            class:negative={rocs.m3 < 0}
                        >
                            <span class="roc-label"
                                >{translations.val_3m || "3M"}</span
                            >
                            <span class="roc-value"
                                >{rocs.m3 !== null
                                    ? rocs.m3.toFixed(1) + "%"
                                    : translations.na || "N/A"}</span
                            >
                        </div>
                        <div
                            class="roc-item"
                            class:positive={rocs.m6 > 0}
                            class:negative={rocs.m6 < 0}
                        >
                            <span class="roc-label"
                                >{translations.val_6m || "6M"}</span
                            >
                            <span class="roc-value"
                                >{rocs.m6 !== null
                                    ? rocs.m6.toFixed(1) + "%"
                                    : translations.na || "N/A"}</span
                            >
                        </div>
                    </div>
                </div>
            </div>
        {/each}
    </div>
</div>

<style>
    .flows-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding-bottom: 40px;
    }

    /* Use global .chart-card styles */

    .chart-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        flex-wrap: wrap;
        gap: 8px;
    }

    .chart-header h3 {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .header-controls {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .last-date {
        font-size: 0.7rem;
        color: var(--text-muted);
        background: var(--bg-tertiary);
        padding: 3px 6px;
        border-radius: 4px;
    }

    .chart-description {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin: 0 0 12px 0;
        padding: 8px 10px;
        background: var(--chart-description-bg);
        border-radius: 6px;
        border-left: 3px solid var(--accent-primary);
    }

    .chart-content {
        min-height: 450px;
        height: 450px;
        flex-shrink: 0;
        margin-bottom: 30px;
    }

    .chart-content.short {
        min-height: 480px;
        height: 480px;
        margin-bottom: 30px;
    }

    .card-divider {
        height: 1px;
        background: var(--border-color);
        margin: 20px 0;
        opacity: 0.5;
    }

    .metrics-footer {
        width: 100%;
    }

    /* ROC Indicator Bar */
    .roc-bar {
        display: flex;
        justify-content: space-around;
        padding: 5px 0;
        gap: 8px;
    }

    .roc-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 6px 12px;
        background: var(--bg-secondary);
        border-radius: 6px;
        min-width: 50px;
        border: 1px solid var(--border-color);
    }

    .roc-item.positive {
        border-color: #10b981;
        background: rgba(16, 185, 129, 0.1);
    }

    .roc-item.negative {
        border-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }

    .roc-label {
        font-size: 0.65rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .roc-value {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .roc-item.positive .roc-value {
        color: #10b981;
    }

    .roc-item.negative .roc-value {
        color: #ef4444;
    }

    @media (max-width: 1200px) {
        .chart-grid {
            grid-template-columns: 1fr;
        }
    }

    .download-btn {
        background: transparent;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s ease;
    }
    .download-btn:hover {
        background: var(--accent-primary);
        border-color: var(--accent-primary);
    }
</style>
