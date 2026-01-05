<script>
    /**
     * GlobalM2Tab.svelte
     * Displays Global M2 Money Supply charts with aggregate and per-country views.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { filterPlotlyData } from "../utils/helpers.js";

    // Core props only
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Local state for time ranges
    let m2Range = "ALL";
    let usM2DataRange = "ALL";
    let euM2DataRange = "ALL";
    let cnM2DataRange = "ALL";
    let jpM2DataRange = "ALL";
    let ukM2DataRange = "ALL";
    let caM2DataRange = "ALL";
    let auM2DataRange = "ALL";
    let inM2DataRange = "ALL";
    let chM2DataRange = "ALL";
    let ruM2DataRange = "ALL";
    let brM2DataRange = "ALL";
    let krM2DataRange = "ALL";
    let mxM2DataRange = "ALL";
    let myM2DataRange = "ALL";

    // Card container references for full-card download feature
    let m2AggregateCard;

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

    // M2 Total (Aggregate)
    $: m2TotalData = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.total,
                name: translations.chart_m2_aggregate || "Global M2 Total",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        m2Range,
    );

    // M2 Weights (computed internally)
    $: m2Weights = Object.entries(dashboardData.m2_weights || {})
        .map(([id, weight]) => {
            const rocs = dashboardData.m2_bank_rocs?.[id] || {};
            return {
                id,
                name: id.toUpperCase(),
                weight,
                isLiability: false,
                m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
                m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
                m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
                y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
                imp1: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
                imp3: rocs["impact_3m"]?.[rocs["impact_3m"].length - 1] || 0,
                imp1y: rocs["impact_1y"]?.[rocs["impact_1y"].length - 1] || 0,
            };
        })
        .sort((a, b) => b.weight - a.weight);

    // Country M2 Data (each computed reactively)
    $: usM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.us,
                name: "US M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        usM2DataRange,
    );
    $: euM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.eu,
                name: "EU M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        euM2DataRange,
    );
    $: cnM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.cn,
                name: "China M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        cnM2DataRange,
    );
    $: jpM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.jp,
                name: "Japan M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#f43f5e", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        jpM2DataRange,
    );
    $: ukM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.uk,
                name: "UK M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        ukM2DataRange,
    );
    $: caM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.ca,
                name: "Canada M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        caM2DataRange,
    );
    $: auM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.au,
                name: "Australia M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        auM2DataRange,
    );
    $: inM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.in,
                name: "India M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        inM2DataRange,
    );
    $: chM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.ch,
                name: "Switzerland M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#0ea5e9", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        chM2DataRange,
    );
    $: ruM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.ru,
                name: "Russia M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        ruM2DataRange,
    );
    $: brM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.br,
                name: "Brazil M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        brM2DataRange,
    );
    $: krM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.kr,
                name: "South Korea M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        krM2DataRange,
    );
    $: mxM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.mx,
                name: "Mexico M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        mxM2DataRange,
    );
    $: myM2Data = filterPlotlyData(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.m2?.my,
                name: "Malaysia M2",
                type: "scatter",
                mode: "lines",
                line: { color: "#6366f1", width: 3, shape: "spline" },
            },
        ],
        dashboardData.dates,
        myM2DataRange,
    );

    // Country configuration - STATIC (not reactive) to avoid cyclical dependency
    // The template will lookup data/range using getDataForCountry and getRangeForCountry
    const countryConfigs = [
        {
            id: "us",
            name: translations.indicator_us_m2 || "US M2",
            color: "#3b82f6",
            bank: "FED",
        },
        {
            id: "eu",
            name: translations.indicator_eu_m2 || "EU M2",
            color: "#8b5cf6",
            bank: "ECB",
        },
        {
            id: "cn",
            name: translations.indicator_cn_m2 || "China M2",
            color: "#10b981",
            bank: "PBOC",
        },
        {
            id: "jp",
            name: translations.indicator_jp_m2 || "Japan M2",
            color: "#f43f5e",
            bank: "BOJ",
        },
        {
            id: "uk",
            name: translations.indicator_uk_m2 || "UK M2",
            color: "#f59e0b",
            bank: "BOE",
        },
        {
            id: "ca",
            name: translations.indicator_ca_m2 || "Canada M2",
            color: "#ef4444",
            bank: "BOC",
        },
        {
            id: "au",
            name: translations.indicator_au_m2 || "Australia M2",
            color: "#3b82f6",
            bank: "RBA",
        },
        {
            id: "in",
            name: translations.indicator_in_m2 || "India M2",
            color: "#6366f1",
            bank: "RBI",
        },
        {
            id: "ch",
            name: translations.indicator_ch_m2 || "Switzerland M2",
            color: "#0ea5e9",
            bank: "SNB",
        },
        {
            id: "ru",
            name: translations.indicator_ru_m2 || "Russia M2",
            color: "#22c55e",
            bank: "CBR",
        },
        {
            id: "br",
            name: translations.indicator_br_m2 || "Brazil M2",
            color: "#f59e0b",
            bank: "BCB",
        },
        {
            id: "kr",
            name: translations.indicator_kr_m2 || "South Korea M2",
            color: "#8b5cf6",
            bank: "BOK",
        },
        {
            id: "mx",
            name: translations.indicator_mx_m2 || "Mexico M2",
            color: "#10b981",
            bank: "MX",
        },
        {
            id: "my",
            name: translations.indicator_my_m2 || "Malaysia M2",
            color: "#6366f1",
            bank: "BNM",
        },
    ];
    // REACTIVE data and ranges map - Svelte tracks these objects for reactivity
    // When a range changes, the corresponding data is recomputed
    $: countryRanges = {
        us: usM2DataRange,
        eu: euM2DataRange,
        cn: cnM2DataRange,
        jp: jpM2DataRange,
        uk: ukM2DataRange,
        ca: caM2DataRange,
        au: auM2DataRange,
        in: inM2DataRange,
        ch: chM2DataRange,
        ru: ruM2DataRange,
        br: brM2DataRange,
        kr: krM2DataRange,
        mx: mxM2DataRange,
        my: myM2DataRange,
    };

    $: countryChartData = {
        us: usM2Data,
        eu: euM2Data,
        cn: cnM2Data,
        jp: jpM2Data,
        uk: ukM2Data,
        ca: caM2Data,
        au: auM2Data,
        in: inM2Data,
        ch: chM2Data,
        ru: ruM2Data,
        br: brM2Data,
        kr: krM2Data,
        mx: mxM2Data,
        my: myM2Data,
    };

    function setRangeForCountry(id, r) {
        if (id === "us") usM2DataRange = r;
        else if (id === "eu") euM2DataRange = r;
        else if (id === "cn") cnM2DataRange = r;
        else if (id === "jp") jpM2DataRange = r;
        else if (id === "uk") ukM2DataRange = r;
        else if (id === "ca") caM2DataRange = r;
        else if (id === "au") auM2DataRange = r;
        else if (id === "in") inM2DataRange = r;
        else if (id === "ch") chM2DataRange = r;
        else if (id === "ru") ruM2DataRange = r;
        else if (id === "br") brM2DataRange = r;
        else if (id === "kr") krM2DataRange = r;
        else if (id === "mx") mxM2DataRange = r;
        else if (id === "my") myM2DataRange = r;
    }

    // M2 ROC helper for indicators
    function getM2Rocs(countryId) {
        const rocs = dashboardData.m2_bank_rocs?.[countryId] || {};
        const getLatest = (arr) => arr?.[arr?.length - 1] ?? null;
        return {
            w1: getLatest(rocs["1W"]),
            m1: getLatest(rocs["1M"]),
            m3: getLatest(rocs["3M"]),
            m6: getLatest(rocs["6M"]),
        };
    }

    // M2 Total ROC helper for aggregate indicator
    function getM2TotalRocs() {
        const rocs = dashboardData.m2?.rocs || {};
        const getLatest = (arr) => arr?.[arr?.length - 1] ?? null;
        return {
            m1: getLatest(rocs["1M"]),
            m3: getLatest(rocs["3M"]),
            m6: getLatest(rocs["6M"]),
            y1: getLatest(rocs["1Y"]),
        };
    }
</script>

<div class="main-charts">
    <div class="country-grid">
        <!-- Aggregate M2 Chart with Weights Table -->
        <div class="chart-card wide" bind:this={m2AggregateCard}>
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
                        {translations.m2_global ||
                            "Global money supply in USD."}
                    </p>
                    <div class="chart-content">
                        <Chart
                            {darkMode}
                            data={m2TotalData}
                            cardContainer={m2AggregateCard}
                            cardTitle="global_m2_aggregate"
                        />
                    </div>

                    <!-- Aggregate ROC Indicators -->
                    {#if dashboardData.m2?.rocs}
                        {@const totalRocs = getM2TotalRocs()}
                        <div class="roc-bar">
                            <div
                                class="roc-item"
                                class:positive={totalRocs.m1 > 0}
                                class:negative={totalRocs.m1 < 0}
                            >
                                <span class="roc-label"
                                    >{translations.val_1m || "1M"}</span
                                >
                                <span class="roc-value"
                                    >{totalRocs.m1 !== null
                                        ? totalRocs.m1.toFixed(1) + "%"
                                        : translations.na || "N/A"}</span
                                >
                            </div>
                            <div
                                class="roc-item"
                                class:positive={totalRocs.m3 > 0}
                                class:negative={totalRocs.m3 < 0}
                            >
                                <span class="roc-label"
                                    >{translations.val_3m || "3M"}</span
                                >
                                <span class="roc-value"
                                    >{totalRocs.m3 !== null
                                        ? totalRocs.m3.toFixed(1) + "%"
                                        : translations.na || "N/A"}</span
                                >
                            </div>
                            <div
                                class="roc-item"
                                class:positive={totalRocs.m6 > 0}
                                class:negative={totalRocs.m6 < 0}
                            >
                                <span class="roc-label"
                                    >{translations.val_6m || "6M"}</span
                                >
                                <span class="roc-value"
                                    >{totalRocs.m6 !== null
                                        ? totalRocs.m6.toFixed(1) + "%"
                                        : translations.na || "N/A"}</span
                                >
                            </div>
                            <div
                                class="roc-item"
                                class:positive={totalRocs.y1 > 0}
                                class:negative={totalRocs.y1 < 0}
                            >
                                <span class="roc-label"
                                    >{translations.val_1y || "1Y"}</span
                                >
                                <span class="roc-value"
                                    >{totalRocs.y1 !== null
                                        ? totalRocs.y1.toFixed(1) + "%"
                                        : translations.na || "N/A"}</span
                                >
                            </div>
                        </div>
                    {/if}
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
                                        <th
                                            >{translations.economy_col ||
                                                "Economy"}</th
                                        >
                                        <th>{translations.wgt_col || "Wgt"}</th>
                                        <th>{translations.val_1m || "1M"}</th>
                                        <th
                                            title={translations.impact_1m ||
                                                "1M Global Impact"}
                                            >{translations.imp_col || "Imp"}</th
                                        >
                                        <th>{translations.val_3m || "3M"}</th>
                                        <th
                                            title={translations.impact_3m ||
                                                "3M Global Impact"}
                                            >{translations.imp_col || "Imp"}</th
                                        >
                                        <th>{translations.val_1y || "1Y"}</th>
                                        <th
                                            title={translations.impact_1y ||
                                                "1Y Global Impact"}
                                            >{translations.imp_col || "Imp"}</th
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
                            * {translations.impact_note_m2 ||
                                "Impact = % contribution of local M2 1M move to total Global M2."}
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Individual Country M2 Charts in 2-column grid -->
        {#each countryConfigs as item}
            {@const rocs = getM2Rocs(item.id)}
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{item.name}</h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={countryRanges[item.id]}
                            onRangeChange={(r) =>
                                setRangeForCountry(item.id, r)}
                        />
                        <span class="last-date">{getLastDate(item.bank)}</span>
                    </div>
                </div>
                <div class="chart-content short">
                    <Chart {darkMode} data={countryChartData[item.id]} />
                </div>
                <!-- ROC Indicators -->
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
        {/each}
    </div>
</div>

<style>
    .main-charts {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 24px;
    }

    .country-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        box-shadow: var(--card-shadow);
    }

    .chart-card.wide {
        grid-column: span 2;
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
        min-height: 400px;
        height: 400px;
    }

    .chart-content.short {
        min-height: 320px;
        height: 320px;
    }

    .gli-layout {
        display: flex;
        gap: 24px;
    }

    .chart-main {
        flex: 2;
        min-width: 0;
    }

    .metrics-sidebar {
        flex: 1;
        min-width: 300px;
        max-width: 400px;
    }

    .metrics-section {
        background: var(--bg-tertiary);
        border-radius: 12px;
        padding: 16px;
    }

    .metrics-section h4 {
        margin: 0 0 12px 0;
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .metrics-table-container {
        max-height: 350px;
        overflow-y: auto;
    }

    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.75rem;
    }

    .metrics-table th,
    .metrics-table td {
        padding: 6px 8px;
        text-align: right;
        border-bottom: 1px solid var(--border-color);
    }

    .metrics-table th:first-child,
    .metrics-table td:first-child {
        text-align: left;
    }

    .metrics-table th {
        font-weight: 600;
        color: var(--text-secondary);
        background: var(--bg-secondary);
        position: sticky;
        top: 0;
    }

    .impact-cell {
        font-size: 0.65rem;
        opacity: 0.8;
    }

    .roc-val.positive {
        color: #10b981;
    }
    .roc-val.negative {
        color: #ef4444;
    }

    /* ROC Indicator Bar */
    .roc-bar {
        display: flex;
        justify-content: space-around;
        margin-top: 20px;
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
        .gli-layout {
            flex-direction: column;
        }
        .metrics-sidebar {
            max-width: 100%;
        }
        .country-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
