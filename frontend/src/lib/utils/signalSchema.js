/**
 * Signal Schema Module
 * ====================
 * Centralized signal definitions for frontend consistency with backend.
 * This mirrors the STANCE_KEYS and STATE_SCORES from signal_config.py.
 */

// Primary factors for bull/bear aggregation (12 canonical signals)
export const STANCE_KEYS = [
    "cli", "hy_spread", "ig_spread", "nfci_credit", "nfci_risk",
    "lending", "vix", "move", "fx_vol", "repo", "tips", "yield_curve"
];

// State to score mapping (must match backend STATE_SCORES)
export const STATE_SCORES = {
    bullish: 1.0,
    neutral: 0.0,
    warning: -0.5,
    bearish: -1.0,
    danger: -2.0,
    unknown: 0.0,
};

// Category classification for grouping signals
export const SIGNAL_CATEGORIES = {
    cli: "credit",
    hy_spread: "credit",
    ig_spread: "credit",
    nfci_credit: "credit",
    nfci_risk: "credit",
    lending: "credit",
    vix: "volatility",
    move: "volatility",
    fx_vol: "volatility",
    repo: "liquidity",
    tips: "rates",
    yield_curve: "rates"
};

// Signal weights (must match backend for consistency)
export const SIGNAL_WEIGHTS = {
    cli: 0.15,
    hy_spread: 0.12,
    ig_spread: 0.08,
    nfci_credit: 0.10,
    nfci_risk: 0.08,
    lending: 0.07,
    vix: 0.10,
    move: 0.05,
    fx_vol: 0.05,
    repo: 0.10,
    tips: 0.05,
    yield_curve: 0.05
};

/**
 * Get signal with backward compatibility fallback.
 * Handles repo_stress -> repo rename.
 */
export function getSignalWithFallback(signals, key) {
    if (signals && signals[key]) {
        return signals[key];
    }
    // Backward compatibility: repo_stress -> repo
    if (key === "repo" && signals && signals["repo_stress"]) {
        return signals["repo_stress"];
    }
    return null;
}

/**
 * Calculate aggregate score from signals (client-side).
 * This mirrors the backend aggregate_signal_score function.
 */
export function calculateAggregateScore(signals) {
    let score = 0;
    let coverage = 0;
    let confidenceSum = 0;
    const missing = [];

    for (const key of STANCE_KEYS) {
        const weight = SIGNAL_WEIGHTS[key] || 0;
        const signal = getSignalWithFallback(signals, key);

        if (signal && signal.state && signal.state !== "unknown") {
            const stateScore = STATE_SCORES[signal.state] ?? 0;
            const conf = signal.confidence ?? 0.5;

            score += weight * stateScore;
            coverage += weight;
            confidenceSum += weight * conf;
        } else {
            missing.push(key);
        }
    }

    // Renormalize if coverage < 1
    if (coverage > 0 && coverage < 1) {
        score = score / coverage;
    }

    // Classify aggregate state
    let aggState;
    if (score >= 0.3) aggState = "bullish";
    else if (score >= 0.1) aggState = "leaning_bullish";
    else if (score <= -0.5) aggState = "bearish";
    else if (score <= -0.2) aggState = "leaning_bearish";
    else aggState = "neutral";

    const avgConfidence = coverage > 0 ? confidenceSum / coverage : 0;

    return {
        score: Math.round(score * 1000) / 1000,
        state: aggState,
        coverage: Math.round(coverage * 1000) / 1000,
        missing_keys: missing,
        confidence: Math.round(avgConfidence * 1000) / 1000
    };
}
