/**
 * Series Configuration
 * 
 * Centralized definitions for all chart series including colors, names, and line styles.
 * This allows consistent styling across all charts and easy maintenance.
 */

/**
 * Line style presets
 */
export const LINE_STYLES = {
    solid: { dash: 'solid' },
    dashed: { dash: 'dash' },
    dotted: { dash: 'dot' },
    dashdot: { dash: 'dashdot' }
};

/**
 * Line width presets
 */
export const LINE_WIDTHS = {
    thin: 1,
    default: 2,
    thick: 3
};

/**
 * Series configuration registry
 * 
 * Each entry contains:
 * - color: Hex color for the series
 * - name: Display name for legends
 * - line: Line style configuration (width, dash)
 * - fill: Optional fill style for area charts
 */
export const SERIES_CONFIG = {
    // ==========================================
    // CREDIT & LIQUIDITY
    // ==========================================
    CLI: {
        color: '#10b981',
        name: 'CLI Aggregate',
        line: { width: 3 }
    },
    CLI_Z: {
        color: '#10b981',
        name: 'CLI (Z-Score)',
        line: { width: 3 }
    },
    CLI_PCT: {
        color: '#10b981',
        name: 'CLI (Percentile)',
        line: { width: 3 }
    },

    // High Yield Spread
    HY_SPREAD: {
        color: '#ef4444',
        name: 'HY Spread',
        line: { width: 2 }
    },
    HY_SPREAD_Z: {
        color: '#ef4444',
        name: 'HY Spread (Z-Score)',
        line: { width: 2 }
    },
    HY_SPREAD_PCT: {
        color: '#ef4444',
        name: 'HY Spread (Percentile)',
        line: { width: 2 }
    },
    HY_SPREAD_RAW: {
        color: '#ef4444',
        name: 'HY Spread (bps)',
        line: { width: 2 }
    },

    // Investment Grade Spread
    IG_SPREAD: {
        color: '#38bdf8',
        name: 'IG Spread',
        line: { width: 2 }
    },
    IG_SPREAD_Z: {
        color: '#38bdf8',
        name: 'IG Spread (Z-Score)',
        line: { width: 2 }
    },
    IG_SPREAD_PCT: {
        color: '#38bdf8',
        name: 'IG Spread (Percentile)',
        line: { width: 2 }
    },
    IG_SPREAD_RAW: {
        color: '#38bdf8',
        name: 'IG Spread (bps)',
        line: { width: 2 }
    },

    // NFCI
    NFCI_CREDIT: {
        color: '#3b82f6',
        name: 'NFCI Credit',
        line: { width: 2 }
    },
    NFCI_RISK: {
        color: '#a855f7',
        name: 'NFCI Risk',
        line: { width: 2 }
    },

    // Lending
    LENDING: {
        color: '#3b82f6',
        name: 'Lending Standards',
        line: { width: 2 }
    },

    // ==========================================
    // VOLATILITY
    // ==========================================
    VIX: {
        color: '#dc2626',
        name: 'VIX',
        line: { width: 2 }
    },
    VIX_Z: {
        color: '#dc2626',
        name: 'VIX (Z-Score)',
        line: { width: 2 }
    },
    VIX_PCT: {
        color: '#dc2626',
        name: 'VIX (Percentile)',
        line: { width: 2 }
    },

    MOVE: {
        color: '#3b82f6',
        name: 'MOVE Index',
        line: { width: 2 }
    },

    FX_VOL: {
        color: '#06b6d4',
        name: 'FX Volatility',
        line: { width: 2 }
    },

    // Stress Indices
    STLFSI: {
        color: '#7c3aed',
        name: 'St. Louis FSI',
        line: { width: 2 }
    },
    KCFSI: {
        color: '#c026d3',
        name: 'Kansas City FSI',
        line: { width: 2 }
    },

    // ==========================================
    // RATES / TREASURY
    // ==========================================
    TREASURY_10Y: {
        color: '#3b82f6',
        name: '10Y UST Yield',
        line: { width: 2 }
    },
    TREASURY_2Y: {
        color: '#6366f1',
        name: '2Y UST Yield',
        line: { width: 2 }
    },
    TREASURY_30Y: {
        color: '#8b5cf6',
        name: '30Y UST Yield',
        line: { width: 2 }
    },
    TREASURY_5Y: {
        color: '#60a5fa',
        name: '5Y UST Yield',
        line: { width: 2 }
    },

    // Yield Curves
    YC_10Y_2Y: {
        color: '#8b5cf6',
        name: '10Y-2Y Spread',
        line: { width: 2.5 },
        fill: { tozeroy: true, color: 'rgba(139, 92, 246, 0.1)' }
    },
    YC_30Y_10Y: {
        color: '#0891b2',
        name: '30Y-10Y Spread',
        line: { width: 2.5 },
        fill: { tozeroy: true, color: 'rgba(8, 145, 178, 0.1)' }
    },
    YC_30Y_2Y: {
        color: '#0891b2',
        name: '30Y-2Y Spread',
        line: { width: 2.5 },
        fill: { tozeroy: true, color: 'rgba(8, 145, 178, 0.1)' }
    },

    // ==========================================
    // REPO / MONEY MARKETS
    // ==========================================
    SOFR: {
        color: '#3b82f6',
        name: 'SOFR',
        line: { width: 2, dash: 'solid' }
    },
    IORB: {
        color: '#22c55e',
        name: 'IORB (Floor)',
        line: { width: 2, dash: 'dash' }
    },
    SRF_RATE: {
        color: '#ef4444',
        name: 'SRF Rate (Ceiling)',
        line: { width: 2, dash: 'dot' }
    },
    RRP_AWARD: {
        color: '#f59e0b',
        name: 'RRP Award',
        line: { width: 1, dash: 'dashdot' }
    },
    SOFR_VOLUME: {
        color: '#10b981',
        name: 'SOFR Volume',
        line: { width: 2 },
        fill: { tozeroy: true, color: 'rgba(16, 185, 129, 0.2)' }
    },

    // ==========================================
    // TIPS / INFLATION
    // ==========================================
    TIPS_BREAKEVEN: {
        color: '#f59e0b',
        name: '10Y Breakeven',
        line: { width: 2 }
    },
    TIPS_REAL_RATE: {
        color: '#3b82f6',
        name: '10Y Real Rate',
        line: { width: 2 }
    },
    TIPS_5Y5Y: {
        color: '#a855f7',
        name: '5Y5Y Forward',
        line: { width: 2 }
    },

    // ==========================================
    // GLOBAL LIQUIDITY
    // ==========================================
    GLI_TOTAL: {
        color: '#10b981',
        name: 'Global Liquidity Index',
        line: { width: 3 }
    },

    // Central Banks
    CB_FED: {
        color: '#3b82f6',
        name: 'Federal Reserve',
        line: { width: 2 }
    },
    CB_ECB: {
        color: '#f59e0b',
        name: 'ECB',
        line: { width: 2 }
    },
    CB_BOJ: {
        color: '#ef4444',
        name: 'Bank of Japan',
        line: { width: 2 }
    },
    CB_PBOC: {
        color: '#a855f7',
        name: 'PBoC',
        line: { width: 2 }
    },
    CB_BOE: {
        color: '#06b6d4',
        name: 'Bank of England',
        line: { width: 2 }
    },
    CB_BOC: {
        color: '#ec4899',
        name: 'Bank of Canada',
        line: { width: 2 }
    },
    CB_RBA: {
        color: '#84cc16',
        name: 'RBA',
        line: { width: 2 }
    },
    CB_SNB: {
        color: '#14b8a6',
        name: 'SNB',
        line: { width: 2 }
    },

    CB_BREADTH: {
        color: '#10b981',
        name: 'CB Breadth',
        line: { width: 2 },
        fill: { tozeroy: true, color: 'rgba(16, 185, 129, 0.1)' }
    },
    CB_HHI: {
        color: '#f59e0b',
        name: 'CB Concentration (HHI)',
        line: { width: 2 }
    },

    // ==========================================
    // DIVERGENCE
    // ==========================================
    CLI_GLI_DIV: {
        color: '#a855f7',
        name: 'CLI-GLI Divergence',
        line: { width: 2 }
    },

    // ==========================================
    // BITCOIN / CRYPTO
    // ==========================================
    BTC: {
        color: '#f7931a',
        name: 'Bitcoin',
        line: { width: 2 }
    },
    ETH: {
        color: '#627eea',
        name: 'Ethereum',
        line: { width: 2 }
    },

    // Stablecoins
    USDT: {
        color: '#26a17b',
        name: 'USDT',
        line: { width: 2 }
    },
    USDC: {
        color: '#2775ca',
        name: 'USDC',
        line: { width: 2 }
    }
};

