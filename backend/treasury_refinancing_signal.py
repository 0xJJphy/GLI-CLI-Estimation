"""
Treasury Refinancing Impact Signal
===================================
A composite signal combining auction demand, TGA dynamics, net liquidity,
and funding stress to assess Treasury market refinancing conditions.

Signal Range: -100 (CRISIS) to +100 (SURPLUS)

Components:
- Auction Demand (35%): Bid-to-cover, indirect %, dealer strain
- TGA Dynamics (25%): Treasury General Account levels and flows
- Net Liquidity (20%): Fed balance sheet minus TGA minus RRP
- Funding Stress (20%): SOFR-IORB spread and SRF usage

Author: Quantitative Analysis Assistant
Date: January 2026
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Component weights (must sum to 1.0)
COMPONENT_WEIGHTS = {
    'auction_demand': 0.35,
    'tga_dynamics': 0.25,
    'net_liquidity': 0.20,
    'funding_stress': 0.20,
}

# Regime thresholds
REGIME_THRESHOLDS = {
    'LIQUIDITY_SURPLUS': 40,      # >= 40: Excess liquidity, yields falling
    'HEALTHY_ABSORPTION': 10,     # 10 to 40: Normal market functioning
    'MILD_PRESSURE': -20,         # -20 to 10: Some yield pressure
    'SUPPLY_STRESS': -50,         # -50 to -20: Significant stress
    # < -50: FUNDING_CRISIS
}

# Alert thresholds
ALERT_THRESHOLDS = {
    'dealer_bills_critical': 45,      # Bills dealer % above this = red flag
    'dealer_notes_critical': 35,      # Notes dealer % above this = red flag
    'indirect_bills_weak': 50,        # Bills indirect % below this = weak
    'indirect_notes_weak': 60,        # Notes indirect % below this = weak
    'tga_building_threshold': 150,    # TGA 13w delta > $150B = draining
    'net_liq_contracting': -200,      # Net liq 13w delta < -$200B = bad
    'sofr_stress_spread': 15,         # SOFR-IORB > 15bp = stress
}


# ==============================================================================
# COMPONENT CALCULATORS
# ==============================================================================

def calculate_auction_demand_component(auction_data: Dict) -> Tuple[float, str, List[str]]:
    """
    Calculate the auction demand component score.
    
    Inputs from treasury_auction_demand.py:
    - demand_score.overall_score: 0-100
    - demand_score.signal: STRONG_DEMAND, SOLID_DEMAND, NEUTRAL, SOFT_DEMAND, WEAK_DEMAND
    - raw_auctions: Recent auction details with dealer %, indirect %
    
    Returns:
    - Score: -50 to +50 (will be weighted)
    - Description: Human-readable summary
    - Alerts: List of alert messages
    """
    alerts = []
    
    if not auction_data or 'demand_score' not in auction_data:
        return 0, "No auction data available", ["⚠️ Auction data unavailable"]
    
    demand_score_data = auction_data.get('demand_score', {})
    overall_score = demand_score_data.get('overall_score', 50)
    signal = demand_score_data.get('signal', 'NEUTRAL')
    by_type = demand_score_data.get('by_type', {})
    
    # Convert 0-100 score to -50 to +50
    component_score = (overall_score - 50)
    
    # Analyze recent auctions for alerts
    raw_auctions = auction_data.get('raw_auctions', [])
    
    # Check for critical dealer takedown
    for auction in raw_auctions[:10]:  # Last 10 auctions
        sec_type = auction.get('security_type', '').upper()
        dealer_pct = auction.get('dealer_percentage', 0) or 0
        indirect_pct = auction.get('indirect_percentage', 0) or 0
        
        if 'BILL' in sec_type and dealer_pct > ALERT_THRESHOLDS['dealer_bills_critical']:
            alerts.append(f"🔴 Critical dealer takedown in Bills: {dealer_pct:.1f}%")
        elif 'NOTE' in sec_type and dealer_pct > ALERT_THRESHOLDS['dealer_notes_critical']:
            alerts.append(f"🔴 Critical dealer takedown in Notes: {dealer_pct:.1f}%")
        
        if 'BILL' in sec_type and indirect_pct < ALERT_THRESHOLDS['indirect_bills_weak']:
            alerts.append(f"🟠 Weak foreign demand in Bills: {indirect_pct:.1f}%")
        elif 'NOTE' in sec_type and indirect_pct < ALERT_THRESHOLDS['indirect_notes_weak']:
            alerts.append(f"🟠 Weak foreign demand in Notes: {indirect_pct:.1f}%")
    
    # Remove duplicates
    alerts = list(set(alerts))[:3]  # Max 3 alerts
    
    # Generate description
    descriptions = {
        'STRONG_DEMAND': "Strong auction demand. Foreign buyers active.",
        'SOLID_DEMAND': "Solid auction absorption. Some dealer strain.",
        'NEUTRAL': "Mixed auction signals. Watch for trend changes.",
        'SOFT_DEMAND': "Softening demand. Dealers absorbing more.",
        'WEAK_DEMAND': "Weak demand. Dealers forced to absorb supply.",
    }
    description = descriptions.get(signal, "Auction demand neutral.")
    
    return component_score, description, alerts


def calculate_tga_dynamics_component(fred_data: Dict, m2_data: Dict = None) -> Tuple[float, str, List[str]]:
    """
    Calculate TGA (Treasury General Account) dynamics component.
    
    Theory:
    - TGA rising = Treasury accumulating cash = draining liquidity
    - TGA falling = Treasury spending = injecting liquidity
    
    Inputs:
    - WTREGEN: Weekly TGA balance (from FRED)
    - 13-week delta and z-score
    
    Returns:
    - Score: -50 to +50
    - Description: Human-readable summary
    - Alerts: List of alert messages
    """
    alerts = []
    
    # Get TGA data from fred_data
    tga_data = fred_data.get('WTREGEN', {})
    tga_values = tga_data.get('values', []) if isinstance(tga_data, dict) else []
    
    if not tga_values or len(tga_values) < 13:
        return 0, "Insufficient TGA data", ["⚠️ TGA data unavailable"]
    
    # Get current and historical values
    current_tga = tga_values[-1] if tga_values else 0
    tga_13w_ago = tga_values[-13] if len(tga_values) >= 13 else current_tga
    tga_4w_ago = tga_values[-4] if len(tga_values) >= 4 else current_tga
    
    # Calculate deltas (in billions)
    delta_13w = current_tga - tga_13w_ago
    delta_4w = current_tga - tga_4w_ago
    
    # Calculate z-score (normalized deviation)
    if len(tga_values) >= 52:
        tga_mean = np.mean(tga_values[-52:])
        tga_std = np.std(tga_values[-52:])
        z_score = (current_tga - tga_mean) / tga_std if tga_std > 0 else 0
    else:
        z_score = 0
    
    # Score calculation:
    # TGA building (positive delta) = negative for liquidity
    # TGA draining (negative delta) = positive for liquidity
    
    # Normalize delta_13w to score (-50 to +50)
    # $300B drain or injection is extreme
    delta_normalized = -delta_13w / 6  # Every $6B = 1 point
    delta_score = max(-50, min(50, delta_normalized))
    
    # Adjust for z-score (high TGA level is bad even if stable)
    z_adjustment = -z_score * 5  # High z-score = penalty
    
    component_score = delta_score + z_adjustment
    component_score = max(-50, min(50, component_score))
    
    # Alerts
    if delta_13w > ALERT_THRESHOLDS['tga_building_threshold']:
        alerts.append(f"🟠 TGA building: +${delta_13w:.0f}B in 13 weeks (liquidity drain)")
    
    if z_score > 1.5:
        alerts.append(f"🟡 TGA elevated: z-score {z_score:.1f}")
    
    # Description
    if delta_13w > 100:
        description = f"TGA ${current_tga:.0f}B, building ${delta_13w:.0f}B/13w. Liquidity drain."
    elif delta_13w < -100:
        description = f"TGA ${current_tga:.0f}B, draining ${-delta_13w:.0f}B/13w. Liquidity injection."
    else:
        description = f"TGA ${current_tga:.0f}B, stable. Neutral impact."
    
    return component_score, description, alerts


def calculate_net_liquidity_component(fred_data: Dict) -> Tuple[float, str, List[str]]:
    """
    Calculate net liquidity component.
    
    Net Liquidity = Fed Balance Sheet - TGA - RRP
    
    Theory:
    - Net liquidity rising = more money in system = bullish
    - Net liquidity falling = tightening = bearish
    
    Returns:
    - Score: -50 to +50
    - Description: Human-readable summary
    - Alerts: List of alert messages
    """
    alerts = []
    
    # Get Fed balance sheet (WALCL)
    walcl = fred_data.get('WALCL', {})
    walcl_values = walcl.get('values', []) if isinstance(walcl, dict) else []
    
    # Get TGA (WTREGEN)
    tga = fred_data.get('WTREGEN', {})
    tga_values = tga.get('values', []) if isinstance(tga, dict) else []
    
    # Get RRP (RRPONTSYD)
    rrp = fred_data.get('RRPONTSYD', {})
    rrp_values = rrp.get('values', []) if isinstance(rrp, dict) else []
    
    if not walcl_values or not tga_values:
        return 0, "Insufficient data for net liquidity", ["⚠️ Net liquidity data unavailable"]
    
    # Calculate net liquidity (approximate - align dates as needed)
    # Values are in billions
    current_walcl = walcl_values[-1] if walcl_values else 0
    current_tga = tga_values[-1] if tga_values else 0
    current_rrp = rrp_values[-1] if rrp_values else 0
    
    net_liq_current = current_walcl - current_tga - current_rrp
    
    # Historical for delta
    walcl_13w = walcl_values[-13] if len(walcl_values) >= 13 else current_walcl
    tga_13w = tga_values[-13] if len(tga_values) >= 13 else current_tga
    rrp_13w = rrp_values[-13] if len(rrp_values) >= 13 else current_rrp
    
    net_liq_13w = walcl_13w - tga_13w - rrp_13w
    delta_13w = net_liq_current - net_liq_13w
    
    # 4-week delta for trend
    walcl_4w = walcl_values[-4] if len(walcl_values) >= 4 else current_walcl
    tga_4w = tga_values[-4] if len(tga_values) >= 4 else current_tga
    rrp_4w = rrp_values[-4] if len(rrp_values) >= 4 else current_rrp
    
    net_liq_4w = walcl_4w - tga_4w - rrp_4w
    delta_4w = net_liq_current - net_liq_4w
    
    # Calculate acceleration (is contraction accelerating?)
    acceleration = delta_4w * 3.25 - delta_13w  # Annualized 4w vs 13w
    
    # Score: $400B swing over 13w is extreme
    score = delta_13w / 8  # Every $8B = 1 point
    score = max(-50, min(50, score))
    
    # Alerts
    if delta_13w < ALERT_THRESHOLDS['net_liq_contracting']:
        alerts.append(f"🔴 Net liquidity contracting: ${delta_13w:.0f}B in 13 weeks")
    elif delta_13w < -100:
        alerts.append(f"🟠 Net liquidity declining: ${delta_13w:.0f}B in 13 weeks")
    
    if acceleration < -100 and delta_4w < 0:
        alerts.append(f"🟡 Liquidity contraction accelerating")
    
    # Description
    if delta_13w > 100:
        description = f"Liquidity expanding: +${delta_13w:.0f}B/13w. Risk-on."
    elif delta_13w < -100:
        description = f"Liquidity contracting: ${delta_13w:.0f}B/13w. Pressure building."
    else:
        description = f"Liquidity stable. Delta: ${delta_13w:.0f}B/13w."
    
    return score, description, alerts


def calculate_funding_stress_component(sofr_data: Dict, rates_data: Dict = None) -> Tuple[float, str, List[str]]:
    """
    Calculate funding stress component.
    
    Indicators:
    - SOFR vs IORB spread (SOFR should trade near IORB)
    - SRF usage (Standing Repo Facility - emergency borrowing)
    
    Theory:
    - SOFR > IORB = funding pressure
    - SOFR < IORB = excess liquidity
    - SRF usage = acute stress
    
    Returns:
    - Score: -50 to +50
    - Description: Human-readable summary
    - Alerts: List of alert messages
    """
    alerts = []
    
    # Get SOFR data
    sofr_values = sofr_data.get('SOFR', {}).get('values', []) if isinstance(sofr_data.get('SOFR'), dict) else []
    iorb_values = sofr_data.get('IORB', {}).get('values', []) if isinstance(sofr_data.get('IORB'), dict) else []
    
    if not sofr_values or not iorb_values:
        # Fallback: check if SOFR is in the main rates_data
        if rates_data:
            sofr_values = rates_data.get('SOFR', {}).get('values', [])
            iorb_values = rates_data.get('IORB', {}).get('values', [])
    
    if not sofr_values or not iorb_values:
        return 0, "SOFR data unavailable", ["⚠️ Funding stress data unavailable"]
    
    # Get current values
    current_sofr = sofr_values[-1] if sofr_values else 0
    current_iorb = iorb_values[-1] if iorb_values else 0
    
    # Calculate spread (in basis points)
    spread_bps = (current_sofr - current_iorb) * 100
    
    # Historical spread for trend
    sofr_4w = sofr_values[-4] if len(sofr_values) >= 4 else current_sofr
    iorb_4w = iorb_values[-4] if len(iorb_values) >= 4 else current_iorb
    spread_4w = (sofr_4w - iorb_4w) * 100
    
    spread_trend = spread_bps - spread_4w
    
    # Score calculation:
    # Spread at 0 = score of +25 (healthy)
    # Spread at +15bp = score of 0 (neutral)
    # Spread at +30bp = score of -50 (crisis)
    # Spread at -15bp = score of +50 (excess liquidity)
    
    score = 25 - (spread_bps / 0.6)  # 15bp = 25 point swing
    score = max(-50, min(50, score))
    
    # Alerts
    if spread_bps > ALERT_THRESHOLDS['sofr_stress_spread']:
        alerts.append(f"🔴 SOFR stress: +{spread_bps:.0f}bp above IORB")
    elif spread_bps > 10:
        alerts.append(f"🟠 SOFR elevated: +{spread_bps:.0f}bp above IORB")
    
    if spread_trend > 5:
        alerts.append(f"🟡 SOFR spread widening: +{spread_trend:.0f}bp in 4 weeks")
    
    # Description
    if spread_bps < -5:
        description = f"SOFR {spread_bps:.0f}bp below IORB. Excess liquidity."
    elif spread_bps > 15:
        description = f"SOFR +{spread_bps:.0f}bp above IORB. Funding stress."
    else:
        description = f"SOFR at IORB. Healthy funding conditions."
    
    return score, description, alerts


# ==============================================================================
# REGIME DETECTION
# ==============================================================================

def detect_regime(score: float) -> Dict[str, Any]:
    """
    Detect market regime based on composite score.
    
    Returns regime classification with description and implications.
    """
    if score >= REGIME_THRESHOLDS['LIQUIDITY_SURPLUS']:
        regime = 'LIQUIDITY_SURPLUS'
        emoji = '💧'
        signal = 'BULLISH'
        description = "Excess liquidity in the system. Yields likely to fall."
        implications = {
            'duration': "Overweight duration. Yields have room to fall.",
            'curve': "Bull flattening likely. Long end leads.",
            'credit': "Tighten credit spreads. Risk-on environment.",
            'equity': "Bullish for equities. Liquidity supportive.",
            'fx': "USD may weaken on looser conditions.",
        }
    elif score >= REGIME_THRESHOLDS['HEALTHY_ABSORPTION']:
        regime = 'HEALTHY_ABSORPTION'
        emoji = '✅'
        signal = 'NEUTRAL_POSITIVE'
        description = "Treasury supply being absorbed smoothly. Stable yields."
        implications = {
            'duration': "Neutral duration. Carry attractive.",
            'curve': "Range-bound curve. Collect carry.",
            'credit': "Neutral credit. Focus on quality.",
            'equity': "Modestly supportive for equities.",
            'fx': "USD neutral.",
        }
    elif score >= REGIME_THRESHOLDS['MILD_PRESSURE']:
        regime = 'MILD_PRESSURE'
        emoji = '⚡'
        signal = 'NEUTRAL'
        description = "Some yield pressure. Auction demand softening."
        implications = {
            'duration': "Neutral. Carry attractive but limited edge.",
            'curve': "Steepening pressure. 2s10s steepener.",
            'credit': "Neutral credit environment.",
            'equity': "Modest headwind for equities.",
            'fx': "USD may strengthen on higher yields.",
        }
    elif score >= REGIME_THRESHOLDS['SUPPLY_STRESS']:
        regime = 'SUPPLY_STRESS'
        emoji = '📉'
        signal = 'BEARISH'
        description = "Supply overwhelming demand. Yields rising."
        implications = {
            'duration': "Underweight duration. Yields rising.",
            'curve': "Bear steepening. Short 2s10s.",
            'credit': "Widen credit spreads. Risk-off.",
            'equity': "Headwind for equities. Higher discount rates.",
            'fx': "USD strength on higher yields and risk-off.",
        }
    else:
        regime = 'FUNDING_CRISIS'
        emoji = '🚨'
        signal = 'CRISIS'
        description = "Acute funding stress. Fed intervention likely."
        implications = {
            'duration': "Extreme caution. Volatility elevated.",
            'curve': "Curve may invert sharply then steepen on intervention.",
            'credit': "Flight to quality. Avoid credit risk.",
            'equity': "Sell equities. Risk-off.",
            'fx': "USD surge on safe-haven flows.",
        }
    
    return {
        'regime': regime,
        'emoji': emoji,
        'signal': signal,
        'description': description,
        'implications': implications,
    }


# ==============================================================================
# MAIN SIGNAL CALCULATOR
# ==============================================================================

def calculate_treasury_refinancing_signal(
    auction_data: Dict,
    fred_data: Dict,
    sofr_data: Dict = None,
    silent: bool = False
) -> Dict[str, Any]:
    """
    Calculate the composite Treasury Refinancing Impact Signal.
    
    Parameters:
    -----------
    auction_data : Dict
        Output from treasury_auction_demand.fetch_treasury_auction_demand()
    fred_data : Dict
        FRED data containing WALCL, WTREGEN, RRPONTSYD
    sofr_data : Dict
        SOFR and IORB rate data
    
    Returns:
    --------
    Dict with:
        - overall_score: -100 to +100
        - regime: Current regime classification
        - components: Breakdown of each component
        - alerts: Active alerts
        - trading_implications: Recommended positioning
    """
    
    if not silent:
        print("  [Treasury Signal] Calculating refinancing impact signal...")
    
    # Calculate each component
    auction_score, auction_desc, auction_alerts = calculate_auction_demand_component(auction_data)
    tga_score, tga_desc, tga_alerts = calculate_tga_dynamics_component(fred_data)
    net_liq_score, net_liq_desc, net_liq_alerts = calculate_net_liquidity_component(fred_data)
    funding_score, funding_desc, funding_alerts = calculate_funding_stress_component(sofr_data or fred_data, fred_data)
    
    # Calculate weighted composite score
    weighted_auction = auction_score * COMPONENT_WEIGHTS['auction_demand']
    weighted_tga = tga_score * COMPONENT_WEIGHTS['tga_dynamics']
    weighted_net_liq = net_liq_score * COMPONENT_WEIGHTS['net_liquidity']
    weighted_funding = funding_score * COMPONENT_WEIGHTS['funding_stress']
    
    overall_score = weighted_auction + weighted_tga + weighted_net_liq + weighted_funding
    
    # Scale to -100 to +100 range (components are -50 to +50)
    overall_score = overall_score * 2
    overall_score = max(-100, min(100, overall_score))
    
    # Detect regime
    regime_data = detect_regime(overall_score)
    
    # Aggregate alerts
    all_alerts = auction_alerts + tga_alerts + net_liq_alerts + funding_alerts
    
    # Determine alert status
    red_alerts = sum(1 for a in all_alerts if '🔴' in a)
    orange_alerts = sum(1 for a in all_alerts if '🟠' in a)
    
    if red_alerts >= 2:
        alert_status = 'CRITICAL'
    elif red_alerts >= 1 or orange_alerts >= 2:
        alert_status = 'WARNING'
    elif orange_alerts >= 1 or len(all_alerts) > 0:
        alert_status = 'CAUTION'
    else:
        alert_status = 'CLEAR'
    
    # Build component breakdown
    components = {
        'auction_demand': {
            'raw_score': round(auction_score, 1),
            'weight': COMPONENT_WEIGHTS['auction_demand'],
            'weighted_score': round(weighted_auction, 2),
            'description': auction_desc,
            'status': 'positive' if auction_score > 10 else 'negative' if auction_score < -10 else 'neutral',
        },
        'tga_dynamics': {
            'raw_score': round(tga_score, 1),
            'weight': COMPONENT_WEIGHTS['tga_dynamics'],
            'weighted_score': round(weighted_tga, 2),
            'description': tga_desc,
            'status': 'positive' if tga_score > 10 else 'negative' if tga_score < -10 else 'neutral',
        },
        'net_liquidity': {
            'raw_score': round(net_liq_score, 1),
            'weight': COMPONENT_WEIGHTS['net_liquidity'],
            'weighted_score': round(weighted_net_liq, 2),
            'description': net_liq_desc,
            'status': 'positive' if net_liq_score > 10 else 'negative' if net_liq_score < -10 else 'neutral',
        },
        'funding_stress': {
            'raw_score': round(funding_score, 1),
            'weight': COMPONENT_WEIGHTS['funding_stress'],
            'weighted_score': round(weighted_funding, 2),
            'description': funding_desc,
            'status': 'positive' if funding_score > 10 else 'negative' if funding_score < -10 else 'neutral',
        },
    }
    
    result = {
        'overall_score': round(overall_score, 1),
        'regime': regime_data['regime'],
        'regime_emoji': regime_data['emoji'],
        'regime_signal': regime_data['signal'],
        'regime_description': regime_data['description'],
        'components': components,
        'alerts': all_alerts,
        'alert_status': alert_status,
        'trading_implications': regime_data['implications'],
        'last_updated': datetime.now().isoformat(),
    }
    
    if not silent:
        print(f"  [Treasury Signal] Score: {overall_score:.1f} | Regime: {regime_data['regime']} | Alerts: {len(all_alerts)}")
    
    return result


# ==============================================================================
# CONVENIENCE FUNCTION FOR DATA PIPELINE
# ==============================================================================

def get_treasury_refinancing_signal(
    auction_data: Dict = None,
    fred_data: Dict = None,
    sofr_data: Dict = None,
    silent: bool = True
) -> Dict[str, Any]:
    """
    Convenience wrapper for data pipeline integration.
    
    Returns empty structure if insufficient data.
    """
    if not auction_data and not fred_data:
        return {
            'overall_score': 0,
            'regime': 'UNKNOWN',
            'regime_emoji': '❓',
            'regime_signal': 'UNKNOWN',
            'regime_description': 'Insufficient data to calculate signal.',
            'components': {},
            'alerts': ['⚠️ Insufficient data for signal calculation'],
            'alert_status': 'UNKNOWN',
            'trading_implications': {},
            'last_updated': datetime.now().isoformat(),
        }
    
    return calculate_treasury_refinancing_signal(
        auction_data=auction_data or {},
        fred_data=fred_data or {},
        sofr_data=sofr_data,
        silent=silent
    )


if __name__ == "__main__":
    # Test with mock data
    print("Treasury Refinancing Signal Module loaded successfully.")
    print(f"Component weights: {COMPONENT_WEIGHTS}")
    print(f"Regime thresholds: {REGIME_THRESHOLDS}")
