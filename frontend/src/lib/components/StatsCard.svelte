<script>
    export let title = "";
    export let value = 0;
    export let change = 0;
    export let suffix = "";
    export let precision = 2;
    export let icon = "📈";

    $: isPositive = change >= 0;
</script>

<div class="stats-card">
    <div class="card-glow"></div>
    <div class="content">
        <div class="header">
            <div class="title-group">
                <span class="icon">{icon}</span>
                <span class="title">{title}</span>
            </div>
            <div
                class="trend"
                class:positive={isPositive}
                class:negative={!isPositive}
            >
                {isPositive ? "▲" : "▼"}
                {(Number(change) || 0).toFixed(2)}%
            </div>
        </div>
        <div class="value">
            <span class="number">{(Number(value) || 0).toFixed(precision)}</span
            >
            <span class="suffix">{suffix}</span>
        </div>
        <div class="footer">
            <div class="progress-bar">
                <div
                    class="progress"
                    style="width: 70%;"
                    class:positive={isPositive}
                    class:negative={!isPositive}
                ></div>
            </div>
        </div>
    </div>
</div>

<style>
    .stats-card {
        position: relative;
        background: var(--bg-secondary, #ffffff);
        border: 1px solid var(--border-color, rgba(0, 0, 0, 0.05));
        border-radius: 16px;
        padding: 24px;
        color: var(--text-primary, #1e293b);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: var(--card-shadow, 0 1px 3px rgba(0, 0, 0, 0.1));
    }

    .stats-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15);
        border-color: var(--accent-secondary, rgba(59, 130, 246, 0.3));
    }

    .card-glow {
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(
            circle at center,
            rgba(59, 130, 246, 0.03) 0%,
            transparent 50%
        );
        opacity: 0;
        transition: opacity 0.3s ease;
        pointer-events: none;
    }

    .stats-card:hover .card-glow {
        opacity: 1;
    }

    .content {
        position: relative;
        z-index: 1;
    }

    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }

    .title-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .icon {
        font-size: 1.25rem;
    }

    .title {
        font-size: 0.875rem;
        color: var(--text-muted, #64748b);
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    .trend {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .trend.positive {
        color: var(--positive-color, #059669);
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .trend.negative {
        color: var(--negative-color, #dc2626);
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .value {
        margin-bottom: 8px;
    }

    .number {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-primary, #0f172a);
    }

    .suffix {
        font-size: 0.875rem;
        color: var(--text-muted, #94a3b8);
        margin-left: 4px;
        font-weight: 600;
    }

    .footer {
        margin-top: 12px;
    }

    .progress-bar {
        height: 6px;
        background: var(--bg-tertiary, #f1f5f9);
        border-radius: 3px;
        overflow: hidden;
    }

    .progress {
        height: 100%;
        border-radius: 3px;
        transition: width 1s ease-out;
    }

    .progress.positive {
        background: var(--positive-color, #10b981);
    }

    .progress.negative {
        background: var(--negative-color, #ef4444);
    }
</style>
