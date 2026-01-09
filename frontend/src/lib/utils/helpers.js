/**
 * Shared helper functions for the GLI-CLI Dashboard.
 * Extracted from App.svelte for modularity and reusability.
 */

// ============================================================================
// DATA ACCESS HELPERS
// ============================================================================

/**
 * Get the last available date for a series from dashboardData.last_dates
 * @param {Object} dashboardData - The dashboard data object
 * @param {string} seriesKey - Key for the series (e.g., "GLI", "FED", "NFCI")
 * @returns {string} - Formatted date string or "N/A"
 */
export const getLastDate = (dashboardData, seriesKey) => {
    if (!dashboardData?.last_dates) return "N/A";
    const key = seriesKey.toUpperCase();
    return (
        dashboardData.last_dates[key] ||
        dashboardData.last_dates[key + "_USD"] ||
        dashboardData.last_dates[seriesKey] ||
        "N/A"
    );
};

/**
 * Get the latest value from an array.
 * @param {Array} arr - Array of values
 * @returns {number|null} - Latest value or 0
 */
export const getLatestValue = (arr) => arr?.[arr?.length - 1] ?? 0;

/**
 * Calculate percentage change over a period.
 * @param {Array} arr - Array of values
 * @param {number} period - Number of periods to look back (default 7)
 * @returns {number} - Percentage change
 */
export const getChange = (arr, period = 7) => {
    if (!arr || arr.length <= period) return 0;
    const lastIdx = arr.length - 1;
    const current = arr[lastIdx];
    const previous = arr[lastIdx - period];
    if (previous === 0 || previous === null || previous === undefined) return 0;
    return ((current - previous) / previous) * 100;
};

// ============================================================================
// TIME RANGE HELPERS
// ============================================================================

/**
 * Get cutoff date based on time range string.
 * @param {string} range - "7D", "21D", "1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", or "ALL"
 * @returns {Date|null}
 */
export const getCutoffDate = (range) => {
    if (range === "ALL") return null;
    const now = new Date();
    switch (range) {
        case "7D":
            return new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        case "21D":
            return new Date(now.getTime() - 21 * 24 * 60 * 60 * 1000);
        case "1M":
            return new Date(now.getFullYear(), now.getMonth() - 1, now.getDate());
        case "3M":
            return new Date(now.getFullYear(), now.getMonth() - 3, now.getDate());
        case "6M":
            return new Date(now.getFullYear(), now.getMonth() - 6, now.getDate());
        case "1Y":
            return new Date(now.getFullYear() - 1, now.getMonth(), now.getDate());
        case "2Y":
            return new Date(now.getFullYear() - 2, now.getMonth(), now.getDate());
        case "3Y":
            return new Date(now.getFullYear() - 3, now.getMonth(), now.getDate());
        case "5Y":
            return new Date(now.getFullYear() - 5, now.getMonth(), now.getDate());
        default:
            return null;
    }
};

/**
 * Get valid indices for dates array based on time range.
 * @param {string[]} dates - Array of date strings
 * @param {string} range - Time range string
 * @returns {number[]}
 */
export const getFilteredIndices = (dates, range) => {
    if (!dates || !Array.isArray(dates) || range === "ALL") {
        return dates ? dates.map((_, i) => i) : [];
    }
    const cutoff = getCutoffDate(range);
    if (!cutoff) return dates.map((_, i) => i);

    return dates.reduce((acc, d, i) => {
        const date = new Date(d);
        if (date >= cutoff) acc.push(i);
        return acc;
    }, []);
};

/**
 * Filter Plotly trace data based on time range.
 * @param {Array} traceArray - Plotly traces
 * @param {string[]} dates - Date array
 * @param {string} range - Time range string
 * @returns {Array}
 */
export const filterPlotlyData = (traceArray, dates, range) => {
    if (!traceArray || !dates || !dates.length) return traceArray;

    let indices;
    if (range === "ALL") {
        // Auto-trim: Find the first index where ANY trace has non-zero/non-null data
        let firstValidIdx = -1;
        for (let i = 0; i < dates.length; i++) {
            const hasData = traceArray.some((trace) => {
                const val = trace.y[i];
                return val !== null && val !== undefined && val !== 0;
            });
            if (hasData) {
                firstValidIdx = i;
                break;
            }
        }
        if (firstValidIdx === -1) return traceArray;
        indices = dates.slice(firstValidIdx).map((_, i) => i + firstValidIdx);
    } else {
        indices = getFilteredIndices(dates, range);
    }

    return traceArray.map((trace) => ({
        ...trace,
        x: indices.map((i) => trace.x[i]),
        y: indices.map((i) => trace.y[i]),
    }));
};

