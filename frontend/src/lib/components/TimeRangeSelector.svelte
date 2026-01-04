<script>
    const defaultRanges = [
        { value: "1M", label: "1M" },
        { value: "3M", label: "3M" },
        { value: "6M", label: "6M" },
        { value: "1Y", label: "1Y" },
        { value: "3Y", label: "3Y" },
        { value: "5Y", label: "5Y" },
        { value: "ALL", label: "ALL" },
    ];

    let {
        selectedRange = $bindable("ALL"),
        onRangeChange = () => {},
        ranges = defaultRanges,
    } = $props();

    function handleClick(range) {
        selectedRange = range;
        onRangeChange(range);
    }
</script>

<div class="time-range-selector">
    {#each ranges as range}
        <button
            class="range-btn"
            class:active={selectedRange === range.value}
            onclick={() => handleClick(range.value)}
        >
            {range.label}
        </button>
    {/each}
</div>

<style>
    .time-range-selector {
        display: flex;
        gap: 2px;
        padding: 2px;
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid var(--border-color);
        border-radius: 4px;
    }

    :global([data-theme="light"]) .time-range-selector {
        background: rgba(0, 0, 0, 0.03);
    }

    .range-btn {
        padding: 2px 8px;
        border: none;
        background: transparent;
        color: var(--text-muted);
        font-family: var(--font-mono);
        font-size: 11px;
        font-weight: 400;
        cursor: pointer;
        border-radius: 3px;
        transition: all 0.15s ease;
        text-transform: uppercase;
    }

    .range-btn:hover {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-primary);
    }

    :global([data-theme="light"]) .range-btn:hover {
        background: rgba(0, 0, 0, 0.05);
    }

    .range-btn.active {
        background: var(--accent-primary);
        color: white;
        font-weight: 600;
    }
</style>
