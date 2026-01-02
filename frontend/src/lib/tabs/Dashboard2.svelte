<script>
    /**
     * DashboardTab.svelte - QUANT EXECUTIVE DASHBOARD
     * Redesigned for actionable signals and data-first approach.
     * Focuses on regime status, stress levels, signal matrix, and early warnings.
     */
    import StatsCard from "../components/StatsCard.svelte";

    // Import stores directly
    import { dashboardData, latestStats } from "../../stores/dataStore";

    import {
        darkMode,
        language,
        currentTranslations,
    } from "../../stores/settingsStore";

    // Import utility functions
    import { getLatestValue } from "../utils/helpers.js";

    // Translations prop
    export let translations = {};

    // Load optimized params on mount
    import { onMount } from "svelte";

    let fomcCountdown = { days: 0, hours: 0, isToday: false };
    let nextFomcDate = null;
    let nextFomcHasSEP = false;

    onMount(() => {
        updateFomcCountdown();
        const interval = setInterval(updateFomcCountdown, 60000);
        return () => clearInterval(interval);
    });

    function updateFomcCountdown() {
        const meetings = $dashboardData.fed_forecasts?.fomc_dates || [];
        const now = new Date();

        for (const meeting of meetings) {
            const meetingDate = new Date(meeting.date + "T14:00:00-05:00");
            if (meetingDate > now) {
                nextFomcDate = meeting.date;
                nextFomcHasSEP = meeting.has_sep || false;
                // Capture probabilities for next meeting
                nextMeetingProbs = meeting.probs || null;
                const diff = meetingDate.getTime() - now.getTime();
                fomcCountdown = {
                    days: Math.floor(diff / (1000 * 60 * 60 * 24)),
                    hours: Math.floor(
                        (diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
                    ),
                    isToday: diff < 24 * 60 * 60 * 1000,
                };
                break;
            }
        }
    }

    // Next meeting probabilities
    let nextMeetingProbs = null;

    // Helper to calculate simple ROC
    function calcRoc(series, periods = 22) {
        if (!series || series.length < periods + 1) return null;
        const current = series[series.length - 1];
        const past = series[series.length - 1 - periods];
        if (current === null || past === null || past === 0) return null;
        return ((current - past) / Math.abs(past)) * 100;
    }

    // Helper to get delta (absolute change)
    function calcDelta(series, periods = 22) {
        if (!series || series.length < periods + 1) return null;
        const current = series[series.length - 1];
        const past = series[series.length - 1 - periods];
        if (current === null || past === null) return null;
        return current - past;
    }

    // ========================================================================
    // REGIME COMPUTATIONS
    // ========================================================================
    $: regimeScore = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr?.score?.length) return 50;
        const latest = mr.score[mr.score.length - 1];
        return latest ?? 50;
    })();

    $: regimeCode = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr?.regime_code?.length) return 0;
        return mr.regime_code[mr.regime_code.length - 1] ?? 0;
    })();

    $: regimeLabel =
        regimeCode === 1
            ? "BULLISH"
            : regimeCode === -1
              ? "BEARISH"
              : "NEUTRAL";
    $: regimeEmoji = regimeCode === 1 ? "🟢" : regimeCode === -1 ? "🔴" : "⚪";
    $: regimeColor =
        regimeCode === 1
            ? "bullish"
            : regimeCode === -1
              ? "bearish"
              : "neutral";

    $: regimeTrend = (() => {
        const accel = getLatestValue($dashboardData.flow_metrics?.gli_accel);
        if (accel === null || accel === undefined)
            return { label: "→", class: "neutral" };
        if (accel > 0.1) return { label: "↗️ Accelerating", class: "positive" };
        if (accel < -0.1)
            return { label: "↘️ Decelerating", class: "negative" };
        return { label: "→ Stable", class: "neutral" };
    })();

    $: regimeDiagnostics = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr)
            return { liquidity_z: 0, credit_z: 0, brakes_z: 0, total_z: 0 };
        const getLatest = (arr) => {
            if (!arr?.length) return 0;
            return arr[arr.length - 1] ?? 0;
        };
        return {
            liquidity_z: getLatest(mr.liquidity_z),
            credit_z: getLatest(mr.credit_z),
            brakes_z: getLatest(mr.brakes_z),
            total_z: getLatest(mr.total_z),
        };
    })();

    // Current Fed Funds Rate and SOFR (Effective Rate)
    $: currentFedRate = getLatestValue(
        $dashboardData.fed_forecasts?.fed_funds_rate,
    );
    $: currentSOFR = getLatestValue($dashboardData.repo_stress?.sofr);

    // ========================================================================
    // STRESS ANALYSIS
    // ========================================================================

    $: stressDimensions = [
        {
            id: "inflation",
            label: "🔥 Inflation",
            score: $dashboardData.stress_analysis?.inflation_stress?.score ?? 0,
            max: 7,
            level:
                $dashboardData.stress_analysis?.inflation_stress?.level ??
                "LOW",
        },
        {
            id: "liquidity",
            label: "💧 Liquidity",
            score: $dashboardData.stress_analysis?.liquidity_stress?.score ?? 0,
            max: 7,
            level:
                $dashboardData.stress_analysis?.liquidity_stress?.level ??
                "LOW",
        },
        {
            id: "credit",
            label: "💳 Credit",
            score: $dashboardData.stress_analysis?.credit_stress?.score ?? 0,
            max: 7,
            level:
                $dashboardData.stress_analysis?.credit_stress?.level ?? "LOW",
        },
        {
            id: "volatility",
            label: "🌪️ Volatility",
            score:
                $dashboardData.stress_analysis?.volatility_stress?.score ?? 0,
            max: 6,
            level:
                $dashboardData.stress_analysis?.volatility_stress?.level ??
                "LOW",
        },
    ];

    $: totalStress = stressDimensions.reduce((acc, d) => acc + d.score, 0);
    $: maxStress = 27;
    $: stressLevel =
        totalStress >= 15
            ? "CRITICAL"
            : totalStress >= 10
              ? "HIGH"
              : totalStress >= 5
                ? "MODERATE"
                : "LOW";
    $: stressColor =
        totalStress >= 15
            ? "#dc2626"
            : totalStress >= 10
              ? "#ea580c"
              : totalStress >= 5
                ? "#ca8a04"
                : "#16a34a";

    function getStressLevelClass(level) {
        if (level === "CRITICAL") return "critical";
        if (level === "HIGH") return "high";
        if (level === "MODERATE") return "moderate";
        return "low";
    }

    // ========================================================================
    // SIGNAL MATRIX
    // ========================================================================
    $: signalMetrics = $dashboardData.signal_metrics || {};

    $: signalMatrix = [
        { id: "cli", label: "CLI Stance", icon: "💳" },
        { id: "hy_spread", label: "HY Spread", icon: "📊" },
        { id: "ig_spread", label: "IG Spread", icon: "📈" },
        { id: "nfci_credit", label: "NFCI Credit", icon: "🏦" },
        { id: "nfci_risk", label: "NFCI Risk", icon: "⚠️" },
        { id: "lending", label: "Lending (SLOOS)", icon: "🏠" },
        { id: "vix", label: "VIX", icon: "📉" },
        { id: "move", label: "MOVE Index", icon: "📊" },
        { id: "fx_vol", label: "FX Volatility", icon: "💱" },
        { id: "tips_real_rate", label: "Real Rates", icon: "📈" },
        { id: "yield_curve", label: "Yield Curve", icon: "📐" },
    ].map((signal) => {
        const data = signalMetrics[signal.id]?.latest || {};
        const percentileSeries = signalMetrics[signal.id]?.percentile || [];
        // Calculate 1M ROC from percentile series if not provided
        let delta = data.delta_1m ?? data.roc_1m ?? null;
        if (delta === null && percentileSeries.length > 22) {
            const current = percentileSeries[percentileSeries.length - 1];
            const past = percentileSeries[percentileSeries.length - 1 - 22];
            if (current !== null && past !== null) {
                delta = current - past;
            }
        }
        return {
            ...signal,
            state: data.state || "neutral",
            value: data.value ?? data.z_score ?? null,
            percentile: data.percentile ?? null,
            delta,
        };
    });

    $: bullCount = signalMatrix.filter((s) => s.state === "bullish").length;
    $: bearCount = signalMatrix.filter((s) => s.state === "bearish").length;
    $: netSignal = bullCount - bearCount;
    $: aggregateSignal =
        netSignal > 2 ? "bullish" : netSignal < -2 ? "bearish" : "neutral";

    // ========================================================================
    // FLOW MOMENTUM
    // ========================================================================
    $: flowData = [
        {
            name: "Global Liquidity (GLI)",
            impulse4w: getLatestValue(
                $dashboardData.flow_metrics?.gli_impulse_4w,
            ),
            impulse13w: getLatestValue(
                $dashboardData.flow_metrics?.gli_impulse_13w,
            ),
            accel: getLatestValue($dashboardData.flow_metrics?.gli_accel),
            zscore: getLatestValue(
                $dashboardData.flow_metrics?.gli_impulse_zscore,
            ),
        },
        {
            name: "Global M2",
            impulse4w: getLatestValue(
                $dashboardData.flow_metrics?.m2_impulse_4w,
            ),
            impulse13w: getLatestValue(
                $dashboardData.flow_metrics?.m2_impulse_13w,
            ),
            accel: getLatestValue($dashboardData.flow_metrics?.m2_accel),
            zscore: getLatestValue(
                $dashboardData.flow_metrics?.m2_impulse_zscore,
            ),
        },
        {
            name: "US Net Liquidity",
            impulse4w: getLatestValue(
                $dashboardData.us_system_metrics?.netliq_delta_4w,
            ),
            impulse13w: getLatestValue(
                $dashboardData.us_system_metrics?.netliq_delta_13w,
            ),
            accel: null,
            zscore: getLatestValue(
                $dashboardData.us_system_metrics?.liquidity_score,
            ),
        },
    ];

    $: cbContributions = [
        { name: "FED", key: "fed_contrib_13w" },
        { name: "PBOC", key: "pboc_contrib_13w" },
        { name: "ECB", key: "ecb_contrib_13w" },
        { name: "BOJ", key: "boj_contrib_13w" },
        { name: "BOE", key: "boe_contrib_13w" },
    ]
        .map((cb) => ({
            name: cb.name,
            contrib: getLatestValue($dashboardData.flow_metrics?.[cb.key]),
        }))
        .sort((a, b) => Math.abs(b.contrib || 0) - Math.abs(a.contrib || 0));

    // ========================================================================
    // REPO USAGE & FED CORRIDOR
    // ========================================================================
    $: repoMetrics = {
        srfUsage:
            getLatestValue($dashboardData.repo_operations?.srf_usage) ??
            getLatestValue($dashboardData.repo_stress?.srf_usage) ??
            0,
        rrpUsage:
            getLatestValue($dashboardData.repo_operations?.rrp_usage) ??
            getLatestValue($dashboardData.us_net_liq_rrp) ??
            0,
        netRepo: getLatestValue($dashboardData.repo_operations?.net_repo) ?? 0,
        netRepoZscore:
            getLatestValue($dashboardData.repo_operations?.net_repo_zscore) ??
            0,
        cumulative30d:
            getLatestValue($dashboardData.repo_operations?.cumulative_30d) ?? 0,
        sofr: getLatestValue($dashboardData.repo_stress?.sofr) ?? 0,
        iorb: getLatestValue($dashboardData.repo_stress?.iorb) ?? 0,
        srfRate: getLatestValue($dashboardData.repo_stress?.srf_rate) ?? 0,
        rrpAward: getLatestValue($dashboardData.repo_stress?.rrp_award) ?? 0,
        sofrVolume:
            getLatestValue($dashboardData.repo_stress?.sofr_volume) ?? 0,
    };

    $: sofrIorbSpread =
        repoMetrics.sofr && repoMetrics.iorb
            ? ((repoMetrics.sofr - repoMetrics.iorb) * 100).toFixed(1)
            : null;

    $: gapToCeiling =
        repoMetrics.srfRate && repoMetrics.sofr
            ? ((repoMetrics.srfRate - repoMetrics.sofr) * 100).toFixed(1)
            : null;

    $: repoStressLevel = (() => {
        if (repoMetrics.srfUsage > 10)
            return {
                label: "HIGH",
                class: "high",
                desc: "SRF activated - banks tapping Fed backstop",
            };
        if (sofrIorbSpread !== null && parseFloat(sofrIorbSpread) > 5)
            return {
                label: "ELEVATED",
                class: "moderate",
                desc: "SOFR above IORB - funding pressure",
            };
        if (repoMetrics.netRepoZscore > 1.5)
            return {
                label: "WATCH",
                class: "moderate",
                desc: "Net repo elevated vs historical",
            };
        return {
            label: "NORMAL",
            class: "low",
            desc: "Repo markets functioning normally",
        };
    })();

    // ========================================================================
    // INFLATION EXPECTATIONS
    // ========================================================================
    $: inflationMetrics = [
        {
            id: "clev_1y",
            label: "Cleveland Fed 1Y",
            source: "Swap",
            value: getLatestValue($dashboardData.inflation_swaps?.cleveland_1y),
            delta1m: calcDelta(
                $dashboardData.inflation_swaps?.cleveland_1y,
                22,
            ),
            roc1m: calcRoc($dashboardData.inflation_swaps?.cleveland_1y, 22),
            roc3m: calcRoc($dashboardData.inflation_swaps?.cleveland_1y, 66),
        },
        {
            id: "clev_2y",
            label: "Cleveland Fed 2Y",
            source: "Swap",
            value: getLatestValue($dashboardData.inflation_swaps?.cleveland_2y),
            delta1m: calcDelta(
                $dashboardData.inflation_swaps?.cleveland_2y,
                22,
            ),
            roc1m: calcRoc($dashboardData.inflation_swaps?.cleveland_2y, 22),
            roc3m: calcRoc($dashboardData.inflation_swaps?.cleveland_2y, 66),
        },
        {
            id: "clev_5y",
            label: "Cleveland Fed 5Y",
            source: "Swap",
            value: getLatestValue($dashboardData.inflation_swaps?.cleveland_5y),
            delta1m: calcDelta(
                $dashboardData.inflation_swaps?.cleveland_5y,
                22,
            ),
            roc1m: calcRoc($dashboardData.inflation_swaps?.cleveland_5y, 22),
            roc3m: calcRoc($dashboardData.inflation_swaps?.cleveland_5y, 66),
        },
        {
            id: "clev_10y",
            label: "Cleveland Fed 10Y",
            source: "Swap",
            value: getLatestValue(
                $dashboardData.inflation_swaps?.cleveland_10y,
            ),
            delta1m: calcDelta(
                $dashboardData.inflation_swaps?.cleveland_10y,
                22,
            ),
            roc1m: calcRoc($dashboardData.inflation_swaps?.cleveland_10y, 22),
            roc3m: calcRoc($dashboardData.inflation_swaps?.cleveland_10y, 66),
        },
        {
            id: "tips_be_5y",
            label: "TIPS Breakeven 5Y",
            source: "TIPS",
            value: getLatestValue($dashboardData.inflation_expect_5y),
            delta1m: calcDelta($dashboardData.inflation_expect_5y, 22),
            roc1m: calcRoc($dashboardData.inflation_expect_5y, 22),
            roc3m: calcRoc($dashboardData.inflation_expect_5y, 66),
        },
        {
            id: "tips_be_10y",
            label: "TIPS Breakeven 10Y",
            source: "TIPS",
            value: getLatestValue($dashboardData.inflation_expect_10y),
            delta1m: calcDelta($dashboardData.inflation_expect_10y, 22),
            roc1m: calcRoc($dashboardData.inflation_expect_10y, 22),
            roc3m: calcRoc($dashboardData.inflation_expect_10y, 66),
        },
        {
            id: "tips_5y5y",
            label: "5Y5Y Forward",
            source: "TIPS",
            value: getLatestValue($dashboardData.tips?.fwd_5y5y),
            delta1m: calcDelta($dashboardData.tips?.fwd_5y5y, 22),
            roc1m: calcRoc($dashboardData.tips?.fwd_5y5y, 22),
            roc3m: calcRoc($dashboardData.tips?.fwd_5y5y, 66),
        },
        {
            id: "tips_real",
            label: "10Y Real Rate",
            source: "TIPS",
            value: getLatestValue($dashboardData.tips?.real_rate),
            delta1m: calcDelta($dashboardData.tips?.real_rate, 22),
            roc1m: calcRoc($dashboardData.tips?.real_rate, 22),
            roc3m: calcRoc($dashboardData.tips?.real_rate, 66),
        },
        {
            id: "umich",
            label: "UMich 1Y Expect",
            source: "Survey",
            value: getLatestValue(
                $dashboardData.inflation_swaps?.umich_expectations,
            ),
            delta1m: calcDelta(
                $dashboardData.inflation_swaps?.umich_expectations,
                22,
            ),
            roc1m: calcRoc(
                $dashboardData.inflation_swaps?.umich_expectations,
                22,
            ),
            roc3m: calcRoc(
                $dashboardData.inflation_swaps?.umich_expectations,
                66,
            ),
        },
    ];

    // Inflation curve signal (1Y vs 2Y)
    $: inflationCurveSignal = (() => {
        const clev1y = getLatestValue(
            $dashboardData.inflation_swaps?.cleveland_1y,
        );
        const clev2y = getLatestValue(
            $dashboardData.inflation_swaps?.cleveland_2y,
        );
        if (!clev1y || !clev2y)
            return { label: "N/A", class: "neutral", spread: 0 };
        const spread = clev1y - clev2y;
        if (spread < -0.05)
            return {
                label: "INVERTED",
                class: "bearish",
                spread,
                desc: "Market expects disinflation",
            };
        if (spread > 0.05)
            return {
                label: "STEEP",
                class: "bullish",
                spread,
                desc: "Near-term inflation elevated",
            };
        return {
            label: "FLAT",
            class: "neutral",
            spread,
            desc: "Inflation expectations stable",
        };
    })();

    // CPI/PCE actuals
    $: actualInflation = {
        cpi: getLatestValue($dashboardData.fed_forecasts?.cpi_yoy),
        coreCpi: getLatestValue($dashboardData.fed_forecasts?.core_cpi_yoy),
        pce: getLatestValue($dashboardData.fed_forecasts?.pce_yoy),
        corePce: getLatestValue($dashboardData.fed_forecasts?.core_pce_yoy),
    };

    // ========================================================================
    // BTC VALUATION (for alerts)
    // ========================================================================
    $: btcPrice = getLatestValue($dashboardData.btc?.price);
    $: btcFairValue = getLatestValue(
        $dashboardData.btc?.fair_value_v2 || $dashboardData.btc?.fair_value,
    );
    $: btcDeviation =
        btcPrice && btcFairValue
            ? ((btcPrice - btcFairValue) / btcFairValue) * 100
            : null;
    $: btcZscore = getLatestValue(
        $dashboardData.btc?.zscore_v2 || $dashboardData.btc?.zscore,
    );

    // ========================================================================
    // CB DIFFUSION & CONCENTRATION
    // ========================================================================
    $: cbDiffusion = getLatestValue(
        $dashboardData.macro_regime?.cb_diffusion_13w,
    );
    $: cbHHI = getLatestValue($dashboardData.macro_regime?.cb_hhi_13w);

    // ========================================================================
    // EARLY WARNINGS & DIVERGENCES
    // ========================================================================
    $: alerts = (() => {
        const alertList = [];

        // 1. Critical Stress
        if (totalStress >= 15) {
            alertList.push({
                type: "danger",
                icon: "🚨",
                title: "CRITICAL STRESS",
                msg: `Total stress at ${totalStress}/27 - Multiple systemic risk indicators elevated`,
                severity: "critical",
            });
        } else if (totalStress >= 10) {
            alertList.push({
                type: "warning",
                icon: "⚠️",
                title: "HIGH STRESS",
                msg: `Total stress at ${totalStress}/27 - Significant market tensions`,
                severity: "high",
            });
        }

        // 2. CLI-GLI Divergence
        const cliMom = getLatestValue(
            $dashboardData.flow_metrics?.cli_momentum_4w,
        );
        const gliImp = getLatestValue(
            $dashboardData.flow_metrics?.gli_impulse_13w,
        );
        if (cliMom !== null && gliImp !== null) {
            if (cliMom > 0.1 && gliImp < -0.1) {
                alertList.push({
                    type: "warning",
                    icon: "🔀",
                    title: "CLI-GLI DIVERGENCE",
                    msg: "Credit easing (CLI↑) while global liquidity contracts (GLI↓)",
                    severity: "medium",
                });
            } else if (cliMom < -0.1 && gliImp > 0.1) {
                alertList.push({
                    type: "warning",
                    icon: "🔀",
                    title: "CLI-GLI DIVERGENCE",
                    msg: "Credit tightening (CLI↓) while global liquidity expands (GLI↑)",
                    severity: "medium",
                });
            }
        }

        // 3. Regime Transition
        const transition = getLatestValue(
            $dashboardData.macro_regime?.transition,
        );
        if (transition && transition > 1.5) {
            alertList.push({
                type: "info",
                icon: "🔄",
                title: "REGIME TRANSITION",
                msg: "High acceleration detected - imminent regime change likely",
                severity: "high",
            });
        }

        // 4. BTC Extreme Valuation
        if (btcZscore !== null) {
            if (btcZscore > 2) {
                alertList.push({
                    type: "signal",
                    icon: "📈",
                    title: "BTC OVERVALUED",
                    msg: `BTC at +${btcZscore.toFixed(1)}σ - Consider profit-taking`,
                    severity: "high",
                });
            } else if (btcZscore < -2) {
                alertList.push({
                    type: "signal",
                    icon: "📉",
                    title: "BTC UNDERVALUED",
                    msg: `BTC at ${btcZscore.toFixed(1)}σ - Potential accumulation zone`,
                    severity: "high",
                });
            } else if (btcZscore < -1.5) {
                alertList.push({
                    type: "info",
                    icon: "👀",
                    title: "BTC APPROACHING VALUE",
                    msg: `BTC at ${btcZscore.toFixed(1)}σ - Approaching accumulation zone`,
                    severity: "medium",
                });
            }
        }

        // 5. CB Concentration Risk
        if (cbHHI !== null && cbHHI > 0.25) {
            alertList.push({
                type: "warning",
                icon: "⚠️",
                title: "CB CONCENTRATION",
                msg: `Single CB dominating liquidity flows (HHI: ${(cbHHI * 100).toFixed(0)}%)`,
                severity: "medium",
            });
        }

        // 6. Low CB Diffusion
        if (cbDiffusion !== null && cbDiffusion < 0.3) {
            alertList.push({
                type: "warning",
                icon: "📉",
                title: "LOW CB BREADTH",
                msg: `Only ${(cbDiffusion * 100).toFixed(0)}% of CBs expanding - narrow liquidity base`,
                severity: "medium",
            });
        }

        // 7. Repo Stress
        if (repoStressLevel.class !== "low") {
            alertList.push({
                type: repoStressLevel.class === "high" ? "danger" : "warning",
                icon: "🏛️",
                title: `REPO ${repoStressLevel.label}`,
                msg: repoStressLevel.desc,
                severity:
                    repoStressLevel.class === "high" ? "critical" : "medium",
            });
        }

        // 8. Inflation Alert
        const tipsBreakeven = getLatestValue(
            $dashboardData.inflation_expect_10y,
        );
        if (tipsBreakeven !== null) {
            if (tipsBreakeven > 2.5) {
                alertList.push({
                    type: "warning",
                    icon: "🔥",
                    title: "INFLATION ELEVATED",
                    msg: `10Y Breakeven at ${tipsBreakeven.toFixed(2)}% - Above Fed target`,
                    severity: "medium",
                });
            } else if (tipsBreakeven < 1.8) {
                alertList.push({
                    type: "info",
                    icon: "❄️",
                    title: "DISINFLATION RISK",
                    msg: `10Y Breakeven at ${tipsBreakeven.toFixed(2)}% - Below target, watch for easing`,
                    severity: "medium",
                });
            }
        }

        // 9. VIX Spike
        const vixValue = getLatestValue($dashboardData.vix?.values);
        if (vixValue !== null && vixValue > 25) {
            alertList.push({
                type: "warning",
                icon: "🌪️",
                title: "ELEVATED VIX",
                msg: `VIX at ${vixValue.toFixed(1)} - Heightened market fear`,
                severity: vixValue > 30 ? "high" : "medium",
            });
        }

        return alertList.slice(0, 6);
    })();

    // ========================================================================
    // FORMATTING HELPERS
    // ========================================================================
    function formatValue(val, decimals = 2, suffix = "") {
        if (val === null || val === undefined || isNaN(val)) return "—";
        return val.toFixed(decimals) + suffix;
    }

    function formatDelta(val, decimals = 2) {
        if (val === null || val === undefined || isNaN(val)) return "—";
        const prefix = val > 0 ? "+" : "";
        return prefix + val.toFixed(decimals);
    }

    function getSignalClass(state) {
        if (state === "bullish") return "signal-bull";
        if (state === "bearish") return "signal-bear";
        return "signal-neutral";
    }

    function getSignalEmoji(state) {
        if (state === "bullish") return "🟢";
        if (state === "bearish") return "🔴";
        return "⚪";
    }
