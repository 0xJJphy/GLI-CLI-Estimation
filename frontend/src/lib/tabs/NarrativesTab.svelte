<script>
    /**
     * NarrativesTab.svelte
     * Displays Crypto Market Regimes, Altseason Index, Fear & Greed,
     * and Narrative Rotation (Scatter Plot).
     */
    import Chart from "../components/Chart.svelte";
    import TimeRangeSelector from "../components/TimeRangeSelector.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import {
        getCutoffDate,
        calculateRollingZScore,
        calculatePercentile,
    } from "../utils/helpers.js";
    import { downloadCardAsImage } from "../utils/downloadCard.js";
    import { loadCryptoTabData } from "../utils/domainLoader.js";
    import { onMount } from "svelte";

    export let dashboardData = {};
    export let darkMode = true;
    export let translations = {};

    // ============================================================
    // STATE & REACTIVE PROPS
    // ============================================================
    let regimeRange = "ALL";

    // Card Refs
    let rotationCard;
    let regimeCard;

    $: t = (key, fallback) => translations[key] || fallback;

    // Modular data loading
    let modularCryptoData = null;
    onMount(async () => {
        try {
            modularCryptoData = await loadCryptoTabData(dashboardData);
            console.log("Modular Crypto/Narratives data loaded");
        } catch (e) {
            console.error("Error loading modular Crypto data:", e);
        }
    });

    // Merge modular data with dashboardData (modular takes precedence)
    // Note: modular crypto.json has flat structure (cai, regimes, narratives)
    // while legacy dashboardData.crypto_narratives has nested structure
    $: effectiveData = {
        ...dashboardData,
        crypto_narratives: {
            // Map modular flat structure to expected nested structure
            ...(dashboardData.crypto_narratives || {}),
            cai:
                modularCryptoData?.crypto_analytics?.cai ||
                dashboardData.crypto_narratives?.cai ||
                [],
            regimes:
                modularCryptoData?.crypto_analytics?.regimes ||
                dashboardData.crypto_narratives?.regimes ||
                [],
            narratives:
                modularCryptoData?.crypto_analytics?.narratives ||
                dashboardData.crypto_narratives?.narratives ||
                {},
            fear_greed:
                modularCryptoData?.crypto_analytics?.fear_greed ||
                dashboardData.crypto_narratives?.fear_greed ||
                [],
            btc_dom:
                modularCryptoData?.crypto_analytics?.btc_dominance ||
                dashboardData.crypto_narratives?.btc_dom ||
                [],
            total_mcap:
                modularCryptoData?.crypto_analytics?.total_mcap ||
                dashboardData.crypto_narratives?.total_mcap ||
                [],
            btc_mcap:
                modularCryptoData?.crypto_analytics?.btc_mcap ||
                dashboardData.crypto_narratives?.btc_mcap ||
                [],
            rs_risk_btc:
                modularCryptoData?.crypto_analytics?.rs_risk_btc ||
                dashboardData.crypto_narratives?.rs_risk_btc ||
                [],
            delta_rs_risk:
                modularCryptoData?.crypto_analytics?.delta_rs_risk ||
                dashboardData.crypto_narratives?.delta_rs_risk ||
                [],
        },
        btc: modularCryptoData?.btc || dashboardData.btc || {},
        dates: modularCryptoData?.dates || dashboardData.dates || [],
    };

    $: data = effectiveData.crypto_narratives || {};
    $: dates = effectiveData.dates || [];

    $: cryptoStartIndex = (() => {
        if (!dates || dates.length === 0) return 0;
        const cai = data.cai || [];
        const btc = dashboardData.btc?.price || [];
        // First non-null in BTC or Altseason Index
        for (let i = 0; i < dates.length; i++) {
            if (
                (cai[i] !== null && cai[i] !== undefined) ||
                (btc[i] !== null && btc[i] !== undefined)
            )
                return i;
        }
        return 0;
    })();

    function filterByRange(series, range) {
        if (!dates || !series || series.length === 0) return series;

        // For ALL, we trim the distant macro past (pre-crypto)
        if (range === "ALL") {
            return series.slice(cryptoStartIndex);
        }

        const cutoff = getCutoffDate(range);
        const filtered = [];
        for (let i = 0; i < dates.length; i++) {
            if (new Date(dates[i]) >= cutoff) {
                filtered.push(series[i]);
            }
        }
        return filtered;
    }

    function getFilteredDates(range) {
        if (!dates) return [];
        if (range === "ALL") return dates.slice(cryptoStartIndex);

        const cutoff = getCutoffDate(range);
        return dates.filter((d) => new Date(d) >= cutoff);
    }

    function getLatestValue(arr, decimals = 2) {
        if (!arr || arr.length === 0) return "N/A";
        const vals = arr.filter((v) => v !== null && v !== undefined);
        if (vals.length === 0) return "N/A";
        const val = vals[vals.length - 1];
        return typeof val === "number" ? val.toFixed(decimals) : val;
    }

    function getLatestValueRaw(arr) {
        if (!arr || arr.length === 0) return null;
        const vals = arr.filter((v) => v !== null && v !== undefined);
        if (vals.length === 0) return null;
        return vals[vals.length - 1];
    }

    // ============================================================
    // REGIME COLORS
    // ============================================================
    const cryptoRegimeColors = {
        Capitulation: {
            bg: "rgba(220, 38, 38, 0.25)",
            text: "#ef4444",
            label: "Capitulation",
        },
        "Stable Refuge": {
            bg: "rgba(71, 85, 105, 0.25)",
            text: "#94a3b8",
            label: "Stable Refuge",
        },
        "Flight to Quality": {
            bg: "rgba(245, 158, 11, 0.25)",
            text: "#f59e0b",
            label: "Flight to Quality",
        },
        "Alt Season": {
            bg: "rgba(16, 185, 129, 0.25)",
            text: "#10b981",
            label: "Alt Season",
        },
        "BTC Season": {
            bg: "rgba(234, 179, 8, 0.25)",
            text: "#eab308",
            label: "BTC Season",
        },
        "Side-ways/Neutral": {
            bg: "rgba(148, 163, 184, 0.1)",
            text: "#64748b",
            label: "Sideways",
        },
    };

    function createRegimeShapes(regimes, range) {
        if (!regimes || !dates) return [];
        const filteredDates = getFilteredDates(range);
        const filteredRegimes = filterByRange(regimes, range);
        if (!filteredDates || filteredDates.length === 0) return [];

        const shapes = [];
        let currentRegime = null;
        let blockStartIdx = 0;

        for (let i = 0; i <= filteredDates.length; i++) {
            const regime =
                i < filteredRegimes.length ? filteredRegimes[i] : null;

            if (regime !== currentRegime || i === filteredDates.length) {
                if (currentRegime !== null) {
                    const d0 = filteredDates[blockStartIdx];
                    const d1 =
                        filteredDates[Math.min(i, filteredDates.length - 1)];
                    const color =
                        cryptoRegimeColors[currentRegime]?.bg ||
                        cryptoRegimeColors["Side-ways/Neutral"].bg;

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
                }
                currentRegime = regime;
                blockStartIdx = i;
            }
        }
        return shapes;
    }

    // ============================================================
    // ROTATION SCATTER PLOT
    // ============================================================
    const narrativeColors = {
        DeFi: "#8B5CF6",
        Meme: "#EC4899",
        AI: "#06B6D4",
        L1: "#F59E0B",
        DePIN: "#22C55E",
        RWA: "#3B82F6",
    };

    $: rotationLayout = {
        xaxis: {
            title: {
                text: "Momentum vs BTC →",
                font: { size: 11, color: darkMode ? "#94a3b8" : "#475569" },
            },
            zeroline: true,
            zerolinecolor: darkMode ? "#475569" : "#cbd5e1",
            zerolinewidth: 2,
            gridcolor: darkMode
                ? "rgba(148,163,184,0.08)"
                : "rgba(71,85,105,0.08)",
            tickfont: { size: 10, color: darkMode ? "#94a3b8" : "#475569" },
            color: darkMode ? "#94a3b8" : "#475569",
        },
        yaxis: {
            title: {
                text: "↑ Share Momentum",
                font: { size: 11, color: darkMode ? "#94a3b8" : "#475569" },
            },
            zeroline: true,
            zerolinecolor: darkMode ? "#475569" : "#cbd5e1",
            zerolinewidth: 2,
            gridcolor: darkMode
                ? "rgba(148,163,184,0.08)"
                : "rgba(71,85,105,0.08)",
            tickfont: { size: 10, color: darkMode ? "#94a3b8" : "#475569" },
            color: darkMode ? "#94a3b8" : "#475569",
        },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
        margin: { t: 20, b: 50, l: 60, r: 20 },
        showlegend: false,
        annotations: [
            {
                x: 0.04,
                y: 0.04,
                text: "LEADERS",
                showarrow: false,
                font: { size: 9, color: "rgba(16, 185, 129, 0.6)" },
                xref: "paper",
                yref: "paper",
            },
            {
                x: 0.96,
                y: 0.04,
                text: "EARLY",
                showarrow: false,
                font: { size: 9, color: "rgba(245, 158, 11, 0.6)" },
                xref: "paper",
                yref: "paper",
            },
            {
                x: 0.04,
                y: 0.96,
                text: "LATE",
                showarrow: false,
                font: { size: 9, color: "rgba(59, 130, 246, 0.6)" },
                xref: "paper",
                yref: "paper",
            },
            {
                x: 0.96,
                y: 0.96,
                text: "LAGGARDS",
                showarrow: false,
                font: { size: 9, color: "rgba(239, 68, 68, 0.6)" },
                xref: "paper",
                yref: "paper",
            },
        ],
    };

    $: rotationData = (() => {
        if (!data.narratives) return [];
        const traces = [];

        for (const [name, nData] of Object.entries(data.narratives)) {
            const x = nData.current_mom_btc;
            const y = nData.current_mom_share;
            const mcap = nData.current_mcap || 1;
            const size = Math.min(Math.max(Math.sqrt(mcap) * 3 + 8, 12), 50);
            const color = narrativeColors[name] || "#64748b";

            traces.push({
                x: [x],
                y: [y],
                name: name,
                text: [name],
                hovertemplate: `<b>${name}</b><br>MCap: $${mcap.toFixed(1)}B<br>Mom BTC: ${(x * 100).toFixed(2)}%<br>Mom Share: ${(y * 100).toFixed(2)}%<extra></extra>`,
                mode: "markers+text",
                textposition: "top center",
                textfont: { size: 10, color: darkMode ? "#e2e8f0" : "#1e293b" },
                marker: {
                    size: [size],
                    color: color,
                    opacity: 0.85,
                    line: {
                        width: 2,
                        color: darkMode
                            ? "rgba(255,255,255,0.3)"
                            : "rgba(0,0,0,0.2)",
                    },
                },
                type: "scatter",
            });
        }
        return traces;
    })();

    // ============================================================
    // CAI & F&G VALUES
    // ============================================================
    $: caiValueRaw = getLatestValueRaw(data.cai);
    $: caiValue = caiValueRaw !== null ? Math.round(caiValueRaw) : "N/A";
    $: fngValueRaw = getLatestValueRaw(data.fear_greed);
    $: fngValue = fngValueRaw !== null ? Math.round(fngValueRaw) : "N/A";

    // F&G ROC Analytics
    $: fngCurrent = data.fng_current || {};
    $: fngRoc7d = fngCurrent.roc_7d;
    $: fngRoc7dZ = fngCurrent.roc_7d_z;
    $: fngRoc7dPct = fngCurrent.roc_7d_pct;
    $: fngRoc30d = fngCurrent.roc_30d;
    $: fngRoc30dZ = fngCurrent.roc_30d_z;

    // Z-Score classification
    function getZScoreClass(z) {
        if (z === null || z === undefined) return "";
        if (z >= 2) return "extreme-positive";
        if (z >= 1) return "positive";
        if (z <= -2) return "extreme-negative";
        if (z <= -1) return "negative";
        return "";
    }

    // ============================================================
    // CAI / F&G DIVERGENCE SIGNAL
    // ============================================================
    // High CAI (>60) + Low F&G (<40) = Silent Rally (bullish without euphoria - sustainable)
    // High CAI (>60) + High F&G (>60) = Overextended (potential top)
    // Low CAI (<40) + Extreme Fear F&G (<20) = Capitulation Opportunity
    // Low CAI (<40) + High F&G (>60) = Divergence Warning (sentiment disconnected from rotation)
    $: divergenceSignal = (() => {
        if (caiValueRaw === null || fngValueRaw === null) return null;

        const cai = caiValueRaw;
        const fng = fngValueRaw;

        if (cai > 60 && fng < 40) {
            return {
                label: "Silent Rally",
                color: "#10b981",
                icon: "🟢",
                desc: "Alts rising without retail euphoria",
            };
        }
        if (cai > 60 && fng > 60) {
            return {
                label: "Overextended",
                color: "#f59e0b",
                icon: "🟡",
                desc: "Potential top - high rotation + high greed",
            };
        }
        if (cai < 40 && fng < 20) {
            return {
                label: "Capitulation",
                color: "#ef4444",
                icon: "🔴",
                desc: "Extreme fear + BTC dominance - possible opportunity",
            };
        }
        if (cai < 40 && fng > 60) {
            return {
                label: "Divergence",
                color: "#a855f7",
                icon: "🟣",
                desc: "Sentiment disconnected from capital rotation",
            };
        }
        return {
            label: "Neutral",
            color: "#64748b",
            icon: "⚪",
            desc: "No clear divergence signal",
        };
    })();

    $: currentRegime = getLatestValue(data.regimes);
    $: regimeColor =
        cryptoRegimeColors[currentRegime] ||
        cryptoRegimeColors["Side-ways/Neutral"];

    $: deltaRs = getLatestValueRaw(data.delta_rs_risk);
    $: rsRatio = getLatestValueRaw(data.rs_risk_btc);

    // Crypto Stats for Cards
    $: totalMcap = getLatestValueRaw(data.total_mcap);
    $: btcMcap = getLatestValueRaw(data.btc_mcap);
    $: ethMcap = getLatestValueRaw(data.eth_mcap);
    $: btcDom = getLatestValueRaw(data.btc_dom);
    $: ethDom = getLatestValueRaw(data.eth_dom);
    $: othersDom = getLatestValueRaw(data.others_dom);
    $: stableDom = getLatestValueRaw(data.stablecoin_dominance);

    // ============================================================
    // CHART: BTC vs REGIME (with CAI toggle)
    // ============================================================
    let showCai = true;

    $: btcRegimeData = (() => {
        const btcPrice = effectiveData.btc?.price;
        if (!btcPrice) return [];
        const filteredDates = getFilteredDates(regimeRange);
        const btc = filterByRange(btcPrice, regimeRange);
        const cai = filterByRange(data.cai, regimeRange);

        const traces = [
            {
                x: filteredDates,
                y: btc,
                name: "BTC Price",
                type: "scatter",
                mode: "lines",
                line: { color: "#f59e0b", width: 2.5 },
                yaxis: "y2",
                hovertemplate:
                    "%{x|%b %d, %Y}<br>BTC: $%{y:,.0f}<extra></extra>",
            },
        ];

        if (showCai) {
            traces.push({
                x: filteredDates,
                y: cai,
                name: "CAI",
                type: "scatter",
                mode: "lines",
                line: { color: "#3b82f6", width: 1.5 },
                fill: "tozeroy",
                fillcolor: "rgba(59, 130, 246, 0.1)",
                yaxis: "y",
                hovertemplate: "%{x|%b %d, %Y}<br>CAI: %{y:.1f}<extra></extra>",
            });
        }
        return traces;
    })();

    $: btcRegimeLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            tickfont: { size: 10 },
        },
        yaxis: {
            title: showCai
                ? { text: "CAI", font: { size: 11, color: "#3b82f6" } }
                : null,
            range: [0, 100],
            color: "#3b82f6",
            gridcolor: showCai ? "rgba(59, 130, 246, 0.1)" : "transparent",
            tickfont: { size: 10 },
            visible: showCai,
        },
        yaxis2: {
            title: { text: "BTC (log)", font: { size: 11, color: "#f59e0b" } },
            type: "log",
            overlaying: "y",
            side: "right",
            showgrid: false,
            color: "#f59e0b",
            tickfont: { size: 10 },
        },
        shapes: createRegimeShapes(data.regimes, regimeRange),
        margin: { t: 10, b: 40, l: showCai ? 50 : 20, r: 55 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
        showlegend: false,
        hovermode: "x unified",
    };

    // ============================================================
    // CHART: Fear & Greed with ROC/Z-Score/Percentile
    // ============================================================
    let fngRange = "1Y";
    let fngDataSource = "absolute"; // absolute (F&G), cai (Altseason Index)
    let fngMetricType = "absolute"; // absolute, roc_7d, roc_30d, roc_90d, roc_180d, roc_365d
    let fngTransform = "raw"; // raw, zscore, percentile
    let fngLookbackWindow = 252; // Lookback window for rolling calculations: 63, 126, 252

    // Check if transform requires lookback window
    $: isFngRocMode = fngMetricType !== "absolute";
    $: showFngLookbackWindow =
        isFngRocMode &&
        (fngTransform === "zscore" || fngTransform === "percentile");

    const fngDataSourceOptions = [
        { value: "absolute", label: "Fear & Greed Index" },
        { value: "cai", label: "Altseason Index (CAI)" },
    ];

    const fngMetricOptions = [
        { value: "absolute", label: "Main Series" },
        { value: "roc_7d", label: "ROC 7D" },
        { value: "roc_30d", label: "ROC 1M" },
        { value: "roc_90d", label: "ROC 3M" },
        { value: "roc_180d", label: "ROC 6M" },
        { value: "roc_365d", label: "ROC YoY" },
    ];

    const fngTransformOptions = [
        { value: "raw", label: "Raw" },
        { value: "zscore", label: "Z-Score" },
        { value: "percentile", label: "Percentile" },
    ];

    // Lookback window options for rolling calculations
    const fngLookbackOptions = [
        { value: 63, label: "63d (1Q)" },
        { value: 126, label: "126d (6M)" },
        { value: 252, label: "252d (1Y)" },
    ];

    function selectFngLookbackWindow(value) {
        fngLookbackWindow = value;
    }

    function getFngSeriesData(metric, transform, dataSource, lookbackWindow) {
        const isCai = dataSource === "cai";
        if (metric === "absolute") return isCai ? data.cai : data.fear_greed;

        // Prefix for CAI specific metrics
        const prefix = isCai ? "cai_" : "fng_";

        // Map metric to raw data keys
        const rawRocMap = {
            roc_7d: data[`${prefix}roc_7d`],
            roc_30d: data[`${prefix}roc_30d`],
            roc_90d: data[`${prefix}roc_90d`],
            roc_180d: data[`${prefix}roc_180d`],
            roc_365d: data[`${prefix}roc_365d`],
        };

        const rawData = rawRocMap[metric];
        if (!rawData) return isCai ? data.cai : data.fear_greed;

        // Apply rolling normalization using frontend calculations
        if (transform === "zscore") {
            return calculateRollingZScore(rawData, lookbackWindow);
        }
        if (transform === "percentile") {
            return calculatePercentile(rawData, lookbackWindow);
        }
        return rawData;
    }

    function getFngSeriesColor(metric, transform) {
        if (transform === "zscore") return "#a855f7"; // Purple
        if (transform === "percentile") return "#06b6d4"; // Cyan
        if (metric.includes("roc")) return "#f97316"; // Orange
        return "#10b981"; // Green
    }

    function getFngSeriesLabel(metric, transform, dataSource) {
        const isCai = dataSource === "cai";
        const base =
            metric === "absolute"
                ? isCai
                    ? "CAI"
                    : "F&G"
                : fngMetricOptions.find((o) => o.value === metric)?.label ||
                  "Metric";

        if (metric === "absolute") return base;
        const suffix =
            fngTransformOptions.find((o) => o.value === transform)?.label || "";
        return transform === "raw" ? base : `${base} (${suffix})`;
    }

    // Create extreme zone shapes for F&G (80/20 bands)
    // Apply to absolute F&G and percentile views
    function createFngExtremeShapes(metric, transform) {
        const showZones = metric === "absolute" || transform === "percentile";
        if (!showZones) return [];

        // Use softer colors for percentile views
        const isPercentile = transform === "percentile";
        const greedColor = isPercentile
            ? "rgba(6, 182, 212, 0.08)"
            : "rgba(16, 185, 129, 0.1)";
        const fearColor = isPercentile
            ? "rgba(6, 182, 212, 0.08)"
            : "rgba(239, 68, 68, 0.1)";

        return [
            {
                // High zone (80-100)
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 80,
                y1: 100,
                fillcolor: greedColor,
                line: { width: 0 },
            },
            {
                // Low zone (0-20)
                type: "rect",
                xref: "paper",
                yref: "y",
                x0: 0,
                x1: 1,
                y0: 0,
                y1: 20,
                fillcolor: fearColor,
                line: { width: 0 },
            },
        ];
    }

    $: fngChartData = (() => {
        const filteredDates = getFilteredDates(fngRange);
        // Explicitly pass fngDataSource and fngLookbackWindow to ensure reactivity
        const seriesData = filterByRange(
            getFngSeriesData(
                fngMetricType,
                fngTransform,
                fngDataSource,
                fngLookbackWindow,
            ),
            fngRange,
        );
        const color = getFngSeriesColor(fngMetricType, fngTransform);

        return [
            {
                x: filteredDates,
                y: seriesData,
                name: getFngSeriesLabel(
                    fngMetricType,
                    fngTransform,
                    fngDataSource,
                ),
                type: "scatter",
                mode: "lines",
                line: { color, width: 2 },
                hovertemplate: "%{x|%b %d, %Y}<br>%{y:.1f}<extra></extra>",
            },
        ];
    })();

    $: fngChartLayout = {
        xaxis: {
            showgrid: false,
            color: darkMode ? "#94a3b8" : "#475569",
            tickfont: { size: 10 },
        },
        yaxis: {
            title: {
                text: getFngSeriesLabel(fngMetricType, fngTransform),
                font: { size: 11 },
            },
            gridcolor: darkMode
                ? "rgba(148,163,184,0.08)"
                : "rgba(71,85,105,0.08)",
            tickfont: { size: 10 },
            color: darkMode ? "#94a3b8" : "#475569",
            range:
                fngMetricType === "absolute" || fngTransform === "percentile"
                    ? [0, 100]
                    : undefined,
        },
        shapes: createFngExtremeShapes(fngMetricType, fngTransform),
        margin: { t: 10, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: darkMode ? "#e2e8f0" : "#1e293b" },
        showlegend: false,
        hovermode: "x unified",
    };

    // F&G classification
    function getFngLabel(val) {
        if (val === null || val === "N/A") return "N/A";
        const v = parseFloat(val);
        if (v >= 80) return "Extreme Greed";
        if (v >= 60) return "Greed";
        if (v >= 40) return "Neutral";
        if (v >= 20) return "Fear";
        return "Extreme Fear";
    }

    function getFngColorClass(val) {
        if (val === null || val === "N/A") return "";
        const v = parseFloat(val);
        if (v >= 60) return "positive";
        if (v >= 40) return "neutral-val";
        return "negative";
    }

    function getCaiColorClass(val) {
        if (val === null || val === "N/A") return "";
        const v = parseFloat(val);
        if (v >= 60) return "positive";
        if (v >= 40) return "neutral-val";
        return "negative";
    }
