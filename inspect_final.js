
const fs = require('fs');
const path = require('path');

const checkFile = (filePath) => {
    try {
        const fullPath = path.resolve(filePath);
        if (fs.existsSync(fullPath)) {
            console.log(`\n--- Inspecting ${filePath} ---`);
            const data = JSON.parse(fs.readFileSync(fullPath, 'utf8'));

            if (filePath.includes('currencies.json')) {
                console.log('Top keys:', Object.keys(data));
                // Look for vol
                function deepSearch(obj, k) {
                    if (k.includes('vol')) console.log(`  Found vol key: ${k}`);
                }
                const search = (o) => {
                    Object.keys(o).forEach(k => {
                        if (k.includes('vol') || k.includes('dxy')) console.log(`  Found key: ${k}`);
                        if (typeof o[k] === 'object' && o[k] !== null) search(o[k]);
                    });
                };
                // Limit recursion to avoid spam
                const keys = Object.keys(data);
                console.log('Sub-keys sample:', keys.slice(0, 10));
            }

            if (filePath.includes('us_system.json')) {
                console.log('Repo Operations keys:', Object.keys(data.repo_operations || {}));
                if (data.repo_operations) {
                    console.log('RRP Usage sample:', data.repo_operations.rrp_usage ? data.repo_operations.rrp_usage.slice(-5) : 'missing');
                }
            }

        }
    } catch (e) { console.error(e.message); }
};

['frontend/public/domains/currencies.json', 'frontend/public/domains/us_system.json'].forEach(checkFile);
