<!--
  ChartStack.svelte
  
  A component for rendering a main chart with N stacked indicator subplots below.
  Uses Plotly's domain-based subplots (single chart instance, multiple y-axes).
  
  Props:
  - mainData: PlotlyTrace[] - Main chart data (yaxis: "y")
  - subcharts: SubchartConfig[] - Subchart configs (data assigned to yaxis: "y2", "y3", etc.)
  - height: number - Total chart height in pixels
  - mainRatio: number - Fraction of height for main chart (default: 0.75)
  - darkMode: boolean
  
  Usage:
  <ChartStack
    mainData={corridorData}
    subcharts={[
      { key: "srf_usage", data: srfData, yaxisTitle: "SRF ($B)" }
    ]}
    height={400}
    mainRatio={0.75}
    {darkMode}
  />
-->
<script>
    import Chart from "./Chart.svelte";

    /**
     * @typedef {Object} SubchartConfig
     * @property {string} key - Unique identifier
     * @property {any[]} data - Plotly trace data (will be assigned to y2, y3, etc.)
     * @property {string} [yaxisTitle] - Y-axis title
     * @property {boolean} [showGrid] - Show grid lines (default: false)
     */

    /** @type {any[]} */
    export let mainData = [];

    /** @type {SubchartConfig[]} */
    export let subcharts = [];

    /** @type {number} */
    export let height = 400;

    /** @type {number} - Fraction of height for main chart (0-1) */
    export let mainRatio = 0.75;

    /** @type {boolean} */
    export let darkMode = false;

    /** @type {string} */
    export let mainYAxisTitle = "";

    /** @type {boolean} */
    export let showLegend = false;

    // Gap between charts (8% of total height)
    const gapRatio = 0.08;

    // ...

    // Build combined layout with all y-axes
    $: combinedLayout = {
        height: height,
        xaxis: {
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            showticklabels: true,
        },
        // Main y-axis
        yaxis: {
            title: mainYAxisTitle,
            domain: domains.main,
            anchor: "x",
            gridcolor: darkMode ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
        },
        // Dynamic subchart y-axes
        ...Object.fromEntries(
            subcharts.map((config, i) => [
                `yaxis${i + 2}`,
                {
                    title: config.yaxisTitle || "",
                    domain: domains.subs[i] || [0, 0.2],
                    anchor: "x",
                    gridcolor:
                        config.showGrid !== false
                            ? darkMode
                                ? "rgba(255,255,255,0.03)"
                                : "rgba(0,0,0,0.03)"
                            : "transparent",
                    rangemode: "tozero",
                    fixedrange: true,
                    side: "right",
                },
            ]),
        ),
        margin: { t: 10, r: 50, l: 50, b: 40 },
        showlegend: showLegend,
        legend: showLegend
            ? {
                  orientation: "h",
                  yanchor: "bottom",
                  y: 1.02,
                  xanchor: "center",
                  x: 0.5,
              }
            : undefined,
    };
</script>

<div class="chart-stack-wrapper" style="height: {height}px">
    <Chart data={combinedData} layout={combinedLayout} {darkMode} />
</div>

<style>
    .chart-stack-wrapper {
        width: 100%;
        overflow: hidden;
    }

    .chart-stack-wrapper :global(.chart-content),
    .chart-stack-wrapper :global(.chart-wrapper) {
        width: 100% !important;
        height: 100% !important;
    }
</style>