/**
 * Format data for TradingView charts.
 * @param {string[]} dates - Date strings
 * @param {number[]} values - Values array
 * @returns {Array<{time: string, value: number}>}
 */
export const formatTV = (dates, values) => {
    if (!dates || !values || !Array.isArray(dates)) return [];
    const points = [];
    for (let i = 0; i < dates.length; i++) {
        const val = values[i];
        if (val === null || val === undefined || isNaN(val) || val <= 0) continue;
        const dateStr = dates[i];
        if (!dateStr || typeof dateStr !== "string") continue;
        points.push({ time: dateStr, value: val });
    }
    return points.sort((a, b) => (a.time > b.time ? 1 : -1));
};

/**
 * Create LightweightChart series config with time range filtering.
 * @param {string[]} dates - Date strings
 * @param {number[]} values - Values array
 * @param {string} range - Time range
 * @param {string} name - Series name
 * @param {string} color - Series color
 * @param {string} type - Series type ("line", "area", etc.)
 * @returns {Array}
 */
export const formatLC = (dates, values, range, name, color, type = "line") => {
    if (!dates || !values) return [];

    const cutoff = getCutoffDate(range);
    const points = [];

    for (let i = 0; i < dates.length; i++) {
        const val = values[i];
        if (val === null || val === undefined || isNaN(val)) continue;
        const dateStr = dates[i];
        if (!dateStr || typeof dateStr !== "string") continue;

        if (cutoff) {
            const pointDate = new Date(dateStr);
            if (pointDate < cutoff) continue;
        }
        points.push({ time: dateStr, value: val });
    }

    const sortedPoints = points.sort((a, b) => (a.time > b.time ? 1 : -1));

    return [
        {
            name,
            type,
            color,
            data: sortedPoints,
            width: 2,
        },
    ];
};

/**
 * Calculate Pearson correlation between two arrays.
 * @param {number[]} xArray 
 * @param {number[]} yArray 
 * @returns {number}
 */
export function calculateCorrelation(xArray, yArray) {
    if (!xArray || !yArray || xArray.length !== yArray.length || xArray.length < 2)
        return 0;

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0, n = 0;
    for (let i = 0; i < xArray.length; i++) {
        const x = xArray[i];
        const y = yArray[i];
        if (x !== null && x !== undefined && y !== null && y !== undefined) {
            sumX += x;
            sumY += y;
            sumXY += x * y;
            sumX2 += x * x;
            sumY2 += y * y;
            n++;
        }
    }
    if (n < 2) return 0;

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
    return denominator === 0 ? 0 : numerator / denominator;
}

/**
 * Find optimal lag for signal vs BTC ROC correlation.
 * @param {string[]} dates 
 * @param {number[]} signalValues 
 * @param {number[]} btcRocValues 
 * @param {number} minLag 
 * @param {number} maxLag 
 * @returns {{lag: number, corr: number}}
 */
export function findOptimalLag(dates, signalValues, btcRocValues, minLag = -15, maxLag = 120) {
    let bestLag = 0;
    let maxCorr = -1;

    for (let k = minLag; k <= maxLag; k += 3) {
        const x = [];
        const y = [];

        for (let i = 0; i < signalValues.length; i++) {
            let j = i + k;
            if (j >= 0 && j < btcRocValues.length) {
                const sig = signalValues[i];
                const roc = btcRocValues[j];
                if (sig != null && roc != null) {
                    x.push(sig);
                    y.push(roc);
                }
            }
        }

        const r = calculateCorrelation(x, y);
        if (r > maxCorr) {
            maxCorr = r;
            bestLag = k;
        }
    }
    return { lag: bestLag, corr: maxCorr };
}

/**
 * Calculate Z-score for an array of values.
 * Uses global mean and std dev (for backward compatibility).
 * For time-series analysis, prefer calculateRollingZScore.
 * @param {number[]} values 
 * @returns {number[]}
 */
export function calculateZScore(values) {
    if (!values || values.length === 0) return [];
    const valid = values.filter((v) => v !== null && v !== undefined);
    if (valid.length < 2) return values;

    const mean = valid.reduce((a, b) => a + b, 0) / valid.length;
    const variance = valid.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / valid.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return values.map(() => 0);

    return values.map((v) => (v === null || v === undefined ? null : (v - mean) / stdDev));
}

