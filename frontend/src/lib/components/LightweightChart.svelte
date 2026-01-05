<script>
    import { onMount } from "svelte";
    import { get } from "svelte/store";
    import {
        createChart,
        LineSeries,
        AreaSeries,
        HistogramSeries,
        createTextWatermark,
        createImageWatermark,
    } from "lightweight-charts";
    import {
        showWatermark,
        watermarkType,
    } from "../../stores/settingsStore.js";

    let {
        data = [],
        title = "",
        logScale = false,
        darkMode = false,
        showActions = true,
    } = $props();

    /**
     * Resets both Left and Right price scales to auto-scale mode.
     */
    export const resetScales = () => {
        if (!api.chart) return;
        api.chart.priceScale("left").applyOptions({ autoScale: true });
        api.chart.priceScale("right").applyOptions({ autoScale: true });
        api.chart.timeScale().fitContent();
    };

    /**
     * Downloads the chart as a PNG image.
     */
    export const downloadChart = () => {
        if (!api.chart) return;
        const canvas = api.chart.takeScreenshot();
        const dataURL = canvas.toDataURL("image/png");
        const link = document.createElement("a");
        link.download = `${title || "chart"}.png`;
        link.href = dataURL;
        link.click();
    };

    /**
     * Toggles fullscreen mode for the chart container.
     */
    export const toggleFullscreen = () => {
        if (!container) return;
        const wrapper = container.parentElement;
        if (!document.fullscreenElement) {
            wrapper.requestFullscreen().catch((err) => {
                console.error(
                    `Error attempting to enable fullscreen: ${err.message}`,
                );
            });
        } else {
            document.exitFullscreen();
        }
    };

    let container;
    let currentData;
    let currentLogScale;
    let currentDarkMode;

    const api = {
        chart: null,
        seriesMap: new Map(),
        watermark: null,
    };

    // Theme-aware colors
    const getColors = (isDark) => ({
        background: isDark ? "#050505" : "#ffffff",
        text: isDark ? "#cbd5e1" : "#475569",
        grid: isDark ? "rgba(71, 85, 105, 0.3)" : "rgba(226, 232, 240, 0.4)",
        crosshairLabel: isDark ? "#334155" : "#1e293b",
        crosshairLine: isDark
            ? "rgba(99, 102, 241, 0.5)"
            : "rgba(99, 102, 241, 0.4)",
        border: isDark ? "rgba(71, 85, 105, 0.5)" : "rgba(226, 232, 240, 0.8)",
    });

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
                // Use image watermark with logo
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
                // Use text watermark
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
    let watermarkVisible = true;
    const unsubWatermark = showWatermark.subscribe((val) => {
        watermarkVisible = val;
        if (api.chart) {
            createWatermarkWithTheme(currentDarkMode);
        }
    });

    // Subscribe to watermark type changes
    const unsubWatermarkType = watermarkType.subscribe(() => {
        if (api.chart) {
            createWatermarkWithTheme(currentDarkMode);
        }
    });

    onMount(() => {
        if (!container) return;

        const colors = getColors(darkMode);

        api.chart = createChart(container, {
            layout: {
                background: { color: darkMode ? "#050505" : "#ffffff" },
                textColor: colors.text,
                fontFamily: "JetBrains Mono",
                fontSize: 12,
            },
            grid: {
                vertLines: {
                    color: darkMode
                        ? "rgba(255, 255, 255, 0.03)"
                        : "rgba(0, 0, 0, 0.03)",
                    style: 2,
                },
                horzLines: {
                    color: darkMode
                        ? "rgba(255, 255, 255, 0.03)"
                        : "rgba(0, 0, 0, 0.03)",
                    style: 2,
                },
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
                visible: true,
                scaleMargins: {
                    top: 0.1,
                    bottom: 0.1,
                },
            },
            leftPriceScale: {
                borderColor: colors.border,
                mode: logScale ? 1 : 0,
                autoScale: true,
                visible: true,
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
                shiftVisibleRangeOnNewBar: true,
            },
            handleScale: {
                mouseWheel: true,
                pinch: true,
                axisPressedMouseMove: {
                    time: true,
                    price: true,
                },
            },
            handleScroll: {
                mouseWheel: true,
                horzTouchDrag: true,
                vertTouchDrag: true,
            },
        });

        // Create watermark using new v5+ API
        createWatermarkWithTheme(darkMode);

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
            }
        };

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        setTimeout(handleResize, 100);
        setTimeout(handleResize, 400);
        setTimeout(handleResize, 1000);

        return () => {
            resizeObserver.disconnect();
            unsubWatermark();
            unsubWatermarkType();
            if (api.watermark) {
                api.watermark.detach();
                api.watermark = null;
            }
            if (api.chart) {
                api.chart.remove();
                api.chart = null;
            }
        };
    });

    function updateSeries() {
        if (!api.chart) return;

        const newDataMap = new Map();
        data.forEach((s) => newDataMap.set(s.name, s));

        // 1. Remove series that are no longer in the data prop
        api.seriesMap.forEach((seriesInstance, name) => {
            if (!newDataMap.has(name)) {
                api.chart.removeSeries(seriesInstance);
                api.seriesMap.delete(name);
            }
        });

        // 2. Add or Update series
        data.forEach((sConfig) => {
            if (!sConfig.data || sConfig.data.length === 0) return;

            try {
                let series = api.seriesMap.get(sConfig.name);

                const seriesOptions = {
                    color: sConfig.color,
                    lineWidth: sConfig.width || 2,
                    priceLineVisible: false,
                    lastValueVisible: true,
                    title: sConfig.name,
                    priceScaleId: sConfig.priceScaleId || "right",
                    ...sConfig.options,
                };

                if (sConfig.type === "area") {
                    seriesOptions.lineColor = sConfig.color;
                    seriesOptions.topColor = sConfig.topColor || sConfig.color;
                    seriesOptions.bottomColor =
                        sConfig.bottomColor || "transparent";
                }

                if (!series) {
                    // Create new series
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
                    series = api.chart.addSeries(seriesType, seriesOptions);
                    api.seriesMap.set(sConfig.name, series);
                } else {
                    // Update existing series options
                    series.applyOptions(seriesOptions);
                }

                series.setData(sConfig.data);
            } catch (e) {
                console.error(
                    `Failed to add/update series ${sConfig.name}:`,
                    e,
                );
            }
        });

        // Only fitContent if it's the very first time we have data,
        // or if explicitly requested by a flag (not implemented yet).
        if (
            api.seriesMap.size > 0 &&
            Array.from(api.seriesMap.values())[0].data().length > 0
        ) {
            // We could optionally fitContent here if we detect it's the "first" load
            // But for now, let's just let it be.
        }
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
            leftPriceScale: {
                borderColor: colors.border,
            },
            timeScale: {
                borderColor: colors.border,
            },
        });

        // Recreate watermark with new theme colors
        createWatermarkWithTheme(darkMode);
    }

    $effect.pre(() => {
        // Read props at top level for Svelte 5 reactivity tracking
        const currentDarkModeValue = darkMode;
        const currentLogScaleValue = logScale;
        const currentDataValue = data;

        // Create a key that includes series names, times, and values to detect deep changes
        const getSeriesKey = (seriesArr) => {
            if (!seriesArr) return "";
            return seriesArr
                .map((s) => {
                    const vals = s.data || [];
                    // Include first, last, and middle time+value for change detection
                    const sample =
                        vals.length > 0
                            ? [
                                  vals[0]?.time,
                                  vals[0]?.value,
                                  vals[Math.floor(vals.length / 2)]?.time,
                                  vals[Math.floor(vals.length / 2)]?.value,
                                  vals[vals.length - 1]?.time,
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

    {#if showActions}
        <div class="chart-actions">
            <button
                class="action-btn"
                title="Download PNG"
                onclick={downloadChart}
            >
                <svg viewBox="0 0 24 24" width="14" height="14">
                    <path
                        fill="currentColor"
                        d="M12 16l-5-5h3V4h4v7h3l-5 5zm-9 4h18v-2H3v2z"
                    />
                </svg>
            </button>
            <button
                class="action-btn"
                title="Toggle Fullscreen"
                onclick={toggleFullscreen}
            >
                <svg viewBox="0 0 24 24" width="14" height="14">
                    <path
                        fill="currentColor"
                        d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
                    />
                </svg>
            </button>
            <button class="reset-btn" onclick={resetScales}> Reset </button>
        </div>
    {/if}
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
        background: #050505;
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
    }

    .chart-actions {
        position: absolute;
        top: 10px;
        right: 10px;
        display: flex;
        gap: 6px;
        z-index: 10;
        background: rgba(15, 23, 42, 0.6);
        padding: 4px;
        border-radius: 6px;
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        opacity: 0;
        transition: opacity 0.2s;
    }

    .chart-container-wrapper:hover .chart-actions {
        opacity: 1;
    }

    .action-btn {
        background: transparent;
        border: none;
        color: rgba(255, 255, 255, 0.7);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .action-btn:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }

    .reset-btn {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #6366f1;
        padding: 2px 8px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.7rem;
        font-weight: 600;
        transition: all 0.2s;
        margin-left: 2px;
    }

    .reset-btn:hover {
        background: #6366f1;
        color: white;
        border-color: #6366f1;
    }

    :global([data-theme="light"]) .chart-actions {
        background: rgba(255, 255, 255, 0.8);
        border-color: rgba(0, 0, 0, 0.1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    :global([data-theme="light"]) .action-btn {
        color: #64748b;
    }

    :global([data-theme="light"]) .action-btn:hover {
        background: rgba(0, 0, 0, 0.05);
        color: #1e293b;
    }

    :global([data-theme="light"]) .reset-btn {
        background: rgba(0, 0, 0, 0.05);
        border-color: rgba(0, 0, 0, 0.1);
    }
</style>
