<script>
    /**
     * GlobalFlowsCbTab.svelte
     * Displays individual central bank balance sheet charts with time range controls.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";

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

    // CB Breadth and Concentration data (for LightweightChart format)
    // Correct paths: macro_regime.cb_diffusion_13w and macro_regime.cb_hhi_13w
    $: cbBreadthData = (dashboardData.macro_regime?.cb_diffusion_13w || [])
        .map((v, i) => ({
            time: dashboardData.dates?.[i],
            value: v,
        }))
        .filter((d) => d.time && d.value !== null);

    $: cbConcentrationData = (dashboardData.macro_regime?.cb_hhi_13w || [])
        .map((v, i) => ({
            time: dashboardData.dates?.[i],
            value: v,
        }))
        .filter((d) => d.time && d.value !== null);

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

    // Lookup functions to get current data for a bank
    function getDataForBank(id) {
        const dataMap = {
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
        return dataMap[id] || [];
    }

    function getRangeForBank(id) {
        const rangeMap = {
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
        return rangeMap[id] || "ALL";
    }

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

<div class="dashboard-grid no-margin">
    {#each bankConfigs as item}
        <div class="chart-card">
            <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={getRangeForBank(item.id)}
                        onRangeChange={(r) => setRangeForBank(item.id, r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate(item.bank)}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.gli_cb ||
                    "Individual central bank assets in USD."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={getDataForBank(item.id)} />
            </div>
        </div>

        {#if item.bank === "FED"}
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
                        ? "Porcentaje de bancos centrales con balance en expansión (13 semanas). ↑ Alcista."
                        : "Percentage of central banks with expanding balance sheets (13-week basis). ↑ Bullish."}
                </p>
                <div class="chart-content">
                    <LightweightChart {darkMode} data={cbBreadthData} />
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
                        ? "Concentración de flujos (Indice HHI). Valores altos indican que pocos bancos mueven la liquidez global."
                        : "Concentration of flows (HHI Index). High values indicate few banks are driving global liquidity."}
                </p>
                <div class="chart-content">
                    <LightweightChart {darkMode} data={cbConcentrationData} />
                </div>
            </div>
        {/if}
    {/each}
</div>
