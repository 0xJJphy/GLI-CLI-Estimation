
const fs = require('fs');
const path = require('path');

const sharedPath = path.join('frontend', 'public', 'domains', 'shared.json');
const sharedData = JSON.parse(fs.readFileSync(sharedPath));

const dates = sharedData.dates;
const uniqueDates = new Set(dates);

console.log(`Total Dates: ${dates.length}`);
console.log(`Unique Dates: ${uniqueDates.size}`);
console.log(`Duplicates: ${dates.length - uniqueDates.size}`);
