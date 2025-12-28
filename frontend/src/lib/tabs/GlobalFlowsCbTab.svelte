<script>
    /**
     * GlobalFlowsCbTab.svelte
     * Displays individual central bank balance sheet charts with time range controls.
     */
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let language = "en";
    export let translations = {};

    // Central Bank data arrays
    export let fedData = [];
    export let ecbData = [];
    export let bojData = [];
    export let boeData = [];
    export let pbocData = [];
    export let bocData = [];
    export let rbaData = [];
    export let snbData = [];
    export let bokData = [];
    export let rbiData = [];
    export let cbrData = [];
    export let bcbData = [];
    export let rbnzData = [];
    export let srData = [];
    export let bnmData = [];

    // CB Breadth and Concentration data
    export let cbBreadthData = [];
    export let cbConcentrationData = [];

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";

    // Time range states - managed locally for this tab
    export let fedRange = "ALL";
    export let ecbRange = "ALL";
    export let bojRange = "ALL";
    export let boeRange = "ALL";
    export let pbocRange = "ALL";
    export let bocRange = "ALL";
    export let rbaRange = "ALL";
    export let snbRange = "ALL";
    export let bokRange = "ALL";
    export let rbiRange = "ALL";
    export let cbrRange = "ALL";
    export let bcbRange = "ALL";
    export let rbnzRange = "ALL";
    export let srRange = "ALL";
    export let bnmRange = "ALL";
    export let cbRange = "ALL";

    // Bank configuration
    $: banks = [
        {
            name: "Federal Reserve (Fed)",
            data: fedData,
            range: fedRange,
            setRange: (r) => (fedRange = r),
            bank: "FED",
        },
        {
            name: "European Central Bank (ECB)",
            data: ecbData,
            range: ecbRange,
            setRange: (r) => (ecbRange = r),
            bank: "ECB",
        },
        {
            name: "Bank of Japan (BoJ)",
            data: bojData,
            range: bojRange,
            setRange: (r) => (bojRange = r),
            bank: "BOJ",
        },
        {
            name: "Bank of England (BoE)",
            data: boeData,
            range: boeRange,
            setRange: (r) => (boeRange = r),
            bank: "BOE",
        },
        {
            name: "People's Bank of China (PBoC)",
            data: pbocData,
            range: pbocRange,
            setRange: (r) => (pbocRange = r),
            bank: "PBOC",
        },
        {
            name: "Bank of Canada (BoC)",
            data: bocData,
            range: bocRange,
            setRange: (r) => (bocRange = r),
            bank: "BOC",
        },
        {
            name: "Reserve Bank of Australia (RBA)",
            data: rbaData,
            range: rbaRange,
            setRange: (r) => (rbaRange = r),
            bank: "RBA",
        },
        {
            name: "Swiss National Bank (SNB)",
            data: snbData,
            range: snbRange,
            setRange: (r) => (snbRange = r),
            bank: "SNB",
        },
        {
            name: "Bank of Korea (BoK)",
            data: bokData,
            range: bokRange,
            setRange: (r) => (bokRange = r),
            bank: "BOK",
        },
        {
            name: "Reserve Bank of India (RBI)",
            data: rbiData,
            range: rbiRange,
            setRange: (r) => (rbiRange = r),
            bank: "RBI",
        },
        {
            name: "Central Bank of Russia (CBR)",
            data: cbrData,
            range: cbrRange,
            setRange: (r) => (cbrRange = r),
            bank: "CBR",
        },
        {
            name: "Central Bank of Brazil (BCB)",
            data: bcbData,
            range: bcbRange,
            setRange: (r) => (bcbRange = r),
            bank: "BCB",
        },
        {
            name: "Reserve Bank of New Zealand (RBNZ)",
            data: rbnzData,
            range: rbnzRange,
            setRange: (r) => (rbnzRange = r),
            bank: "RBNZ",
        },
        {
            name: "Sveriges Riksbank (SR)",
            data: srData,
            range: srRange,
            setRange: (r) => (srRange = r),
            bank: "SR",
        },
        {
            name: "Bank Negara Malaysia (BNM)",
            data: bnmData,
            range: bnmRange,
            setRange: (r) => (bnmRange = r),
            bank: "BNM",
        },
    ];
</script>

<div class="dashboard-grid no-margin">
    {#each banks as item}
        <div class="chart-card">
            <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={item.range}
                        onRangeChange={item.setRange}
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
                <Chart {darkMode} data={item.data} />
            </div>
        </div>

        {#if item.bank === "FED"}
            <!-- CB Breadth Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3>Central Bank Breadth (% Expanding)</h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={cbRange}
                            onRangeChange={(r) => (cbRange = r)}
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
                            selectedRange={cbRange}
                            onRangeChange={(r) => (cbRange = r)}
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
