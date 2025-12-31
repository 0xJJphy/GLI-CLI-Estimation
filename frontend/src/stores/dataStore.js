import { writable, derived } from 'svelte/store';

export const dashboardData = writable({
    dates: [],
    last_dates: {},
    gli: {
        total: [],
        constant_fx: [],
        cb_count: 5,
        data_start_date: null,
        fed: [], ecb: [], boj: [], boe: [], pboc: [],
        boc: [], rba: [], snb: [], bok: [],
        rbi: [], cbr: [], bcb: [], rbnz: [], sr: [], bnm: [],
        rocs: {}
    },
    gli_weights: {},
    m2: {
        total: [], us: [], eu: [], cn: [], jp: [], uk: [],
        ca: [], au: [], in: [], ch: [], ru: [], br: [],
        kr: [], mx: [], my: [],
        rocs: {}
    },
    m2_weights: {},
    m2_bank_rocs: {},
    us_net_liq: [],
    us_net_liq_rrp: [],
    us_net_liq_tga: [],
    us_net_liq_reserves: [],
    us_net_liq_rocs: {},
    reserves_metrics: {
        reserves_roc_3m: [],
        netliq_roc_3m: [],
        spread_zscore: [],
        momentum: [],
        lcr: [],
        acceleration: [],
        volatility: []
    },
    us_system_metrics: {
        fed_roc_20d: [],
        rrp_roc_20d: [],
        tga_roc_20d: [],
        netliq_roc_20d: [],
        rrp_drain_weekly: [],
        rrp_weeks_to_empty: [],
        tga_zscore: [],
        fed_momentum: [],
        liquidity_score: [],
        // Absolute $ deltas (avoid % base effect)
        rrp_delta_4w: [],
        rrp_delta_13w: [],
        tga_delta_4w: [],
        tga_delta_13w: [],
        // Net Liquidity Impulse ($T)
        netliq_delta_4w: [],
        netliq_delta_13w: []
    },
    flow_metrics: {
        gli_impulse_4w: [],
        gli_impulse_13w: [],
        gli_accel: [],
        gli_impulse_zscore: [],
        m2_impulse_4w: [],
        m2_impulse_13w: [],
        m2_accel: [],
        m2_impulse_zscore: [],
        fed_contrib_13w: [],
        ecb_contrib_13w: [],
        boj_contrib_13w: [],
        pboc_contrib_13w: [],
        boe_contrib_13w: [],
        net_liquidity_impulse_4w: [],
        net_liquidity_impulse_13w: [],
        cli_momentum_4w: [],
        cli_momentum_13w: []
    },
    series_metadata: {
        GLI: { last_date: null, freshness: null, cb_count: 0 },
        M2: { last_date: null, freshness: null },
        CLI: { last_date: null, freshness: null },
        NET_LIQ: { last_date: null, freshness: null },
        BTC: { last_date: null, freshness: null }
    },
    us_system_rocs: {
        fed: {}, rrp: {}, tga: {}
    },
    bank_rocs: {
        fed: {}, ecb: {}, boj: {}, boe: {}, pboc: {},
        boc: {}, rba: {}, snb: {}, bok: {}, rbi: {},
        cbr: {}, bcb: {}, rbnz: {}, sr: {}, bnm: {}
    },
    cli: { total: [], percentile: [], rocs: {} },
    cli_components: {
        hy_z: [], ig_z: [], nfci_credit_z: [], nfci_risk_z: [], lending_z: [], vix_z: [],
        weights: { HY: 0.25, IG: 0.15, NFCI_CREDIT: 0.20, NFCI_RISK: 0.20, LENDING: 0.10, VIX: 0.10 }
    },
    vix: { total: [], rocs: {} },
    move: { total: [], rocs: {} },
    fx_vol: { total: [], rocs: {} },
    hy_spread: [],
    ig_spread: [],
    treasury_10y: [],
    treasury_2y: [],
    yield_curve: [],
    // TIPS / Inflation Expectations
    tips: {
        breakeven: [],
        real_rate: [],
        fwd_5y5y: [],
        rocs: {}
    },
    repo_stress: {
        sofr: [],
        iorb: []
    },
    btc: {
        price: [], fair_value: [], upper_2sd: [], upper_1sd: [],
        lower_1sd: [], lower_2sd: [], deviation_zscore: [], rocs: {}
    },
    correlations: { gli_btc: {}, cli_btc: {}, vix_btc: {}, netliq_btc: {} },
    predictive: {
        rocs: { dates: [], cli_7d: [], cli_14d: [], cli_30d: [], btc_7d: [], btc_14d: [], btc_30d: [] },
        lag_correlations: {
            '7d': { lags: [], correlations: [], optimal_lag: 0, max_corr: 0 },
            '14d': { lags: [], correlations: [], optimal_lag: 0, max_corr: 0 },
            '30d': { lags: [], correlations: [], optimal_lag: 0, max_corr: 0 }
        }
    },
    macro_regime: {
        score: [],
        regime_code: [],
        transition: [],
        total_z: [],
        liquidity_z: [],
        credit_z: [],
        brakes_z: [],
        cb_diffusion_13w: [],
        cb_hhi_13w: [],
        repo_stress: [],
        real_rate_shock_4w: [],
        cli_gli_divergence: [],
        reserves_spread_z: []
    },
    signals: {},
    cli_percentile: [],
    signal_metrics: {
        cli: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        hy_spread: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        ig_spread: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        nfci_credit: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        nfci_risk: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        lending: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        vix: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        move: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        fx_vol: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        tips: { latest: { state: "neutral", percentile: 50 }, percentile: [] },
        repo: { latest: { state: "neutral", percentile: 50 }, percentile: [] }
    },
    fed_forecasts: {
        cpi_yoy: [], core_cpi_yoy: [], pce_yoy: [], core_pce_yoy: [],
        ism_mfg: [], ism_svc: [], unemployment: [], nfp: [], nfp_change: [], jolts: [], fed_funds_rate: [],
        inflation_expect_1y: [], inflation_expect_5y: [], inflation_expect_10y: [],
        inflation_swaps: {
            cleveland_1y: [], cleveland_2y: [], cleveland_5y: [], cleveland_10y: [],
            inf_risk_premium_1y: [], inf_risk_premium_10y: [],
            real_rate_1y: [], real_rate_10y: [],
            umich_expectations: [], tips_breakeven_5y: [], tips_breakeven_2y: []
        },
        stress_analysis: {
            inflation_stress: { score: 0, level: 'LOW', signals: [], metrics: {} },
            liquidity_stress: { score: 0, level: 'LOW', signals: [], metrics: {} },
            credit_stress: { score: 0, level: 'LOW', signals: [], metrics: {} },
            volatility_stress: { score: 0, level: 'LOW', signals: [], metrics: {} },
            global_stress: { total_score: 0, level: 'LOW', assessment: '' },
            chart_analyses: {},
            overall_assessment: {}
        }
    }
});

