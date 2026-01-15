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
const DATA_BASE_URL = '';  // Base URL for data files (files are directly in public/domains/)
// Modular domain loading - fixed data mapping in loader functions
// loadM2TabData: spreads m2.economies.* -> m2.*
// loadOffshoreTabData: builds chart1_fred_proxy nested structure
const USE_MODULAR_DOMAINS = true;  // ENABLED for testing fixed mappings

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
            loadDomain("stablecoins"),
            loadDomain("shared"),
        ]);

        // Flatten nested structures for frontend compatibility
        const flattened = { ...stablecoins };

        // 1. Flatten Total ROCs
        if (stablecoins.total_rocs) {
            flattened.total_roc_7d = stablecoins.total_rocs["7d"];
            flattened.total_roc_1m = stablecoins.total_rocs["30d"]; // Frontend expects 1m, backend has 30d
            flattened.total_roc_3m = stablecoins.total_rocs["90d"]; // Frontend expects 3m, backend has 90d
            flattened.total_yoy = stablecoins.total_rocs["yoy"];
        }

        // 2. Flatten Total ROC Z-Scores
        if (stablecoins.total_rocs_z) {
            flattened.total_roc_7d_z = stablecoins.total_rocs_z["7d"];
            flattened.total_roc_1m_z = stablecoins.total_rocs_z["30d"];
            flattened.total_roc_3m_z = stablecoins.total_rocs_z["90d"];
        }

        // 3. New Metrics: Accel & Total Dominance
        if (stablecoins.total_accel_z) {
            flattened.total_accel_z = stablecoins.total_accel_z;
        }
        if (stablecoins.crypto_dominance) {
            flattened.total_dominance = stablecoins.crypto_dominance;
        }

        // 4. Aggregate Depeg Events
        if (stablecoins.depeg_events && !Array.isArray(stablecoins.depeg_events)) {
            let allEvents = [];
            Object.entries(stablecoins.depeg_events).forEach(([coin, events]) => {
                if (Array.isArray(events)) {
                    allEvents = allEvents.concat(
                        events.map((e) => ({ ...e, stablecoin: coin }))
                    );
                }
            });
            // Sort by date ascending
            allEvents.sort(
                (a, b) =>
                    new Date(a.date).getTime() - new Date(b.date).getTime(),
            );
            flattened.depeg_events = allEvents;
        }

        // 4. Flatten Stable Index Dom
        if (stablecoins.stable_index_rocs) {
            flattened.stable_index_dom_roc_7d = stablecoins.stable_index_rocs["7d"];
            flattened.stable_index_dom_roc_30d = stablecoins.stable_index_rocs["30d"];
            flattened.stable_index_dom_roc_90d = stablecoins.stable_index_rocs["90d"];
            flattened.stable_index_dom_roc_180d = stablecoins.stable_index_rocs["180d"];
            flattened.stable_index_dom_roc_yoy = stablecoins.stable_index_rocs["yoy"];
        }
        if (stablecoins.stable_index_rocs_z) {
            flattened.stable_index_dom_roc_7d_z = stablecoins.stable_index_rocs_z["7d"];
            flattened.stable_index_dom_roc_30d_z = stablecoins.stable_index_rocs_z["30d"];
            flattened.stable_index_dom_roc_90d_z = stablecoins.stable_index_rocs_z["90d"];
        }
        if (stablecoins.stable_index_rocs_pct) {
            flattened.stable_index_dom_roc_7d_pct = stablecoins.stable_index_rocs_pct["7d"];
            flattened.stable_index_dom_roc_30d_pct = stablecoins.stable_index_rocs_pct["30d"];
            flattened.stable_index_dom_roc_90d_pct = stablecoins.stable_index_rocs_pct["90d"];
        }

        // 5. Flatten Custom Stables Dom ROCs
        if (stablecoins.custom_stables_dom_rocs) {
            flattened.custom_stables_dom_roc_7d = stablecoins.custom_stables_dom_rocs["7d"];
            flattened.custom_stables_dom_roc_30d = stablecoins.custom_stables_dom_rocs["30d"];
            flattened.custom_stables_dom_roc_90d = stablecoins.custom_stables_dom_rocs["90d"];
            flattened.custom_stables_dom_roc_180d = stablecoins.custom_stables_dom_rocs["180d"];
            flattened.custom_stables_dom_roc_yoy = stablecoins.custom_stables_dom_rocs["yoy"];
        }
        if (stablecoins.custom_stables_dom_rocs_z) {
            flattened.custom_stables_dom_roc_7d_z = stablecoins.custom_stables_dom_rocs_z["7d"];
            flattened.custom_stables_dom_roc_30d_z = stablecoins.custom_stables_dom_rocs_z["30d"];
            flattened.custom_stables_dom_roc_90d_z = stablecoins.custom_stables_dom_rocs_z["90d"];
        }
        if (stablecoins.custom_stables_dom_rocs_pct) {
            flattened.custom_stables_dom_roc_7d_pct = stablecoins.custom_stables_dom_rocs_pct["7d"];
            flattened.custom_stables_dom_roc_30d_pct = stablecoins.custom_stables_dom_rocs_pct["30d"];
            flattened.custom_stables_dom_roc_90d_pct = stablecoins.custom_stables_dom_rocs_pct["90d"];
        }

        return {
            ...flattened,
            btc: shared.btc,
            dates: shared.dates, // Include dates for SFAI chart
        };
    } catch (e) {
        console.warn("Falling back to legacy data for stablecoins", e);
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

/**
 * Load data for NarrativesTab / CryptoTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for crypto/narratives tab
 */
export async function loadCryptoTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            crypto_analytics: legacyData?.crypto_analytics || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [crypto, shared] = await Promise.all([
            loadDomain('crypto'),
            loadDomain('shared')
        ]);

        return {
            crypto_analytics: crypto,
            btc: shared.btc,
            dates: shared.dates
        };
    } catch {
        console.warn('Falling back to legacy data for crypto');
        return {
            crypto_analytics: legacyData?.crypto_analytics || {},
            dates: legacyData?.dates || []
        };
    }
}

