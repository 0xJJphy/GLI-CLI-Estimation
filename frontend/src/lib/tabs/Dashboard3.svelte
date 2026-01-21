<script>
    /**
     * Dashboard3.svelte - QUANT EXECUTIVE DASHBOARD (Component-Based)
     *
     * Clean implementation using extracted reusable components.
     * This is a refactored version of Dashboard2.svelte with better maintainability.
     */
    import StatsCard from "../components/StatsCard.svelte";

    // Import extracted dashboard components
    import {
        RegimeStatusBar,
        StressPanel,
        SignalMatrixPanel,
        AlertsPanel,
        FlowMomentumPanel,
        RepoPlumbingPanel,
    } from "../components/dashboard";

    // Import stores
    import { dashboardData } from "../../stores/dataStore";
    import {
        darkMode,
        currentTranslations,
        t,
    } from "../../stores/settingsStore";

    // Import utilities
    import { getLatestValue } from "../utils/helpers.js";
    import { calcDelta, formatValue } from "../utils/dashboardHelpers.js";
    import { onMount } from "svelte";

    // ========================================================================
    // FOMC COUNTDOWN
    // ========================================================================
    let fomcCountdown = { days: 0, hours: 0, isToday: false };
    let nextFomcHasSEP = false;
    let nextMeetingProbs = null;

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
                nextFomcHasSEP = meeting.has_sep || false;
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

    // ========================================================================
    // REGIME COMPUTATIONS
    // ========================================================================
    $: regimeScore = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr?.score?.length) return 50;
        return mr.score[mr.score.length - 1] ?? 50;
    })();

    $: regimeCode = (() => {
        const mr = $dashboardData.macro_regime;
        if (!mr?.regime_code?.length) return 0;
        return mr.regime_code[mr.regime_code.length - 1] ?? 0;
    })();

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
        const getLatest = (arr) =>
            arr?.length ? (arr[arr.length - 1] ?? 0) : 0;
        const tz = getLatest(mr.total_z);
        return {
            liquidity_z: getLatest(mr.liquidity_z),
            credit_z: getLatest(mr.credit_z),
            brakes_z: getLatest(mr.brakes_z),
            total_z: tz,
            confidence: Math.min(100, Math.abs(tz) * 40),
        };
    })();

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
        let delta = data.delta_1m ?? data.roc_1m ?? null;
        if (delta === null && percentileSeries.length > 22) {
            const current = percentileSeries[percentileSeries.length - 1];
            const past = percentileSeries[percentileSeries.length - 1 - 22];
            if (current !== null && past !== null) delta = current - past;
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
        return {
            score: Math.round(score * 100),
            topDrivers: drivers
                .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
                .slice(0, 3),
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
    // REPO METRICS
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
        sofr: getLatestValue($dashboardData.repo_stress?.sofr) ?? 0,
        iorb: getLatestValue($dashboardData.repo_stress?.iorb) ?? 0,
        srfRate: getLatestValue($dashboardData.repo_stress?.srf_rate) ?? 0,
        rrpAward: getLatestValue($dashboardData.repo_stress?.rrp_award) ?? 0,
        sofrVolume:
            getLatestValue($dashboardData.repo_stress?.sofr_volume) ?? 0,
    };

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
        const sofrIorbSpread =
            repoMetrics.sofr && repoMetrics.iorb
                ? (repoMetrics.sofr - repoMetrics.iorb) * 100
                : 0;
        if (sofrIorbSpread > 5)
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
    // ALERTS
    // ========================================================================
    $: alerts = (() => {
        const alertList = [];
        // Critical Stress
        if (totalStress >= 15) {
            alertList.push({
                type: "danger",
                icon: "🚨",
                title:
                    t($currentTranslations, "alrt_critical_stress_title") ||
                    "CRITICAL STRESS",
                msg: (
                    t($currentTranslations, "alrt_critical_stress_msg") ||
                    "Total stress at {score}/27"
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
                    "Total stress at {score}/27"
                ).replace("{score}", String(totalStress)),
                severity: "high",
            });
        }
        // Repo Stress
        if (repoStressLevel.key) {
            alertList.push({
                type: "warning",
                icon: "🏛️",
                title: repoStressLevel.label,
                msg: repoStressLevel.desc,
                severity: "medium",
            });
        }
        return alertList.slice(0, 6);
    })();
</script>

<div class="dashboard-quant" class:dark={$darkMode}>
    <!-- REGIME STATUS BAR -->
    <RegimeStatusBar
        {regimeScore}
        {regimeCode}
        {regimeDiagnostics}
        {regimeTrend}
        {fomcCountdown}
        {nextFomcHasSEP}
        {nextMeetingProbs}
        {currentFedRate}
        {currentSOFR}
        {bullCount}
        {bearCount}
    />

    <!-- LIQUIDITY ENGINE (StatsCards) -->
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

    <!-- ALERTS PANEL -->
    <AlertsPanel {alerts} />

    <!-- MAIN PANELS GRID -->
    <div class="dashboard-grid">
        <StressPanel {stressDimensions} {totalStress} maxStress={27} />

        <SignalMatrixPanel
            {signalMatrix}
            {weightedScoreInfo}
            {aggregateSignal}
        />

        <FlowMomentumPanel {flowData} {cbContributions} />

        <RepoPlumbingPanel
            {repoMetrics}
            {repoStressLevel}
            rrpSeries={$dashboardData.us_net_liq_rrp}
        />
    </div>
</div>

<style>
    .dashboard-quant {
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-height: 100%;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
    }

    @media (max-width: 1200px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 600px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }

    .dashboard-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
    }

    @media (max-width: 1000px) {
        .dashboard-grid {
            grid-template-columns: 1fr;
        }
    }
</style>
