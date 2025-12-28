<script>
  import { onMount } from "svelte";
  import {
    fetchData,
    dashboardData,
    latestStats,
    isLoading,
    error,
  } from "./stores/dataStore";
  import StatsCard from "./lib/components/StatsCard.svelte";
  import Chart from "./lib/components/Chart.svelte";
  import LightweightChart from "./lib/components/LightweightChart.svelte";
  import SignalBadge from "./lib/components/SignalBadge.svelte";
  import TimeRangeSelector from "./lib/components/TimeRangeSelector.svelte";

  // Tab Components
  import {
    DashboardTab,
    GlobalFlowsCbTab,
    GlobalM2Tab,
    UsSystemTab,
    RiskModelTab,
    BtcAnalysisTab,
    BtcQuantV2Tab,
  } from "./lib/tabs";

  // Global Settings Store
  import {
    darkMode,
    language,
    currentTranslations,
    toggleDarkMode,
    toggleLanguage,
    initSettings,
    t as translate,
  } from "./stores/settingsStore";

  // Initialize from localStorage on mount
  onMount(() => {
    initSettings();
    loadOptimizedParams();
  });

  async function loadOptimizedParams() {
    try {
      const response = await fetch("/regime_params.json");
      if (response.ok) {
        const params = await response.json();
        if (params.recommended_offset_days !== undefined) {
          regimeLag = params.recommended_offset_days;
          console.log(
            `[Optimized] Loaded regimeLag = ${regimeLag} from regime_params.json`,
          );
        }
      }
    } catch (e) {
      console.warn("Could not load optimized regime params, using default.", e);
    }
  }

  function applyTheme() {
    if (typeof document !== "undefined") {
      document.documentElement.setAttribute(
        "data-theme",
        darkMode ? "dark" : "light",
      );
    }
  }

  // Individual time range state for each chart section
  let gliRange = "ALL";
  let fedRange = "ALL";
  let ecbRange = "ALL";
  let bojRange = "ALL";
  let boeRange = "ALL";
  let pbocRange = "ALL";
  let bocRange = "ALL",
    rbaRange = "ALL",
    snbRange = "ALL",
    bokRange = "ALL";
  let rbiRange = "ALL",
    cbrRange = "ALL",
    bcbRange = "ALL",
    rbnzRange = "ALL",
    srRange = "ALL",
    bnmRange = "ALL";
  let netLiqRangeDashboard = "ALL";
  let netLiqRange = "ALL";
  let cliRangeDashboard = "ALL";
  let cliCompRangeDashboard = "ALL";
  let cliRange = "ALL";
  let impulseRange = "ALL";
  let btcRange = "ALL";
  let m2Range = "ALL";
  let vixRange = "ALL";
  let spreadRange = "ALL";
  let hyRange = "ALL",
    igRange = "ALL",
    nfciCreditRange = "ALL",
    nfciRiskRange = "ALL",
    nfciRange = "ALL",
    lendingRange = "ALL",
    reservesRange = "ALL",
    repoStressRange = "ALL",
    tgaRange = "ALL",
    rrpRange = "ALL",
    cbBreadthRange = "ALL",
    cbConcentrationRange = "ALL",
    cbRange = "ALL";

  // Individual M2 time ranges
  let usM2Range = "ALL",
    euM2Range = "ALL",
    cnM2Range = "ALL",
    jpM2Range = "ALL",
    ukM2Range = "ALL";
  let caM2Range = "ALL",
    auM2Range = "ALL",
    inM2Range = "ALL",
    chM2Range = "ALL",
    ruM2Range = "ALL";
  let brM2Range = "ALL",
    krM2Range = "ALL",
    mxM2Range = "ALL",
    myM2Range = "ALL";

  // GLI FX mode: false = Spot USD, true = Constant FX (2019-12-31)

  // GLI FX mode: false = Spot USD, true = Constant FX (2019-12-31)
  let gliShowConstantFx = false;

  // Helper to get cutoff date based on range
  const getCutoffDate = (range) => {
    if (range === "ALL") return null;
    const now = new Date();
    switch (range) {
      case "1M":
        return new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
      case "3M":
        return new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
      case "6M":
        return new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
      case "1Y":
        return new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
      case "3Y":
        return new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
      case "5Y":
        return new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());
      default:
        return null;
    }
  };

  // Filter dates array and get valid indices for Plotly charts
  const getFilteredIndices = (dates, range) => {
    if (!dates || !Array.isArray(dates) || range === "ALL") {
      return dates ? dates.map((_, i) => i) : [];
    }
    const cutoff = getCutoffDate(range);
    if (!cutoff) return dates.map((_, i) => i);

    return dates.reduce((acc, d, i) => {
      const date = new Date(d);
      if (date >= cutoff) acc.push(i);
      return acc;
    }, []);
  };

  // Helper to filter Plotly trace data
  const filterPlotlyData = (traceArray, dates, range) => {
    if (!traceArray || !dates || !dates.length) return traceArray;

    let indices;
    if (range === "ALL") {
      // Auto-trim: Find the first index where ANY trace has non-zero/non-null data
      let firstValidIdx = -1;
      for (let i = 0; i < dates.length; i++) {
        const hasData = traceArray.some((trace) => {
          const val = trace.y ? trace.y[i] : undefined;
          return val !== null && val !== undefined && val !== 0;
        });
        if (hasData) {
          firstValidIdx = i;
          break;
        }
      }
      if (firstValidIdx === -1) return traceArray; // No valid data found at all
      indices = dates.slice(firstValidIdx).map((_, i) => i + firstValidIdx);
    } else {
      indices = getFilteredIndices(dates, range);
    }

    return traceArray.map((trace) => ({
      ...trace,
      x: trace.x ? indices.map((i) => trace.x[i]) : [],
      y: trace.y ? indices.map((i) => trace.y[i]) : [],
    }));
  };

  const formatTV = (dates, values) => {
    if (!dates || !values || !Array.isArray(dates)) return [];
    const points = [];
    for (let i = 0; i < dates.length; i++) {
      const val = values[i];
      if (val === null || val === undefined || isNaN(val) || val <= 0) continue;
      const dateStr = dates[i]; // Backend already provides YYYY-MM-DD
      if (!dateStr || typeof dateStr !== "string") continue;
      points.push({ time: dateStr, value: val });
    }
    // High-performance chronological sort
    return points.sort((a, b) => (a.time > b.time ? 1 : -1));
  };

  // Create LightweightChart series config with time range filtering
  const formatLC = (dates, values, range, name, color, type = "line") => {
    if (!dates || !values) return [];

    // Get cutoff date for filtering
    const cutoff = getCutoffDate(range);

    const points = [];
    for (let i = 0; i < dates.length; i++) {
      const val = values[i];
      if (val === null || val === undefined || isNaN(val)) continue;
      const dateStr = dates[i];
      if (!dateStr || typeof dateStr !== "string") continue;

      // Apply time range filter
      if (cutoff) {
        const pointDate = new Date(dateStr);
        if (pointDate < cutoff) continue;
      }

      points.push({ time: dateStr, value: val });
    }

    const sortedPoints = points.sort((a, b) => (a.time > b.time ? 1 : -1));

    return [
      {
        name,
        type,
        color,
        data: sortedPoints,
        width: 2,
      },
    ];
  };

  let currentTab = "Dashboard";
  let selectedBtcModel = "macro"; // "macro" or "adoption"
  let selectedLagWindow = "7d"; // "7d" | "14d" | "30d"

  onMount(() => {
    fetchData();
  });

  const setTab = (tab) => {
    currentTab = tab;
  };

  $: activeBtcModel = $dashboardData.btc?.models?.[selectedBtcModel] || {
    fair_value: [],
    upper_1sd: [],
    lower_1sd: [],
    upper_2sd: [],
    lower_2sd: [],
    deviation_pct: [],
    deviation_zscore: [],
  };

  // --- Chart Data Definitions (filtered by globalTimeRange) ---
  // Use gliDataSource based on toggle (Spot USD vs Constant FX)
  $: gliDataSource = gliShowConstantFx
    ? $dashboardData.gli.constant_fx
    : $dashboardData.gli.total;
  $: gliDataRaw = [
    {
      x: $dashboardData.dates,
      y: gliDataSource,
      name: gliShowConstantFx ? "GLI Constant-FX" : "GLI Total (Spot USD)",
      type: "scatter",
      mode: "lines",
      line: {
        color: gliShowConstantFx ? "#10b981" : "#6366f1",
        width: 3,
        shape: "spline",
      },
    },
  ];
  $: gliData = filterPlotlyData(gliDataRaw, $dashboardData.dates, gliRange);

  $: fedDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.fed,
      name: "Fed Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
    },
  ];
  $: fedData = filterPlotlyData(fedDataRaw, $dashboardData.dates, fedRange);

  $: ecbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.ecb,
      name: "ECB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
    },
  ];
  $: ecbData = filterPlotlyData(ecbDataRaw, $dashboardData.dates, ecbRange);

  $: bojDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boj,
      name: "BoJ Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
    },
  ];
  $: bojData = filterPlotlyData(bojDataRaw, $dashboardData.dates, bojRange);

  $: boeDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boe,
      name: "BoE Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
    },
  ];
  $: boeData = filterPlotlyData(boeDataRaw, $dashboardData.dates, boeRange);

  $: pbocDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.pboc,
      name: "PBoC Assets (M2Proxy)",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
    },
  ];
  $: pbocData = filterPlotlyData(pbocDataRaw, $dashboardData.dates, pbocRange);

  $: bocDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.boc,
      name: "BoC Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#34d399", width: 3, shape: "spline" },
    },
  ];
  $: bocData = filterPlotlyData(bocDataRaw, $dashboardData.dates, bocRange);

  let btcRocPeriod = 21; // Default 1 Month (21 trading days)
  let btcLag = 0; // Default 0 lag
  let regimeLag = 42; // Optimized offset from train_regime_offset.py (was 72)
  let normalizeImpulse = true; // Always Normalized (Z-Score)
  let showComposite = false; // Toggle for Composite Aggregate Signal
  let optimalLagLabel = "N/A"; // Display string for UI

  function calculateCorrelation(xArray, yArray) {
    if (
      !xArray ||
      !yArray ||
      xArray.length !== yArray.length ||
      xArray.length < 2
    )
      return 0;

    let sumX = 0,
      sumY = 0,
      sumXY = 0,
      sumX2 = 0,
      sumY2 = 0,
      n = 0;
    for (let i = 0; i < xArray.length; i++) {
      const x = xArray[i];
      const y = yArray[i];
      if (x !== null && x !== undefined && y !== null && y !== undefined) {
        sumX += x;
        sumY += y;
        sumXY += x * y;
        sumX2 += x * x;
        sumY2 += y * y;
        n++;
      }
    }
    if (n < 2) return 0;

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt(
      (n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY),
    );
    return denominator === 0 ? 0 : numerator / denominator;
  }

  function findOptimalLag(
    dates,
    signalValues,
    btcRocValues,
    minLag = -15,
    maxLag = 120,
  ) {
    // We want to find shift 'k' for signalValues that maximizes correlation with btcRocValues.
    // btcRocValues stays fixed (associated with 'dates').
    // signalValues[i] is at dates[i].
    // shiftedSignal[i] = signalValues[i - k] ... wait.
    // logic: shiftData(dates, values, k) returns aligned arrays.
    // We can use shiftData inside loop.

    let bestLag = 0;
    let maxCorr = -1;

    // Optimization: btcRoc is sparse? No, it's mapped to dates.
    // But btcRoc might have nulls at start.

    // Create a Map for BTC ROC to speed up? array access is O(1).
    // Dates align by index i.

    for (let k = minLag; k <= maxLag; k += 3) {
      // Step 3 days for speed
      // Simplified shift logic for correlation only (no need for dates array construction)
      // Shift +k: signal[i] moves to dates[i+k].
      // So we compare signal[i] vs btcRoc[i+k].

      const x = [];
      const y = [];

      for (let i = 0; i < signalValues.length; i++) {
        let j = i + k; // shifted index
        if (j >= 0 && j < btcRocValues.length) {
          const sig = signalValues[i];
          const roc = btcRocValues[j];
          if (sig != null && roc != null) {
            x.push(sig);
            y.push(roc);
          }
        }
      }

      const r = calculateCorrelation(x, y);
      if (r > maxCorr) {
        maxCorr = r;
        bestLag = k;
      }
    }
    return { lag: bestLag, corr: maxCorr };
  }

  function calculateZScore(values) {
    if (!values || values.length === 0) return [];
    const valid = values.filter((v) => v !== null && v !== undefined);
    if (valid.length < 2) return values;

    const mean = valid.reduce((a, b) => a + b, 0) / valid.length;
    const variance =
      valid.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / valid.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return values.map(() => 0);

    return values.map((v) =>
      v === null || v === undefined ? null : (v - mean) / stdDev,
    );
  }

  function calculateBtcRoc(prices, dates, period, lag = 0) {
    if (!prices || !dates || prices.length !== dates.length) return [];

    // Valid period check
    if (period <= 0) return [];

    const rocData = [];

    // Lag: if lag > 0, we behave as if the ROC happened 'lag' days later/earlier?
    // In this specific implementation for generic use:
    // If we want to align price with lagged signal, we might need lag.
    // However, the caller currently uses lag=0.
    // We will just return the raw ROC aligned with dates[i].

    for (let i = period; i < prices.length; i++) {
      const current = prices[i];
      const past = prices[i - period];

      if (past && past !== 0) {
        const roc = ((current - past) / past) * 100;

        // Align with Date[i]
        // If we supported shifting here, we'd adjust the date index.
        // For now, strict calendar alignment.
        rocData.push({ x: dates[i], y: roc });
      }
    }
    return rocData;
  }

  function calculateHistoricalRegimes(dates, gli, netliq) {
    if (!dates || !gli || !netliq) return [];

    const shapes = [];
    let currentRegime = null;
    let startIdx = 0;

    for (let i = 0; i < dates.length; i++) {
      const g = gli[i];
      const n = netliq[i];
      let r = "neutral";

      if (g > 0 && n > 0) r = "bullish";
      else if (g < 0 && n < 0) r = "bearish";

      if (r !== currentRegime) {
        if (currentRegime !== null) {
          shapes.push({
            type: "rect",
            xref: "x",
            yref: "paper",
            x0: dates[startIdx],
            x1: dates[i],
            y0: 0,
            y1: 1,
            fillcolor:
              currentRegime === "bullish"
                ? "rgba(16, 185, 129, 0.08)"
                : currentRegime === "bearish"
                  ? "rgba(239, 68, 68, 0.08)"
                  : "rgba(148, 163, 184, 0.03)",
            line: { width: 0 },
            layer: "below",
          });
        }
        currentRegime = r;
        startIdx = i;
      }
    }
    // Final shape
    if (currentRegime !== null) {
      shapes.push({
        type: "rect",
        xref: "x",
        yref: "paper",
        x0: dates[startIdx],
        x1: dates[dates.length - 1],
        y0: 0,
        y1: 1,
        fillcolor:
          currentRegime === "bullish"
            ? "rgba(16, 185, 129, 0.08)"
            : currentRegime === "bearish"
              ? "rgba(239, 68, 68, 0.08)"
              : "rgba(148, 163, 184, 0.03)",
        line: { width: 0 },
        layer: "below",
      });
    }
    return shapes;
  }

  // Helper function for regime chart data (extracted for reactivity)
  function buildRegimeLCData(dates, prices, regimeScore, offset, lastDate) {
    const bgData = [];
    const btcData = [];

    // Helper to add days to YYYY-MM-DD
    const addDays = (dateStr, days) => {
      const d = new Date(dateStr);
      d.setDate(d.getDate() + days);
      return d.toISOString().split("T")[0];
    };

    // Helper: Convert score (0-100) to gradient color
    const scoreToColor = (score) => {
      if (score === null || score === undefined) return null;

      const deviation = (score - 50) / 50; // -1 to +1
      const absDeviation = Math.abs(deviation);
      const alpha = 0.08 + absDeviation * 0.18; // 0.08 to 0.26 opacity

      if (deviation > 0.02) {
        return `rgba(16, 185, 129, ${alpha.toFixed(2)})`; // Green
      } else if (deviation < -0.02) {
        return `rgba(239, 68, 68, ${alpha.toFixed(2)})`; // Red
      } else {
        return `rgba(148, 163, 184, 0.08)`; // Neutral grey
      }
    };

    // BTC Price Data
    for (let i = 0; i < dates.length; i++) {
      if (prices[i] !== undefined && prices[i] !== null) {
        btcData.push({ time: dates[i], value: prices[i] });
      }
    }

    // Regime Background Data - Paint for ALL dates with score, not just BTC dates
    for (let i = 0; i < regimeScore.length && i < dates.length; i++) {
      const score = regimeScore[i];
      const color = scoreToColor(score);

      if (color) {
        // Map signal date to projected date with offset
        let targetDate;
        const targetIdx = i + offset;

        if (targetIdx < dates.length) {
          targetDate = dates[targetIdx];
        } else if (lastDate) {
          const daysToAdd = targetIdx - (dates.length - 1);
          targetDate = addDays(lastDate, daysToAdd);
        }

        if (targetDate) {
          bgData.push({ time: targetDate, value: 1, color });
        }
      }
    }

    return [
      {
        name: "Regime",
        type: "histogram",
        data: bgData,
        color: "transparent",
        options: {
          priceScaleId: "left",
          priceFormat: { type: "custom", formatter: () => "" },
          scaleMargins: { top: 0, bottom: 0 },
        },
      },
      {
        name: "BTC Price",
        type: "area",
        data: btcData,
        color: "#94a3b8",
        topColor: "rgba(148, 163, 184, 0.4)",
        bottomColor: "rgba(148, 163, 184, 0.01)",
        width: 2,
      },
    ];
  }

  // Reactive regime chart data - ALL LOGIC INLINE for proper regimeLag reactivity
  $: regimeLCData = (() => {
    // Explicitly reference regimeLag at the TOP for Svelte to track it
    const currentOffset = regimeLag;

    if (!$dashboardData.dates || !$dashboardData.btc?.price) return [];

    const dates = $dashboardData.dates;
    const prices = $dashboardData.btc.price;
    const regimeScore = $dashboardData.macro_regime?.score || [];
    const lastDate = dates[dates.length - 1];

    const bgData = [];
    const btcData = [];

    // Helper to add days to YYYY-MM-DD
    const addDays = (dateStr, days) => {
      const d = new Date(dateStr);
      d.setDate(d.getDate() + days);
      return d.toISOString().split("T")[0];
    };

    // Helper: Convert score (0-100) to gradient color
    const scoreToColor = (score) => {
      // Use Number() to catch empty strings, null, undefined, etc.
      const s = Number(score);
      if (isNaN(s)) return "rgba(148, 163, 184, 0.05)";

      const deviation = (s - 50) / 50; // -1 to +1
      const absDeviation = Math.abs(deviation);
      const alpha = 0.08 + absDeviation * 0.18; // 0.08 to 0.26 opacity

      if (deviation > 0.02) {
        return `rgba(16, 185, 129, ${alpha.toFixed(2)})`; // Green
      } else if (deviation < -0.02) {
        return `rgba(239, 68, 68, ${alpha.toFixed(2)})`; // Red
      } else {
        return `rgba(148, 163, 184, 0.08)`; // Neutral grey
      }
    };

    // BTC Price Data
    for (let i = 0; i < dates.length; i++) {
      if (prices[i] !== undefined && prices[i] !== null) {
        btcData.push({ time: dates[i], value: prices[i] });
      }
    }

    // Regime Background Data with offset
    // Iterate over the FULL date range (including extended future dates)
    // For each target date, look BACK by offset to find the source signal
    const totalDates = dates.length + currentOffset;

    for (let targetIdx = 0; targetIdx < totalDates; targetIdx++) {
      // Calculate target date
      let targetDate;
      if (targetIdx < dates.length) {
        targetDate = dates[targetIdx];
      } else if (lastDate) {
        const daysToAdd = targetIdx - (dates.length - 1);
        targetDate = addDays(lastDate, daysToAdd);
      }

      // Calculate source index (look back by offset)
      const sourceIdx = targetIdx - currentOffset;

      // Only paint if source index is valid (within score data range)
      if (sourceIdx >= 0 && sourceIdx < regimeScore.length) {
        const score = regimeScore[sourceIdx];
        const color = scoreToColor(score);

        if (color && targetDate) {
          bgData.push({ time: targetDate, value: 1, color });
        }
      }
    }

    return [
      {
        name: "Regime",
        type: "histogram",
        data: bgData,
        color: "transparent",
        options: {
          priceScaleId: "left",
          priceFormat: { type: "custom", formatter: () => "" },
          scaleMargins: { top: 0, bottom: 0 },
        },
      },
      {
        name: "BTC Price",
        type: "area",
        data: btcData,
        color: "#94a3b8",
        topColor: "rgba(148, 163, 184, 0.4)",
        bottomColor: "rgba(148, 163, 184, 0.01)",
        width: 2,
      },
    ];
  })();

  // CB Breadth Chart Data (% of CBs expanding)
  $: cbBreadthData = (() => {
    if (!$dashboardData.dates || !$dashboardData.macro_regime?.cb_diffusion_13w)
      return [];

    const dates = $dashboardData.dates;
    const diffusion = $dashboardData.macro_regime.cb_diffusion_13w;
    const indices = getFilteredIndices(dates, cbBreadthRange);

    const data = indices
      .map((i) => {
        const val = diffusion[i];
        if (val === null || val === undefined) return null;
        return { time: dates[i], value: val * 100 };
      })
      .filter((p) => p !== null);

    return [
      {
        name: "CB Breadth (%)",
        type: "area",
        data: data,
        color: "#3b82f6",
        topColor: "rgba(59, 130, 246, 0.3)",
        bottomColor: "rgba(59, 130, 246, 0.01)",
        width: 2,
      },
    ];
  })();

  // CB Concentration Chart Data (HHI)
  $: cbConcentrationData = (() => {
    if (!$dashboardData.dates || !$dashboardData.macro_regime?.cb_hhi_13w)
      return [];

    const dates = $dashboardData.dates;
    const hhi = $dashboardData.macro_regime.cb_hhi_13w;
    const indices = getFilteredIndices(dates, cbConcentrationRange);

    const data = indices
      .map((i) => {
        const val = hhi[i];
        if (val === null || val === undefined) return null;
        return { time: dates[i], value: val };
      })
      .filter((p) => p !== null);

    return [
      {
        name: "CB Concentration (HHI)",
        type: "area",
        data: data,
        color: "#f59e0b",
        topColor: "rgba(245, 158, 11, 0.3)",
        bottomColor: "rgba(245, 158, 11, 0.01)",
        width: 2,
      },
    ];
  })();

  // --- Signal Lagging Logic ---
  // We want to shift GLI, NetLiq, and CLI traces by 'btcLag' (renamed conceptually to 'signalOffset') days.
  // If Lag > 0, we shift signals FORWARD (Right) to see if they lead Price.
  // Ideally, if Signal(t) predicts Price(t+lag), we shift Signal(t) to t+lag.

  function shiftData(dates, values, lagDays) {
    if (!dates || !values || dates.length !== values.length)
      return { x: dates || [], y: values || [] };
    if (lagDays === 0) return { x: dates, y: values };

    // Since dates are strings YYYY-MM-DD, we assume index shifting is sufficient if data is daily.
    // 1 index approx 1 day (trading day).
    // Shift Right (Positive Lag): Prepend nulls/cut start, or simply shift the x-axis?
    // Easiest is to keep Y values and SHIFT X array.
    // If we shift signal to the right, Signal[i] happens at Date[i+lag].

    // Actually, easier way for Plotly:
    // If we want to move line to the RIGHT (+), we add days to the date object.
    // But we have a discrete date list.
    // Let's use index shifting.

    const shiftedX = [];
    const shiftedY = [];

    for (let i = 0; i < values.length; i++) {
      const targetIdx = i + lagDays;
      if (targetIdx >= 0 && targetIdx < dates.length) {
        shiftedX.push(dates[targetIdx]);
        shiftedY.push(values[i]);
      }
    }
    return { x: shiftedX, y: shiftedY };
  }

  // --- Impulse Chart Data (Signals + BTC ROC) ---
  $: btcRocTrace = (() => {
    if (!$dashboardData.btc || !$dashboardData.btc.price) return null;
    const prices = $dashboardData.btc.price || [];
    const dates = $dashboardData.dates;
    if (!prices.length) return null;

    // Fixed BTC ROC (No Lag on BTC itself, it is the anchor)
    const computed = calculateBtcRoc(prices, dates, btcRocPeriod, 0);
    const yRaw = computed.map((p) => p.y);
    // Force Z-Score if Composite is ON (to match scale) or if Normalized is ON
    const useZ = normalizeImpulse || showComposite;
    const yFinal = useZ ? calculateZScore(yRaw) : yRaw;

    return {
      x: computed.map((p) => p.x),
      y: yFinal,
      name: `BTC ROC (${btcRocPeriod}d)${useZ ? " [Z]" : ""}`,
      type: "scatter",
      mode: "lines",
      line: { color: "#94a3b8", width: 2, dash: "solid" },
      yaxis: useZ ? "y" : "y2",
      opacity: 0.8,
    };
  })();

  // Composite Signal Calculation & Lag Finder
  $: compositeData = (() => {
    if (!showComposite || !$dashboardData.flow_metrics) return null;

    // Get Z-Scores of components
    const g = calculateZScore(
      $dashboardData.flow_metrics.gli_impulse_13w || [],
    );
    const n = calculateZScore(
      $dashboardData.flow_metrics.net_liquidity_impulse_13w || [],
    );
    const c = calculateZScore(
      $dashboardData.flow_metrics.cli_momentum_4w || [],
    );

    if (!g.length) return null;

    // Average Z-Score
    const comp = g.map((val, i) => {
      if (val == null || n[i] == null || c[i] == null) return null;
      return (val + n[i] + c[i]) / 3;
    });

    // Run Correlation Analysis
    const prices = $dashboardData.btc?.price || [];
    const fullRoc = prices.map((curr, i) => {
      if (i < btcRocPeriod) return null;
      const past = prices[i - btcRocPeriod];
      if (!past) return null;
      return ((curr - past) / past) * 100;
    });

    const best = findOptimalLag($dashboardData.dates, comp, fullRoc, 0, 120); // Scan 0 to 120 days positive lag
    optimalLagLabel = `Best Offset: +${best.lag}d (Corr: ${best.corr.toFixed(2)})`;

    return comp;
  })();

  $: compositeShifted = showComposite
    ? shiftData($dashboardData.dates, compositeData, btcLag)
    : null;

  $: gliImpulseShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.gli_impulse_13w,
    btcLag,
  );
  $: netLiqImpulseShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.net_liquidity_impulse_13w,
    btcLag,
  );
  $: cliMomentumShifted = shiftData(
    $dashboardData.dates,
    $dashboardData.flow_metrics?.cli_momentum_4w,
    btcLag,
  );

  $: gliY = normalizeImpulse
    ? calculateZScore(gliImpulseShifted.y)
    : gliImpulseShifted.y;
  $: netLiqY = normalizeImpulse
    ? calculateZScore(netLiqImpulseShifted.y)
    : netLiqImpulseShifted.y;
  $: cliY = normalizeImpulse
    ? calculateZScore(cliMomentumShifted.y)
    : cliMomentumShifted.y;

  $: impulseDataRaw = showComposite
    ? [
        {
          x: compositeShifted?.x || [],
          y: compositeShifted?.y || [],
          name:
            "Composite Liquidity (Z)" + (btcLag !== 0 ? ` [${btcLag}d]` : ""),
          type: "scatter",
          mode: "lines",
          line: { color: "#8b5cf6", width: 3, shape: "spline" }, // Violet
        },
        ...(btcRocTrace ? [btcRocTrace] : []),
      ]
    : [
        {
          x: gliImpulseShifted.x,
          y: gliY,
          name:
            "GLI Impulse (13W)" +
            (btcLag !== 0 ? ` [${btcLag > 0 ? "+" : ""}${btcLag}d]` : ""),
          type: "scatter",
          mode: "lines",
          line: { color: "#3b82f6", width: 2, shape: "spline" },
        },
        {
          x: netLiqImpulseShifted.x,
          y: netLiqY,
          name: "NetLiq Impulse (13W)",
          type: "scatter",
          mode: "lines",
          line: { color: "#10b981", width: 2, shape: "spline" },
        },
        {
          x: cliMomentumShifted.x,
          y: cliY,
          name: "CLI Momentum (4W)",
          type: "scatter",
          mode: "lines",
          line: { color: "#f59e0b", width: 2, shape: "spline" },
        },
        ...(btcRocTrace ? [btcRocTrace] : []),
      ];

  $: impulseData = filterPlotlyData(
    impulseDataRaw,
    $dashboardData.dates,
    impulseRange,
  );

  $: impulseLayout = {
    yaxis: {
      title:
        normalizeImpulse || showComposite
          ? "Z-Score (σ)"
          : "Impulse ($ Trillion)",
      gridcolor: darkMode ? "#334155" : "#e2e8f0",
    },
    yaxis2: {
      title: "BTC ROC (%)",
      overlaying: "y",
      side: "right",
      showgrid: false,
      visible: !(normalizeImpulse || showComposite),
    },
    margin: { t: 30, b: 30, l: 50, r: 50 },
    legend: { orientation: "h", y: 1.1 },
  };

  // Liquidity Score Logic (0-100) - Now uses backend multi-factor score
  $: liquidityScore = (() => {
    const macroRegime = $dashboardData.macro_regime;
    if (!macroRegime || !macroRegime.score || macroRegime.score.length === 0)
      return 50;

    // Get the latest score from the backend
    const latest = macroRegime.score[macroRegime.score.length - 1];
    return latest !== null && latest !== undefined ? latest : 50;
  })();

  // Regime diagnostic values (latest z-scores for display)
  $: regimeDiagnostics = (() => {
    const mr = $dashboardData.macro_regime;
    if (!mr) return { liquidity_z: 0, credit_z: 0, brakes_z: 0, total_z: 0 };

    const getLatest = (arr) => {
      if (!arr || arr.length === 0) return 0;
      const val = arr[arr.length - 1];
      return val !== null && val !== undefined ? val : 0;
    };

    return {
      liquidity_z: getLatest(mr.liquidity_z),
      credit_z: getLatest(mr.credit_z),
      brakes_z: getLatest(mr.brakes_z),
      total_z: getLatest(mr.total_z),
    };
  })();

  // Macro Regime Logic - Now uses backend multi-factor regime_code
  $: currentRegimeId = (() => {
    const macroRegime = $dashboardData.macro_regime;
    if (
      !macroRegime ||
      !macroRegime.regime_code ||
      macroRegime.regime_code.length === 0
    )
      return "neutral";

    const lastCode =
      macroRegime.regime_code[macroRegime.regime_code.length - 1];

    // regime_code: 1 = expansion, -1 = contraction, 0 = neutral
    if (lastCode === 1) return "bullish";
    if (lastCode === -1) return "bearish";
    return "neutral";
  })();

  $: currentRegime = (() => {
    const isEs = $language === "es";
    switch (currentRegimeId) {
      case "bullish":
        return {
          name: $currentTranslations.regime_bullish,
          emoji: "🐂",
          color: "bullish",
          desc: isEs
            ? "Expansión Sincronizada: Tanto la liquidez Global como la de EE.UU. están expandiéndose."
            : "Synchronized Expansion: Both Global and US liquidity are expanding.",
          details: isEs
            ? "Entorno favorable para activos de riesgo."
            : "Favorable environment for risk assets.",
        };
      case "bearish":
        return {
          name: $currentTranslations.regime_bearish,
          emoji: "🐻",
          color: "bearish",
          desc: isEs
            ? "Contracción Sincronizada: Tanto la liquidez Global como la de EE.UU. se están contrayendo."
            : "Synchronized Contraction: Both Global and US liquidity are contracting.",
          details: isEs
            ? "Entorno defensivo/adverso para activos de riesgo."
            : "Defensive/Headwind environment for risk assets.",
        };
      case "neutral":
      default:
        return {
          name: $currentTranslations.regime_neutral,
          emoji: "⚖️",
          color: "neutral",
          desc: isEs
            ? "Régimen Mixto/Divergente: Señales contradictorias entre liquidez Global y doméstica."
            : "Mixed/Divergent Regime: Conflicting signals between Global and domestic liquidity.",
          details: isEs
            ? "Comportamiento lateral o errático esperado."
            : "Choppy or sideways price action expected.",
        };
    }
  })();

  $: rbaDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rba,
      name: "RBA Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fbbf24", width: 3, shape: "spline" },
    },
  ];
  $: rbaData = filterPlotlyData(rbaDataRaw, $dashboardData.dates, rbaRange);

  $: snbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.snb,
      name: "SNB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#f87171", width: 3, shape: "spline" },
    },
  ];
  $: snbData = filterPlotlyData(snbDataRaw, $dashboardData.dates, snbRange);

  $: bokDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bok,
      name: "BoK Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#60a5fa", width: 3, shape: "spline" },
    },
  ];
  $: bokData = filterPlotlyData(bokDataRaw, $dashboardData.dates, bokRange);

  $: rbiDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rbi,
      name: "RBI Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#a78bfa", width: 3, shape: "spline" },
    },
  ];
  $: rbiData = filterPlotlyData(rbiDataRaw, $dashboardData.dates, rbiRange);

  $: cbrDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.cbr,
      name: "CBR Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fb7185", width: 3, shape: "spline" },
    },
  ];
  $: cbrData = filterPlotlyData(cbrDataRaw, $dashboardData.dates, cbrRange);

  $: bcbDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bcb,
      name: "BCB Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#4ade80", width: 3, shape: "spline" },
    },
  ];
  $: bcbData = filterPlotlyData(bcbDataRaw, $dashboardData.dates, bcbRange);

  $: rbnzDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.rbnz,
      name: "RBNZ Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#22d3ee", width: 3, shape: "spline" },
    },
  ];
  $: rbnzData = filterPlotlyData(rbnzDataRaw, $dashboardData.dates, rbnzRange);

  $: srDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.sr,
      name: "Riksbank Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#818cf8", width: 3, shape: "spline" },
    },
  ];
  $: srData = filterPlotlyData(srDataRaw, $dashboardData.dates, srRange);

  $: bnmDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.bnm,
      name: "BNM Assets",
      type: "scatter",
      mode: "lines",
      line: { color: "#fb923c", width: 3, shape: "spline" },
    },
  ];
  $: bnmData = filterPlotlyData(bnmDataRaw, $dashboardData.dates, bnmRange);

  $: netLiqDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq,
      name: "US Net Liquidity",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
    },
  ];
  $: netLiqData = filterPlotlyData(
    netLiqDataRaw,
    $dashboardData.dates,
    netLiqRange,
  );
  $: netLiqDataDashboard = filterPlotlyData(
    netLiqDataRaw,
    $dashboardData.dates,
    netLiqRangeDashboard,
  );

  $: cliDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli,
      name: "CLI",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
    },
  ];
  $: cliData = filterPlotlyData(cliDataRaw, $dashboardData.dates, cliRange);
  $: cliDataDashboard = filterPlotlyData(
    cliDataRaw,
    $dashboardData.dates,
    cliRangeDashboard,
  );

  // TIPS / Inflation Expectations Data
  let tipsRange = "5Y";
  $: tipsDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_breakeven,
      name: "10Y Breakeven Inflation",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
      yaxis: "y",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_real_rate,
      name: "10Y Real Rate (TIPS Yield)",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2, shape: "spline" },
      yaxis: "y2",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.tips_5y5y_forward,
      name: "5Y5Y Forward Inflation",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 2, dash: "dash", shape: "spline" },
      yaxis: "y",
    },
  ];
  $: tipsData = filterPlotlyData(tipsDataRaw, $dashboardData.dates, tipsRange);
  $: tipsLayout = {
    yaxis: { title: "Inflation (%)", side: "left", showgrid: false },
    yaxis2: {
      title: "Real Rate (%)",
      overlaying: "y",
      side: "right",
      showgrid: false,
    },
    legend: { orientation: "h", y: 1.1 },
    margin: { t: 40, r: 60 },
  };

  // Bank Reserves Chart Data
  $: bankReservesDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_reserves,
      name: "Bank Reserves (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#22c55e", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(34, 197, 94, 0.05)",
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq,
      name: "Net Liquidity (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2, dash: "dot", shape: "spline" },
      yaxis: "y2",
    },
  ];
  $: bankReservesData = filterPlotlyData(
    bankReservesDataRaw,
    $dashboardData.dates,
    reservesRange,
  );
  $: bankReservesLayout = {
    yaxis: { title: "Reserves (T)", side: "left", showgrid: false },
    yaxis2: {
      title: "Net Liq (T)",
      overlaying: "y",
      side: "right",
      showgrid: false,
    },
    legend: { orientation: "h", y: 1.1 },
  };

  // Repo Stress Chart Data (SOFR vs IORB)
  $: repoStressDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.repo_stress?.sofr,
      name: "SOFR (%)",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.repo_stress?.iorb,
      name: "IORB (%)",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 2, dash: "dash", shape: "spline" },
    },
  ];
  $: repoStressData = filterPlotlyData(
    repoStressDataRaw,
    $dashboardData.dates,
    repoStressRange,
  );

  // RRP (Reverse Repo) Chart Data
  $: rrpDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_rrp,
      name: "Fed RRP (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(239, 68, 68, 0.05)",
    },
  ];
  $: rrpData = filterPlotlyData(rrpDataRaw, $dashboardData.dates, rrpRange);

  // TGA (Treasury General Account) Chart Data
  $: tgaDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq_tga,
      name: "TGA (T)",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 2, shape: "spline" },
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
    },
  ];
  $: tgaData = filterPlotlyData(tgaDataRaw, $dashboardData.dates, tgaRange);

  // GLI Metrics Helpers
  $: gliWeights = Object.entries($dashboardData.gli_weights || {})
    .map(([id, weight]) => {
      const rocs = $dashboardData.bank_rocs?.[id] || {};
      return {
        id,
        name: id.toUpperCase(),
        weight,
        isLiability: false,
        m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
        m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
        m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
        y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
        imp1: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        imp3: rocs["impact_3m"]?.[rocs["impact_3m"].length - 1] || 0,
        imp1y: rocs["impact_1y"]?.[rocs["impact_1y"].length - 1] || 0,
      };
    })
    .sort((a, b) => b.weight - a.weight);

  // M2 Metrics Helpers
  $: m2Weights = Object.entries($dashboardData.m2_weights || {})
    .map(([id, weight]) => {
      const rocs = $dashboardData.m2_bank_rocs?.[id] || {};
      return {
        id,
        name: id.toUpperCase(),
        weight,
        isLiability: false,
        m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
        m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
        m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
        y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
        imp1: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        imp3: rocs["impact_3m"]?.[rocs["impact_3m"].length - 1] || 0,
        imp1y: rocs["impact_1y"]?.[rocs["impact_1y"].length - 1] || 0,
      };
    })
    .sort((a, b) => b.weight - a.weight);

  // US System Metrics Helpers
  $: usSystemMetrics = $dashboardData.us_system_rocs
    ? Object.entries($dashboardData.us_system_rocs).map(([id, data]) => {
        const labels = {
          fed: "Fed Assets",
          rrp: "Fed RRP",
          tga: "Treasury TGA",
        };
        return {
          id,
          name: labels[id] || id.toUpperCase(),
          isLiability: id !== "fed",
          m1: data["1M"]?.[data["1M"].length - 1] || 0,
          m3: data["3M"]?.[data["3M"].length - 1] || 0,
          y1: data["1Y"]?.[data["1Y"].length - 1] || 0,
          imp1: data["impact_1m"]?.[data["impact_1m"].length - 1] || 0,
          imp3: data["impact_3m"]?.[data["impact_3m"].length - 1] || 0,
          imp1y: data["impact_1y"]?.[data["impact_1y"].length - 1] || 0,
          delta1: data["delta_1m"]?.[data["delta_1m"].length - 1] || 0,
          delta3: data["delta_3m"]?.[data["delta_3m"].length - 1] || 0,
          delta1y: data["delta_1y"]?.[data["delta_1y"].length - 1] || 0,
        };
      })
    : [];

  $: usSystemTotal = usSystemMetrics.reduce(
    (acc, item) => {
      return {
        delta1: acc.delta1 + item.delta1,
        imp1: acc.imp1 + item.imp1,
        delta3: acc.delta3 + item.delta3,
        imp3: acc.imp3 + item.imp3,
        delta1y: acc.delta1y + item.delta1y,
        imp1y: acc.imp1y + item.imp1y,
      };
    },
    { delta1: 0, imp1: 0, delta3: 0, imp3: 0, delta1y: 0, imp1y: 0 },
  );

  $: gliMovers = $dashboardData.bank_rocs
    ? Object.entries($dashboardData.bank_rocs)
        .map(([id, rocs]) => ({
          id,
          name: id.toUpperCase(),
          isLiability: false,
          m1: rocs["1M"]?.[rocs["1M"].length - 1] || 0,
          m3: rocs["3M"]?.[rocs["3M"].length - 1] || 0,
          m6: rocs["6M"]?.[rocs["6M"].length - 1] || 0,
          y1: rocs["1Y"]?.[rocs["1Y"].length - 1] || 0,
          impact: rocs["impact_1m"]?.[rocs["impact_1m"].length - 1] || 0,
        }))
        .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
        .slice(0, 5)
    : [];

  // --- CLI Component Breakdown (Stacked Contribution) ---
  // Weights matching backend: HY (0.25), IG (0.15), NFCI_CREDIT (0.20), NFCI_RISK (0.20), LENDING (0.10), VIX (0.10)
  $: cliComponentDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.hy_z.map((v) => v * 0.25),
      name: "HY Spread Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(239, 68, 68, 0.4)", // red
      line: { color: "#ef4444", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.ig_z.map((v) => v * 0.15),
      name: "IG Spread Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(249, 115, 22, 0.4)", // orange
      line: { color: "#f97316", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_credit_z.map((v) => v * 0.2),
      name: "NFCI Credit Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(234, 179, 8, 0.4)", // yellow
      line: { color: "#eab308", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_risk_z.map((v) => v * 0.2),
      name: "NFCI Risk Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(168, 85, 247, 0.4)", // purple
      line: { color: "#a855f7", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.lending_z.map((v) => v * 0.1),
      name: "Lending Standards Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(59, 130, 246, 0.4)", // blue
      line: { color: "#3b82f6", width: 1 },
    },
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.vix_z.map((v) => v * 0.1),
      name: "VIX Contrast",
      type: "scatter",
      stackgroup: "cli",
      fillcolor: "rgba(107, 114, 128, 0.4)", // gray
      line: { color: "#6b7280", width: 1 },
    },
  ];
  $: cliComponentData = filterPlotlyData(
    cliComponentDataRaw,
    $dashboardData.dates,
    cliCompRangeDashboard,
  );

  $: vixDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.vix,
      name: "VIX",
      type: "scatter",
      mode: "lines",
      line: { color: "#dc2626", width: 3, shape: "spline" },
    },
  ];
  $: vixData = filterPlotlyData(vixDataRaw, $dashboardData.dates, vixRange);

  $: spreadDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.hy_spread,
      name: "HY Spread",
      type: "scatter",
      mode: "lines",
      line: { color: "#7c3aed", width: 3, shape: "spline" },
    },
  ];
  $: spreadData = filterPlotlyData(
    spreadDataRaw,
    $dashboardData.dates,
    spreadRange,
  );

  // --- Individual CLI Components (Z-Scores) ---
  $: hyZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.hy_z,
      name: "HY Spread Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 2 },
    },
  ];
  $: hyZData = filterPlotlyData(hyZDataRaw, $dashboardData.dates, hyRange);

  $: igZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.ig_z,
      name: "IG Spread Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#f97316", width: 2 },
    },
  ];
  $: igZData = filterPlotlyData(igZDataRaw, $dashboardData.dates, igRange);

  $: nfciCreditZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_credit_z,
      name: "NFCI Credit Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#eab308", width: 2 },
    },
  ];
  $: nfciCreditZData = filterPlotlyData(
    nfciCreditZDataRaw,
    $dashboardData.dates,
    nfciRange,
  );

  $: nfciRiskZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.nfci_risk_z,
      name: "NFCI Risk Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#a855f7", width: 2 },
    },
  ];
  $: nfciRiskZData = filterPlotlyData(
    nfciRiskZDataRaw,
    $dashboardData.dates,
    nfciRange,
  );

  $: lendingZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.lending_z,
      name: "Lending Standards Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 2 },
    },
  ];
  $: lendingZData = filterPlotlyData(
    lendingZDataRaw,
    $dashboardData.dates,
    lendingRange,
  );

  $: vixZDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.cli_components.vix_z,
      name: "VIX Contrast",
      type: "scatter",
      mode: "lines",
      line: { color: "#6b7280", width: 2 },
    },
  ];
  $: vixZData = filterPlotlyData(vixZDataRaw, $dashboardData.dates, vixRange);

  // --- M2 Money Supply Chart Data ---
  $: m2TotalDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.total,
      name: "Global M2 Total",
      type: "scatter",
      mode: "lines",
      line: { color: "#6366f1", width: 3, shape: "spline" },
    },
  ];
  $: m2TotalData = filterPlotlyData(
    m2TotalDataRaw,
    $dashboardData.dates,
    m2Range,
  );

  $: usM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.us,
      name: "US M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
    },
  ];
  $: usM2Data = filterPlotlyData(usM2DataRaw, $dashboardData.dates, usM2Range);

  $: euM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.eu,
      name: "EU M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
    },
  ];
  $: euM2Data = filterPlotlyData(euM2DataRaw, $dashboardData.dates, euM2Range);

  $: cnM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.cn,
      name: "China M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
    },
  ];
  $: cnM2Data = filterPlotlyData(cnM2DataRaw, $dashboardData.dates, cnM2Range);

  $: jpM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.jp,
      name: "Japan M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
    },
  ];
  $: jpM2Data = filterPlotlyData(jpM2DataRaw, $dashboardData.dates, jpM2Range);

  $: ukM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.uk,
      name: "UK M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
    },
  ];
  $: ukM2Data = filterPlotlyData(ukM2DataRaw, $dashboardData.dates, ukM2Range);

  $: caM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ca,
      name: "Canada M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 3, shape: "spline" },
    },
  ];
  $: caM2Data = filterPlotlyData(caM2DataRaw, $dashboardData.dates, caM2Range);

  $: auM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.au,
      name: "Australia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#3b82f6", width: 3, shape: "spline" },
    },
  ];
  $: auM2Data = filterPlotlyData(auM2DataRaw, $dashboardData.dates, auM2Range);

  $: inM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.in,
      name: "India M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#6366f1", width: 3, shape: "spline" },
    },
  ];
  $: inM2Data = filterPlotlyData(inM2DataRaw, $dashboardData.dates, inM2Range);

  $: chM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ch,
      name: "Switzerland M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#0ea5e9", width: 3, shape: "spline" },
    },
  ];
  $: chM2Data = filterPlotlyData(chM2DataRaw, $dashboardData.dates, chM2Range);

  $: ruM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.ru,
      name: "Russia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#dc2626", width: 3, shape: "spline" },
    },
  ];
  $: ruM2Data = filterPlotlyData(ruM2DataRaw, $dashboardData.dates, ruM2Range);

  $: brM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.br,
      name: "Brazil M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#10b981", width: 3, shape: "spline" },
    },
  ];
  $: brM2Data = filterPlotlyData(brM2DataRaw, $dashboardData.dates, brM2Range);

  $: krM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.kr,
      name: "South Korea M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#8b5cf6", width: 3, shape: "spline" },
    },
  ];
  $: krM2Data = filterPlotlyData(krM2DataRaw, $dashboardData.dates, krM2Range);

  $: mxM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.mx,
      name: "Mexico M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f59e0b", width: 3, shape: "spline" },
    },
  ];
  $: mxM2Data = filterPlotlyData(mxM2DataRaw, $dashboardData.dates, mxM2Range);

  $: myM2DataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.m2.my,
      name: "Malaysia M2",
      type: "scatter",
      mode: "lines",
      line: { color: "#f43f5e", width: 3, shape: "spline" },
    },
  ];
  $: myM2Data = filterPlotlyData(myM2DataRaw, $dashboardData.dates, myM2Range);

  $: gliSignal = $latestStats?.gli?.change > 0 ? "bullish" : "bearish";
  $: liqSignal = $latestStats?.us_net_liq?.change > 0 ? "bullish" : "bearish";

  // Bitcoin data
  $: btcFairValueData = [
    {
      name: "BTC Price",
      type: "area",
      color: "#f7931a",
      topColor: "rgba(247, 147, 26, 0.1)",
      bottomColor: "rgba(247, 147, 26, 0)",
      data: formatTV($dashboardData.dates, $dashboardData.btc?.price),
      width: 3,
    },
    {
      name: "Fair Value",
      type: "line",
      color: "#10b981",
      data: formatTV($dashboardData.dates, activeBtcModel.fair_value),
      width: 2,
    },
    {
      name: "+2σ",
      type: "line",
      color: "#ef4444",
      data: formatTV($dashboardData.dates, activeBtcModel.upper_2sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "+1σ",
      type: "line",
      color: "#f59e0b",
      data: formatTV($dashboardData.dates, activeBtcModel.upper_1sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "-1σ",
      type: "line",
      color: "#f59e0b",
      data: formatTV($dashboardData.dates, activeBtcModel.lower_1sd),
      width: 1,
      options: { lineStyle: 2 },
    },
    {
      name: "-2σ",
      type: "line",
      color: "#ef4444",
      data: formatTV($dashboardData.dates, activeBtcModel.lower_2sd),
      width: 1,
      options: { lineStyle: 2 },
    },
  ];

  $: btcDeviationData = [
    {
      x: $dashboardData.dates,
      y: activeBtcModel.deviation_zscore || [],
      name: "Price Deviation (Z-Score)",
      type: "scatter",
      mode: "lines",
      line: { color: "#6366f1", width: 2 },
    },
  ];

  $: btcLayout = {
    xaxis: {
      range: (() => {
        const prices = $dashboardData.btc?.price || [];
        const firstIdx = prices.findIndex((p) => p !== null);
        if (firstIdx !== -1) {
          return [
            $dashboardData.dates[firstIdx],
            $dashboardData.dates[prices.length - 1],
          ];
        }
        return undefined;
      })(),
    },
  };

  $: correlationData = (() => {
    const corrs = $dashboardData.correlations || {};
    return [
      {
        x: Object.keys(corrs["gli_btc"] || {}).map(Number),
        y: Object.values(corrs["gli_btc"] || {}),
        name: "GLI vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#6366f1", width: 2 },
      },
      {
        x: Object.keys(corrs["cli_btc"] || {}).map(Number),
        y: Object.values(corrs["cli_btc"] || {}),
        name: "CLI vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#f59e0b", width: 2 },
      },
      {
        x: Object.keys(corrs["vix_btc"] || {}).map(Number),
        y: Object.values(corrs["vix_btc"] || {}),
        name: "VIX vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#dc2626", width: 2 },
      },
      {
        x: Object.keys(corrs["netliq_btc"] || {}).map(Number),
        y: Object.values(corrs["netliq_btc"] || {}),
        name: "Net Liq vs BTC",
        type: "scatter",
        mode: "lines",
        line: { color: "#10b981", width: 2 },
      },
    ];
  })();

  $: lagCorrelationChartData = (() => {
    const lagData =
      $dashboardData.predictive?.lag_correlations?.[selectedLagWindow];
    if (!lagData || !lagData.lags || !lagData.correlations) return [];

    const optimalLag = lagData.optimal_lag || 0;
    const colors = lagData.lags.map((lag) =>
      lag === optimalLag ? "#10b981" : "#6366f1",
    );

    return [
      {
        x: lagData.lags,
        y: lagData.correlations.map((c) => (c !== null ? c * 100 : null)), // Convert to percentage
        name: `${selectedLagWindow.toUpperCase()} ROC Lag Correlation`,
        type: "bar",
        marker: { color: colors },
      },
    ];
  })();

  $: quantV2ChartData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.dates || v2.dates.length === 0) return [];

    return [
      {
        name: "BTC Price",
        type: "area",
        color: "#f7931a",
        topColor: "rgba(247, 147, 26, 0.1)",
        bottomColor: "rgba(247, 147, 26, 0)",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.btc_price[i],
          }))
          .filter((p) => p.value !== null),
        width: 3,
      },
      {
        name: "Fair Value",
        type: "line",
        color: "#10b981",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.fair_value[i],
          }))
          .filter((p) => p.value !== null),
        width: 2,
      },
      {
        name: "+2σ",
        type: "line",
        color: "#ef4444",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.upper_2sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "+1σ",
        type: "line",
        color: "#f59e0b",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.upper_1sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "-1σ",
        type: "line",
        color: "#f59e0b",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.lower_1sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
      {
        name: "-2σ",
        type: "line",
        color: "#ef4444",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.lower_2sd[i],
          }))
          .filter((p) => p.value !== null),
        width: 1,
        options: { lineStyle: 2 },
      },
    ];
  })();

  // Returns comparison chart data (Plotly bar chart)
  $: quantV2ReturnsData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.returns || !v2.returns.dates) return [];

    return [
      {
        x: v2.returns.dates,
        y: v2.returns.actual,
        name: "Actual Returns (%)",
        type: "bar",
        marker: { color: "#f7931a", opacity: 0.7 },
      },
      {
        x: v2.returns.dates,
        y: v2.returns.predicted,
        name: "Predicted Returns (%)",
        type: "scatter",
        mode: "lines",
        line: { color: "#10b981", width: 2 },
      },
    ];
  })();

  // Rebalanced Fair Value chart data (LightweightChart)
  $: quantV2RebalancedData = (() => {
    const v2 = $dashboardData.btc?.models?.quant_v2;
    if (!v2 || !v2.dates || v2.dates.length === 0 || !v2.rebalanced_fv)
      return [];

    return [
      {
        name: "BTC Price",
        type: "area",
        color: "#f7931a",
        topColor: "rgba(247, 147, 26, 0.1)",
        bottomColor: "rgba(247, 147, 26, 0)",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.btc_price[i],
          }))
          .filter((p) => p.value !== null),
        width: 3,
      },
      {
        name: "Rebalanced FV",
        type: "line",
        color: "#8b5cf6",
        data: v2.dates
          .map((d, i) => ({
            time: d,
            value: v2.rebalanced_fv[i],
          }))
          .filter((p) => p.value !== null),
        width: 2,
      },
    ];
  })();

  const getLastDate = (seriesKey) => {
    if (!$dashboardData.last_dates) return "N/A";
    const key = seriesKey.toUpperCase();
    return (
      $dashboardData.last_dates[key] ||
      $dashboardData.last_dates[key + "_USD"] ||
      $dashboardData.last_dates[seriesKey] ||
      "N/A"
    );
  };

  const getLatestROC = (rocsObj, window) => {
    if (!rocsObj || !rocsObj[window] || !Array.isArray(rocsObj[window]))
      return 0;
    const series = rocsObj[window];
    return series.length > 0 ? series[series.length - 1] : 0;
  };

  const getLatestValue = (series) => {
    if (!series || !Array.isArray(series) || series.length === 0) return null;
    for (let i = series.length - 1; i >= 0; i--) {
      if (series[i] !== null && series[i] !== undefined) return series[i];
    }
    return null;
  };
