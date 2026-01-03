<script>
    /**
     * UsDebtTab.svelte
     * Displays Treasury Maturity Tracker with stacked bar chart and metrics.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import TreasuryAuctionDemand from "../components/TreasuryAuctionDemand.svelte";

    // Props from App.svelte
    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Chart view mode: "stacked" or "line"
    let chartViewMode = "stacked";

    // Time range filter
    let selectedTimeRange = "1Y";
    const debtRanges = [
        { value: "1M", label: "1M" },
        { value: "3M", label: "3M" },
        { value: "6M", label: "6M" },
        { value: "1Y", label: "1Y" },
        { value: "2Y", label: "2Y" },
        { value: "3Y", label: "3Y" },
        { value: "4Y", label: "4Y" },
        { value: "5Y", label: "5Y" },
        { value: "ALL", label: "ALL" },
    ];

    const rangeToMonths = {
        "1M": 1,
        "3M": 3,
        "6M": 6,
        "1Y": 12,
        "2Y": 24,
        "3Y": 36,
        "4Y": 48,
        "5Y": 60,
        ALL: 120,
    };

    // --- Computed Data ---
    $: treasuryData = dashboardData.treasury_maturities || {
        schedule: {
            months: [],
            bills: [],
            notes: [],
            bonds: [],
            tips: [],
            frn: [],
            total: [],
        },
        metrics: {},
        monthly_table: [],
    };

    $: rawSchedule = treasuryData.schedule || {};
    $: metrics = treasuryData.metrics || {};
    $: rawMonthlyTable = treasuryData.monthly_table || [];

    // Reactive filtering based on time range
    $: currentMonths = rangeToMonths[selectedTimeRange] || 12;

    $: schedule = {
        months: (rawSchedule.months || []).slice(0, currentMonths),
        bills: (rawSchedule.bills || []).slice(0, currentMonths),
        notes: (rawSchedule.notes || []).slice(0, currentMonths),
        bonds: (rawSchedule.bonds || []).slice(0, currentMonths),
        tips: (rawSchedule.tips || []).slice(0, currentMonths),
        frn: (rawSchedule.frn || []).slice(0, currentMonths),
        total: (rawSchedule.total || []).slice(0, currentMonths),
    };

    $: monthlyTable = (rawMonthlyTable || []).slice(0, currentMonths);

    // Compute dynamic metrics based on the filtered schedule
    $: filteredMetrics = {
        // Peak maturity within selected range
        peak_month: (() => {
            const totals = schedule.total || [];
            const months = schedule.months || [];
            if (!totals.length) return null;
            const maxIdx = totals.indexOf(Math.max(...totals));
            return months[maxIdx] || null;
        })(),
        peak_amount: Math.max(...(schedule.total || [0])),
        // Bills outstanding in selected range
        bills_outstanding: (schedule.bills || []).reduce(
            (a, b) => a + (b || 0),
            0,
        ),
        // Total outstanding in selected range
        total_outstanding: (schedule.total || []).reduce(
            (a, b) => a + (b || 0),
            0,
        ),
        // Next N months refinancing (sum of all maturities in filtered range)
        refinancing_in_range: (schedule.total || []).reduce(
            (a, b) => a + (b || 0),
            0,
        ),
        // Forecast horizon (number of months in view)
        forecast_horizon: currentMonths,
    };

    // Format currency helper
    function formatCurrency(value, decimals = 2) {
        if (value === null || value === undefined) return "$0";
        if (value >= 1000) {
            return `$${(value / 1000).toFixed(decimals)}T`;
        }
        return `$${value.toFixed(decimals)}B`;
    }

    // Chart data for stacked bar chart
    $: stackedChartData = [
        {
            x: schedule.months || [],
            y: schedule.bills || [],
            name: translations.treasury_bills || "Treasury Bills",
            type: "bar",
            marker: { color: "#4ade80" }, // Green
        },
        {
            x: schedule.months || [],
            y: schedule.notes || [],
            name: translations.treasury_notes || "Treasury Notes",
            type: "bar",
            marker: { color: "#3b82f6" }, // Blue
        },
        {
            x: schedule.months || [],
            y: schedule.bonds || [],
            name: translations.treasury_bonds || "Treasury Bonds",
            type: "bar",
            marker: { color: "#8b5cf6" }, // Purple
        },
        {
            x: schedule.months || [],
            y: schedule.tips || [],
            name: "TIPS",
            type: "bar",
            marker: { color: "#f59e0b" }, // Orange
        },
        {
            x: schedule.months || [],
            y: schedule.frn || [],
            name: "FRN",
            type: "bar",
            marker: { color: "#ef4444" }, // Red
        },
    ];

    // Chart data for line view - separate lines for each security type
    $: lineChartData = [
        {
            x: schedule.months || [],
            y: schedule.bills || [],
            name: translations.treasury_bills || "Treasury Bills",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#4ade80", width: 2 }, // Green
            marker: { size: 4 },
        },
        {
            x: schedule.months || [],
            y: schedule.notes || [],
            name: translations.treasury_notes || "Treasury Notes",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#3b82f6", width: 2 }, // Blue
            marker: { size: 4 },
        },
        {
            x: schedule.months || [],
            y: schedule.bonds || [],
            name: translations.treasury_bonds || "Treasury Bonds",
            type: "scatter",
            mode: "lines+markers",
            line: { color: "#8b5cf6", width: 2 }, // Purple
            marker: { size: 4 },
        },
    ];

    $: chartData =
        chartViewMode === "stacked" ? stackedChartData : lineChartData;

    $: chartLayout = {
        barmode: chartViewMode === "stacked" ? "stack" : undefined,
        yaxis: {
            title: translations.amount_billions || "Amount ($ Billions)",
            gridcolor: darkMode ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)",
        },
        xaxis: {
            tickangle: -45,
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
        },
        legend: {
            orientation: "h",
            y: -0.2,
            x: 0.5,
            xanchor: "center",
        },
        margin: { l: 60, r: 20, t: 20, b: 80 },
        showlegend: true,
    };
</script>

<div class="us-debt-tab" class:dark={darkMode}>
    <!-- Header Section -->
    <div class="tab-header">
        <div class="header-left">
            <span class="header-icon">🏛️</span>
            <h2 class="header-title">
                {translations.treasury_maturity_tracker ||
                    "Treasury Maturity Tracker"}
            </h2>
            {#if !schedule.months?.length}
                <span class="demo-badge"
                    >{translations.demo_data || "DEMO DATA"}</span
                >
            {/if}
        </div>
        <div class="header-right">
            <div class="header-controls">
                <TimeRangeSelector
                    ranges={debtRanges}
                    bind:selectedRange={selectedTimeRange}
                />
            </div>
            <span class="source-link">
                {translations.source || "Source"}:
                <a
                    href="https://fiscaldata.treasury.gov"
                    target="_blank"
                    rel="noopener">FiscalData.Treasury.gov</a
                >
            </span>
        </div>
    </div>

    <!-- Metrics Cards -->
    <div class="metrics-grid">
        <div class="metric-card">
            <span class="metric-label"
                >{translations.peak_maturity_month ||
                    "Peak Maturity Month"}</span
            >
            <span class="metric-value cyan"
                >{filteredMetrics.peak_month || "N/A"}</span
            >
            <span class="metric-sub"
                >{translations.highest_refinancing ||
                    "Highest refinancing"}</span
            >
        </div>
        <div class="metric-card">
            <span class="metric-label"
                >{translations.peak_amount || "Peak Amount"}</span
            >
            <span class="metric-value green"
                >{formatCurrency(filteredMetrics.peak_amount)}</span
            >
            <span class="metric-sub"
                >{translations.single_month_max || "Single month maximum"}</span
            >
        </div>
        <div class="metric-card">
            <span class="metric-label"
                >{translations.bills_maturing || "Bills Maturing"}</span
            >
            <span class="metric-value green"
                >{formatCurrency(filteredMetrics.bills_outstanding)}</span
            >
            <span class="metric-sub"
                >{translations.in_selected_range || "In selected range"}</span
            >
        </div>
        <div class="metric-card">
            <span class="metric-label"
                >{translations.total_maturing || "Total Maturing"}</span
            >
            <span class="metric-value white"
                >{formatCurrency(filteredMetrics.total_outstanding)}</span
            >
            <span class="metric-sub"
                >{translations.in_selected_range || "In selected range"}</span
            >
        </div>
        <div class="metric-card">
            <span class="metric-label"
                >{translations.refinancing_in_range ||
                    "Refinancing in Range"}</span
            >
            <span class="metric-value orange"
                >{formatCurrency(filteredMetrics.refinancing_in_range)}</span
            >
            <span class="metric-sub"
                >{translations.must_be_rolled || "Must be rolled over"}</span
            >
        </div>
        <div class="metric-card">
            <span class="metric-label"
                >{translations.forecast_horizon || "Forecast Horizon"}</span
            >
            <span class="metric-value white"
                >{filteredMetrics.forecast_horizon || 0}
                {translations.months_abbr || "Mo"}</span
            >
            <span class="metric-sub"
                >{translations.projection_period || "Projection period"}</span
            >
        </div>
    </div>

    <!-- Maturity Schedule Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3 class="chart-title">
                {translations.maturity_schedule_title ||
                    "Maturity Schedule by Security Type"}
            </h3>
            <div class="chart-controls">
                <div class="view-toggle">
                    <button
                        class:active={chartViewMode === "stacked"}
                        on:click={() => (chartViewMode = "stacked")}
                    >
                        {translations.stacked || "Stacked"}
                    </button>
                    <button
                        class:active={chartViewMode === "line"}
                        on:click={() => (chartViewMode = "line")}
                    >
                        {translations.line || "Line"}
                    </button>
                </div>
            </div>
        </div>
        <div class="chart-content" style="height: 400px;">
            {#if schedule.months?.length > 0}
                <Chart {darkMode} data={chartData} layout={chartLayout} />
            {:else}
                <div class="no-data-placeholder">
                    <span>📊</span>
                    <p>
                        {translations.loading_treasury_data ||
                            "Loading treasury data..."}
                    </p>
                </div>
            {/if}
        </div>
    </div>

    <!-- Monthly Table -->
    <div class="table-card">
        <div class="table-header">
            <h3 class="table-title">
                {translations.monthly_maturity_schedule ||
                    "Monthly Maturity Schedule ($ Billions)"}
            </h3>
            <span class="table-updated">
                {translations.updated || "Updated"}: {metrics.record_date ||
                    "N/A"}
            </span>
        </div>
        <div class="table-content">
            <table>
                <thead>
                    <tr>
                        <th>{translations.month || "Month"}</th>
                        <th
                            >{translations.treasury_bills ||
                                "Treasury Bills"}</th
                        >
                        <th
                            >{translations.treasury_notes ||
                                "Treasury Notes"}</th
                        >
                        <th
                            >{translations.treasury_bonds ||
                                "Treasury Bonds"}</th
                        >
                        <th>{translations.total || "Total"}</th>
                    </tr>
                </thead>
                <tbody>
                    {#each monthlyTable as row}
                        <tr>
                            <td class="month-cell">{row.month}</td>
                            <td class="value-cell green"
                                >{formatCurrency(row.bills, 0)}</td
                            >
                            <td class="value-cell blue"
                                >{formatCurrency(row.notes, 0)}</td
                            >
                            <td class="value-cell purple"
                                >{formatCurrency(row.bonds, 0)}</td
                            >
                            <td class="value-cell total"
                                >{formatCurrency(row.total, 0)}</td
                            >
                        </tr>
                    {:else}
                        <tr>
                            <td colspan="5" class="no-data"
                                >{translations.no_data ||
                                    "No data available"}</td
                            >
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Treasury Auction Demand Section -->
    <TreasuryAuctionDemand {darkMode} {translations} {dashboardData} />
</div>

<style>
    .us-debt-tab {
        padding: 20px;
        color: #f1f5f9;
    }

    /* Header */
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .header-icon {
        font-size: 28px;
    }

    .header-title {
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        color: #f8fafc;
    }

    .demo-badge {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .header-right {
        display: flex;
        align-items: center;
    }

    .source-link {
        font-size: 12px;
        color: #94a3b8;
        background: rgba(255, 255, 255, 0.05);
        padding: 6px 12px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .source-link a {
        color: #22d3ee;
        text-decoration: none;
    }

    .source-link a:hover {
        text-decoration: underline;
    }

    /* Metrics Grid */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .metric-label {
        font-size: 10px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
    }

    .metric-value {
        font-size: 24px;
        font-weight: 700;
    }

    .metric-value.cyan {
        color: #22d3ee;
    }
    .metric-value.green {
        color: #4ade80;
    }
    .metric-value.orange {
        color: #fb923c;
    }
    .metric-value.white {
        color: #f8fafc;
    }

    .metric-sub {
        font-size: 11px;
        color: #64748b;
    }

    /* Chart Card */
    .chart-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .chart-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        color: #f8fafc;
    }

    .chart-controls {
        display: flex;
        gap: 12px;
    }

    .view-toggle {
        display: flex;
        gap: 4px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 8px;
        padding: 4px;
    }

    .view-toggle button {
        background: transparent;
        border: none;
        color: #94a3b8;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }

    .view-toggle button:hover {
        color: #f8fafc;
    }

    .view-toggle button.active {
        background: #3b82f6;
        color: white;
    }

    .chart-content {
        position: relative;
    }

    .no-data-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #64748b;
        gap: 12px;
    }

    .no-data-placeholder span {
        font-size: 48px;
        opacity: 0.5;
    }

    /* Table Card */
    .table-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
    }

    .table-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }

    .table-title {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
        color: #f8fafc;
    }

    .table-updated {
        font-size: 11px;
        color: #64748b;
        background: rgba(255, 255, 255, 0.05);
        padding: 4px 10px;
        border-radius: 6px;
    }

    .table-content {
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
    }

    /* Fixed header for scrollable table */
    .table-content thead {
        position: sticky;
        top: 0;
        z-index: 10;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }

    thead th {
        text-align: left;
        padding: 12px 16px;
        background: rgba(0, 0, 0, 0.2);
        color: #94a3b8;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 10px;
        letter-spacing: 0.5px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    tbody td {
        padding: 12px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .month-cell {
        color: #f8fafc;
        font-weight: 500;
    }

    .value-cell {
        font-family: "JetBrains Mono", monospace;
        font-weight: 500;
    }

    .value-cell.green {
        color: #4ade80;
    }
    .value-cell.blue {
        color: #3b82f6;
    }
    .value-cell.purple {
        color: #8b5cf6;
    }
    .value-cell.total {
        color: #22d3ee;
        font-weight: 700;
    }

    tbody tr:hover {
        background: rgba(255, 255, 255, 0.02);
    }

    .no-data {
        text-align: center;
        color: #64748b;
        padding: 32px !important;
    }

    /* Dark mode adjustments */
    .us-debt-tab:not(.dark) {
        color: #1e293b;
    }

    .us-debt-tab:not(.dark) .header-title,
    .us-debt-tab:not(.dark) .chart-title,
    .us-debt-tab:not(.dark) .table-title {
        color: #1e293b;
    }

    .us-debt-tab:not(.dark) .metric-value.white {
        color: #1e293b;
    }
</style>
