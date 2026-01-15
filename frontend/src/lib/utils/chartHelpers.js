/**
 * Chart Helpers - Plotly-specific shading and visualization utilities.
 * Extracted from RiskModelTab.svelte for reuse across tabs.
 * 
 * These helpers create Plotly shapes for:
 * - Z-score bands (bullish/bearish zones)
 * - Percentile bands (with configurable thresholds)
 * - Regime background shading (bullish/bearish/neutral periods)
 */

// ============================================================================
// PERCENTILE CONFIG - Thresholds for different indicators
// ============================================================================

/**
 * Percentile band configuration for different indicators.
 * - bullishPct: percentile threshold for bullish zone (top band)
 * - bearishPct: percentile threshold for bearish zone (bottom band)
 * - invert: if true, low values are bullish (e.g., VIX, spreads)
 */
export const PERCENTILE_CONFIG = {
    cli: { bullishPct: 70, bearishPct: 30, invert: false },
    hy_spread: { bullishPct: 30, bearishPct: 70, invert: true },
    ig_spread: { bullishPct: 30, bearishPct: 70, invert: true },
    nfci_credit: { bullishPct: 30, bearishPct: 60, invert: true },
    nfci_risk: { bullishPct: 30, bearishPct: 80, invert: true },
    lending: { bullishPct: 40, bearishPct: 60, invert: true },
    vix: { bullishPct: 25, bearishPct: 90, invert: true },
    move: { bullishPct: 30, bearishPct: 80, invert: true },
    fx_vol: { bullishPct: 30, bearishPct: 70, invert: true },
    tips_real: { bullishPct: 30, bearishPct: 75, invert: true },
};

// ============================================================================
// PLOTLY SHAPE GENERATORS
// ============================================================================

/**
 * Create Z-score background bands for Plotly charts.
 * Displays bullish zone (above threshold) and bearish zone (below threshold).
 * 
 * @param {boolean} darkMode - Whether dark mode is active
 * @param {Object} options - Configuration options
 * @param {number} options.bullishThreshold - Z-score threshold for bullish zone (default: 1.0)
 * @param {number} options.bearishThreshold - Z-score threshold for bearish zone (default: -1.0)
 * @param {boolean} options.invertColors - If true, swap bullish/bearish colors (for inverted indicators)
 * @returns {Array} Array of Plotly shape objects
 */
export function createZScoreBands(
    darkMode,
    {
        bullishThreshold = 1.0,
        bearishThreshold = -1.0,
        invertColors = false,
    } = {}
) {
    const greenColor = darkMode
        ? "rgba(16, 185, 129, 0.08)"
        : "rgba(16, 185, 129, 0.12)";
    const redColor = darkMode
        ? "rgba(239, 68, 68, 0.08)"
        : "rgba(239, 68, 68, 0.12)";

    const bullishColor = invertColors ? redColor : greenColor;
    const bearishColor = invertColors ? greenColor : redColor;

    return [
        {
            type: "rect",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: bullishThreshold,
            y1: 6,
            fillcolor: bullishColor,
            line: { width: 0 },
            layer: "below",
        },
        {
            type: "rect",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: -6,
            y1: bearishThreshold,
            fillcolor: bearishColor,
            line: { width: 0 },
            layer: "below",
        },
        {
            type: "line",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: 0,
            y1: 0,
            line: {
                color: darkMode
                    ? "rgba(148, 163, 184, 0.3)"
                    : "rgba(100, 116, 139, 0.3)",
                width: 1,
                dash: "dot",
            },
            layer: "below",
        },
    ];
}

/**
 * Create percentile background bands for Plotly charts.
 * Displays zones based on percentile thresholds.
 * 
 * @param {boolean} darkMode - Whether dark mode is active
 * @param {Object} options - Configuration options
 * @param {number} options.bullishPct - Percentile threshold for bullish zone (default: 70)
 * @param {number} options.bearishPct - Percentile threshold for bearish zone (default: 30)
 * @param {boolean} options.invert - If true, low values are bullish (for VIX, spreads)
 * @returns {Array} Array of Plotly shape objects
 */
export function createPercentileBands(
    darkMode,
    { bullishPct = 70, bearishPct = 30, invert = false } = {}
) {
    const greenColor = darkMode
        ? "rgba(16, 185, 129, 0.10)"
        : "rgba(16, 185, 129, 0.12)";
    const redColor = darkMode
        ? "rgba(239, 68, 68, 0.10)"
        : "rgba(239, 68, 68, 0.12)";

    // For inverted series (VIX, spreads): low = green
    const topColor = invert ? redColor : greenColor;
    const bottomColor = invert ? greenColor : redColor;

    return [
        {
            type: "rect",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: bullishPct,
            y1: 100,
            fillcolor: topColor,
            line: { width: 0 },
            layer: "below",
        },
        {
            type: "rect",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: 0,
            y1: bearishPct,
            fillcolor: bottomColor,
            line: { width: 0 },
            layer: "below",
        },
        {
            type: "line",
            xref: "paper",
            yref: "y",
            x0: 0,
            x1: 1,
            y0: 50,
            y1: 50,
            line: {
                color: darkMode
                    ? "rgba(148, 163, 184, 0.4)"
                    : "rgba(100, 116, 139, 0.4)",
                width: 1,
                dash: "dot",
            },
            layer: "below",
        },
    ];
}

