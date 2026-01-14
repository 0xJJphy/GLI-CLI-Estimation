/**
 * Domain Data Loader
 * 
 * Loads data from modular domain JSON files.
 * Provides backward compatibility with dashboard_data.json while
 * enabling gradual migration to domain-specific data.
 * 
 * Usage:
 *   import { loadDomain, loadDomains, getDomainData } from './domainLoader.js';
 *   
 *   // Load single domain
 *   const currencies = await loadDomain('currencies');
 *   
 *   // Load multiple domains
 *   const { currencies, gli, stablecoins } = await loadDomains(['currencies', 'gli', 'stablecoins']);
 *   
 *   // Get dates (shared across all domains)
 *   const dates = await loadDomain('shared').then(d => d.dates);
 */

// Domain configuration
const DOMAIN_CONFIG = {
    shared: { path: 'domains/shared.json', description: 'Shared data (dates, BTC, CBs)' },
    gli: { path: 'domains/gli.json', description: 'Global Liquidity Index' },
    m2: { path: 'domains/m2.json', description: 'Global M2 Money Supply' },
    us_system: { path: 'domains/us_system.json', description: 'US Fed System' },
    cli: { path: 'domains/cli.json', description: 'Credit Liquidity Index' },
    treasury: { path: 'domains/treasury.json', description: 'Treasury yields/curves' },
    stablecoins: { path: 'domains/stablecoins.json', description: 'Stablecoin analytics' },
    currencies: { path: 'domains/currencies.json', description: 'DXY, FX pairs' },
    crypto: { path: 'domains/crypto.json', description: 'Crypto regimes/narratives' },
    fed_forecasts: { path: 'domains/fed_forecasts.json', description: 'FOMC, inflation' },
    macro_regime: { path: 'domains/macro_regime.json', description: 'Macro regime scoring' },
    offshore: { path: 'domains/offshore.json', description: 'Offshore liquidity' },
    metadata: { path: 'domains/metadata.json', description: 'Processing metadata' },
};

// Cache for loaded domains
const domainCache = new Map();

// Configuration
const DATA_BASE_URL = '/data';  // Base URL for data files
const USE_MODULAR_DOMAINS = false;  // Feature flag - set true to enable domain loading

/**
 * Load a single domain's data
 * @param {string} domainName - Name of the domain to load
 * @param {boolean} useCache - Whether to use cached data (default: true)
 * @returns {Promise<Object>} Domain data
 */
export async function loadDomain(domainName, useCache = true) {
    if (!DOMAIN_CONFIG[domainName]) {
        throw new Error(`Unknown domain: ${domainName}`);
    }

    // Check cache
    if (useCache && domainCache.has(domainName)) {
        return domainCache.get(domainName);
    }

    const config = DOMAIN_CONFIG[domainName];
    const url = `${DATA_BASE_URL}/${config.path}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load ${domainName}: ${response.status}`);
        }

        const data = await response.json();
        domainCache.set(domainName, data);
        return data;
    } catch (error) {
        console.error(`Error loading domain ${domainName}:`, error);
        throw error;
    }
}

/**
 * Load multiple domains in parallel
 * @param {string[]} domainNames - Array of domain names to load
 * @returns {Promise<Object>} Object with domain data keyed by name
 */
export async function loadDomains(domainNames) {
    const results = await Promise.all(
        domainNames.map(async (name) => {
            try {
                const data = await loadDomain(name);
                return [name, data];
            } catch (error) {
                console.warn(`Failed to load domain ${name}:`, error);
                return [name, null];
            }
        })
    );

    return Object.fromEntries(results);
}

/**
 * Get shared dates from the shared domain
 * @returns {Promise<string[]>} Array of date strings
 */
export async function getSharedDates() {
    const shared = await loadDomain('shared');
    return shared.dates || [];
}

/**
 * Resolve a domain reference (e.g., 'shared.btc' -> actual data)
 * @param {string} reference - Reference string like 'shared.btc'
 * @returns {Promise<any>} Resolved data
 */
export async function resolveReference(reference) {
    const [domain, ...path] = reference.split('.');
    const domainData = await loadDomain(domain);

    return path.reduce((obj, key) => obj?.[key], domainData);
}

/**
 * Clear the domain cache
 */
export function clearDomainCache() {
    domainCache.clear();
}

/**
 * Get list of available domains
 * @returns {Object} Domain configuration
 */
export function getAvailableDomains() {
    return { ...DOMAIN_CONFIG };
}

/**
 * Check if domain files exist (for development)
 * @returns {Promise<Object>} Status of each domain
 */
export async function checkDomainStatus() {
    const status = {};

    for (const [name, config] of Object.entries(DOMAIN_CONFIG)) {
        try {
            const response = await fetch(`${DATA_BASE_URL}/${config.path}`, { method: 'HEAD' });
            status[name] = {
                available: response.ok,
                description: config.description
            };
        } catch {
            status[name] = {
                available: false,
                description: config.description
            };
        }
    }

    return status;
}

// ============================================================
// TAB-SPECIFIC DATA LOADERS
// ============================================================
// These functions provide the correct domain data for each tab,
// with fallback to legacy dashboard_data.json

/**
 * Load data for CurrenciesTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for currencies tab
 */
export async function loadCurrenciesTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return legacyData?.currencies || {};
    }

    try {
        const currencies = await loadDomain('currencies');
        return currencies;
    } catch {
        console.warn('Falling back to legacy data for currencies');
        return legacyData?.currencies || {};
    }
}

/**
 * Load data for StableCoinsTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for stablecoins tab
 */
export async function loadStablecoinsTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return legacyData?.stablecoins || {};
    }

    try {
        const [stablecoins, shared] = await Promise.all([
            loadDomain('stablecoins'),
            loadDomain('shared')
        ]);

        // Merge BTC data from shared domain
        return {
            ...stablecoins,
            btc: shared.btc
        };
    } catch {
        console.warn('Falling back to legacy data for stablecoins');
        return legacyData?.stablecoins || {};
    }
}

/**
 * Load data for GlobalFlowsCbTab (GLI)
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for GLI tab
 */
export async function loadGLITabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            gli: legacyData?.gli || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [gli, shared] = await Promise.all([
            loadDomain('gli'),
            loadDomain('shared')
        ]);

        return {
            gli: {
                ...gli,
                // CB data comes from shared domain
                ...shared.central_banks
            },
            dates: shared.dates
        };
    } catch {
        console.warn('Falling back to legacy data for GLI');
        return {
            gli: legacyData?.gli || {},
            dates: legacyData?.dates || []
        };
    }
}

/**
 * Load data for USSystemTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for US System tab
 */
export async function loadUSSystemTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return legacyData;
    }

    try {
        const [us_system, shared] = await Promise.all([
            loadDomain('us_system'),
            loadDomain('shared')
        ]);

        return {
            us_net_liq: {
                net_liquidity: us_system.net_liquidity,
                fed: shared.central_banks?.fed,
                rrp: us_system.rrp,
                tga: us_system.tga,
                bank_reserves: us_system.bank_reserves,
                ...us_system.metrics
            },
            dates: shared.dates
        };
    } catch {
        console.warn('Falling back to legacy data for US System');
        return legacyData;
    }
}

export default {
    loadDomain,
    loadDomains,
    getSharedDates,
    resolveReference,
    clearDomainCache,
    getAvailableDomains,
    checkDomainStatus,
    // Tab loaders
    loadCurrenciesTabData,
    loadStablecoinsTabData,
    loadGLITabData,
    loadUSSystemTabData,
};
