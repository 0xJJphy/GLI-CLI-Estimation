
const fs = require('fs');
const path = require('path');

const filePaths = [
    'frontend/public/domains/us_system.json',
    'frontend/public/domains/cli.json',
    'frontend/public/domains/treasury.json'
];

filePaths.forEach(filePath => {
    try {
        const fullPath = path.resolve(filePath);
        if (fs.existsSync(fullPath)) {
            console.log(`\n--- Inspecting ${filePath} ---`);
            const data = JSON.parse(fs.readFileSync(fullPath, 'utf8'));

            // List top level keys
            const keys = Object.keys(data);
            console.log('Top level keys:', keys.slice(0, 20)); // Limit to first 20

            // Drill down into 'metrics' or similar if it exists, or just check the first few keys
            keys.slice(0, 10).forEach(key => {
                const val = data[key];
                if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
                    console.log(`  Keys in [${key}]:`, Object.keys(val).slice(0, 20));
                }
            });

            // Specifically look for target keywords
            const keywords = ['yield', 'corporate', 'repo', 'volume', 'dxy', 'vol', 'spread', 'divergence', 'cli', 'gli'];
            console.log(`  Searching for keywords: ${keywords.join(', ')}`);

            function search(obj, prefix = '') {
                Object.keys(obj).forEach(k => {
                    const hit = keywords.some(kw => k.toLowerCase().includes(kw));
                    if (hit) console.log(`    MATCH: ${prefix}${k}`);
                    // Shallow recursion for one level if it's a generic container
                    if (['metrics', 'data', 'indicators'].includes(k) && typeof obj[k] === 'object') {
                        Object.keys(obj[k]).forEach(subK => {
                            if (keywords.some(kw => subK.toLowerCase().includes(kw))) {
                                console.log(`    MATCH (deep): ${prefix}${k}.${subK}`);
                            }
                        })
                    }
                });
            }
            search(data);
        } else {
            console.log(`File not found: ${filePath}`);
        }
    } catch (e) {
        console.error(`Error reading ${filePath}:`, e.message);
    }
});
