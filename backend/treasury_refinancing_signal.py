"""
Treasury Refinancing Impact Signal
==================================
Comprehensive signal combining:
1. Auction Demand (Bid-to-Cover, Indirect %, Dealer %)
2. Net Issuance Impact (TGA dynamics, Net Liquidity drain)
3. Funding Stress (SOFR-IORB spread, SRF usage, Repo stress)
4. Forward Calendar (Upcoming settlement pressure)

Output: Single score from -100 (very bearish) to +100 (very bullish)
        with regime classification and trading implications.

Author: Quantitative Analysis Assistant
Date: January 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import os

# ==============================================================================
# CONFIGURATION & ENUMS
# ==============================================================================

class RefinancingRegime(Enum):
    """Treasury refinancing market regime classification."""
    LIQUIDITY_SURPLUS = "liquidity_surplus"      # TGA draining, strong demand, yields falling
    HEALTHY_ABSORPTION = "healthy_absorption"     # Normal rollover, stable yields
    MILD_PRESSURE = "mild_pressure"              # Some strain, yields drifting higher
    SUPPLY_STRESS = "supply_stress"              # Weak demand, dealers absorbing, yields rising
    FUNDING_CRISIS = "funding_crisis"            # Severe stress, Fed intervention likely

class SignalDirection(Enum):
    """Trading signal direction."""
    STRONG_BULLISH = "strong_bullish"    # Long duration, expect yields to fall
    BULLISH = "bullish"                   # Mild long bias
    NEUTRAL = "neutral"                   # No directional bias
    BEARISH = "bearish"                   # Mild short bias
    STRONG_BEARISH = "strong_bearish"    # Short duration, expect yields to rise

@dataclass
class SignalComponent:
    """Individual signal component with score and metadata."""
    name: str
    score: float              # -100 to +100
    weight: float             # Component weight (0 to 1)
    raw_value: Optional[float]
    threshold_breached: Optional[str]
    description: str
    alert_level: str          # normal, caution, warning, critical

# ==============================================================================
# SIGNAL THRESHOLDS
# ==============================================================================

# TGA Thresholds (in Trillions USD)
TGA_THRESHOLDS = {
    'very_high': 0.9,      # >$900B - Treasury has huge cash buffer, will drain
    'high': 0.7,           # >$700B - Elevated, expect some drainage
    'normal_high': 0.5,    # $500-700B - Normal operating range
    'normal_low': 0.3,     # $300-500B - Normal operating range  
    'low': 0.15,           # <$150B - Low, may need to rebuild (issuance coming)
    'critical_low': 0.05   # <$50B - Debt ceiling territory
}

# TGA Delta Thresholds (13-week change in Trillions)
TGA_DELTA_THRESHOLDS = {
    'large_drain': -0.15,   # Draining >$150B = Liquidity injection = Bullish
    'mild_drain': -0.05,    # Draining $50-150B = Mild bullish
    'neutral_low': -0.05,
    'neutral_high': 0.05,
    'mild_build': 0.10,     # Building $50-100B = Mild bearish
    'large_build': 0.15     # Building >$150B = Liquidity drain = Bearish
}

# Net Liquidity Delta Thresholds (13-week change in Trillions)
NETLIQ_DELTA_THRESHOLDS = {
    'large_injection': 0.3,   # >$300B injection = Very bullish
    'mild_injection': 0.1,    # $100-300B injection = Bullish
    'neutral_low': -0.1,
    'neutral_high': 0.1,
    'mild_drain': -0.2,       # $100-200B drain = Bearish
    'large_drain': -0.3       # >$300B drain = Very bearish
}

# SOFR-IORB Spread Thresholds (basis points)
SOFR_IORB_THRESHOLDS = {
    'very_tight': -5,      # SOFR well below IORB = Excess liquidity = Bullish
    'tight': 0,            # At or below IORB = Normal/healthy
    'elevated': 5,         # 5bp above = Mild funding pressure
    'stressed': 10,        # 10bp above = Significant stress
    'critical': 15         # 15bp+ = Crisis territory, SRF activation likely
}

# Auction Demand Score Thresholds
AUCTION_DEMAND_THRESHOLDS = {
    'strong': 30,
    'solid': 10,
    'neutral_low': -10,
    'soft': -30,
    'weak': -50
}

# ==============================================================================
# COMPONENT CALCULATORS
# ==============================================================================

def calculate_auction_demand_component(auction_data: Dict) -> SignalComponent:
    """
    Calculate signal component from auction demand data.
    
    Inputs from treasury_auction_demand module:
    - score: Overall demand score (-100 to +100)
    - by_type: Per-security-type breakdown
    - alerts: Alert summary
    
    Note: fetch_treasury_auction_demand() returns nested structure:
      {demand_score: {overall_score: X}, alerts: {...}}
    So we need to extract from both possible locations.
    """
    # Handle both direct {score: X} and nested {demand_score: {overall_score: X}} formats
    if 'demand_score' in auction_data:
        demand_score = auction_data.get('demand_score', {})
        score = demand_score.get('overall_score', 0)
    else:
        score = auction_data.get('score', 0)
    
    alerts = auction_data.get('alerts', {})
    alert_status = alerts.get('status', 'HEALTHY')

    
    # Determine alert level
    if alert_status == 'CRITICAL':
        alert_level = 'critical'
        description = "Critical auction demand weakness. Multiple stress signals."
    elif alert_status == 'ELEVATED':
        alert_level = 'warning'
        description = "Elevated auction stress. Dealers absorbing excess supply."
    elif alert_status in ['CAUTION', 'WATCH']:
        alert_level = 'caution'
        description = "Some auction strain. Foreign demand softening."
    else:
        if score >= 30:
            alert_level = 'normal'
            description = "Strong auction demand. Treasury financing smoothly."
        elif score >= 10:
            alert_level = 'normal'
            description = "Solid auction absorption. Normal market conditions."
        elif score >= -10:
            alert_level = 'normal'
            description = "Neutral auction demand. Market balanced."
        else:
            alert_level = 'caution'
            description = "Soft auction demand. Monitor for deterioration."
    
    # Determine threshold breached
    threshold_breached = None
    if score >= AUCTION_DEMAND_THRESHOLDS['strong']:
        threshold_breached = 'strong_demand'
    elif score <= AUCTION_DEMAND_THRESHOLDS['weak']:
        threshold_breached = 'weak_demand'
    elif score <= AUCTION_DEMAND_THRESHOLDS['soft']:
        threshold_breached = 'soft_demand'
    
    return SignalComponent(
        name="Auction Demand",
        score=score,
        weight=0.35,  # 35% weight
        raw_value=score,
        threshold_breached=threshold_breached,
        description=description,
        alert_level=alert_level
    )


def calculate_tga_component(us_metrics: Dict) -> SignalComponent:
    """
    Calculate signal component from TGA dynamics.
    
    Inputs from us_system_metrics:
    - tga_usd: Current TGA balance (Trillions)
    - tga_delta_4w: 4-week change
    - tga_delta_13w: 13-week change
    - tga_zscore: Z-score of current level
    """
    tga_current = us_metrics.get('tga_usd', 0.5)
    tga_delta_13w = us_metrics.get('tga_delta_13w', 0)
    tga_zscore = us_metrics.get('tga_zscore', 0)
    
    score = 0
    alerts = []
    
    # === TGA Level Component ===
    # High TGA = Treasury has cash, will eventually drain (bullish for liquidity)
    # Low TGA = Treasury needs to rebuild (issuance coming, bearish)
    if tga_current >= TGA_THRESHOLDS['very_high']:
        score += 25
        alerts.append("TGA very high - expect drainage (liquidity injection)")
    elif tga_current >= TGA_THRESHOLDS['high']:
        score += 15
        alerts.append("TGA elevated - some drainage likely")
    elif tga_current <= TGA_THRESHOLDS['critical_low']:
        score -= 30
        alerts.append("TGA critically low - debt ceiling or heavy issuance ahead")
    elif tga_current <= TGA_THRESHOLDS['low']:
        score -= 15
        alerts.append("TGA low - rebuilding phase likely (issuance)")
    
    # === TGA Delta Component (more important than level) ===
    # Negative delta = TGA draining = Money flowing to economy = Bullish
    # Positive delta = TGA building = Money leaving economy = Bearish
    if tga_delta_13w <= TGA_DELTA_THRESHOLDS['large_drain']:
        score += 40
        alerts.append(f"Large TGA drainage: ${abs(tga_delta_13w)*1000:.0f}B liquidity injection")
    elif tga_delta_13w <= TGA_DELTA_THRESHOLDS['mild_drain']:
        score += 20
        alerts.append(f"TGA draining: ${abs(tga_delta_13w)*1000:.0f}B liquidity injection")
    elif tga_delta_13w >= TGA_DELTA_THRESHOLDS['large_build']:
        score -= 40
        alerts.append(f"Large TGA build: ${tga_delta_13w*1000:.0f}B liquidity drain")
    elif tga_delta_13w >= TGA_DELTA_THRESHOLDS['mild_build']:
        score -= 20
        alerts.append(f"TGA building: ${tga_delta_13w*1000:.0f}B liquidity drain")
    
    # === Z-Score Extreme Detection ===
    if tga_zscore > 2.0:
        score += 10
        alerts.append("TGA z-score >2: Historically high, mean reversion (drain) likely")
    elif tga_zscore < -1.5:
        score -= 10
        alerts.append("TGA z-score <-1.5: Historically low, rebuild likely")
    
    # Clamp score
    score = max(-100, min(100, score))
    
    # Determine alert level
    if abs(tga_delta_13w) >= 0.15 or tga_current <= TGA_THRESHOLDS['critical_low']:
        alert_level = 'warning'
    elif abs(tga_delta_13w) >= 0.08 or tga_current <= TGA_THRESHOLDS['low']:
        alert_level = 'caution'
    else:
        alert_level = 'normal'
    
    # Description
    direction = "draining" if tga_delta_13w < 0 else "building"
    description = f"TGA ${tga_current*1000:.0f}B, {direction} ${abs(tga_delta_13w)*1000:.0f}B/13w. " + (alerts[0] if alerts else "Normal TGA dynamics.")
    
    return SignalComponent(
        name="TGA Dynamics",
        score=score,
        weight=0.25,  # 25% weight
        raw_value=tga_delta_13w,
        threshold_breached='large_build' if tga_delta_13w >= 0.15 else 'large_drain' if tga_delta_13w <= -0.15 else None,
        description=description,
        alert_level=alert_level
    )


def calculate_netliq_component(us_metrics: Dict) -> SignalComponent:
    """
    Calculate signal component from Net Liquidity dynamics.
    
    Net Liquidity = Fed Balance Sheet - TGA - RRP
    
    Inputs:
    - netliq_usd: Current net liquidity
    - netliq_delta_4w, netliq_delta_13w: Changes
    """
    netliq_delta_13w = us_metrics.get('netliq_delta_13w', 0)
    netliq_delta_4w = us_metrics.get('netliq_delta_4w', 0)
    
    score = 0
    
    # 13-week change is primary signal
    if netliq_delta_13w >= NETLIQ_DELTA_THRESHOLDS['large_injection']:
        score += 50
        description = f"Large liquidity injection: +${netliq_delta_13w*1000:.0f}B/13w"
        alert_level = 'normal'
    elif netliq_delta_13w >= NETLIQ_DELTA_THRESHOLDS['mild_injection']:
        score += 25
        description = f"Liquidity expanding: +${netliq_delta_13w*1000:.0f}B/13w"
        alert_level = 'normal'
    elif netliq_delta_13w <= NETLIQ_DELTA_THRESHOLDS['large_drain']:
        score -= 50
        description = f"Large liquidity drain: ${netliq_delta_13w*1000:.0f}B/13w"
        alert_level = 'warning'
    elif netliq_delta_13w <= NETLIQ_DELTA_THRESHOLDS['mild_drain']:
        score -= 25
        description = f"Liquidity contracting: ${netliq_delta_13w*1000:.0f}B/13w"
        alert_level = 'caution'
    else:
        score = netliq_delta_13w * 100  # Linear scale in neutral zone
        description = f"Net liquidity stable: {'+' if netliq_delta_13w >= 0 else ''}{netliq_delta_13w*1000:.0f}B/13w"
        alert_level = 'normal'
    
    # Acceleration/deceleration adjustment
    if netliq_delta_4w * 3 > netliq_delta_13w * 1.5:
        score += 10
        description += " (accelerating)"
    elif netliq_delta_4w * 3 < netliq_delta_13w * 0.5:
        score -= 10
        description += " (decelerating)"
    
    score = max(-100, min(100, score))
    
    return SignalComponent(
        name="Net Liquidity",
        score=score,
        weight=0.20,  # 20% weight
        raw_value=netliq_delta_13w,
        threshold_breached='large_drain' if netliq_delta_13w <= -0.3 else 'large_injection' if netliq_delta_13w >= 0.3 else None,
        description=description,
        alert_level=alert_level
    )


def calculate_funding_stress_component(repo_data: Dict, us_metrics: Dict) -> SignalComponent:
    """
    Calculate signal component from funding/repo market stress.
    
    Inputs:
    - sofr: Current SOFR rate
    - iorb: Interest on Reserve Balances
    - sofr_iorb_spread: SOFR - IORB spread (bp)
    - srf_usage: Standing Repo Facility usage
    - repo_stress_index: Composite repo stress
    """
    sofr = repo_data.get('sofr', 5.3)
    iorb = repo_data.get('iorb', 5.4)
    sofr_iorb_spread = (sofr - iorb) * 100  # Convert to basis points
    srf_usage = repo_data.get('srf_usage', 0)
    
    score = 0
    alerts = []
    alert_level = 'normal'
    
    # SOFR-IORB Spread Analysis
    if sofr_iorb_spread <= SOFR_IORB_THRESHOLDS['very_tight']:
        score += 30
        alerts.append(f"SOFR well below IORB ({sofr_iorb_spread:.0f}bp): Excess liquidity")
    elif sofr_iorb_spread <= SOFR_IORB_THRESHOLDS['tight']:
        score += 15
        alerts.append(f"SOFR at/below IORB ({sofr_iorb_spread:.0f}bp): Healthy")
    elif sofr_iorb_spread >= SOFR_IORB_THRESHOLDS['critical']:
        score -= 50
        alerts.append(f"SOFR critical spread ({sofr_iorb_spread:.0f}bp): Severe funding stress")
        alert_level = 'critical'
    elif sofr_iorb_spread >= SOFR_IORB_THRESHOLDS['stressed']:
        score -= 35
        alerts.append(f"SOFR stressed ({sofr_iorb_spread:.0f}bp): Significant funding pressure")
        alert_level = 'warning'
    elif sofr_iorb_spread >= SOFR_IORB_THRESHOLDS['elevated']:
        score -= 15
        alerts.append(f"SOFR elevated ({sofr_iorb_spread:.0f}bp): Mild funding pressure")
        alert_level = 'caution'
    
    # SRF Usage (Standing Repo Facility)
    if srf_usage > 0:
        if srf_usage > 50:  # >$50B
            score -= 30
            alerts.append(f"Heavy SRF usage: ${srf_usage:.0f}B - Fed providing emergency liquidity")
            alert_level = 'critical'
        elif srf_usage > 10:
            score -= 15
            alerts.append(f"SRF active: ${srf_usage:.0f}B - Some stress relief needed")
            alert_level = 'warning'
        else:
            score -= 5
            alerts.append(f"Minor SRF usage: ${srf_usage:.0f}B")
    
    score = max(-100, min(100, score))
    
    description = alerts[0] if alerts else f"Funding markets normal. SOFR-IORB: {sofr_iorb_spread:.0f}bp"
    
    return SignalComponent(
        name="Funding Stress",
        score=score,
        weight=0.20,  # 20% weight
        raw_value=sofr_iorb_spread,
        threshold_breached='critical_spread' if sofr_iorb_spread >= 15 else 'stressed' if sofr_iorb_spread >= 10 else None,
        description=description,
        alert_level=alert_level
    )


# ==============================================================================
# MAIN SIGNAL CALCULATOR
# ==============================================================================

def calculate_refinancing_impact_signal(
    auction_demand: Dict,
    us_metrics: Dict,
    repo_data: Dict,
    treasury_settlements: Dict = None
) -> Dict:
    """
    Calculate the comprehensive Treasury Refinancing Impact Signal.
    
    Parameters:
    -----------
    auction_demand : Dict
        Output from get_auction_demand_for_pipeline()
    us_metrics : Dict
        US system metrics including TGA, Net Liquidity
    repo_data : Dict
        Repo/funding market data including SOFR, IORB
    treasury_settlements : Dict, optional
        Upcoming Treasury settlement calendar
    
    Returns:
    --------
    Dict : Complete signal with score, regime, components, and recommendations
    """
    
    # Calculate individual components
    components = []
    
    # 1. Auction Demand (35%)
    auction_component = calculate_auction_demand_component(auction_demand)
    components.append(auction_component)
    
    # 2. TGA Dynamics (25%)
    tga_component = calculate_tga_component(us_metrics)
    components.append(tga_component)
    
    # 3. Net Liquidity (20%)
    netliq_component = calculate_netliq_component(us_metrics)
    components.append(netliq_component)
    
    # 4. Funding Stress (20%)
    funding_component = calculate_funding_stress_component(repo_data, us_metrics)
    components.append(funding_component)
    
    # Calculate weighted score
    total_score = sum(c.score * c.weight for c in components)
    total_score = round(total_score, 1)
    
    # Determine regime
    regime = determine_regime(total_score, components)
    
    # Determine signal direction
    signal_direction = determine_signal_direction(total_score)
    
    # Generate trading implications
    implications = generate_trading_implications(total_score, regime, components)
    
    # Check for critical alerts
    critical_components = [c for c in components if c.alert_level == 'critical']
    warning_components = [c for c in components if c.alert_level == 'warning']
    
    # Overall alert status
    if len(critical_components) >= 1:
        alert_status = 'CRITICAL'
        alert_color = '#ef4444'
    elif len(warning_components) >= 2:
        alert_status = 'ELEVATED'
        alert_color = '#f97316'
    elif len(warning_components) >= 1:
        alert_status = 'CAUTION'
        alert_color = '#eab308'
    else:
        alert_status = 'NORMAL'
        alert_color = '#22c55e'
    
    # Build response
    return {
        'score': total_score,
        'score_normalized': (total_score + 100) / 200,  # 0 to 1
        
        'regime': {
            'code': regime.value,
            'name': regime.name.replace('_', ' ').title(),
            'description': get_regime_description(regime),
            'color': get_regime_color(regime)
        },
        
        'signal': {
            'direction': signal_direction.value,
            'name': signal_direction.name.replace('_', ' ').title(),
            'color': get_signal_color(signal_direction)
        },
        
        'components': [
            {
                'name': c.name,
                'score': round(c.score, 1),
                'weight': c.weight,
                'weighted_score': round(c.score * c.weight, 1),
                'raw_value': c.raw_value,
                'description': c.description,
                'alert_level': c.alert_level,
                'threshold_breached': c.threshold_breached
            }
            for c in components
        ],
        
        'alert_status': {
            'status': alert_status,
            'color': alert_color,
            'critical_count': len(critical_components),
            'warning_count': len(warning_components),
            'critical_components': [c.name for c in critical_components],
            'warning_components': [c.name for c in warning_components]
        },
        
        'implications': implications,
        
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'version': '2.0'
        }
    }


def determine_regime(score: float, components: List[SignalComponent]) -> RefinancingRegime:
    """Determine market regime based on score and component analysis."""
    
    # Check for crisis conditions
    funding_stress = next((c for c in components if c.name == "Funding Stress"), None)
    auction_demand = next((c for c in components if c.name == "Auction Demand"), None)
    
    if funding_stress and funding_stress.alert_level == 'critical':
        return RefinancingRegime.FUNDING_CRISIS
    
    if auction_demand and auction_demand.score <= -50 and funding_stress and funding_stress.score <= -20:
        return RefinancingRegime.SUPPLY_STRESS
    
    # Score-based regime
    if score >= 40:
        return RefinancingRegime.LIQUIDITY_SURPLUS
    elif score >= 10:
        return RefinancingRegime.HEALTHY_ABSORPTION
    elif score >= -20:
        return RefinancingRegime.MILD_PRESSURE
    elif score >= -50:
        return RefinancingRegime.SUPPLY_STRESS
    else:
        return RefinancingRegime.FUNDING_CRISIS


def determine_signal_direction(score: float) -> SignalDirection:
    """Determine trading signal direction."""
    if score >= 40:
        return SignalDirection.STRONG_BULLISH
    elif score >= 15:
        return SignalDirection.BULLISH
    elif score >= -15:
        return SignalDirection.NEUTRAL
    elif score >= -40:
        return SignalDirection.BEARISH
    else:
        return SignalDirection.STRONG_BEARISH


def get_regime_description(regime: RefinancingRegime) -> str:
    """Get human-readable regime description."""
    descriptions = {
        RefinancingRegime.LIQUIDITY_SURPLUS: 
            "Excess liquidity in system. TGA draining, strong auction demand, yields likely to fall or stay low.",
        RefinancingRegime.HEALTHY_ABSORPTION:
            "Normal Treasury refinancing conditions. Auctions well-absorbed, stable yield environment.",
        RefinancingRegime.MILD_PRESSURE:
            "Some supply pressure. Dealers absorbing more, yields drifting higher. Monitor for escalation.",
        RefinancingRegime.SUPPLY_STRESS:
            "Significant supply/demand imbalance. Weak auction demand, rising yields, risk-off environment.",
        RefinancingRegime.FUNDING_CRISIS:
            "Severe funding stress. Fed intervention likely. Risk-off, flight to quality dynamics."
    }
    return descriptions.get(regime, "Unknown regime")


def get_regime_color(regime: RefinancingRegime) -> str:
    """Get regime color for UI."""
    colors = {
        RefinancingRegime.LIQUIDITY_SURPLUS: '#22c55e',
        RefinancingRegime.HEALTHY_ABSORPTION: '#84cc16',
        RefinancingRegime.MILD_PRESSURE: '#eab308',
        RefinancingRegime.SUPPLY_STRESS: '#f97316',
        RefinancingRegime.FUNDING_CRISIS: '#ef4444'
    }
    return colors.get(regime, '#6b7280')


def get_signal_color(signal: SignalDirection) -> str:
    """Get signal color for UI."""
    colors = {
        SignalDirection.STRONG_BULLISH: '#22c55e',
        SignalDirection.BULLISH: '#84cc16',
        SignalDirection.NEUTRAL: '#6b7280',
        SignalDirection.BEARISH: '#f97316',
        SignalDirection.STRONG_BEARISH: '#ef4444'
    }
    return colors.get(signal, '#6b7280')


def generate_trading_implications(
    score: float, 
    regime: RefinancingRegime, 
    components: List[SignalComponent]
) -> Dict:
    """Generate trading implications based on signal."""
    
    implications = {
        'duration': '',
        'curve': '',
        'credit': '',
        'equity': '',
        'fx': '',
        'key_risks': [],
        'opportunities': []
    }
    
    # Duration implications
    if score >= 30:
        implications['duration'] = "Long duration favored. Yields likely to fall or stay suppressed."
        implications['opportunities'].append("Long 10Y/30Y Treasuries")
    elif score >= 0:
        implications['duration'] = "Neutral duration. Carry attractive but limited directional edge."
        implications['opportunities'].append("Roll-down trades in belly of curve")
    elif score >= -30:
        implications['duration'] = "Short duration bias. Yields may drift higher."
        implications['opportunities'].append("Underweight long-end duration")
    else:
        implications['duration'] = "Defensive positioning. Significant yield pressure risk."
        implications['opportunities'].append("Short duration, T-bill barbell")
    
    # Curve implications
    tga_component = next((c for c in components if c.name == "TGA Dynamics"), None)
    auction_component = next((c for c in components if c.name == "Auction Demand"), None)
    
    if auction_component and auction_component.score < 0 and tga_component and tga_component.score < 0:
        implications['curve'] = "Steepening pressure. Long-end under supply pressure."
        implications['opportunities'].append("2s10s steepener")
    elif score >= 20:
        implications['curve'] = "Flattening bias. Risk-on environment favors belly."
        implications['opportunities'].append("5s30s flattener")
    else:
        implications['curve'] = "Neutral curve view."
    
    # Credit implications
    if regime == RefinancingRegime.FUNDING_CRISIS:
        implications['credit'] = "Risk-off. Credit spreads likely to widen. Reduce HY exposure."
        implications['key_risks'].append("Credit spread widening")
    elif regime == RefinancingRegime.SUPPLY_STRESS:
        implications['credit'] = "Caution on credit. IG preferred over HY."
        implications['key_risks'].append("Potential spread volatility")
    elif regime == RefinancingRegime.LIQUIDITY_SURPLUS:
        implications['credit'] = "Credit supportive. Spreads likely to compress."
        implications['opportunities'].append("Overweight IG credit")
    else:
        implications['credit'] = "Neutral credit environment."
    
    # Equity implications
    if score >= 30:
        implications['equity'] = "Supportive for equities. Liquidity tailwind."
    elif score <= -30:
        implications['equity'] = "Headwind for equities. Liquidity drag and higher discount rates."
        implications['key_risks'].append("Equity multiple compression")
    else:
        implications['equity'] = "Neutral equity impact from Treasury dynamics."
    
    # FX implications
    funding_component = next((c for c in components if c.name == "Funding Stress"), None)
    if funding_component and funding_component.score <= -30:
        implications['fx'] = "USD strength on funding stress. Safe-haven flows."
    elif auction_component and auction_component.score <= -30:
        implications['fx'] = "Watch for USD weakness if foreign demand continues to fade."
        implications['key_risks'].append("Foreign demand deterioration pressuring USD")
    else:
        implications['fx'] = "Neutral USD impact."
    
    # Key risks based on components
    for c in components:
        if c.alert_level == 'critical':
            implications['key_risks'].append(f"CRITICAL: {c.description}")
        elif c.alert_level == 'warning':
            implications['key_risks'].append(f"WARNING: {c.description}")
    
    return implications


# ==============================================================================
# INTEGRATION FUNCTION FOR DATA_PIPELINE.PY
# ==============================================================================

def get_refinancing_signal_for_pipeline(
    auction_demand_data: Dict,
    us_system_metrics: Dict,
    repo_stress_data: Dict
) -> Dict:
    """
    Simplified function for integration with data_pipeline.py.
    
    Call this from your main data pipeline with the required inputs.
    
    Example:
    --------
    refinancing_signal = get_refinancing_signal_for_pipeline(
        auction_demand_data=get_auction_demand_for_pipeline(),
        us_system_metrics=us_metrics,  # From calculate_us_system_metrics()
        repo_stress_data=repo_stress   # From repo_stress section
    )
    """
    
    # Extract US metrics in expected format
    us_metrics = {
        'tga_usd': us_system_metrics.get('tga_usd', 0.5),
        'tga_delta_4w': us_system_metrics.get('tga_delta_4w', 0),
        'tga_delta_13w': us_system_metrics.get('tga_delta_13w', 0),
        'tga_zscore': us_system_metrics.get('tga_zscore', 0),
        'netliq_delta_4w': us_system_metrics.get('netliq_delta_4w', 0),
        'netliq_delta_13w': us_system_metrics.get('netliq_delta_13w', 0),
    }
    
    # Extract repo data
    repo_data = {
        'sofr': repo_stress_data.get('sofr', 5.3),
        'iorb': repo_stress_data.get('iorb', 5.4),
        'srf_usage': repo_stress_data.get('srf_usage', 0),
    }
    
    try:
        signal = calculate_refinancing_impact_signal(
            auction_demand=auction_demand_data,
            us_metrics=us_metrics,
            repo_data=repo_data
        )
        return signal
    except Exception as e:
        print(f"Error calculating refinancing signal: {e}")
        return {
            'score': 0,
            'regime': {'code': 'error', 'name': 'Error', 'color': '#6b7280'},
            'signal': {'direction': 'neutral', 'name': 'Error', 'color': '#6b7280'},
            'components': [],
            'alert_status': {'status': 'ERROR'},
            'implications': {},
            'metadata': {'timestamp': datetime.now().isoformat(), 'error': str(e)}
        }


# Legacy wrapper for backwards compatibility
def get_treasury_refinancing_signal(
    auction_data: Dict = None,
    fred_data: Dict = None,
    sofr_data: Dict = None,
    silent: bool = True
) -> Dict:
    """
    Legacy wrapper for backwards compatibility with existing data_pipeline.py integration.
    Converts old-format inputs to new format.
    """
    # Convert fred_data format to us_metrics format
    us_metrics = {}
    
    if fred_data:
        # Extract TGA values
        tga_values = fred_data.get('WTREGEN', {}).get('values', [])
        if tga_values and len(tga_values) >= 13:
            current_tga = tga_values[-1] if tga_values[-1] else 0
            tga_13w_ago = tga_values[-13] if len(tga_values) >= 13 and tga_values[-13] else current_tga
            tga_4w_ago = tga_values[-4] if len(tga_values) >= 4 and tga_values[-4] else current_tga
            
            # Convert to trillions (values are in billions)
            us_metrics['tga_usd'] = current_tga / 1000 if current_tga else 0.5
            us_metrics['tga_delta_13w'] = (current_tga - tga_13w_ago) / 1000
            us_metrics['tga_delta_4w'] = (current_tga - tga_4w_ago) / 1000
            
            # Calculate z-score
            if len(tga_values) >= 52:
                valid_values = [v for v in tga_values[-52:] if v is not None]
                if valid_values:
                    tga_mean = np.mean(valid_values)
                    tga_std = np.std(valid_values)
                    us_metrics['tga_zscore'] = (current_tga - tga_mean) / tga_std if tga_std > 0 else 0
        
        # Calculate net liquidity delta
        walcl = fred_data.get('WALCL', {}).get('values', [])
        tga = fred_data.get('WTREGEN', {}).get('values', [])
        rrp = fred_data.get('RRPONTSYD', {}).get('values', [])
        
        if walcl and tga:
            min_len = min(len(walcl), len(tga), len(rrp) if rrp else len(walcl))
            if min_len >= 13:
                def safe_val(arr, idx):
                    return arr[idx] if idx < len(arr) and arr[idx] is not None else 0
                
                netliq_current = safe_val(walcl, -1) - safe_val(tga, -1) - safe_val(rrp, -1)
                netliq_13w = safe_val(walcl, -13) - safe_val(tga, -13) - safe_val(rrp, -13)
                netliq_4w = safe_val(walcl, -4) - safe_val(tga, -4) - safe_val(rrp, -4)
                
                us_metrics['netliq_delta_13w'] = (netliq_current - netliq_13w) / 1000
                us_metrics['netliq_delta_4w'] = (netliq_current - netliq_4w) / 1000
    
    # Convert sofr_data format
    repo_data = {}
    if sofr_data:
        sofr_values = sofr_data.get('SOFR', {}).get('values', [])
        iorb_values = sofr_data.get('IORB', {}).get('values', [])
        
        if sofr_values:
            repo_data['sofr'] = sofr_values[-1] if sofr_values[-1] else 5.3
        if iorb_values:
            repo_data['iorb'] = iorb_values[-1] if iorb_values[-1] else 5.4
        repo_data['srf_usage'] = 0
    
    # Call the main calculator
    try:
        return calculate_refinancing_impact_signal(
            auction_demand=auction_data or {},
            us_metrics=us_metrics,
            repo_data=repo_data
        )
    except Exception as e:
        if not silent:
            print(f"Error calculating refinancing signal: {e}")
        return {
            'score': 0,
            'regime': {'code': 'error', 'name': 'Error', 'description': str(e), 'color': '#6b7280'},
            'signal': {'direction': 'neutral', 'name': 'Error', 'color': '#6b7280'},
            'components': [],
            'alert_status': {'status': 'ERROR', 'color': '#6b7280'},
            'implications': {},
            'metadata': {'timestamp': datetime.now().isoformat(), 'error': str(e)}
        }


# ==============================================================================
# MAIN (for testing)
# ==============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("TREASURY REFINANCING IMPACT SIGNAL v2.0")
    print("=" * 80)
    
    # Test with sample data
    sample_auction_demand = {
        'score': 10.4,
        'signal': 'SOLID_DEMAND',
        'alerts': {
            'status': 'ELEVATED',
            'counts': {'critical': 1, 'warning': 2, 'caution': 1}
        }
    }
    
    sample_us_metrics = {
        'tga_usd': 0.72,           # $720B
        'tga_delta_4w': 0.05,      # +$50B
        'tga_delta_13w': 0.12,     # +$120B (building)
        'tga_zscore': 0.8,
        'netliq_delta_4w': -0.08,  # -$80B
        'netliq_delta_13w': -0.18, # -$180B (draining)
    }
    
    sample_repo_data = {
        'sofr': 5.35,
        'iorb': 5.40,
        'srf_usage': 0,
    }
    
    signal = calculate_refinancing_impact_signal(
        auction_demand=sample_auction_demand,
        us_metrics=sample_us_metrics,
        repo_data=sample_repo_data
    )
    
    print(f"\n📊 OVERALL SCORE: {signal['score']}")
    print(f"📈 REGIME: {signal['regime']['name']}")
    print(f"🎯 SIGNAL: {signal['signal']['name']}")
    print(f"⚠️  ALERT STATUS: {signal['alert_status']['status']}")
    
    print("\n" + "-" * 80)
    print("COMPONENTS:")
    print("-" * 80)
    for comp in signal['components']:
        alert_icon = {'critical': '🔴', 'warning': '🟠', 'caution': '🟡', 'normal': '🟢'}
        icon = alert_icon.get(comp['alert_level'], '⚪')
        print(f"  {icon} {comp['name']}: {comp['score']:+.1f} (weight: {comp['weight']:.0%}) → {comp['weighted_score']:+.1f}")
        print(f"     {comp['description']}")
    
    print("\n" + "-" * 80)
    print("TRADING IMPLICATIONS:")
    print("-" * 80)
    impl = signal['implications']
    print(f"  Duration: {impl['duration']}")
    print(f"  Curve: {impl['curve']}")
    print(f"  Credit: {impl['credit']}")
    print(f"  Equity: {impl['equity']}")
    print(f"  FX: {impl['fx']}")
    
    if impl['key_risks']:
        print(f"\n  ⚠️ Key Risks:")
        for risk in impl['key_risks']:
            print(f"     - {risk}")
    
    if impl['opportunities']:
        print(f"\n  💡 Opportunities:")
        for opp in impl['opportunities']:
            print(f"     - {opp}")
    
    print("\n✅ Module ready for integration")
