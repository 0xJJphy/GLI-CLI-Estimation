<script>
    import { onMount } from "svelte";
    import {
        createChart,
        LineSeries,
        AreaSeries,
        HistogramSeries,
    } from "lightweight-charts";

    let {
        data = [],
        title = "",
        logScale = false,
        darkMode = false,
    } = $props();

    let container;
    let currentData;
    let currentLogScale;
    let currentDarkMode;

    const api = {
        chart: null,
        seriesMap: new Map(),
    };

    // Theme-aware colors
    const getColors = (isDark) => ({
        background: isDark ? "#1e293b" : "#ffffff",
        text: isDark ? "#cbd5e1" : "#475569",
        grid: isDark ? "rgba(71, 85, 105, 0.3)" : "rgba(226, 232, 240, 0.4)",
        crosshairLabel: isDark ? "#334155" : "#1e293b",
        crosshairLine: isDark
            ? "rgba(99, 102, 241, 0.5)"
            : "rgba(99, 102, 241, 0.4)",
        border: isDark ? "rgba(71, 85, 105, 0.5)" : "rgba(226, 232, 240, 0.8)",
    });

    onMount(() => {
        if (!container) return;

        const colors = getColors(darkMode);

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
                    labelBackgroundColor: colors.crosshairLabel,
                    color: colors.crosshairLine,
                    width: 1,
                    style: 2,
                },
                horzLine: {
                    labelBackgroundColor: colors.crosshairLabel,
                    color: colors.crosshairLine,
                    width: 1,
                    style: 2,
                },
            },
            rightPriceScale: {
                borderColor: colors.border,
                mode: logScale ? 1 : 0,
                autoScale: true,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            timeScale: {
                borderColor: colors.border,
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 10,
                barSpacing: 6,
            },
        });

        currentData = data;
        currentLogScale = logScale;
        currentDarkMode = darkMode;

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
                let seriesType;
                switch (sConfig.type) {
                    case "area":
                        seriesType = AreaSeries;
                        break;
                    case "histogram":
                        seriesType = HistogramSeries;
                        break;
                    default:
                        seriesType = LineSeries;
                }

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

    function updateTheme() {
        if (!api.chart) return;

        const colors = getColors(darkMode);

        api.chart.applyOptions({
            layout: {
                background: { color: colors.background },
                textColor: colors.text,
            },
            grid: {
                vertLines: { color: colors.grid },
                horzLines: { color: colors.grid },
            },
            crosshair: {
                vertLine: {
                    labelBackgroundColor: colors.crosshairLabel,
                    color: colors.crosshairLine,
                },
                horzLine: {
                    labelBackgroundColor: colors.crosshairLabel,
                    color: colors.crosshairLine,
                },
            },
            rightPriceScale: {
                borderColor: colors.border,
            },
            timeScale: {
                borderColor: colors.border,
            },
        });
    }

    $effect.pre(() => {
        // Read props at top level for Svelte 5 reactivity tracking
        const currentDarkModeValue = darkMode;
        const currentLogScaleValue = logScale;
        const currentDataValue = data;

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

        const dataKey = getSeriesKey(currentDataValue);
        const currentDataKey = getSeriesKey(currentData);

        if (api.chart && dataKey !== currentDataKey) {
            currentData = currentDataValue;
            updateSeries();
        }

        if (api.chart && currentLogScaleValue !== currentLogScale) {
            currentLogScale = currentLogScaleValue;
            api.chart.priceScale("right").applyOptions({
                mode: currentLogScaleValue ? 1 : 0,
            });
        }

        if (api.chart && currentDarkModeValue !== currentDarkMode) {
            currentDarkMode = currentDarkModeValue;
            updateTheme();
        }
    });
</script>

<div class="chart-container-wrapper" class:dark={darkMode}>
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
        background: var(--bg-secondary, #ffffff);
        transition: background-color 0.3s ease;
    }

    .chart-container-wrapper.dark {
        background: #1e293b;
    }

    .chart-container {
        flex: 1;
        width: 100%;
        height: 100%;
    }

    .chart-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--text-primary, #1e293b);
        margin-bottom: 8px;
        padding-left: 4px;
    }
</style>
