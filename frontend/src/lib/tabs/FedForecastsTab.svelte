<script>
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    export let darkMode = false;
    export let translations = {};
    export let dashboardData = {};

    // Chart data props
    export let cpiData = [];
    export let pceData = [];
    export let pmiData = [];
    export let unemploymentData = [];
    export let fedFundsData = [];

    // Ranges
    export let cpiRange = "5Y";
    export let pceRange = "5Y";
    export let pmiRange = "5Y";
    export let unemploymentRange = "5Y";
    export let fedFundsRange = "5Y";
    export let inflationExpectationsData = [];
    export let inflationExpectationsRange = "5Y";

    // FOMC Meeting Dates - dynamically loaded from data pipeline or fallback to static
    // The pipeline scrapes dates from federalreserve.gov/monetarypolicy/fomccalendars.htm
    $: FOMC_DATES = (dashboardData.fed_forecasts?.fomc_dates || []).map(
        (m) => ({
            date: new Date(m.date),
            label: m.label,
            hasSEP: m.hasSEP || false,
        }),
    );

    // Fallback dates if dynamic fetch fails
    const FALLBACK_FOMC_DATES = [
        {
            date: new Date(Date.UTC(2025, 0, 29)),
            label: "Jan 28-29",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 2, 19)),
            label: "Mar 18-19",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 4, 7)),
            label: "May 6-7",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 5, 18)),
            label: "Jun 17-18",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 6, 30)),
            label: "Jul 29-30",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 8, 17)),
            label: "Sep 16-17",
            hasSEP: true,
        },
        {
            date: new Date(Date.UTC(2025, 9, 29)),
            label: "Oct 28-29",
            hasSEP: false,
        },
        {
            date: new Date(Date.UTC(2025, 11, 10)),
            label: "Dec 9-10",
            hasSEP: true,
        },
    ];

    // Use dynamic dates if available, fallback otherwise
    $: fomcDates = FOMC_DATES.length > 0 ? FOMC_DATES : FALLBACK_FOMC_DATES;

    // Latest Dot Plot data from December 2024 FOMC (most recent)
    // Each entry is a dot representing a Fed official's projection
    const DOT_PLOT_DATA = {
        year: 2024,
        meeting: "December 2024",
        projections: {
            2024: [
                4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375,
                4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375, 4.375,
                4.375,
            ],
            2025: [
                3.625, 3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125,
                4.125, 4.125, 4.125, 4.375, 4.375, 4.375, 4.375, 4.375, 4.625,
                4.625,
            ],
            2026: [
                2.875, 3.125, 3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625,
                3.625, 3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125,
                4.125,
            ],
            2027: [
                2.625, 2.875, 2.875, 2.875, 2.875, 3.125, 3.125, 3.125, 3.125,
                3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625, 3.625, 3.875,
                3.875,
            ],
            longerRun: [
                2.625, 2.625, 2.875, 2.875, 2.875, 2.875, 2.875, 3.0, 3.0, 3.0,
                3.0, 3.0, 3.0, 3.0, 3.125, 3.125, 3.25, 3.25, 3.5,
            ],
        },
        currentRate: 4.375,
    };

    // Calculate next FOMC meeting
    $: nextFOMC = (() => {
        const now = new Date();
        return fomcDates.find((m) => m.date > now) || fomcDates[0];
    })();

    // Countdown calculation (using UTC to avoid timezone issues)
    $: countdown = (() => {
        if (!nextFOMC) return { days: 0, hours: 0, mins: 0 };
        const now = new Date();
        const diff = nextFOMC.date.getTime() - now.getTime();
        // Ensure positive values
        const absDiff = Math.abs(diff);
        const days = Math.floor(absDiff / (1000 * 60 * 60 * 24));
        const hours = Math.floor(
            (absDiff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
        );
        const mins = Math.floor((absDiff % (1000 * 60 * 60)) / (1000 * 60));
        return { days, hours, mins };
    })();

    // Dot plot aggregation for visualization
    $: dotPlotAggregated = Object.entries(DOT_PLOT_DATA.projections).map(
        ([year, dots]) => {
            const counts = {};
            dots.forEach((d) => {
                counts[d] = (counts[d] || 0) + 1;
            });
            const median = dots.sort((a, b) => a - b)[
                Math.floor(dots.length / 2)
            ];
            return {
                year,
                counts,
                median,
                min: Math.min(...dots),
                max: Math.max(...dots),
            };
        },
    );

    // Chart layouts
    $: cpiLayout = {
        yaxis: { title: "YoY %", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
        shapes: [
            {
                type: "line",
                y0: 2,
                y1: 2,
                x0: 0,
                x1: 1,
                xref: "paper",
                line: { color: "#10b981", width: 2, dash: "dash" },
                layer: "below",
            },
        ],
        annotations: [
            {
                x: 1.02,
                y: 2,
                xref: "paper",
                yref: "y",
                text: "2% Target",
                showarrow: false,
                font: { size: 10, color: "#10b981" },
            },
        ],
    };

    $: pmiLayout = {
        yaxis: { title: "PMI Index", range: [35, 70], dtick: 5 },
        margin: { l: 50, r: 20, t: 20, b: 40 },
        shapes: [
            {
                type: "line",
                y0: 50,
                y1: 50,
                x0: 0,
                x1: 1,
                xref: "paper",
                line: { color: "#f59e0b", width: 2, dash: "dash" },
                layer: "below",
            },
        ],
        annotations: [
            {
                x: 1.02,
                y: 50,
                xref: "paper",
                yref: "y",
                text: "Expansion/Contraction",
                showarrow: false,
                font: { size: 9, color: "#f59e0b" },
            },
        ],
    };

    $: unemploymentLayout = {
        yaxis: { title: "Rate (%)", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    $: fedFundsLayout = {
        yaxis: { title: "Rate (%)", autorange: true },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    // Get latest values helper
    function getLatest(arr) {
        if (!arr || arr.length === 0) return null;
        for (let i = arr.length - 1; i >= 0; i--) {
            if (arr[i] !== null && arr[i] !== undefined && !isNaN(arr[i]))
                return arr[i];
        }
        return null;
    }

    // Latest values
    $: latestCPI = getLatest(dashboardData.fed_forecasts?.cpi_yoy);
    $: latestCoreCPI = getLatest(dashboardData.fed_forecasts?.core_cpi_yoy);
    $: latestPCE = getLatest(dashboardData.fed_forecasts?.pce_yoy);
    $: latestCorePCE = getLatest(dashboardData.fed_forecasts?.core_pce_yoy);
    $: latestISMMfg = getLatest(dashboardData.fed_forecasts?.ism_mfg);
    $: latestISMSvc = getLatest(dashboardData.fed_forecasts?.ism_svc);
    $: latestUnemployment = getLatest(
        dashboardData.fed_forecasts?.unemployment,
    );
    $: latestFedFunds = getLatest(dashboardData.fed_forecasts?.fed_funds_rate);
    $: latestInflationExpect5Y = getLatest(
        dashboardData.fed_forecasts?.inflation_expect_5y,
    );
    $: latestInflationExpect10Y = getLatest(
        dashboardData.fed_forecasts?.inflation_expect_10y,
    );
</script>

<div class="fed-forecasts-tab">
    <!-- FOMC Countdown Card -->
    <div class="fomc-countdown-section">
        <div class="countdown-card">
            <div class="countdown-header">
                <h3>
                    📅 {translations.next_fomc_meeting || "Next FOMC Meeting"}
                </h3>
                <span class="meeting-date"
                    >{nextFOMC?.label || "TBD"}
                    {nextFOMC?.hasSEP ? "(SEP)" : ""}</span
                >
            </div>
            <div class="countdown-timer">
                <div class="countdown-unit">
                    <span class="countdown-value">{countdown.days}</span>
                    <span class="countdown-label"
                        >{translations.days || "Days"}</span
                    >
                </div>
                <div class="countdown-unit">
                    <span class="countdown-value">{countdown.hours}</span>
                    <span class="countdown-label"
                        >{translations.hours || "Hours"}</span
                    >
                </div>
                <div class="countdown-unit">
                    <span class="countdown-value">{countdown.mins}</span>
                    <span class="countdown-label"
                        >{translations.mins || "Mins"}</span
                    >
                </div>
            </div>
            {#if nextFOMC?.hasSEP}
                <div class="sep-indicator">
                    {translations.includes_sep ||
                        "Includes Summary of Economic Projections (Dot Plot)"}
                </div>
            {/if}
        </div>

        <!-- Key Metrics Cards -->
        <div class="metrics-row">
            <div class="metric-card">
                <span class="metric-label"
                    >{translations.fed_funds_rate || "Fed Funds Rate"}</span
                >
                <span class="metric-value"
                    >{latestFedFunds?.toFixed(2) ?? "—"}%</span
                >
            </div>
            <div class="metric-card">
                <span class="metric-label"
                    >{translations.core_pce_yoy || "Core PCE YoY"}</span
                >
                <span
                    class="metric-value"
                    class:above-target={latestCorePCE > 2}
                    >{latestCorePCE?.toFixed(2) ?? "—"}%</span
                >
            </div>
            <div class="metric-card">
                <span class="metric-label"
                    >{translations.unemployment_rate || "Unemployment"}</span
                >
                <span class="metric-value"
                    >{latestUnemployment?.toFixed(1) ?? "—"}%</span
                >
            </div>
            <div class="metric-card">
                <span class="metric-label"
                    >{translations.ism_mfg_pmi || "ISM Mfg PMI"}</span
                >
                <span class="metric-value" class:below-50={latestISMMfg < 50}
                    >{latestISMMfg?.toFixed(1) ?? "—"}</span
                >
            </div>
        </div>
    </div>

    <!-- Dot Plot Section -->
    <div class="dot-plot-section">
        <div class="chart-card full-width">
            <div class="chart-header">
                <h3>
                    🎯 {translations.fed_dot_plot || "Fed Dot Plot"} ({DOT_PLOT_DATA.meeting})
                </h3>
            </div>
            <p class="chart-description">
                {translations.fomc_projections_description ||
                    "FOMC participants' projections for the federal funds rate. Each dot represents one official's view."}
            </p>
            <div class="dot-plot-container">
                <div class="dot-plot-grid">
                    {#each dotPlotAggregated as yearData}
                        <div class="dot-plot-column">
                            <div class="dot-plot-year">
                                {yearData.year === "longerRun"
                                    ? translations.long_run || "Long Run"
                                    : yearData.year}
                            </div>
                            <div class="dot-plot-dots">
                                {#each Object.entries(yearData.counts).sort((a, b) => Number(b[0]) - Number(a[0])) as [rate, count]}
                                    <div class="dot-row">
                                        <span class="dot-rate">{rate}%</span>
                                        <div class="dots">
                                            {#each Array(count) as _}
                                                <span
                                                    class="dot"
                                                    class:median={Number(
                                                        rate,
                                                    ) === yearData.median}
                                                ></span>
                                            {/each}
                                        </div>
                                    </div>
                                {/each}
                            </div>
                            <div class="dot-plot-median">
                                Median: {yearData.median}%
                            </div>
                        </div>
                    {/each}
                </div>
                <div class="dot-plot-legend">
                    <span class="legend-item"
                        ><span class="dot"></span>
                        {translations.individual_projection ||
                            "Individual Projection"}</span
                    >
                    <span class="legend-item"
                        ><span class="dot median"></span>
                        {translations.median || "Median"}</span
                    >
                    <span class="legend-item current-rate"
                        >{translations.current_rate || "Current Rate"}: {DOT_PLOT_DATA.currentRate}%</span
                    >
                </div>
            </div>
        </div>
    </div>

    <!-- Inflation Charts -->
    <div class="charts-grid">
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    📊 {translations.cpi_inflation_yoy || "CPI Inflation (YoY)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cpiRange}
                        onRangeChange={(r) => (cpiRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.cpi_description ||
                    "Consumer Price Index year-over-year change. Target: 2%"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cpiData} layout={cpiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.headline_cpi || "Headline CPI"}:
                    <b>{latestCPI?.toFixed(2) ?? "—"}%</b></span
                >
                <span
                    >{translations.core_cpi || "Core CPI"}:
                    <b>{latestCoreCPI?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    📊 {translations.pce_inflation_yoy || "PCE Inflation (YoY)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={pceRange}
                        onRangeChange={(r) => (pceRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.pce_description ||
                    "Personal Consumption Expenditures (Fed's preferred gauge). Target: 2%"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={pceData} layout={cpiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.headline_pce || "Headline PCE"}:
                    <b>{latestPCE?.toFixed(2) ?? "—"}%</b></span
                >
                <span
                    >{translations.core_pce || "Core PCE"}:
                    <b>{latestCorePCE?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>🏭 {translations.ism_pmi || "ISM PMI"}</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={pmiRange}
                        onRangeChange={(r) => (pmiRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.pmi_description ||
                    "Manufacturing & Services PMI. Above 50 = Expansion, Below 50 = Contraction"}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={pmiData} layout={pmiLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.manufacturing || "Manufacturing"}:
                    <b class:below-50={latestISMMfg < 50}
                        >{latestISMMfg?.toFixed(1) ?? "—"}</b
                    ></span
                >
                <span
                    >{translations.services || "Services"}:
                    <b class:below-50={latestISMSvc < 50}
                        >{latestISMSvc?.toFixed(1) ?? "—"}</b
                    ></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    👷 {translations.unemployment_rate || "Unemployment Rate"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={unemploymentRange}
                        onRangeChange={(r) => (unemploymentRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.unemployment_description ||
                    "U.S. unemployment rate. Key indicator for Fed dual mandate."}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={unemploymentData}
                    layout={unemploymentLayout}
                />
            </div>
            <div class="latest-values">
                <span
                    >{translations.current || "Current"}:
                    <b>{latestUnemployment?.toFixed(1) ?? "—"}%</b></span
                >
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    🏦 {translations.fed_funds_rate || "Federal Funds Rate"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={fedFundsRange}
                        onRangeChange={(r) => (fedFundsRange = r)}
                    />
                </div>
            </div>
            <p class="chart-description">
                {translations.fed_funds_description ||
                    "Effective Federal Funds Rate. Primary tool for monetary policy."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={fedFundsData} layout={fedFundsLayout} />
            </div>
            <div class="latest-values">
                <span
                    >{translations.current_rate || "Current Rate"}:
                    <b>{latestFedFunds?.toFixed(2) ?? "—"}%</b></span
                >
            </div>
        </div>
    </div>

    <!-- Inflation Expectations Chart -->
    <div class="chart-section">
        <div class="chart-header">
            <h3>
                💹 {translations.inflation_expectations ||
                    "Inflation Expectations (TIPS Breakeven)"}
            </h3>
            <p class="chart-description">
                {translations.inflation_expectations_description ||
                    "Market-implied inflation expectations vs actual CPI. Divergence signals potential policy shifts."}
            </p>
        </div>
        <div class="chart-container">
            <TimeRangeSelector
                bind:selectedRange={inflationExpectationsRange}
            />
            <Chart data={inflationExpectationsData} layout={cpiLayout} />
            <div class="chart-footer">
                <div class="latest-values">
                    <div class="value-item">
                        <span class="value-label">5Y Breakeven:</span>
                        <span class="value-number">
                            {latestInflationExpect5Y !== null
                                ? `${latestInflationExpect5Y.toFixed(2)}%`
                                : "N/A"}
                        </span>
                    </div>
                    <div class="value-item">
                        <span class="value-label">10Y Breakeven:</span>
                        <span class="value-number">
                            {latestInflationExpect10Y !== null
                                ? `${latestInflationExpect10Y.toFixed(2)}%`
                                : "N/A"}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .fed-forecasts-tab {
        padding: 20px;
    }

    /* FOMC Countdown Section */
    .fomc-countdown-section {
        margin-bottom: 30px;
    }

    .countdown-card {
        background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
        border-radius: 16px;
        padding: 24px;
        color: white;
        margin-bottom: 20px;
    }

    .countdown-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    .countdown-header h3 {
        margin: 0;
        font-size: 1.3rem;
    }

    .meeting-date {
        font-size: 1.1rem;
        opacity: 0.9;
        font-weight: 600;
    }

    .countdown-timer {
        display: flex;
        justify-content: center;
        gap: 40px;
    }

    .countdown-unit {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .countdown-value {
        font-size: 3rem;
        font-weight: 800;
        line-height: 1;
    }

    .countdown-label {
        font-size: 0.9rem;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .sep-indicator {
        text-align: center;
        margin-top: 15px;
        font-size: 0.85rem;
        opacity: 0.85;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        display: inline-block;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    }

    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
    }

    .metric-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        flex-direction: column;
        align-items: center;
        border: 1px solid var(--border-color);
    }

    .metric-label {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .metric-value.above-target {
        color: #ef4444;
    }

    .metric-value.below-50 {
        color: #f59e0b;
    }

    /* Dot Plot Section */
    .dot-plot-section {
        margin-bottom: 30px;
    }

    .chart-card.full-width {
        width: 100%;
    }

    .dot-plot-container {
        padding: 20px;
    }

    .dot-plot-grid {
        display: flex;
        justify-content: space-around;
        gap: 20px;
        flex-wrap: wrap;
    }

    .dot-plot-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 120px;
    }

    .dot-plot-year {
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 10px;
        color: var(--text-primary);
    }

    .dot-plot-dots {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .dot-row {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .dot-rate {
        font-size: 0.75rem;
        color: var(--text-muted);
        width: 40px;
        text-align: right;
    }

    .dots {
        display: flex;
        gap: 3px;
    }

    .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #3b82f6;
    }

    .dot.median {
        background: #10b981;
        box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
    }

    .dot-plot-median {
        margin-top: 10px;
        font-size: 0.85rem;
        color: #10b981;
        font-weight: 600;
    }

    .dot-plot-legend {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-top: 20px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.85rem;
        color: var(--text-muted);
    }

    .current-rate {
        color: var(--text-primary);
        font-weight: 600;
    }

    /* Charts Grid */
    .charts-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    .chart-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid var(--border-color);
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }

    .chart-header h3 {
        margin: 0;
        font-size: 1.1rem;
    }

    .chart-description {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0 0 15px 0;
        padding: 10px;
        background: var(--chart-description-bg);
        border-radius: 8px;
        border-left: 3px solid var(--accent-primary);
    }

    .chart-content {
        height: 300px;
    }

    .latest-values {
        display: flex;
        justify-content: space-around;
        padding: 12px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.9rem;
    }

    .latest-values b.below-50 {
        color: #f59e0b;
    }

    @media (max-width: 1200px) {
        .charts-grid {
            grid-template-columns: 1fr;
        }

        .metrics-row {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 768px) {
        .countdown-timer {
            gap: 20px;
        }

        .countdown-value {
            font-size: 2rem;
        }

        .metrics-row {
            grid-template-columns: 1fr;
        }

        .dot-plot-grid {
            flex-direction: column;
            align-items: center;
        }
    }
</style>