export const isLoading = writable(true);
export const error = writable(null);
export const selectedSource = writable('tv'); // 'tv' or 'fred'

export async function fetchData() {
    isLoading.set(true);
    let source;
    selectedSource.subscribe(val => source = val)();

    try {
        const filename = `/dashboard_data_${source}.json`;
        const response = await fetch(filename);
        if (!response.ok) {
            // Fallback to generic if specific not found
            const fallback = await fetch('/dashboard_data.json');
            if (!fallback.ok) throw new Error('Failed to fetch data');
            const data = await fallback.json();
            dashboardData.set(data);
        } else {
            const data = await response.json();
            dashboardData.set(data);
        }
    } catch (e) {
        console.error(e);
        error.set(e.message);
    } finally {
        isLoading.set(false);
    }
}

export const latestStats = derived(dashboardData, ($data) => {
    if (!$data.dates.length) return null;
    const lastIdx = $data.dates.length - 1;
    const prevIdx = lastIdx - 1;

    const getChange = (arr, period = 7) => {
        if (!arr || arr.length <= period) return 0;
        const current = arr[lastIdx];
        const previous = arr[lastIdx - period];
        if (previous === 0 || previous === null || previous === undefined) return 0;
        return ((current - previous) / previous) * 100;
    };

    const safeGet = (arr, idx) => {
        if (!arr || idx < 0 || idx >= arr.length) return null;
        return arr[idx];
    };

    const getLatestValue = (path) => {
        const arr = path.split('.').reduce((obj, key) => obj?.[key], $data);
        if (!arr || !arr.length) return null;
        return arr[arr.length - 1];
    };

    return {
        gli: {
            value: getLatestValue('gli.total'),
            change: getChange($data.gli.total)
        },
        us_net_liq: {
            value: getLatestValue('us_net_liq'),
            change: getChange($data.us_net_liq)
        },
        cli: {
            value: getLatestValue('cli.total'),
            change: (safeGet($data.cli?.total, lastIdx) ?? 0) - (safeGet($data.cli?.total, prevIdx) ?? 0)
        },
        vix: {
            value: getLatestValue('vix.total'),
            change: getChange($data.vix?.total)
        },
        move: {
            value: getLatestValue('move.total'),
            change: getChange($data.move?.total)
        },
        btc: {
            price: getLatestValue('btc.price'),
            fair_value: getLatestValue('btc.models.macro.fair_value'),
            deviation_zscore: getLatestValue('btc.models.macro.deviation_zscore'),
            deviation_pct: getLatestValue('btc.models.macro.deviation_pct')
        }
    };
});