/**
 * Load data for FedForecastsTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for Fed Forecasts tab
 */
export async function loadFedForecastsTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            fed_forecasts: legacyData?.fed_forecasts || {},
            inflation_swaps: legacyData?.inflation_swaps || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [fed_forecasts, shared] = await Promise.all([
            loadDomain('fed_forecasts'),
            loadDomain('shared')
        ]);

        return {
            fed_forecasts,
            inflation_swaps: fed_forecasts.inflation_swaps || {},
            dates: shared.dates
        };
    } catch {
        console.warn('Falling back to legacy data for Fed Forecasts');
        return {
            fed_forecasts: legacyData?.fed_forecasts || {},
            inflation_swaps: legacyData?.inflation_swaps || {},
            dates: legacyData?.dates || []
        };
    }
}

/**
 * Load data for RegimesTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for Regimes tab
 */
export async function loadRegimesTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            macro_regime: legacyData?.macro_regime || {},
            regime_v2a: legacyData?.regime_v2a || {},
            regime_v2b: legacyData?.regime_v2b || {},
            cli_v2: legacyData?.cli_v2 || {},
            stress_historical: legacyData?.stress_historical || {},
            signals: legacyData?.signals || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [macro_regime, shared, cli, crypto] = await Promise.all([
            loadDomain('macro_regime'),
            loadDomain('shared'),
            loadDomain('cli'),
            loadDomain('crypto')
        ]);

        return {
            macro_regime,
            // These might be nested in macro_regime or top-level in legacy
            // We favor the modular structure but provide compatibility
            regime_v2a: macro_regime.v2a || macro_regime,
            regime_v2b: macro_regime.v2b || macro_regime,
            cli_v2: cli.v2 || cli,
            stress_historical: macro_regime.stress_historical || macro_regime.stress || {},
            signals: macro_regime.signals || {},
            btc: shared.btc || {},
            dates: shared.dates
        };
    } catch (error) {
        console.warn('Falling back to legacy data for Regimes:', error);
        return {
            macro_regime: legacyData?.macro_regime || {},
            regime_v2a: legacyData?.regime_v2a || {},
            regime_v2b: legacyData?.regime_v2b || {},
            cli_v2: legacyData?.cli_v2 || {},
            stress_historical: legacyData?.stress_historical || {},
            signals: legacyData?.signals || {},
            dates: legacyData?.dates || []
        };
    }
}


