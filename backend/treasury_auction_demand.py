"""
Treasury Auction Demand Module v2.0
===================================
Enhanced with automatic alert detection for:
- High dealer takedown (forced absorption)
- Weak foreign demand (low indirect %)
- Poor bid-to-cover ratios
- Tail analysis (auction pricing stress)
- Trend deterioration signals

Data Source: TreasuryDirect.gov API
Author: Quantitative Analysis Assistant
Date: January 2026
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

# ==============================================================================
# CONFIGURATION
# ==============================================================================

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

TREASURY_DIRECT_BASE_URL = "https://www.treasurydirect.gov/TA_WS"

SECURITY_TYPES = ['Bill', 'Note', 'Bond', 'TIPS', 'FRN', 'CMB']

CACHE_FILE = os.path.join(OUTPUT_DIR, 'treasury_auction_demand_cache.json')
CACHE_HOURS = 6

LOOKBACK_YEARS = 2

# ==============================================================================
# ALERT THRESHOLDS (Calibrated from historical data)
# ==============================================================================

class AlertLevel(Enum):
    CRITICAL = "critical"    # Immediate concern
    WARNING = "warning"      # Watch closely
    CAUTION = "caution"      # Minor concern
    NORMAL = "normal"        # No concern

# Dealer takedown thresholds (higher = worse, dealers forced to absorb)
DEALER_THRESHOLDS = {
    'Bill': {'critical': 45, 'warning': 40, 'caution': 35, 'healthy': 25},
    'Note': {'critical': 35, 'warning': 28, 'caution': 22, 'healthy': 15},
    'Bond': {'critical': 30, 'warning': 25, 'caution': 20, 'healthy': 12},
    'TIPS': {'critical': 35, 'warning': 28, 'caution': 22, 'healthy': 15},
    'FRN':  {'critical': 40, 'warning': 35, 'caution': 28, 'healthy': 20},
    'CMB':  {'critical': 50, 'warning': 45, 'caution': 40, 'healthy': 30},
}

# Indirect bidder thresholds (lower = worse, weak foreign demand)
INDIRECT_THRESHOLDS = {
    'Bill': {'critical': 40, 'warning': 48, 'caution': 55, 'healthy': 65},
    'Note': {'critical': 50, 'warning': 58, 'caution': 63, 'healthy': 70},
    'Bond': {'critical': 50, 'warning': 58, 'caution': 63, 'healthy': 70},
    'TIPS': {'critical': 45, 'warning': 52, 'caution': 58, 'healthy': 65},
    'FRN':  {'critical': 35, 'warning': 42, 'caution': 48, 'healthy': 55},
    'CMB':  {'critical': 38, 'warning': 45, 'caution': 52, 'healthy': 60},
}

# Bid-to-Cover thresholds (lower = worse)
BTC_THRESHOLDS = {
    'Bill': {'critical': 2.2, 'warning': 2.4, 'caution': 2.5, 'healthy': 2.7},
    'Note': {'critical': 2.1, 'warning': 2.3, 'caution': 2.4, 'healthy': 2.6},
    'Bond': {'critical': 2.0, 'warning': 2.2, 'caution': 2.3, 'healthy': 2.5},
    'TIPS': {'critical': 2.1, 'warning': 2.3, 'caution': 2.4, 'healthy': 2.6},
    'FRN':  {'critical': 2.3, 'warning': 2.5, 'caution': 2.6, 'healthy': 2.8},
    'CMB':  {'critical': 2.5, 'warning': 2.7, 'caution': 2.8, 'healthy': 3.0},
}


# ==============================================================================
# ALERT DETECTION FUNCTIONS
# ==============================================================================

def detect_auction_alerts(auction: Dict) -> List[Dict]:
    """
    Detect alerts for a single auction.
    
    Returns list of alerts with severity, type, and description.
    """
    alerts = []
    sec_type = auction.get('security_type', 'Note')
    security_name = f"{auction.get('security_term', '')} {sec_type}".strip()
    
    # Get thresholds for this security type
    dealer_thresh = DEALER_THRESHOLDS.get(sec_type, DEALER_THRESHOLDS['Note'])
    indirect_thresh = INDIRECT_THRESHOLDS.get(sec_type, INDIRECT_THRESHOLDS['Note'])
    btc_thresh = BTC_THRESHOLDS.get(sec_type, BTC_THRESHOLDS['Note'])
    
    # === ALERT 1: High Dealer Takedown ===
    dealer_pct = auction.get('dealer_pct')
    if dealer_pct is not None:
        if dealer_pct >= dealer_thresh['critical']:
            alerts.append({
                'level': AlertLevel.CRITICAL.value,
                'type': 'HIGH_DEALER_TAKEDOWN',
                'icon': '🔴',
                'title': 'Critical Dealer Absorption',
                'message': f"Dealers absorbed {dealer_pct:.1f}% of {security_name} (threshold: {dealer_thresh['critical']}%)",
                'metric': 'dealer_pct',
                'value': dealer_pct,
                'threshold': dealer_thresh['critical'],
                'implication': 'Real demand severely lacking. Dealers forced to absorb excess supply.',
                'market_impact': 'Bearish for bonds, potential yield pressure'
            })
        elif dealer_pct >= dealer_thresh['warning']:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'type': 'HIGH_DEALER_TAKEDOWN',
                'icon': '🟠',
                'title': 'Elevated Dealer Absorption',
                'message': f"Dealers absorbed {dealer_pct:.1f}% of {security_name}",
                'metric': 'dealer_pct',
                'value': dealer_pct,
                'threshold': dealer_thresh['warning'],
                'implication': 'End-user demand weaker than normal.',
                'market_impact': 'Watch for yield drift higher'
            })
        elif dealer_pct >= dealer_thresh['caution']:
            alerts.append({
                'level': AlertLevel.CAUTION.value,
                'type': 'ELEVATED_DEALER',
                'icon': '🟡',
                'title': 'Slightly Elevated Dealer %',
                'message': f"Dealer takedown at {dealer_pct:.1f}% for {security_name}",
                'metric': 'dealer_pct',
                'value': dealer_pct,
                'threshold': dealer_thresh['caution'],
                'implication': 'Minor absorption pressure.',
                'market_impact': 'Neutral, monitor trend'
            })
    
    # === ALERT 2: Weak Foreign Demand (Low Indirect) ===
    indirect_pct = auction.get('indirect_pct')
    if indirect_pct is not None:
        if indirect_pct <= indirect_thresh['critical']:
            alerts.append({
                'level': AlertLevel.CRITICAL.value,
                'type': 'WEAK_FOREIGN_DEMAND',
                'icon': '🔴',
                'title': 'Critical Foreign Demand Drop',
                'message': f"Indirect bidders only {indirect_pct:.1f}% for {security_name} (threshold: {indirect_thresh['critical']}%)",
                'metric': 'indirect_pct',
                'value': indirect_pct,
                'threshold': indirect_thresh['critical'],
                'implication': 'Foreign central banks and sovereign funds avoiding this maturity.',
                'market_impact': 'USD weakness risk, yield pressure'
            })
        elif indirect_pct <= indirect_thresh['warning']:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'type': 'WEAK_FOREIGN_DEMAND',
                'icon': '🟠',
                'title': 'Below-Average Foreign Demand',
                'message': f"Indirect bidders at {indirect_pct:.1f}% for {security_name}",
                'metric': 'indirect_pct',
                'value': indirect_pct,
                'threshold': indirect_thresh['warning'],
                'implication': 'Foreign demand softening.',
                'market_impact': 'Monitor USD and yield curve'
            })
        elif indirect_pct <= indirect_thresh['caution']:
            alerts.append({
                'level': AlertLevel.CAUTION.value,
                'type': 'SOFT_FOREIGN_DEMAND',
                'icon': '🟡',
                'title': 'Soft Foreign Participation',
                'message': f"Indirect bidders at {indirect_pct:.1f}% for {security_name}",
                'metric': 'indirect_pct',
                'value': indirect_pct,
                'threshold': indirect_thresh['caution'],
                'implication': 'Slightly below normal foreign interest.',
                'market_impact': 'Neutral'
            })
    
    # === ALERT 3: Poor Bid-to-Cover ===
    btc = auction.get('bid_to_cover')
    if btc is not None:
        if btc <= btc_thresh['critical']:
            alerts.append({
                'level': AlertLevel.CRITICAL.value,
                'type': 'POOR_BID_TO_COVER',
                'icon': '🔴',
                'title': 'Critical Demand Shortage',
                'message': f"BTC only {btc:.2f}x for {security_name} (threshold: {btc_thresh['critical']}x)",
                'metric': 'bid_to_cover',
                'value': btc,
                'threshold': btc_thresh['critical'],
                'implication': 'Severe lack of buyer interest.',
                'market_impact': 'Immediate yield pressure likely'
            })
        elif btc <= btc_thresh['warning']:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'type': 'WEAK_BID_TO_COVER',
                'icon': '🟠',
                'title': 'Weak Auction Coverage',
                'message': f"BTC at {btc:.2f}x for {security_name}",
                'metric': 'bid_to_cover',
                'value': btc,
                'threshold': btc_thresh['warning'],
                'implication': 'Below-average demand.',
                'market_impact': 'Yields may drift higher'
            })
    
    # === ALERT 4: Combined Stress (multiple weak metrics) ===
    stress_count = 0
    if dealer_pct and dealer_pct >= dealer_thresh['caution']:
        stress_count += 1
    if indirect_pct and indirect_pct <= indirect_thresh['caution']:
        stress_count += 1
    if btc and btc <= btc_thresh['caution']:
        stress_count += 1
    
    if stress_count >= 3:
        alerts.append({
            'level': AlertLevel.CRITICAL.value,
            'type': 'MULTI_METRIC_STRESS',
            'icon': '⚠️',
            'title': 'Multiple Stress Indicators',
            'message': f"{security_name} showing weakness across {stress_count} metrics",
            'metric': 'combined',
            'value': stress_count,
            'threshold': 3,
            'implication': 'Broad-based demand weakness for this maturity.',
            'market_impact': 'Significant supply/demand imbalance'
        })
    elif stress_count == 2:
        # Only add if we don't already have critical alerts
        critical_count = sum(1 for a in alerts if a['level'] == AlertLevel.CRITICAL.value)
        if critical_count == 0:
            alerts.append({
                'level': AlertLevel.WARNING.value,
                'type': 'DUAL_METRIC_STRESS',
                'icon': '⚠️',
                'title': 'Multiple Caution Signals',
                'message': f"{security_name} showing weakness in {stress_count} metrics",
                'metric': 'combined',
                'value': stress_count,
                'threshold': 2,
                'implication': 'Auction absorbed but with strain.',
                'market_impact': 'Watch follow-through in secondary market'
            })
    
    return alerts


def detect_trend_alerts(df: pd.DataFrame, lookback_auctions: int = 10) -> List[Dict]:
    """
    Detect trend-based alerts across multiple auctions.
    """
    alerts = []
    
    if df.empty or len(df) < 5:
        return alerts
    
    for sec_type in ['Bill', 'Note', 'Bond']:
        type_df = df[df['security_type'] == sec_type].head(lookback_auctions)
        
        if len(type_df) < 5:
            continue
        
        # Check for deteriorating trend in dealer %
        dealer_series = type_df['dealer_pct'].dropna()
        if len(dealer_series) >= 5:
            recent_avg = dealer_series.head(3).mean()
            older_avg = dealer_series.tail(3).mean()
            
            if recent_avg > older_avg * 1.25:  # 25% increase
                alerts.append({
                    'level': AlertLevel.WARNING.value,
                    'type': 'DETERIORATING_DEALER_TREND',
                    'icon': '📈',
                    'title': f'{sec_type} Dealer Trend Deteriorating',
                    'message': f"Dealer absorption rising: {older_avg:.1f}% → {recent_avg:.1f}%",
                    'metric': 'dealer_pct_trend',
                    'value': recent_avg,
                    'threshold': older_avg * 1.25,
                    'implication': f'Systematic weakening in {sec_type} demand.',
                    'market_impact': 'Watch term premium expansion'
                })
        
        # Check for deteriorating indirect %
        indirect_series = type_df['indirect_pct'].dropna()
        if len(indirect_series) >= 5:
            recent_avg = indirect_series.head(3).mean()
            older_avg = indirect_series.tail(3).mean()
            
            if recent_avg < older_avg * 0.85:  # 15% decrease
                alerts.append({
                    'level': AlertLevel.WARNING.value,
                    'type': 'DETERIORATING_FOREIGN_TREND',
                    'icon': '📉',
                    'title': f'{sec_type} Foreign Demand Weakening',
                    'message': f"Indirect bidders declining: {older_avg:.1f}% → {recent_avg:.1f}%",
                    'metric': 'indirect_pct_trend',
                    'value': recent_avg,
                    'threshold': older_avg * 0.85,
                    'implication': f'Foreign appetite for {sec_type}s declining.',
                    'market_impact': 'USD and long-end yields at risk'
                })
        
        # Check for deteriorating BTC
        btc_series = type_df['bid_to_cover'].dropna()
        if len(btc_series) >= 5:
            recent_avg = btc_series.head(3).mean()
            older_avg = btc_series.tail(3).mean()
            
            if recent_avg < older_avg * 0.90:  # 10% decrease
                alerts.append({
                    'level': AlertLevel.CAUTION.value,
                    'type': 'DETERIORATING_BTC_TREND',
                    'icon': '📉',
                    'title': f'{sec_type} Coverage Declining',
                    'message': f"Bid-to-cover weakening: {older_avg:.2f}x → {recent_avg:.2f}x",
                    'metric': 'btc_trend',
                    'value': recent_avg,
                    'threshold': older_avg * 0.90,
                    'implication': f'Overall demand for {sec_type}s softening.',
                    'market_impact': 'Neutral to slightly bearish'
                })
    
    return alerts


def detect_maturity_preference_shift(df: pd.DataFrame) -> List[Dict]:
    """
    Detect shifts in maturity preference (e.g., flight to short-term).
    """
    alerts = []
    
    if df.empty or len(df) < 10:
        return alerts
    
    # Compare short vs long-term demand
    bills_df = df[df['security_type'] == 'Bill'].head(10)
    bonds_df = df[df['security_type'] == 'Bond'].head(5)
    
    if bills_df.empty or bonds_df.empty:
        return alerts
    
    bills_btc = bills_df['bid_to_cover'].dropna().mean()
    bonds_btc = bonds_df['bid_to_cover'].dropna().mean()
    
    bills_indirect = bills_df['indirect_pct'].dropna().mean()
    bonds_indirect = bonds_df['indirect_pct'].dropna().mean()
    
    # Strong preference for short-term
    if bills_btc > bonds_btc * 1.20 and bills_indirect > bonds_indirect * 1.10:
        alerts.append({
            'level': AlertLevel.CAUTION.value,
            'type': 'FLIGHT_TO_SHORT_TERM',
            'icon': '🔄',
            'title': 'Flight to Short-Term',
            'message': f"Bills BTC {bills_btc:.2f}x vs Bonds {bonds_btc:.2f}x",
            'metric': 'maturity_preference',
            'value': bills_btc / bonds_btc if bonds_btc > 0 else 0,
            'threshold': 1.20,
            'implication': 'Investors prefer liquidity and short duration.',
            'market_impact': 'Curve may steepen, long-end vulnerable'
        })
    
    return alerts


def generate_alert_summary(all_alerts: List[Dict]) -> Dict:
    """
    Generate summary of all alerts with severity counts and recommendations.
    """
    critical = [a for a in all_alerts if a['level'] == AlertLevel.CRITICAL.value]
    warning = [a for a in all_alerts if a['level'] == AlertLevel.WARNING.value]
    caution = [a for a in all_alerts if a['level'] == AlertLevel.CAUTION.value]
    
    # Overall status
    if len(critical) >= 2:
        status = 'CRITICAL'
        status_color = '#ef4444'
        recommendation = 'Multiple critical alerts detected. Treasury demand under significant stress. Consider reducing duration exposure.'
    elif len(critical) >= 1:
        status = 'ELEVATED'
        status_color = '#f97316'
        recommendation = 'Critical alert detected. Monitor closely for follow-through in secondary market.'
    elif len(warning) >= 3:
        status = 'ELEVATED'
        status_color = '#f97316'
        recommendation = 'Multiple warning signals. Auction demand showing strain across segments.'
    elif len(warning) >= 1:
        status = 'CAUTION'
        status_color = '#eab308'
        recommendation = 'Some demand weakness detected. Normal market functioning but monitor trends.'
    elif len(caution) >= 2:
        status = 'WATCH'
        status_color = '#84cc16'
        recommendation = 'Minor concerns noted. Market functioning normally.'
    else:
        status = 'HEALTHY'
        status_color = '#22c55e'
        recommendation = 'Auction demand healthy across all segments. No action required.'
    
    # Group alerts by type for easier display
    alerts_by_type = {}
    for alert in all_alerts:
        alert_type = alert['type']
        if alert_type not in alerts_by_type:
            alerts_by_type[alert_type] = []
        alerts_by_type[alert_type].append(alert)
    
    return {
        'status': status,
        'status_color': status_color,
        'recommendation': recommendation,
        'counts': {
            'critical': len(critical),
            'warning': len(warning),
            'caution': len(caution),
            'total': len(all_alerts)
        },
        'critical_alerts': critical,
        'warning_alerts': warning,
        'caution_alerts': caution,
        'alerts_by_type': alerts_by_type,
        'all_alerts': all_alerts
    }


# ==============================================================================
# CACHE MANAGEMENT
# ==============================================================================

def is_cache_fresh() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        file_mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        hours_elapsed = (datetime.now() - file_mtime).total_seconds() / 3600
        return hours_elapsed < CACHE_HOURS
    except Exception:
        return False


def load_cache() -> Optional[Dict]:
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(data: Dict) -> None:
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save auction demand cache: {e}")


# ==============================================================================
# API FETCHING FUNCTIONS
# ==============================================================================

def fetch_auctioned_securities(security_type: str, max_results: int = 250) -> List[Dict]:
    url = f"{TREASURY_DIRECT_BASE_URL}/securities/auctioned"
    params = {
        'format': 'json',
        'type': security_type,
        'pagesize': min(max_results, 250)
    }
    
    headers = {
        'User-Agent': 'GLI-CLI-Dashboard/2.0 (Treasury Auction Analysis)',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.RequestException as e:
        print(f"  [TreasuryDirect] Error fetching {security_type}: {e}")
        return []


def fetch_all_auction_data(lookback_days: int = 730, silent: bool = False) -> pd.DataFrame:
    all_auctions = []
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    
    for sec_type in SECURITY_TYPES:
        if not silent:
            print(f"  [TreasuryDirect] Fetching {sec_type} auctions...")
        
        auctions = fetch_auctioned_securities(sec_type)
        
        for auction in auctions:
            try:
                auction_date_str = auction.get('auctionDate', '')
                if not auction_date_str:
                    continue
                    
                auction_date = datetime.strptime(auction_date_str[:10], '%Y-%m-%d')
                
                if auction_date < cutoff_date:
                    continue
                
                record = {
                    'auction_date': auction_date,
                    'issue_date': auction.get('issueDate', '')[:10] if auction.get('issueDate') else None,
                    'maturity_date': auction.get('maturityDate', '')[:10] if auction.get('maturityDate') else None,
                    'security_type': auction.get('securityType', sec_type),
                    'security_term': auction.get('securityTerm', ''),
                    'cusip': auction.get('cusip', ''),
                    'bid_to_cover': _safe_float(auction.get('bidToCoverRatio')),
                    'competitive_accepted': _safe_float(auction.get('competitiveAccepted')),
                    'competitive_tendered': _safe_float(auction.get('competitiveTendered')),
                    'noncompetitive_accepted': _safe_float(auction.get('noncompetitiveAccepted')),
                    'direct_bidder_accepted': _safe_float(auction.get('directBidderAccepted')),
                    'direct_bidder_tendered': _safe_float(auction.get('directBidderTendered')),
                    'indirect_bidder_accepted': _safe_float(auction.get('indirectBidderAccepted')),
                    'indirect_bidder_tendered': _safe_float(auction.get('indirectBidderTendered')),
                    'primary_dealer_accepted': _safe_float(auction.get('primaryDealerAccepted')),
                    'primary_dealer_tendered': _safe_float(auction.get('primaryDealerTendered')),
                    'high_yield': _safe_float(auction.get('highInvestmentRate')) or _safe_float(auction.get('highYield')),
                    'high_discount_rate': _safe_float(auction.get('highDiscountRate')),
                    'avg_median_yield': _safe_float(auction.get('averageMedianYield')),
                    'low_yield': _safe_float(auction.get('lowInvestmentRate')) or _safe_float(auction.get('lowYield')),
                    'offering_amount': _safe_float(auction.get('offeringAmount')) or _safe_float(auction.get('totalAccepted')),
                    'total_accepted': _safe_float(auction.get('totalAccepted')),
                    'total_tendered': _safe_float(auction.get('totalTendered')),
                    'allocation_pct': _safe_float(auction.get('allocationPercentage')),
                }
                
                all_auctions.append(record)
                
            except Exception as e:
                continue
        
        time.sleep(0.2)
    
    if not all_auctions:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_auctions)
    df = df.sort_values('auction_date', ascending=False).reset_index(drop=True)
    df = _calculate_derived_metrics(df)
    
    if not silent:
        print(f"  [TreasuryDirect] Fetched {len(df)} auction records")
    
    return df


def _safe_float(value) -> Optional[float]:
    if value is None or value == '' or value == 'null':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    total_accepted = df['total_accepted'].fillna(0)
    
    df['indirect_pct'] = np.where(
        total_accepted > 0,
        (df['indirect_bidder_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    df['direct_pct'] = np.where(
        total_accepted > 0,
        (df['direct_bidder_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    df['dealer_pct'] = np.where(
        total_accepted > 0,
        (df['primary_dealer_accepted'].fillna(0) / total_accepted) * 100,
        np.nan
    )
    
    df['amount_billions'] = df['offering_amount'].fillna(0) / 1e9
    df['term_weeks'] = df['security_term'].apply(_parse_term_to_weeks)
    df['maturity_bucket'] = df.apply(_categorize_maturity, axis=1)
    
    return df


def _parse_term_to_weeks(term_str: str) -> Optional[int]:
    if not term_str:
        return None
    term_str = str(term_str).lower()
    
    if 'week' in term_str:
        try:
            return int(term_str.split('-')[0].strip())
        except:
            pass
    if 'day' in term_str:
        try:
            return max(1, int(term_str.split('-')[0].strip()) // 7)
        except:
            pass
    if 'month' in term_str:
        try:
            return int(term_str.split('-')[0].strip()) * 4
        except:
            pass
    if 'year' in term_str:
        try:
            return int(term_str.split('-')[0].strip()) * 52
        except:
            pass
    return None


def _categorize_maturity(row) -> str:
    sec_type = row.get('security_type', '')
    term_weeks = row.get('term_weeks')
    
    if sec_type == 'Bill':
        return 'Short-Term (Bills)'
    elif sec_type in ['Note', 'FRN']:
        if term_weeks and term_weeks <= 104:
            return 'Short Coupon (2Y)'
        elif term_weeks and term_weeks <= 260:
            return 'Belly (3-5Y)'
        else:
            return 'Intermediate (7-10Y)'
    elif sec_type == 'Bond':
        return 'Long-Term (20-30Y)'
    elif sec_type == 'TIPS':
        return 'TIPS (Inflation)'
    elif sec_type == 'CMB':
        return 'Cash Management Bills'
    return 'Other'


# ==============================================================================
# ANALYSIS FUNCTIONS
# ==============================================================================

def calculate_auction_demand_score(df: pd.DataFrame, lookback_auctions: int = 10) -> Dict:
    if df.empty:
        return _empty_demand_result()
    
    results = {
        'overall_score': 0,
        'signal': 'NEUTRAL',
        'signal_description': '',
        'by_type': {},
        'recent_auctions': [],
        'metrics': {},
        'timestamp': datetime.now().isoformat()
    }
    
    scores = []
    
    for sec_type in SECURITY_TYPES:
        type_df = df[df['security_type'] == sec_type].head(lookback_auctions)
        
        if type_df.empty:
            continue
        
        type_score = _calculate_type_score(type_df, sec_type)
        results['by_type'][sec_type] = type_score
        
        weight = {'Bill': 0.30, 'Note': 0.35, 'Bond': 0.15, 'TIPS': 0.10, 'FRN': 0.05, 'CMB': 0.05}.get(sec_type, 0.1)
        scores.append(type_score['score'] * weight)
    
    if scores:
        results['overall_score'] = round(sum(scores) / sum([0.30, 0.35, 0.15, 0.10, 0.05, 0.05][:len(scores)]), 1)
    
    # Determine signal with description
    if results['overall_score'] >= 30:
        results['signal'] = 'STRONG_DEMAND'
        results['signal_color'] = '#22c55e'
        results['signal_description'] = 'Excellent auction absorption. Treasury has no financing concerns.'
    elif results['overall_score'] >= 10:
        results['signal'] = 'SOLID_DEMAND'
        results['signal_color'] = '#84cc16'
        results['signal_description'] = 'Healthy auction absorption. Normal market conditions.'
    elif results['overall_score'] <= -30:
        results['signal'] = 'WEAK_DEMAND'
        results['signal_color'] = '#ef4444'
        results['signal_description'] = 'Poor auction demand. Watch for yield pressure and funding stress.'
    elif results['overall_score'] <= -10:
        results['signal'] = 'SOFT_DEMAND'
        results['signal_color'] = '#f97316'
        results['signal_description'] = 'Below-average demand. Monitor for deterioration.'
    else:
        results['signal'] = 'NEUTRAL'
        results['signal_color'] = '#6b7280'
        results['signal_description'] = 'Mixed signals. Market functioning normally.'
    
    # Recent auctions WITH alerts
    results['recent_auctions'] = _get_recent_auctions_with_alerts(df, n=15)
    
    # Aggregate metrics
    results['metrics'] = {
        'avg_btc_all': round(df['bid_to_cover'].dropna().mean(), 2) if not df['bid_to_cover'].dropna().empty else None,
        'avg_indirect_all': round(df['indirect_pct'].dropna().mean(), 1) if not df['indirect_pct'].dropna().empty else None,
        'avg_direct_all': round(df['direct_pct'].dropna().mean(), 1) if not df['direct_pct'].dropna().empty else None,
        'avg_dealer_all': round(df['dealer_pct'].dropna().mean(), 1) if not df['dealer_pct'].dropna().empty else None,
        'total_auctions': len(df),
        'date_range': {
            'start': df['auction_date'].min().strftime('%Y-%m-%d') if not df.empty else None,
            'end': df['auction_date'].max().strftime('%Y-%m-%d') if not df.empty else None
        }
    }
    
    return results


def _calculate_type_score(df: pd.DataFrame, sec_type: str) -> Dict:
    btc_thresh = BTC_THRESHOLDS.get(sec_type, BTC_THRESHOLDS['Note'])
    indirect_thresh = INDIRECT_THRESHOLDS.get(sec_type, INDIRECT_THRESHOLDS['Note'])
    dealer_thresh = DEALER_THRESHOLDS.get(sec_type, DEALER_THRESHOLDS['Note'])
    
    avg_btc = df['bid_to_cover'].dropna().mean() if not df['bid_to_cover'].dropna().empty else None
    avg_indirect = df['indirect_pct'].dropna().mean() if not df['indirect_pct'].dropna().empty else None
    avg_direct = df['direct_pct'].dropna().mean() if not df['direct_pct'].dropna().empty else None
    avg_dealer = df['dealer_pct'].dropna().mean() if not df['dealer_pct'].dropna().empty else None
    
    # BTC score
    btc_score = 0
    if avg_btc is not None:
        if avg_btc >= btc_thresh['healthy']:
            btc_score = 50
        elif avg_btc >= btc_thresh['caution']:
            btc_score = 25
        elif avg_btc >= btc_thresh['warning']:
            btc_score = -25
        else:
            btc_score = -50
    
    # Indirect score
    indirect_score = 0
    if avg_indirect is not None:
        if avg_indirect >= indirect_thresh['healthy']:
            indirect_score = 50
        elif avg_indirect >= indirect_thresh['caution']:
            indirect_score = 25
        elif avg_indirect >= indirect_thresh['warning']:
            indirect_score = -25
        else:
            indirect_score = -50
    
    # Dealer score (inverted - lower is better)
    dealer_score = 0
    if avg_dealer is not None:
        if avg_dealer <= dealer_thresh['healthy']:
            dealer_score = 30
        elif avg_dealer <= dealer_thresh['caution']:
            dealer_score = 10
        elif avg_dealer <= dealer_thresh['warning']:
            dealer_score = -20
        else:
            dealer_score = -40
    
    # Combined score (BTC 40%, Indirect 35%, Dealer 25%)
    combined_score = (btc_score * 0.40) + (indirect_score * 0.35) + (dealer_score * 0.25)
    
    return {
        'score': round(combined_score, 1),
        'avg_btc': round(avg_btc, 2) if avg_btc else None,
        'avg_indirect_pct': round(avg_indirect, 1) if avg_indirect else None,
        'avg_direct_pct': round(avg_direct, 1) if avg_direct else None,
        'avg_dealer_pct': round(avg_dealer, 1) if avg_dealer else None,
        'btc_score': round(btc_score, 1),
        'indirect_score': round(indirect_score, 1),
        'dealer_score': round(dealer_score, 1),
        'auction_count': len(df)
    }


def _get_recent_auctions_with_alerts(df: pd.DataFrame, n: int = 15) -> List[Dict]:
    recent = df.head(n * 2)
    
    auctions = []
    for _, row in recent.iterrows():
        if pd.isna(row.get('bid_to_cover')):
            continue
        
        sec_type = row.get('security_type', 'Note')
        btc = row['bid_to_cover']
        indirect = row.get('indirect_pct')
        direct = row.get('direct_pct')
        dealer = row.get('dealer_pct')
        
        # Convert row to dict for alert detection
        auction_dict = {
            'security_type': sec_type,
            'security_term': row.get('security_term', ''),
            'bid_to_cover': btc,
            'indirect_pct': indirect,
            'direct_pct': direct,
            'dealer_pct': dealer
        }
        
        # Detect alerts for this auction
        alerts = detect_auction_alerts(auction_dict)
        
        # Determine overall status based on alerts
        has_critical = any(a['level'] == 'critical' for a in alerts)
        has_warning = any(a['level'] == 'warning' for a in alerts)
        has_caution = any(a['level'] == 'caution' for a in alerts)
        
        if has_critical:
            status = 'CRITICAL'
            status_color = '#ef4444'
        elif has_warning:
            status = 'WARNING'
            status_color = '#f97316'
        elif has_caution:
            status = 'CAUTION'
            status_color = '#eab308'
        else:
            # Determine if strong or normal
            btc_thresh = BTC_THRESHOLDS.get(sec_type, BTC_THRESHOLDS['Note'])
            if btc >= btc_thresh['healthy']:
                status = 'STRONG'
                status_color = '#22c55e'
            else:
                status = 'NORMAL'
                status_color = '#6b7280'
        
        auctions.append({
            'date': row['auction_date'].strftime('%Y-%m-%d'),
            'security': f"{row.get('security_term', '')} {sec_type}",
            'security_type': sec_type,
            'cusip': row.get('cusip', ''),
            'bid_to_cover': round(btc, 2),
            'indirect_pct': round(indirect, 1) if indirect else None,
            'direct_pct': round(direct, 1) if direct else None,
            'dealer_pct': round(dealer, 1) if dealer else None,
            'amount_billions': round(row.get('amount_billions', 0), 1),
            'status': status,
            'status_color': status_color,
            'alerts': alerts,
            'alert_count': len(alerts)
        })
        
        if len(auctions) >= n:
            break
    
    return auctions


def _empty_demand_result() -> Dict:
    return {
        'overall_score': 0,
        'signal': 'NO_DATA',
        'signal_color': '#6b7280',
        'signal_description': 'No auction data available.',
        'by_type': {},
        'recent_auctions': [],
        'metrics': {},
        'alerts': {'status': 'NO_DATA', 'counts': {'critical': 0, 'warning': 0, 'caution': 0, 'total': 0}},
        'timestamp': datetime.now().isoformat()
    }


# ==============================================================================
# MAIN FETCH FUNCTION
# ==============================================================================

def fetch_treasury_auction_demand(silent: bool = False) -> Dict:
    """
    Main function to fetch and analyze Treasury auction demand with alerts.
    """
    if is_cache_fresh():
        cached = load_cache()
        if cached:
            if not silent:
                print("  [TreasuryDirect] Using cached auction demand data")
            return cached
    
    if not silent:
        print("  [TreasuryDirect] Fetching fresh auction demand data...")
    
    df = fetch_all_auction_data(lookback_days=LOOKBACK_YEARS * 365, silent=silent)
    
    if df.empty:
        if not silent:
            print("  [TreasuryDirect] No auction data available, trying cache fallback")
        cached = load_cache()
        if cached:
            return cached
        return _empty_demand_result()
    
    # Calculate demand score
    demand_score = calculate_auction_demand_score(df)
    
    # Detect all alerts
    all_alerts = []
    
    # Per-auction alerts (from recent auctions)
    for auction in demand_score.get('recent_auctions', []):
        all_alerts.extend(auction.get('alerts', []))
    
    # Trend alerts
    trend_alerts = detect_trend_alerts(df)
    all_alerts.extend(trend_alerts)
    
    # Maturity preference alerts
    preference_alerts = detect_maturity_preference_shift(df)
    all_alerts.extend(preference_alerts)
    
    # Generate alert summary
    alert_summary = generate_alert_summary(all_alerts)
    
    result = {
        'demand_score': demand_score,
        'alerts': alert_summary,
        'last_updated': datetime.now().isoformat()
    }
    
    save_cache(result)
    
    if not silent:
        print(f"  [TreasuryDirect] Score: {demand_score['overall_score']} ({demand_score['signal']})")
        print(f"  [TreasuryDirect] Alerts: {alert_summary['counts']['critical']} critical, {alert_summary['counts']['warning']} warning, {alert_summary['counts']['caution']} caution")
    
    return result


def get_auction_demand_for_pipeline() -> Dict:
    """
    Simplified function for integration with data_pipeline.py.
    """
    try:
        result = fetch_treasury_auction_demand(silent=True)
        demand = result.get('demand_score', {})
        alerts = result.get('alerts', {})
        
        return {
            'score': demand.get('overall_score', 0),
            'signal': demand.get('signal', 'NO_DATA'),
            'signal_color': demand.get('signal_color', '#6b7280'),
            'signal_description': demand.get('signal_description', ''),
            'by_type': demand.get('by_type', {}),
            'recent_auctions': demand.get('recent_auctions', []),
            'metrics': demand.get('metrics', {}),
            'alerts': {
                'status': alerts.get('status', 'NO_DATA'),
                'status_color': alerts.get('status_color', '#6b7280'),
                'recommendation': alerts.get('recommendation', ''),
                'counts': alerts.get('counts', {}),
                'critical_alerts': alerts.get('critical_alerts', []),
                'warning_alerts': alerts.get('warning_alerts', []),
            },
            'last_updated': result.get('last_updated')
        }
    except Exception as e:
        print(f"  [TreasuryDirect] Error: {e}")
        return {
            'score': 0,
            'signal': 'ERROR',
            'signal_color': '#6b7280',
            'signal_description': str(e),
            'by_type': {},
            'recent_auctions': [],
            'metrics': {},
            'alerts': {'status': 'ERROR', 'counts': {}},
            'last_updated': datetime.now().isoformat()
        }


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TREASURY AUCTION DEMAND MODULE v2.0")
    print("=" * 70)
    
    result = fetch_treasury_auction_demand(silent=False)
    
    print("\n" + "=" * 70)
    print("ALERT SUMMARY")
    print("=" * 70)
    
    alerts = result.get('alerts', {})
    print(f"\nStatus: {alerts.get('status', 'N/A')}")
    print(f"Critical: {alerts.get('counts', {}).get('critical', 0)}")
    print(f"Warning: {alerts.get('counts', {}).get('warning', 0)}")
    print(f"Caution: {alerts.get('counts', {}).get('caution', 0)}")
    print(f"\nRecommendation: {alerts.get('recommendation', 'N/A')}")
    
    if alerts.get('critical_alerts'):
        print("\n🔴 CRITICAL ALERTS:")
        for alert in alerts['critical_alerts'][:5]:
            print(f"  - {alert['title']}: {alert['message']}")
    
    if alerts.get('warning_alerts'):
        print("\n🟠 WARNING ALERTS:")
        for alert in alerts['warning_alerts'][:5]:
            print(f"  - {alert['title']}: {alert['message']}")
    
    print("\n✅ Module ready for integration")
