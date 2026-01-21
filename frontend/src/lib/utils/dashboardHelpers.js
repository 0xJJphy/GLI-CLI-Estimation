/**
 * Dashboard Helper Functions
 * Shared utilities for dashboard components
 * Extracted from Dashboard2.svelte for reusability
 */

/**
 * Format a numeric value with decimals and optional suffix
 * @param {number|null} val - Value to format
 * @param {number} decimals - Decimal places
 * @param {string} suffix - Optional suffix (%, T, B, etc.)
 * @returns {string} Formatted value or "—" if invalid
 */
export function formatValue(val, decimals = 2, suffix = "") {
    if (val === null || val === undefined || isNaN(val)) return "—";
    return val.toFixed(decimals) + suffix;
}

/**
 * Format a delta value with +/- prefix
 * @param {number|null} val - Delta value
 * @param {number} decimals - Decimal places
 * @returns {string} Formatted delta with sign
 */
export function formatDelta(val, decimals = 2) {
    if (val === null || val === undefined || isNaN(val)) return "—";
    const prefix = val > 0 ? "+" : "";
    return prefix + val.toFixed(decimals);
}

/**
 * Calculate Rate of Change (ROC)
 * @param {number[]} series - Time series array
 * @param {number} periods - Lookback periods (default: 22 trading days ≈ 1 month)
 * @returns {number|null} ROC percentage or null if insufficient data
 */
export function calcRoc(series, periods = 22) {
    if (!series || series.length < periods + 1) return null;
    const current = series[series.length - 1];
    const past = series[series.length - 1 - periods];
    if (current === null || past === null || past === 0) return null;
    return ((current - past) / Math.abs(past)) * 100;
}

/**
 * Calculate absolute delta
 * @param {number[]} series - Time series array
 * @param {number} periods - Lookback periods
 * @returns {number|null} Absolute change or null if insufficient data
 */
export function calcDelta(series, periods = 22) {
    if (!series || series.length < periods + 1) return null;
    const current = series[series.length - 1];
    const past = series[series.length - 1 - periods];
    if (current === null || past === null) return null;
    return current - past;
}

/**
 * Get CSS class for signal state
 * @param {string} state - "bullish", "bearish", or "neutral"
 * @returns {string} CSS class name
 */
export function getSignalClass(state) {
    if (state === "bullish") return "signal-bull";
    if (state === "bearish") return "signal-bear";
    return "signal-neutral";
}

/**
 * Get emoji for signal state
 * @param {string} state - "bullish", "bearish", or "neutral"
 * @returns {string} Emoji indicator
 */
export function getSignalEmoji(state) {
    if (state === "bullish") return "🟢";
    if (state === "bearish") return "🔴";
    return "⚪";
}

/**
 * Get CSS class for stress level
 * @param {string} level - "CRITICAL", "HIGH", "MODERATE", or "LOW"
 * @returns {string} CSS class name
 */
export function getStressLevelClass(level) {
    if (level === "CRITICAL") return "critical";
    if (level === "HIGH") return "high";
    if (level === "MODERATE") return "moderate";
    return "low";
}

/**
 * Get color for regime state
 * @param {number} regimeCode - 1 (bullish), -1 (bearish), 0 (neutral)
 * @returns {string} Hex color
 */
export function getRegimeColor(regimeCode) {
    if (regimeCode === 1) return "#10b981";
    if (regimeCode === -1) return "#ef4444";
    return "#6b7280";
}

/**
 * Get stress color based on total score
 * @param {number} totalStress - Total stress score
 * @returns {string} Hex color
 */
export function getStressColor(totalStress) {
    if (totalStress >= 15) return "#dc2626";
    if (totalStress >= 10) return "#ea580c";
    if (totalStress >= 5) return "#ca8a04";
    return "#16a34a";
}
