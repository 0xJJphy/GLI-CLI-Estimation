<script>
    import { onMount } from "svelte";
    import {
        createChart,
        LineSeries,
        HistogramSeries,
    } from "lightweight-charts";

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

    // Regime colors
    const regimeColors = {
        0: "rgba(107, 114, 128, 0.15)",
        1: "rgba(34, 197, 94, 0.25)",
        2: "rgba(239, 68, 68, 0.25)",
        3: "rgba(59, 130, 246, 0.25)",
        4: "rgba(139, 92, 246, 0.25)",
    };

    const regimeSolidColors = {
        0: "#6b7280",
        1: "#22c55e",
        2: "#ef4444",
        3: "#3b82f6",
        4: "#8b5cf6",
    };

    // Custom primitive for background coloring
    class BackgroundColorPrimitive {
        constructor(regimeData, colors) {
            this._regimeData = regimeData;
            this._colors = colors;
        }

        updateData(regimeData) {
            this._regimeData = regimeData;
        }

        paneViews() {
            return [
                new BackgroundColorPaneView(this._regimeData, this._colors),
            ];
        }
    }

    class BackgroundColorPaneView {
        constructor(regimeData, colors) {
            this._regimeData = regimeData;
            this._colors = colors;
        }

        zOrder() {
            return "bottom";
        }

        renderer() {
            return new BackgroundColorRenderer(this._regimeData, this._colors);
        }
    }

    class BackgroundColorRenderer {
        constructor(regimeData, colors) {
            this._regimeData = regimeData;
            this._colors = colors;
        }

        draw(target, priceConverter) {
            const ctx = target.context;
            const width = target.mediaSize.width;
            const height = target.mediaSize.height;

            if (!this._regimeData || this._regimeData.length === 0) return;

            // Group consecutive regimes
            let currentRegime = this._regimeData[0]?.value;
            let startX = 0;
            const barWidth = width / this._regimeData.length;

            for (let i = 0; i <= this._regimeData.length; i++) {
                const regime = this._regimeData[i]?.value;
                if (i === this._regimeData.length || regime !== currentRegime) {
                    // Draw rectangle for the regime period
                    if (currentRegime !== 0 && currentRegime !== undefined) {
                        ctx.fillStyle =
                            this._colors[currentRegime] || this._colors[0];
                        ctx.fillRect(
                            startX,
                            0,
                            (i - startX / barWidth) * barWidth,
                            height,
                        );
                    }
                    if (i < this._regimeData.length) {
                        startX = i * barWidth;
                        currentRegime = regime;
                    }
                }
            }
        }
    }

    // Theme colors
    const getColors = (isDark) => ({
        background: isDark ? "#050505" : "#ffffff",
        text: isDark ? "#cbd5e1" : "#475569",
        grid: isDark ? "rgba(255, 255, 255, 0.03)" : "rgba(0, 0, 0, 0.03)",
    });

    let backgroundPrimitive = null;

    onMount(() => {
        if (!container) return;

        const colors = getColors(darkMode);

        chart = createChart(container, {
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

        // BTC Series (main pane, right scale)
        btcSeries = chart.addSeries(LineSeries, {
            color: "#f7931a",
            lineWidth: 2,
            priceScaleId: "right",
            priceLineVisible: false,
            lastValueVisible: true,
            title: "BTC",
        });

        // Indicator Series (bottom, left scale)
        indicatorSeries = chart.addSeries(HistogramSeries, {
            priceScaleId: "left",
            priceLineVisible: false,
            lastValueVisible: false,
            title: "",
        });

        updateData();

        const handleResize = () => {
            if (chart && container && container.clientWidth > 0) {
                chart.applyOptions({
                    width: container.clientWidth,
                    height: container.clientHeight,
                });
            }
        };

        const resizeObserver = new ResizeObserver(handleResize);
        resizeObserver.observe(container);

        setTimeout(handleResize, 100);
        setTimeout(() => chart?.timeScale().fitContent(), 200);

        return () => {
            resizeObserver.disconnect();
            if (chart) {
                chart.remove();
                chart = null;
            }
        };
    });

    function updateData() {
        if (!chart || !btcSeries || !indicatorSeries) return;

        // Update BTC data
        if (btcData.length > 0) {
            btcSeries.setData(btcData);
        }

        // Update indicator data with colors
        if (indicatorData.length > 0) {
            indicatorSeries.setData(indicatorData);
        }

        // Fit content after data update
        setTimeout(() => chart?.timeScale().fitContent(), 50);
    }

    // React to data changes
    $effect(() => {
        if (btcData && indicatorData && chart) {
            updateData();
        }
    });

    // React to theme changes
    $effect(() => {
        if (chart && darkMode !== undefined) {
            const colors = getColors(darkMode);
            chart.applyOptions({
                layout: {
                    background: { color: colors.background },
                    textColor: colors.text,
                },
                grid: {
                    vertLines: { color: colors.grid },
                    horzLines: { color: colors.grid },
                },
            });
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