</script>

<!-- Header -->
<div class="tab-header" class:light={!darkMode}>
    <div class="header-content">
        <h2>{t("nav_narratives", "Crypto Narratives")}</h2>
        <p class="description">
            Capital rotation, market regimes, and narrative momentum analysis.
        </p>
    </div>
</div>

<!-- Main Content -->
<div class="narratives-content" class:light={!darkMode}>
    <!-- Top Row: Gauges and Regime -->
    <div class="top-row">
        <!-- CAI -->
        <div class="stat-card">
            <div class="stat-label">
                {t("cai_label", "Altseason Index (CAI)")}
            </div>
            <div class="stat-gauge">
                <svg viewBox="0 0 100 50" class="gauge-svg">
                    <path
                        d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke={darkMode
                            ? "rgba(255,255,255,0.1)"
                            : "rgba(0,0,0,0.1)"}
                        stroke-width="8"
                    />
                    <path
                        d="M 10 50 A 40 40 0 0 1 90 50"
                        fill="none"
                        stroke="url(#caiGradient)"
                        stroke-width="8"
                        stroke-dasharray={`${(caiValueRaw !== null ? Math.min(Math.max(caiValueRaw, 0), 100) / 100 : 0) * 125.6} 125.6`}
                        stroke-linecap="round"
                    />
                    <defs>
                        <linearGradient
                            id="caiGradient"
                            x1="0%"
                            y1="0%"
                            x2="100%"
                            y2="0%"
                        >
                            <stop offset="0%" stop-color="#f59e0b" />
                            <stop offset="50%" stop-color="#3b82f6" />
                            <stop offset="100%" stop-color="#10b981" />
                        </linearGradient>
                    </defs>
                </svg>
                <div class="gauge-value {getCaiColorClass(caiValue)}">
                    {caiValue}
                </div>
            </div>
            <div class="gauge-scale">
                <span class="btc-side">BTC</span>
                <span class="alt-side">ALT</span>
            </div>
            <div class="stat-status {getCaiColorClass(caiValue)}">
                {caiValueRaw > 60
                    ? "ALT SEASON"
                    : caiValueRaw < 40
                      ? "BTC SEASON"
                      : "NEUTRAL"}
            </div>
        </div>

        <!-- Fear & Greed -->
        <div class="stat-card">
            <div class="stat-label">{t("fng_label", "Fear & Greed Index")}</div>
            <div class="fng-value {getFngColorClass(fngValue)}">{fngValue}</div>
            <div class="fng-bar">
                <div class="fng-gradient"></div>
                {#if fngValueRaw !== null}
                    <div class="fng-marker" style="left: {fngValueRaw}%"></div>
                {/if}
            </div>
            <div class="stat-status {getFngColorClass(fngValue)}">
                {getFngLabel(fngValue)}
            </div>
            <!-- F&G ROC Metrics -->
            <div class="fng-rocs">
                <div class="roc-item">
                    <span class="roc-label">ROC 7d</span>
                    <span
                        class="roc-value"
                        class:positive={fngRoc7d > 0}
                        class:negative={fngRoc7d < 0}
                    >
                        {fngRoc7d !== null && fngRoc7d !== undefined
                            ? (fngRoc7d > 0 ? "+" : "") + fngRoc7d.toFixed(1)
                            : "N/A"}
                    </span>
                </div>
                <div class="roc-item">
                    <span class="roc-label">Z-Score</span>
                    <span class="roc-value {getZScoreClass(fngRoc7dZ)}">
                        {fngRoc7dZ !== null && fngRoc7dZ !== undefined
                            ? fngRoc7dZ.toFixed(2) + "σ"
                            : "N/A"}
                    </span>
                </div>
                <div class="roc-item">
                    <span class="roc-label">Pctl</span>
                    <span class="roc-value">
                        {fngRoc7dPct !== null && fngRoc7dPct !== undefined
                            ? fngRoc7dPct.toFixed(0) + "%"
                            : "N/A"}
                    </span>
                </div>
            </div>
        </div>

        <!-- Current Regime -->
        <div class="stat-card regime-stat">
            <div class="stat-label">
                {t("market_regime", "Current Market Regime")}
            </div>
            <div class="regime-display">
                <div
                    class="regime-dot"
                    style="background: {regimeColor.bg}; border-color: {regimeColor.text}"
                ></div>
                <div class="regime-name" style="color: {regimeColor.text}">
                    {currentRegime}
                </div>
            </div>
            <div class="regime-metrics">
                <div
                    class="metric-item"
                    title={t(
                        "risk_vs_btc_desc",
                        "30-day change in log(Alts/BTC). Positive = Alts outperforming BTC",
                    )}
                >
                    <span class="metric-label"
                        >{t("risk_vs_btc", "Alts/BTC Mom")}</span
                    >
                    <span
                        class="metric-value"
                        class:positive={deltaRs > 0}
                        class:negative={deltaRs < 0}
                    >
                        {deltaRs !== null
                            ? (deltaRs > 0 ? "+" : "") +
                              (deltaRs * 100).toFixed(2) +
                              "%"
                            : "N/A"}
                    </span>
                    <span class="metric-hint">
                        {deltaRs > 0
                            ? t("alts_outperforming", "Alts outperforming")
                            : deltaRs < 0
                              ? t("btc_outperforming", "BTC outperforming")
                              : t("neutral_perf", "Neutral")}
                    </span>
                </div>
                <div
                    class="metric-item"
                    title={t(
                        "rs_log_ratio_desc",
                        "Log ratio of Risk Assets (Alts ex-Stables) vs BTC. Negative = BTC dominance",
                    )}
                >
                    <span class="metric-label"
                        >{t("rs_log_ratio", "RS Ratio")}</span
                    >
                    <span class="metric-value"
                        >{rsRatio !== null ? rsRatio.toFixed(3) : "N/A"}</span
                    >
                    <span class="metric-hint">
                        {rsRatio !== null
                            ? rsRatio > 0
                                ? t("alts_larger", "Alts > BTC MCap")
                                : t("btc_larger", "BTC > Alts MCap")
                            : ""}
                    </span>
                </div>
            </div>
        </div>

        <!-- CAI/F&G Divergence Signal -->
        {#if divergenceSignal}
            <div class="stat-card divergence-card">
                <div class="stat-label">CAI/F&G Signal</div>
                <div class="divergence-display">
                    <span class="divergence-icon">{divergenceSignal.icon}</span>
                    <span
                        class="divergence-label"
                        style="color: {divergenceSignal.color}"
                    >
                        {divergenceSignal.label}
                    </span>
                </div>
                <div class="divergence-desc">
                    {divergenceSignal.desc}
                </div>
                <div class="divergence-values">
                    <span>CAI: {caiValue}</span>
                    <span>F&G: {fngValue}</span>
                </div>
            </div>
        {/if}
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
        <!-- Regime Timeline -->
        <div class="chart-card" bind:this={regimeCard}>
            <div class="chart-header">
                <h3>
                    {t(
                        "regime_timeline_title",
                        "Regime Timeline & BTC Evolution",
                    )}
                </h3>
                <div class="header-controls">
                    <label class="toggle-label">
                        <input type="checkbox" bind:checked={showCai} />
                        <span>CAI</span>
                    </label>
                    <TimeRangeSelector bind:selectedRange={regimeRange} />
                    <button
                        class="icon-btn"
                        title={t("download_image", "Download as Image")}
                        on:click={() =>
                            downloadCardAsImage(regimeCard, "CryptoRegimes")}
                    >
                        <svg
                            class="icon"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                            />
                        </svg>
                    </button>
                </div>
            </div>
            <div class="chart-container">
                <Chart
                    data={btcRegimeData}
                    layout={btcRegimeLayout}
                    {darkMode}
                />
            </div>
            <div class="regime-legend">
                {#each Object.entries(cryptoRegimeColors) as [name, colors]}
                    <div class="legend-item">
                        <div
                            class="legend-dot"
                            style="background: {colors.bg}; border-color: {colors.text}"
                        ></div>
                        <span>{colors.label}</span>
                    </div>
                {/each}
            </div>
        </div>

        <!-- Narrative Rotation -->
        <div class="chart-card" bind:this={rotationCard}>
            <div class="chart-header">
                <h3>
                    {t("narrative_rotation_title", "Narrative Rotation Matrix")}
                </h3>
                <div class="header-controls">
                    <button
                        class="icon-btn"
                        title={t("download_image", "Download as Image")}
                        on:click={() =>
                            downloadCardAsImage(
                                rotationCard,
                                "NarrativeRotation",
                            )}
                    >
                        <svg
                            class="icon"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                            />
                        </svg>
                    </button>
                </div>
            </div>
            <div class="chart-container">
                <Chart data={rotationData} layout={rotationLayout} {darkMode} />
            </div>
            <div class="chart-footer">
                Bubble size = Market Cap | Position = 30D Relative Momentum
            </div>
        </div>
    </div>

    <!-- Narratives Grid Row -->
    <div class="narratives-grid-row">
        <div class="grid-header">
            <h3>
                {t("narrative_performance", "Narrative Market Performance")}
            </h3>
        </div>
        <div class="narratives-grid">
            {#if data.narratives}
                {#each Object.entries(data.narratives) as [name, nData]}
                    {@const color = narrativeColors[name] || "#64748b"}
                    {@const momBtc = nData.current_mom_btc}
                    <div class="narrative-card">
                        <div class="narrative-header">
                            <div
                                class="narrative-dot"
                                style="background: {color}"
                            ></div>
                            <span class="narrative-name">{name}</span>
                        </div>
                        <div class="narrative-mcap">
                            ${nData.current_mcap?.toFixed(1) || "0"}B
                        </div>
                        <div
                            class="narrative-momentum"
                            class:positive={momBtc > 0}
                            class:negative={momBtc < 0}
                        >
                            <span>{momBtc > 0 ? "▲" : "▼"}</span>
                            <span>{(momBtc * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                {/each}
            {:else}
                <div class="no-data">No narrative data available</div>
            {/if}
        </div>
    </div>

    <!-- Crypto Stats Cards -->
    <div class="stats-cards-row">
        <div class="mini-card">
            <span class="mini-label">Total MCap</span>
            <span class="mini-value"
                >${totalMcap !== null
                    ? (totalMcap / 1000).toFixed(2)
                    : "N/A"}T</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">BTC MCap</span>
            <span class="mini-value"
                >${btcMcap !== null
                    ? (btcMcap / 1000).toFixed(2)
                    : "N/A"}T</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">ETH MCap</span>
            <span class="mini-value"
                >${ethMcap !== null ? ethMcap.toFixed(0) : "N/A"}B</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">BTC.D</span>
            <span class="mini-value"
                >{btcDom !== null ? btcDom.toFixed(1) : "N/A"}%</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">ETH.D</span>
            <span class="mini-value"
                >{ethDom !== null ? ethDom.toFixed(1) : "N/A"}%</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">Others.D</span>
            <span class="mini-value"
                >{othersDom !== null ? othersDom.toFixed(1) : "N/A"}%</span
            >
        </div>
        <div class="mini-card">
            <span class="mini-label">Stable.D</span>
            <span class="mini-value"
                >{stableDom !== null ? stableDom.toFixed(1) : "N/A"}%</span
            >
        </div>
    </div>

    <!-- Fear & Greed Chart -->
    <div class="chart-card">
        <div class="chart-header">
            <h3>
                {fngDataSource === "absolute"
                    ? t("fng_chart_title", "Fear & Greed Index Analysis")
                    : t("cai_chart_title", "Altseason Index (CAI) Analysis")}
            </h3>
            <div class="header-controls">
                <Dropdown
                    options={fngDataSourceOptions}
                    bind:value={fngDataSource}
                    {darkMode}
                    small={true}
                />
                <Dropdown
                    options={fngMetricOptions}
                    bind:value={fngMetricType}
                    {darkMode}
                    small={true}
                />
                {#if fngMetricType !== "absolute"}
                    <Dropdown
                        options={fngTransformOptions}
                        bind:value={fngTransform}
                        {darkMode}
                        small={true}
                    />
                {/if}
                <TimeRangeSelector bind:selectedRange={fngRange} />
            </div>
        </div>
        <div class="chart-container">
            <Chart data={fngChartData} layout={fngChartLayout} {darkMode} />
        </div>
    </div>
</div>

<style>
    /* Main Layout */
    .narratives-content {
        display: flex;
        flex-direction: column;
        gap: 24px;
        padding-bottom: 40px;
    }
    .header-content h2 {
        margin: 0 0 8px 0;
        font-size: 1.5rem;
        color: var(--text-primary);
    }
    .light .header-content h2 {
        color: #1e293b;
    }
    .narratives-tab {
        padding-bottom: 40px;
    }
    .description {
        margin: 0;
        color: var(--text-muted);
        font-size: 0.9rem;
    }

    /* Tab Header */
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 24px;
        background: var(--bg-secondary);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        margin-bottom: 32px;
    }

    .light .tab-header {
        background: #f8fafc;
        backdrop-filter: none;
        border-color: #e2e8f0;
    }

    /* Rows */
    .top-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
        padding: 0;
    }
    @media (max-width: 1024px) {
        .top-row {
            grid-template-columns: 1fr;
        }
    }

    .stat-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s ease;
    }
    .light .stat-card {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .stat-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
        margin-bottom: 12px;
    }
    .stat-status {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.15em;
        margin-top: 8px;
        color: var(--text-secondary);
    }
    .stat-status.positive {
        color: #10b981;
    }
    .stat-status.negative {
        color: #f59e0b;
    }
    .stat-status.neutral-val {
        color: #3b82f6;
    }

    /* CAI Gauge */
    .stat-gauge {
        position: relative;
        width: 140px;
        height: 70px;
    }
    .gauge-svg {
        width: 100%;
        height: 100%;
    }
    .gauge-value {
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.75rem;
        font-weight: 800;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-primary);
    }
    .gauge-value.positive {
        color: #10b981;
    }
    .gauge-value.negative {
        color: #f59e0b;
    }
    .gauge-value.neutral-val {
        color: #3b82f6;
    }
    .gauge-scale {
        display: flex;
        justify-content: space-between;
        width: 100%;
        font-size: 0.65rem;
        font-weight: 600;
        margin-top: 4px;
    }
    .btc-side {
        color: #f59e0b;
    }
    .alt-side {
        color: #10b981;
    }

    /* F&G */
    .fng-value {
        font-size: 2.5rem;
        font-weight: 800;
        font-family: "JetBrains Mono", monospace;
        line-height: 1;
        color: var(--text-primary);
    }
    .fng-value.positive {
        color: #10b981;
    }
    .fng-value.negative {
        color: #ef4444;
    }
    .fng-value.neutral-val {
        color: #eab308;
    }
    .fng-bar {
        width: 100%;
        height: 8px;
        border-radius: 4px;
        margin: 12px 0 8px;
        position: relative;
        overflow: visible;
    }
    .fng-gradient {
        width: 100%;
        height: 100%;
        border-radius: 4px;
        background: linear-gradient(
            to right,
            #ef4444,
            #f59e0b,
            #eab308,
            #22c55e,
            #10b981
        );
    }
    .fng-marker {
        position: absolute;
        top: -4px;
        width: 4px;
        height: 16px;
        background: white;
        border-radius: 2px;
        transform: translateX(-50%);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
    }

    /* F&G ROC Metrics */
    .fng-rocs {
        display: flex;
        gap: 12px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--border-color);
    }
    /* Selects / Dropdowns */
    /* Removing duplicated/conflicting select styles - handled by Dropdown component */
    .roc-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
    }
    .roc-label {
        font-size: 0.55rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
    }
    .roc-value {
        font-size: 0.75rem;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-secondary);
    }
    .roc-value.positive {
        color: #10b981;
    }
    .roc-value.negative {
        color: #ef4444;
    }
    .roc-value.extreme-positive {
        color: #10b981;
        text-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
    }
    .roc-value.extreme-negative {
        color: #ef4444;
        text-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
    }

    /* Regime Card */
    .regime-stat {
        align-items: flex-start;
        text-align: left;
    }
    .regime-display {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    .regime-dot {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid;
    }
    .regime-name {
        font-size: 1.25rem;
        font-weight: 700;
    }
    .regime-metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        width: 100%;
    }
    .metric-item {
        background: var(--bg-tertiary);
        padding: 10px;
        border-radius: 8px;
        cursor: help;
        display: flex;
        flex-direction: column;
        gap: 2px;
        border: 1px solid transparent;
    }
    .light .metric-item {
        background: #f1f5f9;
        border-color: #e2e8f0;
    }
    .metric-label {
        display: block;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 0.95rem;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-secondary);
    }
    .metric-hint {
        font-size: 0.58rem;
        color: var(--text-muted);
        font-style: italic;
        margin-top: 2px;
    }
    .metric-value.positive {
        color: #10b981;
    }
    .metric-value.negative {
        color: #ef4444;
    }

    /* Charts Row */
    .charts-row {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 20px;
    }
    @media (max-width: 1200px) {
        .charts-row {
            grid-template-columns: 1fr;
        }
    }

    /* Use global .chart-card styles, only override min-height */
    .chart-card {
        min-height: 480px;
    }
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .chart-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: var(--text-primary);
    }
    .header-controls {
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .icon-btn {
        padding: 6px;
        border-radius: 6px;
        background: transparent;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .icon-btn:hover {
        background: rgba(99, 102, 241, 0.1);
        color: #6366f1;
    }
    .icon {
        width: 18px;
        height: 18px;
    }
    .chart-container {
        flex-grow: 1;
        width: 100%;
        min-height: 320px;
        overflow: hidden;
    }
    .regime-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--border-color);
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 3px;
        border: 1px solid;
    }
    .chart-footer {
        text-align: center;
        font-size: 0.72rem;
        color: var(--text-muted);
        margin-top: 16px;
        font-style: italic;
    }

    /* Narratives Grid Row */
    .narratives-grid-row {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        display: flex;
        flex-direction: column;
        gap: 20px;
        box-shadow: var(--card-shadow);
    }
    .light .narratives-grid-row {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .grid-header h3 {
        margin: 0;
        font-size: 1.1rem;
        color: var(--text-primary);
    }

    .narratives-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 20px;
        justify-content: center;
        justify-items: center;
    }
    .narrative-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        min-width: 180px;
        width: 100%;
        max-width: 240px;
        box-shadow: var(--card-shadow);
    }
    .light .narrative-card {
        background: #ffffff;
        border-color: #e2e8f0;
    }
    .narrative-card:hover {
        transform: translateY(-4px);
        background: rgba(255, 255, 255, 0.05);
        border-color: #6366f1;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
    }
    .light .narrative-card:hover {
        background: #f1f5f9;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    }
    .narrative-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        margin-bottom: 12px;
    }
    .narrative-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
    }
    .narrative-name {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-secondary);
    }
    .narrative-mcap {
        font-size: 1.5rem;
        font-weight: 800;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-primary);
        margin-bottom: 8px;
    }
    .narrative-momentum {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        font-family: "JetBrains Mono", monospace;
    }
    .narrative-momentum.positive {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
    }
    .narrative-momentum.negative {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
    }
    .no-data {
        grid-column: 1 / -1;
        text-align: center;
        padding: 40px;
        color: var(--text-muted);
    }

    /* Crypto Stats Cards Row */
    .stats-cards-row {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 12px;
        justify-content: center;
    }
    @media (max-width: 1200px) {
        .stats-cards-row {
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        }
    }
    @media (max-width: 768px) {
        .stats-cards-row {
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        }
    }
    .mini-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        display: flex;
        flex-direction: column;
        gap: 6px;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s ease;
    }
    .light .mini-card {
        background: #f8fafc;
        border-color: #e2e8f0;
    }
    .mini-card:hover {
        transform: translateY(-2px);
        border-color: #6366f1;
    }
    .mini-label {
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
    }
    .mini-value {
        font-size: 1.1rem;
        font-weight: 800;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-primary);
    }

    /* Toggle Label */
    .toggle-label {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 4px 10px;
        border-radius: 6px;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        transition: all 0.15s ease;
    }
    .toggle-label:hover {
        background: rgba(59, 130, 246, 0.2);
    }
    .toggle-label input {
        margin: 0;
        accent-color: #3b82f6;
    }

    /* Removing legacy dropdown styles */

    /* Divergence Card */
    .divergence-card {
        background: var(--bg-secondary);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 16px;
        position: relative;
        overflow: hidden;
        box-shadow: var(--card-shadow);
        transition: transform 0.2s ease;
    }
    .light .divergence-card {
        background: #f8fafc;
        border-color: rgba(99, 102, 241, 0.2);
    }
    .divergence-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
    }
    .divergence-display {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin: 12px 0;
    }
    .divergence-icon {
        font-size: 1.5rem;
    }
    .divergence-label {
        font-size: 1.2rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .divergence-desc {
        font-size: 0.68rem;
        color: var(--text-muted);
        text-align: center;
        line-height: 1.4;
        margin-bottom: 12px;
    }
    .divergence-values {
        display: flex;
        justify-content: center;
        gap: 16px;
        font-size: 0.7rem;
        font-family: "JetBrains Mono", monospace;
        color: var(--text-secondary);
    }
</style>
