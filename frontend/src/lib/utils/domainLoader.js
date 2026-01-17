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
        console.log('[CurrenciesLoader] Successfully loaded from domain JSONs');
        return currencies;
    } catch {
        console.warn('[CurrenciesLoader] FALLBACK: Using legacy data');
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

        console.log('[StablecoinsLoader] Successfully loaded from domain JSONs');
        return {
            ...flattened,
            btc: shared.btc,
            dates: shared.dates, // Include dates for SFAI chart
        };
    } catch (e) {
        console.warn('[StablecoinsLoader] FALLBACK: Using legacy data', e.message);
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

        console.log('[GLILoader] Successfully loaded from domain JSONs');
        return {
            gli: {
                ...gli,
                // CB data comes from shared domain
                ...shared.central_banks
            },
            dates: shared.dates
        };
    } catch {
        console.warn('[GLILoader] FALLBACK: Using legacy data');
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

        console.log('[USSystemLoader] Successfully loaded from domain JSONs');
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
        console.warn('[USSystemLoader] FALLBACK: Using legacy data');
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

        console.log('[CryptoLoader] Successfully loaded from domain JSONs');
        return {
            crypto_analytics: crypto,
            btc: shared.btc,
            dates: shared.dates
        };
    } catch {
        console.warn('[CryptoLoader] FALLBACK: Using legacy data');
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

        console.log('[FedForecastsLoader] Successfully loaded from domain JSONs');
        return {
            fed_forecasts,
            inflation_swaps: fed_forecasts.inflation_swaps || {},
            dates: shared.dates
        };
    } catch {
        console.warn('[FedForecastsLoader] FALLBACK: Using legacy data');
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
        const [macro_regime, shared, crypto] = await Promise.all([
            loadDomain('macro_regime'),
            loadDomain('shared'),
            loadDomain('crypto')
        ]);

        console.log('[RegimesLoader] Successfully loaded from domain JSONs');
        return {
            macro_regime,
            // These might be nested in macro_regime or top-level in legacy
            // We favor the modular structure but provide compatibility
            regime_v2a: macro_regime.v2a || macro_regime,
            regime_v2b: macro_regime.v2b || macro_regime,
            // CLI data wrapper to match frontend expectation (cli.total, cli_v2.cli_v2)
            cli: { total: macro_regime.cli_v1 || [] },
            cli_v2: { cli_v2: macro_regime.cli_v2 || [] },
            stress_historical: macro_regime.stress_historical || macro_regime.stress || {},
            signals: macro_regime.signals || {},
            btc: shared.btc || {},
            dates: shared.dates
        };
    } catch (error) {
        console.warn('[RegimesLoader] FALLBACK: Using legacy data', error.message);
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

        console.log('[M2Loader] Successfully loaded from domain JSONs');
        return {
            m2: mappedM2,
            // m2_weights and m2_bank_rocs are expected at top level by GlobalM2Tab
            m2_weights: m2.weights || {},
            m2_bank_rocs: m2.economy_rocs || {},
            dates: shared.dates
        };
    } catch (error) {
        console.warn('[M2Loader] FALLBACK: Using legacy data', error.message);
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

        console.log('[OffshoreLoader] Successfully loaded from domain JSONs (offshore.json + shared.json)');
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
        console.warn('[OffshoreLoader] FALLBACK: Using legacy dashboard_data.json -', error.message);
        return {
            offshore_liquidity: legacyData?.offshore_liquidity || {},
            dates: legacyData?.dates || []
        };
    }
}


/**
 * Load data for RiskModelTab
 * @param {Object} legacyData - Legacy dashboard_data (fallback)
 * @returns {Promise<Object>} Data for Risk Model tab
 */
