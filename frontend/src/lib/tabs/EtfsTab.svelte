<script>
    import { onMount } from "svelte";
    import {
        t,
        currentTranslations,
        darkMode,
    } from "../../stores/settingsStore";
    import {
        etfData,
        etfLoading,
        dashboardData,
        fetchEtfData,
    } from "../../stores/dataStore";
    import Chart from "../components/Chart.svelte";
    import LightweightChart from "../components/LightweightChart.svelte";
    import Dropdown from "../components/Dropdown.svelte";
    import {
        calculateRollingZScore,
        calculatePercentile,
        calculateEMA,
        calculateSMA,
        applySmoothing,
    } from "../utils/helpers";

    // Data is now fetched locally to avoid bloating main dashboard_data.json
    $: summary = $etfData?.summary || [];
    $: flowsAgg = $etfData?.flows_agg || {};
    $: individualDaily = $etfData?.individual_daily || {};
    $: dates = $etfData?.dates || [];

    let selectedTicker = "IBIT";
    let chartTimeframe = "1D"; // 1D, 7D, 30D, 90D
    let showMA = true;
    let showBtcOverlay = false;

    // Advanced Chart State
    let aggChartMode = "net_flow"; // "net_flow" or "roc"
    let selectedRoc = "7d"; // "7d", "30d", "90d", "yoy"
    let aggNormMode = "raw"; // "raw", "zscore", "percentile"
    let maWindow = 20;

    // ROC Metric Selection (AUM vs Flows)
    let rocMetric = "aum"; // "aum" or "flows"

    // Premium/Discount Smoothing Options
    let pdSmoothType = "ema"; // "raw", "ema", "sma"
    let pdSmoothWindow = 10; // 5, 10, 20

    $: aggModes = [
        { value: "net_flow", label: t($currentTranslations, "etf_net_flows") },
        { value: "roc", label: "Rate of Change (ROC) AUM" },
    ];

    $: normOptions = [
        { value: "raw", label: t($currentTranslations, "view_raw") || "Raw" },
        { value: "zscore", label: "Z-Score" },
        { value: "percentile", label: "%ile" },
    ];

    $: maWindowOptions = [
        { value: 10, label: "10d MA" },
        { value: 20, label: "20d MA" },
        { value: 50, label: "50d MA" },
        { value: 100, label: "100d MA" },
    ];

    // ROC Metric Options
    $: rocMetricOptions = [
        { value: "aum", label: "ROC AUM" },
        { value: "flows", label: "ROC Flows" },
    ];

    // P/D Smoothing Type Options
    $: pdSmoothTypeOptions = [
        { value: "raw", label: "Raw" },
        { value: "ema", label: "EMA (Rec.)" },
        { value: "sma", label: "SMA" },
    ];

    // P/D Smoothing Window Options
    $: pdSmoothWindowOptions = [
        { value: 5, label: "5d" },
        { value: 10, label: "10d" },
        { value: 20, label: "20d" },
    ];

    /**
     * Helper to calculate simple moving average
     */
    function calculateSMA(data, window) {
        if (!data || data.length === 0) return [];
        let results = [];
        for (let i = 0; i < data.length; i++) {
            if (i < window - 1) {
                results.push(null);
                continue;
            }
            let sum = 0;
            for (let j = 0; j < window; j++) {
                sum += data[i - j] || 0;
            }
            results.push(sum / window);
        }
        return results;
    }

    $: tickerOptions = summary.map((s) => ({
        value: s.ticker,
        label: s.ticker,
    }));

    // Aggregated Stats
    $: lastIdx = (flowsAgg.total_flow_usd || []).length - 1;
    $: lastAggFlow = lastIdx >= 0 ? flowsAgg.total_flow_usd[lastIdx] : 0;
    $: totalCumFlow = (flowsAgg.cum_flow_usd || [])[lastIdx] || 0;
    $: totalAUM = summary.reduce((acc, curr) => acc + (curr.aum_usd || 0), 0);

    $: statsCards = [
        {
            label: `${t($currentTranslations, "etf_7d_flow")}`,
            value: flowsAgg.flow_usd_7d ? flowsAgg.flow_usd_7d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_30d_flow")}`,
            value: flowsAgg.flow_usd_30d ? flowsAgg.flow_usd_30d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_90d_flow")}`,
            value: flowsAgg.flow_usd_90d ? flowsAgg.flow_usd_90d[lastIdx] : 0,
            isCurrency: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 7d`,
            value: flowsAgg.aum_roc_7d ? flowsAgg.aum_roc_7d[lastIdx] : 0,
            isPct: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 30d`,
            value: flowsAgg.aum_roc_30d ? flowsAgg.aum_roc_30d[lastIdx] : 0,
            isPct: true,
        },
        {
            label: `${t($currentTranslations, "etf_aum_roc")} 90d`,
            value: flowsAgg.aum_roc_90d ? flowsAgg.aum_roc_90d[lastIdx] : 0,
            isPct: true,
        },
    ];

    // Main Chart Data Mapping
    $: barColors = (processedMainData.y || []).map((val) =>
        val >= 0 ? "#10b981" : "#ef4444",
    );

    // Advanced Data Logic (ROC + Normalization)
    $: processedMainData = (() => {
        if (aggChartMode === "net_flow") {
            const yData =
                chartTimeframe === "1D"
                    ? flowsAgg.total_flow_usd || []
                    : chartTimeframe === "7D"
                      ? flowsAgg.flow_usd_7d || []
                      : chartTimeframe === "30D"
                        ? flowsAgg.flow_usd_30d || []
                        : flowsAgg.flow_usd_90d || [];
            return {
                y: yData,
                name: t($currentTranslations, "etf_net_flows"),
                type: "bar",
            };
        }

        // ROC Mode Logic - supports both AUM and Flows ROC
        let rawRoc = [];
        const cumFlow = flowsAgg.cum_flow_usd || [];

        if (rocMetric === "flows") {
            // Use Flow ROC (more volatile, better for trading signals)
            if (chartTimeframe === "7D") rawRoc = flowsAgg.flow_roc_7d || [];
            else if (chartTimeframe === "30D") rawRoc = flowsAgg.flow_roc_30d || [];
            else if (chartTimeframe === "90D") rawRoc = flowsAgg.flow_roc_90d || [];
            else if (chartTimeframe === "YOY") {
                rawRoc = cumFlow.map((v, i) => {
                    const prevYearIdx = i - 252;
                    if (prevYearIdx < 0) return null;
                    const prev = cumFlow[prevYearIdx];
                    return prev ? ((v - prev) / Math.abs(prev)) * 100 : null;
                });
            } else {
                rawRoc = flowsAgg.flow_roc_7d || [];
            }
        } else {
            // Use AUM ROC (more stable, shows total market growth)
            if (chartTimeframe === "7D") rawRoc = flowsAgg.aum_roc_7d || [];
            else if (chartTimeframe === "30D") rawRoc = flowsAgg.aum_roc_30d || [];
            else if (chartTimeframe === "90D") rawRoc = flowsAgg.aum_roc_90d || [];
            else if (chartTimeframe === "YOY") {
                rawRoc = cumFlow.map((v, i) => {
                    const prevYearIdx = i - 252;
                    if (prevYearIdx < 0) return null;
                    const prev = cumFlow[prevYearIdx];
                    return prev ? ((v - prev) / Math.abs(prev)) * 100 : null;
                });
            } else {
                rawRoc = flowsAgg.aum_roc_7d || [];
            }
        }

        let finalY = rawRoc;
        if (aggNormMode === "zscore") {
            finalY = calculateRollingZScore(rawRoc, 252);
        } else if (aggNormMode === "percentile") {
            finalY = calculatePercentile(rawRoc, 252);
        }

        return {
            y: finalY,
            name: `${chartTimeframe} ROC ${rocMetric === "flows" ? "Flows" : "AUM"} ${aggNormMode !== "raw" ? `(${aggNormMode.toUpperCase()})` : ""}`,
            type: "scatter",
        };
    })();

    // MA Area Logic: Calculated in Frontend, handles zero-crossings for clean fill
    $: maDataRaw = calculateSMA(processedMainData.y, maWindow);
    $: maProcessed = (() => {
        if (!maDataRaw || maDataRaw.length === 0)
            return { dates: [], pos: [], neg: [], line: [] };

        let pDates = [];
        let pPos = [];
        let pNeg = [];
        let pLine = [];

        for (let i = 0; i < maDataRaw.length; i++) {
            const curr = maDataRaw[i];
            const prev = i > 0 ? maDataRaw[i - 1] : null;

            // Handle zero crossing for clean fill areas
            if (
                prev !== null &&
                curr !== null &&
                ((prev > 0 && curr < 0) || (prev < 0 && curr > 0))
            ) {
                // Interpolate precisely for linear sharp transitions
                // x2 = x1 + (0 - y1) * (x1 - x2) / (y1 - y2)
                // But for discrete dates, we can just push a zero point at the current date
                // or a mid-point if we want to be fancy. For Plotly bar/line blend,
                // pushing the zero at the current date index works well with 'linear' shape.
                pDates.push(dates[i]);
                pPos.push(0);
                pNeg.push(0);
                pLine.push(0);
            }

            pDates.push(dates[i]);
            pLine.push(curr);
            pPos.push(curr !== null && curr >= 0 ? curr : null);
            pNeg.push(curr !== null && curr < 0 ? curr : null);
        }
        return { dates: pDates, pos: pPos, neg: pNeg, line: pLine };
    })();

    $: maDates = maProcessed.dates;
    $: maPos = maProcessed.pos;
    $: maNeg = maProcessed.neg;
    $: maLine = maProcessed.line;

    // --- BTC Price Overlay Logic ---
    // Efficiently map BTC prices from global dashboard data into ETF-specific date space
    // using a lookup dictionary to handle gaps (weekends/holidays) correctly.
    $: btcDatesMap = $dashboardData?.dates || [];
    $: btcRawPrices = $dashboardData?.btc?.price || [];
    $: btcLookup = btcDatesMap.reduce((acc, date, i) => {
        acc[date] = btcRawPrices[i];
        return acc;
    }, {});

    $: btcPricesMapped = dates.map((d) => btcLookup[d] || null);

    $: mainChartData = [
        {
            x: dates,
            y: processedMainData.y,
            name: processedMainData.name,
            type: processedMainData.type,
            mode: processedMainData.type === "scatter" ? "lines" : undefined,
            marker: { color: barColors },
            line: {
                color:
                    processedMainData.type === "scatter"
                        ? "#3b82f6"
                        : undefined,
                width: 2,
            },
            fill: processedMainData.type === "scatter" ? "tozeroy" : undefined,
            fillcolor:
                processedMainData.type === "scatter"
                    ? "rgba(59, 130, 246, 0.1)"
                    : undefined,
            opacity: 0.8,
        },
        ...(showMA
            ? [
                  {
                      x: maDates,
                      y: maPos,
                      name: t($currentTranslations, "etf_ma"),
                      legendgroup: "ma",
                      type: "scatter",
                      mode: "lines",
                      fill: "tozeroy",
                      fillcolor: "rgba(16, 185, 129, 0.25)",
                      line: { color: "#10b981", width: 2, shape: "linear" },
                      connectgaps: false,
                  },
                  {
                      x: maDates,
                      y: maNeg,
                      name: t($currentTranslations, "etf_ma"),
                      legendgroup: "ma",
                      showlegend: false,
                      type: "scatter",
                      mode: "lines",
                      fill: "tozeroy",
                      fillcolor: "rgba(239, 68, 68, 0.25)",
                      line: { color: "#ef4444", width: 2, shape: "linear" },
                      connectgaps: false,
                  },
              ]
            : []),
        {
            x: dates,
            y: flowsAgg.cum_flow_usd,
            name: t($currentTranslations, "etf_cum_flows"),
            type: "scatter",
            mode: "lines",
            yaxis: "y2",
            line: { color: "#10b981", width: 3 },
        },
        ...(showBtcOverlay && btcPricesMapped.length > 0
            ? [
                  {
                      x: dates,
                      y: btcPricesMapped,
                      name: "Bitcoin Price",
                      type: "scatter",
                      mode: "lines",
                      yaxis: "y3",
                      line: { color: "#f59e0b", width: 1.5, dash: "dot" },
                      connectgaps: true,
                  },
              ]
            : []),
    ];

    $: mainChartLayout = {
        title: {
            text:
                aggChartMode === "roc"
                    ? `${rocMetric === "flows" ? "Flow" : "AUM"} Rate of Change (ROC) - ${chartTimeframe} ${aggNormMode !== "raw" ? `(${aggNormMode.toUpperCase()})` : ""}`
                    : `ETF Net Flows - ${chartTimeframe}`,
            font: { color: $darkMode ? "#e2e8f0" : "#1e293b", size: 16 },
        },
        yaxis: {
            title: aggChartMode === "roc" ? "ROC (%)" : "Net Flow ($)",
            gridcolor: $darkMode ? "#334155" : "#e2e8f0",
        },
        yaxis2: {
            title: "Cumulative Flow ($)",
            overlaying: "y",
            side: "right",
            showgrid: false,
        },
        yaxis3: {
            title: "BTC Price ($)",
            overlaying: "y",
            side: "right",
            anchor: "free",
            position: 0.95,
            showgrid: false,
            visible: showBtcOverlay,
        },
        height: 480,
        margin: { l: 60, r: 80, t: 80, b: 50 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: true,
        legend: { orientation: "h", y: -0.2 },
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b" },
    };

    // Ticker Analysis State
    let tickerMetric = "flow"; // "flow" or "prem_disc"
    let tickerMode = "individual"; // "individual" or "aggregate"
    let normalizationMode = "raw"; // "raw", "zscore", "percentile"

    $: tickerDataRaw =
        tickerMode === "aggregate"
            ? flowsAgg
            : individualDaily[selectedTicker] || {};

    $: tickerX = tickerMode === "aggregate" ? dates : tickerDataRaw.date || [];
    // Apply smoothing to Premium/Discount data
    $: tickerYRaw = (() => {
        if (tickerMetric === "flow") {
            return tickerDataRaw.total_flow_usd || tickerDataRaw.flow_usd || [];
        }

        // Get raw P/D data first
        let rawPD =
            tickerDataRaw.avg_premium_discount ||
            tickerDataRaw.premium_discount ||
            [];

        // Apply smoothing if not using z-score/percentile (those already smooth implicitly)
        if (normalizationMode === "raw" && pdSmoothType !== "raw") {
            rawPD = applySmoothing(rawPD, pdSmoothType, pdSmoothWindow);
        }

        // Then apply normalization if needed
        if (normalizationMode === "zscore") {
            // Apply smoothing to z-score output for cleaner signals
            const zscore = tickerDataRaw.pd_zscore_1y || calculateRollingZScore(rawPD, 126);
            return pdSmoothType !== "raw"
                ? applySmoothing(zscore, pdSmoothType, pdSmoothWindow)
                : zscore;
        } else if (normalizationMode === "percentile") {
            // Apply smoothing to percentile output for cleaner signals
            const pctile = tickerDataRaw.pd_percentile_1y || calculatePercentile(rawPD, 126);
            return pdSmoothType !== "raw"
                ? applySmoothing(pctile, pdSmoothType, pdSmoothWindow)
                : pctile;
        }

        return rawPD;
    })();

    $: tickerY = tickerYRaw;

    $: tickerChartData = [
        {
            x: tickerX,
            y: tickerY,
            name: `${tickerMode === "aggregate" ? "Aggregate" : selectedTicker} ${tickerMetric === "flow" ? "Flow" : "P/D"}`,
            type: tickerMetric === "flow" ? "bar" : "scatter",
            mode: tickerMetric === "flow" ? undefined : "lines",
            marker: { color: tickerMetric === "flow" ? "#f59e0b" : undefined },
            line: {
                color: tickerMetric === "flow" ? undefined : "#3b82f6",
                width: 2,
            },
            fill: tickerMetric === "prem_disc" ? "tozeroy" : undefined,
            fillcolor:
                tickerMetric === "prem_disc"
                    ? "rgba(59, 130, 246, 0.1)"
                    : undefined,
        },
        ...(tickerMetric === "flow"
            ? [
                  {
                      x: tickerX,
                      y: (tickerY || []).reduce((acc, curr, i) => {
                          const prev = acc.length > 0 ? acc[acc.length - 1] : 0;
                          acc.push(prev + (curr || 0));
                          return acc;
                      }, []),
                      name: "Cumulative",
                      type: "scatter",
                      mode: "lines",
                      yaxis: "y2",
                      line: { color: "#8b5cf6", width: 2 },
                  },
              ]
            : []),
    ];

    // Z-Score reference bands (horizontal lines at -2, -1, 0, +1, +2)
    $: zscoreShapes = normalizationMode === "zscore" && tickerMetric === "prem_disc"
        ? [
              // +2 band (overbought extreme)
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 2,
                  y1: 2,
                  line: { color: "#10b981", width: 1, dash: "dash" },
              },
              // +1 band
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 1,
                  y1: 1,
                  line: { color: "#86efac", width: 1, dash: "dot" },
              },
              // 0 band (neutral)
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 0,
                  y1: 0,
                  line: { color: "#64748b", width: 2 },
              },
              // -1 band
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: -1,
                  y1: -1,
                  line: { color: "#fca5a5", width: 1, dash: "dot" },
              },
              // -2 band (oversold extreme)
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: -2,
                  y1: -2,
                  line: { color: "#ef4444", width: 1, dash: "dash" },
              },
          ]
        : [];

    // Percentile reference bands (25, 50, 75)
    $: percentileShapes = normalizationMode === "percentile" && tickerMetric === "prem_disc"
        ? [
              // 75th percentile
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 75,
                  y1: 75,
                  line: { color: "#10b981", width: 1, dash: "dash" },
              },
              // 50th percentile (median)
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 50,
                  y1: 50,
                  line: { color: "#64748b", width: 2 },
              },
              // 25th percentile
              {
                  type: "line",
                  x0: 0,
                  x1: 1,
                  xref: "paper",
                  y0: 25,
                  y1: 25,
                  line: { color: "#ef4444", width: 1, dash: "dash" },
              },
          ]
        : [];

    $: tickerChartLayout = {
        title: `${tickerMode === "aggregate" ? "Aggregate" : selectedTicker} - ${tickerMetric === "flow" ? "Flow Analysis" : "Premium/Discount"} ${pdSmoothType !== "raw" ? `(${pdSmoothType.toUpperCase()} ${pdSmoothWindow}d` : ""} ${normalizationMode !== "raw" ? `${pdSmoothType !== "raw" ? ", " : "("}${normalizationMode.toUpperCase()})` : pdSmoothType !== "raw" ? ")" : ""}`,
        yaxis: {
            title:
                tickerMetric === "flow"
                    ? "Flow ($)"
                    : normalizationMode === "raw"
                      ? "Prem/Disc (%)"
                      : normalizationMode === "zscore"
                        ? "Z-Score"
                        : "Percentile",
            gridcolor: $darkMode ? "#334155" : "#e2e8f0",
            ...(normalizationMode === "zscore" ? { range: [-3, 3] } : {}),
            ...(normalizationMode === "percentile" ? { range: [0, 100] } : {}),
        },
        ...(tickerMetric === "flow"
            ? {
                  yaxis2: {
                      title: "Cumulative ($)",
                      overlaying: "y",
                      side: "right",
                      showgrid: false,
                  },
              }
            : {}),
        shapes: [...zscoreShapes, ...percentileShapes],
        height: 380,
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b" },
        margin: { t: 40, b: 40, l: 60, r: 60 },
    };

    function formatNumber(num, decimals = 2) {
        if (num === undefined || num === null) return "0.00";
        if (Math.abs(num) >= 1e9) return (num / 1e9).toFixed(decimals) + "B";
        if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(decimals) + "M";
        return num.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    }

    // Market Share Pie Chart Data
    $: marketShareData = (() => {
        if (!summary || summary.length === 0) return [];

        // Get top 6 ETFs and group rest as "Others"
        const top6 = summary.slice(0, 6);
        const othersAum = summary.slice(6).reduce((acc, s) => acc + (s.aum_usd || 0), 0);

        const labels = top6.map((s) => s.ticker);
        const values = top6.map((s) => s.aum_usd || 0);

        if (othersAum > 0) {
            labels.push("Others");
            values.push(othersAum);
        }

        return [
            {
                labels,
                values,
                type: "pie",
                hole: 0.4,
                textinfo: "label+percent",
                textposition: "outside",
                marker: {
                    colors: [
                        "#3b82f6", // IBIT - Blue
                        "#10b981", // FBTC - Green
                        "#f59e0b", // ARKB - Amber
                        "#8b5cf6", // BITB - Purple
                        "#ec4899", // HODL - Pink
                        "#06b6d4", // BRRR - Cyan
                        "#64748b", // Others - Slate
                    ],
                },
                hovertemplate: "<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
            },
        ];
    })();

    $: marketShareLayout = {
        title: {
            text: "Market Share by AUM",
            font: { color: $darkMode ? "#e2e8f0" : "#1e293b", size: 14 },
        },
        height: 320,
        margin: { t: 40, b: 20, l: 20, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: false,
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b", size: 11 },
    };

    // Flow-BTC Correlation Chart Data
    $: correlationChartData = [
        {
            x: dates,
            y: flowsAgg.flow_btc_corr_30d || [],
            name: "30d Correlation",
            type: "scatter",
            mode: "lines",
            line: { color: "#3b82f6", width: 2 },
            fill: "tozeroy",
            fillcolor: "rgba(59, 130, 246, 0.1)",
        },
        {
            x: dates,
            y: flowsAgg.flow_btc_corr_60d || [],
            name: "60d Correlation",
            type: "scatter",
            mode: "lines",
            line: { color: "#10b981", width: 1.5, dash: "dot" },
        },
    ];

    $: correlationChartLayout = {
        title: {
            text: "ETF Flows vs BTC Price Correlation",
            font: { color: $darkMode ? "#e2e8f0" : "#1e293b", size: 14 },
        },
        yaxis: {
            title: "Correlation",
            range: [-1, 1],
            gridcolor: $darkMode ? "#334155" : "#e2e8f0",
            zeroline: true,
            zerolinecolor: $darkMode ? "#475569" : "#94a3b8",
            zerolinewidth: 2,
        },
        height: 280,
        margin: { t: 40, b: 40, l: 50, r: 20 },
        paper_bgcolor: "transparent",
        plot_bgcolor: "transparent",
        showlegend: true,
        legend: { orientation: "h", y: -0.2, font: { size: 10 } },
        font: { color: $darkMode ? "#e2e8f0" : "#1e293b" },
        shapes: [
            // Reference lines at +0.5 and -0.5
            {
                type: "line",
                x0: dates[0],
                x1: dates[dates.length - 1],
                y0: 0.5,
                y1: 0.5,
                line: { color: "#10b981", width: 1, dash: "dash" },
            },
            {
                type: "line",
                x0: dates[0],
                x1: dates[dates.length - 1],
                y0: -0.5,
                y1: -0.5,
                line: { color: "#ef4444", width: 1, dash: "dash" },
            },
        ],
    };

    onMount(() => {
        if (!$etfData) {
            fetchEtfData();
        }
    });
</script>

<div class="etfs-tab">
    {#if $etfLoading}
        <div class="loading-overlay">
            <div class="spinner"></div>
            <p>Loading ETF Data...</p>
        </div>
    {:else if !$etfData}
        <div class="error-msg">
            <p>Failed to load ETF data. Is the backend pipeline running?</p>
            <button on:click={fetchEtfData}>Retry</button>
        </div>
    {:else}
        <!-- Summary Header -->
        <div class="tab-header" class:light={!$darkMode}>
            <div class="header-content">
                <h2>{t($currentTranslations, "etf_title")}</h2>
                <p class="description">
                    Track Spot Bitcoin ETF flows, AUM growth, and market
                    premiums.
                </p>
            </div>
            <div class="header-stats">
                <div class="stat-item main">
                    <span class="stat-label"
                        >{t($currentTranslations, "etf_aum")}</span
                    >
                    <span class="stat-value">${formatNumber(totalAUM)}</span>
                </div>
                {#each statsCards as card}
                    <div class="stat-item">
                        <span class="stat-label">{card.label}</span>
                        <span
                            class="stat-value"
                            class:pos={card.value > 0}
                            class:neg={card.value < 0}
                        >
                            {card.isCurrency ? "$" : ""}{formatNumber(
                                card.value,
                                card.isPct ? 2 : 0,
                            )}{card.isPct ? "%" : ""}
                        </span>
                    </div>
                {/each}
            </div>
        </div>

        <!-- Main Chart Section -->
        <div class="chart-card full-width" class:light={!$darkMode}>
            <div class="chart-header">
                <div class="header-controls">
                    <Dropdown
                        options={aggModes}
                        bind:value={aggChartMode}
                        darkMode={$darkMode}
                        small={true}
                    />
                    {#if aggChartMode === "roc"}
                        <Dropdown
                            options={rocMetricOptions}
                            bind:value={rocMetric}
                            darkMode={$darkMode}
                            small={true}
                        />
                        <Dropdown
                            options={normOptions}
                            bind:value={aggNormMode}
                            darkMode={$darkMode}
                            small={true}
                        />
                    {/if}
                    <Dropdown
                        options={maWindowOptions}
                        bind:value={maWindow}
                        darkMode={$darkMode}
                        small={true}
                    />
                    <div class="timeframe-toggles">
                        {#if aggChartMode === "net_flow"}
                            <button
                                class:active={chartTimeframe === "1D"}
                                on:click={() => (chartTimeframe = "1D")}
                                >1D</button
                            >
                        {/if}
                        <button
                            class:active={chartTimeframe === "7D"}
                            on:click={() => (chartTimeframe = "7D")}
                            >{aggChartMode === "roc"
                                ? "7D ROC"
                                : t($currentTranslations, "etf_weekly")}</button
                        >
                        <button
                            class:active={chartTimeframe === "30D"}
                            on:click={() => (chartTimeframe = "30D")}
                            >{aggChartMode === "roc"
                                ? "30D ROC"
                                : t(
                                      $currentTranslations,
                                      "etf_monthly",
                                  )}</button
                        >
                        <button
                            class:active={chartTimeframe === "90D"}
                            on:click={() => (chartTimeframe = "90D")}
                            >{aggChartMode === "roc"
                                ? "90D ROC"
                                : t(
                                      $currentTranslations,
                                      "etf_quarterly",
                                  )}</button
                        >
                        <button
                            class:active={chartTimeframe === "YOY"}
                            on:click={() => (chartTimeframe = "YOY")}
                            >{aggChartMode === "roc"
                                ? "YoY ROC"
                                : "YoY Flow"}</button
                        >
                    </div>
                </div>
                <div class="secondary-controls">
                    <label class="custom-checkbox">
                        <input type="checkbox" bind:checked={showMA} />
                        <span class="checkmark"></span>
                        <span class="label-text"
                            >{t($currentTranslations, "etf_ma")}</span
                        >
                    </label>
                    <label class="custom-checkbox">
                        <input type="checkbox" bind:checked={showBtcOverlay} />
                        <span class="checkmark"></span>
                        <span class="label-text"
                            >{t($currentTranslations, "etf_btc_overlay")}</span
                        >
                    </label>
                </div>
            </div>
            <Chart
                data={mainChartData}
                layout={mainChartLayout}
                darkMode={$darkMode}
            />
        </div>

        <div class="bottom-grid">
            <!-- Individual Ticker Section -->
            <div class="card ticker-section">
                <div class="card-header">
                    <div class="header-main">
                        <h3>
                            {t($currentTranslations, "etf_ticker")} Analysis
                        </h3>
                        <div class="ticker-mode-selector">
                            <button
                                class:active={tickerMetric === "flow"}
                                on:click={() => (tickerMetric = "flow")}
                            >
                                {t($currentTranslations, "etf_net_flows")}
                            </button>
                            <button
                                class:active={tickerMetric === "prem_disc"}
                                on:click={() => (tickerMetric = "prem_disc")}
                            >
                                {t($currentTranslations, "etf_prem_disc")}
                            </button>
                        </div>
                    </div>
                    <div class="ticker-controls">
                        <label class="custom-checkbox">
                            <input
                                type="checkbox"
                                checked={tickerMode === "aggregate"}
                                on:change={(e) =>
                                    (tickerMode = e.currentTarget.checked
                                        ? "aggregate"
                                        : "individual")}
                            />
                            <span class="checkmark"></span>
                            <span class="label-text"
                                >{t($currentTranslations, "etf_aggregate") ||
                                    "Aggregate"}</span
                            >
                        </label>

                        {#if tickerMetric === "prem_disc"}
                            <Dropdown
                                options={normOptions}
                                bind:value={normalizationMode}
                                darkMode={$darkMode}
                                small={true}
                            />
                            <Dropdown
                                options={pdSmoothTypeOptions}
                                bind:value={pdSmoothType}
                                darkMode={$darkMode}
                                small={true}
                            />
                            {#if pdSmoothType !== "raw"}
                                <Dropdown
                                    options={pdSmoothWindowOptions}
                                    bind:value={pdSmoothWindow}
                                    darkMode={$darkMode}
                                    small={true}
                                />
                            {/if}
                        {/if}

                        {#if tickerMode === "individual"}
                            <Dropdown
                                options={tickerOptions}
                                bind:value={selectedTicker}
                                darkMode={$darkMode}
                                small={true}
                            />
                        {/if}
                    </div>
                </div>
                <div class="ticker-chart-wrapper">
                    <Chart
                        data={tickerChartData}
                        layout={tickerChartLayout}
                        darkMode={$darkMode}
                    />
                </div>
            </div>

            <!-- Market Share Pie Chart -->
            <div class="card pie-chart-card">
                <Chart
                    data={marketShareData}
                    layout={marketShareLayout}
                    darkMode={$darkMode}
                />
            </div>
        </div>

        <!-- Second Row: Table + Correlation -->
        <div class="bottom-grid-2">
            <!-- Summary Table -->
            <div class="card table-card">
                <div class="card-header">
                    <h3>{t($currentTranslations, "etf_summary_all")}</h3>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>{t($currentTranslations, "etf_ticker")}</th>
                                <th class="text-right"
                                    >{t($currentTranslations, "etf_aum")}</th
                                >
                                <th class="text-right"
                                    >{t(
                                        $currentTranslations,
                                        "etf_prem_disc",
                                    )}</th
                                >
                                <th class="text-right"
                                    >{t($currentTranslations, "etf_nav")}</th
                                >
                            </tr>
                        </thead>
                        <tbody>
                            {#each summary as row}
                                <tr>
                                    <td>
                                        <div class="ticker-cell">
                                            <span class="ticker-badge"
                                                >{row.ticker}</span
                                            >
                                            <span class="provider"
                                                >{row.provider_name ||
                                                    row.issuer}</span
                                            >
                                        </div>
                                    </td>
                                    <td class="text-right"
                                        >${formatNumber(row.aum_usd)}</td
                                    >
                                    <td
                                        class="text-right"
                                        class:pos={row.premium_discount > 0}
                                        class:neg={row.premium_discount < 0}
                                        >{formatNumber(
                                            row.premium_discount,
                                            2,
                                        )}%</td
                                    >
                                    <td class="text-right"
                                        >${formatNumber(row.nav)}</td
                                    >
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Flow-BTC Correlation Chart -->
            <div class="card correlation-card">
                <Chart
                    data={correlationChartData}
                    layout={correlationChartLayout}
                    darkMode={$darkMode}
                />
                <div class="correlation-hint">
                    <span class="hint-text">High correlation = flows follow price | Low/negative = flows independent</span>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .etfs-tab {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        padding: 1rem;
        color: var(--text-color);
        min-height: 400px;
        position: relative;
    }

    .loading-overlay {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        height: 400px;
    }

    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(59, 130, 246, 0.1);
        border-top-color: #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* Dashboard Standard Styles */
    .tab-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }

    .header-content h2 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .header-content .description {
        margin: 4px 0 0 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    .header-stats {
        display: flex;
        gap: 20px;
    }

    .stat-item {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
    }

    .stat-item.main .stat-value {
        color: #3b82f6;
        font-size: 1.5rem;
    }

    .stat-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
    }

    .pos {
        color: #10b981;
    }
    .neg {
        color: #ef4444;
    }

    .chart-card {
        background: var(--card-bg);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .full-width {
        grid-column: 1 / -1;
    }

    .card {
        background: var(--card-bg);
        border-radius: 12px;
        border: 1px solid var(--border-color);
        padding: 20px;
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.25rem;
    }

    .card-header h3 {
        margin: 0;
        font-size: 1.125rem;
        font-weight: 600;
    }

    .bottom-grid {
        display: grid;
        grid-template-columns: 1.5fr 1fr;
        gap: 1.5rem;
    }

    .bottom-grid-2 {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-top: 1.5rem;
    }

    @media (max-width: 1024px) {
        .bottom-grid,
        .bottom-grid-2 {
            grid-template-columns: 1fr;
        }
    }

    .pie-chart-card {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .correlation-card {
        position: relative;
    }

    .correlation-hint {
        padding: 8px 12px;
        background: var(--bg-secondary);
        border-radius: 6px;
        margin-top: 8px;
    }

    .hint-text {
        font-size: 0.7rem;
        color: var(--text-muted);
        font-style: italic;
    }

    .table-wrapper {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th {
        text-align: left;
        padding: 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border-color);
        text-transform: uppercase;
    }

    td {
        padding: 1rem 0.75rem;
        border-bottom: 1px solid var(--border-color);
        font-size: 0.875rem;
    }

    .text-right {
        text-align: right;
    }

    .ticker-cell {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .ticker-badge {
        background: #3b82f620;
        color: #3b82f6;
        padding: 0.125rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 700;
        font-family: monospace;
        width: fit-content;
    }

    .provider {
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    :global(.dark) .chart-card,
    :global(.dark) .card {
        background: #0f172a;
        border-color: #1e293b;
    }

    :global(.dark) .ticker-badge {
        background: #3b82f630;
    }

    .timeframe-toggles {
        display: flex;
        gap: 0.5rem;
    }

    .timeframe-toggles button {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 0.35rem 0.75rem;
        border-radius: 0.375rem;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        color: var(--text-muted);
    }

    .timeframe-toggles button.active {
        background: #3b82f6;
        color: #f8fafc;
        border-color: #3b82f6;
    }

    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .header-controls {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
    }

    .secondary-controls {
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }

    /* Custom Checkbox Styling */
    .custom-checkbox {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        cursor: pointer;
        user-select: none;
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-secondary);
    }

    .custom-checkbox input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
        height: 0;
        width: 0;
    }

    .checkmark {
        height: 18px;
        width: 18px;
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        position: relative;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .custom-checkbox:hover input ~ .checkmark {
        border-color: #3b82f6;
        background-color: rgba(59, 130, 246, 0.1);
    }

    .custom-checkbox input:checked ~ .checkmark {
        background-color: #3b82f6;
        border-color: #3b82f6;
    }

    .checkmark:after {
        content: "";
        position: absolute;
        display: none;
        left: 6px;
        top: 2px;
        width: 4px;
        height: 8px;
        border: solid white;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
    }

    .custom-checkbox input:checked ~ .checkmark:after {
        display: block;
    }

    .label-text {
        transition: color 0.2s;
    }

    .custom-checkbox input:checked ~ .label-text {
        color: var(--text-primary);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .header-main {
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .ticker-mode-selector {
        display: flex;
        background: var(--bg-secondary);
        padding: 2px;
        border-radius: 6px;
        border: 1px solid var(--border-color);
    }

    .ticker-mode-selector button {
        padding: 4px 12px;
        font-size: 0.75rem;
        background: transparent;
        border: none;
        color: var(--text-muted);
        cursor: pointer;
        border-radius: 4px;
        transition: all 0.2s;
    }

    .ticker-mode-selector button.active {
        background: var(--card-bg);
        color: var(--text-color);
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }

    .ticker-controls {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .ticker-chart-wrapper {
        min-height: 380px;
    }
</style>