/**
 * Load data for GlobalM2Tab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for M2 tab
 */
export async function loadM2TabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            m2: legacyData?.m2 || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [m2, shared] = await Promise.all([
            loadDomain('m2'),
            loadDomain('shared')
        ]);

        // Map modular m2.economies.* to expected m2.* format
        // Modular: { economies: { us: [], eu: [] }, total: [], rocs: {}, weights: {} }
        // Expected: { us: [], eu: [], total: [], rocs: {} }
        const mappedM2 = {
            total: m2.total || [],
            rocs: m2.rocs || {},
            // Spread all economy data directly into m2
            ...(m2.economies || {}),
        };

        return {
            m2: mappedM2,
            // m2_weights and m2_bank_rocs are expected at top level by GlobalM2Tab
            m2_weights: m2.weights || {},
            m2_bank_rocs: m2.economy_rocs || {},
            dates: shared.dates
        };
    } catch (error) {
        console.warn('Falling back to legacy data for M2:', error);
        return {
            m2: legacyData?.m2 || {},
            dates: legacyData?.dates || []
        };
    }
}

/**
 * Load data for OffshoreLiquidityTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for Offshore Liquidity tab
 */
export async function loadOffshoreTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            offshore_liquidity: legacyData?.offshore_liquidity || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [offshore, shared] = await Promise.all([
            loadDomain('offshore'),
            loadDomain('shared')
        ]);

        // Map modular flat structure to expected nested format
        // Modular: { obfr_effr_spread: [], cb_swaps: [], stress_score: [], ... }
        // Expected: { chart1_fred_proxy: { obfr_effr_spread: [], cb_swaps_b: [], ... }, chart2_xccy_diy: {}, thresholds: {} }

        const dates = shared.dates || [];
        const lastIdx = dates.length - 1;

        return {
            offshore_liquidity: {
                chart1_fred_proxy: {
                    dates: dates,
                    obfr: offshore.obfr || [],
                    effr: offshore.effr || [],
                    obfr_effr_spread: offshore.obfr_effr_spread || [],
                    cb_swaps_b: offshore.cb_swaps || [],
                    stress_level: offshore.stress_level || 'normal',
                    stress_score: Array.isArray(offshore.stress_score)
                        ? offshore.stress_score[offshore.stress_score.length - 1]
                        : offshore.stress_score || 0,
                    latest: {
                        obfr_effr_spread: offshore.obfr_effr_spread?.[lastIdx],
                        spread_zscore: offshore.obfr_effr_spread_z?.[lastIdx],
                        cb_swaps_b: offshore.cb_swaps?.[lastIdx],
                    }
                },
                chart2_xccy_diy: offshore.xccy_basis_ref || null,
                thresholds: legacyData?.offshore_liquidity?.thresholds || {
                    obfr_effr: { normal: 3, elevated: 6, stressed: 10, critical: 15 },
                    cb_swaps: { active: 0.1, elevated: 10, stressed: 50, crisis: 100 },
                    xccy: { normal: -10, elevated: -20, stressed: -35, crisis: -50 }
                },
                analysis: legacyData?.offshore_liquidity?.analysis || {}
            },
            dates: dates
        };
    } catch (error) {
        console.warn('Falling back to legacy data for Offshore:', error);
        return {
            offshore_liquidity: legacyData?.offshore_liquidity || {},
            dates: legacyData?.dates || []
        };
    }
}

/**
 * Load data for UsDebtTab / Treasury
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for Treasury tab
 */
export async function loadTreasuryTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            treasury: legacyData?.treasury || {},
            tips: legacyData?.tips || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [treasury, shared] = await Promise.all([
            loadDomain('treasury'),
            loadDomain('shared')
        ]);

        return {
            treasury,
            tips: treasury.tips || {},
            dates: shared.dates
        };
    } catch {
        console.warn('Falling back to legacy data for Treasury');
        return {
            treasury: legacyData?.treasury || {},
            tips: legacyData?.tips || {},
            dates: legacyData?.dates || []
        };
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
    loadCryptoTabData,
    loadFedForecastsTabData,
    loadRegimesTabData,
    loadM2TabData,
    loadOffshoreTabData,
    loadTreasuryTabData,
};
