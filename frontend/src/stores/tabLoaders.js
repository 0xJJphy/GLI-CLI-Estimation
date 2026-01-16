/**
 * Tab-specific Domain Loaders
 * 
 * Each tab can load just the domain data it needs without affecting others.
 * This allows incremental migration while keeping legacy loading as default.
 */

import { writable, get } from 'svelte/store';

// Cache for loaded domain data
const domainCache = {};

/**
 * Load a specific domain JSON file.
 * @param {string} domainName - Name of the domain (e.g., 'stablecoins', 'currencies')
 * @returns {Promise<object|null>}
 */
export async function loadDomain(domainName) {
    // Return from cache if available
    if (domainCache[domainName]) {
        return domainCache[domainName];
    }

    try {
        const response = await fetch(`/domains/${domainName}.json`);
        if (!response.ok) {
            console.warn(`[TabLoader] Failed to load ${domainName}: ${response.status}`);
            return null;
        }
        const data = await response.json();
        domainCache[domainName] = data;
        return data;
    } catch (error) {
        console.error(`[TabLoader] Error loading ${domainName}:`, error);
        return null;
    }
}

/**
 * Load multiple domains in parallel.
 * @param {string[]} domainNames - Array of domain names to load
 * @returns {Promise<Record<string, object>>}
 */
export async function loadDomains(domainNames) {
    const results = await Promise.all(
        domainNames.map(async (name) => {
            const data = await loadDomain(name);
            return { name, data };
        })
    );

    return results.reduce((acc, { name, data }) => {
        if (data) acc[name] = data;
        return acc;
    }, {});
}

/**
 * Create a store for tab-specific data that loads from domains.
 * Falls back to legacy dashboardData if domain loading fails.
 * 
 * @param {string[]} requiredDomains - Domains this tab needs
 * @param {function} transformer - Function to transform domain data to tab format
 * @returns {{ data: Writable, loading: Writable, error: Writable, load: function }}
 */
export function createTabStore(requiredDomains, transformer) {
    const data = writable(null);
    const loading = writable(false);
    const error = writable(null);

    async function load() {
        loading.set(true);
        error.set(null);

        try {
            const domains = await loadDomains(requiredDomains);

            // Check if all required domains loaded
            const missingDomains = requiredDomains.filter(d => !domains[d]);
            if (missingDomains.length > 0) {
                console.warn('[TabStore] Missing domains:', missingDomains);
                throw new Error(`Missing domains: ${missingDomains.join(', ')}`);
            }

            // Transform domain data to tab format
            const transformedData = transformer(domains);
            data.set(transformedData);

        } catch (err) {
            console.error('[TabStore] Load failed:', err);
            error.set(err.message);
        } finally {
            loading.set(false);
        }
    }

    return { data, loading, error, load };
}

// ============================================================
// TAB-SPECIFIC LOADERS
// Each loader returns data in the format the tab expects
// ============================================================

/**
 * StableCoinsTab data loader
 */
export const stablecoinsTabStore = createTabStore(
    ['stablecoins', 'shared'],
    (domains) => {
        const sc = domains.stablecoins;
        const shared = domains.shared;

        return {
            dates: shared.dates,
            btc: shared.btc,
            stablecoins: sc,
        };
    }
);

/**
 * CurrenciesTab data loader
 */
export const currenciesTabStore = createTabStore(
    ['currencies', 'shared'],
    (domains) => {
        const curr = domains.currencies;
        const shared = domains.shared;

        return {
            dates: curr.dates || shared.dates,
            currencies: curr,
            btc: shared.btc,
        };
    }
);

/**
 * OffshoreLiquidityTab data loader
 */
export const offshoreTabStore = createTabStore(
    ['offshore', 'shared'],
    (domains) => {
        const off = domains.offshore;
        const shared = domains.shared;

        return {
            dates: shared.dates,
            offshore_liquidity: off,
        };
    }
);

/**
 * GlobalM2Tab data loader
 */
export const m2TabStore = createTabStore(
    ['m2', 'shared'],
    (domains) => {
        const m2 = domains.m2;
        const shared = domains.shared;

        return {
            dates: shared.dates,
            m2: {
                total: m2.total,
                us: m2.economies?.us || [],
                eu: m2.economies?.eu || [],
                cn: m2.economies?.cn || [],
                jp: m2.economies?.jp || [],
                uk: m2.economies?.uk || m2.economies?.gb || [],
                ca: m2.economies?.ca || [],
                au: m2.economies?.au || [],
                in: m2.economies?.in || [],
                ch: m2.economies?.ch || [],
                ru: m2.economies?.ru || [],
                br: m2.economies?.br || [],
                kr: m2.economies?.kr || [],
                mx: m2.economies?.mx || [],
                my: m2.economies?.my || [],
                rocs: m2.rocs,
            },
            m2_weights: m2.weights,
            m2_bank_rocs: m2.economy_rocs,
        };
    }
);

/**
 * UsSystemTab data loader
 */
export const usSystemTabStore = createTabStore(
    ['us_system', 'shared'],
    (domains) => {
        const us = domains.us_system;
        const shared = domains.shared;

        return {
            dates: shared.dates,
            us_net_liq: us.net_liquidity,
            us_net_liq_rrp: us.rrp,
            us_net_liq_tga: us.tga,
            us_net_liq_reserves: us.bank_reserves,
            us_net_liq_rocs: us.net_liq_rocs,
            us_system_metrics: us.metrics,
            repo_operations: us.repo_operations,
            gli: {
                fed: shared.central_banks?.fed || [],
            },
        };
    }
);

/**
 * Clear all cached domain data
 */
export function clearDomainCache() {
    Object.keys(domainCache).forEach(key => delete domainCache[key]);
}
