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
            probs: m.probs || null,
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

    // Fed Rate Probabilities Chart logic
    let selectedMeetingIndex = 0;

    $: selectedMeeting = fomcDates[selectedMeetingIndex] || fomcDates[0];

    $: probChartData =
        selectedMeeting && selectedMeeting.probs
            ? [
                  {
                      x: [
                          translations.prob_cut || "Cut",
                          translations.no_change || "Hold",
                          translations.prob_hike || "Hike",
                      ],
                      y: [
                          selectedMeeting.probs.cut,
                          selectedMeeting.probs.hold,
                          selectedMeeting.probs.hike,
                      ],
                      type: "bar",
                      marker: {
                          color: ["#10b981", "#f59e0b", "#ef4444"],
                      },
                      text: [
                          `${selectedMeeting.probs.cut}%`,
                          `${selectedMeeting.probs.hold}%`,
                          `${selectedMeeting.probs.hike}%`,
                      ],
                      textposition: "auto",
                      hoverinfo: "none",
                  },
              ]
            : [];

    $: probChartLayout = {
        title: {
            text: selectedMeeting
                ? `${selectedMeeting.label} (${selectedMeeting.date.getFullYear()})`
                : "",
            font: { size: 13, color: darkMode ? "#e5e7eb" : "#374151" },
        },
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: { color: darkMode ? "#e5e7eb" : "#374151" },
        showlegend: false,
        margin: { t: 40, b: 40, l: 40, r: 20 },
        height: 300,
        xaxis: { gridcolor: darkMode ? "#374151" : "#e5e7eb" },
        yaxis: {
            gridcolor: darkMode ? "#374151" : "#e5e7eb",
            range: [0, 105],
            title: "% Probability",
        },
    };

    // Dot Plot data - dynamically loaded from pipeline or fallback
    // Source: palewire/fed-dot-plot-scraper (scraped from Fed website)
    const FALLBACK_DOT_PLOT = {
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

    // Use dynamic Dot Plot if available from data pipeline
    $: DOT_PLOT_DATA =
        dashboardData.fed_forecasts?.dot_plot || FALLBACK_DOT_PLOT;

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

    // Dot plot aggregation for visualization (Filtering out 'longerRun' as requested)
    $: dotPlotAggregated = Object.entries(DOT_PLOT_DATA.projections)
        .filter(([key]) => key !== "longerRun")
        .map(([year, dots]) => {
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
        });

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
    <!-- Key Metrics Cards -->
    <div class="metrics-section">
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

    <!-- Dot Plot Section + FOMC Calendar -->
    <div class="dot-plot-section">
        <div class="left-stats-column">
            <!-- Dot Plot Card -->
            <div class="chart-card dot-plot-card">
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
                                            <span class="dot-rate">{rate}%</span
                                            >
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
                                    {translations.median || "Median"}: {yearData.median}%
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

            {#if probChartData.length > 0}
                <div class="chart-card prob-chart-card">
                    <div class="chart-header">
                        <h3>
                            📊 {translations.target_rate ||
                                "Target Rate Probabilities"}
                        </h3>
                    </div>
                    <div class="chart-content">
                        <Chart
                            {darkMode}
                            data={probChartData}
                            layout={probChartLayout}
                        />
                    </div>
                    {#if selectedMeeting && selectedMeeting.probs}
                        <div class="prob-footer">
                            <span class="implied-info">
                                {translations.implied_rate || "Implied Rate"}:
                                <b>{selectedMeeting.probs.implied_rate}%</b>
                            </span>
                        </div>
                    {/if}
                </div>
            {/if}
        </div>

        <!-- FOMC Calendar Card -->
        <div class="chart-card fomc-calendar-card">
            <div class="chart-header">
                <h3>
                    📅 {translations.upcoming_fomc_meetings ||
                        "Upcoming FOMC Meetings"}
                </h3>
            </div>
            <div class="fomc-meetings-list">
                {#each fomcDates.slice(0, 8) as meeting, i}
                    <div
                        class="fomc-meeting-item"
                        class:next-meeting={i === 0}
                        class:selected={selectedMeetingIndex === i}
                        on:click={() => (selectedMeetingIndex = i)}
                        on:keydown={(e) =>
                            e.key === "Enter" && (selectedMeetingIndex = i)}
                        role="button"
                        tabindex="0"
                    >
                        <div class="meeting-date-badge">
                            <span class="meeting-month"
                                >{meeting.label.split(" ")[0]}</span
                            >
                            <span class="meeting-days"
                                >{meeting.label.split(" ")[1]}</span
                            >
                        </div>
                        <div class="meeting-info">
                            <span class="meeting-year"
                                >{meeting.date.getFullYear()}</span
                            >
                            {#if meeting.hasSEP}
                                <span class="sep-badge">SEP</span>
                            {/if}
                        </div>

                        {#if meeting.probs}
                            <div class="meeting-probs">
                                <div class="prob-row">
                                    <div class="prob-label-group">
                                        <span class="prob-label"
                                            >{translations.prob_cut ||
                                                "Cut"}</span
                                        >
                                        <div class="roc-container">
                                            {#if meeting.probs.roc1d}
                                                <span
                                                    class="roc-value"
                                                    title="1-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc1d.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc1d.cut < 0}
                                                >
                                                    1D: {meeting.probs.roc1d
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1d.cut}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc5d}
                                                <span
                                                    class="roc-value"
                                                    title="5-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc5d.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc5d.cut < 0}
                                                >
                                                    5D: {meeting.probs.roc5d
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc5d.cut}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc1m}
                                                <span
                                                    class="roc-value"
                                                    title="1-Month Trend"
                                                    class:up={meeting.probs
                                                        .roc1m.cut > 0}
                                                    class:down={meeting.probs
                                                        .roc1m.cut < 0}
                                                >
                                                    1M: {meeting.probs.roc1m
                                                        .cut > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1m.cut}%
                                                </span>
                                            {/if}
                                        </div>
                                    </div>
                                    <span
                                        class="prob-value"
                                        class:high={meeting.probs.cut > 60}
                                        class:med={meeting.probs.cut > 30 &&
                                            meeting.probs.cut <= 60}
                                        class:low={meeting.probs.cut <= 30}
                                    >
                                        {meeting.probs.cut}%
                                    </span>
                                </div>
                                <div class="prob-row">
                                    <div class="prob-label-group">
                                        <span class="prob-label"
                                            >{translations.prob_hold ||
                                                "Hold"}</span
                                        >
                                        <div class="roc-container">
                                            {#if meeting.probs.roc1d}
                                                <span
                                                    class="roc-value"
                                                    title="1-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc1d.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc1d.hold < 0}
                                                >
                                                    1D: {meeting.probs.roc1d
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1d.hold}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc5d}
                                                <span
                                                    class="roc-value"
                                                    title="5-Day Trend"
                                                    class:up={meeting.probs
                                                        .roc5d.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc5d.hold < 0}
                                                >
                                                    5D: {meeting.probs.roc5d
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc5d.hold}%
                                                </span>
                                            {/if}
                                            {#if meeting.probs.roc1m}
                                                <span
                                                    class="roc-value"
                                                    title="1-Month Trend"
                                                    class:up={meeting.probs
                                                        .roc1m.hold > 0}
                                                    class:down={meeting.probs
                                                        .roc1m.hold < 0}
                                                >
                                                    1M: {meeting.probs.roc1m
                                                        .hold > 0
                                                        ? "+"
                                                        : ""}{meeting.probs
                                                        .roc1m.hold}%
                                                </span>
                                            {/if}
                                        </div>
                                    </div>
                                    <span
                                        class="prob-value"
                                        class:high={meeting.probs.hold > 60}
                                        class:med={meeting.probs.hold > 30 &&
                                            meeting.probs.hold <= 60}
                                        class:low={meeting.probs.hold <= 30}
                                    >
                                        {meeting.probs.hold}%
                                    </span>
                                </div>
                                {#if meeting.probs.hike > 0}
                                    <div class="prob-row">
                                        <div class="prob-label-group">
                                            <span class="prob-label"
                                                >{translations.prob_hike ||
                                                    "Hike"}</span
                                            >
                                            <div class="roc-container">
                                                {#if meeting.probs.roc1d}
                                                    <span
                                                        class="roc-value"
                                                        title="1-Day Trend"
                                                        class:up={meeting.probs
                                                            .roc1d.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc1d.hike <
                                                            0}
                                                    >
                                                        1D: {meeting.probs.roc1d
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc1d.hike}%
                                                    </span>
                                                {/if}
                                                {#if meeting.probs.roc5d}
                                                    <span
                                                        class="roc-value"
                                                        title="5-Day Trend"
                                                        class:up={meeting.probs
                                                            .roc5d.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc5d.hike <
                                                            0}
                                                    >
                                                        5D: {meeting.probs.roc5d
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc5d.hike}%
                                                    </span>
                                                {/if}
                                                {#if meeting.probs.roc1m}
                                                    <span
                                                        class="roc-value"
                                                        title="1-Month Trend"
                                                        class:up={meeting.probs
                                                            .roc1m.hike > 0}
                                                        class:down={meeting
                                                            .probs.roc1m.hike <
                                                            0}
                                                    >
                                                        1M: {meeting.probs.roc1m
                                                            .hike > 0
                                                            ? "+"
                                                            : ""}{meeting.probs
                                                            .roc1m.hike}%
                                                    </span>
                                                {/if}
                                            </div>
                                        </div>
                                        <span
                                            class="prob-value"
                                            class:high={meeting.probs.hike > 60}
                                            class:med={meeting.probs.hike >
                                                30 && meeting.probs.hike <= 60}
                                            class:low={meeting.probs.hike <= 30}
                                        >
                                            {meeting.probs.hike}%
                                        </span>
                                    </div>
                                {/if}
                                {#if meeting.probs.cumulative_cuts > 0}
                                    <div class="cumulative-info">
                                        Σ {meeting.probs.cumulative_cuts}
                                        {translations.cumulative_cuts || "Cuts"}
                                    </div>
                                {/if}
                            </div>
                        {/if}

                        {#if i === 0}
                            <div class="next-badge">
                                {translations.next || "NEXT"}
                            </div>
                        {/if}
                    </div>
                {/each}
            </div>
            <div class="fomc-legend">
                <span class="legend-note">
                    <span class="sep-badge-small">SEP</span> = {translations.summary_of_projections ||
                        "Summary of Economic Projections"}
                </span>
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

    .metrics-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 25px;
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

    /* Dot Plot Section - Two Column Layout */
    /* Dot Plot Section - Two Column Layout */
    .dot-plot-section {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-bottom: 25px;
        align-items: stretch;
    }

    .left-stats-column {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .dot-plot-card,
    .prob-chart-card,
    .fomc-calendar-card {
        min-width: 0;
        display: flex;
        flex-direction: column;
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
    }

    .dot-plot-card,
    .prob-chart-card {
        flex: 1;
    }

    .fomc-meetings-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 15px;
    }

    .fomc-meeting-item {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        background: rgba(0, 0, 0, 0.03);
        border-radius: 8px;
        margin-bottom: 8px;
        position: relative;
        border: 1px solid transparent;
        transition: all 0.2s ease;
        cursor: pointer;
    }

    .fomc-meeting-item:hover {
        background: rgba(0, 0, 0, 0.06);
        border-color: var(--accent-primary);
    }

    .fomc-meeting-item.selected {
        background: rgba(59, 130, 246, 0.1);
        border-color: #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
    }

    .fomc-meeting-item.next-meeting {
        background: rgba(16, 185, 129, 0.05);
        border-left: 4px solid #10b981;
    }

    .prob-footer {
        padding: 10px;
        text-align: center;
        border-top: 1px solid var(--border-color);
        margin-top: 10px;
    }

    .implied-info {
        font-size: 0.9rem;
        color: var(--text-muted);
    }

    .implied-info b {
        color: var(--accent-primary);
    }

    .meeting-date-badge {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-width: 50px;
        width: 50px;
        height: 50px;
        flex-shrink: 0;
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 6px;
        margin-right: 12px;
    }

    .meeting-month {
        font-size: 0.7rem;
        font-weight: 800;
        line-height: 1;
        text-transform: uppercase;
        color: #ffc107;
        margin-bottom: 2px;
    }

    .meeting-days {
        font-size: 0.9rem;
        font-weight: 700;
        line-height: 1;
        color: var(--text-primary);
    }

    .meeting-info {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        flex: 1;
    }

    .meeting-year {
        font-size: 0.85rem;
        opacity: 0.8;
    }

    .sep-badge {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
    }

    .sep-badge-small {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        font-size: 0.6rem;
        font-weight: 700;
        padding: 1px 4px;
        border-radius: 3px;
    }

    .next-badge {
        position: absolute;
        left: -10px;
        top: -10px;
        background: linear-gradient(135deg, #4caf50, #45a049);
        color: white;
        font-size: 0.55rem;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        z-index: 10;
        letter-spacing: 0.5px;
    }

    /* Rate Probabilities */
    .meeting-probs {
        display: flex;
        flex-direction: column;
        gap: 3px;
        margin-left: auto;
        padding-left: 15px;
        border-left: 1px solid var(--border-color);
        min-width: 240px;
        position: relative;
        z-index: 1;
    }

    .prob-label-group {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .roc-container {
        display: flex;
        gap: 5px;
        flex-wrap: wrap;
    }

    .roc-value {
        font-size: 0.62rem;
        font-weight: 700;
        white-space: nowrap;
        background: rgba(0, 0, 0, 0.03);
        padding: 1px 3px;
        border-radius: 3px;
        color: var(--text-muted);
    }

    .roc-value.up {
        color: #10b981;
    }

    .roc-value.down {
        color: #ef4444;
    }

    .prob-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        gap: 8px;
    }

    .prob-label {
        color: var(--text-muted);
    }

    .prob-value {
        font-weight: 600;
        font-family: "Monaco", monospace;
    }

    .prob-value.high {
        color: #10b981;
    }

    .prob-value.med {
        color: #f59e0b;
    }

    .prob-value.low {
        color: var(--text-muted);
    }

    .cumulative-info {
        margin-top: 4px;
        font-size: 0.65rem;
        color: #3b82f6;
        font-weight: 600;
        text-align: right;
    }

    .fomc-legend {
        padding: 10px 15px;
        border-top: 1px solid rgba(100, 100, 100, 0.2);
        font-size: 0.75rem;
        opacity: 0.8;
    }

    .legend-note {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    @media (max-width: 1200px) {
        .dot-plot-section {
            grid-template-columns: 1fr;
        }
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
        .metrics-row {
            grid-template-columns: 1fr;
        }

        .dot-plot-grid {
            flex-direction: column;
            align-items: center;
        }
    }
</style>