</script>

<svelte:head>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
  <link
    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;600;800&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<div class="app-container">
  <aside class="sidebar">
    <svg style="position: absolute; width: 0; height: 0;" aria-hidden="true">
      <filter id="remove-white">
        <feColorMatrix
          type="matrix"
          values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 -3 -3 -3 1 8.5"
        />
      </filter>
    </svg>

    <div class="brand">
      <div
        class="logo-box"
        style="background: transparent; padding: 0; overflow: visible;"
      >
        <img
          src="logo-isometric.jpg"
          alt="Quant Terminal"
          style="width: 100%; height: 100%; object-fit: contain; filter: url(#remove-white);"
        />
      </div>
      <div class="brand-text">
        <h2>Quant Terminal</h2>
        <span>Liquidity Engine</span>
      </div>
    </div>

    <nav>
      <div
        class="nav-item"
        class:active={currentTab === "Dashboard"}
        on:click={() => setTab("Dashboard")}
        on:keydown={(e) => e.key === "Enter" && setTab("Dashboard")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">📊</span>
        {$currentTranslations.nav_dashboard}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global Flows CB"}
        on:click={() => setTab("Global Flows CB")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global Flows CB")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🌍</span>
        {$currentTranslations.nav_gli}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global M2"}
        on:click={() => setTab("Global M2")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global M2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">💰</span>
        {$currentTranslations.nav_m2}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "US System"}
        on:click={() => setTab("US System")}
        on:keydown={(e) => e.key === "Enter" && setTab("US System")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🇺🇸</span>
        {$currentTranslations.nav_us_system}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Risk Model"}
        on:click={() => setTab("Risk Model")}
        on:keydown={(e) => e.key === "Enter" && setTab("Risk Model")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">⚠️</span>
        {$currentTranslations.nav_risk_model}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Analysis"}
        on:click={() => setTab("BTC Analysis")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Analysis")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">₿</span>
        {$currentTranslations.nav_btc_analysis}
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Quant v2"}
        on:click={() => setTab("BTC Quant v2")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Quant v2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🧪</span>
        {$currentTranslations.nav_btc_quant}
      </div>
    </nav>

    <div class="sidebar-footer"></div>
  </aside>

  <main class="content">
    <header>
      <div class="content-header">
        <h1>
          {currentTab}
          {$currentTranslations.nav_dashboard === "Dashboard"
            ? "Overview"
            : "Resumen"}
        </h1>
        <p>
          {$currentTranslations.header_desc}
        </p>
      </div>
      <div class="header-actions">
        <div class="status-indicator">
          <div class="pulse"></div>
          {$currentTranslations.system_live}
        </div>
        <button
          class="header-toggle"
          on:click={toggleLanguage}
          title={$currentTranslations.switch_lang}
        >
          <span class="toggle-icon">🌐</span>
          <span class="toggle-label">{$language === "en" ? "EN" : "ES"}</span>
        </button>
        <button
          class="header-toggle"
          on:click={toggleDarkMode}
          title={$darkMode
            ? $currentTranslations.light_mode
            : $currentTranslations.dark_mode}
        >
          <span class="toggle-icon">{darkMode ? "☀️" : "🌙"}</span>
          <span class="toggle-label"
            >{$darkMode
              ? ($currentTranslations.light_mode || "").split(" ")[0]
              : ($currentTranslations.dark_mode || "").split(" ")[0]}</span
          >
        </button>
        {#if $isLoading}
          <div class="loader"></div>
        {:else}
          <button class="refresh-btn" on:click={fetchData}
            >{$currentTranslations.refresh_data}</button
          >
        {/if}
      </div>
    </header>

    {#if $error}
      <div class="error-banner">
        <strong>Connection Error:</strong>
        {$error}
      </div>
    {/if}

    <div class="dashboard-grid">
      {#if currentTab === "Dashboard"}
        <DashboardTab
          darkMode={$darkMode}
          language={$language}
          translations={$currentTranslations}
          dashboardData={$dashboardData}
          latestStats={$latestStats}
          {gliData}
          netLiqData={netLiqDataDashboard}
          cliData={cliDataDashboard}
          {cliComponentData}
          {regimeLCData}
          {impulseData}
          {impulseLayout}
          {gliWeights}
          {usSystemMetrics}
          {usSystemTotal}
          {gliSignal}
          {liqSignal}
          {currentRegime}
          {liquidityScore}
          {regimeDiagnostics}
          bind:regimeLag
          bind:btcRocPeriod
          bind:btcLag
          bind:showComposite
          {optimalLagLabel}
          {getLastDate}
          {getLatestValue}
          bind:gliRange
          bind:gliShowConstantFx
          bind:netLiqRange={netLiqRangeDashboard}
          bind:cliRange={cliRangeDashboard}
          bind:cliCompRange={cliCompRangeDashboard}
          bind:impulseRange
        />
      {:else if currentTab === "Global Flows CB"}
        <GlobalFlowsCbTab
          darkMode={$darkMode}
          language={$language}
          translations={$currentTranslations}
          {fedData}
          {ecbData}
          {bojData}
          {boeData}
          {pbocData}
          {bocData}
          {rbaData}
          {snbData}
          {bokData}
          {rbiData}
          {cbrData}
          {bcbData}
          {rbnzData}
          {srData}
          {bnmData}
          {cbBreadthData}
          {cbConcentrationData}
          {getLastDate}
          bind:fedRange
          bind:ecbRange
          bind:bojRange
          bind:boeRange
          bind:pbocRange
          bind:bocRange
          bind:rbaRange
          bind:snbRange
          bind:bokRange
          bind:rbiRange
          bind:cbrRange
          bind:bcbRange
          bind:rbnzRange
          bind:srRange
          bind:bnmRange
          bind:cbBreadthRange
          bind:cbConcentrationRange
        />
      {:else if currentTab === "Global M2"}
        <GlobalM2Tab
          darkMode={$darkMode}
          translations={$currentTranslations}
          {m2TotalData}
          {m2Weights}
          {usM2Data}
          {euM2Data}
          {cnM2Data}
          {jpM2Data}
          {ukM2Data}
          {caM2Data}
          {auM2Data}
          {krM2Data}
          {inM2Data}
          {brM2Data}
          {mxM2Data}
          {ruM2Data}
          {chM2Data}
          {myM2Data}
          {getLastDate}
          bind:m2Range
          bind:usM2DataRange={usM2Range}
          bind:euM2DataRange={euM2Range}
          bind:cnM2DataRange={cnM2Range}
          bind:jpM2DataRange={jpM2Range}
          bind:ukM2DataRange={ukM2Range}
          bind:caM2DataRange={caM2Range}
          bind:auM2DataRange={auM2Range}
          bind:inM2DataRange={inM2Range}
          bind:chM2DataRange={chM2Range}
          bind:ruM2DataRange={ruM2Range}
          bind:brM2DataRange={brM2Range}
          bind:krM2DataRange={krM2Range}
          bind:mxM2DataRange={mxM2Range}
          bind:myM2DataRange={myM2Range}
        />
      {:else if currentTab === "US System"}
        <UsSystemTab
          darkMode={$darkMode}
          language={$language}
          translations={$currentTranslations}
          dashboardData={$dashboardData}
          {netLiqData}
          {bankReservesData}
          {bankReservesLayout}
          {fedData}
          {rrpData}
          {tgaData}
          {usSystemMetrics}
          {usSystemTotal}
          {getLastDate}
          {getLatestValue}
          bind:netLiqRange
          bind:reservesRange
          bind:fedRange
          bind:rrpRange
          bind:tgaRange
        />
      {:else if currentTab === "Risk Model"}
        <RiskModelTab
          darkMode={$darkMode}
          language={$language}
          translations={$currentTranslations}
          dashboardData={$dashboardData}
          {cliData}
          {hyZData}
          {igZData}
          {nfciCreditZData}
          {nfciRiskZData}
          {lendingZData}
          {vixZData}
          {tipsData}
          {tipsLayout}
          {repoStressData}
          {getLastDate}
          {getLatestValue}
          {getLatestROC}
          bind:cliRange
          bind:hyRange
          bind:igRange
          bind:nfciCreditRange
          bind:nfciRiskRange
          bind:lendingRange
          bind:vixRange
          bind:tipsRange
          bind:repoStressRange
        />
      {:else if currentTab === "BTC Analysis"}
        <BtcAnalysisTab
          darkMode={$darkMode}
          translations={$currentTranslations}
          latestStats={$latestStats}
          dashboardData={$dashboardData}
          {btcFairValueData}
          lagCorrelationChartData={$dashboardData.predictive?.lag_correlations}
          {correlationData}
          {getLatestROC}
          bind:selectedBtcModel
          bind:selectedLagWindow
          bind:btcRange
        />
      {:else if currentTab === "BTC Quant v2"}
        <BtcQuantV2Tab
          darkMode={$darkMode}
          translations={$currentTranslations}
          dashboardData={$dashboardData}
          {quantV2ChartData}
          {quantV2RebalancedData}
          {quantV2ReturnsData}
          {getLatestValue}
        />
      {/if}
    </div>
  </main>
</div>

<style>
  /* CSS Variables for Theme */
  :global(:root) {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-tertiary: #f1f5f9;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --accent-primary: #4f46e5;
    --accent-secondary: #3b82f6;
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    --chart-description-bg: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    --positive-color: #059669;
    --negative-color: #dc2626;
  }

  :global([data-theme="dark"]) {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-tertiary: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --border-color: #334155;
    --accent-primary: #6366f1;
    --accent-secondary: #60a5fa;
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    --chart-description-bg: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    --positive-color: #10b981;
    --negative-color: #f87171;
  }

  :global(body) {
    margin: 0;
    padding: 0;
    background: var(--bg-primary);
    color: var(--text-primary);
    font-family:
      "Inter",
      -apple-system,
      system-ui,
      sans-serif;
    overflow-x: hidden;
    transition:
      background-color 0.3s ease,
      color 0.3s ease;
  }

  /* Custom Scrollbar Styling */
  :global(::-webkit-scrollbar) {
    width: 8px;
    height: 8px;
  }

  :global(::-webkit-scrollbar-track) {
    background: transparent;
  }

  :global(::-webkit-scrollbar-thumb) {
    background: rgba(100, 116, 139, 0.2);
    border-radius: 10px;
    transition: background 0.2s;
  }

  :global(::-webkit-scrollbar-thumb:hover) {
    background: rgba(100, 116, 139, 0.4);
  }

  :global([data-theme="dark"] ::-webkit-scrollbar-thumb) {
    background: rgba(148, 163, 184, 0.2);
  }

  :global([data-theme="dark"] ::-webkit-scrollbar-thumb:hover) {
    background: rgba(148, 163, 184, 0.4);
  }

  /* Firefox Support */
  :global(*) {
    scrollbar-width: thin;
    scrollbar-color: rgba(100, 116, 139, 0.2) transparent;
  }

  :global([data-theme="dark"]) {
    scrollbar-color: rgba(148, 163, 184, 0.2) transparent;
  }

  .app-container {
    display: flex;
    min-height: 100vh;
    width: 100vw;
  }

  .sidebar {
    width: 280px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: 40px 24px;
    flex-shrink: 0;
    transition:
      background-color 0.3s ease,
      border-color 0.3s ease;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 48px;
    padding-left: 8px;
  }

  .logo-box {
    width: 44px;
    height: 44px;
    background: #4f46e5;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 800;
    font-size: 1.25rem;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
  }

  .brand-text h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .brand-text span {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
  }

  nav {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .nav-item {
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 0.9375rem;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 500;
  }

  .nav-icon {
    font-size: 1.125rem;
  }

  .nav-item:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: rgba(79, 70, 229, 0.1);
    color: var(--accent-primary);
    font-weight: 600;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 0 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.8125rem;
    color: var(--text-muted);
    font-weight: 500;
  }

  .pulse {
    width: 10px;
    height: 10px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 0 rgba(16, 185, 129, 0.4);
    animation: pulse-light 2s infinite;
  }

  @keyframes pulse-light {
    0% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6);
    }
    70% {
      transform: scale(1);
      box-shadow: 0 0 0 8px rgba(16, 185, 129, 0);
    }
    100% {
      transform: scale(0.95);
      box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
    }
  }

  .content {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background: var(--bg-primary);
    transition: background-color 0.3s ease;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    width: 100%;
  }

  .content-header h1 {
    margin: 0 0 4px 0;
    font-size: 2.25rem;
    font-weight: 800;
    color: var(--text-primary);
    letter-spacing: -0.025em;
  }

  .content-header p {
    margin: 0;
    color: var(--text-muted);
    font-size: 1.125rem;
  }

  .refresh-btn {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 10px 20px;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: var(--card-shadow);
  }

  .refresh-btn:hover {
    background: var(--bg-tertiary);
    border-color: var(--accent-secondary);
    transform: translateY(-1px);
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border: 1px solid var(--border-color);
    background: var(--bg-secondary);
    border-radius: 10px;
    cursor: pointer;
    font-size: 0.8125rem;
    color: var(--text-secondary);
    transition: all 0.2s;
  }

  .header-toggle:hover {
    background: var(--accent-primary);
    color: white;
    border-color: var(--accent-primary);
  }

  .toggle-icon {
    font-size: 0.875rem;
  }

  .toggle-label {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }

  .error-banner {
    background: #fef2f2;
    border: 1px solid #fee2e2;
    color: #dc2626;
    padding: 16px 24px;
    border-radius: 16px;
    margin-bottom: 32px;
    font-size: 0.9375rem;
    font-weight: 500;
  }

  :global(.dashboard-grid) {
    width: 100%;
  }

  :global(.stats-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 32px;
    margin-bottom: 40px;
    width: 100%;
  }

  :global(.main-charts) {
    display: flex;
    flex-direction: column;
    gap: 32px;
    width: 100%;
  }

  :global(.chart-card) {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 32px;
    display: flex;
    flex-direction: column;
    box-shadow: var(--card-shadow);
    transition:
      background-color 0.3s ease,
      border-color 0.3s ease;
  }

  :global(.wide) {
    grid-column: span 2;
  }

  :global(.chart-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  :global(.header-controls) {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  :global(.chart-header h3) {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  :global(.last-date) {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    background: var(--bg-tertiary);
    padding: 4px 10px;
    border-radius: 6px;
  }

  :global(.chart-content) {
    min-height: 500px;
    height: 500px;
    flex: none; /* Force fixed height to rule out flex issues */
    width: 100%;
    position: relative;
    overflow: hidden;
  }

  :global(.chart-description) {
    margin: 8px 0 16px 0;
    padding: 12px 16px;
    background: var(--chart-description-bg);
    border-radius: 8px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    line-height: 1.5;
    border-left: 3px solid var(--accent-secondary);
  }

  /* Macro Regime Panel (Global for DashboardTab) */
  :global(.regime-card) {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    position: relative;
    overflow: hidden;
    box-shadow: var(--card-shadow);
    margin-bottom: 24px;
  }

  :global(.regime-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 16px;
  }

  :global(.regime-title) {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  :global(.regime-badge) {
    padding: 6px 14px;
    border-radius: 99px;
    font-size: 13px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    display: flex;
    align-items: center;
    gap: 6px;
    color: white;
  }

  :global(.bg-bullish) {
    background: #10b981;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
  }
  :global(.bg-bearish) {
    background: #ef4444;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
  }
  :global(.bg-global_inj) {
    background: #3b82f6;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  }
  :global(.bg-us_inj) {
    background: #8b5cf6;
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
  }
  :global(.bg-early_warning) {
    background: #f59e0b;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
  }
  :global(.bg-losing_steam) {
    background: #6366f1;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
  }
  :global(.bg-neutral) {
    background: #94a3b8;
    box-shadow: 0 4px 12px rgba(148, 163, 184, 0.2);
  }

  :global(.regime-body) {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
  }

  :global(.regime-description) {
    font-size: 14px;
    line-height: 1.5;
    color: var(--text-primary);
    font-weight: 500;
  }

  :global(.regime-details) {
    font-size: 12px;
    color: var(--text-muted);
    font-style: italic;
  }

  :global(.regime-glow) {
    position: absolute;
    top: -30px;
    right: -30px;
    width: 120px;
    height: 120px;
    border-radius: 50%;
    opacity: 0.15;
    filter: blur(40px);
    transition: all 0.5s ease;
  }

  :global(.glow-bullish) {
    background: #10b981;
  }
  :global(.glow-bearish) {
    background: #ef4444;
  }
  :global(.glow-global_inj) {
    background: #3b82f6;
  }
  :global(.glow-us_inj) {
    background: #8b5cf6;
  }
  :global(.glow-early_warning) {
    background: #f59e0b;
  }
  :global(.glow-losing_steam) {
    background: #6366f1;
  }
  :global(.glow-neutral) {
    background: #94a3b8;
  }

  /* ====== METRICS TABLE & SIDEBAR STYLES ====== */
  /* These are used by tab components for data tables */

  :global(.gli-layout) {
    display: grid;
    grid-template-columns: 1fr 400px;
    gap: 24px;
  }

  :global(.chart-main) {
    display: flex;
    flex-direction: column;
  }

  :global(.metrics-sidebar) {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 16px;
    background: var(--bg-tertiary);
    border-radius: 16px;
    max-height: 600px;
    overflow-y: auto;
  }

  :global(.metrics-section) {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  :global(.metrics-section h4) {
    margin: 0 0 8px 0;
    font-size: 0.8125rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  :global(.metrics-table) {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.75rem;
  }

  :global(.metrics-table th),
  :global(.metrics-table td) {
    padding: 8px 6px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
  }

  :global(.metrics-table th) {
    font-weight: 600;
    color: var(--text-muted);
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    background: rgba(148, 163, 184, 0.05);
  }

  :global(.metrics-table td) {
    color: var(--text-primary);
  }

  :global(.metrics-table tbody tr:hover) {
    background: rgba(99, 102, 241, 0.05);
  }

  :global(.metrics-table.compact) {
    font-size: 0.6875rem;
  }

  :global(.metrics-table.compact th),
  :global(.metrics-table.compact td) {
    padding: 6px 4px;
  }

  :global(.total-row) {
    background: rgba(99, 102, 241, 0.08);
    font-weight: 600;
  }

  :global(.total-row td) {
    border-top: 2px solid var(--border-color);
    border-bottom: none;
  }

  /* ROC Value Styling */
  :global(.roc-val) {
    font-variant-numeric: tabular-nums;
    font-weight: 500;
  }

  :global(.roc-val.positive) {
    color: var(--positive-color);
  }

  :global(.roc-val.negative) {
    color: var(--negative-color);
  }

  :global(.impact-cell) {
    font-weight: 600;
  }

  /* Signal Cell Styling */
  :global(.signal-cell) {
    font-weight: 600;
    text-align: center;
  }

  :global(.signal-cell.plus) {
    color: var(--positive-color);
  }

  :global(.signal-cell.minus) {
    color: var(--negative-color);
  }

  /* Health Table Styling */
  :global(.health-table td:first-child) {
    font-weight: 500;
  }

  :global(.data-health-section) {
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 12px;
    background: rgba(99, 102, 241, 0.03);
  }

  /* ROC Inline Display */
  :global(.roc-inline) {
    display: flex;
    gap: 12px;
    font-size: 0.6875rem;
    color: var(--text-muted);
  }

  :global(.roc-inline .positive) {
    color: var(--positive-color);
  }

  :global(.roc-inline .negative) {
    color: var(--negative-color);
  }

  /* Responsive: Stack sidebar on smaller screens */
  @media (max-width: 1200px) {
    :global(.gli-layout) {
      grid-template-columns: 1fr;
    }

    :global(.metrics-sidebar) {
      max-height: none;
    }
  }

  /* ====== ADDITIONAL DASHBOARD & RISK MODEL STYLES ====== */

  :global(.stats-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 24px;
    margin-bottom: 32px;
  }

  /* ROC Section Styles */
  :global(.roc-section) {
    margin-top: 32px;
  }

  :global(.roc-card) {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 20px;
    padding: 24px;
    box-shadow: var(--card-shadow);
  }

  :global(.roc-card h4) {
    margin: 0 0 20px 0;
    color: var(--text-primary);
    font-size: 1.125rem;
    font-weight: 700;
  }

  :global(.roc-grid) {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  :global(.roc-row) {
    display: grid;
    grid-template-columns: 2fr repeat(4, 1fr);
    gap: 16px;
    padding: 14px 20px;
    background: var(--bg-tertiary);
    border-radius: 12px;
    align-items: center;
    transition:
      transform 0.2s ease,
      background-color 0.2s ease;
  }

  :global(.roc-row:not(.header):hover) {
    transform: translateX(4px);
    background: rgba(99, 102, 241, 0.08);
  }

  :global(.roc-row.header) {
    background: transparent;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border-color);
    border-radius: 0;
    margin-bottom: 4px;
  }

  :global(.roc-col) {
    font-size: 0.9375rem;
    color: var(--text-primary);
    font-weight: 500;
  }

  :global(.roc-row.header .roc-col) {
    color: var(--text-muted);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 700;
  }

  :global(.roc-col.label) {
    font-weight: 700;
    color: var(--text-secondary);
  }

  :global(.roc-col.plus) {
    color: var(--positive-color);
  }

  :global(.roc-col.minus) {
    color: var(--negative-color);
  }

  /* Regime Card Refinement */
  :global(.regime-card) {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global(.regime-header) {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }

  :global(.regime-title) {
    font-size: 0.8125rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    font-weight: 700;
  }

  :global(.regime-badge) {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 18px;
    border-radius: 99px;
    font-weight: 700;
    font-size: 0.9375rem;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  :global(.regime-badge.bg-bullish) {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  }
  :global(.regime-badge.bg-bearish) {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  }
  :global(.regime-badge.bg-grey) {
    background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  }

  :global(.liquidity-score) {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 14px;
    background: var(--bg-tertiary);
    border-radius: 12px;
  }

  :global(.score-label) {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
  }

  :global(.score-val) {
    font-size: 1.375rem;
    font-weight: 800;
    font-family: "Outfit", sans-serif;
  }

  :global(.score-val.high) {
    color: #10b981;
  }
  :global(.score-val.low) {
    color: #ef4444;
  }

  :global(.regime-body) {
    background: var(--bg-tertiary);
    padding: 24px;
    border-radius: 20px;
    border: 1px solid var(--border-color);
    margin-bottom: 24px;
  }

  :global(.regime-description) {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 12px 0;
  }

  :global(.regime-details) {
    font-size: 0.9375rem;
    color: var(--text-secondary);
    line-height: 1.6;
    margin: 0;
  }

  /* FX Toggle Styles */
  :global(.fx-toggle) {
    display: flex;
    gap: 4px;
    background: var(--bg-tertiary);
    padding: 4px;
    border-radius: 10px;
    border: 1px solid var(--border-color);
  }

  :global(.fx-btn) {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  :global(.fx-btn.active) {
    background: var(--bg-secondary);
    color: var(--accent-primary);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  :global(.fx-btn:hover:not(.active)) {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }

  /* Premium Buttons & Toggles */
  :global(.toggle-btn.active) {
    background: var(--accent-primary) !important;
    color: white !important;
    box-shadow: 0 0 15px rgba(99, 102, 241, 0.4);
    transform: translateY(-1px);
  }

  /* Interpretation Section */
  :global(.interp-section) {
    background: rgba(30, 41, 59, 0.5);
    border-radius: 12px;
    padding: 24px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  :global(.interp-section h4) {
    color: var(--accent-primary);
    margin: 0 0 12px 0;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  :global(.interp-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-top: 16px;
  }

  :global(.interp-item) {
    background: rgba(255, 255, 255, 0.02);
    padding: 12px;
    border-radius: 8px;
  }

  :global(.interp-label) {
    display: block;
    font-weight: 600;
    margin-bottom: 4px;
    color: var(--text-primary);
  }

  :global(.interp-val) {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  :global(.grid-2) {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 20px;
    width: 100%;
  }

  :global(.grid-4) {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 20px;
    width: 100%;
  }

  @media (max-width: 1200px) {
    :global(.grid-4) {
      grid-template-columns: repeat(2, 1fr) !important;
    }
  }

  @media (max-width: 768px) {
    :global(.grid-2),
    :global(.grid-4) {
      grid-template-columns: 1fr !important;
    }
  }

  /* Premium Cards (Quant v2) */
  :global(.metric-card.premium) {
    background: linear-gradient(
      135deg,
      rgba(30, 41, 59, 1) 0%,
      rgba(15, 23, 42, 1) 100%
    );
    border: 1px solid rgba(99, 102, 241, 0.2);
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  :global(.metric-card.premium:hover) {
    transform: translateY(-4px);
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow:
      0 10px 25px -5px rgba(0, 0, 0, 0.3),
      0 8px 10px -6px rgba(0, 0, 0, 0.3);
  }

  :global(.metric-card.premium::before) {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(
      90deg,
      transparent,
      var(--accent-primary),
      transparent
    );
    z-index: 2;
  }

  /* Shimmer Effect */
  :global(.metric-card.premium::after) {
    content: "";
    position: absolute;
    top: 0;
    left: -100%;
    width: 200%;
    height: 100%;
    background: linear-gradient(
      120deg,
      transparent,
      rgba(255, 255, 255, 0.03),
      transparent
    );
    transition: none;
    pointer-events: none;
  }

  :global(.metric-card.premium:hover::after) {
    animation: shimmer 1.5s infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  :global(.metric-card.purple) {
    border-color: rgba(167, 139, 250, 0.3);
  }
  :global(.metric-card.purple::before) {
    background: linear-gradient(90deg, transparent, #a78bfa, transparent);
  }
  :global(.metric-card.purple:hover) {
    border-color: rgba(167, 139, 250, 0.6);
    box-shadow: 0 10px 25px -5px rgba(167, 139, 250, 0.2);
  }

  :global(.metric-card.blue) {
    border-color: rgba(59, 130, 246, 0.3);
  }
  :global(.metric-card.blue::before) {
    background: linear-gradient(90deg, transparent, #3b82f6, transparent);
  }
  :global(.metric-card.blue:hover) {
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.2);
  }

  :global(.metric-card.orange) {
    border-color: rgba(245, 158, 11, 0.3);
  }
  :global(.metric-card.orange::before) {
    background: linear-gradient(90deg, transparent, #f59e0b, transparent);
  }
  :global(.metric-card.orange:hover) {
    border-color: rgba(245, 158, 11, 0.6);
    box-shadow: 0 10px 25px -5px rgba(245, 158, 11, 0.2);
  }

  /* ====== RISK SIGNAL DASHBOARD STYLES ====== */
  :global(.risk-dashboard) {
    margin-bottom: 32px;
    background: linear-gradient(
      160deg,
      rgba(30, 41, 59, 0.8) 0%,
      rgba(15, 23, 42, 0.9) 100%
    );
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    padding: 24px;
    backdrop-filter: blur(12px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  :global(.risk-dashboard-header) {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  :global(.risk-dashboard-header h2) {
    font-size: 1.125rem;
    font-weight: 800;
    margin: 0;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    background: linear-gradient(to right, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  :global(.signal-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
  }

  :global(.signal-item) {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    transition: all 0.2s ease;
  }

  :global(.signal-item:hover) {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-2px);
  }

  :global(.signal-label) {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  :global(.signal-status) {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.875rem;
    font-weight: 700;
  }

  :global(.signal-dot) {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    box-shadow: 0 0 8px currentColor;
  }

  :global(.signal-value) {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 500;
    font-variant-numeric: tabular-nums;
  }

  :global(.text-bullish) {
    color: #10b981;
  }
  :global(.text-bearish) {
    color: #ef4444;
  }
  :global(.text-neutral) {
    color: #94a3b8;
  }
  :global(.text-warning) {
    color: #f59e0b;
  }

  /* ====== RISK DASHBOARD REFINEMENTS ====== */
  :global(.risk-header-summary) {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 24px;
    background: rgba(255, 255, 255, 0.03);
    padding: 16px 24px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  :global(.stance-details) {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.02em;
  }

  /* Table Scroll Fix */
  :global(.metrics-table-container) {
    width: 100%;
    overflow-x: auto;
  }

  :global(.metrics-table) {
    width: 100%;
    min-width: 100%;
    table-layout: auto; /* Allow columns to fit content */
    font-size: 0.6875rem; /* ~11px - reduced to fit bigger tables */
  }

  :global(.metrics-sidebar .metrics-table) {
    font-size: 0.625rem !important; /* ~10px - extreme compaction for 8+ columns */
    table-layout: fixed; /* Force fitting within sidebar */
  }

  :global(
      .metrics-sidebar .metrics-table th,
      :global(.metrics-sidebar .metrics-table td)
    ) {
    padding: 3px 2px !important; /* Ultra-tight padding for sidebars */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  :global(.metrics-table th, :global(.metrics-table td)) {
    padding: 4px 3px !important; /* Tighter padding for main tables */
    line-height: 1.1;
  }

  :global(.metrics-table th) {
    text-transform: uppercase;
    letter-spacing: 0em; /* Reduced spacing to save width */
    font-weight: 700;
  }

  /* Signal-based Colors (Text & Global) */
  :global(.text-positive),
  :global(.text-bullish) {
    color: var(--positive-color) !important;
  }

  :global(.text-negative),
  :global(.text-bearish) {
    color: var(--negative-color) !important;
  }

  /* Signal-based Card Highlighting */
  :global(.chart-card.signal-bullish) {
    border-top: 4px solid #10b981 !important;
    background: linear-gradient(
      180deg,
      rgba(16, 185, 129, 0.05) 0%,
      var(--bg-secondary) 100%
    ) !important;
  }

  :global(.chart-card.signal-bearish) {
    border-top: 4px solid #ef4444 !important;
    background: linear-gradient(
      180deg,
      rgba(239, 68, 68, 0.05) 0%,
      var(--bg-secondary) 100%
    ) !important;
  }

  :global(.chart-card.signal-neutral) {
    border-top: 4px solid var(--border-color);
  }
</style>
