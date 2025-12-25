<script>
    import { onMount } from "svelte";
    import { createChart, LineSeries, AreaSeries } from "lightweight-charts";

    let { data = [], title = "", logScale = false } = $props();

    let container;
    let currentData;
    let currentLogScale;

    const api = {
        chart: null,
        seriesMap: new Map(),
    };

    const colors = {
        background: "#ffffff",
        text: "#475569",
        grid: "rgba(226, 232, 240, 0.4)",
    };

    onMount(() => {
        if (!container) return;

        api.chart = createChart(container, {
            layout: {
                background: { color: colors.background },
                textColor: colors.text,
                fontFamily: "Inter, -apple-system, system-ui, sans-serif",
                fontSize: 12,
            },
            grid: {
                vertLines: { color: colors.grid },
                horzLines: { color: colors.grid },
            },
            crosshair: {
                mode: 0,
                vertLine: {
                    labelBackgroundColor: "#1e293b",
                    color: "rgba(99, 102, 241, 0.4)",
                    width: 1,
                    style: 2,
                },
                horzLine: {
                    labelBackgroundColor: "#1e293b",
                    color: "rgba(99, 102, 241, 0.4)",
                    width: 1,
                    style: 2,
                },
            },
            rightPriceScale: {
                borderColor: "rgba(226, 232, 240, 0.8)",
                mode: logScale ? 1 : 0,
                autoScale: true,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            timeScale: {
                borderColor: "rgba(226, 232, 240, 0.8)",
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 10,
                barSpacing: 6,
            },
        });

        currentData = data;
        currentLogScale = logScale;

        updateSeries();

        const handleResize = () => {
            if (api.chart && container && container.clientWidth > 0) {
                api.chart.applyOptions({
                    width: container.clientWidth,
                    height: container.clientHeight,
                });
                api.chart.timeScale().fitContent();
            }
        };

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        setTimeout(handleResize, 100);
        setTimeout(handleResize, 400);
        setTimeout(handleResize, 1000);

        return () => {
            resizeObserver.disconnect();
            if (api.chart) {
                api.chart.remove();
                api.chart = null;
            }
        };
    });

    function updateSeries() {
        if (!api.chart) return;

        api.seriesMap.forEach((s) => api.chart.removeSeries(s));
        api.seriesMap.clear();

        if (!data || data.length === 0) return;

        data.forEach((sConfig) => {
            if (!sConfig.data || sConfig.data.length === 0) return;

            try {
                let series;
                const seriesType =
                    sConfig.type === "area" ? AreaSeries : LineSeries;

                const options = {
                    color: sConfig.color,
                    lineWidth: sConfig.width || 2,
                    priceLineVisible: false,
                    lastValueVisible: true,
                    title: sConfig.name,
                    ...sConfig.options,
                };

                if (sConfig.type === "area") {
                    options.lineColor = sConfig.color;
                    options.topColor = sConfig.topColor || sConfig.color;
                    options.bottomColor = sConfig.bottomColor || "transparent";
                }

                series = api.chart.addSeries(seriesType, options);
                series.setData(sConfig.data);
                api.seriesMap.set(sConfig.name, series);
            } catch (e) {
                console.error(`Failed to add series ${sConfig.name}:`, e);
            }
        });

        api.chart.timeScale().fitContent();
    }

    $effect.pre(() => {
        // Create a key that includes series names and sample values to detect deep changes
        const getSeriesKey = (seriesArr) => {
            if (!seriesArr) return "";
            return seriesArr
                .map((s) => {
                    const vals = s.data || [];
                    // Include first, last, and a middle value for change detection
                    const sample =
                        vals.length > 0
                            ? [
                                  vals[0]?.value,
                                  vals[Math.floor(vals.length / 2)]?.value,
                                  vals[vals.length - 1]?.value,
                              ]
                            : [];
                    return `${s.name}:${vals.length}:${JSON.stringify(sample)}`;
                })
                .join("|");
        };

        const dataKey = getSeriesKey(data);
        const currentDataKey = getSeriesKey(currentData);

        if (api.chart && dataKey !== currentDataKey) {
            currentData = data;
            updateSeries();
        }

        if (api.chart && logScale !== currentLogScale) {
            currentLogScale = logScale;
            api.chart.priceScale("right").applyOptions({
                mode: logScale ? 1 : 0,
            });
        }
    });
</script>

<div class="chart-container-wrapper">
    {#if title}
        <div class="chart-title">{title}</div>
    {/if}
    <div bind:this={container} class="chart-container"></div>
</div>

<style>
    .chart-container-wrapper {
        display: flex;
        flex-direction: column;
        width: 100%;
        height: 100%;
        min-height: 450px;
        position: relative;
        background: #ffffff;
    }

    .chart-container {
        flex: 1;
        width: 100%;
        height: 100%;
    }

    .chart-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
        padding-left: 4px;
    }
</style>
