<script>
    let { selectedRange = "ALL", onRangeChange = () => {} } = $props();

    const ranges = [
        { value: "1M", label: "1M" },
        { value: "3M", label: "3M" },
        { value: "6M", label: "6M" },
        { value: "1Y", label: "1Y" },
        { value: "3Y", label: "3Y" },
        { value: "ALL", label: "ALL" },
    ];

    function handleClick(range) {
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
        gap: 4px;
        padding: 4px;
        background: rgba(241, 245, 249, 0.8);
        border-radius: 8px;
    }

    .range-btn {
        padding: 4px 10px;
        border: none;
        background: transparent;
        color: #64748b;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        border-radius: 6px;
        transition: all 0.2s ease;
    }

    .range-btn:hover {
        background: rgba(99, 102, 241, 0.1);
        color: #6366f1;
    }

    .range-btn.active {
        background: #6366f1;
        color: white;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.3);
    }
</style>
