<script>
    /**
     * RiskModelTab.svelte
     * Displays Credit Liquidity Index (CLI) and risk metrics.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";

    // Props
    export let darkMode = false;
    export let language = "en";
    export let translations = {};
    export let dashboardData = {};

    // Satisfy lint for unused language prop
    $: _lang = language;

    // --- Background Shading Helpers ---

    function createZScoreBands(
        darkMode,
        {
            bullishThreshold = 1.0,
            bearishThreshold = -1.0,
            invertColors = false,
        } = {},
    ) {
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.08)"
            : "rgba(16, 185, 129, 0.12)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.08)"
            : "rgba(239, 68, 68, 0.12)";

        const bullishColor = invertColors ? redColor : greenColor;
        const bearishColor = invertColors ? greenColor : redColor;

        return [
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: bullishThreshold,
                y1: 6,
                fillcolor: bullishColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: -6,
                y1: bearishThreshold,
                fillcolor: bearishColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 0,
                line: {
                    color: darkMode
                        ? "rgba(148, 163, 184, 0.3)"
                        : "rgba(100, 116, 139, 0.3)",
                    width: 1,
                    dash: "dot",
                },
                layer: "below",
            },
        ];
    }

    function createRegimeShapes(filteredDates, allDates, allSignals, darkMode) {
        if (
            !filteredDates ||
            !allDates ||
            !allSignals ||
            filteredDates.length === 0
        )
            return [];

        // Find the start and end indices of the filtered range in the original data
        const startIdx = allDates.findIndex((d) => d === filteredDates[0]);
        const endIdx = allDates.findIndex(
            (d) => d === filteredDates[filteredDates.length - 1],
        );

        if (startIdx === -1 || endIdx === -1) return [];

        const dates = allDates.slice(startIdx, endIdx + 1);
        const signals = allSignals.slice(startIdx, endIdx + 1);

        const shapes = [];
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.12)"
            : "rgba(16, 185, 129, 0.15)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.12)"
            : "rgba(239, 68, 68, 0.15)";

        let currentRegime = null;
        let blockStartIdx = 0;

        for (let i = 0; i <= dates.length; i++) {
            const regime = i < dates.length ? signals[i] : null;
            if (regime !== currentRegime || i === dates.length) {
                if (
                    currentRegime === "bullish" ||
                    currentRegime === "bearish"
                ) {
                    const d0 = dates[blockStartIdx];
                    const d1 = dates[Math.min(i, dates.length - 1)];
                    if (d0 && d1) {
                        shapes.push({
                            type: "rect",
                            xref: "x",
                            yref: "paper",
                            x0: d0,
                            x1: d1,
                            y0: 0,
                            y1: 1,
                            fillcolor:
                                currentRegime === "bullish"
                                    ? greenColor
                                    : redColor,
                            line: { width: 0 },
                            layer: "below",
                        });
                    }
                }
                currentRegime = regime;
                blockStartIdx = i;
            }
        }
        return shapes;
    }

    function calculateSignalArray(
        zScores,
        {
            bullishThreshold = 1.0,
            bearishThreshold = -1.0,
            invertLogic = false,
            requireMomentum = false,
            momentumBars = 21,
        } = {},
    ) {
        if (!zScores || !Array.isArray(zScores)) return [];
        return zScores.map((z, i) => {
            if (z === null || z === undefined || !Number.isFinite(z))
                return "neutral";
            let momentumOk = true;
            if (requireMomentum && i >= momentumBars) {
                const prev = zScores[i - momentumBars];
                if (Number.isFinite(prev)) {
                    const momentum = z - prev;
                    if (z > bullishThreshold && momentum < 0)
                        momentumOk = false;
                    if (z < bearishThreshold && momentum > 0)
                        momentumOk = false;
                }
            }
            if (!momentumOk) return "neutral";
            if (invertLogic) {
                if (z < -Math.abs(bullishThreshold)) return "bullish";
                if (z > Math.abs(bearishThreshold)) return "bearish";
            } else {
                if (z > bullishThreshold) return "bullish";
                if (z < bearishThreshold) return "bearish";
            }
            return "neutral";
        });
    }

    // Chart data
    export let cliData = [];
    export let hyZData = [];
    export let igZData = [];
    export let nfciCreditZData = [];
    export let nfciRiskZData = [];
    export let lendingZData = [];
    export let vixZData = [];
    export let tipsData = [];
    export let tipsLayout = {};
    export let repoStressData = [];

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;
    export let getLatestROC = (rocs, period) =>
        rocs?.[period]?.[rocs?.[period]?.length - 1] ?? 0;

    // Time range states - managed locally
    export let cliRange = "ALL";
    export let hyRange = "ALL";
    export let igRange = "ALL";
    export let nfciCreditRange = "ALL";
    export let nfciRiskRange = "ALL";
    export let lendingRange = "ALL";
    export let vixRange = "ALL";
    export let tipsRange = "ALL";
    export let repoStressRange = "ALL";

    $: hyLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: 1.0,
            bearishThreshold: -1.0,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: igLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: 1.0,
            bearishThreshold: -1.0,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciCreditLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: 0.5,
            bearishThreshold: -0.5,
            invertColors: true,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciRiskLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: -0.5,
            bearishThreshold: 1.0,
            invertColors: true,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: lendingLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: 0,
            bearishThreshold: 0.5,
            invertColors: true,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: vixLayout = {
        shapes: createZScoreBands(darkMode, {
            bullishThreshold: -0.5,
            bearishThreshold: 2.0,
            invertColors: true,
        }),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };

    // CLI Composite Regime
    $: cliSignals = calculateSignalArray(dashboardData.cli, {
        bullishThreshold: 0.5,
        bearishThreshold: -0.5,
        requireMomentum: true,
        momentumBars: 20,
    });
    $: cliLayout = {
        shapes: createRegimeShapes(
            cliData[0]?.x || [],
            dashboardData.dates,
            cliSignals,
            darkMode,
        ),
        yaxis: { title: "CLI Index", dtick: 2.5, autorange: true },
    };

    // TIPS Composite Regime
    $: tipsRegimeSignals = (() => {
        const dates = dashboardData.dates;
        const be = dashboardData.tips_breakeven;
        const rr = dashboardData.tips_real_rate;
        const fwd = dashboardData.tips_5y5y_forward;
        if (!dates || !be || !rr || !fwd) return [];
        return dates.map((_, i) => {
            if (i < 63) return "neutral";
            const rrNow = rr[i];
            const beNow = be[i];
            const fwdNow = fwd[i];
            const rr3mAgo = rr[i - 63];
            const be3mAgo = be[i - 63];
            const fwd3mAgo = fwd[i - 63];
            if (
                [rrNow, beNow, fwdNow, rr3mAgo, be3mAgo, fwd3mAgo].some(
                    (v) => !Number.isFinite(v),
                )
            )
                return "neutral";
            const rr3mDelta = rrNow - rr3mAgo;
            const be3mDelta = beNow - be3mAgo;
            const fwd3mDelta = fwdNow - fwd3mAgo;
            if (rrNow > 2.0 || rr3mDelta > 0.5) return "bearish";
            if (be3mDelta > 0.2 && rr3mDelta <= 0) return "bullish";
            if (fwd3mDelta < -0.2) return "bearish";
            return "neutral";
        });
    })();
    $: tipsLayoutWithBands = {
        ...tipsLayout,
        shapes: createRegimeShapes(
            tipsData[0]?.x || [],
            dashboardData.dates,
            tipsRegimeSignals,
            darkMode,
        ),
        yaxis: { ...tipsLayout.yaxis, dtick: 0.5, autorange: true },
        yaxis2: { ...tipsLayout.yaxis2, dtick: 0.5, autorange: true },
    };

    // Repo Regime
    $: repoRegimeSignals = (() => {
        const sofr = dashboardData.repo_stress?.sofr;
        const iorb = dashboardData.repo_stress?.iorb;
        if (!sofr || !iorb) return [];
        return sofr.map((s, i) => {
            const spread = s - (iorb[i] || 0);
            if (!Number.isFinite(spread)) return "neutral";
            if (spread >= 0) return "bullish";
            if (spread < -0.05) return "bearish";
            return "neutral";
        });
    })();
    $: repoStressLayout = {
        shapes: createRegimeShapes(
            repoStressData[0]?.x || [],
            dashboardData.dates,
            repoRegimeSignals,
            darkMode,
        ),
        yaxis: { title: "Percent (%)", dtick: 1.0, autorange: true },
    };

    // Credit indicators configuration
    $: creditIndicators = [
        {
            id: "hy",
            name: "HY Spread Contrast",
            data: hyZData,
            range: hyRange,
            setRange: (r) => (hyRange = r),
            bank: "HY_SPREAD",
            descKey: "hy_spread",
            layout: hyLayout,
        },
        {
            id: "ig",
            name: "IG Spread Contrast",
            data: igZData,
            range: igRange,
            setRange: (r) => (igRange = r),
            bank: "IG_SPREAD",
            descKey: "ig_spread",
            layout: igLayout,
        },
        {
            id: "nfci_credit",
            name: "NFCI Credit Contrast",
            data: nfciCreditZData,
            range: nfciCreditRange,
            setRange: (r) => (nfciCreditRange = r),
            bank: "NFCI",
            descKey: "nfci_credit",
            layout: nfciCreditLayout,
        },
        {
            id: "nfci_risk",
            name: "NFCI Risk Contrast",
            data: nfciRiskZData,
            range: nfciRiskRange,
            setRange: (r) => (nfciRiskRange = r),
            bank: "NFCI",
            descKey: "nfci_risk",
            layout: nfciRiskLayout,
        },
        {
            id: "lending",
            name: "Lending Standards Contrast",
            data: lendingZData,
            range: lendingRange,
            setRange: (r) => (lendingRange = r),
            bank: "LENDING_STD",
            descKey: "lending",
            layout: lendingLayout,
        },
        {
            id: "vix_z",
            name: "VIX Contrast (Z-Score)",
            data: vixZData,
            range: vixRange,
            setRange: (r) => (vixRange = r),
            bank: "VIX",
            descKey: "vix",
            layout: vixLayout,
        },
    ];

    // --- Backend Signals Integration ---
    $: signals = dashboardData?.signals || {};

    const signalConfig = [
        { id: "cli", label: "CLI Stance" },
        { id: "hy", label: "HY Momentum" },
        { id: "ig", label: "IG Momentum" },
        { id: "nfci_credit", label: "Credit (NFCI)" },
        { id: "nfci_risk", label: "Risk (NFCI)" },
        { id: "lending", label: "Lending (SLOOS)" },
        { id: "vix", label: "Volatility (VIX)" },
        { id: "tips", label: "Macro (TIPS)" },
        { id: "repo", label: "Liquidity (SOFR)" },
    ];

    const getStatusLabel = (state) => {
        if (state === "bullish") return "BULLISH";
        if (state === "bearish") return "BEARISH";
        if (state === "warning") return "WARNING";
        return "NEUTRAL";
    };

    $: bullCount = Object.values(signals).filter(
        (s) => s.state === "bullish",
    ).length;
    $: bearCount = Object.values(signals).filter(
        (s) => s.state === "bearish",
    ).length;
    $: aggregateState =
        bullCount > bearCount + 1
            ? "bullish"
            : bearCount > bullCount + 1
              ? "bearish"
              : "neutral";
</script>

<!-- Header with Aggregate Stance -->
<div class="risk-header-summary">
    <div class="regime-badge bg-{aggregateState}">
        <span style="font-size: 1.2rem;"
            >{aggregateState === "bullish"
                ? "🚀"
                : aggregateState === "bearish"
                  ? "⚠️"
                  : "⚖️"}</span
        >
        {aggregateState.toUpperCase()} STANCE
    </div>
    <div class="stance-details">
        {bullCount} Bullish | {bearCount} Bearish | {signalConfig.length} Factors
    </div>
</div>

<div class="main-charts">
    <div class="grid-2">
        <!-- TIPS / Inflation Expectations Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_inflation_exp ||
                        "Inflation Expectations (TIPS Market)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={tipsRange}
                        onRangeChange={(r) => (tipsRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("TIPS_BREAKEVEN")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.tips || "Breakeven, Real Rate, and 5Y5Y Forward."}
            </p>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={tipsData}
                    layout={tipsLayoutWithBands}
                />
            </div>

            {#if signals.tips}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">Macro Signal (TIPS)</div>
                        <div class="signal-status text-{signals.tips.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(signals.tips.state)}
                        </div>
                        <div
                            class="signal-value"
                            style="font-size: 0.8rem; display: flex; gap: 12px;"
                        >
                            <span
                                >RR Δ: <b
                                    class={signals.tips.rr_delta > 0.4
                                        ? "text-bearish"
                                        : "text-neutral"}
                                    >{signals.tips.rr_delta > 0
                                        ? "+"
                                        : ""}{signals.tips.rr_delta}</b
                                ></span
                            >
                            <span
                                >BE Δ: <b
                                    class={signals.tips.be_delta > 0.15
                                        ? "text-bullish"
                                        : "text-neutral"}
                                    >{signals.tips.be_delta > 0
                                        ? "+"
                                        : ""}{signals.tips.be_delta}</b
                                ></span
                            >
                            <span
                                >5Y5Y Δ: <b
                                    class={signals.tips.fwd_delta < -0.15
                                        ? "text-warning"
                                        : "text-neutral"}
                                    >{signals.tips.fwd_delta > 0
                                        ? "+"
                                        : ""}{signals.tips.fwd_delta}</b
                                ></span
                            >
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- CLI Aggregate Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>Credit Liquidity Index (CLI Aggregate)</h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={cliRange}
                        onRangeChange={(r) => (cliRange = r)}
                    />
                    <span class="last-date"
                        >Last Data: {getLastDate("NFCI")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.cli ||
                    "Aggregates credit conditions, volatility, and lending."}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cliData} layout={cliLayout} />
            </div>

            {#if signals.cli}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">CLI Stance</div>
                        <div class="signal-status text-{signals.cli.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(signals.cli.state)}
                        </div>
                        <div class="signal-value">
                            Score: {signals.cli.value > 0 ? "+" : ""}{signals
                                .cli.value}
                            <span style="margin-left: 8px; opacity: 0.7;"
                                >(Momentum: {signals.cli.momentum > 0
                                    ? "+"
                                    : ""}{signals.cli.momentum})</span
                            >
                        </div>
                    </div>
                </div>
            {/if}
        </div>

        <!-- Repo Stress Chart -->
        <div class="chart-card">
            <div class="chart-header">
                <h3>
                    {translations.chart_repo_stress ||
                        "Repo Market Stress (SOFR vs IORB)"}
                </h3>
                <div class="header-controls">
                    <TimeRangeSelector
                        selectedRange={repoStressRange}
                        onRangeChange={(r) => (repoStressRange = r)}
                    />
                    <span class="last-date"
                        >{translations.last_data || "Last Data:"}
                        {getLastDate("SOFR")}</span
                    >
                </div>
            </div>
            <p class="chart-description">
                {translations.repo_stress ||
                    "SOFR vs IORB spread indicates funding stress."}
            </p>
            <div class="chart-content" style="height: 300px;">
                <Chart
                    {darkMode}
                    data={repoStressData}
                    layout={repoStressLayout}
                />
            </div>

            <!-- Compact Metrics Sidebar Replacement -->
            <div
                class="metrics-section"
                style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;"
            >
                <div class="metrics-table-container">
                    <table class="metrics-table compact">
                        <thead>
                            <tr>
                                <th>Rate</th>
                                <th>Value</th>
                                <th>Spread/Signal</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="color: #f59e0b; font-weight: 600;"
                                    >SOFR</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.sofr,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                                <td
                                    rowspan="2"
                                    style="vertical-align: middle; text-align: center; background: rgba(0,0,0,0.1); border-radius: 8px;"
                                >
                                    <div
                                        class:text-bullish={signals.repo
                                            ?.state === "bullish"}
                                        class:text-bearish={signals.repo
                                            ?.state === "bearish"}
                                        style="font-weight: 800; font-size: 1.1rem;"
                                    >
                                        {(
                                            (signals.repo?.value ?? 0) * 100
                                        ).toFixed(1)} bps
                                    </div>
                                    <div
                                        style="font-size: 14px; margin-top: 4px;"
                                    >
                                        {#if signals.repo?.state === "bullish" || signals.repo?.state === "neutral"}
                                            ✅ OK
                                        {:else}
                                            ⚠️ STRESS
                                        {/if}
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="color: #8b5cf6; font-weight: 600;"
                                    >IORB</td
                                >
                                <td
                                    >{(
                                        getLatestValue(
                                            dashboardData.repo_stress?.iorb,
                                        ) ?? 0
                                    ).toFixed(2)}%</td
                                >
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Individual Indicators -->
        {#each creditIndicators as item}
            <div class="chart-card">
                <div class="chart-header">
                    <h3>{item.name}</h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={item.range}
                            onRangeChange={item.setRange}
                        />
                        <span class="last-date"
                            >Last: {getLastDate(item.bank)}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {translations[item.descKey] || ""}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={item.data} layout={item.layout} />
                </div>

                {#if signals[item.id === "vix_z" ? "vix" : item.id]}
                    {@const s = signals[item.id === "vix_z" ? "vix" : item.id]}
                    <div
                        class="metrics-section"
                        style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                    >
                        <div
                            class="signal-item"
                            style="background: rgba(0,0,0,0.15); border: none;"
                        >
                            <div class="signal-label">{item.name} Signal</div>
                            <div class="signal-status text-{s.state}">
                                <span class="signal-dot"></span>
                                {getStatusLabel(s.state)}
                            </div>
                            <div class="signal-value">
                                Z-Score: {s.value > 0 ? "+" : ""}{s.value}
                            </div>
                        </div>
                    </div>
                {/if}
            </div>
        {/each}
    </div>
</div>

<!-- ROC Section -->
<div class="roc-section">
    <div class="roc-card">
        <h4>Pulsar Momentum (ROC)</h4>
        <div class="metrics-table-container">
            <div class="roc-grid">
                <div class="roc-row header">
                    <div class="roc-col">Factor</div>
                    <div class="roc-col">1M</div>
                    <div class="roc-col">3M</div>
                    <div class="roc-col">6M</div>
                    <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">Global GLI</div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "1M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "3M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "6M").toFixed(
                            2,
                        )}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.gli?.rocs,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(dashboardData.gli?.rocs, "1Y").toFixed(
                            2,
                        )}%
                    </div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">US Net Liq</div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "3M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "6M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.us_net_liq_rocs,
                            "1Y",
                        ).toFixed(2)}%
                    </div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">Fed Assets</div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "3M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "6M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.fed,
                            "1Y",
                        ).toFixed(2)}%
                    </div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">PBoC Assets</div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "3M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "3M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "3M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "6M",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "6M",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "6M",
                        ).toFixed(2)}%
                    </div>
                    <div
                        class="roc-col"
                        class:plus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1Y",
                        ) > 0}
                        class:minus={getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1Y",
                        ) < 0}
                    >
                        {getLatestROC(
                            dashboardData.bank_rocs?.pboc,
                            "1Y",
                        ).toFixed(2)}%
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
