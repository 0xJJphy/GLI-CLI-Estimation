"""
Signal Configuration Module
============================
Centralized signal definitions for macro/financial indicators.
This is the SINGLE SOURCE OF TRUTH for all signal thresholds and logic.

Usage:
    from signal_config import SIGNAL_CONFIG, compute_signal

Architecture:
    - Each signal has: direction, thresholds, reasons
    - Thresholds define state boundaries (bullish/warning/bearish)
    - Reasons provide human-readable explanations
    - compute_signal() returns {state, value, reason, confidence}
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SignalState(Enum):
    """Unified signal states across all indicators."""
    BULLISH = "bullish"
    WARNING = "warning"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    DANGER = "danger"  # Systemic stress (e.g., SRF usage)
    UNKNOWN = "unknown"  # Missing data


# State to score mapping for weighted aggregation
STATE_SCORES = {
    "bullish": 1.0,
    "neutral": 0.0,
    "warning": -0.5,
    "bearish": -1.0,
    "danger": -2.0,
    "unknown": 0.0,
}


class SignalDirection(Enum):
    """Direction convention for signal interpretation."""
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"
    COMPOSITE = "composite"  # Multi-dimensional (e.g., TIPS)


@dataclass
class SignalResult:
    """Standardized signal output structure."""
    state: str
    value: float
    reason: str
    confidence: float  # 0-1, distance from threshold + data freshness
    label: Optional[str] = None  # Optional display label (e.g., "Reflation")


# =============================================================================
# UNIFIED SIGNAL CONFIGURATION
# =============================================================================

SIGNAL_CONFIG: Dict[str, Dict[str, Any]] = {
    
    # -------------------------------------------------------------------------
    # REPO (SOFR-IORB Spread) - formerly repo_stress
    # -------------------------------------------------------------------------
    # Spread = SOFR - IORB in basis points
    # Lower spread = better liquidity conditions
    "repo": {
        "direction": SignalDirection.LOWER_IS_BETTER,
        "weight": 0.10,
        "category": "liquidity",
        "units": "bps",
        "thresholds": {
            # bullish: spread <= 0 (SOFR at or below IORB)
            "bullish_max": 0.0,
            # warning: 0 < spread <= 5 bps
            "warning_max": 5.0,
            # bearish: spread > 5 bps
            "bearish_min": 5.0,
            # danger: SRF usage > $1B (banks tapping Fed backstop at ceiling rate)
            # Note: Small SRF usage (<$1B) is normal operational noise
            "srf_usage_threshold": 1.0,  # Billions USD
        },
        "reasons": {
            SignalState.BULLISH: "SOFR ≈ IORB: adequate interbank liquidity",
            SignalState.WARNING: "SOFR slightly above IORB: monitor repo conditions",
            SignalState.BEARISH: "SOFR >> IORB: repo liquidity stress detected",
            SignalState.DANGER: "SRF Usage > $1B: banks borrowing at ceiling rate",
            SignalState.NEUTRAL: "Repo spread in normal operating range",
        },
        "hysteresis": 0.5,  # bps buffer to prevent flip-flops
    },
    
    # -------------------------------------------------------------------------
    # TIPS (Breakeven + Real Rate composite)
    # -------------------------------------------------------------------------
    # 2D grid: (BE level, RR level) -> signal
    "tips": {
        "direction": SignalDirection.COMPOSITE,
        "weight": 0.05,
        "category": "rates",
        "units": "%",
        "thresholds": {
            # Breakeven thresholds (%)
            "be_high": 2.5,
            "be_low": 2.0,
            # Real Rate thresholds (%)
            "rr_high": 2.0,
            "rr_low": 0.5,
        },
        "grid": {
            # (BE_level, RR_level) -> (state, label)
            ("high", "low"): (SignalState.BULLISH, "Reflation"),
            ("high", "high"): (SignalState.WARNING, "Stagflation"),
            ("low", "high"): (SignalState.BEARISH, "Tightening"),
            ("low", "low"): (SignalState.NEUTRAL, "Disinflation"),
            ("normal", "normal"): (SignalState.NEUTRAL, "Goldilocks"),
            ("normal", "high"): (SignalState.WARNING, "Rate Pressure"),
            ("normal", "low"): (SignalState.BULLISH, "Accommodative"),
            ("high", "normal"): (SignalState.WARNING, "Inflation Watch"),
            ("low", "normal"): (SignalState.NEUTRAL, "Low Inflation"),
        },
        "reasons": {
            SignalState.BULLISH: "BE high + RR low: reflation environment, Fed dovish",
            SignalState.WARNING: "BE high + RR high: stagflation risk, monitor closely",
            SignalState.BEARISH: "RR high + BE low: tightening, Fed hawkish stance",
            SignalState.NEUTRAL: "BE and RR in normal range, macro equilibrium",
            SignalState.DANGER: "Forward inflation expectations collapsing",
        },
    },
    
    # -------------------------------------------------------------------------
    # CREDIT SPREADS (HY & IG)
    # -------------------------------------------------------------------------
    # Note: These use INVERTED Z-scores in cli_df, so higher Z = better
    "hy_spread": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # Inverted Z
        "weight": 0.12,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 1.2,   # Z > 1.2 (spread contracted)
            "bearish_max": -1.2,  # Z < -1.2 (spread widened)
        },
        "reasons": {
            SignalState.BULLISH: "HY spread contracted: risk appetite, easy credit",
            SignalState.BEARISH: "HY spread widened: risk aversion, credit stress",
            SignalState.NEUTRAL: "HY spread in normal range, no extreme signal",
        },
    },
    
    "ig_spread": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # Inverted Z
        "weight": 0.08,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 1.2,
            "bearish_max": -1.2,
        },
        "reasons": {
            SignalState.BULLISH: "IG spread low: solid credit conditions",
            SignalState.BEARISH: "IG spread elevated: credit market tension",
            SignalState.NEUTRAL: "IG spread stable, normal conditions",
        },
    },
    
    # -------------------------------------------------------------------------
    # CLI (Credit Liquidity Index)
    # -------------------------------------------------------------------------
    "cli": {
        "direction": SignalDirection.HIGHER_IS_BETTER,
        "weight": 0.15,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 0.5,
            "bearish_max": -0.5,
        },
        "momentum_required": True,  # Confirm with 4w momentum
        "reasons": {
            SignalState.BULLISH: "CLI indicates credit expansion and risk appetite",
            SignalState.BEARISH: "CLI indicates credit contraction and risk aversion",
            SignalState.NEUTRAL: "CLI neutral, balanced liquidity conditions",
        },
    },

    # -------------------------------------------------------------------------
    # NFCI CREDIT (NEGATED)
    # -------------------------------------------------------------------------
    "nfci_credit": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # After negation
        "weight": 0.10,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 0.5,
            "bearish_max": -0.6,
        },
        "reasons": {
            SignalState.BULLISH: "NFCI Credit negative: loose credit conditions",
            SignalState.BEARISH: "NFCI Credit positive: restrictive credit conditions",
            SignalState.NEUTRAL: "NFCI Credit neutral, no extreme pressure",
        },
    },
    
    # -------------------------------------------------------------------------
    # NFCI (Risk subindex, NEGATED)
    # -------------------------------------------------------------------------
    "nfci_risk": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # After negation
        "weight": 0.08,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 0.5,
            "bearish_max": -1.2,  # Asymmetric: bearish only on extreme stress
        },
        "reasons": {
            SignalState.BULLISH: "NFCI Risk low: systemic risk contained",
            SignalState.BEARISH: "NFCI Risk elevated: higher perceived systemic risk",
            SignalState.NEUTRAL: "NFCI Risk at normal levels",
        },
    },
    
    # -------------------------------------------------------------------------
    # LENDING STANDARDS (SLOOS, NEGATED)
    # -------------------------------------------------------------------------
    "lending": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # After negation
        "weight": 0.07,
        "category": "credit",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 0.1,
            "bearish_max": -0.6,
        },
        "reasons": {
            SignalState.BULLISH: "Credit standards relaxed: credit expansion",
            SignalState.BEARISH: "Restrictive standards: credit contraction",
            SignalState.NEUTRAL: "Lending standards unchanged",
        },
    },
    
    # -------------------------------------------------------------------------
    # VIX (Volatility, NEGATED)
    # -------------------------------------------------------------------------
    "vix": {
        "direction": SignalDirection.HIGHER_IS_BETTER,  # After negation
        "weight": 0.10,
        "category": "volatility",
        "units": "z-score",
        "thresholds": {
            "bullish_min": 0.7,
            "bearish_max": -2.2,  # Very asymmetric: bearish only in panic
        },
        "reasons": {
            SignalState.BULLISH: "VIX low: market complacency/confidence",
            SignalState.BEARISH: "VIX elevated: fear and market volatility",
            SignalState.NEUTRAL: "VIX in normal range, moderate volatility",
        },
    },
    
    # -------------------------------------------------------------------------
    # MOVE INDEX (Bond Volatility)
    # -------------------------------------------------------------------------
    "move": {
        "direction": SignalDirection.LOWER_IS_BETTER,
        "weight": 0.05,
        "category": "volatility",
        "units": "index",
        "thresholds": {
            "bullish_max": 80,
            "bearish_min": 120,
        },
        "reasons": {
            SignalState.BULLISH: "MOVE low: stable bond market/liquidity",
            SignalState.BEARISH: "MOVE high: bond market stress/repricing",
            SignalState.NEUTRAL: "MOVE average: normal bond volatility",
        },
    },
    
    # -------------------------------------------------------------------------
    # FX VOLATILITY (EVZ)
    # -------------------------------------------------------------------------
    "fx_vol": {
        "direction": SignalDirection.LOWER_IS_BETTER,
        "weight": 0.05,
        "category": "volatility",
        "units": "index",
        "thresholds": {
            "bullish_max": 8,
            "bearish_min": 12,
        },
        "reasons": {
            SignalState.BULLISH: "FX Vol low: stable global flows",
            SignalState.BEARISH: "FX Vol high: currency market stress",
            SignalState.NEUTRAL: "FX Vol average: normal currency volatility",
        },
    },

    # -------------------------------------------------------------------------
    # YIELD CURVE (10Y-2Y Spread)
    # -------------------------------------------------------------------------
    "yield_curve": {
        "direction": SignalDirection.HIGHER_IS_BETTER,
        "weight": 0.05,
        "category": "rates",
        "units": "bps",
        "thresholds": {
            "bullish_min": 50,   # Normal positive slope
            "bearish_max": -10,  # Inverted
        },
        "reasons": {
            SignalState.BULLISH: "Yield curve normal: growth expectations healthy",
            SignalState.BEARISH: "Yield curve inverted: recession signal",
            SignalState.NEUTRAL: "Yield curve flat: uncertain growth outlook",
        },
    },
}

# Backward compatibility alias
SIGNAL_CONFIG["repo_stress"] = SIGNAL_CONFIG["repo"]  # Deprecated


# =============================================================================
# SIGNAL COMPUTATION FUNCTIONS
# =============================================================================

def compute_signal(
    indicator: str,
    value: float,
    momentum: Optional[float] = None,
    srf_usage: bool = False,
    be_value: Optional[float] = None,  # For TIPS
    rr_value: Optional[float] = None,  # For TIPS
) -> SignalResult:
    """
    Compute signal state for a given indicator.
    
    Args:
        indicator: Key from SIGNAL_CONFIG (e.g., 'repo_stress', 'hy_spread')
        value: Current value or Z-score
        momentum: Optional 4-week momentum for confirmation
        srf_usage: True if SRF facility is being used (repo only)
        be_value: Breakeven inflation (TIPS only)
        rr_value: Real rate (TIPS only)
    
    Returns:
        SignalResult with state, value, reason, confidence
    """
    if indicator not in SIGNAL_CONFIG:
        return SignalResult(
            state=SignalState.NEUTRAL.value,
            value=value,
            reason=f"Unknown indicator: {indicator}",
            confidence=0.0
        )
    
    config = SIGNAL_CONFIG[indicator]
    
    # Special handling for TIPS (composite 2D)
    if indicator == "tips":
        return _compute_tips_signal(config, be_value, rr_value)
    
    # Special handling for repo stress (includes SRF danger)
    # Both 'repo' (canonical) and 'repo_stress' (backward-compat) use same logic
    if indicator in ("repo", "repo_stress"):
        return _compute_repo_signal(SIGNAL_CONFIG["repo"], value, srf_usage)
    
    # Standard single-value signals
    return _compute_standard_signal(config, indicator, value, momentum)


def _compute_tips_signal(
    config: Dict,
    be_value: Optional[float],
    rr_value: Optional[float]
) -> SignalResult:
    """Compute TIPS signal using 2D grid."""
    if be_value is None or rr_value is None:
        return SignalResult(
            state=SignalState.NEUTRAL.value,
            value=0,
            reason="Insufficient TIPS data",
            confidence=0.0
        )
    
    thresholds = config["thresholds"]
    
    # Classify BE level
    if be_value >= thresholds["be_high"]:
        be_level = "high"
    elif be_value <= thresholds["be_low"]:
        be_level = "low"
    else:
        be_level = "normal"
    
    # Classify RR level
    if rr_value >= thresholds["rr_high"]:
        rr_level = "high"
    elif rr_value <= thresholds["rr_low"]:
        rr_level = "low"
    else:
        rr_level = "normal"
    
    # Look up grid
    grid_key = (be_level, rr_level)
    if grid_key in config["grid"]:
        state, label = config["grid"][grid_key]
    else:
        state, label = SignalState.NEUTRAL, "Mixed"
    
    reason = config["reasons"].get(state, "TIPS signal computed")
    
    # Confidence based on distance from thresholds
    be_dist = min(abs(be_value - thresholds["be_high"]), 
                  abs(be_value - thresholds["be_low"]))
    rr_dist = min(abs(rr_value - thresholds["rr_high"]), 
                  abs(rr_value - thresholds["rr_low"]))
    confidence = min(1.0, (be_dist + rr_dist) / 2.0)
    
    return SignalResult(
        state=state.value,
        value=be_value,  # Report BE as primary value
        reason=reason,
        confidence=confidence,
        label=label
    )


def _compute_repo_signal(
    config: Dict,
    spread: float,
    srf_usage: bool
) -> SignalResult:
    """Compute repo stress signal with SRF danger overlay."""
    thresholds = config["thresholds"]
    reasons = config["reasons"]
    
    # SRF usage overrides everything
    if srf_usage:
        return SignalResult(
            state=SignalState.DANGER.value,
            value=spread,
            reason=reasons[SignalState.DANGER],
            confidence=1.0,
            label="SRF Active"
        )
    
    # Apply thresholds
    if spread <= thresholds["bullish_max"]:
        state = SignalState.BULLISH
        confidence = min(1.0, abs(spread) / 5.0)
    elif spread <= thresholds["warning_max"]:
        state = SignalState.WARNING
        confidence = 1.0 - (spread / thresholds["warning_max"])
    else:
        state = SignalState.BEARISH
        confidence = min(1.0, (spread - thresholds["bearish_min"]) / 10.0)
    
    return SignalResult(
        state=state.value,
        value=spread,
        reason=reasons[state],
        confidence=confidence
    )


def _compute_standard_signal(
    config: Dict,
    indicator: str,
    value: float,
    momentum: Optional[float]
) -> SignalResult:
    """Compute signal for standard single-value indicators."""
    thresholds = config["thresholds"]
    reasons = config["reasons"]
    direction = config["direction"]
    
    # Check if momentum confirmation is required
    needs_momentum = config.get("momentum_required", False)
    
    state = SignalState.NEUTRAL
    
    if direction == SignalDirection.HIGHER_IS_BETTER:
        bullish_min = thresholds.get("bullish_min")
        bearish_max = thresholds.get("bearish_max")
        
        if bullish_min is not None and value >= bullish_min:
            if not needs_momentum or (momentum is not None and momentum > 0):
                state = SignalState.BULLISH
        elif bearish_max is not None and value <= bearish_max:
            if not needs_momentum or (momentum is not None and momentum < 0):
                state = SignalState.BEARISH
                
    elif direction == SignalDirection.LOWER_IS_BETTER:
        bullish_max = thresholds.get("bullish_max")
        bearish_min = thresholds.get("bearish_min")
        
        if bullish_max is not None and value <= bullish_max:
            state = SignalState.BULLISH
        elif bearish_min is not None and value >= bearish_min:
            state = SignalState.BEARISH
    
    # Calculate confidence (distance from threshold)
    confidence = 0.5  # Default moderate confidence
    if state == SignalState.BULLISH:
        if direction == SignalDirection.HIGHER_IS_BETTER:
            confidence = min(1.0, (value - thresholds.get("bullish_min", 0)) / 2.0)
        else:
            confidence = min(1.0, (thresholds.get("bullish_max", 0) - value) / 2.0)
    elif state == SignalState.BEARISH:
        if direction == SignalDirection.HIGHER_IS_BETTER:
            confidence = min(1.0, (thresholds.get("bearish_max", 0) - value) / 2.0)
        else:
            confidence = min(1.0, (value - thresholds.get("bearish_min", 0)) / 2.0)
    
    return SignalResult(
        state=state.value,
        value=value,
        reason=reasons.get(state, f"{indicator} signal computed"),
        confidence=abs(confidence)
    )


def get_signal_config(indicator: str) -> Optional[Dict]:
    """Get configuration for a specific indicator."""
    return SIGNAL_CONFIG.get(indicator)


def get_all_indicators() -> list:
    """Get list of all configured indicator keys."""
    return list(SIGNAL_CONFIG.keys())


# =============================================================================
# STANCE KEYS (Primary factors for aggregation)
# =============================================================================
# These are the 12 canonical signals used for bull/bear scoring.
# Does NOT include backward-compat aliases (repo_stress) or composite sub-parts.

STANCE_KEYS = [
    "cli", "hy_spread", "ig_spread", "nfci_credit", "nfci_risk",
    "lending", "vix", "move", "fx_vol", "repo", "tips", "yield_curve"
]


def validate_weights() -> Tuple[bool, float, list]:
    """
    Validate that weights sum to 1.0 for STANCE_KEYS.
    
    Returns:
        (is_valid, total_weight, missing_keys)
    """
    total = 0.0
    missing = []
    for key in STANCE_KEYS:
        cfg = SIGNAL_CONFIG.get(key)
        if cfg and "weight" in cfg:
            total += cfg["weight"]
        else:
            missing.append(key)
    
    is_valid = abs(total - 1.0) < 0.01  # Allow 1% tolerance
    return is_valid, round(total, 3), missing


def aggregate_signal_score(signals: Dict[str, Dict]) -> Dict:
    """
    Compute weighted aggregate score from individual signals.
    
    Args:
        signals: Dict of signal_key -> {state, confidence, ...}
    
    Returns:
        {
            score: float (-2 to +1 range),
            state: str (aggregate state),
            coverage: float (sum of weights with valid data),
            missing_keys: list,
            confidence: float (weighted average confidence)
        }
    """
    score = 0.0
    coverage = 0.0
    confidence_sum = 0.0
    missing = []
    
    for key in STANCE_KEYS:
        cfg = SIGNAL_CONFIG.get(key)
        if not cfg or "weight" not in cfg:
            continue
            
        weight = cfg["weight"]
        
        if key in signals and signals[key].get("state") not in (None, "unknown"):
            state = signals[key]["state"]
            sig_conf = signals[key].get("confidence", 0.5)
            
            score += weight * STATE_SCORES.get(state, 0.0)
            coverage += weight
            confidence_sum += weight * sig_conf
        else:
            missing.append(key)
    
    # Renormalize if coverage < 1 (missing data)
    if coverage > 0 and coverage < 1.0:
        score = score / coverage
    
    # Classify aggregate state
    if score >= 0.3:
        agg_state = "bullish"
    elif score >= 0.1:
        agg_state = "leaning_bullish"
    elif score <= -0.5:
        agg_state = "bearish"
    elif score <= -0.2:
        agg_state = "leaning_bearish"
    else:
        agg_state = "neutral"
    
    # Average confidence
    avg_confidence = confidence_sum / coverage if coverage > 0 else 0.0
    
    return {
        "score": round(score, 3),
        "state": agg_state,
        "coverage": round(coverage, 3),
        "missing_keys": missing,
        "confidence": round(avg_confidence, 3)
    }
