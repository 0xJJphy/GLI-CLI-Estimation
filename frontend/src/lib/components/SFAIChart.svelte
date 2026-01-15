<script>
    import { onMount } from "svelte";
    import {
        createChart,
        LineSeries,
        HistogramSeries,
        createTextWatermark,
        createImageWatermark,
    } from "lightweight-charts";
    import {
        showWatermark,
        watermarkType,
    } from "../../stores/settingsStore.js";
    import { get } from "svelte/store";

    let {
        btcData = [],
        regimeData = [],
        indicatorData = [],
        indicatorMode = "regime",
        darkMode = false,
    } = $props();

    let container;
    let chart = null;
    let btcSeries = null;
    let indicatorSeries = null;
    let watermark = null;

    const api = {
        chart: null,
        watermark: null,
    };

    // Helper to create watermark with current theme and type
    const createWatermarkWithTheme = (isDark) => {
        if (!api.chart) return;
        if (api.watermark) {
            api.watermark.detach();
            api.watermark = null;
        }
        if (get(showWatermark)) {
            const wmType = get(watermarkType);
            if (wmType === "image") {
                const logoSrc = isDark ? "/logo-white.png" : "/logo.png";
                api.watermark = createImageWatermark(
                    api.chart.panes()[0],
                    logoSrc,
                    {
                        alpha: isDark ? 0.15 : 0.12,
                        padding: 20,
                    },
                );
            } else {
                api.watermark = createTextWatermark(api.chart.panes()[0], {
                    horzAlign: "center",
                    vertAlign: "center",
                    lines: [
                        {
                            text: "0xJJphy",
                            color: isDark
                                ? "rgba(255, 255, 255, 0.18)"
                                : "rgba(0, 0, 0, 0.10)",
                            fontSize: 48,
                            fontFamily: "JetBrains Mono",
                        },
                    ],
                });
            }
        }
    };

    // Subscribe to watermark stores for reactivity
    const unsubWatermark = showWatermark.subscribe(() => {
        if (api.chart) createWatermarkWithTheme(darkMode);
    });

    const unsubWatermarkType = watermarkType.subscribe(() => {
        if (api.chart) createWatermarkWithTheme(darkMode);
    });

    // Regime colors
    const regimeColors = {
        0: "rgba(107, 114, 128, 0.15)",
        1: "rgba(34, 197, 94, 0.25)",
        2: "rgba(239, 68, 68, 0.25)",
        3: "rgba(59, 130, 246, 0.25)",
        4: "rgba(139, 92, 246, 0.25)",
    };

    // Theme colors
    const getColors = (isDark) => ({
        background: isDark ? "#050505" : "#ffffff",
        text: isDark ? "#cbd5e1" : "#475569",
        grid: isDark ? "rgba(255, 255, 255, 0.03)" : "rgba(0, 0, 0, 0.03)",
    });

    onMount(() => {
        if (!container) return;

        const colors = getColors(darkMode);

        api.chart = createChart(container, {
            layout: {
                background: { color: colors.background },
                textColor: colors.text,
                fontFamily: "JetBrains Mono",
                fontSize: 11,
            },
            grid: {
                vertLines: { color: colors.grid, style: 2 },
                horzLines: { color: colors.grid, style: 2 },
            },
            rightPriceScale: {
                mode: 1, // Log scale
                autoScale: true,
                visible: true,
                scaleMargins: { top: 0.05, bottom: 0.25 },
            },
            leftPriceScale: {
                autoScale: true,
                visible: true,
                scaleMargins: { top: 0.8, bottom: 0.02 },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                rightOffset: 5,
                barSpacing: 4,
            },
            crosshair: { mode: 0 },
            handleScale: { mouseWheel: true, pinch: true },
            handleScroll: { mouseWheel: true, horzTouchDrag: true },
        });

        // Create watermark
        createWatermarkWithTheme(darkMode);

        // BTC Series (main pane, right scale)
        btcSeries = api.chart.addSeries(LineSeries, {
            color: "#f7931a",
            lineWidth: 2,
            priceScaleId: "right",
            priceLineVisible: false,
            lastValueVisible: true,
            title: "BTC",
        });

        // Indicator Series (bottom, left scale)
        indicatorSeries = api.chart.addSeries(HistogramSeries, {
            priceScaleId: "left",
            priceLineVisible: false,
            lastValueVisible: false,
            title: "",
        });

        updateData();

        const handleResize = () => {
            if (api.chart && container && container.clientWidth > 0) {
                api.chart.applyOptions({
                    width: container.clientWidth,
                    height: container.clientHeight,
                });
            }
        };

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        setTimeout(handleResize, 100);
        setTimeout(() => api.chart?.timeScale().fitContent(), 200);

        return () => {
            resizeObserver.disconnect();
            unsubWatermark();
            unsubWatermarkType();
            if (api.chart) {
                api.chart.remove();
                api.chart = null;
            }
        };
    });

    function updateData() {
        if (!api.chart || !btcSeries || !indicatorSeries) return;

        // Update BTC data
        if (btcData.length > 0) {
            btcSeries.setData(btcData);
        }

        // Update indicator data with colors
        if (indicatorData.length > 0) {
            indicatorSeries.setData(indicatorData);
        }

        // Fit content after data update
        setTimeout(() => api.chart?.timeScale().fitContent(), 50);
    }

    // React to data changes
    $effect(() => {
        if (btcData && indicatorData && api.chart) {
            updateData();
        }
    });

    // React to theme changes
    $effect(() => {
        if (api.chart && darkMode !== undefined) {
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
            });
            // Recreate watermark with new theme colors
            createWatermarkWithTheme(darkMode);
        }
    });
</script>

<div
    bind:this={container}
    class="sfai-chart-container"
    class:dark={darkMode}
></div>

<style>
    .sfai-chart-container {
        width: 100%;
        height: 100%;
        min-height: 350px;
        background: var(--bg-secondary, #ffffff);
    }

    .sfai-chart-container.dark {
        background: #050505;
    }
</style>
