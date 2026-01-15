<script>
    import Chart from "./Chart.svelte";
    import TimeRangeSelector from "./TimeRangeSelector.svelte";
    import { filterWithCache, getLatestValue } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    export let dashboardData = {};
    export let rangeIndicesCache = {};
    export let translations = {};
    export let darkMode = false;

    // Local State
    let repoStressRange = "1Y";
    let sofrVolumeRange = "ALL";
    let sofrVolumeViewMode = "raw";

    let repoCorridorCard;
    let sofrVolumeCard;

    // Repo Corridor Processing
    $: repoStressData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.srf_rate || [],
                name: translations.repo_srf_ceiling || "SRF Rate (Ceiling)",
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 1.5, dash: "dash" },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr || [],
                name: "SOFR",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2.5 },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.iorb || [],
                name: translations.repo_iorb_floor || "IORB (Floor)",
                type: "scatter",
                mode: "lines",
                line: { color: "#22c55e", width: 1.5, dash: "dash" },
            },
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.rrp_award || [],
                name: "RRP Award",
                type: "scatter",
                mode: "lines",
                line: { color: "#8b5cf6", width: 1.5, dash: "dot" },
            },
        ],
        dashboardData.dates,
        repoStressRange,
        rangeIndicesCache,
    );

    $: srfUsageBar = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.srf_usage || [],
                name: "SRF Usage ($B)",
                type: "bar",
                marker: { color: "rgba(239, 68, 68, 0.4)" },
                yaxis: "y2",
            },
        ],
        dashboardData.dates,
        repoStressRange,
        rangeIndicesCache,
    );

    $: repoFusedData = [...repoStressData, ...srfUsageBar];

    $: repoFusedLayout = {
        yaxis: { title: "Rate (%)", domain: [0.28, 1], tickformat: ".2f" },
        yaxis2: {
            title: "SRF ($B)",
            domain: [0, 0.2],
            anchor: "x",
            rangemode: "tozero",
        },
        margin: { t: 10, r: 20, b: 30, l: 50 },
        showlegend: true,
        height: 500,
    };

    // Metrics for Repo Corridor
    $: latestSofr = getLatestValue(dashboardData.repo_stress?.sofr);
    $: latestIorb = getLatestValue(dashboardData.repo_stress?.iorb);
    $: latestSrf = getLatestValue(dashboardData.repo_stress?.srf_rate);
    $: latestRrp = getLatestValue(dashboardData.repo_stress?.rrp_award);
    $: latestSrfUsage = getLatestValue(dashboardData.repo_stress?.srf_usage);
    $: latestSofrToFloor = (latestSofr - latestIorb) * 100;
    $: latestSofrToCeiling = (latestSrf - latestSofr) * 100;

    $: corridorStressLevel = (() => {
        if (latestSrfUsage > 1 || latestSofrToCeiling < 5) return "HIGH";
        if (latestSofrToFloor > 5 || latestSofrToCeiling < 10)
            return "ELEVATED";
        return "NORMAL";
    })();

    $: corridorStressColor =
        corridorStressLevel === "HIGH"
            ? "#ef4444"
            : corridorStressLevel === "ELEVATED"
              ? "#f59e0b"
              : "#22c55e";

    // SOFR Volume Processing
    $: sofrVolumeData = filterWithCache(
        [
            {
                x: dashboardData.dates,
                y: dashboardData.repo_stress?.sofr_volume || [],
                name: "SOFR Volume ($B)",
                type: "scatter",
                mode: "lines",
                line: { color: "#06b6d4", width: 2 },
                fill: "tozeroy",
                fillcolor: "rgba(6, 182, 212, 0.1)",
            },
        ],
        dashboardData.dates,
        sofrVolumeRange,
        rangeIndicesCache,
    );

    // Helper for status label
    function getStatusLabel(state) {
        if (!state) return translations.status_neutral || "NEUTRAL";
        const key = `status_${state.toLowerCase()}`;
        return translations[key] || state.toUpperCase();
    }
</script>

