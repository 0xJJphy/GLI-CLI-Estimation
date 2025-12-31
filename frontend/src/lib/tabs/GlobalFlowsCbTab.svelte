<script>
    /**
     * GlobalFlowsCbTab.svelte
     * Displays individual central bank balance sheet charts with time range controls.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData, getCutoffDate } from "../utils/helpers.js";

    // Core props only
    export let darkMode = false;
    export let language = "en";
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
    let cbBreadthRange = "ALL";
    let cbConcentrationRange = "ALL";

    // --- Internal Helper Functions ---
    function getLastDate(seriesKey) {
        if (!dashboardData.last_dates) return "N/A";
        const key = seriesKey.toUpperCase();
        return (
            dashboardData.last_dates[key] ||
            dashboardData.last_dates[key + "_USD"] ||
            dashboardData.last_dates[seriesKey] ||
            "N/A"
        );
    }

    // --- Internal Chart Data Processing ---
    $: fedData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.fed,
                name: "Fed Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        fedRange,
    );
    $: ecbData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.ecb,
                name: "ECB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        ecbRange,
    );
    $: bojData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.boj,
                name: "BoJ Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        bojRange,
    );
    $: boeData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.boe,
                name: "BoE Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        boeRange,
    );
    $: pbocData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.pboc,
                name: "PBoC Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        pbocRange,
    );
    $: bocData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.boc,
                name: "BoC Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#34d399", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        bocRange,
    );
    $: rbaData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.rba,
                name: "RBA Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#14b8a6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        rbaRange,
    );
    $: snbData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.snb,
                name: "SNB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        snbRange,
    );
    $: bokData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.bok,
                name: "BoK Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#0ea5e9", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        bokRange,
    );
    $: rbiData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.rbi,
                name: "RBI Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        rbiRange,
    );
    $: cbrData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.cbr,
                name: "CBR Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        cbrRange,
    );
    $: bcbData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.bcb,
                name: "BCB Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        bcbRange,
    );
    $: rbnzData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.rbnz,
                name: "RBNZ Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#d946ef", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        rbnzRange,
    );
    $: srData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.sr,
                name: "SR Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#ec4899", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        srRange,
    );
    $: bnmData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.gli?.bnm,
                name: "BNM Assets",
                type: "scatter",
                mode: "lines",
                line: { color: "#fb923c", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        bnmRange,
    );

    // CB Breadth and Concentration data (Plotly format for better stability)
    // Now with time range filtering
    $: cbBreadthData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.macro_regime?.cb_diffusion_13w,
                name: "CB Breadth (% Expanding)",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2, shape: "spline" },
                fill: "tozeroy",
                fillcolor: "rgba(16, 185, 129, 0.1)",
            },
        ],
        dashboardData.dates,
        cbBreadthRange,
    );

    $: cbConcentrationData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.macro_regime?.cb_hhi_13w,
                name: "CB Concentration (HHI)",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2, shape: "spline" },
            },
        ],
        dashboardData.dates,
        cbConcentrationRange,
    );

    // Bank ROC lookup for indicators
    function getBankRocs(bankId) {
        const rocs = dashboardData.bank_rocs?.[bankId] || {};
        const getLatest = (arr) => arr?.[arr?.length - 1] ?? null;
        return {
            w1: getLatest(rocs["1W"]),
            m1: getLatest(rocs["1M"]),
            m3: getLatest(rocs["3M"]),
            m6: getLatest(rocs["6M"]),
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
    }
</script>

<div class="flows-container">
    <!-- First Row: Aggregate GLI Chart (Full Width) -->
    <div class="chart-card full-width">
        <div class="chart-header">
            <h3>{translations.chart_gli || "Global Liquidity Index (GLI)"}</h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={fedRange}
                    onRangeChange={(r) => setRangeForBank("fed", r)}
                />
                <span class="last-date"
                    >{translations.last_data || "Last:"}
                    {getLastDate("GLI")}</span
                >
            </div>
        </div>
        <p class="chart-description">
            {translations.gli_desc ||
                "Aggregate central bank balance sheets in USD. Larger = more weight in global liquidity."}
        </p>
        <div class="chart-content">
            <Chart {darkMode} data={bankChartData.fed} />
        </div>
    </div>

    <!-- All Charts in 2-column grid -->
    <div class="chart-grid">
        <!-- CB Breadth Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Central Bank Breadth (% Expanding)</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cbBreadthRange}
                        onRangeChange={(r) => (cbBreadthRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {language === "es"
                    ? "% de bancos centrales en expansión (13 semanas). ↑ Alcista."
                    : "Percentage of CBs expanding (13-week basis). ↑ Bullish."}
            </p>
            <div class="chart-content short">
                <Chart {darkMode} data={cbBreadthData} />
            </div>
        </div>

        <!-- CB Concentration Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Central Bank Concentration (HHI)</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cbConcentrationRange}
                        onRangeChange={(r) => (cbConcentrationRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {language === "es"
                    ? "Índice HHI. Alto = pocos bancos dominan flujos."
                    : "HHI Index. High = few banks drive liquidity."}
            </p>
            <div class="chart-content short">
                <Chart {darkMode} data={cbConcentrationData} />
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
                <!-- ROC Indicators -->
                <div class="roc-bar">
                    <div
                        class="roc-item"
                        class:positive={rocs.w1 > 0}
                        class:negative={rocs.w1 < 0}
                    >
                        <span class="roc-label">1W</span>
                        <span class="roc-value"
                            >{rocs.w1 !== null
                                ? rocs.w1.toFixed(1) + "%"
                                : "N/A"}</span
                        >
                    </div>
                    <div
                        class="roc-item"
                        class:positive={rocs.m1 > 0}
                        class:negative={rocs.m1 < 0}
                    >
                        <span class="roc-label">1M</span>
                        <span class="roc-value"
                            >{rocs.m1 !== null
                                ? rocs.m1.toFixed(1) + "%"
                                : "N/A"}</span
                        >
                    </div>
                    <div
                        class="roc-item"
                        class:positive={rocs.m3 > 0}
                        class:negative={rocs.m3 < 0}
                    >
                        <span class="roc-label">3M</span>
                        <span class="roc-value"
                            >{rocs.m3 !== null
                                ? rocs.m3.toFixed(1) + "%"
                                : "N/A"}</span
                        >
                    </div>
                    <div
                        class="roc-item"
                        class:positive={rocs.m6 > 0}
                        class:negative={rocs.m6 < 0}
                    >
                        <span class="roc-label">6M</span>
                        <span class="roc-value"
                            >{rocs.m6 !== null
                                ? rocs.m6.toFixed(1) + "%"
                                : "N/A"}</span
                        >
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
        padding: 24px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        box-shadow: var(--card-shadow);
    }

    .chart-card.full-width {
        width: 100%;
    }

    .chart-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .chart-card.half {
        width: 100%;
        height: fit-content;
    }

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
        height: 350px;
        min-height: 350px;
    }

    .chart-content.short {
        height: 280px;
        min-height: 280px;
    }

    /* ROC Indicator Bar */
    .roc-bar {
        display: flex;
        justify-content: space-around;
        margin-top: 12px;
        padding: 10px;
        background: var(--bg-tertiary);
        border-radius: 8px;
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
        .chart-row {
            grid-template-columns: 1fr;
        }
    }
</style>
