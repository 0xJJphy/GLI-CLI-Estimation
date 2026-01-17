
const fs = require('fs');
const path = require('path');

const legacyPath = path.join('backend', 'data', 'dashboard_data.json');
const data = JSON.parse(fs.readFileSync(legacyPath));
const dates = data.dates;

function findStart(key, subKey) {
    let series = null;
    if (subKey && data.signal_metrics[key]) {
        series = data.signal_metrics[key][subKey];
    } else if (data.signal_metrics[key]) {
        // handle case where key is direct
        series = data.signal_metrics[key].raw || null;
    }

    if (!series) {
        // Try top level if not in signal_metrics
        if (data[key]) series = data[key];
        else return "Key Not Found";
    }

    // Find first non-null
    for (let i = 0; i < series.length; i++) {
        if (series[i] !== null && series[i] !== undefined) {
            return `${dates[i]} (Index ${i})`;
        }
    }
    return "All Null";
}

console.log("Legacy Start Dates:");
console.log("HY Spread:", findStart('hy_spread', 'raw'));
console.log("St Louis Stress:", findStart('st_louis_stress', 'total')); // or raw?
console.log("Treasury 10Y:", findStart('treasury_10y', 'raw'));
console.log("Yield Curve:", findStart('yield_curve', 'raw'));
console.log("NFCI Credit:", findStart('nfci_credit', 'raw'));
