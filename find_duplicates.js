const fs = require('fs');

const content = fs.readFileSync('frontend/src/stores/settingsStore.js', 'utf8');

function findDuplicates(objStr, langName, startLine) {
    const keys = [];
    const duplicates = [];
    const lines = objStr.split('\n');
    lines.forEach((line, index) => {
        const match = line.match(/^\s*([a-z0-9_]+):/);
        if (match) {
            const key = match[1];
            if (keys.includes(key)) {
                duplicates.push({ key, absLine: startLine + index + 1 });
            }
            keys.push(key);
        }
    });
    return duplicates;
}

const enMatch = content.match(/en: \{([\s\S]*?)\n\s\s\s\s\},/);
const esMatch = content.match(/es: \{([\s\S]*?)\n\s\s\s\s\},/);

if (enMatch) {
    const enStart = content.indexOf('en: {') + 1;
    const initialLines = content.substring(0, content.indexOf('en: {')).split('\n').length;
    console.log('--- English Duplicates ---');
    console.log(findDuplicates(enMatch[1], 'en', initialLines));
}

if (esMatch) {
    const esStart = content.indexOf('es: {') + 1;
    const initialLines = content.substring(0, content.indexOf('es: {')).split('\n').length;
    console.log('--- Spanish Duplicates ---');
    console.log(findDuplicates(esMatch[1], 'es', initialLines));
}
