<script>
  import { onMount } from "svelte";
  import {
    fetchData,
    dashboardData,
    latestStats,
    isLoading,
    error,
    selectedSource,
  } from "./stores/dataStore";
  import StatsCard from "./lib/components/StatsCard.svelte";
  import Chart from "./lib/components/Chart.svelte";
  import LightweightChart from "./lib/components/LightweightChart.svelte";
  import SignalBadge from "./lib/components/SignalBadge.svelte";
  import TimeRangeSelector from "./lib/components/TimeRangeSelector.svelte";

  // Individual time range state for each chart section
  let gliRange = "ALL";
  let fedRange = "ALL";
  let ecbRange = "ALL";
  let bojRange = "ALL";
  let boeRange = "ALL";
  let pbocRange = "ALL";
  let netLiqRange = "ALL";
  let cliRange = "ALL";
  let btcRange = "ALL";
  let m2Range = "ALL";
  let vixRange = "ALL";
  let spreadRange = "ALL";

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
    if (!traceArray || range === "ALL") return traceArray;
    const indices = getFilteredIndices(dates, range);

    return traceArray.map((trace) => ({
      ...trace,
      x: indices.map((i) => trace.x[i]),
      y: indices.map((i) => trace.y[i]),
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

  const toggleSource = () => {
    selectedSource.update((s) => (s === "tv" ? "fred" : "tv"));
    fetchData();
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
  $: gliDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.gli.total,
      name: "GLI Total",
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      line: { color: "#6366f1", width: 3, shape: "spline" },
      fillcolor: "rgba(99, 102, 241, 0.05)",
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
      fill: "tozeroy",
      fillcolor: "rgba(59, 130, 246, 0.05)",
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
      fill: "tozeroy",
      fillcolor: "rgba(139, 92, 246, 0.05)",
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
      fill: "tozeroy",
      fillcolor: "rgba(244, 63, 94, 0.05)",
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
      fill: "tozeroy",
      fillcolor: "rgba(245, 158, 11, 0.05)",
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
      fill: "tozeroy",
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: pbocData = filterPlotlyData(pbocDataRaw, $dashboardData.dates, pbocRange);

  $: netLiqDataRaw = [
    {
      x: $dashboardData.dates,
      y: $dashboardData.us_net_liq,
      name: "US Net Liquidity",
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      line: { color: "#10b981", width: 3, shape: "spline" },
      fillcolor: "rgba(16, 185, 129, 0.05)",
    },
  ];
  $: netLiqData = filterPlotlyData(
    netLiqDataRaw,
    $dashboardData.dates,
    netLiqRange,
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
    return $dashboardData.last_dates[seriesKey] || "N/A";
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

<div class="app-container">
  <aside class="sidebar">
    <div class="brand">
      <div class="logo-box">A</div>
      <div class="brand-text">
        <h2>Antigravity</h2>
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
        <span class="nav-icon">📊</span> Dashboard
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global Flows CB"}
        on:click={() => setTab("Global Flows CB")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global Flows CB")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🏦</span> Global Flows CB
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Global M2"}
        on:click={() => setTab("Global M2")}
        on:keydown={(e) => e.key === "Enter" && setTab("Global M2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">💰</span> Global M2
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "US System"}
        on:click={() => setTab("US System")}
        on:keydown={(e) => e.key === "Enter" && setTab("US System")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🇺🇸</span> US System
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "Risk Model"}
        on:click={() => setTab("Risk Model")}
        on:keydown={(e) => e.key === "Enter" && setTab("Risk Model")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">⚠️</span> Risk Model
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Analysis"}
        on:click={() => setTab("BTC Analysis")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Analysis")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">₿</span> BTC Analysis
      </div>
      <div
        class="nav-item"
        class:active={currentTab === "BTC Quant v2"}
        on:click={() => setTab("BTC Quant v2")}
        on:keydown={(e) => e.key === "Enter" && setTab("BTC Quant v2")}
        role="button"
        tabindex="0"
      >
        <span class="nav-icon">🧪</span> BTC Quant v2
      </div>
    </nav>

    <div class="sidebar-footer">
      <div class="status-indicator">
        <div class="pulse"></div>
        System Live
      </div>
    </div>
  </aside>

  <main class="content">
    <header>
      <div class="content-header">
        <h1>{currentTab} Overview</h1>
        <p>
          Real-time macro liquidity and credit monitoring across 5 major central
          banks
        </p>
      </div>
      <div class="header-actions">
        <div class="source-toggle">
          <button
            class="toggle-btn"
            class:active={$selectedSource === "fred"}
            on:click={toggleSource}
          >
            FRED
          </button>
          <button
            class="toggle-btn"
            class:active={$selectedSource === "tv"}
            on:click={toggleSource}
          >
            TV Hybrid
          </button>
        </div>
        {#if $isLoading}
          <div class="loader"></div>
        {:else}
          <button class="refresh-btn" on:click={fetchData}>Refresh Data</button>
        {/if}
      </div>
    </header>
    {#if $selectedSource === "fred"}
      <div class="source-announcement">
        <span class="info-icon">ℹ️</span>
        <p>
          <strong>Notice:</strong> FRED data utilizes
          <strong>M3 Money Supply</strong> proxies for Global Liquidity calculation.
          This results in higher totals (~60T) compared to Central Bank Assets (~26T)
          used in TV Hybrid.
        </p>
      </div>
    {/if}

    {#if $error}
      <div class="error-banner">
        <strong>Connection Error:</strong>
        {$error}
      </div>
    {/if}

    <div class="dashboard-grid">
      {#if currentTab === "Dashboard"}
        {#if $latestStats}
          <div class="stats-grid">
            <StatsCard
              title="Global Liquidity (GLI)"
              value={$latestStats.gli.value}
              change={$latestStats.gli.change}
              suffix="T"
              icon="🌍"
            />
            <StatsCard
              title="US Net Liquidity"
              value={$latestStats.us_net_liq.value}
              change={$latestStats.us_net_liq.change}
              suffix="T"
              icon="🇺🇸"
            />
            <StatsCard
              title="Credit Index (CLI)"
              value={$latestStats.cli.value}
              change={$latestStats.cli.change}
              suffix="Z"
              icon="💳"
              precision={3}
            />
            <StatsCard
              title="Volatility Index"
              value={$latestStats.vix.value}
              change={$latestStats.vix.change}
              icon="🌪️"
            />
          </div>
        {/if}

        <div class="main-charts">
          <div class="chart-card">
            <div class="chart-header">
              <div class="label-group">
                <h3>Global Liquidity Index (16 Banks)</h3>
                <SignalBadge type={gliSignal} text={gliSignal} />
              </div>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={gliRange}
                  onRangeChange={(r) => (gliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("PBOC")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={gliData} />
            </div>
          </div>

          <div class="chart-card">
            <div class="chart-header">
              <div class="label-group">
                <h3>US Net Liquidity</h3>
                <SignalBadge type={liqSignal} text={liqSignal} />
              </div>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={netLiqRange}
                  onRangeChange={(r) => (netLiqRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("FED")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={netLiqData} />
            </div>
          </div>

          <div class="chart-card wide">
            <div class="chart-header">
              <div class="label-group">
                <h3>Credit Liquidity Index (CLI)</h3>
              </div>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("NFCI")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={cliData} />
            </div>
          </div>
        </div>
      {:else if currentTab === "Global Flows CB"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Global Liquidity Index (Aggregate)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={gliRange}
                  onRangeChange={(r) => (gliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("PBOC")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={gliData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Federal Reserve (Fed)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={fedRange}
                  onRangeChange={(r) => (fedRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("FED")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={fedData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>European Central Bank (ECB)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={ecbRange}
                  onRangeChange={(r) => (ecbRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("ECB")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={ecbData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Bank of Japan (BoJ)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={bojRange}
                  onRangeChange={(r) => (bojRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("BOJ")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={bojData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Bank of England (BoE)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={boeRange}
                  onRangeChange={(r) => (boeRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("BOE")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={boeData} />
            </div>
          </div>
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>People's Bank of China (PBoC)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={pbocRange}
                  onRangeChange={(r) => (pbocRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("PBOC")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={pbocData} />
            </div>
          </div>
        </div>
      {:else if currentTab === "Global M2"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Global Liquidity Index (Aggregate M2 Proxy)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={m2Range}
                  onRangeChange={(r) => (m2Range = r)}
                />
                <span class="last-date">Last Data: {getLastDate("PBOC")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={gliData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>US M2 (Fed)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={fedRange}
                  onRangeChange={(r) => (fedRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("FED")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={fedData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>EU M2 (ECB)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={ecbRange}
                  onRangeChange={(r) => (ecbRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("ECB")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={ecbData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>China M2 (PBoC)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={pbocRange}
                  onRangeChange={(r) => (pbocRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("PBOC")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={pbocData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Japan M2 (BoJ)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={bojRange}
                  onRangeChange={(r) => (bojRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("BOJ")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={bojData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>UK M2 (BoE)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={boeRange}
                  onRangeChange={(r) => (boeRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("BOE")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={boeData} />
            </div>
          </div>
        </div>
      {:else if currentTab === "US System"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>US Net Liquidity Trends</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={netLiqRange}
                  onRangeChange={(r) => (netLiqRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("FED")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={netLiqData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Fed Assets (USD Trillion)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={fedRange}
                  onRangeChange={(r) => (fedRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("FED")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={fedData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>US Credit Conditions</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("NFCI")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={cliData} />
            </div>
          </div>
        </div>
      {:else if currentTab === "Risk Model"}
        <div class="main-charts">
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Credit Risk Premium</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={cliRange}
                  onRangeChange={(r) => (cliRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("NFCI")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={cliData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>Volatility (VIX)</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={vixRange}
                  onRangeChange={(r) => (vixRange = r)}
                />
                <span class="last-date">Last Data: {getLastDate("VIX")}</span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={vixData} />
            </div>
          </div>
          <div class="chart-card">
            <div class="chart-header">
              <h3>High Yield OAS</h3>
              <div class="header-controls">
                <TimeRangeSelector
                  selectedRange={spreadRange}
                  onRangeChange={(r) => (spreadRange = r)}
                />
                <span class="last-date"
                  >Last Data: {getLastDate("HY_SPREAD")}</span
                >
              </div>
            </div>
            <div class="chart-content">
              <Chart data={spreadData} />
            </div>
          </div>
        </div>

        <!-- NEW ROC Section -->
        <div class="roc-section">
          <div class="roc-card">
            <h4>Pulsar Momentum (ROC)</h4>
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
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">US Net Liq</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">Fed Assets</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "1M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "3M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "6M") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.bank_rocs.fed, "1Y") >
                    0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.fed,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.fed, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">PBoC Assets</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.bank_rocs.pboc,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.bank_rocs.pboc, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "Global M2"}
        <div class="main-charts">
          <!-- Global M2 Overview -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>💰 Global M2 Money Supply (5 Major Economies)</h3>
              <span class="last-date">USA + EU + China + Japan + UK</span>
            </div>
            <div class="chart-content">
              <Chart
                data={[
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.total,
                    type: "scatter",
                    mode: "lines",
                    fill: "tozeroy",
                    name: "Global M2",
                    line: { color: "#10b981", width: 2 },
                  },
                ]}
              />
            </div>
          </div>

          <!-- M2 Breakdown by Economy -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>📊 M2 by Economy (Trillions USD)</h3>
            </div>
            <div class="chart-content">
              <Chart
                data={[
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.us,
                    type: "scatter",
                    mode: "lines",
                    name: "USA",
                    line: { color: "#3b82f6", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.cn,
                    type: "scatter",
                    mode: "lines",
                    name: "China",
                    line: { color: "#ef4444", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.eu,
                    type: "scatter",
                    mode: "lines",
                    name: "EU",
                    line: { color: "#f59e0b", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.jp,
                    type: "scatter",
                    mode: "lines",
                    name: "Japan",
                    line: { color: "#8b5cf6", width: 2 },
                  },
                  {
                    x: $dashboardData.dates,
                    y: $dashboardData.m2?.uk,
                    type: "scatter",
                    mode: "lines",
                    name: "UK",
                    line: { color: "#06b6d4", width: 2 },
                  },
                ]}
              />
            </div>
          </div>

          <!-- M2 ROCs -->
          <div class="roc-section">
            <div class="roc-card">
              <h4>M2 Momentum (ROC)</h4>
              <div class="roc-grid">
                <div class="roc-row header">
                  <div class="roc-col">Factor</div>
                  <div class="roc-col">1M</div>
                  <div class="roc-col">3M</div>
                  <div class="roc-col">6M</div>
                  <div class="roc-col">1Y</div>
                </div>
                <div class="roc-row">
                  <div class="roc-col label">Global M2</div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "1M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "1M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "1M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "3M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "3M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "3M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "6M") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "6M") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "6M").toFixed(2)}%
                  </div>
                  <div
                    class="roc-col"
                    class:plus={getLatestROC($dashboardData.m2?.rocs, "1Y") > 0}
                    class:minus={getLatestROC($dashboardData.m2?.rocs, "1Y") <
                      0}
                  >
                    {getLatestROC($dashboardData.m2?.rocs, "1Y").toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "BTC Analysis"}
        <div class="main-charts">
          <!-- BTC Price vs Fair Value -->
          <div class="chart-card wide">
            <div class="chart-header">
              <div class="header-with-toggle">
                <h3>₿ Bitcoin: Price vs Fair Value Model</h3>
                <div class="model-toggle">
                  <button
                    class="toggle-btn"
                    class:active={selectedBtcModel === "macro"}
                    on:click={() => (selectedBtcModel = "macro")}
                  >
                    Macro-Only
                  </button>
                  <button
                    class="toggle-btn"
                    class:active={selectedBtcModel === "adoption"}
                    on:click={() => (selectedBtcModel = "adoption")}
                  >
                    Adoption-Adjusted
                  </button>
                </div>
              </div>
              <span class="last-date">
                {selectedBtcModel === "macro"
                  ? "Liquidity-driven regression"
                  : "Adoption curve + Liquidity regression"}
              </span>
            </div>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart data={btcFairValueData} logScale={true} />
              <div class="debug-chart-info">
                Points: {btcFairValueData[0]?.data?.length || 0}
              </div>
            </div>
          </div>

          <!-- Deviation Stats -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>Current Valuation ({selectedBtcModel.toUpperCase()})</h3>
            </div>
            <div class="btc-stats">
              <div class="btc-stat-item">
                <span class="btc-label">BTC Price</span>
                <span class="btc-value price">
                  ${getLatestValue(
                    $dashboardData.btc?.price,
                  )?.toLocaleString() || "N/A"}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Fair Value</span>
                <span class="btc-value fair">
                  ${Math.round(
                    getLatestValue(activeBtcModel.fair_value) || 0,
                  ).toLocaleString()}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Deviation</span>
                <span
                  class="btc-value deviation"
                  class:overvalued={getLatestValue(
                    activeBtcModel.deviation_pct,
                  ) > 0}
                  class:undervalued={getLatestValue(
                    activeBtcModel.deviation_pct,
                  ) < 0}
                >
                  {getLatestValue(activeBtcModel.deviation_pct)?.toFixed(1) ||
                    "0"}%
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Z-Score</span>
                <span
                  class="btc-value zscore"
                  class:extreme={Math.abs(
                    getLatestValue(activeBtcModel.deviation_zscore) || 0,
                  ) > 2}
                >
                  {getLatestValue(activeBtcModel.deviation_zscore)?.toFixed(
                    2,
                  ) || "0"}σ
                </span>
              </div>
            </div>
          </div>

          <!-- Predictive Signals (CLI vs BTC Lag Correlation) -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>🔮 Predictive Signals: CLI → BTC Lag Analysis</h3>
              <div class="model-toggle">
                <button
                  class="toggle-btn"
                  class:active={selectedLagWindow === "7d"}
                  on:click={() => (selectedLagWindow = "7d")}
                >
                  7D
                </button>
                <button
                  class="toggle-btn"
                  class:active={selectedLagWindow === "14d"}
                  on:click={() => (selectedLagWindow = "14d")}
                >
                  14D
                </button>
                <button
                  class="toggle-btn"
                  class:active={selectedLagWindow === "30d"}
                  on:click={() => (selectedLagWindow = "30d")}
                >
                  30D
                </button>
              </div>
            </div>
            <div class="predictive-stats">
              <div class="pred-stat">
                <span class="pred-label">ROC Window</span>
                <span class="pred-value">{selectedLagWindow.toUpperCase()}</span
                >
              </div>
              <div class="pred-stat">
                <span class="pred-label">Optimal Lag</span>
                <span class="pred-value highlight">
                  {$dashboardData.predictive?.lag_correlations?.[
                    selectedLagWindow
                  ]?.optimal_lag || 0} days
                </span>
              </div>
              <div class="pred-stat">
                <span class="pred-label">Max Correlation</span>
                <span
                  class="pred-value"
                  class:positive={($dashboardData.predictive
                    ?.lag_correlations?.[selectedLagWindow]?.max_corr || 0) > 0}
                  class:negative={($dashboardData.predictive
                    ?.lag_correlations?.[selectedLagWindow]?.max_corr || 0) < 0}
                >
                  {(
                    ($dashboardData.predictive?.lag_correlations?.[
                      selectedLagWindow
                    ]?.max_corr || 0) * 100
                  ).toFixed(2)}%
                </span>
              </div>
              <div class="pred-stat">
                <span class="pred-label">Interpretation</span>
                <span class="pred-value small">
                  {#if ($dashboardData.predictive?.lag_correlations?.[selectedLagWindow]?.optimal_lag || 0) > 0}
                    CLI change today may predict BTC in ~{$dashboardData
                      .predictive?.lag_correlations?.[selectedLagWindow]
                      ?.optimal_lag} days
                  {:else}
                    CLI and BTC move simultaneously
                  {/if}
                </span>
              </div>
            </div>
            <div class="chart-content">
              <Chart data={lagCorrelationChartData} />
            </div>
          </div>

          <!-- Cross-Correlation Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>Cross-Correlation Analysis (90-Day Window)</h3>
              <span class="last-date"
                >Negative lag = indicator leads BTC | Positive lag = BTC leads
                indicator</span
              >
            </div>
            <div class="chart-content">
              <Chart data={correlationData} />
            </div>
          </div>

          <!-- ROC Comparison -->
          <div class="chart-card wide">
            <h4>Momentum Comparison (ROC %)</h4>
            <div class="roc-grid">
              <div class="roc-row header">
                <div class="roc-col">Asset</div>
                <div class="roc-col">1M</div>
                <div class="roc-col">3M</div>
                <div class="roc-col">6M</div>
                <div class="roc-col">1Y</div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">₿ Bitcoin</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.btc?.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.btc?.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.btc?.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">Global GLI</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "3M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "3M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "3M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "6M") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "6M") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "6M").toFixed(2)}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC($dashboardData.gli.rocs, "1Y") > 0}
                  class:minus={getLatestROC($dashboardData.gli.rocs, "1Y") < 0}
                >
                  {getLatestROC($dashboardData.gli.rocs, "1Y").toFixed(2)}%
                </div>
              </div>
              <div class="roc-row">
                <div class="roc-col label">US Net Liq</div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "3M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "3M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "6M",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "6M").toFixed(
                    2,
                  )}%
                </div>
                <div
                  class="roc-col"
                  class:plus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) > 0}
                  class:minus={getLatestROC(
                    $dashboardData.us_net_liq_rocs,
                    "1Y",
                  ) < 0}
                >
                  {getLatestROC($dashboardData.us_net_liq_rocs, "1Y").toFixed(
                    2,
                  )}%
                </div>
              </div>
            </div>
          </div>

          <!-- Interpretation Panel -->
          <div class="chart-card wide interpretation-panel">
            <h4>📊 Model Interpretation</h4>
            <div class="interpretation-grid">
              <div class="interp-card">
                <h5>Fair Value Model</h5>
                <p>
                  Regression using:<br />
                  • GLI (45-day lag)<br />
                  • CLI (14-day lag)<br />
                  • VIX (coincident)<br />
                  • US Net Liq (30-day lag)
                </p>
              </div>
              <div class="interp-card">
                <h5>Deviation Zones</h5>
                <p>
                  • <span class="extreme-zone">±2σ:</span> Extreme
                  over/undervaluation<br />
                  • <span class="moderate-zone">±1σ:</span> Moderate deviation<br
                  />
                  • Within ±1σ: Fair value range
                </p>
              </div>
              <div class="interp-card">
                <h5>Trading Signals</h5>
                <p>
                  • <strong>Z &gt; +2:</strong> Consider profit-taking<br />
                  • <strong>Z &lt; -2:</strong> Potential accumulation<br />
                  • <strong>ROC divergence:</strong> Momentum shifts
                </p>
              </div>
            </div>
          </div>
        </div>
      {:else if currentTab === "BTC Quant v2"}
        <div class="main-charts">
          <!-- Quant v2 Model Description -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>🧪 Quant v2: Enhanced Bitcoin Fair Value Model</h3>
              <span class="last-date"
                >Weekly Δlog returns + ElasticNet + PCA GLI Factor</span
              >
            </div>
            <div class="quant-description">
              <p>
                This model addresses econometric issues in the legacy model:
              </p>
              <ul>
                <li>
                  <strong>Weekly frequency</strong> (W-FRI) instead of daily to avoid
                  ffill autocorrelation
                </li>
                <li>
                  <strong>Δlog(BTC) returns</strong> instead of log levels (avoids
                  spurious regression)
                </li>
                <li>
                  <strong>ElasticNet</strong> with 1-8 week lags for automatic feature
                  selection
                </li>
                <li>
                  <strong>PCA GLI factor</strong> instead of raw sum (handles colinearity)
                </li>
                <li>
                  <strong>Rolling 52-week volatility</strong> for adaptive bands
                </li>
              </ul>
            </div>
          </div>

          <!-- OOS Metrics Panel -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>📈 Out-of-Sample Metrics</h3>
            </div>
            <div class="quant-metrics">
              <div class="metric-item">
                <span class="metric-label">OOS RMSE</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.oos_rmse || 0
                  ).toFixed(4)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">OOS MAE</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.oos_mae || 0
                  ).toFixed(4)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Hit Rate</span>
                <span class="metric-value highlight"
                  >{(
                    ($dashboardData.btc?.models?.quant_v2?.metrics?.hit_rate ||
                      0) * 100
                  ).toFixed(2)}%</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">R² In-Sample</span>
                <span class="metric-value"
                  >{(
                    ($dashboardData.btc?.models?.quant_v2?.metrics
                      ?.r2_insample || 0) * 100
                  ).toFixed(2)}%</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Active Features</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.metrics
                    ?.n_active_features || 0}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">Frequency</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.frequency ||
                    "weekly"}</span
                >
              </div>
            </div>
          </div>

          <!-- Model Parameters -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>⚙️ Model Parameters</h3>
            </div>
            <div class="quant-metrics">
              <div class="metric-item">
                <span class="metric-label">Alpha (λ)</span>
                <span class="metric-value"
                  >{(
                    $dashboardData.btc?.models?.quant_v2?.metrics?.alpha || 0
                  ).toFixed(6)}</span
                >
              </div>
              <div class="metric-item">
                <span class="metric-label">L1 Ratio</span>
                <span class="metric-value"
                  >{$dashboardData.btc?.models?.quant_v2?.metrics?.l1_ratio ||
                    0}</span
                >
              </div>
            </div>
          </div>

          <!-- Fair Value Chart (Cumulative) -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>₿ Bitcoin: Quant v2 Fair Value (Weekly - Cumulative)</h3>
              <span class="last-date"
                >⚠️ Cumulative drift may cause divergence over time</span
              >
            </div>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart data={quantV2ChartData} logScale={true} />
            </div>
          </div>

          <!-- Rebalanced Fair Value Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>₿ Bitcoin: Rebalanced Fair Value (Quarterly Reset)</h3>
              <span class="last-date"
                >✅ Resets to actual price every 13 weeks to avoid drift</span
              >
            </div>
            <div class="chart-content tv-chart-wrap">
              <LightweightChart data={quantV2RebalancedData} logScale={true} />
            </div>
          </div>

          <!-- Returns Comparison Chart -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>📊 Weekly Returns: Predicted vs Actual (%)</h3>
              <span class="last-date"
                >Orange bars = Actual | Green line = Predicted</span
              >
            </div>
            <div class="chart-content">
              <Chart data={quantV2ReturnsData} />
            </div>
          </div>

          <!-- Active Features List -->
          <div class="chart-card wide">
            <div class="chart-header">
              <h3>🎯 Active Features (Selected by ElasticNet)</h3>
            </div>
            <div class="features-grid">
              {#each Object.entries($dashboardData.btc?.models?.quant_v2?.active_features || {}) as [feature, coef]}
                <div
                  class="feature-item"
                  class:positive={coef > 0}
                  class:negative={coef < 0}
                >
                  <span class="feature-name">{feature}</span>
                  <span class="feature-coef">{coef.toFixed(4)}</span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Current Valuation -->
          <div class="chart-card">
            <div class="chart-header">
              <h3>📊 Current Valuation (Quant v2)</h3>
            </div>
            <div class="btc-stats">
              <div class="btc-stat-item">
                <span class="btc-label">BTC Price</span>
                <span class="btc-value price">
                  ${getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.btc_price,
                  )?.toLocaleString() || "N/A"}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Fair Value</span>
                <span class="btc-value fair">
                  ${Math.round(
                    getLatestValue(
                      $dashboardData.btc?.models?.quant_v2?.fair_value,
                    ) || 0,
                  ).toLocaleString()}
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Deviation</span>
                <span
                  class="btc-value deviation"
                  class:overvalued={getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  ) > 0}
                  class:undervalued={getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  ) < 0}
                >
                  {getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_pct,
                  )?.toFixed(1) || "0"}%
                </span>
              </div>
              <div class="btc-stat-item">
                <span class="btc-label">Z-Score</span>
                <span
                  class="btc-value zscore"
                  class:extreme={Math.abs(
                    getLatestValue(
                      $dashboardData.btc?.models?.quant_v2?.deviation_zscore,
                    ) || 0,
                  ) > 2}
                >
                  {getLatestValue(
                    $dashboardData.btc?.models?.quant_v2?.deviation_zscore,
                  )?.toFixed(2) || "0"}σ
                </span>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #f8fafc;
    color: #0f172a;
    font-family:
      "Inter",
      -apple-system,
      system-ui,
      sans-serif;
    overflow-x: hidden;
  }

  .app-container {
    display: flex;
    min-height: 100vh;
    width: 100vw;
  }

  .sidebar {
    width: 280px;
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
    display: flex;
    flex-direction: column;
    padding: 40px 24px;
    flex-shrink: 0;
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
    color: #0f172a;
  }

  .brand-text span {
    font-size: 0.75rem;
    color: #64748b;
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
    color: #64748b;
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
    background: #f1f5f9;
    color: #0f172a;
  }

  .nav-item.active {
    background: #eef2ff;
    color: #4f46e5;
    font-weight: 600;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 0 8px;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.8125rem;
    color: #64748b;
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
    padding: 48px;
    overflow-y: auto;
    background: #f8fafc;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;
    max-width: 1600px;
    margin-right: auto;
  }

  .content-header h1 {
    margin: 0 0 4px 0;
    font-size: 2.25rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.025em;
  }

  .content-header p {
    margin: 0;
    color: #64748b;
    font-size: 1.125rem;
  }

  .refresh-btn {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #0f172a;
    padding: 10px 20px;
    border-radius: 12px;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }

  .refresh-btn:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
    transform: translateY(-1px);
  }

  .source-toggle {
    display: flex;
    background: #f1f5f9;
    padding: 4px;
    border-radius: 12px;
    margin-right: 16px;
  }

  .toggle-btn {
    border: none;
    background: transparent;
    padding: 6px 16px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    color: #64748b;
    transition: all 0.2s;
  }

  .toggle-btn.active {
    background: #ffffff;
    color: #4f46e5;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  /* Specificity fix for Indigo theme on dark toggle */
  .model-toggle .toggle-btn.active {
    background: #6366f1;
    color: white !important;
  }

  .source-announcement {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    padding: 10px 16px;
    border-radius: 12px;
    margin-top: 16px;
    animation: slideDown 0.3s ease-out;
  }

  .source-announcement p {
    font-size: 0.75rem;
    color: #1e40af;
    line-height: 1.4;
    margin: 0;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
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

  .dashboard-grid {
    max-width: 1600px;
    margin-right: auto;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 32px;
    margin-bottom: 40px;
  }

  .main-charts {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 32px;
  }

  .chart-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 24px;
    padding: 32px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .wide {
    grid-column: span 2;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
  }

  .chart-header h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 700;
    color: #1e293b;
  }

  .last-date {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
    background: #f1f5f9;
    padding: 4px 10px;
    border-radius: 6px;
  }

  .header-with-toggle {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .model-toggle {
    display: flex;
    gap: 8px;
    background: #f1f5f9;
    padding: 4px;
    border-radius: 8px;
    width: fit-content;
  }

  .model-toggle .toggle-btn {
    padding: 6px 16px;
    font-size: 0.75rem;
    border: none; /* Reset boarder from base .toggle-btn */
    background: transparent;
    color: #64748b;
    box-shadow: none;
  }

  .model-toggle .toggle-btn.active {
    background: #ffffff;
    color: #6366f1;
    font-weight: 700;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }

  /* Specificity fix for Indigo theme on dark toggle */
  .model-toggle .toggle-btn.active {
    background: #6366f1;
    color: white !important;
  }

  .roc-section {
    margin-top: 40px;
    max-width: 1600px;
  }

  .roc-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 24px;
    padding: 32px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }

  .roc-card h4 {
    margin: 0 0 24px 0;
    font-size: 1.25rem;
    font-weight: 800;
    color: #0f172a;
  }

  .roc-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .roc-row {
    display: grid;
    grid-template-columns: 2fr repeat(4, 1fr);
    padding: 12px 16px;
    border-radius: 12px;
    align-items: center;
  }

  .roc-row.header {
    background: #f8fafc;
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .roc-col.label {
    font-weight: 600;
    color: #1e293b;
  }

  .roc-col.plus {
    color: #059669;
    font-weight: 700;
  }

  .roc-col.minus {
    color: #dc2626;
    font-weight: 700;
  }

  .label-group {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .chart-content {
    min-height: 500px;
    height: 500px;
    flex: none; /* Force fixed height to rule out flex issues */
    width: 100%;
    position: relative;
    overflow: hidden;
  }

  .debug-chart-info {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.4);
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    pointer-events: none;
    z-index: 100;
  }

  .loader {
    width: 28px;
    height: 28px;
    border: 3px solid #f1f5f9;
    border-top-color: #4f46e5;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* Quant v2 Tab Styles */
  .quant-description {
    padding: 16px;
    background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
    border-radius: 8px;
    border-left: 4px solid #10b981;
  }

  .quant-description p {
    margin: 0 0 12px 0;
    color: #065f46;
    font-weight: 500;
  }

  .quant-description ul {
    margin: 0;
    padding-left: 20px;
    color: #047857;
  }

  .quant-description li {
    margin-bottom: 6px;
    line-height: 1.5;
  }

  .quant-metrics {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px;
    background: #f8fafc;
    border-radius: 8px;
  }

  .metric-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
  }

  .metric-value {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
  }

  .metric-value.highlight {
    color: #10b981;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    padding: 16px;
  }

  .feature-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: #f8fafc;
    border-radius: 6px;
    border-left: 3px solid #94a3b8;
  }

  .feature-item.positive {
    border-left-color: #10b981;
    background: #f0fdf4;
  }

  .feature-item.negative {
    border-left-color: #ef4444;
    background: #fef2f2;
  }

  .feature-name {
    font-size: 13px;
    font-weight: 500;
    color: #334155;
  }

  .feature-coef {
    font-size: 13px;
    font-weight: 600;
    font-family: "Monaco", "Consolas", monospace;
    color: #475569;
  }

  .feature-item.positive .feature-coef {
    color: #059669;
  }

  .feature-item.negative .feature-coef {
    color: #dc2626;
  }

  @media (max-width: 1200px) {
    .main-charts {
      grid-template-columns: 1fr;
    }
    .wide {
      grid-column: span 1;
    }
  }

  /* BTC Analysis Styles */
  .btc-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 24px;
  }

  .btc-stat-item {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }

  .btc-label {
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .btc-value {
    font-size: 24px;
    font-weight: 700;
    color: #0f172a;
  }

  .btc-value.price {
    color: #f7931a;
  }

  .btc-value.fair {
    color: #10b981;
  }

  .btc-value.deviation.overvalued {
    color: #ef4444;
  }

  .btc-value.deviation.undervalued {
    color: #10b981;
  }

  .btc-value.zscore.extreme {
    color: #dc2626;
    animation: pulse 2s ease-in-out infinite;
  }

  .interpretation-panel {
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 2px solid #fbbf24;
  }

  .interpretation-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .interp-card {
    background: white;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #f59e0b;
  }

  .interp-card h5 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #92400e;
  }

  .interp-card p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: #78350f;
  }

  .extreme-zone {
    color: #dc2626;
    font-weight: 600;
  }

  .moderate-zone {
    color: #f59e0b;
    font-weight: 600;
  }

  @media (max-width: 1200px) {
    .interpretation-grid {
      grid-template-columns: 1fr;
    }
    .btc-stats {
      grid-template-columns: 1fr;
    }
  }

  /* Predictive Signals Stats */
  .predictive-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    padding: 16px;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-radius: 8px;
    margin-bottom: 16px;
  }

  .pred-stat {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .pred-label {
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
  }

  .pred-value {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
  }

  .pred-value.highlight {
    color: #6366f1;
  }

  .pred-value.positive {
    color: #10b981;
  }

  .pred-value.negative {
    color: #ef4444;
  }

  .pred-value.small {
    font-size: 13px;
    font-weight: 500;
    color: #475569;
  }

  @media (max-width: 900px) {
    .predictive-stats {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .app-container {
      flex-direction: column;
    }
    .sidebar {
      width: 100%;
      height: auto;
      padding: 24px;
      border-right: none;
      border-bottom: 1px solid #e2e8f0;
    }
    .content {
      padding: 24px;
    }
  }
</style>
