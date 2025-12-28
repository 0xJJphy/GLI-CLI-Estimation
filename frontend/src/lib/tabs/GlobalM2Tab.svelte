<script>
    /**
     * GlobalM2Tab.svelte
     * Displays Global M2 Money Supply charts with aggregate and per-country views.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let translations = {};

    // Main M2 data
    export let m2TotalData = [];
    export let m2Weights = [];

    // Individual country M2 data
    export let usM2Data = [];
    export let euM2Data = [];
    export let cnM2Data = [];
    export let jpM2Data = [];
    export let ukM2Data = [];
    export let caM2Data = [];
    export let auM2Data = [];
    export let inM2Data = [];
    export let chM2Data = [];
    export let ruM2Data = [];
    export let brM2Data = [];
    export let krM2Data = [];
    export let mxM2Data = [];
    export let myM2Data = [];

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";

    // Time range states - managed locally
    export let m2Range = "ALL";
    export let usM2DataRange = "ALL";
    export let euM2DataRange = "ALL";
    export let cnM2DataRange = "ALL";
    export let jpM2DataRange = "ALL";
    export let ukM2DataRange = "ALL";
    export let caM2DataRange = "ALL";
    export let auM2DataRange = "ALL";
    export let inM2DataRange = "ALL";
    export let chM2DataRange = "ALL";
    export let ruM2DataRange = "ALL";
    export let brM2DataRange = "ALL";
    export let krM2DataRange = "ALL";
    export let mxM2DataRange = "ALL";
    export let myM2DataRange = "ALL";

    // Country M2 configuration
    $: countries = [
        {
            id: "us",
            name: "US M2",
            data: usM2Data,
            range: usM2DataRange,
            setRange: (r) => (usM2DataRange = r),
            bank: "FED",
        },
        {
            id: "eu",
            name: "EU M2",
            data: euM2Data,
            range: euM2DataRange,
            setRange: (r) => (euM2DataRange = r),
            bank: "ECB",
        },
        {
            id: "cn",
            name: "China M2",
            data: cnM2Data,
            range: cnM2DataRange,
            setRange: (r) => (cnM2DataRange = r),
            bank: "PBOC",
        },
        {
            id: "jp",
            name: "Japan M2",
            data: jpM2Data,
            range: jpM2DataRange,
            setRange: (r) => (jpM2DataRange = r),
            bank: "BOJ",
        },
        {
            id: "uk",
            name: "UK M2",
            data: ukM2Data,
            range: ukM2DataRange,
            setRange: (r) => (ukM2DataRange = r),
            bank: "BOE",
        },
        {
            id: "ca",
            name: "Canada M2",
            data: caM2Data,
            range: caM2DataRange,
            setRange: (r) => (caM2DataRange = r),
            bank: "BOC",
        },
        {
            id: "au",
            name: "Australia M2",
            data: auM2Data,
            range: auM2DataRange,
            setRange: (r) => (auM2DataRange = r),
            bank: "RBA",
        },
        {
            id: "in",
            name: "India M2",
            data: inM2Data,
            range: inM2DataRange,
            setRange: (r) => (inM2DataRange = r),
            bank: "RBI",
        },
        {
            id: "ch",
            name: "Switzerland M2",
            data: chM2Data,
            range: chM2DataRange,
            setRange: (r) => (chM2DataRange = r),
            bank: "SNB",
        },
        {
            id: "ru",
            name: "Russia M2",
            data: ruM2Data,
            range: ruM2DataRange,
            setRange: (r) => (ruM2DataRange = r),
            bank: "CBR",
        },
        {
            id: "br",
            name: "Brazil M2",
            data: brM2Data,
            range: brM2DataRange,
            setRange: (r) => (brM2DataRange = r),
            bank: "BCB",
        },
        {
            id: "kr",
            name: "South Korea M2",
            data: krM2Data,
            range: krM2DataRange,
            setRange: (r) => (krM2DataRange = r),
            bank: "BOK",
        },
        {
            id: "mx",
            name: "Mexico M2",
            data: mxM2Data,
            range: mxM2DataRange,
            setRange: (r) => (mxM2DataRange = r),
            bank: "MX",
        },
        {
            id: "my",
            name: "Malaysia M2",
            data: myM2Data,
            range: myM2DataRange,
            setRange: (r) => (myM2DataRange = r),
            bank: "BNM",
        },
    ];
</script>

<div class="main-charts">
    <!-- Aggregate M2 Chart with Weights Table -->
    <div class="chart-card wide">
        <div class="gli-layout">
            <div class="chart-main">
                <div class="chart-header">
                    <h3>
                        {translations.chart_m2_aggregate ||
                            "Global M2 Money Supply (Aggregate)"}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={m2Range}
                            onRangeChange={(r) => (m2Range = r)}
                        />
                        <span class="last-date"
                            >{translations.last || "Last:"}
                            {getLastDate("M2_TOTAL")}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations.m2_global || "Global money supply in USD."}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={m2TotalData} />
                </div>
            </div>

            <div class="metrics-sidebar">
                <div class="metrics-section">
                    <h4>
                        {translations.chart_m2_comp ||
                            "M2 Composition & Performance"}
                    </h4>
                    <div class="metrics-table-container">
                        <table class="metrics-table">
                            <thead>
                                <tr>
                                    <th>Economy</th>
                                    <th>Wgt</th>
                                    <th>1M</th>
                                    <th
                                        title={translations.impact_1m ||
                                            "1M Global Impact"}>Imp</th
                                    >
                                    <th>3M</th>
                                    <th
                                        title={translations.impact_3m ||
                                            "3M Global Impact"}>Imp</th
                                    >
                                    <th>1Y</th>
                                    <th
                                        title={translations.impact_1y ||
                                            "1Y Global Impact"}>Imp</th
                                    >
                                </tr>
                            </thead>
                            <tbody>
                                {#each m2Weights.slice(0, 10) as item}
                                    <tr>
                                        <td>{item.name}</td>
                                        <td>{item.weight.toFixed(0)}%</td>
                                        <td
                                            class="roc-val"
                                            class:positive={(!item.isLiability &&
                                                item.m1 > 0) ||
                                                (item.isLiability &&
                                                    item.m1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m1 < 0) ||
                                                (item.isLiability &&
                                                    item.m1 > 0)}
                                            >{item.m1.toFixed(1)}%</td
                                        >
                                        <td
                                            class="roc-val impact-cell"
                                            class:positive={item.imp1 > 0}
                                            class:negative={item.imp1 < 0}
                                            >{item.imp1.toFixed(2)}%</td
                                        >
                                        <td
                                            class="roc-val"
                                            class:positive={(!item.isLiability &&
                                                item.m3 > 0) ||
                                                (item.isLiability &&
                                                    item.m3 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.m3 < 0) ||
                                                (item.isLiability &&
                                                    item.m3 > 0)}
                                            >{item.m3.toFixed(1)}%</td
                                        >
                                        <td
                                            class="roc-val impact-cell"
                                            class:positive={item.imp3 > 0}
                                            class:negative={item.imp3 < 0}
                                            >{item.imp3.toFixed(2)}%</td
                                        >
                                        <td
                                            class="roc-val"
                                            class:positive={(!item.isLiability &&
                                                item.y1 > 0) ||
                                                (item.isLiability &&
                                                    item.y1 < 0)}
                                            class:negative={(!item.isLiability &&
                                                item.y1 < 0) ||
                                                (item.isLiability &&
                                                    item.y1 > 0)}
                                            >{item.y1.toFixed(1)}%</td
                                        >
                                        <td
                                            class="roc-val impact-cell"
                                            class:positive={item.imp1y > 0}
                                            class:negative={item.imp1y < 0}
                                            >{item.imp1y.toFixed(2)}%</td
                                        >
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                    <p
                        style="font-size: 10px; color: #94a3b8; margin-top: 8px;"
                    >
                        * Impact = % contribution of local M2 1M move to total
                        Global M2.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Individual Country M2 Charts -->
    {#each countries as item}
        <div class="chart-card">
            <div class="chart-header">
                <h3>{item.name}</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={item.range}
                        onRangeChange={item.setRange}
                    />
                    <span class="last-date">Last: {getLastDate(item.bank)}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.m2_country || "Country M2 money supply in USD."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={item.data} />
            </div>
        </div>
    {/each}
</div>