export async function loadRiskModelTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return legacyData;
    }

    try {
        const [cli, gli, us_system, treasury, macro_regime, fed_forecasts, shared] = await Promise.all([
            loadDomain('cli'),
            loadDomain('gli'),
            loadDomain('us_system'),
            loadDomain('treasury'),
            loadDomain('macro_regime'),
            loadDomain('fed_forecasts'),
            loadDomain('shared')
        ]);

        console.log('[RiskModelLoader] Successfully loaded from domain JSONs');

        // Helper to align legacy arrays (start 2002) to shared dates (start 1970)
        const alignToShared = (legacyArr) => {
            if (!legacyArr || !Array.isArray(legacyArr) || legacyArr.length === 0) return null;
            if (!shared?.dates) return legacyArr;

            // If already matches shared length (e.g. from aligned domain), return as is
            if (legacyArr.length === shared.dates.length) return legacyArr;

            // If matches legacy dates length, pad to align with shared
            if (legacyData?.dates && legacyArr.length === legacyData.dates.length) {
                const offset = shared.dates.indexOf(legacyData.dates[0]);
                if (offset > 0) {
                    const padding = new Array(offset).fill(null);
                    return [...padding, ...legacyArr];
                }
            }
            return legacyArr;
        };

        const alignSignalObj = (obj) => {
            if (!obj) return {};
            return {
                ...obj,
                raw: alignToShared(obj.raw),
                percentile: alignToShared(obj.percentile),
                zscore: alignToShared(obj.zscore)
            };
        };

        return {
            dates: shared.dates,

            // CLI Domain
            cli: {
                total: cli.total || alignToShared(legacyData?.cli?.total),
                percentile: cli.percentile || alignToShared(legacyData?.cli?.percentile),
                rocs: cli.rocs || legacyData?.cli?.rocs || {}
            },

            // GLI Data (Used for ROCs in RiskModelTab)
            gli: {
                total: gli.total || alignToShared(legacyData?.gli?.total),
                rocs: gli.rocs || legacyData?.gli?.rocs || {}
            },

            // Raw spreads - needed for some charts (legacy field names)
            hy_spread: cli.raw?.hy_spread || alignToShared(legacyData?.hy_spread),
            ig_spread: cli.raw?.ig_spread || alignToShared(legacyData?.ig_spread),
            hy_oasis: cli.raw?.hy_spread || alignToShared(legacyData?.hy_spread),
            ig_oasis: cli.raw?.ig_spread || alignToShared(legacyData?.ig_spread),
            nfci: {
                credit: cli.raw?.nfci_credit || alignToShared(legacyData?.nfci?.credit || legacyData?.nfci_credit),
                risk: cli.raw?.nfci_risk || alignToShared(legacyData?.nfci?.risk || legacyData?.nfci_risk)
            },
            nfci_credit: cli.raw?.nfci_credit || alignToShared(legacyData?.nfci_credit),
            nfci_risk: cli.raw?.nfci_risk || alignToShared(legacyData?.nfci_risk),
            lending_standards: cli.raw?.lending_std || alignToShared(legacyData?.lending || legacyData?.lending_standards),
            lending: cli.raw?.lending_std || alignToShared(legacyData?.lending),
            vix: cli.raw?.vix || alignToShared(legacyData?.vix?.total || legacyData?.vix),
            move: cli.raw?.move || alignToShared(legacyData?.move?.total || legacyData?.move || legacyData?.move_index),
            fx_vol: cli.raw?.fx_vol || alignToShared(legacyData?.fx_vol?.total || legacyData?.fx_vol),

            // US System Domain (Net Liquidity)
            us_net_liq: us_system.net_liquidity || alignToShared(legacyData?.us_net_liq),
            us_net_liq_rrp: us_system.rrp || alignToShared(legacyData?.us_net_liq_rrp),
            us_net_liq_tga: us_system.tga || alignToShared(legacyData?.us_net_liq_tga),
            us_net_liq_reserves: us_system.bank_reserves || alignToShared(legacyData?.us_net_liq_reserves),
            us_net_liq_rocs: us_system.net_liq_rocs || legacyData?.us_net_liq_rocs || {},
            us_system_metrics: us_system.metrics || legacyData?.us_system_metrics || {},
            reserves_metrics: us_system.reserves_metrics || legacyData?.reserves_metrics || {},

            repo_operations: us_system.repo_operations || legacyData?.repo_operations || {},
            repo_stress: {
                sofr: alignToShared(us_system.repo_stress?.sofr) || alignToShared(legacyData?.repo_stress?.sofr),
                iorb: alignToShared(us_system.repo_stress?.iorb) || alignToShared(legacyData?.repo_stress?.iorb),
                srf_rate: alignToShared(us_system.repo_stress?.srf_rate) || alignToShared(legacyData?.repo_stress?.srf_rate),
                srf_usage: alignToShared(us_system.repo_stress?.srf_usage) || alignToShared(legacyData?.repo_stress?.srf_usage),
                sofr_volume: alignToShared(us_system.repo_stress?.sofr_volume) || alignToShared(legacyData?.repo_stress?.sofr_volume),
                sofr_to_floor: alignToShared(us_system.repo_stress?.sofr_to_floor) || alignToShared(legacyData?.repo_stress?.sofr_to_floor),
                sofr_to_ceiling: alignToShared(us_system.repo_stress?.sofr_to_ceiling) || alignToShared(legacyData?.repo_stress?.sofr_to_ceiling),
                sofr_volume_roc_5d: alignToShared(us_system.repo_stress?.sofr_volume_roc_5d) || alignToShared(legacyData?.repo_stress?.sofr_volume_roc_5d),
                sofr_volume_roc_20d: alignToShared(us_system.repo_stress?.sofr_volume_roc_20d) || alignToShared(legacyData?.repo_stress?.sofr_volume_roc_20d),
                rrp_award: alignToShared(us_system.repo_stress?.rrp_award) || alignToShared(legacyData?.repo_stress?.rrp_award),
            },

            // Treasury Domain
            treasury_10y: treasury.yields?.['10y'] || alignToShared(legacyData?.treasury_10y),
            treasury_2y: treasury.yields?.['2y'] || alignToShared(legacyData?.treasury_2y),
            treasury_5y: treasury.yields?.['5y'] || alignToShared(legacyData?.treasury_5y),
            treasury_30y: treasury.yields?.['30y'] || alignToShared(legacyData?.treasury_30y),

            yield_curve: treasury.curves?.['10y_2y'] || alignToShared(legacyData?.yield_curve),
            yield_curve_30y_10y: treasury.curves?.['30y_10y'] || alignToShared(legacyData?.yield_curve_30y_10y),
            yield_curve_30y_2y: treasury.curves?.['30y_2y'] || alignToShared(legacyData?.yield_curve_30y_2y),
            yield_curve_10y_5y: treasury.curves?.['10y_5y'] || alignToShared(legacyData?.yield_curve_10y_5y),

            // Fed Forecasts Domain
            inflation_expect_1y: fed_forecasts.inflation_expectations?.cleveland_1y || alignToShared(legacyData?.inflation_expect_1y),
            inflation_expect_5y: fed_forecasts.inflation_expectations?.cleveland_5y || alignToShared(legacyData?.inflation_expect_5y),
            inflation_expect_10y: fed_forecasts.inflation_expectations?.cleveland_10y || alignToShared(legacyData?.inflation_expect_10y),

            inflation_swaps: {
                cleveland_1y: fed_forecasts.inflation_expectations?.cleveland_1y || alignToShared(legacyData?.inflation_swaps?.cleveland_1y || legacyData?.inflation_expect_1y),
                cleveland_2y: fed_forecasts.inflation_expectations?.cleveland_2y || alignToShared(legacyData?.inflation_swaps?.cleveland_2y || legacyData?.inflation_expect_2y),
                cleveland_5y: fed_forecasts.inflation_expectations?.cleveland_5y || alignToShared(legacyData?.inflation_swaps?.cleveland_5y || legacyData?.inflation_expect_5y),
                cleveland_10y: fed_forecasts.inflation_expectations?.cleveland_10y || alignToShared(legacyData?.inflation_swaps?.cleveland_10y || legacyData?.inflation_expect_10y),
            },

            tips: {
                breakeven: fed_forecasts.tips_ref?.breakeven || alignToShared(legacyData?.tips?.breakeven || legacyData?.tips_breakeven),
                real_rate: fed_forecasts.tips_ref?.real_rate || alignToShared(legacyData?.tips?.real_rate || legacyData?.tips_real_rate),
                fwd_5y5y: fed_forecasts.tips_ref?.fwd_5y5y || alignToShared(legacyData?.tips?.fwd_5y5y || legacyData?.tips_fwd_5y5y),
            },

            fed_forecasts: {
                nfp: fed_forecasts.nfp || alignToShared(legacyData?.fed_forecasts?.nfp),
                nfp_change: fed_forecasts.nfp_change || alignToShared(legacyData?.fed_forecasts?.nfp_change),
                jolts: fed_forecasts.jolts || alignToShared(legacyData?.fed_forecasts?.jolts),
                fed_funds: fed_forecasts.fed_funds_rate || alignToShared(legacyData?.fed_forecasts?.fed_funds || legacyData?.fed_funds_rate),
                ...fed_forecasts
            },

            // Macro Regime Domain - both flattened and full object for different consumers
            divergence: macro_regime.cli_gli_divergence || alignToShared(legacyData?.macro_regime?.cli_gli_divergence || legacyData?.divergence),
            cli_gli_divergence: macro_regime.cli_gli_divergence || alignToShared(legacyData?.cli_gli_divergence || legacyData?.divergence),
            signals: macro_regime.signals || legacyData.signals || {},
            signal_aggregate: macro_regime.score || legacyData.signal_aggregate || null,
            macro_regime: macro_regime || legacyData?.macro_regime || {}, // Pass full object for charts accessing nested paths
            last_dates: legacyData.last_dates || {},

            st_louis_stress: us_system.st_louis_stress?.total || alignToShared(legacyData?.st_louis_stress),
            kansas_city_stress: us_system.kansas_city_stress?.total || alignToShared(legacyData?.kansas_city_stress),

            // Construct signal_metrics to match legacy structure for RiskModelTab
            // This is critical - must match keys and structure exactly
            signal_metrics: {
                ...legacyData.signal_metrics,
                // CLI composite
                cli: {
                    raw: cli.total || alignToShared(legacyData?.signal_metrics?.cli?.raw || legacyData?.cli?.total),
                    percentile: cli.percentile || alignToShared(legacyData?.signal_metrics?.cli?.percentile || legacyData?.cli?.percentile),
                    zscore: cli.z_score || alignToShared(legacyData?.signal_metrics?.cli?.zscore || []),
                    // Advanced V2 (Regime) Metrics
                    v2_raw: cli.v2_total || [],
                    v2_percentile: cli.v2_percentile || []
                },
                // Credit spreads
                hy_spread: {
                    raw: cli.raw?.hy_spread || alignToShared(legacyData?.signal_metrics?.hy_spread?.raw || legacyData?.hy_spread),
                    percentile: cli.components?.hy_spread_pct || alignToShared(legacyData?.signal_metrics?.hy_spread?.percentile),
                    zscore: cli.components?.hy_spread_z || alignToShared(legacyData?.signal_metrics?.hy_spread?.zscore)
                },
                ig_spread: {
                    raw: cli.raw?.ig_spread || alignToShared(legacyData?.signal_metrics?.ig_spread?.raw || legacyData?.ig_spread),
                    percentile: cli.components?.ig_spread_pct || alignToShared(legacyData?.signal_metrics?.ig_spread?.percentile),
                    zscore: cli.components?.ig_spread_z || alignToShared(legacyData?.signal_metrics?.ig_spread?.zscore)
                },
                // NFCI components
                nfci_credit: {
                    raw: cli.raw?.nfci_credit || alignToShared(legacyData?.signal_metrics?.nfci_credit?.raw),
                    percentile: cli.components?.nfci_credit_pct || alignToShared(legacyData?.signal_metrics?.nfci_credit?.percentile),
                    zscore: cli.components?.nfci_credit_z || alignToShared(legacyData?.signal_metrics?.nfci_credit?.zscore)
                },
                nfci_risk: {
                    raw: cli.raw?.nfci_risk || alignToShared(legacyData?.signal_metrics?.nfci_risk?.raw),
                    percentile: cli.components?.nfci_risk_pct || alignToShared(legacyData?.signal_metrics?.nfci_risk?.percentile),
                    zscore: cli.components?.nfci_risk_z || alignToShared(legacyData?.signal_metrics?.nfci_risk?.zscore)
                },
                // Lending
                lending: {
                    raw: cli.raw?.lending_std || alignToShared(legacyData?.signal_metrics?.lending?.raw),
                    percentile: cli.components?.lending_std_pct || alignToShared(legacyData?.signal_metrics?.lending?.percentile),
                    zscore: cli.components?.lending_std_z || alignToShared(legacyData?.signal_metrics?.lending?.zscore)
                },
                // Vol metrics
                vix: {
                    raw: cli.raw?.vix || alignToShared(legacyData?.signal_metrics?.vix?.raw),
                    percentile: cli.components?.vix_pct || alignToShared(legacyData?.signal_metrics?.vix?.percentile),
                    zscore: cli.components?.vix_z || alignToShared(legacyData?.signal_metrics?.vix?.zscore)
                },
                move: {
                    raw: cli.raw?.move || alignToShared(legacyData?.signal_metrics?.move?.raw),
                    percentile: cli.components?.move_pct || alignToShared(legacyData?.signal_metrics?.move?.percentile),
                    zscore: cli.components?.move_z || alignToShared(legacyData?.signal_metrics?.move?.zscore)
                },
                fx_vol: {
                    raw: cli.raw?.fx_vol || alignToShared(legacyData?.signal_metrics?.fx_vol?.raw),
                    percentile: cli.components?.fx_vol_pct || alignToShared(legacyData?.signal_metrics?.fx_vol?.percentile),
                    zscore: cli.components?.fx_vol_z || alignToShared(legacyData?.signal_metrics?.fx_vol?.zscore)
                },

                // Treasury Metrics
                treasury_10y: {
                    raw: treasury.yields?.['10y'] || alignToShared(legacyData?.signal_metrics?.treasury_10y?.raw),
                    percentile: treasury.yields?.['10y_p'] || treasury.yields?.['10y_pct'] || alignToShared(legacyData?.signal_metrics?.treasury_10y?.percentile),
                    zscore: treasury.yields?.['10y_z'] || alignToShared(legacyData?.signal_metrics?.treasury_10y?.zscore)
                },
                treasury_2y: {
                    raw: treasury.yields?.['2y'] || alignToShared(legacyData?.signal_metrics?.treasury_2y?.raw),
                    percentile: treasury.yields?.['2y_p'] || treasury.yields?.['2y_pct'] || alignToShared(legacyData?.signal_metrics?.treasury_2y?.percentile),
                    zscore: treasury.yields?.['2y_z'] || alignToShared(legacyData?.signal_metrics?.treasury_2y?.zscore)
                },
                treasury_30y: {
                    raw: treasury.yields?.['30y'] || alignToShared(legacyData?.signal_metrics?.treasury_30y?.raw),
                    percentile: treasury.yields?.['30y_p'] || treasury.yields?.['30y_pct'] || alignToShared(legacyData?.signal_metrics?.treasury_30y?.percentile),
                    zscore: treasury.yields?.['30y_z'] || alignToShared(legacyData?.signal_metrics?.treasury_30y?.zscore)
                },
                treasury_5y: {
                    raw: treasury.yields?.['5y'] || alignToShared(legacyData?.signal_metrics?.treasury_5y?.raw),
                    percentile: treasury.yields?.['5y_p'] || treasury.yields?.['5y_pct'] || alignToShared(legacyData?.signal_metrics?.treasury_5y?.percentile),
                    zscore: treasury.yields?.['5y_z'] || alignToShared(legacyData?.signal_metrics?.treasury_5y?.zscore)
                },
                // Treasury curves in signal_metrics
                yield_curve: {
                    raw: treasury.curves?.['10y_2y'] || alignToShared(legacyData?.signal_metrics?.yield_curve?.raw || legacyData?.yield_curve),
                    percentile: treasury.curves?.['10y_2y_p'] || treasury.curves?.['10y_2y_pct'] || alignToShared(legacyData?.signal_metrics?.yield_curve?.percentile),
                    zscore: treasury.curves?.['10y_2y_z'] || alignToShared(legacyData?.signal_metrics?.yield_curve?.zscore)
                },
                yield_curve_30y_10y: {
                    raw: treasury.curves?.['30y_10y'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_10y?.raw),
                    percentile: treasury.curves?.['30y_10y_p'] || treasury.curves?.['30y_10y_pct'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_10y?.percentile),
                    zscore: treasury.curves?.['30y_10y_z'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_10y?.zscore)
                },
                yield_curve_30y_2y: {
                    raw: treasury.curves?.['30y_2y'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_2y?.raw),
                    percentile: treasury.curves?.['30y_2y_p'] || treasury.curves?.['30y_2y_pct'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_2y?.percentile),
                    zscore: treasury.curves?.['30y_2y_z'] || alignToShared(legacyData?.signal_metrics?.yield_curve_30y_2y?.zscore)
                },
                // Stress Indices
                st_louis_stress: {
                    raw: alignToShared(us_system.st_louis_stress?.total) || alignToShared(legacyData?.signal_metrics?.st_louis_stress?.raw),
                    percentile: alignToShared(us_system.st_louis_stress?.percentile) || alignToShared(legacyData?.signal_metrics?.st_louis_stress?.percentile),
                    zscore: alignToShared(us_system.st_louis_stress?.z_score) || alignToShared(legacyData?.signal_metrics?.st_louis_stress?.zscore)
                },
                kansas_city_stress: {
                    raw: alignToShared(us_system.kansas_city_stress?.total) || alignToShared(legacyData?.signal_metrics?.kansas_city_stress?.raw),
                    percentile: alignToShared(us_system.kansas_city_stress?.percentile) || alignToShared(legacyData?.signal_metrics?.kansas_city_stress?.percentile),
                    zscore: alignToShared(us_system.kansas_city_stress?.z_score) || alignToShared(legacyData?.signal_metrics?.kansas_city_stress?.zscore)
                },
                // Corporate yields
                baa_yield: alignSignalObj(legacyData?.signal_metrics?.baa_yield),
                aaa_yield: alignSignalObj(legacyData?.signal_metrics?.aaa_yield),
                baa_aaa_spread: alignSignalObj(legacyData?.signal_metrics?.baa_aaa_spread),
                // TIPS metrics  
                tips_real_rate: alignSignalObj(legacyData?.signal_metrics?.tips_real_rate),
                tips_breakeven: alignSignalObj(legacyData?.signal_metrics?.tips_breakeven),
                tips: alignSignalObj(legacyData?.signal_metrics?.tips),
                // Labor metrics
                nfp: alignSignalObj(legacyData?.signal_metrics?.nfp),
                jolts: alignSignalObj(legacyData?.signal_metrics?.jolts),
                // Divergence metrics
                cli_gli_divergence: {
                    raw: macro_regime.cli_gli_divergence || alignToShared(legacyData?.signal_metrics?.cli_gli_divergence?.raw || legacyData?.divergence),
                    percentile: alignToShared(legacyData?.signal_metrics?.cli_gli_divergence?.percentile),
                    zscore: alignToShared(legacyData?.signal_metrics?.cli_gli_divergence?.zscore),
                    momentum_pct: alignToShared(legacyData?.signal_metrics?.cli_gli_divergence?.momentum_pct),
                    signal_series: alignToShared(legacyData?.signal_metrics?.cli_gli_divergence?.signal_series),
                    latest: legacyData?.signal_metrics?.cli_gli_divergence?.latest || {}
                }
            },

            // Fallback for fields not yet in domains or handled differently
            credit_spreads: legacyData?.credit_spreads || {},
            inflation_swaps_fallback: legacyData?.inflation_swaps || {},
            stress_analysis: legacyData?.stress_analysis || {},

            // Direct Corporate Yields fallback if not mapped in signal_metrics (for new charts)
            baa_yield: treasury.corporate?.baa_yield || alignToShared(legacyData?.baa_yield),
            aaa_yield: treasury.corporate?.aaa_yield || alignToShared(legacyData?.aaa_yield),
            baa_aaa_spread: treasury.corporate?.baa_aaa_spread || alignToShared(legacyData?.baa_aaa_spread),
        };
    } catch (error) {
        console.warn('[RiskModelLoader] FALLBACK: Using legacy data -', error.message);
        return legacyData;
    }
}

