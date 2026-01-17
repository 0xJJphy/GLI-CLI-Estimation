
const fs = require('fs');
const path = require('path');

function loadJSON(p) {
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p));
}

const legacyPath = path.join('backend', 'data', 'dashboard_data.json');
const sharedPath = path.join('frontend', 'public', 'domains', 'shared.json');
const cliPath = path.join('frontend', 'public', 'domains', 'cli.json');
const systemPath = path.join('frontend', 'public', 'domains', 'us_system.json');
const treasuryPath = path.join('frontend', 'public', 'domains', 'treasury.json');

const legacy = loadJSON(legacyPath);
const shared = loadJSON(sharedPath);
const cli = loadJSON(cliPath);
const system = loadJSON(systemPath);
const treasury = loadJSON(treasuryPath);

if (!legacy || !shared || !cli || !system || !treasury) {
    console.error("Missing files.");
    process.exit(1);
}

// 1. Check Density
const sharedDates = shared.dates;
const uniqueDates = new Set(sharedDates);
console.log(`Shared Dates: ${sharedDates.length}. Unique: ${uniqueDates.size}. Duplicates: ${sharedDates.length - uniqueDates.size}`);
if (sharedDates.length !== uniqueDates.size) {
    console.log("❌ CRITICAL: shared.json still has duplicates!");
} else {
    console.log("✅ shared.json is deduplicated.");
}

// 2. Comparison Function
function compare(legacyKey, modValue, modZ, modPct, name, dateIndex, legacyDateIndex) {
    const lMetrics = legacy.signal_metrics[legacyKey];
    if (!lMetrics) {
        console.log(`⚠️ Legacy metrics not found for ${legacyKey}`);
        return;
    }

    const lRaw = lMetrics.raw ? lMetrics.raw[legacyDateIndex] : null;
    const lZ = lMetrics.zscore ? lMetrics.zscore[legacyDateIndex] : null;
    const lPct = lMetrics.percentile ? lMetrics.percentile[legacyDateIndex] : null;

    console.log(`\n--- ${name} ---`);
    console.log(`Raw: L=${lRaw?.toFixed(4)} | N=${modValue?.toFixed(4)} | Diff=${Math.abs(lRaw - modValue).toFixed(4)}`);
    console.log(`Z  : L=${lZ?.toFixed(4)} | N=${modZ?.toFixed(4)} | Diff=${Math.abs(lZ - modZ).toFixed(4)} ${Math.abs(lZ - modZ) < 0.5 ? '✅' : '❌'}`);
    console.log(`Pct: L=${lPct?.toFixed(4)} | N=${modPct?.toFixed(4)} | Diff=${Math.abs(lPct - modPct).toFixed(4)} ${Math.abs(lPct - modPct) < 10 ? '✅' : '❌'}`);
}

// Find a test date (recent but with data)
const targetDate = "2024-01-05";
const sIndex = sharedDates.indexOf(targetDate);
const lIndex = legacy.dates.indexOf(targetDate);

console.log(`Comparing date: ${targetDate} (Shared Idx: ${sIndex}, Legacy Idx: ${lIndex})`);

if (sIndex === -1 || lIndex === -1) {
    console.error("Target date not found.");
    process.exit(1);
}

// Compare HY Spread (CLI) - Note: Inverted logic handled?
// Legacy HY Z usually Low Spread -> Negative Z (Good).
// Modular HY Z (Raw) -> Low Spread -> Negative Z (Good).
compare('hy_spread',
    cli.raw.hy_spread[sIndex],
    cli.components.hy_spread_z[sIndex],
    cli.components.hy_spread_pct[sIndex],
    "HY SPREAD"
    , sIndex, lIndex
);

// Compare St Louis Stress (US System)
compare('st_louis_stress',
    system.st_louis_stress.total[sIndex],
    system.st_louis_stress.z_score[sIndex],
    system.st_louis_stress.percentile[sIndex],
    "ST LOUIS STRESS",
    sIndex, lIndex
);

// Compare 10Y Yield (Treasury)
compare('treasury_10y',
    treasury.yields['10y'][sIndex],
    treasury.yields['10y_z'][sIndex],
    treasury.yields['10y_pct'][sIndex],
    "10Y YIELD",
    sIndex, lIndex
);

// Compare Yield Curve 10y-2y
compare('yield_curve',
    treasury.curves['10y_2y'][sIndex],
    treasury.curves['10y_2y_z'][sIndex],
    treasury.curves['10y_2y_pct'][sIndex],
    "YIELD CURVE 10Y-2Y",
    sIndex, lIndex
);
