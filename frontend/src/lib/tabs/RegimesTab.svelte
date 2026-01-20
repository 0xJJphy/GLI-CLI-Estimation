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
    import { loadRegimesTabData, loadDomain } from "../utils/domainLoader.js";
    import { onMount } from "svelte";

    export let dashboardData = {};
    export let darkMode = true;
    export let translations = {};
    // language prop is handled via translations internally

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

    // Independent offsets for each BTC+Regime chart (V2A and V2B)
    // offset extends the regime background into the future (BTC stays static)
    let v2aOffsetDays = 0;
    let v2aBestOffset = 0;
    let v2bOffsetDays = 0;
    let v2bBestOffset = 0;

    // Offset for Regime Score chart (uses currently selected version)
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

    // Modular data loading
    let modularRegimeData = null;
    let loading = true;

    onMount(async () => {
        try {
            modularRegimeData = await loadRegimesTabData(dashboardData);
            console.log("Modular Regimes data loaded");
        } catch (e) {
            console.error("Error loading modular Regimes data:", e);
        } finally {
            loading = false;
        }
    });

    // Merge modular data with dashboardData (modular takes precedence)
    $: effectiveData = {
        ...dashboardData,
        macro_regime:
            modularRegimeData?.macro_regime || dashboardData.macro_regime || {},
        regime_v2a:
            modularRegimeData?.regime_v2a || dashboardData.regime_v2a || {},
        regime_v2b:
            modularRegimeData?.regime_v2b || dashboardData.regime_v2b || {},
        cli: modularRegimeData?.cli || dashboardData.cli || {},
        cli_v2: modularRegimeData?.cli_v2 || dashboardData.cli_v2 || {},
        stress_historical:
            modularRegimeData?.stress_historical ||
            dashboardData.stress_historical ||
            {},
        btc: modularRegimeData?.btc || dashboardData.btc || {},
        dates: modularRegimeData?.dates || dashboardData.dates || [],
    };

    $: console.log("[RegimesTab] Effective Data Updated:", {
        hasModular: !!modularRegimeData,
        datesLength: effectiveData.dates?.length,
        v2aScoreLength: effectiveData.regime_v2a?.score?.length,
        legacyDates: dashboardData.dates?.length,
    });

    // ============================================================
    // DATA ALIGNMENT VALIDATION
    // ============================================================
    // Check if dates and regime data are properly aligned
    $: dataAligned = (() => {
        const datesLen = effectiveData.dates?.length || 0;
        const v2aLen = effectiveData.regime_v2a?.score?.length || 0;
        const v2bLen = effectiveData.regime_v2b?.score?.length || 0;

        // Data is aligned if lengths match (or data doesn't exist yet)
        // Allow tolerance of 1 for potential off-by-one errors during live updates
        const aligned =
            (v2aLen === 0 || Math.abs(datesLen - v2aLen) <= 1) &&
            (v2bLen === 0 || Math.abs(datesLen - v2bLen) <= 1);

        if (!aligned && !loading && datesLen > 0) {
            console.warn("[RegimesTab] DATA ALIGNMENT WARNING:", {
                dates: datesLen,
                v2a_score: v2aLen,
                v2b_score: v2bLen,
                mismatch: datesLen - v2aLen,
            });
        }

        return aligned;
    })();

    // Check if data is ready for rendering (loaded and aligned)
    $: dataReady =
        !loading &&
        effectiveData.dates?.length > 0 &&
        (effectiveData.regime_v2a?.score?.length > 0 ||
            effectiveData.regime_v2b?.score?.length > 0);

    // ============================================================
    // HELPER FUNCTIONS
    // ============================================================
    function getLastDate() {
        if (loading) return "Loading...";
        const dates = effectiveData.dates;
        if (!dates || dates.length === 0) return "N/A";
        return dates[dates.length - 1]?.split("T")[0] || "N/A";
    }

    function filterByRange(series, range) {
        // ... (rest of function)

        const dates = effectiveData.dates;
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
        return filterByRange(effectiveData.dates, range);
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

    // Calculate best offset for V2A (correlation with BTC returns)
    function calculateBestOffsetV2A() {
        // Use effectiveData to get modular data when available
        const btcPrice = effectiveData.btc?.price;
        const scores = effectiveData.regime_v2a?.score;
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

    // Calculate best offset for V2B (correlation with BTC returns)
    function calculateBestOffsetV2B() {
        // Use effectiveData to get modular data when available
        const btcPrice = effectiveData.btc?.price;
        const scores = effectiveData.regime_v2b?.score;
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

    // Apply best offset for V2A chart
    function applyBestOffsetV2A() {
        v2aBestOffset = calculateBestOffsetV2A();
        v2aOffsetDays = v2aBestOffset;
    }

    // Apply best offset for V2B chart
    function applyBestOffsetV2B() {
        v2bBestOffset = calculateBestOffsetV2B();
        v2bOffsetDays = v2bBestOffset;
    }

    // Apply best offset for the standalone Regime Score chart (uses regimeVersion)
    function applyBestOffsetGlobal() {
        if (regimeVersion === "v2a") {
            regimeOffsetDays = calculateBestOffsetV2A();
        } else {
            regimeOffsetDays = calculateBestOffsetV2B();
        }
    }

    /**
     * Calculates rolling percentile for each value in the array based on a sliding window.
     * @param {Array} arr - Numeric array
     * @param {number} window - Window size for the historical reference
     */
    function calculateRollingPercentile(arr, window = 252) {
        if (!arr || arr.length === 0) return [];
        return arr.map((val, idx) => {
            if (val === null || isNaN(val)) return null;
            const start = Math.max(0, idx - window);
            const slice = arr
                .slice(start, idx + 1)
                .filter((v) => v !== null && !isNaN(v));
            if (slice.length < 5) return null;
            const count = slice.filter((v) => v < val).length;
            return (count / slice.length) * 100;
        });
    }

    /**
     * Calculates rolling Z-score (standardized score).
     */
    function calculateZScore(arr, window = 252) {
        if (!arr || arr.length === 0) return [];
        return arr.map((val, idx) => {
            if (val === null || isNaN(val)) return null;
            const start = Math.max(0, idx - window);
            const slice = arr
                .slice(start, idx + 1)
                .filter((v) => v !== null && !isNaN(v));
            if (slice.length < 10) return null;

            const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
            const stdDev = Math.sqrt(
                slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) /
                    slice.length,
            );

            if (stdDev === 0) return 0;
            return (val - mean) / stdDev;
        });
    }

    // Create regime shapes with SCORE-BASED INTENSITY
    // offsetDays SHIFTS all shapes forward in time (regime leads BTC by offsetDays)
    function createRegimeShapes(scores, range, isDarkMode, offsetDays = 0) {
        // Use effectiveData.dates (modular-aware) instead of incorrect dashboardData.dates
        if (!scores || !effectiveData.dates) return [];
        const filteredDates = getFilteredDates(range);
        const filteredScores = filterByRange(scores, range);
        if (!filteredDates || !filteredScores || filteredDates.length === 0)
            return [];

        // Helper to shift a date string by offsetDays
        function shiftDate(dateStr, days) {
            if (days === 0) return dateStr;
            const d = new Date(dateStr);
            d.setDate(d.getDate() + days);
            return d.toISOString().split("T")[0];
        }

        const shapes = [];
        let currentDirection = null;
        let blockStartIdx = 0;
        let blockScores = [];

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
                    const modeOpacity = isDarkMode ? opacity : opacity * 1.6;

                    const color =
                        currentDirection === "bull"
                            ? `rgba(16, 185, 129, ${modeOpacity.toFixed(2)})`
                            : `rgba(239, 68, 68, ${modeOpacity.toFixed(2)})`;

                    if (d0 && d1) {
                        // Shift both dates forward by offsetDays
                        shapes.push({
                            type: "rect",
                            xref: "x",
                            yref: "paper",
                            x0: shiftDate(d0, offsetDays),
                            x1: shiftDate(d1, offsetDays),
                            y0: 0,
                            y1: 1,
                            fillcolor: color,
                            line: { width: 0 },
                            layer: "below",
                        });
                    }
                }
                currentDirection = direction;
                blockStartIdx = i;
                blockScores = score !== null ? [score] : [];
            } else if (score !== null) {
                blockScores.push(score);
            }
        }

        return shapes;
    }

    // ============================================================
    // REACTIVE DATA
    // ============================================================
    $: currentRegime =
        regimeVersion === "v2a"
            ? effectiveData.regime_v2a
            : effectiveData.regime_v2b;

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
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // BTC + Regime V2A with Score Subplot - reactive to darkMode and offset
    // BTC trace remains static; only the regime background extends into future via v2aOffsetDays
    $: btcRegimeV2aData = (() => {
        const btcPrice = effectiveData.btc?.price;
        const score = effectiveData.regime_v2a?.score;
        if (!btcPrice) return [];
        const dates = getFilteredDates(btcRegimeV2aRange);
        const btc = filterByRange(btcPrice, btcRegimeV2aRange);
        const scoreFiltered = filterByRange(score, btcRegimeV2aRange);

        // BTC trace uses original dates (no extension)
        // Regime background shapes are extended via createRegimeShapes()
        return [
            // BTC Price trace (on y2) - static, no future dates
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

    // Calculate extended range for x-axis (extends to show future regime projection)
    $: btcV2aXRange = (() => {
        const dates = getFilteredDates(btcRegimeV2aRange);
        if (!dates || dates.length === 0) return undefined;
        const startDate = dates[0];
        const lastDate = new Date(dates[dates.length - 1]);
        if (v2aOffsetDays > 0) {
            lastDate.setDate(lastDate.getDate() + v2aOffsetDays);
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
                effectiveData.regime_v2a?.score,
                btcRegimeV2aRange,
                darkMode,
                v2aOffsetDays,
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
        showlegend: false,
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // BTC + Regime V2B with Score Subplot
    $: btcRegimeV2bData = (() => {
        const btcPrice = effectiveData.btc?.price;
        const score = effectiveData.regime_v2b?.score;
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
        if (v2bOffsetDays > 0)
            lastDate.setDate(lastDate.getDate() + v2bOffsetDays);
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
                effectiveData.regime_v2b?.score,
                btcRegimeV2bRange,
                darkMode,
                v2bOffsetDays,
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
        showlegend: false,
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // CLI Comparison - reactive to darkMode
    $: cliComparisonData = (() => {
        const dates = getFilteredDates(cliComparisonRange);
        const cliV1 = filterByRange(
            effectiveData.cli?.total,
            cliComparisonRange,
        );
        const cliV2 = filterByRange(
            effectiveData.cli_v2?.cli_v2,
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

    // Stress Percentiles - Normalizing the raw scores against their history
    $: stressPercentiles = (() => {
        const stress =
            effectiveData.stress_historical || dashboardData.stress_historical;
        if (!stress)
            return { inflation: [], liquidity: [], credit: [], volatility: [] };
        // Using a 504-day window (approx 2 years) for normalization
        return {
            inflation: calculateRollingPercentile(stress.inflation_stress, 504),
            liquidity: calculateRollingPercentile(stress.liquidity_stress, 504),
            credit: calculateRollingPercentile(stress.credit_stress, 504),
            volatility: calculateRollingPercentile(
                stress.volatility_stress,
                504,
            ),
        };
    })();

    // Heatmap - Driver Intensity over time
    $: stressHeatmapData = (() => {
        const dates = getFilteredDates(stressHistoricalRange);
        const p = stressPercentiles;
        if (!dates || dates.length === 0) return [];

        return [
            {
                z: [
                    filterByRange(p.volatility, stressHistoricalRange),
                    filterByRange(p.credit, stressHistoricalRange),
                    filterByRange(p.liquidity, stressHistoricalRange),
                    filterByRange(p.inflation, stressHistoricalRange),
                ],
                x: dates,
                y: [
                    t("stress_volatility", "Volatility"),
                    t("stress_credit", "Credit"),
                    t("stress_liquidity", "Liquidity"),
                    t("stress_inflation", "Inflation"),
                ],
                type: "heatmap",
                colorscale: [
                    [0, darkMode ? "#0f172a" : "#f8fafc"],
                    [0.5, "#f59e0b"],
                    [1, "#ef4444"],
                ],
                showscale: true,
                colorbar: {
                    title: "%",
                    thickness: 10,
                    len: 0.8,
                },
            },
        ];
    })();

    $: stressHeatmapLayout = {
        xaxis: { showgrid: false, color: darkMode ? "#94a3b8" : "#475569" },
        yaxis: {
            type: "category",
            color: darkMode ? "#94a3b8" : "#475569",
            automargin: true,
        },
        margin: { t: 10, b: 40, l: 100, r: 20 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Radar Chart - Current State Profile
    $: stressRadarData = (() => {
        const p = stressPercentiles;
        const keys = ["volatility", "credit", "liquidity", "inflation"];
        const currentVals = keys.map((k) => {
            const vals = p[k].filter((v) => v !== null);
            return vals.length > 0 ? vals[vals.length - 1] : 0;
        });

        return [
            {
                type: "scatterpolar",
                r: currentVals,
                theta: [
                    t("stress_volatility", "Volatility"),
                    t("stress_credit", "Credit"),
                    t("stress_liquidity", "Liquidity"),
                    t("stress_inflation", "Inflation"),
                ],
                fill: "toself",
                fillcolor: "rgba(239, 68, 68, 0.3)",
                line: { color: "#ef4444" },
            },
        ];
    })();

    $: stressRadarLayout = {
        polar: {
            bgcolor: "transparent",
            radialaxis: {
                visible: true,
                range: [0, 100],
                color: darkMode ? "#94a3b8" : "#475569",
                gridcolor: darkMode
                    ? "rgba(148,163,184,0.1)"
                    : "rgba(71,85,105,0.1)",
            },
            angularaxis: {
                color: darkMode ? "#94a3b8" : "#475569",
                gridcolor: darkMode
                    ? "rgba(148,163,184,0.1)"
                    : "rgba(71,85,105,0.1)",
            },
        },
        showlegend: false,
        margin: { t: 30, b: 30, l: 30, r: 30 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Keep the "Total Stress" as a simple line chart for trend analysis
    $: stressTotalData = (() => {
        const stress =
            effectiveData.stress_historical || dashboardData.stress_historical;
        if (!stress?.total_stress) return [];
        const dates = getFilteredDates(stressHistoricalRange);
        return [
            {
                x: dates,
                y: filterByRange(stress.total_stress, stressHistoricalRange),
                name: t("total_stress", "Total Stress"),
                type: "scatter",
                mode: "lines",
                fill: "tozeroy",
                line: { color: "#ef4444", width: 2 },
                fillcolor: "rgba(239, 68, 68, 0.1)",
            },
        ];
    })();

    $: stressTotalLayout = {
        xaxis: { showgrid: false, color: darkMode ? "#94a3b8" : "#475569" },
        yaxis: {
            title: t("stress_score_y", "Score"),
            range: [0, 27],
            color: darkMode ? "#94a3b8" : "#475569",
            gridcolor: darkMode
                ? "rgba(148,163,184,0.1)"
                : "rgba(71,85,105,0.1)",
        },
        margin: { t: 10, b: 40, l: 50, r: 20 },
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
    };

    $: latestStress = (() => {
        const stress =
            effectiveData.stress_historical || dashboardData.stress_historical;
        if (!stress?.total_stress) return { score: 0 };
        const scores = stress.total_stress.filter((s) => s !== null);
        return { score: scores.length > 0 ? scores[scores.length - 1] : 0 };
    })();
</script>

<div class="tab-container regimes-tab" class:light={!darkMode}>
    {#if loading}
        <div class="flex items-center justify-center h-96">
            <div
                class="text-xl font-bold {darkMode
                    ? 'text-gray-300'
                    : 'text-gray-700'}"
            >
                {t("loading_data", "Loading Regimes Data...")}
            </div>
        </div>
    {:else}
        <!-- Data Alignment Warning Banner -->
        {#if !dataAligned}
            <div class="alignment-warning" class:light={!darkMode}>
                <span class="warning-icon">⚠️</span>
                <div class="warning-content">
                    <span class="warning-title"
                        >{t(
                            "data_alignment_warning",
                            "Data Alignment Issue Detected",
                        )}</span
                    >
                    <span class="warning-details">
                        Dates: {effectiveData.dates?.length || 0} | V2A: {effectiveData
                            .regime_v2a?.score?.length || 0} | V2B: {effectiveData
                            .regime_v2b?.score?.length || 0}
                    </span>
                    <span class="warning-hint"
                        >Try refreshing the page or regenerating domain data.</span
                    >
                </div>
            </div>
        {/if}

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
                <div
                    class="regime-badge {getSignalLabel(latestRegimeCode)
                        .class}"
                >
                    <span class="emoji"
                        >{getSignalLabel(latestRegimeCode).emoji}</span
                    >
                    <span class="label"
                        >{getSignalLabel(latestRegimeCode).text}</span
                    >
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
                <p
                    class="formula-text {regimeVersion === 'v2a'
                        ? 'v2a'
                        : 'v2b'}"
                >
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
                        <span class="value-label"
                            >{t("regime_credit", "Credit")}</span
                        >
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
                        <span class="value-label"
                            >{t("regime_brakes", "Brakes")}</span
                        >
                        <span
                            class="value-num"
                            class:positive={Number(latestBrakes) > 0}
                            class:negative={Number(latestBrakes) < 0}
                            >{latestBrakes}</span
                        >
                    </div>
                    <div class="value-item total">
                        <span class="value-label"
                            >{t("regime_total_z", "Total Z")}</span
                        >
                        <span class="value-num">{latestScore}</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Offset Slider for Regime Score chart only -->
        <div class="offset-panel" class:light={!darkMode}>
            <div class="offset-label">
                <span
                    >{t(
                        "regime_score_offset_label",
                        "Regime Score Offset:",
                    )}</span
                >
                <input
                    type="range"
                    min="0"
                    max="120"
                    bind:value={regimeOffsetDays}
                />
                <span class="offset-value">{regimeOffsetDays}d</span>
            </div>
            <button class="best-offset-btn" on:click={applyBestOffsetGlobal}>
                {t("best_offset_label", "Best Offset")}
            </button>
        </div>

        <!-- Main Content Grid -->
        <div class="regimes-grid" class:light={!darkMode}>
            <!-- Regime Score Chart -->
            <div class="chart-card full-width" bind:this={regimeScoreCard}>
                <div class="chart-header">
                    <h3>
                        {regimeVersion === "v2a"
                            ? t(
                                  "regime_v2a_score_title",
                                  "Macro Regime V2A Score",
                              )
                            : t(
                                  "regime_v2b_score_title",
                                  "Macro Regime V2B Score",
                              )}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={regimeScoreRange}
                            onRangeChange={(r) => (regimeScoreRange = r)}
                        />
                        <span class="last-date"
                            >{t("last_data", "Last Data:")}
                            {getLastDate()}</span
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
                <div class="offset-inline" class:light={!darkMode}>
                    <span>{t("offset_days_label", "Offset:")}</span>
                    <input
                        type="range"
                        min="0"
                        max="120"
                        bind:value={v2aOffsetDays}
                    />
                    <span class="offset-value">{v2aOffsetDays}d</span>
                    <button
                        class="best-offset-btn-inline"
                        on:click={applyBestOffsetV2A}
                    >
                        {t("best_offset", "Best")}: {v2aBestOffset || "?"}
                    </button>
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
                        {t(
                            "regime_btc_overlay_v2b",
                            "BTC + Regime V2B (Growth-Aware)",
                        )}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={btcRegimeV2bRange}
                            onRangeChange={(r) => (btcRegimeV2bRange = r)}
                        />
                    </div>
                </div>
                <div class="offset-inline" class:light={!darkMode}>
                    <span>{t("offset_days_label", "Offset:")}</span>
                    <input
                        type="range"
                        min="0"
                        max="120"
                        bind:value={v2bOffsetDays}
                    />
                    <span class="offset-value">{v2bOffsetDays}d</span>
                    <button
                        class="best-offset-btn-inline"
                        on:click={applyBestOffsetV2B}
                    >
                        {t("best_offset", "Best")}: {v2bBestOffset || "?"}
                    </button>
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
                                on:click={() => (cliVersion = "both")}
                                >Both</button
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
                        {t(
                            "block_decomposition_title",
                            "Regime Block Decomposition",
                        )}
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

            <!-- Historical Stress Dashboard - Refactored -->
            <div class="chart-card full-width" bind:this={stressHistCard}>
                <div class="chart-header">
                    <h3>
                        {t(
                            "stress_historical_title",
                            "Historical Stress Dashboard",
                        )}
                    </h3>
                    <div class="header-controls">
                        <TimeRangeSelector
                            selectedRange={stressHistoricalRange}
                            onRangeChange={(r) => (stressHistoricalRange = r)}
                        />
                    </div>
                </div>
                <p class="chart-desc">
                    {t(
                        "stress_historical_quant_desc",
                        "Intensity Heatmap (Rolling Percentiles) + Current Stress Profile + Historical Trend.",
                    )}
                </p>

                <div class="stress-dashboard-layout">
                    <div class="stress-main-panel">
                        <div class="sub-chart-title">
                            {t(
                                "stress_driver_intensity",
                                "Driver Intensity Heatmap (0-100%)",
                            )}
                        </div>
                        <div class="chart-content heatmap-container">
                            <Chart
                                data={stressHeatmapData}
                                layout={stressHeatmapLayout}
                                {darkMode}
                                cardContainer={stressHistCard}
                                cardTitle="stress_intensity_heatmap"
                            />
                        </div>

                        <div class="stress-lower-grid">
                            <div class="trend-panel">
                                <div class="sub-chart-title">
                                    {t(
                                        "stress_total_trend",
                                        "Total Stress Trend (Raw Score)",
                                    )}
                                </div>
                                <div class="chart-content">
                                    <Chart
                                        data={stressTotalData}
                                        layout={stressTotalLayout}
                                        {darkMode}
                                        cardContainer={stressHistCard}
                                        cardTitle="stress_total_trend"
                                    />
                                </div>
                            </div>
                            <div class="radar-panel">
                                <div class="sub-chart-title">
                                    {t(
                                        "stress_current_profile",
                                        "Current Stress Profile",
                                    )}
                                </div>
                                <div class="chart-content radar-container">
                                    <Chart
                                        data={stressRadarData}
                                        layout={stressRadarLayout}
                                        {darkMode}
                                        cardContainer={stressHistCard}
                                        cardTitle="stress_current_radar"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="stress-sidebar">
                        <div class="stress-summary-badge">
                            <div class="badge-label">
                                {t(
                                    "latest_stress_status",
                                    "Current Stress Status",
                                )}
                            </div>
                            <div
                                class="badge-value {getStressLevel(
                                    latestStress.score,
                                ).class}"
                            >
                                {getStressLevel(latestStress.score).text}
                            </div>
                            <div class="badge-score">
                                {latestStress.score} / 27
                            </div>
                        </div>

                        <div class="driver-pills">
                            {#each [{ key: "volatility", label: "Volatility", color: "#ef4444" }, { key: "credit", label: "Credit", color: "#10b981" }, { key: "liquidity", label: "Liquidity", color: "#3b82f6" }, { key: "inflation", label: "Inflation", color: "#f59e0b" }] as driver}
                                {@const pArray = stressPercentiles[
                                    driver.key
                                ].filter((v) => v !== null)}
                                {@const latestP =
                                    pArray.length > 0
                                        ? pArray[pArray.length - 1]
                                        : 0}
                                <div class="driver-pill">
                                    <span
                                        class="dot"
                                        style="background: {driver.color}"
                                    ></span>
                                    <span class="label"
                                        >{t(
                                            "stress_" + driver.key,
                                            driver.label,
                                        )}</span
                                    >
                                    <span
                                        class="value"
                                        class:high={latestP > 70}
                                        class:low={latestP < 30}
                                        >{latestP.toFixed(0)}%</span
                                    >
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    /* ... styles ... */
    .regime-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        margin-bottom: 32px;
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
        padding: 16px var(--content-inner-padding);
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
        padding: 12px var(--content-inner-padding);
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
        accent-color: #f97316;
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

    /* Inline offset controls for individual BTC+Regime charts */
    .offset-inline {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        margin: 8px 0 4px 0;
        background: rgba(59, 130, 246, 0.08);
        border-radius: 6px;
        border: 1px solid rgba(59, 130, 246, 0.15);
        font-size: 0.8rem;
        color: var(--text-secondary, #94a3b8);
    }
    .offset-inline.light {
        background: rgba(59, 130, 246, 0.05);
        border-color: rgba(59, 130, 246, 0.12);
        color: #64748b;
    }
    .offset-inline input[type="range"] {
        width: 120px;
        cursor: pointer;
        accent-color: #f97316;
    }
    .offset-inline .offset-value {
        font-weight: 600;
        color: var(--text-primary, #f1f5f9);
        min-width: 35px;
    }
    .offset-inline.light .offset-value {
        color: #1e293b;
    }
    .best-offset-btn-inline {
        padding: 4px 10px;
        background: #3b82f6;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.75rem;
        transition: background 0.2s;
        white-space: nowrap;
    }
    .best-offset-btn-inline:hover {
        background: #2563eb;
    }

    .regimes-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
        padding: 20px 0;
    }

    /* Use global .chart-card styles */
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
    /* Stress Dashboard Refactor Styles */
    .stress-dashboard-layout {
        display: grid;
        grid-template-columns: 1fr 280px;
        gap: 20px;
        margin-top: 10px;
    }
    .stress-main-panel {
        display: flex;
        flex-direction: column;
        gap: 20px;
    }
    .sub-chart-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary, #94a3b8);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .heatmap-container {
        height: 250px !important;
    }
    .stress-lower-grid {
        display: grid;
        grid-template-columns: 1.2fr 1.1fr;
        gap: 20px;
        min-height: 250px;
        overflow: hidden;
    }
    .stress-sidebar {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 20px;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
    .light .stress-sidebar {
        background: rgba(0, 0, 0, 0.02);
    }
    .stress-summary-badge {
        text-align: center;
        padding: 15px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .badge-label {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
        margin-bottom: 5px;
    }
    .badge-value {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    .badge-value.low {
        color: #10b981;
    }
    .badge-value.moderate {
        color: #f59e0b;
    }
    .badge-value.high {
        color: #ef4444;
    }
    .badge-value.critical {
        color: #dc2626;
    }

    .badge-score {
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-secondary, #94a3b8);
    }

    .driver-pills {
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .driver-pill {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        font-size: 0.85rem;
    }
    .driver-pill .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }
    .driver-pill .label {
        flex: 1;
        color: var(--text-secondary, #94a3b8);
    }
    .driver-pill .value {
        font-weight: 700;
        font-family: monospace;
        color: var(--text-primary, #f1f5f9);
    }
    .light .driver-pill .value {
        color: #1e293b;
    }
    .driver-pill .value.high {
        color: #ef4444 !important;
    }
    .driver-pill .value.low {
        color: #10b981 !important;
    }

    /* Data Alignment Warning Banner */
    .alignment-warning {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 20px;
        margin-bottom: 20px;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.4);
        border-radius: 8px;
        color: #f59e0b;
    }
    .alignment-warning.light {
        background: rgba(245, 158, 11, 0.1);
        color: #d97706;
    }
    .alignment-warning .warning-icon {
        font-size: 1.2rem;
        margin-top: 2px;
    }
    .warning-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .warning-title {
        font-weight: 600;
        font-size: 0.95rem;
    }
    .warning-details {
        font-family: monospace;
        font-size: 0.85rem;
        opacity: 0.9;
    }
    .warning-hint {
        font-size: 0.8rem;
        opacity: 0.8;
        font-style: italic;
    }

    .radar-container {
        height: 100% !important;
    }

    @media (max-width: 1200px) {
        .stress-dashboard-layout {
            grid-template-columns: 1fr;
        }
        .stress-sidebar {
            order: -1;
            flex-direction: row;
            flex-wrap: wrap;
            justify-content: space-between;
        }
        .driver-pills {
            flex-direction: row;
            flex-wrap: wrap;
            flex: 1;
        }
    }

    @media (max-width: 768px) {
        .stress-lower-grid {
            grid-template-columns: 1fr;
            height: auto;
        }
        .stress-lower-grid > div {
            height: 250px;
        }
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