<div class="grid-2">
    <!-- Fed Rate Corridor Chart -->
    <div class="chart-card wide" bind:this={repoCorridorCard}>
        <div class="chart-header">
            <div class="title-group">
                <h3>
                    {translations.chart_repo_corridor ||
                        "Fed Rate Corridor (Liquidity Stress)"}
                </h3>
                <div
                    class="stress-badge"
                    style="background: {corridorStressColor}20; color: {corridorStressColor}"
                >
                    {corridorStressLevel}
                </div>
            </div>
            <div class="header-controls">
                <button
                    class="download-card-btn"
                    on:click={() =>
                        downloadCardAsImage(repoCorridorCard, "repo_corridor")}
                    >📷</button
                >
                <TimeRangeSelector
                    selectedRange={repoStressRange}
                    onRangeChange={(r) => (repoStressRange = r)}
                />
            </div>
        </div>

        <p class="chart-description">
            {translations.repo_corridor_desc ||
                "SOFR should trade between IORB (floor) and SRF Rate (ceiling). Approaching ceiling or SRF usage signals funding stress."}
        </p>

        <div class="chart-content" style="height: 500px;">
            <Chart
                {darkMode}
                data={repoFusedData}
                layout={repoFusedLayout}
                cardContainer={repoCorridorCard}
                cardTitle="fed_rate_corridor"
            />
        </div>

        <div class="metrics-section repo-metrics">
            <div class="metric-group">
                <div class="metric-sub-box">
                    <span class="label">SOFR-IORB Spread</span>
                    <span class="value" style="color: {corridorStressColor}"
                        >{latestSofrToFloor.toFixed(1)} bps</span
                    >
                </div>
                {#if latestSrfUsage > 0}
                    <div class="metric-sub-box stress">
                        <span class="label">⚠️ SRF Usage</span>
                        <span class="value">${latestSrfUsage.toFixed(1)}B</span>
                    </div>
                {/if}
            </div>
            <table class="metrics-table compact">
                <thead>
                    <tr>
                        <th>Rate</th>
                        <th>Value</th>
                        <th>Signal</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="color: #ef4444">SRF (Ceiling)</td>
                        <td>{latestSrf.toFixed(2)}%</td>
                        <td rowspan="4" class="status-cell">
                            <div
                                class="status-indicator"
                                style="color: {corridorStressColor}"
                            >
                                {#if corridorStressLevel === "NORMAL"}
                                    ✅ OK
                                {:else if corridorStressLevel === "ELEVATED"}
                                    ⚠️ ELEVATED
                                {:else}
                                    🚨 STRESS
                                {/if}
                            </div>
                        </td>
                    </tr>
                    <tr
                        ><td style="color: #3b82f6">SOFR</td><td
                            >{latestSofr.toFixed(2)}%</td
                        ></tr
                    >
                    <tr
                        ><td style="color: #22c55e">IORB (Floor)</td><td
                            >{latestIorb.toFixed(2)}%</td
                        ></tr
                    >
                    <tr
                        ><td style="color: #8b5cf6">RRP Award</td><td
                            >{latestRrp.toFixed(2)}%</td
                        ></tr
                    >
                </tbody>
            </table>
        </div>
    </div>

    <!-- SOFR Volume Chart -->
    <div class="chart-card" bind:this={sofrVolumeCard}>
        <div class="chart-header">
            <h3>
                {translations.chart_sofr_volume ||
                    "Repo Market Depth (SOFR Volume)"}
            </h3>
            <div class="header-controls">
                <button
                    class="download-card-btn"
                    on:click={() =>
                        downloadCardAsImage(sofrVolumeCard, "sofr_volume")}
                    >📷</button
                >
                <TimeRangeSelector
                    selectedRange={sofrVolumeRange}
                    onRangeChange={(r) => (sofrVolumeRange = r)}
                />
            </div>
        </div>
        <p class="chart-description">
            {translations.sofr_volume_desc ||
                "SOFR transaction volume measures repo market depth. Falling volume = early warning of dysfunction."}
        </p>
        <div class="chart-content" style="height: 300px;">
            <Chart
                {darkMode}
                data={sofrVolumeData}
                layout={{ yaxis: { title: "SOFR Volume ($B)" } }}
            />
        </div>
        <div class="metrics-section">
            <div class="signal-item">
                <span class="signal-label">Latest Volume</span>
                <span class="signal-value"
                    ><b
                        >${getLatestValue(
                            dashboardData.repo_stress?.sofr_volume,
                        ).toFixed(1)}B</b
                    ></span
                >
                <span class="signal-status">
                    {#if getLatestValue(dashboardData.repo_stress?.sofr_volume) > 1000}
                        ✅ DEEP
                    {:else if getLatestValue(dashboardData.repo_stress?.sofr_volume) > 500}
                        🔶 MODERATE
                    {:else}
                        ⚠️ THIN
                    {/if}
                </span>
            </div>
        </div>
    </div>
</div>

<style>
    .grid-2 {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
        margin-top: 24px;
    }

    .chart-card.wide {
        grid-column: span 2;
    }

    .title-group {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .stress-badge {
        font-size: 10px;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 4px;
        letter-spacing: 0.5px;
    }

    .repo-metrics {
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 24px;
        align-items: center;
    }

    .metric-sub-box {
        display: flex;
        flex-direction: column;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 6px;
        margin-bottom: 8px;
    }

    .metric-sub-box.stress {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #ef4444;
    }

    .metric-sub-box .label {
        font-size: 11px;
        opacity: 0.7;
    }

    .metric-sub-box .value {
        font-size: 16px;
        font-weight: 700;
    }

    .metrics-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }

    .metrics-table th {
        text-align: left;
        opacity: 0.6;
        padding-bottom: 8px;
    }

    .metrics-table td {
        padding: 4px 0;
        font-weight: 600;
    }

    .status-cell {
        vertical-align: middle;
        text-align: center;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
    }

    .status-indicator {
        font-weight: 800;
        font-size: 14px;
    }

    @media (max-width: 1024px) {
        .grid-2,
        .chart-card.wide {
            grid-template-columns: 1fr;
            grid-column: span 1;
        }
        .repo-metrics {
            grid-template-columns: 1fr;
        }
    }
</style>
