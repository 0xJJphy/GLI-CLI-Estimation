<script>
    /**
     * RegimesTab.svelte
     * Displays Macro Regime V2, CLI V2, and Historical Stress Dashboard.
     * Allows switching between V2A (Inflation-Aware) and V2B (Growth-Aware).
     * All text is translatable and reactive to language changes.
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import { getCutoffDate } from "../utils/helpers.js";

    export let dashboardData = {};
    export let darkMode = true;
    export let translations = {};
    export let language = "en";

    // ============================================================
    // STATE VARIABLES
    // ============================================================
    let regimeVersion = "v2a";
    let cliVersion = "both";
    let regimeScoreRange = "3Y";
    let cliComparisonRange = "3Y";
    let blockDecompRange = "1Y";
    let stressHistoricalRange = "3Y";
    let btcRegimeV2aRange = "5Y";
    let btcRegimeV2bRange = "5Y";

    // Offset for BTC overlay (shift regime relative to BTC)
    let btcOffsetDays = 0;
    let bestOffset = 0;

    // Offset for Regime Score chart (shift background forward)
    let regimeOffsetDays = 0;

    // Card container references for full-card download feature
    let regimeScoreCard;
    let cliComparisonCard;
    let blockDecompCard;
    let stressHistCard;
    let btcV2aCard;
    let btcV2bCard;

    // ============================================================
    // REACTIVE TRANSLATION HELPER (fixes language switching)
    // ============================================================
    $: t = (key, fallback) => translations[key] || fallback;

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================
    function getLastDate() {
        const dates = dashboardData.dates;
        if (!dates || dates.length === 0) return "N/A";
        return dates[dates.length - 1]?.split("T")[0] || "N/A";
    }

    function filterByRange(series, range) {
        const dates = dashboardData.dates;
        if (!dates || !series || series.length === 0) return series;
        if (range === "ALL") return series;
        const cutoff = getCutoffDate(range);
        const indices = [];
        for (let i = 0; i < dates.length; i++) {
            if (new Date(dates[i]) >= cutoff) indices.push(i);
        }
        return indices.map((i) => series[i]);
    }

    function getFilteredDates(range) {
        return filterByRange(dashboardData.dates, range);
    }

    function getLatestValue(arr, decimals = 2) {
        if (!arr || arr.length === 0) return "N/A";
        const vals = arr.filter((v) => v !== null && v !== undefined);
        if (vals.length === 0) return "N/A";
        const val = vals[vals.length - 1];
        return typeof val === "number" ? val.toFixed(decimals) : val;
    }

    // Get signal label - now reactive to translations
    $: getSignalLabel = (code) => {
        if (code === 1)
            return {
                text: t("regime_bullish_label", "BULLISH"),
                class: "bullish",
                emoji: "🟢",
                desc: t(
                    "regime_bullish_desc",
                    "Dual expansion: Liquidity expanding, credit easing.",
                ),
            };
        if (code === -1)
            return {
                text: t("regime_bearish_label", "BEARISH"),
                class: "bearish",
                emoji: "🔴",
                desc: t(
                    "regime_bearish_desc",
                    "Dual contraction: Liquidity contracting, credit tightening.",
                ),
            };
        return {
            text: t("regime_neutral_label", "NEUTRAL"),
            class: "neutral",
            emoji: "⚪",
            desc: t(
                "regime_neutral_desc",
                "Mixed/divergent regime: Conflicting signals.",
            ),
        };
    };

    function getStressLevel(score) {
        if (score >= 15)
            return {
                text: t("stress_critical", "CRITICAL"),
                class: "critical",
            };
        if (score >= 10)
            return { text: t("stress_high", "HIGH"), class: "high" };
        if (score >= 5)
            return {
                text: t("stress_moderate", "MODERATE"),
                class: "moderate",
            };
        return { text: t("stress_low", "LOW"), class: "low" };
    }

    // Calculate best offset (correlation with BTC returns)
    function calculateBestOffset() {
        const btcPrice = dashboardData.btc?.price;
        const scores =
            regimeVersion === "v2a"
                ? dashboardData.regime_v2a?.score
                : dashboardData.regime_v2b?.score;

        if (!btcPrice || !scores || btcPrice.length < 100) return 0;

        let bestCorr = -Infinity;
        let bestOff = 0;

        // Test offsets from 0 to 90 days
        for (let off = 0; off <= 90; off += 5) {
            let sumXY = 0,
                sumX = 0,
                sumY = 0,
                sumX2 = 0,
                sumY2 = 0,
                n = 0;

            for (
                let i = off + 1;
                i < Math.min(btcPrice.length, scores.length);
                i++
            ) {
                const btcRet =
                    btcPrice[i] && btcPrice[i - 1]
                        ? (btcPrice[i] - btcPrice[i - 1]) / btcPrice[i - 1]
                        : null;
                const score = scores[i - off];

                if (
                    btcRet !== null &&
                    score !== null &&
                    !isNaN(btcRet) &&
                    !isNaN(score)
                ) {
                    sumX += score;
                    sumY += btcRet;
                    sumXY += score * btcRet;
                    sumX2 += score * score;
                    sumY2 += btcRet * btcRet;
                    n++;
                }
            }

            if (n > 50) {
                const corr =
                    (n * sumXY - sumX * sumY) /
                    (Math.sqrt(n * sumX2 - sumX * sumX) *
                        Math.sqrt(n * sumY2 - sumY * sumY));
                if (corr > bestCorr) {
                    bestCorr = corr;
                    bestOff = off;
                }
            }
        }
        return bestOff;
    }

    // Apply offset to set best value
    function applyBestOffset() {
        bestOffset = calculateBestOffset();
        btcOffsetDays = bestOffset;
    }

    // Create regime shapes with SCORE-BASED INTENSITY
    // offsetDays extends the LAST regime block into the future (not shifting all shapes)
    function createRegimeShapes(scores, range, isDarkMode, offsetDays = 0) {
        if (!scores || !dashboardData.dates) return [];
        const filteredDates = getFilteredDates(range);
        const filteredScores = filterByRange(scores, range);
        if (!filteredDates || !filteredScores || filteredDates.length === 0)
            return [];

        const shapes = [];
        let currentDirection = null;
        let blockStartIdx = 0;
        let blockScores = [];
        let lastBlockDirection = null;
        let lastBlockAvgScore = 50;

        for (let i = 0; i <= filteredDates.length; i++) {
            const score = i < filteredScores.length ? filteredScores[i] : null;
            const direction =
                score === null ? null : score >= 50 ? "bull" : "bear";

            if (direction !== currentDirection || i === filteredDates.length) {
                if (currentDirection !== null && blockScores.length > 0) {
                    const d0 = filteredDates[blockStartIdx];
                    const d1 =
                        filteredDates[Math.min(i, filteredDates.length - 1)];
                    const avgScore =
                        blockScores.reduce((a, b) => a + b, 0) /
                        blockScores.length;
                    const distanceFrom50 = Math.abs(avgScore - 50);
                    const opacity = Math.min(
                        0.45,
                        0.1 + (distanceFrom50 / 50) * 0.35,
                    );
                    const modeOpacity = isDarkMode ? opacity : opacity * 1.15;

                    const color =
                        currentDirection === "bull"
                            ? `rgba(16, 185, 129, ${modeOpacity.toFixed(2)})`
                            : `rgba(239, 68, 68, ${modeOpacity.toFixed(2)})`;

                    if (d0 && d1) {
                        shapes.push({
                            type: "rect",
                            xref: "x",
                            yref: "paper",
                            x0: d0,
                            x1: d1,
                            y0: 0,
                            y1: 1,
                            fillcolor: color,
                            line: { width: 0 },
                            layer: "below",
                        });
                    }

                    // Track last block for future extension
                    lastBlockDirection = currentDirection;
                    lastBlockAvgScore = avgScore;
                }
                currentDirection = direction;
                blockStartIdx = i;
                blockScores = score !== null ? [score] : [];
            } else if (score !== null) {
                blockScores.push(score);
            }
        }

        // Extend last block into future by offsetDays
        if (offsetDays > 0 && lastBlockDirection !== null) {
            const lastDate = new Date(filteredDates[filteredDates.length - 1]);
            const futureDate = new Date(lastDate);
            futureDate.setDate(futureDate.getDate() + offsetDays);

            const distanceFrom50 = Math.abs(lastBlockAvgScore - 50);
            const opacity = Math.min(0.45, 0.1 + (distanceFrom50 / 50) * 0.35);
            const modeOpacity = isDarkMode ? opacity : opacity * 1.15;
            const color =
                lastBlockDirection === "bull"
                    ? `rgba(16, 185, 129, ${modeOpacity.toFixed(2)})`
                    : `rgba(239, 68, 68, ${modeOpacity.toFixed(2)})`;

            shapes.push({
                type: "rect",
                xref: "x",
                yref: "paper",
                x0: lastDate.toISOString().split("T")[0],
                x1: futureDate.toISOString().split("T")[0],
                y0: 0,
                y1: 1,
                fillcolor: color,
                line: { width: 0 },
                layer: "below",
            });
        }

        return shapes;
    }

    // ============================================================
    // REACTIVE DATA
    // ============================================================
    $: currentRegime =
        regimeVersion === "v2a"
            ? dashboardData.regime_v2a
            : dashboardData.regime_v2b;

    $: latestRegimeCode = (() => {
        if (!currentRegime?.regime_code) return 0;
        const codes = currentRegime.regime_code.filter((c) => c !== null);
        return codes.length > 0 ? codes[codes.length - 1] : 0;
    })();

    $: latestScore = getLatestValue(currentRegime?.score, 1);
    $: latestLiquidity = getLatestValue(currentRegime?.liquidity_z, 2);
    $: latestCredit = getLatestValue(currentRegime?.credit_z, 2);
    $: latestBrakes = getLatestValue(currentRegime?.brakes_z, 2);
    $: latestGrowth = getLatestValue(currentRegime?.growth_z, 2);

    // Regime Score Chart - reactive to darkMode
    $: regimeScoreData = (() => {
        if (!currentRegime?.score) return [];
        const dates = getFilteredDates(regimeScoreRange);
        const score = filterByRange(currentRegime.score, regimeScoreRange);
        return [
            {
                x: dates,
                y: score,
                name:
                    regimeVersion === "v2a"
                        ? t("regime_v2a_score_title", "V2A Score")
                        : t("regime_v2b_score_title", "V2B Score"),
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
                fill: "tozeroy",
                fillcolor: darkMode
                    ? "rgba(59, 130, 246, 0.15)"
                    : "rgba(59, 130, 246, 0.1)",
            },
        ];
    })();

    // Extended X-range for regime score chart (allows showing future dates)
    $: regimeXRange = (() => {
        const dates = getFilteredDates(regimeScoreRange);
        if (!dates || dates.length === 0) return undefined;
        const startDate = dates[0];
        const lastDate = new Date(dates[dates.length - 1]);
        if (regimeOffsetDays > 0) {
            lastDate.setDate(lastDate.getDate() + regimeOffsetDays);
        }
        return [startDate, lastDate.toISOString().split("T")[0]];
    })();

    $: regimeScoreLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            range: regimeXRange,
        },
        yaxis: {
            title: t("chart_score_y", "Score"),
            range: [0, 100],
            tickvals: [20, 35, 50, 65, 80],
            color: darkMode ? "#94a3b8" : "#475569",
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        shapes: [
            ...createRegimeShapes(
                currentRegime?.score,
                regimeScoreRange,
                darkMode,
                regimeOffsetDays,
            ),
            // Static horizontal lines for reference
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
        ],
        margin: { t: 20, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // BTC + Regime V2A with Score Subplot - reactive to darkMode and offset
    $: btcRegimeV2aData = (() => {
        const btcPrice = dashboardData.btc?.price;
        const score = dashboardData.regime_v2a?.score;
        if (!btcPrice) return [];
        const dates = getFilteredDates(btcRegimeV2aRange);
        const btc = filterByRange(btcPrice, btcRegimeV2aRange);
        const scoreFiltered = filterByRange(score, btcRegimeV2aRange);

        // Extend dates for future projection when offset is applied
        let extendedDates = [...dates];
        if (btcOffsetDays > 0 && dates.length > 0) {
            const lastDate = new Date(dates[dates.length - 1]);
            for (let i = 1; i <= btcOffsetDays; i++) {
                const futureDate = new Date(lastDate);
                futureDate.setDate(futureDate.getDate() + i);
                extendedDates.push(futureDate.toISOString().split("T")[0]);
            }
        }

        return [
            // BTC Price trace (on y2)
            {
                x: dates,
                y: btc,
                name: t("btc_price", "BTC Price"),
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
                yaxis: "y2",
            },
            // Score trace (on y3 - bottom subplot)
            {
                x: dates,
                y: scoreFiltered,
                name: t("regime_score_label", "Score"),
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 1.5 },
                yaxis: "y3",
                fill: "tozeroy",
                fillcolor: "rgba(59, 130, 246, 0.12)",
            },
        ];
    })();

    // Calculate extended range for x-axis
    $: btcV2aXRange = (() => {
        const dates = getFilteredDates(btcRegimeV2aRange);
        if (!dates || dates.length === 0) return undefined;
        const startDate = dates[0];
        const lastDate = new Date(dates[dates.length - 1]);
        if (btcOffsetDays > 0) {
            lastDate.setDate(lastDate.getDate() + btcOffsetDays);
        }
        return [startDate, lastDate.toISOString().split("T")[0]];
    })();

    $: btcRegimeV2aLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            range: btcV2aXRange,
            domain: [0, 1],
        },
        yaxis: { visible: false, domain: [0.25, 1] }, // Hidden main y
        yaxis2: {
            title: t("btc_price_log", "BTC Price (log)"),
            type: "log",
            side: "right",
            overlaying: "y",
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            domain: [0.25, 1],
        },
        yaxis3: {
            title: t("chart_score_y", "Score"),
            range: [0, 100],
            side: "left",
            anchor: "x",
            domain: [0, 0.22],
            color: darkMode ? "#94a3b8" : "#475569",
            tickvals: [25, 50, 75],
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        shapes: [
            ...createRegimeShapes(
                dashboardData.regime_v2a?.score,
                btcRegimeV2aRange,
                darkMode,
                btcOffsetDays,
            ),
            // 50 line on score subplot
            {
                type: "line",
                xref: "paper",
                yref: "y3",
                x0: 0,
                x1: 1,
                y0: 50,
                y1: 50,
                line: {
                    color: darkMode
                        ? "rgba(148,163,184,0.4)"
                        : "rgba(100,116,139,0.4)",
                    width: 1,
                    dash: "dot",
                },
            },
        ],
        margin: { t: 20, b: 40, l: 50, r: 60 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: false,
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // BTC + Regime V2B with Score Subplot
    $: btcRegimeV2bData = (() => {
        const btcPrice = dashboardData.btc?.price;
        const score = dashboardData.regime_v2b?.score;
        if (!btcPrice) return [];
        const dates = getFilteredDates(btcRegimeV2bRange);
        const btc = filterByRange(btcPrice, btcRegimeV2bRange);
        const scoreFiltered = filterByRange(score, btcRegimeV2bRange);

        return [
            {
                x: dates,
                y: btc,
                name: t("btc_price", "BTC Price"),
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
                yaxis: "y2",
            },
            {
                x: dates,
                y: scoreFiltered,
                name: t("regime_score_label", "Score"),
                type: "scatter",
                mode: "lines",
                line: { color: "#a855f7", width: 1.5 },
                yaxis: "y3",
                fill: "tozeroy",
                fillcolor: "rgba(168, 85, 247, 0.12)",
            },
        ];
    })();

    $: btcV2bXRange = (() => {
        const dates = getFilteredDates(btcRegimeV2bRange);
        if (!dates || dates.length === 0) return undefined;
        const startDate = dates[0];
        const lastDate = new Date(dates[dates.length - 1]);
        if (btcOffsetDays > 0)
            lastDate.setDate(lastDate.getDate() + btcOffsetDays);
        return [startDate, lastDate.toISOString().split("T")[0]];
    })();

    $: btcRegimeV2bLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            range: btcV2bXRange,
            domain: [0, 1],
        },
        yaxis: { visible: false, domain: [0.25, 1] },
        yaxis2: {
            title: t("btc_price_log", "BTC Price (log)"),
            type: "log",
            side: "right",
            overlaying: "y",
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            domain: [0.25, 1],
        },
        yaxis3: {
            title: t("chart_score_y", "Score"),
            range: [0, 100],
            side: "left",
            anchor: "x",
            domain: [0, 0.22],
            color: darkMode ? "#94a3b8" : "#475569",
            tickvals: [25, 50, 75],
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        shapes: [
            ...createRegimeShapes(
                dashboardData.regime_v2b?.score,
                btcRegimeV2bRange,
                darkMode,
                btcOffsetDays,
            ),
            {
                type: "line",
                xref: "paper",
                yref: "y3",
                x0: 0,
                x1: 1,
                y0: 50,
                y1: 50,
                line: {
                    color: darkMode
                        ? "rgba(148,163,184,0.4)"
                        : "rgba(100,116,139,0.4)",
                    width: 1,
                    dash: "dot",
                },
            },
        ],
        margin: { t: 20, b: 40, l: 50, r: 60 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: false,
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // CLI Comparison - reactive to darkMode
    $: cliComparisonData = (() => {
        const dates = getFilteredDates(cliComparisonRange);
        const cliV1 = filterByRange(
            dashboardData.cli?.total,
            cliComparisonRange,
        );
        const cliV2 = filterByRange(
            dashboardData.cli_v2?.cli_v2,
            cliComparisonRange,
        );
        const traces = [];
        if (cliV1?.length > 0) {
            traces.push({
                x: dates,
                y: cliV1,
                name: t("cli_v1_label", "CLI V1 (Original)"),
                type: "scatter",
                mode: "lines",
                line: { color: "#94a3b8", width: 1.5 },
                visible:
                    cliVersion === "v1" || cliVersion === "both"
                        ? true
                        : "legendonly",
            });
        }
        if (cliV2?.length > 0) {
            traces.push({
                x: dates,
                y: cliV2,
                name: t("cli_v2_label", "CLI V2 (Enhanced)"),
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
                visible:
                    cliVersion === "v2" || cliVersion === "both"
                        ? true
                        : "legendonly",
            });
        }
        return traces;
    })();

    $: cliComparisonLayout = {
        xaxis: { showgrid: false, color: darkMode ? "#94a3b8" : "#475569" },
        yaxis: {
            title: "Z-Score",
            zeroline: true,
            color: darkMode ? "#94a3b8" : "#475569",
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        shapes: [
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
        ],
        margin: { t: 20, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        legend: { orientation: "h", y: 1.1 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Block Decomposition - reactive to darkMode
    $: blockDecompData = (() => {
        if (!currentRegime) return [];
        const dates = getFilteredDates(blockDecompRange);
        const traces = [
            {
                x: dates,
                y: filterByRange(currentRegime.liquidity_z, blockDecompRange),
                name: t("regime_liquidity", "Liquidity"),
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 2 },
            },
            {
                x: dates,
                y: filterByRange(currentRegime.credit_z, blockDecompRange),
                name: t("regime_credit", "Credit"),
                type: "scatter",
                mode: "lines",
                line: { color: "#10b981", width: 2 },
            },
            {
                x: dates,
                y: filterByRange(currentRegime.brakes_z, blockDecompRange),
                name: t("regime_brakes", "Brakes"),
                type: "scatter",
                mode: "lines",
                line: { color: "#ef4444", width: 2 },
            },
        ];
        if (regimeVersion === "v2b" && currentRegime.growth_z) {
            traces.splice(2, 0, {
                x: dates,
                y: filterByRange(currentRegime.growth_z, blockDecompRange),
                name: t("regime_growth", "Growth"),
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2 },
            });
        }
        return traces;
    })();

    $: blockDecompLayout = {
        xaxis: { showgrid: false, color: darkMode ? "#94a3b8" : "#475569" },
        yaxis: {
            title: "Z-Score",
            zeroline: true,
            color: darkMode ? "#94a3b8" : "#475569",
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        margin: { t: 20, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        legend: { orientation: "h", y: 1.1 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Historical Stress - reactive to darkMode
    $: stressHistoricalData = (() => {
        const stress = dashboardData.stress_historical;
        if (!stress?.total_stress) return [];
        const dates = getFilteredDates(stressHistoricalRange);
        return [
            {
                x: dates,
                y: filterByRange(
                    stress.inflation_stress,
                    stressHistoricalRange,
                ),
                name: t("stress_inflation", "Inflation"),
                type: "bar",
                marker: { color: "#f59e0b" },
            },
            {
                x: dates,
                y: filterByRange(
                    stress.liquidity_stress,
                    stressHistoricalRange,
                ),
                name: t("stress_liquidity", "Liquidity"),
                type: "bar",
                marker: { color: "#3b82f6" },
            },
            {
                x: dates,
                y: filterByRange(stress.credit_stress, stressHistoricalRange),
                name: t("stress_credit", "Credit"),
                type: "bar",
                marker: { color: "#10b981" },
            },
            {
                x: dates,
                y: filterByRange(
                    stress.volatility_stress,
                    stressHistoricalRange,
                ),
                name: t("stress_volatility", "Volatility"),
                type: "bar",
                marker: { color: "#ef4444" },
            },
        ];
    })();

    $: stressHistoricalLayout = {
        xaxis: { showgrid: false, color: darkMode ? "#94a3b8" : "#475569" },
        yaxis: {
            title: t("stress_score_y", "Stress Score"),
            range: [0, 27],
            color: darkMode ? "#94a3b8" : "#475569",
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        barmode: "stack",
        shapes: [
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 5,
                y1: 5,
                line: { color: "#f59e0b", width: 1, dash: "dash" },
                layer: "above",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 10,
                y1: 10,
                line: { color: "#ef4444", width: 1, dash: "dash" },
                layer: "above",
            },
            {
                type: "line",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 15,
                y1: 15,
                line: { color: "#dc2626", width: 1, dash: "dash" },
                layer: "above",
            },
        ],
        margin: { t: 20, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        legend: { orientation: "h", y: 1.1 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    $: latestStress = (() => {
        const stress = dashboardData.stress_historical;
        if (!stress?.total_stress) return { score: 0 };
        const scores = stress.total_stress.filter((s) => s !== null);
        return { score: scores.length > 0 ? scores[scores.length - 1] : 0 };
    })();
</script>

<!-- Header with Version Toggle and Signal -->
<div class="regime-header" class:light={!darkMode}>
    <div class="header-left">
        <h2>{t("regimes_header", "Macro Regimes")}</h2>
        <div class="version-selector">
            <button
                class:active={regimeVersion === "v2a"}
                on:click={() => (regimeVersion = "v2a")}
            >
                {t("regime_v2a_title", "V2A: Inflation-Aware")}
            </button>
            <button
                class:active={regimeVersion === "v2b"}
                on:click={() => (regimeVersion = "v2b")}
            >
                {t("regime_v2b_title", "V2B: Growth-Aware")}
            </button>
        </div>
    </div>
    <div class="header-right">
        <div class="regime-badge {getSignalLabel(latestRegimeCode).class}">
            <span class="emoji">{getSignalLabel(latestRegimeCode).emoji}</span>
            <span class="label">{getSignalLabel(latestRegimeCode).text}</span>
            <span class="score"
                >{t("regime_score_label", "SCORE")}: {latestScore}</span
            >
        </div>
    </div>
</div>

<!-- Regime Description Panel with CURRENT VALUES -->
<div class="regime-detail-panel" class:light={!darkMode}>
    <div class="regime-description">
        <h4>
            {getSignalLabel(latestRegimeCode).text}
            {t("regime_formula_title", "Regime")}
        </h4>
        <p class="desc-text">{getSignalLabel(latestRegimeCode).desc}</p>
    </div>
    <div class="regime-formula">
        <h5>{t("regime_formula_title", "Regime Formula")}</h5>
        <p class="formula-text {regimeVersion === 'v2a' ? 'v2a' : 'v2b'}">
            {regimeVersion === "v2a"
                ? t(
                      "regime_v2a_formula",
                      "Score = 50×Liquidity + 25×Credit + 25×Brakes",
                  )
                : t(
                      "regime_v2b_formula",
                      "Score = 40×Liquidity + 25×Credit + 20×Growth + 15×Brakes",
                  )}
        </p>
        <ul class="formula-legend">
            <li>
                <span class="dot green"></span> Score &gt; 50: {t(
                    "regime_bullish_label",
                    "Bullish",
                )}
            </li>
            <li>
                <span class="dot red"></span> Score &lt; 50: {t(
                    "regime_bearish_label",
                    "Bearish",
                )}
            </li>
        </ul>
    </div>
    <div class="current-values">
        <h5>{t("regime_current_values", "Current Values")}</h5>
        <div class="values-grid">
            <div class="value-item">
                <span class="value-label"
                    >{t("regime_liquidity", "Liquidity")}</span
                >
                <span
                    class="value-num"
                    class:positive={Number(latestLiquidity) > 0}
                    class:negative={Number(latestLiquidity) < 0}
                    >{latestLiquidity}</span
                >
            </div>
            <div class="value-item">
                <span class="value-label">{t("regime_credit", "Credit")}</span>
                <span
                    class="value-num"
                    class:positive={Number(latestCredit) > 0}
                    class:negative={Number(latestCredit) < 0}
                    >{latestCredit}</span
                >
            </div>
            {#if regimeVersion === "v2b"}
                <div class="value-item">
                    <span class="value-label"
                        >{t("regime_growth", "Growth")}</span
                    >
                    <span
                        class="value-num"
                        class:positive={Number(latestGrowth) > 0}
                        class:negative={Number(latestGrowth) < 0}
                        >{latestGrowth}</span
                    >
                </div>
            {/if}
            <div class="value-item">
                <span class="value-label">{t("regime_brakes", "Brakes")}</span>
                <span
                    class="value-num"
                    class:positive={Number(latestBrakes) > 0}
                    class:negative={Number(latestBrakes) < 0}
                    >{latestBrakes}</span
                >
            </div>
            <div class="value-item total">
                <span class="value-label">{t("regime_total_z", "Total Z")}</span
                >
                <span class="value-num">{latestScore}</span>
            </div>
        </div>
    </div>
</div>

<!-- Offset Slider (controls both regime score and BTC charts) -->
<div class="offset-panel" class:light={!darkMode}>
    <div class="offset-label">
        <span>{t("offset_days_label", "Offset (Days):")}</span>
        <input
            type="range"
            min="0"
            max="120"
            bind:value={regimeOffsetDays}
            on:input={() => (btcOffsetDays = regimeOffsetDays)}
        />
        <span class="offset-value">{regimeOffsetDays}</span>
    </div>
    <button class="best-offset-btn" on:click={applyBestOffset}>
        {t("best_offset_label", "Best Offset")}: {bestOffset ||
            t("calculate_label", "Calculate")}
    </button>
</div>

<!-- Main Content Grid -->
<div class="regimes-grid" class:light={!darkMode}>
    <!-- Regime Score Chart -->
    <div class="chart-card full-width" bind:this={regimeScoreCard}>
        <div class="chart-header">
            <h3>
                {regimeVersion === "v2a"
                    ? t("regime_v2a_score_title", "Macro Regime V2A Score")
                    : t("regime_v2b_score_title", "Macro Regime V2B Score")}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={regimeScoreRange}
                    onRangeChange={(r) => (regimeScoreRange = r)}
                />
                <span class="last-date"
                    >{t("last_data", "Last Data:")} {getLastDate()}</span
                >
            </div>
        </div>
        <p class="chart-desc">
            {regimeVersion === "v2a"
                ? t(
                      "regime_v2a_desc",
                      "Focuses on inflation pressures via monetary brakes.",
                  )
                : t(
                      "regime_v2b_desc",
                      "Balances growth momentum with credit conditions.",
                  )}
        </p>
        <div class="chart-content">
            <Chart
                data={regimeScoreData}
                layout={regimeScoreLayout}
                {darkMode}
                cardContainer={regimeScoreCard}
                cardTitle="regime_score"
            />
        </div>
    </div>

    <!-- BTC + Regime V2A Chart -->
    <div class="chart-card full-width" bind:this={btcV2aCard}>
        <div class="chart-header">
            <h3>
                {t(
                    "regime_btc_overlay_v2a",
                    "BTC + Regime V2A (Inflation-Aware)",
                )}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={btcRegimeV2aRange}
                    onRangeChange={(r) => (btcRegimeV2aRange = r)}
                />
            </div>
        </div>
        <p class="chart-desc">
            {t(
                "regime_btc_desc",
                "Log-scale BTC Price overlaid on Macro Regime. Green: Bullish. Red: Bearish.",
            )}
        </p>
        <div class="chart-content btc-chart">
            <Chart
                data={btcRegimeV2aData}
                layout={btcRegimeV2aLayout}
                {darkMode}
                cardContainer={btcV2aCard}
                cardTitle="btc_regime_v2a"
            />
        </div>
    </div>

    <!-- BTC + Regime V2B Chart -->
    <div class="chart-card full-width" bind:this={btcV2bCard}>
        <div class="chart-header">
            <h3>
                {t("regime_btc_overlay_v2b", "BTC + Regime V2B (Growth-Aware)")}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={btcRegimeV2bRange}
                    onRangeChange={(r) => (btcRegimeV2bRange = r)}
                />
            </div>
        </div>
        <p class="chart-desc">
            {t(
                "regime_btc_desc",
                "Log-scale BTC Price overlaid on Macro Regime. Green: Bullish. Red: Bearish.",
            )}
        </p>
        <div class="chart-content btc-chart">
            <Chart
                data={btcRegimeV2bData}
                layout={btcRegimeV2bLayout}
                {darkMode}
                cardContainer={btcV2bCard}
                cardTitle="btc_regime_v2b"
            />
        </div>
    </div>

    <!-- CLI Comparison Chart -->
    <div class="chart-card" bind:this={cliComparisonCard}>
        <div class="chart-header">
            <h3>{t("cli_comparison_title", "CLI V1 vs V2")}</h3>
            <div class="header-controls">
                <div class="cli-selector">
                    <button
                        class:active={cliVersion === "v1"}
                        on:click={() => (cliVersion = "v1")}>V1</button
                    >
                    <button
                        class:active={cliVersion === "v2"}
                        on:click={() => (cliVersion = "v2")}>V2</button
                    >
                    <button
                        class:active={cliVersion === "both"}
                        on:click={() => (cliVersion = "both")}>Both</button
                    >
                </div>
                <TimeRangeSelector
                    selectedRange={cliComparisonRange}
                    onRangeChange={(r) => (cliComparisonRange = r)}
                />
            </div>
        </div>
        <p class="chart-desc">
            {t(
                "cli_v2_formula",
                "CLI V2: HY Spread + HY Momentum + IG + NFCI + MOVE + FX Vol",
            )}
        </p>
        <div class="chart-content">
            <Chart
                data={cliComparisonData}
                layout={cliComparisonLayout}
                {darkMode}
                cardContainer={cliComparisonCard}
                cardTitle="cli_comparison"
            />
        </div>
    </div>

    <!-- Block Decomposition Chart -->
    <div class="chart-card" bind:this={blockDecompCard}>
        <div class="chart-header">
            <h3>
                {t("block_decomposition_title", "Regime Block Decomposition")}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={blockDecompRange}
                    onRangeChange={(r) => (blockDecompRange = r)}
                />
            </div>
        </div>
        <p class="chart-desc">
            {t(
                "block_decomp_desc",
                "Contribution of each block (Liquidity, Credit, Growth, Brakes) to the total score.",
            )}
        </p>
        <div class="chart-content">
            <Chart
                data={blockDecompData}
                layout={blockDecompLayout}
                {darkMode}
                cardContainer={blockDecompCard}
                cardTitle="block_decomposition"
            />
        </div>
    </div>

    <!-- Historical Stress Chart -->
    <div class="chart-card full-width" bind:this={stressHistCard}>
        <div class="chart-header">
            <h3>
                {t("stress_historical_title", "Historical Stress Dashboard")}
            </h3>
            <div class="header-controls">
                <TimeRangeSelector
                    selectedRange={stressHistoricalRange}
                    onRangeChange={(r) => (stressHistoricalRange = r)}
                />
                <div
                    class="stress-badge {getStressLevel(latestStress.score)
                        .class}"
                >
                    {getStressLevel(latestStress.score).text} ({latestStress.score}/27)
                </div>
            </div>
        </div>
        <p class="chart-desc">
            {t(
                "stress_historical_desc",
                "Inflation (7) + Liquidity (7) + Credit (7) + Volatility (6) = 27 max.",
            )}
        </p>
        <div class="chart-content">
            <Chart
                data={stressHistoricalData}
                layout={stressHistoricalLayout}
                {darkMode}
                cardContainer={stressHistCard}
                cardTitle="historical_stress"
            />
        </div>
    </div>
</div>

<style>
    .regime-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding: 16px 20px;
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    .regime-header.light {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .header-left h2 {
        margin: 0 0 10px 0;
        font-size: 1.4rem;
        color: var(--text-primary, #f1f5f9);
    }
    .light .header-left h2 {
        color: #1e293b;
    }
    .version-selector,
    .cli-selector {
        display: flex;
        gap: 8px;
    }
    .version-selector button,
    .cli-selector button {
        padding: 6px 14px;
        border: 1px solid var(--border-color, #334155);
        background: transparent;
        color: var(--text-secondary, #94a3b8);
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    .light .version-selector button,
    .light .cli-selector button {
        border-color: #cbd5e1;
        color: #64748b;
    }
    .version-selector button.active,
    .cli-selector button.active {
        background: var(--accent-color, #3b82f6);
        color: white;
        border-color: var(--accent-color, #3b82f6);
    }
    .regime-badge {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 18px;
        border-radius: 8px;
        font-weight: 600;
    }
    .regime-badge.bullish {
        background: rgba(16, 185, 129, 0.18);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #10b981;
    }
    .regime-badge.bearish {
        background: rgba(239, 68, 68, 0.18);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #ef4444;
    }
    .regime-badge.neutral {
        background: rgba(148, 163, 184, 0.18);
        border: 1px solid rgba(148, 163, 184, 0.4);
        color: #94a3b8;
    }
    .regime-badge .emoji {
        font-size: 1.3rem;
    }
    .regime-badge .score {
        font-size: 0.9rem;
        opacity: 0.9;
    }

    .regime-detail-panel {
        display: grid;
        grid-template-columns: 1.5fr 1fr 1fr;
        gap: 16px;
        margin-bottom: 20px;
        padding: 16px;
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    .regime-detail-panel.light {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .regime-description h4 {
        margin: 0 0 8px 0;
        font-size: 1rem;
        color: var(--text-primary, #f1f5f9);
    }
    .light .regime-description h4 {
        color: #1e293b;
    }
    .regime-description .desc-text {
        margin: 0;
        font-size: 0.9rem;
        color: var(--text-secondary, #94a3b8);
        line-height: 1.5;
    }
    .light .desc-text {
        color: #64748b;
    }
    .regime-formula h5,
    .current-values h5 {
        margin: 0 0 8px 0;
        font-size: 0.85rem;
        color: var(--text-muted, #64748b);
        text-transform: uppercase;
    }
    .formula-text {
        font-family: monospace;
        font-size: 0.85rem;
        padding: 8px;
        border-radius: 6px;
        margin: 0 0 10px 0;
    }
    .formula-text.v2a {
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    .formula-text.v2b {
        background: rgba(245, 158, 11, 0.1);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .formula-legend {
        list-style: none;
        margin: 0;
        padding: 0;
        font-size: 0.75rem;
        color: var(--text-secondary, #94a3b8);
    }
    .formula-legend li {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 4px;
    }
    .formula-legend .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .formula-legend .dot.green {
        background: #10b981;
    }
    .formula-legend .dot.red {
        background: #ef4444;
    }
    .values-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
    }
    .value-item {
        display: flex;
        justify-content: space-between;
        padding: 6px 8px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 4px;
    }
    .light .value-item {
        background: rgba(226, 232, 240, 0.5);
    }
    .value-item.total {
        grid-column: 1 / -1;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    .value-label {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
    }
    .value-num {
        font-size: 0.85rem;
        font-weight: 600;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }
    .light .value-num {
        color: #1e293b;
    }
    .value-num.positive {
        color: #10b981;
    }
    .value-num.negative {
        color: #ef4444;
    }

    .offset-panel {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 12px 16px;
        margin-bottom: 20px;
        background: var(--card-bg, #050505);
        border-radius: 8px;
        border: 1px solid var(--border-color, #334155);
    }
    .offset-panel.light {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .offset-label {
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--text-secondary, #94a3b8);
        font-size: 0.9rem;
    }
    .light .offset-label {
        color: #64748b;
    }
    .offset-label input[type="range"] {
        width: 200px;
        cursor: pointer;
    }
    .offset-value {
        font-weight: 600;
        color: var(--text-primary, #f1f5f9);
        min-width: 30px;
    }
    .light .offset-value {
        color: #1e293b;
    }
    .best-offset-btn {
        padding: 8px 16px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.85rem;
        transition: background 0.2s;
    }
    .best-offset-btn:hover {
        background: #2563eb;
    }

    .regimes-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
    .chart-card {
        background: var(--bg-secondary);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 16px;
    }
    .regimes-grid.light .chart-card {
        background: #ffffff;
        border-color: #e2e8f0;
    }
    .chart-card.full-width {
        grid-column: 1 / -1;
    }
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .chart-header h3 {
        margin: 0;
        font-size: 1rem;
        color: var(--text-primary, #f1f5f9);
    }
    .light .chart-header h3 {
        color: #1e293b;
    }
    .header-controls {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .last-date {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
    }
    .chart-desc {
        margin: 0 0 12px 0;
        font-size: 0.8rem;
        color: var(--text-secondary, #94a3b8);
    }
    .light .chart-desc {
        color: #64748b;
    }
    .chart-content {
        height: 300px;
    }
    .chart-card.full-width .chart-content {
        height: 350px;
    }
    .btc-chart {
        height: 400px;
    }
    .stress-badge {
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .stress-badge.low {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
    }
    .stress-badge.moderate {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }
    .stress-badge.high {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }
    .stress-badge.critical {
        background: rgba(220, 38, 38, 0.3);
        color: #dc2626;
    }

    @media (max-width: 1024px) {
        .regimes-grid {
            grid-template-columns: 1fr;
        }
        .regime-detail-panel {
            grid-template-columns: 1fr;
        }
        .regime-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 15px;
        }
        .offset-panel {
            flex-direction: column;
            gap: 12px;
        }
        .offset-label input[type="range"] {
            width: 100%;
        }
    }
</style>
