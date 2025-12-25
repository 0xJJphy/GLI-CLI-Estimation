import { writable, derived } from 'svelte/store';

export const dashboardData = writable({
    dates: [],
    last_dates: {},
    gli: { total: [], fed: [], ecb: [], boj: [], boe: [], pboc: [], rocs: {} },
    us_net_liq: [],
    us_net_liq_rocs: {},
    bank_rocs: { fed: {}, ecb: {}, boj: {}, boe: {}, pboc: {} },
    cli: [],
    vix: [],
    hy_spread: [],
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

    const getChange = (arr) => {
        if (!arr || arr.length < 2) return 0;
        return ((arr[lastIdx] - arr[prevIdx]) / arr[prevIdx]) * 100;
    };

    const safeGet = (arr, idx) => {
        if (!arr || idx < 0 || idx >= arr.length) return null;
        return arr[idx];
    };

    const getValue = (path, idx) => {
        const arr = path.split('.').reduce((obj, key) => obj?.[key], $data);
        return safeGet(arr, idx);
    };

    return {
        gli: {
            value: getValue('gli.total', lastIdx),
            change: getChange($data.gli.total)
        },
        us_net_liq: {
            value: getValue('us_net_liq', lastIdx),
            change: getChange($data.us_net_liq)
        },
        cli: {
            value: getValue('cli', lastIdx),
            change: (safeGet($data.cli, lastIdx) ?? 0) - (safeGet($data.cli, prevIdx) ?? 0)
        },
        vix: {
            value: getValue('vix', lastIdx),
            change: getChange($data.vix)
        }
    };
});
