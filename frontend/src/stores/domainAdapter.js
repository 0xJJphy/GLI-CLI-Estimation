/**
 * Domain Adapter
 * 
 * Provides compatibility layer between new domain-based data loading
 * and legacy dashboardData format expected by frontend components.
 * 
 * Features:
 * - Parallel loading of domain JSON files
 * - Transformation to legacy format for backward compatibility
 * - Fallback to monolithic dashboard_data.json if domains fail
 */

// Domain configuration: name -> file path
const DOMAIN_CONFIG = {
    shared: '/domains/shared.json',
    gli: '/domains/gli.json',
    m2: '/domains/m2.json',
    us_system: '/domains/us_system.json',
    cli: '/domains/cli.json',
    treasury: '/domains/treasury.json',
    currencies: '/domains/currencies.json',
    stablecoins: '/domains/stablecoins.json',
    crypto: '/domains/crypto.json',
    fed_forecasts: '/domains/fed_forecasts.json',
    macro_regime: '/domains/macro_regime.json',
    offshore: '/domains/offshore.json',
};

/**
 * Load all domain JSON files in parallel.
 * Returns an object with domain name as key and parsed data as value.
 * @returns {Promise<Record<string, any>>}
 */
export async function loadAllDomains() {
    const entries = Object.entries(DOMAIN_CONFIG);

    const results = await Promise.allSettled(
        entries.map(async ([name, path]) => {
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`Failed to load ${name}: ${response.status}`);
            }
            const data = await response.json();
            return { name, data };
        })
    );

    const domains = {};
    const errors = [];

    for (const result of results) {
        if (result.status === 'fulfilled') {
            domains[result.value.name] = result.value.data;
        } else {
            errors.push(result.reason.message);
        }
    }

    if (errors.length > 0) {
        console.warn('[DomainAdapter] Some domains failed to load:', errors);
    }

    return domains;
}

/**
 * Transform domain data to legacy dashboardData format.
 * This provides backward compatibility with existing components.
 * @param {Record<string, any>} domains - Loaded domain data
 * @returns {object} - Legacy format dashboardData
 */
