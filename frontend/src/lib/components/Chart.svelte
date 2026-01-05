<script>
    import { onMount, afterUpdate } from "svelte";
    import Plotly from "plotly.js-dist-min";
    import { downloadCardAsImage } from "../utils/downloadCard.js";

    export let data = [];
    export let layout = {};
    export let config = { responsive: true, displayModeBar: false };
    export let yType = "linear";
    export let darkMode = false;
    export let divId =
        "plotly-chart-" + Math.random().toString(36).substr(2, 9);
    // Optional: Reference to the parent card container for "Download Card" feature
    export let cardContainer = null;
    export let cardTitle = "chart_card"; // Filename prefix for card download

    let chartContainer;

    // Theme-aware colors
    const getLayout = (isDark) => ({
        paper_bgcolor: "rgba(0,0,0,0)",
        plot_bgcolor: "rgba(0,0,0,0)",
        font: {
            color: isDark ? "#cbd5e1" : "#1e293b",
            family: "'JetBrains Mono', monospace",
        },
        margin: { t: 40, r: 20, l: 65, b: 100 },
        xaxis: {
            gridcolor: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.05)",
            zeroline: false,
            color: isDark ? "#94a3b8" : "#64748b",
        },
        yaxis: {
            gridcolor: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.05)",
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
        annotations: [
            {
                text: "0xJJphy",
                xref: "paper",
                yref: "paper",
                x: 0.5,
                y: 0.5,
                showarrow: false,
                font: {
                    size: 60,
                    family: "'JetBrains Mono', monospace",
                    color: isDark
                        ? "rgba(255,255,255,0.05)"
                        : "rgba(0,0,0,0.12)",
                },
                textangle: 0,
            },
        ],
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

    function downloadImage() {
        Plotly.downloadImage(chartContainer, {
            format: "png",
            width: chartContainer.clientWidth,
            height: chartContainer.clientHeight,
            filename: "chart",
        });
    }

    function toggleFullscreen() {
        if (!chartContainer) return;
        const wrapper = chartContainer.parentElement;
        if (!document.fullscreenElement) {
            wrapper.requestFullscreen().catch((err) => {
                console.error(
                    `Error attempting to enable fullscreen: ${err.message}`,
                );
            });
        } else {
            document.exitFullscreen();
        }
    }

    function resetView() {
        Plotly.relayout(chartContainer, {
            "xaxis.autorange": true,
            "yaxis.autorange": true,
        });
    }

    async function downloadCard() {
        if (cardContainer) {
            await downloadCardAsImage(cardContainer, cardTitle);
        } else {
            console.warn("[Chart] No cardContainer provided for card download");
            // Fallback to chart download
            downloadImage();
        }
    }
</script>

<div class="chart-content relative">
    <div id={divId} bind:this={chartContainer} class="chart-wrapper"></div>
    <div class="chart-actions">
        <button
            class="action-btn"
            title="Download Chart PNG"
            on:click={downloadImage}
        >
            <svg viewBox="0 0 24 24" width="14" height="14">
                <path
                    fill="currentColor"
                    d="M12 16l-5-5h3V4h4v7h3l-5 5zm-9 4h18v-2H3v2z"
                />
            </svg>
        </button>
        {#if cardContainer}
            <button
                class="action-btn"
                title="Download Full Card"
                on:click={downloadCard}
            >
                <svg viewBox="0 0 24 24" width="14" height="14">
                    <path
                        fill="currentColor"
                        d="M3 3h18v18H3V3zm2 2v14h14V5H5zm2 2h10v2H7V7zm0 4h10v2H7v-2zm0 4h7v2H7v-2z"
                    />
                </svg>
            </button>
        {/if}
        <button
            class="action-btn"
            title="Toggle Fullscreen"
            on:click={toggleFullscreen}
        >
            <svg viewBox="0 0 24 24" width="14" height="14">
                <path
                    fill="currentColor"
                    d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"
                />
            </svg>
        </button>
        <button class="reset-btn" on:click={resetView}> Reset </button>
    </div>
</div>

<style>
    .chart-content.relative {
        position: relative;
        width: 100%;
        height: 100%;
    }

    .chart-wrapper {
        width: 100%;
        height: 100%;
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

    .chart-content:hover .chart-actions {
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