/**
 * Create regime background shapes for Plotly charts.
 * Colors the background based on signal state (bullish/bearish/neutral).
 * 
 * @param {string[]} filteredDates - Dates that are currently visible in the chart
 * @param {string[]} allDates - Full date array from dashboardData
 * @param {string[]} allSignals - Array of signal states ("bullish", "bearish", "neutral")
 * @param {boolean} darkMode - Whether dark mode is active
 * @returns {Array} Array of Plotly shape objects
 */
export function createRegimeShapes(filteredDates, allDates, allSignals, darkMode) {
    if (
        !filteredDates ||
        !allDates ||
        !allSignals ||
        filteredDates.length === 0
    )
        return [];

    // Find the start and end indices of the filtered range in the original data
    const startIdx = allDates.indexOf(filteredDates[0]);
    const endIdx = allDates.indexOf(filteredDates[filteredDates.length - 1]);

    if (startIdx === -1 || endIdx === -1) return [];

    const dates = allDates.slice(startIdx, endIdx + 1);
    const signals = allSignals.slice(startIdx, endIdx + 1);

    const shapes = [];
    const greenColor = darkMode
        ? "rgba(16, 185, 129, 0.12)"
        : "rgba(16, 185, 129, 0.15)";
    const redColor = darkMode
        ? "rgba(239, 68, 68, 0.12)"
        : "rgba(239, 68, 68, 0.15)";

    let currentRegime = null;
    let blockStartIdx = 0;

    // Iterate once and merge identical adjacent regimes
    for (let i = 0; i <= dates.length; i++) {
        const regime = i < dates.length ? signals[i] : null;
        if (regime !== currentRegime || i === dates.length) {
            if (currentRegime === "bullish" || currentRegime === "bearish") {
                const d0 = dates[blockStartIdx];
                const d1 = dates[Math.min(i, dates.length - 1)];
                if (d0 && d1) {
                    shapes.push({
                        type: "rect",
                        xref: "x",
                        yref: "paper",
                        x0: d0,
                        x1: d1,
                        y0: 0,
                        y1: 1,
                        fillcolor: currentRegime === "bullish" ? greenColor : redColor,
                        line: { width: 0 },
                        layer: "below",
                    });
                }
            }
            currentRegime = regime;
            blockStartIdx = i;
        }
    }
    return shapes;
}

/**
 * Build a range indices cache for efficient chart filtering.
 * Pre-computes indices for common date ranges to avoid repeated lookups.
 * 
 * @param {string[]} dates - Full date array from dashboardData
 * @param {string[]} ranges - Array of range codes (e.g., ["1M", "3M", "6M", "1Y", "3Y", "5Y"])
 * @param {Date} minDate - Minimum valid date (to exclude bad data like 1970)
 * @returns {Object} Cache object mapping range codes to index arrays
 */
export function buildRangeIndicesCache(dates, ranges = ["1M", "3M", "6M", "1Y", "3Y", "5Y"], minDate = new Date("1990-01-01"), getCutoffDateFn = null) {
    if (!dates || !Array.isArray(dates)) return {};

    // Filter out dates before minDate to prevent 1970 x-axis issues
    const allValidIndices = dates
        .map((dateStr, i) => ({ date: new Date(dateStr), index: i }))
        .filter((item) => item.date >= minDate)
        .map((item) => item.index);

    const cache = { ALL: allValidIndices };

    // Use passed function or inline implementation
    const getCutoff = getCutoffDateFn || ((range) => {
        if (range === "ALL") return null;
        const now = new Date();
        switch (range) {
            case "1M": return new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
            case "3M": return new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
            case "6M": return new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
            case "1Y": return new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
            case "2Y": return new Date(now.getFullYear() - 2, now.getMonth(), now.getDate());
            case "3Y": return new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
            case "5Y": return new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());
            default: return null;
        }
    });

    ranges.forEach((r) => {
        const cutoff = getCutoff(r);
        if (!cutoff) {
            cache[r] = cache.ALL;
            return;
        }
        const indices = [];
        for (let i = 0; i < dates.length; i++) {
            const dateObj = new Date(dates[i]);
            if (dateObj >= cutoff && dateObj >= minDate) indices.push(i);
        }
        cache[r] = indices;
    });

    return cache;
}

/**
 * Filter Plotly trace data using a pre-built range cache.
 * More efficient than filterPlotlyData for components with multiple charts.
 * 
 * @param {Array} traceArray - Array of Plotly trace objects
 * @param {string} range - Range code (e.g., "1Y", "ALL")
 * @param {Object} rangeIndicesCache - Pre-built cache from buildRangeIndicesCache
 * @param {string[]} dates - Full date array from dashboardData
 * @param {boolean} autoTrim - If true, trim leading zeros/nulls for "ALL" range
 * @returns {Array} Filtered trace array
 */
export function filterWithCache(traceArray, range, rangeIndicesCache, dates, autoTrim = true) {
    if (!traceArray || !dates) return traceArray;

    let indices = rangeIndicesCache[range] || rangeIndicesCache["ALL"] || [];

    if (range === "ALL" && autoTrim) {
        let firstValidIdx = -1;
        for (let i = 0; i < dates.length; i++) {
            const hasData = traceArray.some((t) => {
                const val = t.y ? t.y[i] : undefined;
                return val !== null && val !== undefined && val !== 0;
            });
            if (hasData) {
                firstValidIdx = i;
                break;
            }
        }
        if (firstValidIdx !== -1) {
            indices = indices.filter((idx) => idx >= firstValidIdx);
        }
    }

    if (indices.length === 0) return traceArray;

    return traceArray.map((trace) => ({
        ...trace,
        x: indices.map((i) => dates[i]),
        y: indices.map((i) => (trace.y ? trace.y[i] : undefined)),
    }));
}
