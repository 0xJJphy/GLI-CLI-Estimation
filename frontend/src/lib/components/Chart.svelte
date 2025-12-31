<script>
    import { onMount, afterUpdate } from "svelte";
    import Plotly from "plotly.js-dist-min";

    export let data = [];
    export let layout = {};
    export let config = { responsive: true, displayModeBar: false };
    export let yType = "linear";
    export let darkMode = false;
    export let divId =
        "plotly-chart-" + Math.random().toString(36).substr(2, 9);

    let chartContainer;

    // Theme-aware colors
    const getLayout = (isDark) => ({
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: {
            color: isDark ? "#cbd5e1" : "#1e293b",
            family: "Inter, sans-serif",
        },
        margin: { t: 40, r: 20, l: 60, b: 40 },
        xaxis: {
            gridcolor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            zeroline: false,
            color: isDark ? "#94a3b8" : "#64748b",
        },
        yaxis: {
            gridcolor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            zeroline: false,
            color: isDark ? "#94a3b8" : "#64748b",
        },
        legend: {
            orientation: "h",
            yanchor: "bottom",
            y: 1.02,
            xanchor: "right",
            x: 1,
            font: {
                color: isDark ? "#cbd5e1" : "#1e293b",
            },
        },
    });

    onMount(() => {
        const processedData = data.map((trace) => ({
            ...trace,
            connectgaps: true,
        }));

        const defaultLayout = getLayout(darkMode);

        Plotly.newPlot(
            chartContainer,
            processedData,
            {
                ...defaultLayout,
                yaxis: { ...defaultLayout.yaxis, type: yType, autorange: true },
                ...layout,
            },
            config,
        );

        const resizeObserver = new ResizeObserver(() => {
            Plotly.Plots.resize(chartContainer);
        });
        resizeObserver.observe(chartContainer);

        return () => {
            resizeObserver.disconnect();
            Plotly.purge(chartContainer);
        };
    });

    afterUpdate(() => {
        const processedData = data.map((trace) => ({
            ...trace,
            connectgaps: true,
        }));

        const defaultLayout = getLayout(darkMode);

        Plotly.react(
            chartContainer,
            processedData,
            {
                ...defaultLayout,
                yaxis: { ...defaultLayout.yaxis, type: yType, autorange: true },
                ...layout,
            },
            config,
        );
    });
</script>

<div bind:this={chartContainer} class="chart-wrapper"></div>

<style>
    .chart-wrapper {
        width: 100%;
        height: 100%;
        min-height: 100%;
    }
</style>