/**
 * Calculate ROLLING Z-score for time-series data.
 * For each point, calculates Z-score using only historical data within the lookback window.
 * This avoids look-ahead bias and captures regime changes.
 * 
 * @param {number[]} values - Array of values
 * @param {number} window - Lookback window in periods (e.g., 252 for 1 year of daily data)
 * @returns {number[]} Array of rolling Z-scores
 */
export function calculateRollingZScore(values, window = 252) {
    if (!values || values.length === 0) return [];

    return values.map((v, i) => {
        if (v === null || v === undefined) return null;

        // Get historical values within the lookback window (including current)
        const lookbackStart = Math.max(0, i + 1 - window);
        const historical = values.slice(lookbackStart, i + 1).filter(x => x !== null && x !== undefined);

        // Need minimum 20 data points for meaningful statistics
        if (historical.length < 20) return null;

        // Calculate mean and std dev of the historical window
        const mean = historical.reduce((a, b) => a + b, 0) / historical.length;
        const variance = historical.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / historical.length;
        const stdDev = Math.sqrt(variance);

        if (stdDev === 0) return 0;

        return (v - mean) / stdDev;
    });
}

/**
 * Calculate rolling percentile rank for an array of values.
 * For each value, computes what percentage of historical values are below it.
 * @param {number[]} values 
 * @param {number} window - Lookback window for percentile calculation (default: all history)
 * @returns {number[]} Array of percentile values (0-100)
 */
export function calculatePercentile(values, window = null) {
    if (!values || values.length === 0) return [];

    return values.map((v, i) => {
        if (v === null || v === undefined) return null;

        // Get historical values up to current point
        const lookback = window ? Math.min(window, i + 1) : i + 1;
        const historicalStart = Math.max(0, i + 1 - lookback);
        const historical = values.slice(historicalStart, i + 1).filter(x => x !== null && x !== undefined);

        if (historical.length < 2) return 50; // Default to 50th percentile if not enough data

        // Count how many values are below current value
        const below = historical.filter(x => x < v).length;
        return (below / (historical.length - 1)) * 100;
    });
}

/**
 * Calculate BTC Rate of Change.
 * @param {number[]} prices 
 * @param {string[]} dates 
 * @param {number} period 
 * @param {number} lag 
 * @returns {Array<{x: string, y: number}>}
 */
export function calculateBtcRoc(prices, dates, period, lag = 0) {
    if (!prices || !dates || prices.length !== dates.length) return [];
    if (period <= 0) return [];

    const rocData = [];
    for (let i = period; i < prices.length; i++) {
        const current = prices[i];
        const past = prices[i - period];

        if (past && past !== 0) {
            const roc = ((current - past) / past) * 100;
            rocData.push({ x: dates[i], y: roc });
        }
    }
    return rocData;
}

/**
 * Calculate historical regime shapes for Plotly charts.
 * @param {string[]} dates 
 * @param {number[]} gli - GLI impulse values
 * @param {number[]} netliq - Net liquidity impulse values
 * @returns {Array}
 */
export function calculateHistoricalRegimes(dates, gli, netliq) {
    if (!dates || !gli || !netliq) return [];

    const shapes = [];
    let currentRegime = null;
    let startIdx = 0;

    for (let i = 0; i < dates.length; i++) {
        const g = gli[i];
        const n = netliq[i];
        let r = "neutral";

        if (g > 0 && n > 0) r = "bullish";
        else if (g < 0 && n < 0) r = "bearish";

        if (r !== currentRegime) {
            if (currentRegime !== null) {
                shapes.push({
                    type: "rect",
                    xref: "x",
                    yref: "paper",
                    x0: dates[startIdx],
                    x1: dates[i],
                    y0: 0,
                    y1: 1,
                    fillcolor:
                        currentRegime === "bullish"
                            ? "rgba(16, 185, 129, 0.08)"
                            : currentRegime === "bearish"
                                ? "rgba(239, 68, 68, 0.08)"
                                : "rgba(148, 163, 184, 0.03)",
                    line: { width: 0 },
                    layer: "below",
                });
            }
            currentRegime = r;
            startIdx = i;
        }
    }

    // Final shape
    if (currentRegime !== null) {
        shapes.push({
            type: "rect",
            xref: "x",
            yref: "paper",
            x0: dates[startIdx],
            x1: dates[dates.length - 1],
            y0: 0,
            y1: 1,
            fillcolor:
                currentRegime === "bullish"
                    ? "rgba(16, 185, 129, 0.08)"
                    : currentRegime === "bearish"
                        ? "rgba(239, 68, 68, 0.08)"
                        : "rgba(148, 163, 184, 0.03)",
            line: { width: 0 },
            layer: "below",
        });
    }
    return shapes;
}
