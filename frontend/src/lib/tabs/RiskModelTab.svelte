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

    function createPercentileBands(
        darkMode,
        { bullishPct = 70, bearishPct = 30, invert = false } = {},
    ) {
        const greenColor = darkMode
            ? "rgba(16, 185, 129, 0.10)"
            : "rgba(16, 185, 129, 0.12)";
        const redColor = darkMode
            ? "rgba(239, 68, 68, 0.10)"
            : "rgba(239, 68, 68, 0.12)";

        // For inverted series (VIX, spreads): low = green
        const topColor = invert ? redColor : greenColor;
        const bottomColor = invert ? greenColor : redColor;

        return [
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: bullishPct,
                y1: 100,
                fillcolor: topColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: bearishPct,
                fillcolor: bottomColor,
                line: { width: 0 },
                layer: "below",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 50,
                y1: 50,
                line: {
                    color: darkMode
                        ? "rgba(148, 163, 184, 0.4)"
                        : "rgba(100, 116, 139, 0.4)",
                    width: 1,
                    dash: "dot",
                },
                layer: "below",
            },
        ];
    }

    const PERCENTILE_CONFIG = {
        cli: { bullishPct: 70, bearishPct: 30, invert: false },
        hy_spread: { bullishPct: 30, bearishPct: 70, invert: true },
        ig_spread: { bullishPct: 30, bearishPct: 70, invert: true },
        nfci_credit: { bullishPct: 30, bearishPct: 60, invert: true },
        nfci_risk: { bullishPct: 30, bearishPct: 80, invert: true },
        lending: { bullishPct: 40, bearishPct: 60, invert: true },
        vix: { bullishPct: 25, bearishPct: 90, invert: true },
        move: { bullishPct: 30, bearishPct: 80, invert: true },
        fx_vol: { bullishPct: 30, bearishPct: 70, invert: true },
        tips_real: { bullishPct: 30, bearishPct: 75, invert: true },
    };

    // Chart data - Z-Score
    export let cliData = [];
    export let cliPercentileData = [];
    export let hyZData = [];
    export let hyPctData = [];
    export let igZData = [];
    export let igPctData = [];
    export let nfciCreditZData = [];
    export let nfciCreditPctData = [];
    export let nfciRiskZData = [];
    export let nfciRiskPctData = [];
    export let lendingZData = [];
    export let lendingPctData = [];
    export let vixZData = [];
    export let vixPctData = [];
    export let moveZData = [];
    export let movePctData = [];
    export let fxVolZData = [];
    export let fxVolPctData = [];
    export let tipsData = [];
    export let tipsLayout = {};
    export let repoStressData = [];

    // Raw data props (original values without transformation)
    export let vixRawData = [];
    export let moveRawData = [];
    export let fxVolRawData = [];
    export let hyRawData = [];
    export let igRawData = [];
    export let nfciCreditRawData = [];
    export let nfciRiskRawData = [];
    export let lendingRawData = [];

    // View mode per chart: 'zscore', 'percentile', or 'raw'
    let cliViewMode = "zscore";
    let hyViewMode = "zscore";
    let igViewMode = "zscore";
    let nfciCreditViewMode = "zscore";
    let nfciRiskViewMode = "zscore";
    let lendingViewMode = "zscore";
    let vixViewMode = "zscore";
    let moveViewMode = "zscore";
    let fxVolViewMode = "zscore";

    // Last date lookup function
    export let getLastDate = (bank) => "N/A";
    export let getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;
    export let getLatestROC = (rocs, period) =>
        rocs?.[period]?.[rocs?.[period]?.length - 1] ?? 0;

    // Signal justification text - uses translation keys
    function getSignalReason(signalKey, state) {
        // Map signalKey to translation prefix
        const keyMap = {
            hy_spread: "hy",
            ig_spread: "ig",
            nfci_credit: "nfci_credit",
            nfci_risk: "nfci_risk",
            lending: "lending",
            vix: "vix",
            cli: "cli",
            repo: "repo",
            tips: "tips",
        };
        const prefix = keyMap[signalKey] || signalKey;
        const translationKey = `signal_${prefix}_${state}`;
        return (
            translations[translationKey] ||
            translations[`signal_${prefix}_neutral`] ||
            "—"
        );
    }

    // Time range states - managed locally
    export let cliRange = "ALL";
    export let hyRange = "ALL";
    export let igRange = "ALL";
    export let nfciCreditRange = "ALL";
    export let nfciRiskRange = "ALL";
    export let lendingRange = "ALL";
    export let vixRange = "ALL";
    export let moveRange = "ALL";
    export let fxVolRange = "ALL";
    export let tipsRange = "ALL";
    export let repoStressRange = "ALL";

    // Z-Score Layouts (using original createZScoreBands from line 20)
    $: hyZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: igZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciCreditZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: nfciRiskZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: lendingZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: vixZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: moveZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };
    $: fxVolZLayout = {
        shapes: createZScoreBands(darkMode),
        yaxis: { title: "Z-Score", dtick: 2.5, autorange: true },
    };

    // Percentile Layouts (when viewMode is 'percentile')
    $: hyLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.hy_spread),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: igLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.ig_spread),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: nfciCreditLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.nfci_credit),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: nfciRiskLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.nfci_risk),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: lendingLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.lending),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: vixLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.vix),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: moveLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.move),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: fxVolLayout = {
        shapes: createPercentileBands(darkMode, PERCENTILE_CONFIG.fx_vol),
        yaxis: {
            title: "Percentile",
            range: [-5, 105],
            dtick: 25,
            autorange: false,
        },
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };

    // Raw Layouts (no bands, just autorange y-axis)
    const rawLayoutBase = {
        shapes: [],
        margin: { l: 50, r: 20, t: 20, b: 40 },
    };
    $: hyRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "HY Spread (bps)", autorange: true },
    };
    $: igRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "IG Spread (bps)", autorange: true },
    };
    $: nfciCreditRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "NFCI Credit", autorange: true },
    };
    $: nfciRiskRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "NFCI Risk", autorange: true },
    };
    $: lendingRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "Net % Tightening", autorange: true },
    };
    $: vixRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "VIX Level", autorange: true },
    };
    $: moveRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "MOVE Index", autorange: true },
    };
    $: fxVolRawLayout = {
        ...rawLayoutBase,
        yaxis: { title: "DXY Realized Vol (%)", autorange: true },
    };

    // CLI Chart - use cliData for Z-score, or cliPercentileData for percentile
    $: cliChartData =
        cliViewMode === "percentile" ? cliPercentileData : cliData;
    $: cliLayout =
        cliViewMode === "percentile"
            ? {
                  shapes: createPercentileBands(
                      darkMode,
                      PERCENTILE_CONFIG.cli,
                  ),
                  yaxis: {
                      title: "Percentile",
                      range: [0, 100],
                      dtick: 25,
                  },
              }
            : {
                  shapes: createZScoreBands(darkMode),
                  yaxis: { title: "CLI Index", dtick: 2.5, autorange: true },
              };

    // TIPS Composite Regime
    $: tipsRegimeSignals = (() => {
        const dates = dashboardData.dates;
        const be = dashboardData.tips?.breakeven;
        const rr = dashboardData.tips?.real_rate;
        const fwd = dashboardData.tips?.fwd_5y5y;
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
        yaxis: {
            ...tipsLayout.yaxis,
            title: "Breakeven & 5Y5Y (%)",
            dtick: 0.5,
            autorange: true,
        },
        yaxis2: {
            ...tipsLayout.yaxis2,
            title: "Real Rate (%)",
            dtick: 0.5,
            autorange: true,
            side: "right",
            overlaying: "y",
        },
        showlegend: false,
        margin: { l: 60, r: 60, t: 20, b: 40 },
    };

    // Computed TIPS signal from frontend data (fallback if backend signal_metrics.tips not populated)
    $: computedTipsSignal = (() => {
        const be = dashboardData.tips?.breakeven;
        const rr = dashboardData.tips?.real_rate;
        if (!be || !rr || be.length < 63) return null;

        const latestBE = be[be.length - 1];
        const latestRR = rr[rr.length - 1];
        const beAvg =
            be.slice(-252).reduce((a, b) => a + b, 0) /
            Math.min(252, be.length);
        const rrAvg =
            rr.slice(-252).reduce((a, b) => a + b, 0) /
            Math.min(252, rr.length);

        const beHigh = latestBE > beAvg * 1.1;
        const rrHigh = latestRR > rrAvg + 0.5;
        const beLow = latestBE < beAvg * 0.9;
        const rrLow = latestRR < rrAvg - 0.3;

        let state = "neutral";
        let reasonKey = "signal_tips_neutral";

        if (beHigh && rrHigh) {
            state = "warning";
            reasonKey = "signal_tips_warning";
        } else if (beHigh && !rrHigh) {
            state = "bullish";
            reasonKey = "signal_tips_bullish";
        } else if (rrHigh && !beHigh) {
            state = "bearish";
            reasonKey = "signal_tips_bearish";
        } else if (beLow && rrLow) {
            state = "neutral";
            reasonKey = "signal_tips_disinflation";
        }

        return { state, value: latestRR, valueBE: latestBE, reasonKey };
    })();

    // Repo Regime - corrected logic
    // SOFR ≈ IORB (within 5bps) = Normal/Bullish (adequate liquidity)
    // SOFR >> IORB (>10bps above) = Bearish (liquidity stress, like Sept 2019)
    // SOFR << IORB (significantly below) = Warning (excess liquidity, unusual)
    $: repoRegimeSignals = (() => {
        const sofr = dashboardData.repo_stress?.sofr;
        const iorb = dashboardData.repo_stress?.iorb;
        if (!sofr || !iorb) return [];
        return sofr.map((s, i) => {
            const spread = (s - (iorb[i] || 0)) * 100; // Convert to bps
            if (!Number.isFinite(spread)) return "neutral";
            if (spread > 10) return "bearish"; // SOFR >> IORB = liquidity stress
            if (spread < -5) return "warning"; // SOFR << IORB = excess liquidity (unusual)
            if (Math.abs(spread) <= 5) return "bullish"; // Normal range = healthy
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

    // Credit indicators configuration - each chart has independent viewMode
    $: creditIndicators = [
        {
            id: "hy",
            name: translations.credit_hy_name || "HY Spread Contrast",
            signalKey: "hy_spread",
            desc:
                translations.credit_hy_desc ||
                "High Yield spread vs Treasury. Higher = Risk-off, Lower = Risk-on.",
            data:
                hyViewMode === "raw"
                    ? hyRawData
                    : hyViewMode === "percentile"
                      ? hyPctData
                      : hyZData,
            range: hyRange,
            setRange: (r) => (hyRange = r),
            bank: "HY_SPREAD",
            layout:
                hyViewMode === "raw"
                    ? hyRawLayout
                    : hyViewMode === "percentile"
                      ? hyLayout
                      : hyZLayout,
            viewMode: hyViewMode,
            setViewMode: (m) => (hyViewMode = m),
        },
        {
            id: "ig",
            name: translations.credit_ig_name || "IG Spread Contrast",
            signalKey: "ig_spread",
            desc:
                translations.credit_ig_desc ||
                "Investment Grade spread vs Treasury. Higher = Stress, Lower = Calm.",
            data:
                igViewMode === "raw"
                    ? igRawData
                    : igViewMode === "percentile"
                      ? igPctData
                      : igZData,
            range: igRange,
            setRange: (r) => (igRange = r),
            bank: "IG_SPREAD",
            layout:
                igViewMode === "raw"
                    ? igRawLayout
                    : igViewMode === "percentile"
                      ? igLayout
                      : igZLayout,
            viewMode: igViewMode,
            setViewMode: (m) => (igViewMode = m),
        },
        {
            id: "nfci_credit",
            name:
                translations.credit_nfci_credit_name || "NFCI Credit Contrast",
            signalKey: "nfci_credit",
            desc:
                translations.credit_nfci_credit_desc ||
                "Fed Chicago NFCI Credit subindex. Positive = Tighter, Negative = Easier.",
            data:
                nfciCreditViewMode === "raw"
                    ? nfciCreditRawData
                    : nfciCreditViewMode === "percentile"
                      ? nfciCreditPctData
                      : nfciCreditZData,
            range: nfciCreditRange,
            setRange: (r) => (nfciCreditRange = r),
            bank: "NFCI_CREDIT",
            layout:
                nfciCreditViewMode === "raw"
                    ? nfciCreditRawLayout
                    : nfciCreditViewMode === "percentile"
                      ? nfciCreditLayout
                      : nfciCreditZLayout,
            viewMode: nfciCreditViewMode,
            setViewMode: (m) => (nfciCreditViewMode = m),
        },
        {
            id: "nfci_risk",
            name: translations.credit_nfci_risk_name || "NFCI Risk Contrast",
            signalKey: "nfci_risk",
            desc:
                translations.credit_nfci_risk_desc ||
                "Fed Chicago NFCI Risk subindex. Positive = Higher risk, Negative = Lower risk.",
            data:
                nfciRiskViewMode === "raw"
                    ? nfciRiskRawData
                    : nfciRiskViewMode === "percentile"
                      ? nfciRiskPctData
                      : nfciRiskZData,
            range: nfciRiskRange,
            setRange: (r) => (nfciRiskRange = r),
            bank: "NFCI_RISK",
            layout:
                nfciRiskViewMode === "raw"
                    ? nfciRiskRawLayout
                    : nfciRiskViewMode === "percentile"
                      ? nfciRiskLayout
                      : nfciRiskZLayout,
            viewMode: nfciRiskViewMode,
            setViewMode: (m) => (nfciRiskViewMode = m),
        },
        {
            id: "lending",
            name:
                translations.credit_lending_name ||
                "Lending Standards Contrast",
            signalKey: "lending",
            desc:
                translations.credit_lending_desc ||
                "Fed SLOOS survey. Positive = Tighter lending, Negative = Easier lending.",
            data:
                lendingViewMode === "raw"
                    ? lendingRawData
                    : lendingViewMode === "percentile"
                      ? lendingPctData
                      : lendingZData,
            range: lendingRange,
            setRange: (r) => (lendingRange = r),
            bank: "LENDING_STD",
            layout:
                lendingViewMode === "raw"
                    ? lendingRawLayout
                    : lendingViewMode === "percentile"
                      ? lendingLayout
                      : lendingZLayout,
            viewMode: lendingViewMode,
            setViewMode: (m) => (lendingViewMode = m),
        },
        {
            id: "vix",
            name: translations.credit_vix_name || "VIX Contrast",
            signalKey: "vix",
            desc:
                translations.credit_vix_desc ||
                "CBOE Volatility Index. Higher = Fear/Stress, Lower = Complacency.",
            data:
                vixViewMode === "raw"
                    ? vixRawData
                    : vixViewMode === "percentile"
                      ? vixPctData
                      : vixZData,
            range: vixRange,
            setRange: (r) => (vixRange = r),
            bank: "VIX",
            layout:
                vixViewMode === "raw"
                    ? vixRawLayout
                    : vixViewMode === "percentile"
                      ? vixLayout
                      : vixZLayout,
            viewMode: vixViewMode,
            setViewMode: (m) => (vixViewMode = m),
        },
        {
            id: "move",
            name: translations.indicator_move_name || "MOVE Index Contrast",
            signalKey: "move",
            desc:
                translations.indicator_move_desc ||
                "ICE BofA MOVE Index. Measures implied bond volatility. Higher = Stress.",
            data:
                moveViewMode === "raw"
                    ? moveRawData
                    : moveViewMode === "percentile"
                      ? movePctData
                      : moveZData,
            range: moveRange,
            setRange: (r) => (moveRange = r),
            bank: "MOVE",
            layout:
                moveViewMode === "raw"
                    ? moveRawLayout
                    : moveViewMode === "percentile"
                      ? moveLayout
                      : moveZLayout,
            viewMode: moveViewMode,
            setViewMode: (m) => (moveViewMode = m),
        },
        {
            id: "fx_vol",
            name:
                translations.indicator_fx_vol_name || "DXY Realized Volatility",
            signalKey: "fx_vol",
            desc:
                translations.indicator_fx_vol_desc ||
                "21-day realized volatility of the US Dollar Index. Measures currency market stress.",
            data:
                fxVolViewMode === "raw"
                    ? fxVolRawData
                    : fxVolViewMode === "percentile"
                      ? fxVolPctData
                      : fxVolZData,
            range: fxVolRange,
            setRange: (r) => (fxVolRange = r),
            bank: "FX_VOL",
            layout:
                fxVolViewMode === "raw"
                    ? fxVolRawLayout
                    : fxVolViewMode === "percentile"
                      ? fxVolLayout
                      : fxVolZLayout,
            viewMode: fxVolViewMode,
            setViewMode: (m) => (fxVolViewMode = m),
        },
    ];

    // Unified signal derived from signal_metrics
    $: signalsFromMetrics = dashboardData.signal_metrics || {};

    const signalConfig = [
        { id: "cli", label: "CLI Stance" },
        { id: "hy", label: "HY Momentum" },
        { id: "ig", label: "IG Momentum" },
        { id: "nfci_credit", label: "Credit (NFCI)" },
        { id: "nfci_risk", label: "Risk (NFCI)" },
        { id: "lending", label: "Lending (SLOOS)" },
        { id: "vix", label: "Volatility (VIX)" },
        { id: "move", label: "MOVE Index" },
        { id: "fx_vol", label: "FX Volatility" },
        { id: "tips", label: "Macro (TIPS)" },
        { id: "repo", label: "Liquidity (SOFR)" },
    ];

    function getStatusLabel(state) {
        if (!state) return translations.status_neutral || "NEUTRAL";
        const key = `status_${state.toLowerCase()}`;
        return translations[key] || state.toUpperCase();
    }

    $: bullCount = Object.values(signalsFromMetrics).filter(
        (s) => s.latest?.state === "bullish",
    ).length;
    $: bearCount = Object.values(signalsFromMetrics).filter(
        (s) => s.latest?.state === "bearish",
    ).length;
    $: aggregateState =
        bullCount > bearCount + 1
            ? "bullish"
            : bearCount > bullCount + 1
              ? "bearish"
              : "neutral";
</script>

<!-- Header with Aggregate Stance & View Mode Toggle -->
<div class="risk-header-summary">
    <div class="regime-badge bg-{aggregateState}">
        <span style="font-size: 1.2rem;"
            >{aggregateState === "bullish"
                ? "🚀"
                : aggregateState === "bearish"
                  ? "⚠️"
                  : "⚖️"}</span
        >
        {getStatusLabel(aggregateState)}
        {translations.risk_stance || "STANCE"}
    </div>
    <div class="stance-details">
        {bullCount}
        {translations.risk_bullish || "Bullish"} | {bearCount}
        {translations.risk_bearish || "Bearish"} | {signalConfig.length}
        {translations.risk_factors || "Factors"}
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
            <div class="chart-legend">
                <span class="legend-item">
                    <span class="legend-dot" style="background: #f59e0b"></span>
                    <span class="legend-label"
                        >{translations.tips_breakeven || "Breakeven"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_be_desc ||
                            "Inflation expectations"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #3b82f6"></span>
                    <span class="legend-label"
                        >{translations.tips_real_rate || "Real Rate"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_rr_desc || "Cost of money"}</span
                    >
                </span>
                <span class="legend-item">
                    <span class="legend-dot" style="background: #10b981"></span>
                    <span class="legend-label"
                        >{translations.tips_fwd || "5Y5Y Forward"}</span
                    >
                    <span class="legend-desc"
                        >{translations.tips_fwd_desc ||
                            "Long-term anchor"}</span
                    >
                </span>
            </div>
            <div class="chart-content">
                <Chart
                    {darkMode}
                    data={tipsData}
                    layout={tipsLayoutWithBands}
                />
            </div>

            {#if signalsFromMetrics.tips?.latest}
                {@const s = signalsFromMetrics.tips.latest}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {getStatusLabel(s.state)}
                        </div>
                        <div class="signal-value">
                            {translations.repo_value || "Value"}: {s.value?.toFixed(
                                2,
                            ) ?? "N/A"} | {translations.percentile ||
                                "Percentile"}: P{s.percentile?.toFixed(0) ??
                                "N/A"}
                        </div>
                    </div>
                </div>
            {:else if computedTipsSignal}
                {@const s = computedTipsSignal}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-{s.state}">
                            <span class="signal-dot"></span>
                            {s.state === "warning"
                                ? "⚠️ WARNING"
                                : getStatusLabel(s.state)}
                        </div>
                        <div
                            class="signal-value"
                            style="display: flex; gap: 12px;"
                        >
                            <span>BE: {s.valueBE?.toFixed(2) ?? "N/A"}%</span>
                            <span>RR: {s.value?.toFixed(2) ?? "N/A"}%</span>
                        </div>
                        <div
                            class="signal-reason"
                            style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                        >
                            {translations[s.reasonKey] || s.reasonKey}
                        </div>
                    </div>
                </div>
            {:else}
                <div
                    class="metrics-section"
                    style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                >
                    <div
                        class="signal-item"
                        style="background: rgba(0,0,0,0.15); border: none;"
                    >
                        <div class="signal-label">
                            {translations.tips_signal_label ||
                                "TIPS Macro Signal"}
                        </div>
                        <div class="signal-status text-neutral">
                            <span class="signal-dot"></span>
                            {translations.refresh_data || "Loading..."}
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
                    <div class="view-mode-toggle">
                        <button
                            class:active={cliViewMode === "zscore"}
                            on:click={() => (cliViewMode = "zscore")}>Z</button
                        >
                        <button
                            class:active={cliViewMode === "percentile"}
                            on:click={() => (cliViewMode = "percentile")}
                            >%</button
                        >
                    </div>
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
                {cliViewMode === "percentile"
                    ? translations.cli_desc_ext ||
                      "↑ CLI = Easier credit (bullish) ↓ Contraction = Tighter (bearish)"
                    : ""}
            </p>
            <div class="chart-content">
                <Chart {darkMode} data={cliChartData} layout={cliLayout} />
            </div>

            <!-- Signal Box -->
            {#if dashboardData.signal_metrics?.cli?.latest}
                {@const s = dashboardData.signal_metrics.cli.latest}
                <div class="signal-box">
                    <div class="signal-header">
                        {translations.cli_stance || "CLI STANCE"}
                    </div>
                    <div class="signal-badge {s.state}">
                        {s.state === "bullish"
                            ? "🟢"
                            : s.state === "bearish"
                              ? "🔴"
                              : "⚪"}
                        {getStatusLabel(s.state)}
                    </div>
                    <div class="signal-details">
                        {translations.percentile || "Percentile"}: {s.percentile?.toFixed(
                            0,
                        ) ?? "N/A"}
                        <span class="signal-hint">
                            ({s.percentile >= 70
                                ? translations.cli_top_30 || "Top 30%"
                                : s.percentile <= 30
                                  ? translations.cli_bottom_30 || "Bottom 30%"
                                  : translations.cli_mid_range ||
                                    "Middle range"})
                        </span>
                    </div>
                    <div
                        class="signal-reason"
                        style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                    >
                        {getSignalReason("cli", s.state)}
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
                                <th>{translations.repo_rate || "Rate"}</th>
                                <th>{translations.repo_value || "Value"}</th>
                                <th
                                    >{translations.repo_spread_sig ||
                                        "Spread/Signal"}</th
                                >
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
                                        class:text-bullish={signalsFromMetrics
                                            .repo?.latest?.state === "bullish"}
                                        class:text-bearish={signalsFromMetrics
                                            .repo?.latest?.state === "bearish"}
                                        style="font-weight: 800; font-size: 1.1rem;"
                                    >
                                        {(
                                            (getLatestValue(
                                                dashboardData.repo_stress?.sofr,
                                            ) -
                                                getLatestValue(
                                                    dashboardData.repo_stress
                                                        ?.iorb,
                                                )) *
                                            100
                                        ).toFixed(1)} bps
                                    </div>
                                    <div
                                        style="font-size: 14px; margin-top: 4px;"
                                    >
                                        {#if signalsFromMetrics.repo?.latest?.state === "bullish" || signalsFromMetrics.repo?.latest?.state === "neutral"}
                                            ✅ {translations.status_ok || "OK"}
                                        {:else}
                                            ⚠️ {translations.status_stress ||
                                                "STRESS"}
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
                        <div class="view-mode-toggle">
                            <button
                                class:active={item.viewMode === "zscore"}
                                on:click={() => item.setViewMode("zscore")}
                                title="Z-Score">Z</button
                            >
                            <button
                                class:active={item.viewMode === "percentile"}
                                on:click={() => item.setViewMode("percentile")}
                                title="Percentile">%</button
                            >
                            <button
                                class:active={item.viewMode === "raw"}
                                on:click={() => item.setViewMode("raw")}
                                title="Raw Values">📊</button
                            >
                        </div>
                        <TimeRangeSelector
                            selectedRange={item.range}
                            onRangeChange={item.setRange}
                        />
                        <span class="last-date"
                            >{translations.last || "Last"}: {getLastDate(
                                item.bank,
                            )}</span
                        >
                    </div>
                </div>
                <p class="chart-description">
                    {item.desc}
                </p>
                <div class="chart-content">
                    <Chart {darkMode} data={item.data} layout={item.layout} />
                </div>

                {#if signalsFromMetrics[item.signalKey]?.latest}
                    {@const s = signalsFromMetrics[item.signalKey].latest}
                    <div
                        class="metrics-section"
                        style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;"
                    >
                        <div
                            class="signal-item"
                            style="background: rgba(0,0,0,0.15); border: none;"
                        >
                            <div class="signal-label">
                                {translations.signal_status || "Signal Status"}
                            </div>
                            <div class="signal-status text-{s.state}">
                                <span class="signal-dot"></span>
                                {getStatusLabel(s.state)}
                            </div>
                            <div class="signal-value">
                                {translations.repo_value || "Value"}:
                                <b>{s.value?.toFixed(2) ?? "N/A"}</b>
                                | {translations.percentile || "Percentile"}:
                                <b>P{s.percentile?.toFixed(0) ?? "N/A"}</b>
                            </div>
                            <div
                                class="signal-reason"
                                style="font-size: 11px; color: rgba(255,255,255,0.55); margin-top: 6px; font-style: italic;"
                            >
                                {getSignalReason(item.signalKey, s.state)}
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
        <h4>{translations.roc_title || "Momentum Pulse (ROC)"}</h4>
        <div class="metrics-table-container">
            <div class="roc-grid">
                <div class="roc-row header">
                    <div class="roc-col">
                        {translations.roc_factor || "Factor"}
                    </div>
                    <div class="roc-col">1M</div>
                    <div class="roc-col">3M</div>
                    <div class="roc-col">6M</div>
                    <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_gli || "Global GLI"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.gli?.rocs,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_netliq || "US Net Liquidity"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.us_net_liq_rocs,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <!-- Core Banks -->
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_fed || "Fed Assets"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.fed,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_pboc || "PBoC Assets"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.bank_rocs?.pboc,
                                period,
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <!-- Macro Factors -->
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_cli || "Credit (CLI)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.cli?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.cli?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(dashboardData.cli?.rocs, period) ??
                                0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_real_rates || "Real Rates (5Y)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.tips?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.tips?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.tips?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_move || "MOVE Index (Bonds)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.move?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.move?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.move?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_fxvol || "FX Volatility (EVZ)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.fx_vol?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.fx_vol?.rocs,
                                period,
                            ) < 0}
                        >
                            {(
                                getLatestROC(
                                    dashboardData.fx_vol?.rocs,
                                    period,
                                ) ?? 0
                            ).toFixed(2)}%
                        </div>
                    {/each}
                </div>
                <div class="roc-row">
                    <div class="roc-col label">
                        {translations.indicator_vix || "Volatility (VIX)"}
                    </div>
                    {#each ["1M", "3M", "6M", "1Y"] as period}
                        <div
                            class="roc-col"
                            class:plus={getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            ) > 0}
                            class:minus={getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            ) < 0}
                        >
                            {getLatestROC(
                                dashboardData.vix?.rocs,
                                period,
                            )?.toFixed(2) ?? "0.00"}%
                        </div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    /* Toggle button styling */
    .view-mode-toggle {
        display: inline-flex;
        gap: 2px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 6px;
        padding: 2px;
        margin-right: 8px;
    }
    .view-mode-toggle button {
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 600;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        background: transparent;
        color: rgba(255, 255, 255, 0.5);
    }
    .view-mode-toggle button:hover {
        color: rgba(255, 255, 255, 0.8);
    }
    .view-mode-toggle button.active {
        background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
    }

    /* Signal Box for CLI */
    .signal-box {
        margin-top: 15px;
        padding: 12px 16px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .signal-header {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .signal-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 14px;
        font-weight: 700;
        padding: 4px 0;
    }
    .signal-badge.bullish {
        color: #10b981;
    }
    .signal-badge.bearish {
        color: #ef4444;
    }
    .signal-badge.neutral {
        color: #94a3b8;
    }
    .signal-details {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.7);
        margin-top: 4px;
    }
    .signal-hint {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.4);
        margin-left: 4px;
    }

    /* Signal Item - for credit indicators */
    .signal-item {
        padding: 10px 12px;
        border-radius: 6px;
    }
    .signal-label {
        font-size: 11px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .signal-status {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 700;
    }
    .signal-status.text-bullish {
        color: #10b981;
    }
    .signal-status.text-bearish {
        color: #ef4444;
    }
    .signal-status.text-neutral {
        color: #94a3b8;
    }
    .signal-status.text-warning {
        color: #f59e0b;
    }
    .signal-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    .signal-value {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 4px;
    }

    /* Chart description styling */
    .chart-description {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.65);
        line-height: 1.5;
        padding: 8px 12px;
        background: rgba(0, 0, 0, 0.15);
        border-radius: 6px;
        border-left: 3px solid rgba(99, 102, 241, 0.5);
        margin: 8px 0;
    }

    /* Chart legend styling */
    .chart-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        padding: 10px 14px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        margin: 8px 0 12px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .legend-label {
        font-size: 12px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
    }
    .legend-desc {
        font-size: 11px;
        color: rgba(255, 255, 255, 0.45);
        font-style: italic;
    }
</style>