export function adaptToLegacyFormat(domains) {
    const legacy = {};

    // === SHARED DOMAIN ===
    if (domains.shared) {
        legacy.dates = domains.shared.dates || [];
        legacy.btc = {
            price: domains.shared.btc?.price || [],
            rocs: domains.shared.btc?.rocs || {},
        };
    }

    // === GLI DOMAIN ===
    if (domains.gli) {
        legacy.gli = {
            total: domains.gli.total || [],
            constant_fx: domains.gli.constant_fx || [],
            cb_count: domains.gli.cb_count || 0,
            rocs: domains.gli.rocs || {},
            // Map individual CB data from shared domain
            fed: domains.shared?.central_banks?.fed || [],
            ecb: domains.shared?.central_banks?.ecb || [],
            boj: domains.shared?.central_banks?.boj || [],
            boe: domains.shared?.central_banks?.boe || [],
            pboc: domains.shared?.central_banks?.pboc || [],
            boc: domains.shared?.central_banks?.boc || [],
            rba: domains.shared?.central_banks?.rba || [],
            snb: domains.shared?.central_banks?.snb || [],
            bok: domains.shared?.central_banks?.bok || [],
            rbi: domains.shared?.central_banks?.rbi || [],
            cbr: domains.shared?.central_banks?.cbr || [],
            bcb: domains.shared?.central_banks?.bcb || [],
            rbnz: domains.shared?.central_banks?.rbnz || [],
            sr: domains.shared?.central_banks?.sr || [],
            bnm: domains.shared?.central_banks?.bnm || [],
        };
        legacy.gli_weights = domains.gli.weights || {};
        legacy.bank_rocs = domains.gli.bank_rocs || {};
    }

    // === M2 DOMAIN ===
    if (domains.m2) {
        legacy.m2 = {
            total: domains.m2.total || [],
            rocs: domains.m2.rocs || {},
            us: domains.m2.economies?.us || [],
            eu: domains.m2.economies?.eu || [],
            cn: domains.m2.economies?.cn || [],
            jp: domains.m2.economies?.jp || [],
            uk: domains.m2.economies?.uk || domains.m2.economies?.gb || [],
            ca: domains.m2.economies?.ca || [],
            au: domains.m2.economies?.au || [],
            in: domains.m2.economies?.in || [],
            ch: domains.m2.economies?.ch || [],
            ru: domains.m2.economies?.ru || [],
            br: domains.m2.economies?.br || [],
            kr: domains.m2.economies?.kr || [],
            mx: domains.m2.economies?.mx || [],
            my: domains.m2.economies?.my || [],
        };
        legacy.m2_weights = domains.m2.weights || {};
        legacy.m2_bank_rocs = domains.m2.economy_rocs || {};
    }

    // === US SYSTEM DOMAIN ===
    if (domains.us_system) {
        // Legacy uses flat keys, domain uses nested
        legacy.us_net_liq = domains.us_system.net_liquidity || [];
        legacy.us_net_liq_rrp = domains.us_system.rrp || [];
        legacy.us_net_liq_tga = domains.us_system.tga || [];
        legacy.us_net_liq_reserves = domains.us_system.bank_reserves || [];
        legacy.us_net_liq_rocs = domains.us_system.net_liq_rocs || {};
        legacy.us_system_metrics = domains.us_system.metrics || {};
        legacy.repo_operations = domains.us_system.repo_operations || {};
        legacy.reserves_metrics = domains.us_system.reserves_metrics || {};
    }

    // === CLI DOMAIN ===
    if (domains.cli) {
        legacy.cli = {
            total: domains.cli.total || [],
            percentile: domains.cli.percentile || [],
            rocs: domains.cli.rocs || {},
        };
        legacy.cli_components = {
            hy_z: domains.cli.components?.hy_spread_z || [],
            ig_z: domains.cli.components?.ig_spread_z || [],
            nfci_credit_z: domains.cli.components?.nfci_credit_z || [],
            nfci_risk_z: domains.cli.components?.nfci_risk_z || [],
            lending_z: domains.cli.components?.lending_std_z || [],
            vix_z: domains.cli.components?.vix_z || [],
            weights: domains.cli.weights || {},
        };
        // Raw values
        legacy.hy_spread = domains.cli.raw?.hy_spread || [];
        legacy.ig_spread = domains.cli.raw?.ig_spread || [];
        legacy.vix = { total: domains.cli.raw?.vix || [], rocs: {} };
    }

    // === TREASURY DOMAIN ===
    if (domains.treasury) {
        legacy.treasury_10y = domains.treasury.yields?.treasury_10y || [];
        legacy.treasury_2y = domains.treasury.yields?.treasury_2y || [];
        legacy.yield_curve = domains.treasury.curves?.['10y_2y'] || [];
    }

    // === CURRENCIES DOMAIN ===
    if (domains.currencies) {
        legacy.currencies = domains.currencies;
    }

    // === STABLECOINS DOMAIN ===
    if (domains.stablecoins) {
        legacy.stablecoins = domains.stablecoins;
    }

    // === CRYPTO DOMAIN ===
    if (domains.crypto) {
        legacy.crypto_analytics = domains.crypto;
        // Fear & Greed
        legacy.fear_greed = domains.crypto.fear_greed || [];
    }

    // === FED FORECASTS DOMAIN ===
    if (domains.fed_forecasts) {
        legacy.fed_forecasts = {
            cpi_yoy: domains.fed_forecasts.cpi_yoy || [],
            core_cpi_yoy: domains.fed_forecasts.core_cpi_yoy || [],
            pce_yoy: domains.fed_forecasts.pce_yoy || [],
            core_pce_yoy: domains.fed_forecasts.core_pce_yoy || [],
            unemployment: domains.fed_forecasts.unemployment || [],
            nfp: domains.fed_forecasts.nfp || [],
            nfp_change: domains.fed_forecasts.nfp_change || [],
            jolts: domains.fed_forecasts.jolts || [],
            fed_funds_rate: domains.fed_forecasts.fed_funds_rate || [],
            ism_mfg: domains.fed_forecasts.ism_mfg || [],
            ism_svc: domains.fed_forecasts.ism_svc || [],
            inflation_swaps: domains.fed_forecasts.inflation_expectations || {},
        };
        // Also expose at root for RiskModelTab
        legacy.inflation_swaps = domains.fed_forecasts.inflation_expectations || {};
    }

    // === MACRO REGIME DOMAIN ===
    if (domains.macro_regime) {
        legacy.macro_regime = {
            score: domains.macro_regime.score || [],
            regime_code: domains.macro_regime.regime_code || [],
            total_z: domains.macro_regime.total_z || [],
            liquidity_z: domains.macro_regime.liquidity_z || [],
            credit_z: domains.macro_regime.credit_z || [],
            brakes_z: domains.macro_regime.brakes_z || [],
            cli_gli_divergence: domains.macro_regime.cli_gli_divergence || [],
            cb_diffusion_13w: domains.macro_regime.cb_diffusion_13w || [],
            cb_hhi_13w: domains.macro_regime.cb_hhi_13w || [],
        };
        legacy.cli_v2 = domains.macro_regime.cli_v2 || {};
        legacy.regime_v2a = domains.macro_regime.v2a || {};
        legacy.regime_v2b = domains.macro_regime.v2b || {};
        legacy.stress_historical = domains.macro_regime.stress_historical || {};
    }

    // === OFFSHORE DOMAIN ===
    if (domains.offshore) {
        legacy.offshore_liquidity = domains.offshore;
        // Also spread some keys to repo_stress for RiskModelTab
        legacy.repo_stress = {
            sofr: domains.offshore.sofr || [],
            iorb: domains.offshore.iorb || [],
            sofr_volume: domains.offshore.sofr_volume || [],
            srf_usage: domains.offshore.srf_usage || [],
            srf_rate: domains.offshore.srf_rate || [],
            rrp_award: domains.offshore.rrp_award || [],
        };
    }

    // === ADDITIONAL DERIVED FIELDS ===
    // VIX and MOVE often accessed directly
    if (domains.cli?.raw?.vix) {
        legacy.vix = { total: domains.cli.raw.vix, rocs: {} };
    }
    if (domains.cli?.raw?.move) {
        legacy.move = { total: domains.cli.raw.move, rocs: {} };
    }

    // TIPS data from fed_forecasts
    if (domains.fed_forecasts?.inflation_expectations) {
        legacy.tips = {
            breakeven: domains.fed_forecasts.inflation_expectations.tips_breakeven_10y || [],
            real_rate: domains.fed_forecasts.inflation_expectations.tips_real_rate || [],
            fwd_5y5y: domains.fed_forecasts.inflation_expectations.tips_5y5y_forward || [],
            rocs: {},
        };
    }

    return legacy;
}

/**
 * Fetch domain data and return in legacy format.
 * Falls back to legacy dashboard_data.json on failure.
 * @param {boolean} useDomains - Whether to use domain loading (feature flag)
 * @returns {Promise<object>}
 */
export async function fetchWithDomainAdapter(useDomains = true) {
    if (!useDomains) {
        // Use legacy loading
        const response = await fetch('/dashboard_data.json');
        if (!response.ok) throw new Error('Failed to fetch legacy data');
        return response.json();
    }

    try {
        const domains = await loadAllDomains();
        const legacyFormat = adaptToLegacyFormat(domains);
        console.log('[DomainAdapter] Successfully loaded and adapted domain data');
        return legacyFormat;
    } catch (error) {
        console.error('[DomainAdapter] Domain loading failed, falling back to legacy:', error);
        // Fallback to legacy
        const response = await fetch('/dashboard_data.json');
        if (!response.ok) throw new Error('Failed to fetch fallback data');
        return response.json();
    }
}
