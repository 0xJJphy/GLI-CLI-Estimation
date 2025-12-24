<script>
    export let type = "neutral";
    export let text = "";

    $: classes = `badge ${type}`;
</script>

<span class={classes}>
    {text}
</span>

<style>
    .badge {
        padding: 4px 10px;
        border-radius: 99px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .bullish {
        background: #ecfdf5;
        color: #059669;
        border: 1px solid #d1fae5;
    }

    .bearish {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fee2e2;
    }

    .neutral {
        background: #f8fafc;
        color: #64748b;
        border: 1px solid #e2e8f0;
    }
</style>
