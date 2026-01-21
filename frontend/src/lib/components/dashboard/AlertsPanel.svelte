<script>
    /**
     * AlertsPanel.svelte
     * Displays early warnings and market alerts
     * Extracted from Dashboard2.svelte
     */
    import { currentTranslations } from "../../../stores/settingsStore";

    /** @type {Array<{type: string, icon: string, title: string, msg: string, severity: string}>} */
    export let alerts = [];
</script>

{#if alerts.length > 0}
    <div class="alerts-panel">
        <div class="alerts-header">
            <h3>
                ⚠️ {$currentTranslations.alerts || "Alerts"} ({alerts.length})
            </h3>
        </div>
        <div class="alerts-grid">
            {#each alerts as alert}
                <div class="alert-item {alert.type} {alert.severity}">
                    <span class="alert-icon">{alert.icon}</span>
                    <div class="alert-content">
                        <span class="alert-title">{alert.title}</span>
                        <span class="alert-msg">{alert.msg}</span>
                    </div>
                </div>
            {/each}
        </div>
    </div>
{/if}

<style>
    .alerts-panel {
        grid-column: 1 / -1;
        background: var(--bg-secondary);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid var(--border-color);
        box-shadow: var(--card-shadow);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .alerts-panel:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px -5px rgba(0, 0, 0, 0.15);
        border-color: var(--accent-secondary);
    }

    .alerts-header h3 {
        margin: 0 0 0.75rem 0;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .alerts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 0.75rem;
    }

    .alert-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.75rem;
        border-radius: var(--radius-md);
        background: var(--bg-elevated);
        border-left: 4px solid var(--border-color);
    }

    .alert-item.danger {
        border-left-color: var(--signal-danger);
        background: var(--signal-danger-bg);
    }

    .alert-item.warning {
        border-left-color: var(--signal-warning);
        background: var(--signal-warning-bg);
    }

    .alert-item.info {
        border-left-color: var(--accent-secondary);
        background: rgba(59, 130, 246, 0.1);
    }

    .alert-item.signal {
        border-left-color: var(--accent-primary);
        background: rgba(139, 92, 246, 0.1);
    }

    .alert-item.critical {
        animation: pulse-critical 2s infinite;
    }

    @keyframes pulse-critical {
        0%,
        100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }

    .alert-icon {
        font-size: 1.25rem;
        flex-shrink: 0;
    }

    .alert-content {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        min-width: 0;
    }

    .alert-title {
        font-weight: 600;
        font-size: 0.8rem;
        color: var(--text-primary);
    }

    .alert-msg {
        font-size: 0.75rem;
        color: var(--text-secondary);
        line-height: 1.4;
    }
</style>
