/**
 * Dashboard Components Barrel Export
 * Import all dashboard components from this single file
 */

// High-Priority Components
export { default as RegimeStatusBar } from './RegimeStatusBar.svelte';
export { default as StressPanel } from './StressPanel.svelte';
export { default as SignalMatrixPanel } from './SignalMatrixPanel.svelte';
export { default as AlertsPanel } from './AlertsPanel.svelte';

// Medium-Priority Components
export { default as FlowMomentumPanel } from './FlowMomentumPanel.svelte';
export { default as RepoPlumbingPanel } from './RepoPlumbingPanel.svelte';

// Low-Priority Components (to be added as created)
// export { default as BtcFundamentalsPanel } from './BtcFundamentalsPanel.svelte';
// export { default as InflationPanel } from './InflationPanel.svelte';
// export { default as CatalystsPanel } from './CatalystsPanel.svelte';