</script>

<div class="dashboard-quant" class:dark={$darkMode}>
    <!-- ================================================================== -->
    <!-- 1. REGIME STATUS BAR -->
    <!-- ================================================================== -->
    <div class="regime-status-bar">
        <div class="regime-score-container">
            <div
                class="regime-score-ring"
                style="--score: {regimeScore}; --color: {regimeCode === 1
                    ? '#10b981'
                    : regimeCode === -1
                      ? '#ef4444'
                      : '#6b7280'}"
            >
                <span class="score-value">{regimeScore.toFixed(0)}</span>
            </div>
            <div class="regime-info">
                <span class="regime-label {regimeColor}"
                    >{regimeEmoji} {regimeLabel}</span
                >
                <span class="regime-trend {regimeTrend.class}"
                    >{regimeTrend.label}</span
                >
            </div>
        </div>

        <div class="regime-components">
            <div class="component">
                <span class="comp-label">Liquidity</span>
                <span
                    class="comp-value"
                    class:positive={regimeDiagnostics.liquidity_z > 0}
                    class:negative={regimeDiagnostics.liquidity_z < 0}
                >
                    {formatDelta(regimeDiagnostics.liquidity_z)}σ
                </span>
            </div>
            <div class="component">
                <span class="comp-label">Credit</span>
                <span
                    class="comp-value"
                    class:positive={regimeDiagnostics.credit_z > 0}
                    class:negative={regimeDiagnostics.credit_z < 0}
                >
                    {formatDelta(regimeDiagnostics.credit_z)}σ
                </span>
            </div>
            <div class="component">
                <span class="comp-label">Brakes</span>
                <span
                    class="comp-value"
                    class:positive={regimeDiagnostics.brakes_z < 0}
                    class:negative={regimeDiagnostics.brakes_z > 0}
                >
                    {formatDelta(regimeDiagnostics.brakes_z)}σ
                </span>
            </div>
        </div>

        <div class="fomc-section">
            <div class="fomc-countdown">
                <span class="fomc-label">Next FOMC</span>
                {#if fomcCountdown.isToday}
                    <span class="fomc-today">🔴 TODAY</span>
                {:else}
                    <span class="fomc-time"
                        >{fomcCountdown.days}d {fomcCountdown.hours}h</span
                    >
                {/if}
                {#if nextFomcHasSEP}
                    <span class="fomc-sep">📊 SEP</span>
                {/if}
            </div>

            {#if currentFedRate || currentSOFR}
                <div class="rates-container">
                    {#if currentFedRate}
                        <div class="fed-rate">
                            <span class="rate-label">Target</span>
                            <span class="rate-value target"
                                >{currentFedRate.toFixed(2)}%</span
                            >
                        </div>
                    {/if}
                    {#if currentSOFR}
                        <div class="fed-rate">
                            <span class="rate-label">SOFR</span>
                            <span class="rate-value sofr"
                                >{currentSOFR.toFixed(2)}%</span
                            >
                        </div>
                    {/if}
                </div>
            {/if}

            <div class="probs-group">
                <div
                    class="prob-item cut"
                    class:high={nextMeetingProbs?.cut > 50}
                >
                    <span class="prob-label">Cut</span>
                    <span class="prob-value"
                        >{nextMeetingProbs?.cut ?? "—"}%</span
                    >
                    {#if nextMeetingProbs?.roc1m}
                        <span
                            class="prob-change"
                            class:up={nextMeetingProbs.roc1m > 0}
                            class:down={nextMeetingProbs.roc1m < 0}
                        >
                            {nextMeetingProbs.roc1m > 0
                                ? "+"
                                : ""}{nextMeetingProbs.roc1m.toFixed(0)}
                        </span>
                    {/if}
                </div>
                <div
                    class="prob-item hold"
                    class:high={nextMeetingProbs?.hold > 50}
                >
                    <span class="prob-label">Hold</span>
                    <span class="prob-value"
                        >{nextMeetingProbs?.hold ?? "—"}%</span
                    >
                </div>
                {#if nextMeetingProbs?.hike > 5}
                    <div class="prob-item hike">
                        <span class="prob-label">Hike</span>
                        <span class="prob-value">{nextMeetingProbs.hike}%</span>
                    </div>
                {/if}
            </div>
        </div>

        <div class="signal-summary">
            <span class="summary-label">Signals</span>
            <span class="summary-value">
                <span class="bull-count">🟢 {bullCount}</span>
                <span class="bear-count">🔴 {bearCount}</span>
                <span
                    class="net-count"
                    class:positive={netSignal > 0}
                    class:negative={netSignal < 0}
                >
                    Net: {netSignal > 0 ? "+" : ""}{netSignal}
                </span>
            </span>
        </div>
    </div>

    <!-- ================================================================== -->
    <!-- 2. LIQUIDITY PULSE (Stats Cards) -->
    <!-- ================================================================== -->
    {#if $latestStats}
        <div class="stats-grid">
            <StatsCard
                title={translations.stat_gli || "Global Liquidity (GLI)"}
                value={$latestStats.gli?.value}
                change={$latestStats.gli?.change}
                period="7d"
                suffix="T"
                icon="🌍"
            />
            <StatsCard
                title={translations.stat_us_net || "US Net Liquidity"}
                value={$latestStats.us_net_liq?.value}
                change={$latestStats.us_net_liq?.change}
                period="7d"
                suffix="T"
                icon="🇺🇸"
            />
            <StatsCard
                title={translations.stat_cli || "Credit Index (CLI)"}
                value={$latestStats.cli?.value}
                change={$latestStats.cli?.change}
                period="7d"
                suffix="Z"
                icon="💳"
                precision={3}
            />
            <StatsCard
                title={translations.stat_vix || "VIX"}
                value={$latestStats.vix?.value}
                change={$latestStats.vix?.change}
                period="7d"
                icon="🌪️"
            />
        </div>
    {/if}

    <!-- ================================================================== -->
    <!-- EARLY WARNINGS & ALERTS (TOP) -->
    <!-- ================================================================== -->
    {#if alerts.length > 0}
        <div class="alerts-panel">
            <div class="alerts-header">
                <h3>⚠️ Alerts ({alerts.length})</h3>
            </div>
            <div class="alerts-grid">
                {#each alerts as alert}
                    <div class="alert-item {alert.type} {alert.severity}">
                        <span class="alert-icon">{alert.icon}</span>
                        <div class="alert-content">
                            <span class="alert-title">{alert.title}</span>
                            <span class="alert-msg">{alert.msg}</span>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}

    <div class="dashboard-grid">
        <!-- ================================================================== -->
        <!-- 3. STRESS DASHBOARD -->
        <!-- ================================================================== -->
        <div class="panel stress-panel">
            <div class="panel-header">
                <h3>📊 Market Stress Dashboard</h3>
                <div class="stress-total" style="--stress-color: {stressColor}">
                    <span class="stress-score">{totalStress}/{maxStress}</span>
                    <span
                        class="stress-level {getStressLevelClass(stressLevel)}"
                        >{stressLevel}</span
                    >
                </div>
            </div>
            <div class="stress-grid">
                {#each stressDimensions as dim}
                    <div class="stress-item">
                        <span class="stress-label">{dim.label}</span>
                        <div class="stress-bar-container">
                            <div
                                class="stress-bar"
                                style="width: {(dim.score / dim.max) *
                                    100}%; background: {dim.score >= 4
                                    ? '#ef4444'
                                    : dim.score >= 2
                                      ? '#f59e0b'
                                      : '#10b981'}"
                            ></div>
                        </div>
                        <span class="stress-value">{dim.score}/{dim.max}</span>
                        <span
                            class="stress-badge {getStressLevelClass(
                                dim.level,
                            )}">{dim.level}</span
                        >
                    </div>
                {/each}
            </div>
        </div>

        <!-- ================================================================== -->
        <!-- 4. SIGNAL MATRIX -->
        <!-- ================================================================== -->
        <div class="panel signal-panel">
            <div class="panel-header">
                <h3>📡 Signal Matrix</h3>
                <div class="aggregate-badge {aggregateSignal}">
                    {aggregateSignal === "bullish"
                        ? "🟢 RISK-ON"
                        : aggregateSignal === "bearish"
                          ? "🔴 RISK-OFF"
                          : "⚪ NEUTRAL"}
                </div>
            </div>
            <div class="signal-table-container">
                <table class="signal-table">
                    <thead>
                        <tr>
                            <th>Indicator</th>
                            <th>Value</th>
                            <th>Δ1M</th>
                            <th>Signal</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each signalMatrix as signal}
                            <tr>
                                <td class="indicator-cell">
                                    <span class="indicator-icon"
                                        >{signal.icon}</span
                                    >
                                    <span class="indicator-name"
                                        >{signal.label}</span
                                    >
                                </td>
                                <td class="value-cell">
                                    {signal.value !== null
                                        ? signal.value.toFixed(2)
                                        : "—"}
                                    {#if signal.percentile !== null}
                                        <span class="percentile"
                                            >P{signal.percentile.toFixed(
                                                0,
                                            )}</span
                                        >
                                    {/if}
                                </td>
                                <td
                                    class="delta-cell"
                                    class:positive={signal.delta > 0}
                                    class:negative={signal.delta < 0}
                                >
                                    {signal.delta !== null
                                        ? formatDelta(signal.delta)
                                        : "—"}
                                </td>
                                <td
                                    class="signal-cell {getSignalClass(
                                        signal.state,
                                    )}"
                                >
                                    {getSignalEmoji(signal.state)}
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- ================================================================== -->
        <!-- 5. FLOW MOMENTUM -->
        <!-- ================================================================== -->
        <div class="panel flow-panel">
            <div class="panel-header">
                <h3>⚡ Flow Momentum</h3>
            </div>
            <table class="flow-table">
                <thead>
                    <tr>
                        <th>Aggregate</th>
                        <th>Impulse 4W</th>
                        <th>Impulse 13W</th>
                        <th>Accel</th>
                        <th>Z-Score</th>
                    </tr>
                </thead>
                <tbody>
                    {#each flowData as flow}
                        <tr>
                            <td class="flow-name">{flow.name}</td>
                            <td
                                class="flow-val"
                                class:positive={flow.impulse4w > 0}
                                class:negative={flow.impulse4w < 0}
                            >
                                {formatValue(flow.impulse4w, 2, "T")}
                            </td>
                            <td
                                class="flow-val"
                                class:positive={flow.impulse13w > 0}
                                class:negative={flow.impulse13w < 0}
                            >
                                {formatValue(flow.impulse13w, 2, "T")}
                            </td>
                            <td
                                class="flow-val"
                                class:positive={flow.accel > 0}
                                class:negative={flow.accel < 0}
                            >
                                {flow.accel !== null
                                    ? formatValue(flow.accel, 2, "T")
                                    : "—"}
                            </td>
                            <td
                                class="flow-zscore"
                                class:high={flow.zscore > 1}
                                class:low={flow.zscore < -1}
                            >
                                {formatValue(flow.zscore, 2, "σ")}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>

            <div class="cb-contributions">
                <h4>CB Contribution to ΔGLI (13W)</h4>
                <div class="contrib-bars">
                    {#each cbContributions as cb}
                        <div class="contrib-item">
                            <span class="cb-name">{cb.name}</span>
                            <div class="contrib-bar-wrapper">
                                <div
                                    class="contrib-bar"
                                    class:positive={cb.contrib > 0}
                                    class:negative={cb.contrib < 0}
                                    style="width: {Math.min(
                                        Math.abs(cb.contrib || 0),
                                        50,
                                    )}%"
                                ></div>
                            </div>
                            <span
                                class="contrib-val"
                                class:positive={cb.contrib > 0}
                                class:negative={cb.contrib < 0}
                            >
                                {formatValue(cb.contrib, 1, "%")}
                            </span>
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <!-- ================================================================== -->
        <!-- 6. REPO USAGE & FED CORRIDOR -->
        <!-- ================================================================== -->
        <div class="panel repo-panel">
            <div class="panel-header">
                <h3>🏛️ Repo Market & Fed Corridor</h3>
                <div class="repo-status {repoStressLevel.class}">
                    {repoStressLevel.label}
                </div>
            </div>

            <div class="corridor-visual">
                <div class="corridor-rate ceiling">
                    <span class="rate-label">SRF (Ceiling)</span>
                    <span class="rate-value"
                        >{formatValue(repoMetrics.srfRate, 2, "%")}</span
                    >
                </div>
                <div class="corridor-rate sofr">
                    <span class="rate-label">SOFR</span>
                    <span class="rate-value"
                        >{formatValue(repoMetrics.sofr, 3, "%")}</span
                    >
                    <span class="rate-spread"
                        >Gap: {gapToCeiling ?? "—"}bps</span
                    >
                </div>
                <div class="corridor-rate iorb">
                    <span class="rate-label">IORB (Floor)</span>
                    <span class="rate-value"
                        >{formatValue(repoMetrics.iorb, 2, "%")}</span
                    >
                    <span class="rate-spread"
                        >Spread: {sofrIorbSpread ?? "—"}bps</span
                    >
                </div>
                <div class="corridor-rate rrp">
                    <span class="rate-label">RRP Award</span>
                    <span class="rate-value"
                        >{formatValue(repoMetrics.rrpAward, 2, "%")}</span
                    >
                </div>
            </div>

            <div class="repo-metrics-grid">
                <div class="repo-metric">
                    <span class="metric-label">RRP Usage</span>
                    <span class="metric-value"
                        >${formatValue(repoMetrics.rrpUsage, 2)}T</span
                    >
                </div>
                <div class="repo-metric">
                    <span class="metric-label">SRF Usage</span>
                    <span
                        class="metric-value"
                        class:warning={repoMetrics.srfUsage > 0}
                        >${formatValue(repoMetrics.srfUsage, 1)}B</span
                    >
                </div>
                <div class="repo-metric">
                    <span class="metric-label">SOFR Volume</span>
                    <span class="metric-value"
                        >${formatValue(repoMetrics.sofrVolume, 0)}B</span
                    >
                </div>
                <div class="repo-metric">
                    <span class="metric-label">Net Repo Z</span>
                    <span
                        class="metric-value"
                        class:elevated={repoMetrics.netRepoZscore > 1}
                        >{formatValue(repoMetrics.netRepoZscore, 2)}σ</span
                    >
                </div>
            </div>

            <p class="repo-desc">{repoStressLevel.desc}</p>
        </div>

        <!-- ================================================================== -->
        <!-- 7. INFLATION EXPECTATIONS -->
        <!-- ================================================================== -->
        <div class="panel inflation-panel wide">
            <div class="panel-header">
                <h3>🔥 Inflation Expectations</h3>
                <div class="inflation-signal {inflationCurveSignal.class}">
                    Curve: {inflationCurveSignal.label} ({formatDelta(
                        inflationCurveSignal.spread,
                        2,
                    )}pp)
                </div>
            </div>

            <div class="actual-inflation">
                <div class="actual-item">
                    <span class="actual-label">CPI YoY</span>
                    <span class="actual-value"
                        >{formatValue(actualInflation.cpi, 2, "%")}</span
                    >
                </div>
                <div class="actual-item">
                    <span class="actual-label">Core CPI</span>
                    <span class="actual-value"
                        >{formatValue(actualInflation.coreCpi, 2, "%")}</span
                    >
                </div>
                <div class="actual-item">
                    <span class="actual-label">PCE YoY</span>
                    <span class="actual-value"
                        >{formatValue(actualInflation.pce, 2, "%")}</span
                    >
                </div>
                <div class="actual-item target">
                    <span class="actual-label">Core PCE</span>
                    <span class="actual-value"
                        >{formatValue(actualInflation.corePce, 2, "%")}</span
                    >
                    <span class="target-badge">Fed Target: 2%</span>
                </div>
            </div>

            <table class="inflation-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Source</th>
                        <th>Value</th>
                        <th>Δ1M (pp)</th>
                        <th>ROC 1M</th>
                        <th>ROC 3M</th>
                    </tr>
                </thead>
                <tbody>
                    {#each inflationMetrics as metric}
                        <tr>
                            <td class="metric-name">{metric.label}</td>
                            <td class="metric-source">{metric.source}</td>
                            <td class="metric-val"
                                >{formatValue(metric.value, 2, "%")}</td
                            >
                            <td
                                class="metric-delta"
                                class:positive={metric.delta1m > 0}
                                class:negative={metric.delta1m < 0}
                            >
                                {formatDelta(metric.delta1m, 2)}
                            </td>
                            <td
                                class="metric-roc"
                                class:positive={metric.roc1m > 0}
                                class:negative={metric.roc1m < 0}
                            >
                                {formatDelta(metric.roc1m, 1)}%
                            </td>
                            <td
                                class="metric-roc"
                                class:positive={metric.roc3m > 0}
                                class:negative={metric.roc3m < 0}
                            >
                                {formatDelta(metric.roc3m, 1)}%
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
            <p class="inflation-note">
                {inflationCurveSignal.desc ||
                    "Inflation expectations curve analysis"}
            </p>
        </div>
    </div>
</div>

<style>
    .dashboard-quant {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    /* ========== REGIME STATUS BAR ========== */
    .regime-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 24px;
        padding: 16px 24px;
        background: var(--bg-secondary, #1e293b);
        border-radius: 16px;
        border: 1px solid var(--border-color, #334155);
        flex-wrap: wrap;
    }

    .regime-score-container {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .regime-score-ring {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: conic-gradient(
            var(--color) calc(var(--score) * 1%),
            var(--bg-tertiary, #334155) 0
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
    }

    .regime-score-ring::before {
        content: "";
        position: absolute;
        width: 52px;
        height: 52px;
        background: var(--bg-secondary, #1e293b);
        border-radius: 50%;
    }

    .score-value {
        position: relative;
        z-index: 1;
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-primary, #f1f5f9);
    }

    .regime-info {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .regime-label {
        font-size: 1.1rem;
        font-weight: 700;
    }
    .regime-label.bullish {
        color: #10b981;
    }
    .regime-label.bearish {
        color: #ef4444;
    }
    .regime-label.neutral {
        color: #6b7280;
    }

    .regime-trend {
        font-size: 0.85rem;
        color: var(--text-muted, #94a3b8);
    }
    .regime-trend.positive {
        color: #10b981;
    }
    .regime-trend.negative {
        color: #ef4444;
    }

    .regime-components {
        display: flex;
        gap: 20px;
    }

    .component {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
    }

    .comp-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .comp-value {
        font-size: 0.95rem;
        font-weight: 700;
        font-family: monospace;
    }
    .comp-value.positive {
        color: #10b981;
    }
    .comp-value.negative {
        color: #ef4444;
    }

    /* Fed Rates & Probabilities Section - Redesigned */
    .fomc-section {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 8px 12px;
        background: var(--bg-tertiary, #334155);
        border-radius: 10px;
        border: 1px solid var(--border-color, #475569);
    }

    .fomc-countdown {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 12px;
        border-right: 1px solid var(--border-color, #475569);
    }

    .fomc-label {
        font-size: 0.6rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .fomc-time {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
        font-family: monospace;
    }

    .fomc-today {
        font-size: 1rem;
        font-weight: 800;
        color: #ef4444;
        animation: pulse 1.5s infinite;
    }

    .fomc-sep {
        font-size: 0.6rem;
        color: #f59e0b;
        font-weight: 600;
        margin-top: 2px;
    }

    @keyframes pulse {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    .rates-container {
        display: flex;
        gap: 0;
        border-right: 1px solid var(--border-color, #475569);
    }

    .fed-rate {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 10px;
    }

    .fed-rate:first-child {
        border-right: 1px dashed var(--border-color, #475569);
    }

    .fed-rate .rate-label {
        font-size: 0.55rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .fed-rate .rate-value {
        font-size: 1rem;
        font-weight: 700;
        font-family: monospace;
    }

    .fed-rate .rate-value.target {
        color: #60a5fa;
    }

    .fed-rate .rate-value.sofr {
        color: #f59e0b;
    }

    .probs-group {
        display: flex;
        gap: 2px;
        margin-left: 4px;
    }

    .prob-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 10px;
        border-radius: 6px;
        min-width: 48px;
        transition: all 0.2s ease;
    }

    .prob-item.cut {
        background: rgba(34, 197, 94, 0.08);
        border-bottom: 2px solid #22c55e;
    }

    .prob-item.cut.high {
        background: rgba(34, 197, 94, 0.2);
    }

    .prob-item.hold {
        background: rgba(100, 116, 139, 0.08);
        border-bottom: 2px solid #64748b;
    }

    .prob-item.hold.high {
        background: rgba(100, 116, 139, 0.2);
    }

    .prob-item.hike {
        background: rgba(239, 68, 68, 0.08);
        border-bottom: 2px solid #ef4444;
    }

    .prob-label {
        font-size: 0.55rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .prob-value {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
        font-family: monospace;
    }

    .prob-change {
        font-size: 0.55rem;
        font-weight: 600;
        padding: 1px 4px;
        border-radius: 3px;
        margin-top: 1px;
    }

    .prob-change.up {
        color: #22c55e;
        background: rgba(34, 197, 94, 0.2);
    }

    .prob-change.down {
        color: #ef4444;
        background: rgba(239, 68, 68, 0.2);
    }

    .signal-summary {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
    }

    .summary-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .summary-value {
        display: flex;
        gap: 8px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    .bull-count {
        color: #10b981;
    }
    .bear-count {
        color: #ef4444;
    }
    .net-count {
        color: var(--text-muted);
    }
    .net-count.positive {
        color: #10b981;
    }
    .net-count.negative {
        color: #ef4444;
    }

    /* ========== STATS GRID ========== */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
    }

    @media (max-width: 1200px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    /* ========== DASHBOARD GRID ========== */
    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }

    @media (max-width: 1400px) {
        .dashboard-grid {
            grid-template-columns: 1fr;
        }
    }

    /* ========== PANELS ========== */
    .panel {
        background: var(--bg-secondary, #1e293b);
        border: 1px solid var(--border-color, #334155);
        border-radius: 16px;
        padding: 20px;
    }

    .panel.wide {
        grid-column: span 2;
    }

    @media (max-width: 1400px) {
        .panel.wide {
            grid-column: span 1;
        }
    }

    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-color, #334155);
    }

    .panel-header h3 {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
    }

    /* ========== STRESS PANEL ========== */
    .stress-total {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .stress-score {
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--stress-color);
        font-family: monospace;
    }

    .stress-level {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .stress-level.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .stress-level.moderate {
        background: rgba(202, 138, 4, 0.2);
        color: #ca8a04;
    }
    .stress-level.high {
        background: rgba(234, 88, 12, 0.2);
        color: #ea580c;
    }
    .stress-level.critical {
        background: rgba(220, 38, 38, 0.2);
        color: #dc2626;
    }

    .stress-grid {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .stress-item {
        display: grid;
        grid-template-columns: 120px 1fr 50px 80px;
        align-items: center;
        gap: 12px;
    }

    .stress-label {
        font-size: 0.85rem;
        color: var(--text-secondary, #cbd5e1);
    }

    .stress-bar-container {
        height: 8px;
        background: var(--bg-tertiary, #334155);
        border-radius: 4px;
        overflow: hidden;
    }

    .stress-bar {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    .stress-value {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary, #f1f5f9);
        text-align: right;
        font-family: monospace;
    }

    .stress-badge {
        font-size: 0.65rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        text-align: center;
    }

    /* ========== SIGNAL TABLE ========== */
    .signal-table-container {
        max-height: 400px;
        overflow-y: auto;
    }

    .signal-table,
    .flow-table,
    .inflation-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.85rem;
    }

    .signal-table th,
    .flow-table th,
    .inflation-table th {
        text-align: left;
        padding: 8px;
        font-size: 0.7rem;
        text-transform: uppercase;
        color: var(--text-muted, #94a3b8);
        border-bottom: 1px solid var(--border-color, #334155);
    }

    .signal-table td,
    .flow-table td,
    .inflation-table td {
        padding: 8px;
        border-bottom: 1px solid
            var(--border-color-light, rgba(51, 65, 85, 0.5));
    }

    .indicator-cell {
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .indicator-icon {
        font-size: 1rem;
    }

    .indicator-name {
        font-weight: 500;
        color: var(--text-primary, #f1f5f9);
    }

    .value-cell {
        font-family: monospace;
        color: var(--text-secondary, #cbd5e1);
    }

    .percentile {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        margin-left: 4px;
    }

    .delta-cell,
    .metric-delta,
    .metric-roc {
        font-family: monospace;
    }
    .delta-cell.positive,
    .metric-delta.positive,
    .metric-roc.positive {
        color: #10b981;
    }
    .delta-cell.negative,
    .metric-delta.negative,
    .metric-roc.negative {
        color: #ef4444;
    }

    .signal-cell {
        text-align: center;
        font-size: 1.1rem;
    }
    .signal-cell.signal-bull {
        background: rgba(16, 185, 129, 0.1);
    }
    .signal-cell.signal-bear {
        background: rgba(239, 68, 68, 0.1);
    }

    .aggregate-badge {
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .aggregate-badge.bullish {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .aggregate-badge.bearish {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    .aggregate-badge.neutral {
        background: rgba(107, 114, 128, 0.2);
        color: #9ca3af;
    }

    /* ========== FLOW PANEL ========== */
    .flow-name {
        font-weight: 600;
        color: var(--text-primary, #f1f5f9);
    }

    .flow-val {
        font-family: monospace;
    }
    .flow-val.positive {
        color: #10b981;
    }
    .flow-val.negative {
        color: #ef4444;
    }

    .flow-zscore {
        font-family: monospace;
        font-weight: 600;
    }
    .flow-zscore.high {
        color: #10b981;
    }
    .flow-zscore.low {
        color: #ef4444;
    }

    .cb-contributions {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color, #334155);
    }

    .cb-contributions h4 {
        margin: 0 0 12px 0;
        font-size: 0.85rem;
        color: var(--text-muted, #94a3b8);
    }

    .contrib-bars {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .contrib-item {
        display: grid;
        grid-template-columns: 50px 1fr 60px;
        align-items: center;
        gap: 10px;
    }

    .cb-name {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary, #cbd5e1);
    }

    .contrib-bar-wrapper {
        height: 8px;
        background: var(--bg-tertiary, #334155);
        border-radius: 4px;
        overflow: hidden;
    }

    .contrib-bar {
        height: 100%;
        border-radius: 4px;
    }
    .contrib-bar.positive {
        background: #10b981;
    }
    .contrib-bar.negative {
        background: #ef4444;
    }

    .contrib-val {
        font-size: 0.8rem;
        font-family: monospace;
        text-align: right;
    }
    .contrib-val.positive {
        color: #10b981;
    }
    .contrib-val.negative {
        color: #ef4444;
    }

    /* ========== REPO PANEL ========== */
    .repo-status {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .repo-status.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .repo-status.moderate {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    .repo-status.high {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .corridor-visual {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 12px;
        background: var(--bg-tertiary, #334155);
        border-radius: 10px;
        margin-bottom: 16px;
    }

    .corridor-rate {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border-radius: 6px;
    }

    .corridor-rate.ceiling {
        background: rgba(239, 68, 68, 0.1);
        border-left: 3px solid #ef4444;
    }

    .corridor-rate.sofr {
        background: rgba(59, 130, 246, 0.15);
        border-left: 3px solid #3b82f6;
    }

    .corridor-rate.iorb {
        background: rgba(16, 185, 129, 0.1);
        border-left: 3px solid #10b981;
    }

    .corridor-rate.rrp {
        background: rgba(107, 114, 128, 0.1);
        border-left: 3px solid #6b7280;
    }

    .rate-label {
        font-size: 0.75rem;
        color: var(--text-muted, #94a3b8);
        min-width: 80px;
    }

    .rate-value {
        font-size: 1rem;
        font-weight: 700;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }

    .rate-spread {
        font-size: 0.75rem;
        color: var(--text-muted, #94a3b8);
        margin-left: auto;
    }

    .repo-metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 12px;
    }

    .repo-metric {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 10px;
        background: var(--bg-tertiary, #334155);
        border-radius: 8px;
    }

    .metric-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 0.95rem;
        font-weight: 700;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }
    .metric-value.warning {
        color: #f59e0b;
    }
    .metric-value.elevated {
        color: #ef4444;
    }

    .repo-desc {
        font-size: 0.8rem;
        color: var(--text-muted, #94a3b8);
        margin: 0;
        font-style: italic;
    }

    /* ========== INFLATION PANEL ========== */
    .inflation-signal {
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .inflation-signal.bullish {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    .inflation-signal.bearish {
        background: rgba(59, 130, 246, 0.2);
        color: #3b82f6;
    }
    .inflation-signal.neutral {
        background: rgba(107, 114, 128, 0.2);
        color: #9ca3af;
    }

    .actual-inflation {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }

    .actual-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 10px;
        background: var(--bg-tertiary, #334155);
        border-radius: 8px;
    }

    .actual-item.target {
        border: 1px solid rgba(239, 68, 68, 0.3);
    }

    .actual-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .actual-value {
        font-size: 1.1rem;
        font-weight: 700;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }

    .target-badge {
        font-size: 0.6rem;
        color: #ef4444;
        font-weight: 600;
    }

    .metric-name {
        font-weight: 500;
        color: var(--text-primary, #f1f5f9);
    }

    .metric-source {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
    }

    .metric-val {
        font-family: monospace;
        font-weight: 600;
        color: var(--text-secondary, #cbd5e1);
    }

    .inflation-note {
        margin: 12px 0 0 0;
        font-size: 0.8rem;
        color: var(--text-muted, #94a3b8);
        font-style: italic;
    }

    /* ========== BTC PANEL ========== */
    .btc-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
    }

    .btc-metric {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px;
        background: var(--bg-tertiary, #334155);
        border-radius: 8px;
    }

    .btc-metric.zscore {
        border: 1px solid var(--border-color, #334155);
    }

    .btc-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .btc-value {
        font-size: 1rem;
        font-weight: 700;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }
    .btc-value.positive {
        color: #10b981;
    }
    .btc-value.negative {
        color: #ef4444;
    }
    .btc-value.overbought {
        color: #ef4444;
    }
    .btc-value.oversold {
        color: #10b981;
    }

    .btc-breadth {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .breadth-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        padding: 12px;
        background: var(--bg-tertiary, #334155);
        border-radius: 8px;
    }

    .breadth-label {
        font-size: 0.7rem;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
    }

    .breadth-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
    }
    .breadth-value.warning {
        color: #f59e0b;
    }

    .breadth-desc {
        font-size: 0.65rem;
        color: var(--text-muted, #94a3b8);
    }

    /* ========== ALERTS PANEL ========== */
    .alerts-panel {
        background: var(--bg-secondary, #1e293b);
        border: 1px solid var(--border-color, #334155);
        border-radius: 16px;
        padding: 20px;
    }

    .alerts-header {
        margin-bottom: 16px;
    }

    .alerts-header h3 {
        margin: 0;
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
    }

    .alerts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 12px;
    }

    .alert-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 16px;
        border-radius: 10px;
        border-left: 4px solid;
    }

    .alert-item.danger {
        background: rgba(220, 38, 38, 0.1);
        border-color: #dc2626;
    }
    .alert-item.warning {
        background: rgba(245, 158, 11, 0.1);
        border-color: #f59e0b;
    }
    .alert-item.info {
        background: rgba(59, 130, 246, 0.1);
        border-color: #3b82f6;
    }
    .alert-item.signal {
        background: rgba(139, 92, 246, 0.1);
        border-color: #8b5cf6;
    }

    .alert-icon {
        font-size: 1.2rem;
    }

    .alert-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }

    .alert-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: var(--text-primary, #f1f5f9);
    }

    .alert-msg {
        font-size: 0.8rem;
        color: var(--text-secondary, #cbd5e1);
        line-height: 1.4;
    }

    /* ========== DARK MODE ADJUSTMENTS ========== */
    .dashboard-quant:not(.dark) {
        --bg-secondary: #f8fafc;
        --bg-tertiary: #e2e8f0;
        --border-color: #cbd5e1;
        --text-primary: #1e293b;
        --text-secondary: #475569;
        --text-muted: #64748b;
    }
</style>