/**
 * Helper function to create a Plotly trace from a series key
 * 
 * @param {string} seriesKey - Key from SERIES_CONFIG
 * @param {Array} x - X-axis data (dates)
 * @param {Array} y - Y-axis data (values)
 * @param {Object} overrides - Optional overrides for any property
 * @returns {Object} Plotly trace object
 */
export function createTrace(seriesKey, x, y, overrides = {}) {
    const config = SERIES_CONFIG[seriesKey] || {};

    const trace = {
        x,
        y,
        name: config.name || seriesKey,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: config.color || '#888888',
            width: config.line?.width || 2,
            ...(config.line?.dash && { dash: config.line.dash }),
            ...overrides.line
        }
    };

    // Add fill if configured
    if (config.fill?.tozeroy) {
        trace.fill = 'tozeroy';
        trace.fillcolor = config.fill.color || `${config.color}20`;
    }

    // Apply any overrides
    return { ...trace, ...overrides, line: { ...trace.line, ...overrides.line } };
}

/**
 * Get series color by key
 * 
 * @param {string} seriesKey - Key from SERIES_CONFIG
 * @returns {string} Hex color
 */
export function getSeriesColor(seriesKey) {
    return SERIES_CONFIG[seriesKey]?.color || '#888888';
}

/**
 * Get series name by key
 * 
 * @param {string} seriesKey - Key from SERIES_CONFIG
 * @returns {string} Display name
 */
export function getSeriesName(seriesKey) {
    return SERIES_CONFIG[seriesKey]?.name || seriesKey;
}
