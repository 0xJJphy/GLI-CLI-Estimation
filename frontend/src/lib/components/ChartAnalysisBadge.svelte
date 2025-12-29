<script>
    export let analysis = null;
    export let darkMode = false;

    $: signalColor = getSignalColorFromText(analysis?.signal_color || "yellow");

    function getSignalColorFromText(color) {
        const colors = {
            green: {
                bg: "rgba(22, 163, 74, 0.15)",
                text: "#16a34a",
                border: "#16a34a",
            },
            yellow: {
                bg: "rgba(202, 138, 4, 0.15)",
                text: "#ca8a04",
                border: "#ca8a04",
            },
            red: {
                bg: "rgba(220, 38, 38, 0.15)",
                text: "#dc2626",
                border: "#dc2626",
            },
            orange: {
                bg: "rgba(234, 88, 12, 0.15)",
                text: "#ea580c",
                border: "#ea580c",
            },
        };
        return colors[color] || colors.yellow;
    }
</script>

{#if analysis}
    <div class="chart-analysis" class:dark={darkMode}>
        <div
            class="analysis-badge"
            style="background-color: {signalColor.bg}; border-color: {signalColor.border}"
        >
            <span
                class="signal-indicator"
                style="background-color: {signalColor.text}"
            ></span>
            <span class="signal-text" style="color: {signalColor.text}"
                >{analysis.signal || "N/A"}</span
            >
        </div>
        <div class="analysis-summary">
            {analysis.summary || "No analysis available"}
        </div>
    </div>
{/if}

<style>
    .chart-analysis {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 12px;
        background: var(--bg-tertiary, #2a2a3e);
        border-radius: 8px;
        margin-top: 12px;
        border: 1px solid var(--border-color, #333);
    }

    .analysis-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 4px;
        border: 1px solid;
        width: fit-content;
    }

    .signal-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    .signal-text {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .analysis-summary {
        font-size: 12px;
        line-height: 1.5;
        color: var(--text-secondary, #aaa);
    }
</style>
