/**
 * analytics.js
 * Utility functions for frontend financial data analysis.
 */

/**
 * Calculates the Rate of Change (ROC) for a given series.
 * ROC% = ((Current / Past) - 1) * 100
 * 
 * @param {Array<string>} dates - Array of ISO dates
 * @param {Array<number>} values - Array of numeric values
 * @param {number} period - ROC period in days
 * @returns {Object} { x: Array<string>, y: Array<number> }
 */
export function calculateROC(dates, values, period) {
    if (!dates || !values || dates.length !== values.length || period <= 0) {
        return { x: [], y: [] };
    }

    const rocX = [];
    const rocY = [];

    for (let i = period; i < values.length; i++) {
        const current = values[i];
        const past = values[i - period];

        if (current !== null && past !== null && past !== 0) {
            const roc = ((current / past) - 1) * 100;
            rocX.push(dates[i]);
            rocY.push(roc);
        }
    }

    return { x: rocX, y: rocY };
}

/**
 * Normalizes a numeric series using Z-Score (standard deviation from mean).
 * 
 * @param {Array<number>} values - Array of numeric values
 * @returns {Array<number>} Normalized values
 */
export function normalizeZScore(values) {
    if (!values || values.length === 0) return [];

    const valid = values.filter(v => v !== null && v !== undefined);
    if (valid.length < 2) return values.map(v => v !== null ? 0 : null);

    const mean = valid.reduce((a, b) => a + b, 0) / valid.length;
    const variance = valid.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / valid.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return values.map(v => v !== null ? 0 : null);

    return values.map(v => (v === null || v === undefined) ? null : (v - mean) / stdDev);
}

/**
 * Aligns an overlay series to the timescale of a base series.
 * Useful for plotting superimposed ROCs.
 * 
 * @param {Object} base - { x: Array, y: Array }
 * @param {Object} overlay - { x: Array, y: Array }
 * @returns {Object} { x: Array, yBase: Array, yOverlay: Array }
 */
export function alignSeries(base, overlay) {
    if (!base.x.length || !overlay.x.length) return { x: base.x, yBase: base.y, yOverlay: [] };

    const overlayMap = new Map();
    overlay.x.forEach((d, i) => overlayMap.set(d, overlay.y[i]));

    const alignedY = base.x.map(date => overlayMap.get(date) ?? null);

    return {
        x: base.x,
        yBase: base.y,
        yOverlay: alignedY,
    };
}

/**
 * Shifts a series by a given number of days and extends the timeline if necessary.
 * 
 * @param {Array<string>} dates - Original dates
 * @param {Array<number>} values - Original values
 * @param {number} offsetDays - Days to shift (positive = forward/right, negative = backward/left)
 * @returns {Object} { x: Array<string>, y: Array<number> }
 */
export function shiftSeries(dates, values, offsetDays) {
    if (!dates || !values || offsetDays === 0) return { x: dates, y: values };

    const shiftedX = [];
    const shiftedY = [];

    for (let i = 0; i < dates.length; i++) {
        if (values[i] === null || values[i] === undefined) continue;

        const d = new Date(dates[i]);
        d.setDate(d.getDate() + offsetDays);
        shiftedX.push(d.toISOString().split('T')[0]);
        shiftedY.push(values[i]);
    }

    return { x: shiftedX, y: shiftedY };
}

/**
 * Formats a generic { x: dates, y: values } series into TradingView [{ time, value }] format.
 * 
 * @param {Object} series - Object with x (dates) and y (values) arrays
 * @returns {Array<Object>} - Array of { time, value } points
 */
export function formatForTV(series) {
    if (!series || !series.x || !series.y) return [];

    const points = [];
    for (let i = 0; i < series.x.length; i++) {
        const val = series.y[i];
        if (val === null || val === undefined || isNaN(val)) continue;

        points.push({
            time: series.x[i],
            value: val
        });
    }

    // Ensure chronological order
    return points.sort((a, b) => (a.time > b.time ? 1 : -1));
}
