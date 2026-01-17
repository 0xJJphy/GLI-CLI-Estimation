
const fs = require('fs');
const path = require('path');

const legacyPath = path.join('backend', 'data', 'dashboard_data.json');
const data = JSON.parse(fs.readFileSync(legacyPath));

console.log("Top level keys:", Object.keys(data));
if (data.treasury) console.log("Treasury keys:", Object.keys(data.treasury));
if (data.us_net_liq) console.log("Net Liq keys (if dict):", typeof data.us_net_liq);
if (data.st_louis_stress) console.log("St Louis Stress type:", typeof data.st_louis_stress);
if (data.signal_metrics) {
    console.log("Signal Metrics keys:", Object.keys(data.signal_metrics));
    if (data.signal_metrics.hy_spread) console.log("HY Spread metrics:", Object.keys(data.signal_metrics.hy_spread));
}
if (data.yield_curve) console.log("Yield Curve keys:", typeof data.yield_curve);
