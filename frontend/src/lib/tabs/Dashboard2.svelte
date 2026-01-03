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
        t,
    } from "../../stores/settingsStore";

    // Import utility functions
    import { getLatestValue } from "../utils/helpers.js";

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
            ? $currentTranslations.status_bullish
            : regimeCode === -1
              ? $currentTranslations.status_bearish
              : $currentTranslations.status_neutral;
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
        if (accel > 0.1)
            return {
                label: `↗️ ${$currentTranslations.regime_accelerating || "Accelerating"}`,
                class: "positive",
            };
        if (accel < -0.1)
            return {
                label: `↘️ ${$currentTranslations.regime_decelerating || "Decelerating"}`,
                class: "negative",
            };
        return {
            label: `→ ${$currentTranslations.stable || "Stable"}`,
            class: "neutral",
        };
    })();

    $: regimeDiagnostics = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr)
            return {
                liquidity_z: 0,
                credit_z: 0,
                brakes_z: 0,
                total_z: 0,
                confidence: 0,
            };
        const getLatest = (arr) => {
            if (!arr?.length) return 0;
            return arr[arr.length - 1] ?? 0;
        };
        const tz = getLatest(mr.total_z);
        return {
            liquidity_z: getLatest(mr.liquidity_z),
            credit_z: getLatest(mr.credit_z),
            brakes_z: getLatest(mr.brakes_z),
            total_z: tz,
            confidence: Math.min(100, Math.abs(tz) * 40), // Simple confidence based on Z magnitude
        };
    })();

    $: currentFedRate = getLatestValue(
        $dashboardData.fed_forecasts?.fed_funds_rate,
    );
    $: currentSOFR = getLatestValue($dashboardData.repo_stress?.sofr);

    // ========================================================================
    // NARRATIVE & CATALYSTS
    // ========================================================================
    $: assessment = $dashboardData.stress_analysis?.overall_assessment || {
        headline:
            $currentTranslations.market_in_transition || "MARKET IN TRANSITION",
        key_risks: [
            $currentTranslations.no_major_stress ||
                "No major stress signals detected",
        ],
        key_positives: [
            $currentTranslations.liquidity_stable ||
                "Liquidity conditions stable",
        ],
        recommendation:
            $currentTranslations.monitor_closely ||
            "Monitor closely for regime changes",
    };

    // Helper to translate structured backend assessment items
    function getAssessmentText(item) {
        if (!item) return "";
        if (typeof item === "object") {
            return t($currentTranslations, item.key || item.text || "");
        }
        return t($currentTranslations, item);
    }

    $: treasurySettlements =
        $dashboardData["treasury_settlements"]?.grouped || [];
    $: next7dSettlements = treasurySettlements.filter((s) => {
        const date = new Date(s.date);
        const now = new Date();
        const nextWeek = new Date();
        nextWeek.setDate(now.getDate() + 7);
        return date >= now && date <= nextWeek;
    });

    $: totalNext7dAmount = next7dSettlements.reduce(
        (acc, s) => acc + (s.amount || 0),
        0,
    );
    $: rrpBuffer = getLatestValue($dashboardData.us_net_liq_rrp) * 1000; // T -> B

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
            ? t($currentTranslations, "status_critical") || "CRITICAL"
            : totalStress >= 10
              ? t($currentTranslations, "status_high") || "HIGH"
              : totalStress >= 5
                ? t($currentTranslations, "status_moderate") || "MODERATE"
                : t($currentTranslations, "status_low") || "LOW";
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

    // Weighted Signal Score & Drivers
    $: signalWeights = {
        cli: 0.2,
        hy_spread: 0.15,
        ig_spread: 0.1,
        nfci_credit: 0.1,
        nfci_risk: 0.1,
        lending: 0.1,
        tips_real_rate: 0.1,
        repo: 0.15,
    };

    $: weightedScoreInfo = (() => {
        let score = 0;
        const drivers = [];

        signalMatrix.forEach((s) => {
            const weight = signalWeights[s.id] || 0.05;
            const sValue =
                s.state === "bullish" ? 1 : s.state === "bearish" ? -1 : 0;
            score += sValue * weight;

            if (s.state !== "neutral") {
                drivers.push({
                    id: s.id,
                    label: s.label,
                    impact: sValue * weight,
                    state: s.state,
                });
            }
        });

        const topDrivers = drivers
            .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
            .slice(0, 3);

        return {
            score: Math.round(score * 100), // Scale to -100 to 100
            topDrivers,
        };
    })();

    $: aggregateSignal =
        weightedScoreInfo.score > 15
            ? "bullish"
            : weightedScoreInfo.score < -15
              ? "bearish"
              : "neutral";

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
                label: t($currentTranslations, "status_high") || "HIGH",
                class: "high",
                key: "alrt_repo_high_title",
                desc:
                    t($currentTranslations, "repo_srf_activated") ||
                    "SRF activated - banks tapping Fed backstop",
            };
        if (sofrIorbSpread !== null && parseFloat(sofrIorbSpread) > 5)
            return {
                label: t($currentTranslations, "status_elevated") || "ELEVATED",
                class: "moderate",
                key: "alrt_repo_elevated_title",
                desc:
                    t($currentTranslations, "repo_funding_pressure") ||
                    "SOFR above IORB - funding pressure",
            };
        if (repoMetrics.netRepoZscore > 1.5)
            return {
                label: t($currentTranslations, "status_watch") || "WATCH",
                class: "moderate",
                key: "alrt_repo_watch_title",
                desc:
                    t($currentTranslations, "repo_net_elevated") ||
                    "Net repo elevated vs historical",
            };
        return {
            label: t($currentTranslations, "status_normal") || "NORMAL",
            class: "low",
            key: null,
            desc:
                $currentTranslations.repo_normal_desc ||
                "Repo markets functioning normally",
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

    // BTC VALUATION (for dashboard blocks)
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
                title:
                    t($currentTranslations, "alrt_critical_stress_title") ||
                    "CRITICAL STRESS",
                msg: (
                    t($currentTranslations, "alrt_critical_stress_msg") ||
                    "Total stress at {score}/27 - Multiple systemic risk indicators elevated"
                ).replace("{score}", String(totalStress)),
                severity: "critical",
            });
        } else if (totalStress >= 10) {
            alertList.push({
                type: "warning",
                icon: "⚠️",
                title:
                    t($currentTranslations, "alrt_high_stress_title") ||
                    "HIGH STRESS",
                msg: (
                    t($currentTranslations, "alrt_high_stress_msg") ||
                    "Total stress at {score}/27 - Significant market tensions"
                ).replace("{score}", String(totalStress)),
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
                    title:
                        t($currentTranslations, "alrt_cligli_div_ease_title") ||
                        "CLI-GLI DIVERGENCE",
                    msg:
                        t($currentTranslations, "alrt_cligli_div_ease_msg") ||
                        "Credit easing (CLI↑) while global liquidity contracts (GLI↓)",
                    severity: "medium",
                });
            } else if (cliMom < -0.1 && gliImp > 0.1) {
                alertList.push({
                    type: "warning",
                    icon: "🔀",
                    title:
                        t(
                            $currentTranslations,
                            "alrt_cligli_div_tight_title",
                        ) || "CLI-GLI DIVERGENCE",
                    msg:
                        t($currentTranslations, "alrt_cligli_div_tight_msg") ||
                        "Credit tightening (CLI↓) while global liquidity expands (GLI↑)",
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
                title:
                    t($currentTranslations, "alrt_regime_transition_title") ||
                    "REGIME TRANSITION",
                msg:
                    t($currentTranslations, "alrt_regime_transition_msg") ||
                    "High acceleration detected - imminent regime change likely",
                severity: "high",
            });
        }

        // 4. BTC Extreme Valuation
        if (btcZscore !== null) {
            if (btcZscore > 2) {
                alertList.push({
                    type: "signal",
                    icon: "📈",
                    title:
                        t($currentTranslations, "alrt_btc_overvalued_title") ||
                        "BTC OVERVALUED",
                    msg: (
                        t($currentTranslations, "alrt_btc_overvalued_msg") ||
                        "BTC at +{zscore}σ - Consider profit-taking"
                    ).replace("{zscore}", String(formatValue(btcZscore, 1))),
                    severity: "high",
                });
            } else if (btcZscore < -2) {
                alertList.push({
                    type: "signal",
                    icon: "📉",
                    title:
                        t($currentTranslations, "alrt_btc_undervalued_title") ||
                        "BTC UNDERVALUED",
                    msg: (
                        t($currentTranslations, "alrt_btc_undervalued_msg") ||
                        "BTC at {zscore}σ - Potential accumulation zone"
                    ).replace("{zscore}", String(formatValue(btcZscore, 1))),
                    severity: "high",
                });
            } else if (btcZscore < -1.5) {
                alertList.push({
                    type: "info",
                    icon: "👀",
                    title:
                        t($currentTranslations, "alrt_btc_value_zone_title") ||
                        "BTC APPROACHING VALUE",
                    msg: (
                        t($currentTranslations, "alrt_btc_value_zone_msg") ||
                        "BTC at {zscore}σ - Approaching accumulation zone"
                    ).replace("{zscore}", String(formatValue(btcZscore, 1))),
                    severity: "medium",
                });
            }
        }

        // 5. CB Concentration Risk
        if (cbHHI !== null && cbHHI > 0.25) {
            alertList.push({
                type: "warning",
                icon: "⚠️",
                title:
                    t($currentTranslations, "alrt_cb_concentration_title") ||
                    "CB CONCENTRATION",
                msg: (
                    t($currentTranslations, "alrt_cb_concentration_msg") ||
                    "Single CB dominating liquidity flows (HHI: {hhi}%)"
                ).replace("{hhi}", String(formatValue(cbHHI * 100, 0))),
                severity: "medium",
            });
        }

        // 6. Low CB Diffusion
        if (cbDiffusion !== null && cbDiffusion < 0.3) {
            alertList.push({
                type: "warning",
                icon: "📉",
                title:
                    t($currentTranslations, "alrt_cb_breadth_low_title") ||
                    "LOW CB BREADTH",
                msg: (
                    t($currentTranslations, "alrt_cb_breadth_low_msg") ||
                    "Only {breadth}% of CBs expanding - narrow liquidity base"
                ).replace(
                    "{breadth}",
                    String(formatValue(cbDiffusion * 100, 0)),
                ),
                severity: "medium",
            });
        }

        // 7. Repo Stress
        if (repoStressLevel.class !== "low") {
            alertList.push({
                type: repoStressLevel.class === "high" ? "danger" : "warning",
                icon: "🏛️",
                title:
                    t($currentTranslations, repoStressLevel.key) ||
                    `REPO ${repoStressLevel.label}`,
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
                    title:
                        t($currentTranslations, "alrt_infl_elevated_title") ||
                        "INFLATION ELEVATED",
                    msg: (
                        t($currentTranslations, "alrt_infl_elevated_msg") ||
                        "10Y Breakeven at {be}% - Above Fed target"
                    ).replace("{be}", String(formatValue(tipsBreakeven, 2))),
                    severity: "medium",
                });
            } else if (tipsBreakeven < 1.8) {
                alertList.push({
                    type: "info",
                    icon: "❄️",
                    title:
                        t($currentTranslations, "alrt_disinfl_risk_title") ||
                        "DISINFLATION RISK",
                    msg: (
                        t($currentTranslations, "alrt_disinfl_risk_msg") ||
                        "10Y Breakeven at {be}% - Below target, watch for easing"
                    ).replace("{be}", String(formatValue(tipsBreakeven, 2))),
                    severity: "medium",
                });
            }
        }

        // 9. VIX Spike
        const vixValue = getLatestValue($dashboardData.vix?.values);
        if (vixValue !== null && vixValue > 25) {
            alertList.push({
                type: "danger",
                icon: "🎭",
                title:
                    t($currentTranslations, "alrt_vix_spike_title") ||
                    "ELEVATED VIX",
                msg: (
                    t($currentTranslations, "alrt_vix_spike_msg") ||
                    "VIX at {vix} - Heightened market fear"
                ).replace("{vix}", String(formatValue(vixValue, 1))),
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
    <!-- 0. EXECUTIVE NARRATIVE (NEW) -->
    <!-- ================================================================== -->
    <div class="narrative-assessment" class:dark={$darkMode}>
        <div class="narrative-main">
            <div class="narrative-headline">
                <span class="label"
                    >{$currentTranslations.market_assessment ||
                        "MARKET ASSESSMENT"}</span
                >
                <h2>{getAssessmentText(assessment.headline)}</h2>
                <div class="recommendation-badge">
                    {getAssessmentText(assessment.recommendation)}
                </div>
            </div>
            <div class="narrative-details">
                <div class="detail-group risks">
                    <span class="group-title"
                        >⚠️ {$currentTranslations.top_risks}</span
                    >
                    <ul>
                        {#each assessment.key_risks as risk}
                            <li>{getAssessmentText(risk)}</li>
                        {/each}
                    </ul>
                </div>
                <div class="detail-group positives">
                    <span class="group-title"
                        >✅ {$currentTranslations.supportive_factors ||
                            "SUPPORTIVE FACTORS"}</span
                    >
                    <ul>
                        {#each assessment.key_positives as positive}
                            <li>{getAssessmentText(positive)}</li>
                        {/each}
                    </ul>
                </div>
            </div>
        </div>

        <div class="catalyst-next-7d">
            <div class="panel-header">
                <h3>
                    🗓️ {$currentTranslations.next_7d_catalysts ||
                        "Next 7 Days Catalysts"}
                </h3>
            </div>
            {#if next7dSettlements.length > 0}
                <div class="catalyst-summary">
                    <div class="summ-item">
                        <span class="l"
                            >{$currentTranslations.settlements ||
                                "Settlements"}</span
                        >
                        <span class="v"
                            >{formatValue(totalNext7dAmount, 1, "B")}</span
                        >
                    </div>
                    <div class="summ-item">
                        <span class="l"
                            >{$currentTranslations.rrp_buffer ||
                                "RRP Buffer"}</span
                        >
                        <span class="v">{formatValue(rrpBuffer, 0, "B")}</span>
                    </div>
                </div>
                <div class="settlement-mini-table">
                    {#each next7dSettlements as s}
                        <div class="s-row">
                            <span class="s-date"
                                >{new Date(s.date).toLocaleDateString(
                                    undefined,
                                    { month: "short", day: "numeric" },
                                )}</span
                            >
                            <span class="s-type">{s.types}</span>
                            <span class="s-amt">${s.amount}B</span>
                            <span class="s-risk {s.risk_level}"
                                >{s.risk_level.toUpperCase()}</span
                            >
                        </div>
                    {/each}
                </div>
            {:else}
                <div class="no-catalysts">
                    {$currentTranslations.no_major_settlements ||
                        "No major settlements next 7d"}
                </div>
            {/if}
        </div>
    </div>

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
                <div class="score-inner">
                    <span class="score-value"
                        >{formatValue(regimeScore, 0)}</span
                    >
                    <span class="confidence-label"
                        >{formatValue(regimeDiagnostics.confidence, 0)}% {$currentTranslations.confidence ||
                            "Conf."}</span
                    >
                </div>
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
                <span class="comp-label"
                    >{$currentTranslations.regime_liquidity}</span
                >
                <span
                    class="comp-value"
                    class:positive={regimeDiagnostics.liquidity_z > 0}
                    class:negative={regimeDiagnostics.liquidity_z < 0}
                >
                    {formatDelta(regimeDiagnostics.liquidity_z)}σ
                </span>
            </div>
            <div class="component">
                <span class="comp-label"
                    >{$currentTranslations.regime_credit}</span
                >
                <span
                    class="comp-value"
                    class:positive={regimeDiagnostics.credit_z > 0}
                    class:negative={regimeDiagnostics.credit_z < 0}
                >
                    {formatDelta(regimeDiagnostics.credit_z)}σ
                </span>
            </div>
            <div class="component">
                <span class="comp-label"
                    >{$currentTranslations.regime_brakes}</span
                >
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
                <span class="fomc-label"
                    >{$currentTranslations.next || "Next"} FOMC</span
                >
                {#if fomcCountdown.isToday}
                    <span class="fomc-today"
                        >🔴 {$currentTranslations.today || "TODAY"}</span
                    >
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
                            <span class="rate-label"
                                >{$currentTranslations.target || "Target"}</span
                            >
                            <span class="rate-value target"
                                >{formatValue(currentFedRate, 2, "%")}</span
                            >
                        </div>
                    {/if}
                    {#if currentSOFR}
                        <div class="fed-rate">
                            <span class="rate-label">SOFR</span>
                            <span class="rate-value sofr"
                                >{formatValue(currentSOFR, 2, "%")}</span
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
                    <span class="prob-label"
                        >{$currentTranslations.prob_cut || "Cut"}</span
                    >
                    <span class="prob-value"
                        >{nextMeetingProbs?.cut ?? "—"}%</span
                    >
                    {#if nextMeetingProbs?.roc1m?.cut !== undefined}
                        <span
                            class="prob-change"
                            class:up={nextMeetingProbs.roc1m.cut > 0}
                            class:down={nextMeetingProbs.roc1m.cut < 0}
                        >
                            {nextMeetingProbs.roc1m.cut > 0
                                ? "+"
                                : ""}{nextMeetingProbs.roc1m.cut.toFixed(0)}
                        </span>
                    {/if}
                </div>
                <div
                    class="prob-item hold"
                    class:high={nextMeetingProbs?.hold > 50}
                >
                    <span class="prob-label"
                        >{$currentTranslations.prob_hold || "Hold"}</span
                    >
                    <span class="prob-value"
                        >{nextMeetingProbs?.hold ?? "—"}%</span
                    >
                </div>
                {#if nextMeetingProbs?.hike > 5}
                    <div class="prob-item hike">
                        <span class="prob-label"
                            >{$currentTranslations.prob_hike || "Hike"}</span
                        >
                        <span class="prob-value">{nextMeetingProbs.hike}%</span>
                    </div>
                {/if}
            </div>
        </div>

        <div class="signal-summary">
            <span class="summary-label"
                >{$currentTranslations.nav_regimes || "Signals"}</span
            >
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
    <!-- 2. LIQUIDITY ENGINE (4-Card Block) (NEW) -->
    <!-- ================================================================== -->
    <div class="stats-grid liquidity-engine">
        <StatsCard
            title={$currentTranslations.indicator_fed || "FED ASSETS"}
            value={getLatestValue($dashboardData.gli?.fed)}
            change={calcDelta($dashboardData.gli?.fed, 5)}
            period="1w"
            suffix="T"
            icon="🏦"
        />
        <StatsCard
            title={$currentTranslations.stat_bank_reserves || "BANK RESERVES"}
            value={getLatestValue($dashboardData.us_net_liq_reserves)}
            change={calcDelta($dashboardData.us_net_liq_reserves, 5)}
            period="1w"
            suffix="T"
            icon="🛡️"
        />
        <StatsCard
            title={$currentTranslations.stat_rrp_usage || "ON RRP USAGE"}
            value={getLatestValue($dashboardData.us_net_liq_rrp)}
            change={calcDelta($dashboardData.us_net_liq_rrp, 5)}
            period="1w"
            suffix="T"
            icon="📉"
        />
        <StatsCard
            title={$currentTranslations.stat_tga_balance || "TGA BALANCE"}
            value={getLatestValue($dashboardData.us_net_liq_tga)}
            change={calcDelta($dashboardData.us_net_liq_tga, 5)}
            period="1w"
            suffix="T"
            icon="🏛️"
        />
    </div>

    <!-- ================================================================== -->
    <!-- EARLY WARNINGS & ALERTS (TOP) -->
    <!-- ================================================================== -->
    {#if alerts.length > 0}
        <div class="alerts-panel">
            <div class="alerts-header">
                <h3>
                    ⚠️ {$currentTranslations.alerts || "Alerts"} ({alerts.length})
                </h3>
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
                <h3>
                    📊 {$currentTranslations.stress_panel_title ||
                        "Market Stress Dashboard"}
                </h3>
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
                <div class="title-with-score">
                    <h3>
                        📡 {$currentTranslations.signal_matrix_title ||
                            "Signal Matrix"}
                    </h3>
                    <div class="weighted-score-pill {aggregateSignal}">
                        {weightedScoreInfo.score > 0
                            ? "+"
                            : ""}{weightedScoreInfo.score}
                    </div>
                </div>
                <div class="top-drivers-mini">
                    {#each weightedScoreInfo.topDrivers as driver}
                        <div class="driver-tag {driver.state}">
                            {driver.label}
                        </div>
                    {/each}
                </div>
                <div class="aggregate-badge {aggregateSignal}">
                    {aggregateSignal === "bullish"
                        ? `🟢 ${$currentTranslations.risk_on_label || "RISK-ON"}`
                        : aggregateSignal === "bearish"
                          ? `🔴 ${$currentTranslations.risk_off_label || "RISK-OFF"}`
                          : `⚪ ${$currentTranslations.neutral_label || "NEUTRAL"}`}
                </div>
            </div>
            <div class="signal-table-container">
                <table class="signal-table">
                    <thead>
                        <tr>
                            <th
                                >{$currentTranslations.indicator_col ||
                                    "Indicator"}</th
                            >
                            <th>{$currentTranslations.value_col || "Value"}</th>
                            <th>{$currentTranslations.delta_col || "Δ1M"}</th>
                            <th
                                >{$currentTranslations.signal_col ||
                                    "Signal"}</th
                            >
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
                                    {formatValue(signal.value, 2)}
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
                <h3>
                    ⚡ {$currentTranslations.flow_momentum_title ||
                        "Flow Momentum"}
                </h3>
            </div>
            <table class="flow-table">
                <thead>
                    <tr>
                        <th
                            >{$currentTranslations.aggregate_col ||
                                "Aggregate"}</th
                        >
                        <th
                            >{$currentTranslations.impulse_4w_col ||
                                "Impulse 4W"}</th
                        >
                        <th
                            >{$currentTranslations.impulse_13w_col ||
                                "Impulse 13W"}</th
                        >
                        <th>{$currentTranslations.accel_col || "Accel"}</th>
                        <th>{$currentTranslations.zscore_col || "Z-Score"}</th>
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
                <h4>
                    {$currentTranslations.cb_contrib_title ||
                        "CB Contribution to ΔGLI (13W)"}
                </h4>
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
        <!-- ================================================================== -->
        <!-- 6. REPO & PLUMBING (REDESIGNED) -->
        <!-- ================================================================== -->
        <div class="panel repo-panel">
            <div class="panel-header">
                <h3>
                    🏛️ {$currentTranslations.plumbing_title ||
                        "Plumbing: Repo & Corridor"}
                </h3>
                <div class="repo-status {repoStressLevel.class}">
                    {repoStressLevel.label}
                </div>
            </div>

            <div class="repo-split">
                <div class="repo-sub-section">
                    <span class="sub-label"
                        >{$currentTranslations.corridor_status_bps ||
                            "CORRIDOR STATUS (BPS)"}</span
                    >
                    <div class="corridor-visual">
                        <div class="c-line ceiling">
                            <span class="l">SRF</span>
                            <span class="v"
                                >{formatValue(
                                    repoMetrics.srfRate,
                                    2,
                                    "%",
                                )}</span
                            >
                        </div>
                        <div class="c-line sofr">
                            <span class="l">SOFR</span>
                            <span class="v"
                                >{formatValue(repoMetrics.sofr, 3, "%")}</span
                            >
                            <span class="delta"
                                >{$currentTranslations.gap_label || "Gap"}: {gapToCeiling ??
                                    "—"}bps</span
                            >
                        </div>
                        <div class="c-line floor">
                            <span class="l">IORB</span>
                            <span class="v"
                                >{formatValue(repoMetrics.iorb, 2, "%")}</span
                            >
                            <span class="delta"
                                >{$currentTranslations.spread_label || "Spr"}: {sofrIorbSpread ??
                                    "—"}bps</span
                            >
                        </div>
                    </div>
                </div>

                <div class="repo-sub-section">
                    <span class="sub-label"
                        >{$currentTranslations.liquidity_flows ||
                            "LIQUIDITY FLOWS"}</span
                    >
                    <div class="flow-metrics-grid">
                        <div class="f-metric">
                            <span class="l"
                                >{$currentTranslations.rrp_1w_label ||
                                    "ΔRRP (1w)"}</span
                            >
                            <span
                                class="v"
                                class:drain={calcDelta(
                                    $dashboardData.us_net_liq_rrp,
                                    5,
                                ) > 0}
                                class:inject={calcDelta(
                                    $dashboardData.us_net_liq_rrp,
                                    5,
                                ) < 0}
                            >
                                {formatDelta(
                                    calcDelta(
                                        $dashboardData.us_net_liq_rrp,
                                        5,
                                    ) * 1000,
                                    0,
                                )}B
                            </span>
                        </div>
                        <div class="f-metric">
                            <span class="l"
                                >{$currentTranslations.srf_usage_label ||
                                    "SRF Usage"}</span
                            >
                            <span
                                class="v"
                                class:warning={repoMetrics.srfUsage > 0}
                                >{formatValue(
                                    repoMetrics.srfUsage,
                                    1,
                                    "B",
                                )}</span
                            >
                        </div>
                        <div class="f-metric">
                            <span class="l"
                                >{$currentTranslations.sofr_vol_label ||
                                    "SOFR Vol"}</span
                            >
                            <span class="v">${repoMetrics.sofrVolume}B</span>
                        </div>
                        <div class="f-metric">
                            <span class="l"
                                >{$currentTranslations.net_repo_z_label ||
                                    "Net Repo Z"}</span
                            >
                            <span class="v"
                                >{formatValue(
                                    repoMetrics.netRepoZscore,
                                    2,
                                    "σ",
                                )}</span
                            >
                        </div>
                    </div>
                </div>
            </div>
            <p class="repo-desc">{repoStressLevel.desc}</p>
        </div>

        <!-- ================================================================== -->
        <!-- 6b. BTC FUNDAMENTALS (NEW) -->
        <!-- ================================================================== -->
        <div class="panel btc-panel">
            <div class="panel-header">
                <h3>
                    ₿ {$currentTranslations.btc_fundamentals_title ||
                        "BTC Fundamentals-Lite"}
                </h3>
                <div
                    class="btc-signal-badge"
                    class:cheap={btcZscore < -1}
                    class:expensive={btcZscore > 1}
                >
                    {btcZscore > 1
                        ? $currentTranslations.valuation_premium || "PREMIUM"
                        : btcZscore < -1
                          ? $currentTranslations.valuation_discount ||
                            "DISCOUNT"
                          : $currentTranslations.valuation_fair || "FAIR VALUE"}
                </div>
            </div>
            <div class="btc-quant-grid">
                <div class="btc-q-item">
                    <span class="l"
                        >{$currentTranslations.price_vs_fair ||
                            "Price vs Fair"}</span
                    >
                    <span
                        class="v"
                        class:positive={btcDeviation > 0}
                        class:negative={btcDeviation < 0}
                    >
                        {formatDelta(btcDeviation, 1)}%
                    </span>
                </div>
                <div class="btc-q-item">
                    <span class="l"
                        >{$currentTranslations.valuation_z ||
                            "Valuation Z"}</span
                    >
                    <span class="v">{formatValue(btcZscore, 2, "σ")}</span>
                </div>
                <div class="btc-q-item">
                    <span class="l"
                        >{$currentTranslations.drawdown || "Drawdown"}</span
                    >
                    <span class="v"
                        >{formatValue(
                            getLatestValue($dashboardData.btc?.drawdown),
                            1,
                            "%",
                        )}</span
                    >
                </div>
                <div class="btc-q-item">
                    <span class="l"
                        >{$currentTranslations.realized_vol ||
                            "Realized Vol"}</span
                    >
                    <span class="v"
                        >{formatValue(
                            getLatestValue(
                                $dashboardData.btc?.realized_vol_30d,
                            ),
                            1,
                            "%",
                        )}</span
                    >
                </div>
            </div>
        </div>

        <!-- ================================================================== -->
        <!-- 7. INFLATION EXPECTATIONS -->
        <!-- ================================================================== -->
        <div class="panel inflation-panel wide">
            <div class="panel-header">
                <h3>
                    🔥 {$currentTranslations.inflation_expect_title ||
                        "Inflation Expectations"}
                </h3>
                <div class="inflation-signal {inflationCurveSignal.class}">
                    {$currentTranslations.curve_label || "Curve"}: {inflationCurveSignal.label}
                    ({formatDelta(inflationCurveSignal.spread, 2)}pp)
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
                    <span class="target-badge"
                        >{$currentTranslations.fed_target_label ||
                            "Fed Target"}: 2%</span
                    >
                </div>
            </div>

            <table class="inflation-table">
                <thead>
                    <tr>
                        <th>{$currentTranslations.metric_col || "Metric"}</th>
                        <th>{$currentTranslations.source_col || "Source"}</th>
                        <th>{$currentTranslations.value_col || "Value"}</th>
                        <th
                            >{$currentTranslations.delta_pp_col ||
                                "Δ1M (pp)"}</th
                        >
                        <th>{$currentTranslations.roc_1m_col || "ROC 1M"}</th>
                        <th>{$currentTranslations.roc_3m_col || "ROC 3M"}</th>
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

    /* ========== EXECUTIVE NARRATIVE ========== */
    .narrative-assessment {
        display: grid;
        grid-template-columns: 1fr 400px;
        gap: 20px;
        background: linear-gradient(
            135deg,
            var(--bg-secondary, #1e293b) 0%,
            var(--bg-tertiary, #334155) 100%
        );
        border-radius: 20px;
        border: 1px solid var(--border-color, #475569);
        overflow: hidden;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }

    .narrative-main {
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 20px;
    }

    .narrative-headline {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .narrative-headline .label {
        font-size: 0.75rem;
        font-weight: 800;
        color: #60a5fa;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    .narrative-headline h2 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--text-primary, #f1f5f9);
        line-height: 1.2;
    }

    .recommendation-badge {
        display: inline-block;
        align-self: flex-start;
        margin-top: 8px;
        padding: 6px 14px;
        background: rgba(96, 165, 250, 0.15);
        color: #60a5fa;
        border: 1px solid rgba(96, 165, 250, 0.3);
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .narrative-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
    }

    .detail-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }

    .group-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .detail-group ul {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .detail-group li {
        font-size: 0.9rem;
        color: var(--text-secondary, #cbd5e1);
        padding-left: 12px;
        position: relative;
    }

    .detail-group.risks li {
        border-left: 2px solid #ef4444;
    }

    .detail-group.positives li {
        border-left: 2px solid #10b981;
    }

    /* ========== CATALYSTS ========== */
    .catalyst-next-7d {
        background: rgba(0, 0, 0, 0.2);
        padding: 24px;
        border-left: 1px solid var(--border-color, #475569);
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    .catalyst-summary {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
    }

    .summ-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
        background: var(--bg-secondary, #1e293b);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--border-color, #334155);
    }

    .summ-item .l {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .summ-item .v {
        font-size: 1rem;
        font-weight: 700;
        font-family: monospace;
    }

    .settlement-mini-table {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .s-row {
        display: grid;
        grid-template-columns: 60px 1fr 60px 70px;
        align-items: center;
        gap: 10px;
        padding: 8px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        font-size: 0.8rem;
    }

    .s-date {
        font-weight: 600;
        color: var(--text-muted);
    }

    .s-type {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--text-secondary);
    }

    .s-amt {
        font-weight: 700;
        font-family: monospace;
        text-align: right;
    }

    .s-risk {
        font-size: 0.65rem;
        font-weight: 800;
        text-align: center;
        padding: 2px 4px;
        border-radius: 4px;
    }

    .s-risk.low {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }

    .s-risk.medium {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
    }

    .s-risk.high {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    .no-catalysts {
        text-align: center;
        padding: 40px 20px;
        color: var(--text-muted);
        font-style: italic;
        font-size: 0.9rem;
    }

    @media (max-width: 1000px) {
        .narrative-assessment {
            grid-template-columns: 1fr;
        }
        .catalyst-next-7d {
            border-left: none;
            border-top: 1px solid var(--border-color, #475569);
        }
        .narrative-details {
            grid-template-columns: 1fr;
        }
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

    .score-inner {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    .score-value {
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-primary, #f1f5f9);
        line-height: 1.1;
    }

    .confidence-label {
        font-size: 0.55rem;
        font-weight: 700;
        color: var(--text-muted, #94a3b8);
        text-transform: uppercase;
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

    /* Signal Matrix Header Styles */
    .title-with-score {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .weighted-score-pill {
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 0.9rem;
        font-weight: 800;
        font-family: monospace;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }

    .weighted-score-pill.bullish {
        background: #10b981;
        color: white;
    }
    .weighted-score-pill.bearish {
        background: #ef4444;
        color: white;
    }
    .weighted-score-pill.neutral {
        background: #6b7280;
        color: white;
    }

    .top-drivers-mini {
        display: flex;
        gap: 6px;
    }

    .driver-tag {
        font-size: 0.6rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .driver-tag.bullish {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }
    .driver-tag.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }

    /* Repo Split Layout */
    .repo-split {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin-bottom: 8px;
    }

    .repo-sub-section {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .sub-label {
        font-size: 0.6rem;
        font-weight: 800;
        color: var(--text-muted);
        letter-spacing: 1px;
    }

    .corridor-visual {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    .c-line {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 10px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.03);
    }

    .c-line .l {
        font-size: 0.7rem;
        width: 40px;
        color: var(--text-muted);
    }
    .c-line .v {
        font-family: monospace;
        font-weight: 700;
    }
    .c-line .delta {
        font-size: 0.65rem;
        color: var(--text-muted);
        margin-left: auto;
    }

    .c-line.ceiling {
        border-left: 3px solid #ef4444;
    }
    .c-line.sofr {
        border-left: 3px solid #3b82f6;
        background: rgba(59, 130, 246, 0.05);
    }
    .c-line.floor {
        border-left: 3px solid #10b981;
    }

    .flow-metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
    }

    .f-metric {
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }

    .f-metric .l {
        font-size: 0.6rem;
        color: var(--text-muted);
    }
    .f-metric .v {
        font-size: 0.9rem;
        font-weight: 700;
        font-family: monospace;
    }
    .f-metric .v.drain {
        color: #ef4444;
    }
    .f-metric .v.inject {
        color: #10b981;
    }

    /* BTC Quant Grid */
    .btc-signal-badge {
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 800;
    }
    .btc-signal-badge.cheap {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .btc-signal-badge.expensive {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    .btc-quant-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
    }

    .btc-q-item {
        background: rgba(255, 255, 255, 0.03);
        padding: 10px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        border: 1px solid var(--border-color);
    }

    .btc-q-item .l {
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
    }
    .btc-q-item .v {
        font-size: 1.1rem;
        font-weight: 800;
        font-family: monospace;
    }
    .btc-q-item .v.positive {
        color: #ef4444;
    }
    .btc-q-item .v.negative {
        color: #10b981;
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
    .inflation-signal.warning {
        background: rgba(245, 158, 11, 0.3);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.5);
    }
    .inflation-signal.danger {
        background: rgba(239, 68, 68, 0.3);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.5);
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
