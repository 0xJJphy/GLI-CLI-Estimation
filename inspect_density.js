
const fs = require('fs');
const path = require('path');

const legacyPath = path.join('backend', 'data', 'dashboard_data.json');
const sharedPath = path.join('frontend', 'public', 'domains', 'shared.json');

const legacyData = JSON.parse(fs.readFileSync(legacyPath));
const sharedData = JSON.parse(fs.readFileSync(sharedPath));

console.log(`Legacy Dates Length: ${legacyData.dates.length}`);
console.log(`Shared Dates Length: ${sharedData.dates.length}`);

const lStart = legacyData.dates[0];
const lEnd = legacyData.dates[legacyData.dates.length - 1];
console.log(`Legacy Range: ${lStart} to ${lEnd}`);

const sStart = sharedData.dates[0];
const sEnd = sharedData.dates[sharedData.dates.length - 1];
console.log(`Shared Range: ${sStart} to ${sEnd}`);

// Calculate density (approx)
const daysBetween = (d1, d2) => (new Date(d2) - new Date(d1)) / (1000 * 60 * 60 * 24);

const lDays = daysBetween(lStart, lEnd);
const sDays = daysBetween(sStart, sEnd);

console.log(`Legacy Density: ${legacyData.dates.length / lDays} pts/day`);
console.log(`Shared Density: ${sharedData.dates.length / sDays} pts/day`);
