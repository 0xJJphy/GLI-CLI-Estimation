
const fs = require('fs');
const path = require('path');

// Load data
const legacyPath = path.join('backend', 'data', 'dashboard_data.json');
const cliPath = path.join('frontend', 'public', 'domains', 'cli.json');

if (!fs.existsSync(legacyPath) || !fs.existsSync(cliPath)) {
    console.error("Data files not found.");
    process.exit(1);
}

const legacyData = JSON.parse(fs.readFileSync(legacyPath));
const cliData = JSON.parse(fs.readFileSync(cliPath));

// Target date: 2024-01-05 (arbitrary recent date)
const targetDate = "2024-01-05";
const legacyIndex = legacyData.dates.indexOf(targetDate);

if (legacyIndex === -1) {
    console.error(`Date ${targetDate} not found in legacy data.`);
    process.exit(1);
}

// Map CLI dates to index (since CLI is now 1970-based and legacy is 2002-based)
// We need to find the index in CLI data that corresponds to the same date.
// But wait, the CLI JSON doesn't store dates! That's in shared.json.
const sharedPath = path.join('frontend', 'public', 'domains', 'shared.json');
if (!fs.existsSync(sharedPath)) {
    console.error("Shared dates file not found.");
    process.exit(1);
}
const sharedData = JSON.parse(fs.readFileSync(sharedPath));
const cliIndex = sharedData.dates.indexOf(targetDate);

if (cliIndex === -1) {
    console.error(`Date ${targetDate} not found in shared data.`);
    process.exit(1);
}

console.log(`Comparing data for date: ${targetDate}`);
console.log(`Legacy Index: ${legacyIndex}, CLI Index: ${cliIndex}`);

// Comparators
const compare = (label, legacyVal, cliVal) => {
    // Handle potential nulls
    if (legacyVal === null || legacyVal === undefined || cliVal === null || cliVal === undefined) {
        console.log(`[${label}] Legacy: ${legacyVal} | New: ${cliVal} | Diff: N/A | ?`);
        return;
    }
    const diff = Math.abs(legacyVal - cliVal);
    const match = diff < 0.0001;
    console.log(`[${label}] Legacy: ${legacyVal?.toFixed(4)} | New: ${cliVal?.toFixed(4)} | Diff: ${diff.toFixed(6)} | ${match ? '✅' : '❌'}`);
};

console.log("\n--- RAW VALUES ---");
// HY Spread
compare("HY Spread", legacyData.hy_spread[legacyIndex], cliData.raw.hy_spread[cliIndex]);
// NFCI Credit
compare("NFCI Credit", legacyData.nfci_credit[legacyIndex], cliData.raw.nfci_credit[cliIndex]);
// Lending
compare("Lending Std", legacyData.lending[legacyIndex], cliData.raw.lending_std[cliIndex]);

console.log("\n--- Z-SCORES ---");
// Legacy Z-scores are usually in signal_metrics
if (legacyData.signal_metrics) {
    // Note: Z-scores might be inverted in one but not the other. Math.abs check helps, but we want exactness.
    compare("HY Z-Score", legacyData.signal_metrics.hy_spread.zscore[legacyIndex], cliData.components.hy_spread_z[cliIndex]);
    compare("NFCI Credit Z", legacyData.signal_metrics.nfci_credit.zscore[legacyIndex], cliData.components.nfci_credit_z[cliIndex]);
}

console.log("\n--- PERCENTILES ---");
if (legacyData.signal_metrics) {
    compare("HY Pct", legacyData.signal_metrics.hy_spread.percentile[legacyIndex], cliData.components.hy_spread_pct[cliIndex]);
    compare("NFCI Credit Pct", legacyData.signal_metrics.nfci_credit.percentile[legacyIndex], cliData.components.nfci_credit_pct[cliIndex]);
}