export async function loadTreasuryTabData(legacyData) {
    if (!USE_MODULAR_DOMAINS) {
        return {
            treasury_maturities: legacyData?.treasury_maturities || {},
            treasury_auction_demand: legacyData?.treasury_auction_demand || {},
            treasury_refinancing_signal: legacyData?.treasury_refinancing_signal || {},
            dates: legacyData?.dates || []
        };
    }

    try {
        const [treasury, shared] = await Promise.all([
            loadDomain('treasury'),
            loadDomain('shared')
        ]);

        console.log('[TreasuryLoader] Successfully loaded from domain JSONs');

        // Map domain structure to UsDebtTab expected format
        return {
            treasury_maturities: treasury.maturities || legacyData?.treasury_maturities || {},
            treasury_auction_demand: treasury.auction_demand || legacyData?.treasury_auction_demand || {},
            treasury_refinancing_signal: legacyData?.treasury_refinancing_signal || {}, // Still from legacy for now
            treasury: treasury, // Full treasury domain for other uses
            dates: shared.dates
        };
    } catch (error) {
        console.warn('[TreasuryLoader] FALLBACK: Using legacy data -', error.message);
        return {
            treasury_maturities: legacyData?.treasury_maturities || {},
            treasury_auction_demand: legacyData?.treasury_auction_demand || {},
            treasury_refinancing_signal: legacyData?.treasury_refinancing_signal || {},
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
    loadRiskModelTabData,
};
