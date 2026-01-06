import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fredapi import Fred
from dotenv import load_dotenv
import json
import time
import logging
from typing import Dict, List, Any, Optional
import calendar

# Import Regime V2 module for CLI V2 and advanced regime calculations
from regime_v2 import (
    calculate_cli_v2,
    calculate_macro_regime_v2a,
    calculate_macro_regime_v2b,
    calculate_stress_historical,
    clean_series_for_json as clean_series_v2
)

# Import unified signal configuration
from signal_config import (
    compute_signal, SIGNAL_CONFIG, SignalState, STATE_SCORES,
    STANCE_KEYS, aggregate_signal_score, validate_weights
)

# Import Treasury maturity data module
from treasury_data import get_treasury_maturity_data

# Import Treasury auction demand module
from treasury_auction_demand import fetch_treasury_auction_demand

# Import Treasury refinancing signal module
from treasury_refinancing_signal import get_treasury_refinancing_signal

# Import Offshore Dollar Liquidity module
from offshore_liquidity import get_offshore_liquidity_output

# Helper functions for JSON serialization and date handling
def clean_for_json(obj):
    if isinstance(obj, pd.Series):
        # Return None (null in JSON) instead of 0 for NaN/Inf to avoid invalid JSON
        return [float(x) if pd.notnull(x) and np.isfinite(x) else None for x in obj.tolist()]
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(x) for x in obj]
    elif isinstance(obj, (float, np.float64, np.float32)):
        if pd.isnull(obj) or not np.isfinite(obj):
            return None
        return float(obj)
    return obj

def get_safe_last_date(series):
    try:
        valid = series.dropna()
        if not valid.empty:
            return valid.index[-1].strftime('%Y-%m-%d')
    except:
        pass
    return "N/A"

def get_current_fed_rate() -> float:
    """
    Returns the current Effective Federal Funds Rate (DFF) from FRED.
    This provides the real baseline used by CME FedWatch.
    """
    try:
        fred_client = Fred(api_key=os.getenv('FRED_API_KEY'))
        # Get latest Effective Fed Funds Rate
        # Series 'DFF' is the Daily Effective Fed Funds Rate
        s = fred_client.get_series('DFF')
        if not s.empty:
            return s.dropna().iloc[-1]
            
    except Exception as e:
        print(f"Error fetching DFF from FRED: {e}")
        
    return 3.58  # Current EFFR as of late Dec 2025 (hard fallback)

def calculate_projections(price: float, meeting: Dict, current_rate: float) -> Dict:
    """Helper to calculate probabilities for a specific futures price."""
    m_date = datetime.strptime(meeting['date'], '%Y-%m-%d')
    day = m_date.day
    _, num_days = calendar.monthrange(m_date.year, m_date.month)
    
    implied_month_avg = 100 - price
    try:
        target_post = (implied_month_avg * num_days - current_rate * (day - 1)) / (num_days - day + 1)
    except ZeroDivisionError:
        target_post = implied_month_avg
        
    rate_diff = target_post - current_rate
    cuts_implied = -rate_diff / 0.25
    
    p_cut, p_hold, p_hike = 0.0, 0.0, 0.0
    
    if cuts_implied > 0:
        if cuts_implied >= 1:
            p_cut = 100.0
        else:
            p_cut = cuts_implied * 100
            p_hold = (1 - cuts_implied) * 100
    elif cuts_implied < 0:
        hikes_implied = -cuts_implied
        if hikes_implied >= 1:
            p_hike = 100.0
        else:
            p_hike = hikes_implied * 100
            p_hold = (1 - hikes_implied) * 100
    else:
        p_hold = 100.0
        
    return {
        'cut': round(max(0, min(100, p_cut)), 1),
        'hold': round(max(0, min(100, p_hold)), 1),
        'hike': round(max(0, min(100, p_hike)), 1),
        'implied_rate': round(target_post, 3),
        'cumulative_cuts': round(max(0, cuts_implied), 2)
    }

def calculate_fed_probabilities(futures_data: Dict[str, Dict], meetings: List[Dict], current_rate: float) -> List[Dict]:
    """
    Calculate probabilities using CME FedWatch-style methodology:
    - For the first meeting: use the current EFFR (current_rate) as baseline
    - For subsequent meetings: use the prior meeting's implied post-rate as baseline
    
    futures_data is month_name -> {'price': current, 'price_1d': old1, 'price_5d': old5, 'price_1m': oldM}
    """
    # Sort meetings by date to ensure correct iteration
    sorted_meetings = sorted(meetings, key=lambda m: datetime.strptime(m['date'], '%Y-%m-%d'))
    
    # Running baseline: starts with current EFFR, then updated by each meeting's outcome
    running_baseline = current_rate
    is_first_meeting = True
    
    for meeting in sorted_meetings:
        date_obj = datetime.strptime(meeting['date'], '%Y-%m-%d')
        meeting_month = date_obj.strftime('%b %Y')
        
        if meeting_month not in futures_data:
            # No data for this month, skip
            continue
        
        # For the first meeting, use current EFFR as baseline
        # For subsequent meetings, use the running baseline (post-rate from prior meeting)
        if is_first_meeting:
            baseline_for_meeting = current_rate
            is_first_meeting = False
        else:
            baseline_for_meeting = running_baseline
            
        data = futures_data[meeting_month]
        
        # Calculate probabilities using the baseline
        curr_probs = calculate_projections(data['price'], meeting, baseline_for_meeting)
        old1_probs = calculate_projections(data['price_1d'], meeting, baseline_for_meeting)
        old5_probs = calculate_projections(data['price_5d'], meeting, baseline_for_meeting)
        oldM_probs = calculate_projections(data['price_1m'], meeting, baseline_for_meeting)
        
        # Sanity check: if implied_rate is way off (<0 or >10), use raw implied instead
        implied_month_avg = 100 - data['price']
        if curr_probs['implied_rate'] < 0 or curr_probs['implied_rate'] > 10:
            # Fallback: use raw implied month average
            curr_probs['implied_rate'] = round(implied_month_avg, 3)
            # Recalculate probabilities based on simple diff from baseline
            rate_diff = implied_month_avg - baseline_for_meeting
            cuts_implied = -rate_diff / 0.25
            p_cut, p_hold, p_hike = 0.0, 0.0, 0.0
            if cuts_implied > 0:
                p_cut = min(100, cuts_implied * 100)
                p_hold = max(0, 100 - p_cut)
            elif cuts_implied < 0:
                p_hike = min(100, -cuts_implied * 100)
                p_hold = max(0, 100 - p_hike)
            else:
                p_hold = 100.0
            curr_probs['cut'] = round(p_cut, 1)
            curr_probs['hold'] = round(p_hold, 1)
            curr_probs['hike'] = round(p_hike, 1)
            curr_probs['cumulative_cuts'] = round(max(0, cuts_implied), 2)
        
        # Add ROCs
        curr_probs['roc1d'] = {
            'cut': round(curr_probs['cut'] - old1_probs['cut'], 1),
            'hold': round(curr_probs['hold'] - old1_probs['hold'], 1),
            'hike': round(curr_probs['hike'] - old1_probs['hike'], 1)
        }
        curr_probs['roc5d'] = {
            'cut': round(curr_probs['cut'] - old5_probs['cut'], 1),
            'hold': round(curr_probs['hold'] - old5_probs['hold'], 1),
            'hike': round(curr_probs['hike'] - old5_probs['hike'], 1)
        }
        curr_probs['roc1m'] = {
            'cut': round(curr_probs['cut'] - oldM_probs['cut'], 1),
            'hold': round(curr_probs['hold'] - oldM_probs['hold'], 1),
            'hike': round(curr_probs['hike'] - oldM_probs['hike'], 1)
        }
        
        # Store baseline used for this meeting (for debugging/display)
        curr_probs['baseline'] = round(baseline_for_meeting, 3)
        
        meeting['probs'] = curr_probs
        
        # Update running baseline for the next meeting - use the implied post-meeting rate
        running_baseline = curr_probs['implied_rate']
        
    return meetings

def fetch_fed_funds_futures(meetings: List[Dict] = None) -> Dict[str, Dict]:
    """
    Fetch Fed Funds Futures (price vs 1D, 5D, 1M ago).
    Returns month_name -> {'price': curr, 'price_1d': p1, 'price_5d': p5, 'price_1m': pM}
    """
    results = {}
    
    try:
        if not tv:
            return results
            
        from tvDatafeed import Interval
        tv_client = tv
        
        today = datetime.now()
        month_codes = {
            1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
            7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
        }
        
        target_months = []
        if meetings:
            for m in meetings:
                d = datetime.strptime(m['date'], '%Y-%m-%d')
                target_months.append((d.month, d.year))
        
        for i in range(13):
            d = today + timedelta(days=31 * i)
            m_y = (d.month, d.year)
            if m_y not in target_months: target_months.append(m_y)
        
        target_months.sort(key=lambda x: (x[1], x[0]))

        # We need historical data (last 45 bars to cover 1M back)
        for month, year in target_months:
            code = month_codes[month]
            yr_str = str(year)[-2:]
            symbol = f"ZQ{code}20{yr_str}"
            
            try:
                # Get historical daily data
                data = tv_client.get_hist(symbol=symbol, exchange='CBOT', interval=Interval.in_daily, n_bars=45)
                
                if data is not None and not data.empty:
                    curr_price = float(data['close'].iloc[-1])
                    
                    # 1D ago (approx 1 trading day)
                    p1 = float(data['close'].iloc[-2]) if len(data) > 1 else curr_price
                    # 5D ago (approx 5 trading days)
                    p5 = float(data['close'].iloc[-6]) if len(data) > 6 else p1
                    # 1 month ago (approx 22 trading days)
                    pM = float(data['close'].iloc[-23]) if len(data) > 23 else p5
                    
                    month_name = datetime(year, month, 1).strftime('%b %Y')
                    results[month_name] = {
                        'price': round(curr_price, 4),
                        'price_1d': round(p1, 4),
                        'price_5d': round(p5, 4),
                        'price_1m': round(pM, 4)
                    }
            except:
                # Fallback to continuous front month ZQ1! if specific month fails
                try:
                    front = tv_client.get_hist(symbol='ZQ1!', exchange='CBOT', interval=Interval.in_daily, n_bars=45)
                    if front is not None and not front.empty:
                        c_p = float(front['close'].iloc[-1])
                        p1f = float(front['close'].iloc[-2]) if len(front) > 1 else c_p
                        p5f = float(front['close'].iloc[-6]) if len(front) > 6 else p1f
                        pMf = float(front['close'].iloc[-23]) if len(front) > 23 else p5f
                        
                        month_name = datetime(year, month, 1).strftime('%b %Y')
                        results[month_name] = {
                            'price': round(c_p, 4),
                            'price_1d': round(p1f, 4),
                            'price_5d': round(p5f, 4),
                            'price_1m': round(pMf, 4)
                        }
                except:
                    continue
                
        return results
        
    except Exception as e:
        print(f"Error in fetch_fed_funds_futures: {e}")
        return {}
        
    return results

def fetch_treasury_settlements() -> List[Dict]:
    """
    Fetch Treasury auction settlements from US Treasury Fiscal Data API.
    Returns a list of settlements with date, type, amount, and RRP coverage.
    Includes both past and future settlements with historical RRP data.
    Uses 24-hour cache to reduce API calls and improve resilience.
    """
    settlements = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Cache configuration
    cache_file = os.path.join(OUTPUT_DIR, 'treasury_settlements_cache.json')
    cache_hours = 24  # Refresh cache every 24 hours
    
    # Check if cache is fresh
    def is_cache_fresh():
        if not os.path.exists(cache_file):
            return False
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            hours_elapsed = (datetime.now() - file_mtime).total_seconds() / 3600
            return hours_elapsed < cache_hours
        except Exception:
            return False
    
    # Load from cache
    def load_cache():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    # Save to cache
    def save_cache(data):
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Warning: Could not save treasury cache: {e}")
    
    # Check if cached data has actual settlements (not empty)
    def is_cache_valid(data):
        if not data:
            return False
        individual = data.get('individual', [])
        grouped = data.get('grouped', [])
        return len(individual) > 0 or len(grouped) > 0
    
    # If cache is fresh AND has valid data, return cached data
    if is_cache_fresh():
        cached = load_cache()
        if cached and is_cache_valid(cached):
            return cached
    
    try:
        # Get current RRP balance and historical data
        rrp_balance_current = get_rrp_balance()
        rrp_history = get_rrp_history()
        
        # Helper function to get RRP balance for a specific date
        def get_rrp_for_date(date_str: str) -> float:
            if date_str >= today:
                return rrp_balance_current
            # Look for exact match or closest previous date
            if date_str in rrp_history:
                return rrp_history[date_str]
            # Find closest previous date
            sorted_dates = sorted([d for d in rrp_history.keys() if d <= date_str], reverse=True)
            if sorted_dates:
                return rrp_history[sorted_dates[0]]
            return rrp_balance_current
        
        # Helper function to process auction data
        def process_auction(auction: Dict, is_upcoming: bool = False) -> Optional[Dict]:
            issue_date = auction.get('issue_date', '')
            security_type = auction.get('security_type', '')
            security_term = auction.get('security_term', '')
            offering_amt = auction.get('offering_amt', '0')
            
            # Parse amount - API returns in DOLLARS, convert to BILLIONS
            try:
                amount_str = str(offering_amt).replace(',', '').replace('null', '0') if offering_amt else '0'
                amount_dollars = float(amount_str) if amount_str and amount_str != 'null' else 0
                amount_billions = amount_dollars / 1_000_000_000
            except (ValueError, TypeError):
                amount_billions = 0
            
            # Skip if no valid date or zero amounts
            if not issue_date or amount_billions <= 0:
                return None
                
            is_future = issue_date >= today
            rrp_at_time = get_rrp_for_date(issue_date)
            coverage_ratio = rrp_at_time / amount_billions if amount_billions > 0 else 999
            
            if coverage_ratio >= 3:
                risk_level = 'low'
            elif coverage_ratio >= 1.5:
                risk_level = 'medium'
            else:
                risk_level = 'high'
            
            return {
                'date': issue_date,
                'type': f"{security_term} {security_type}".strip(),
                'amount': round(amount_billions, 1),
                'rrp_balance': round(rrp_at_time, 1),
                'coverage_ratio': round(coverage_ratio, 1),
                'risk_level': risk_level,
                'is_future': is_future
            }
        
        base_url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
        
        # Helper function for robust GET with retry on 5xx/429 errors
        def get_json_with_retry(url: str, params: Dict, timeout: int, label: str, attempts: int = 5) -> Optional[Dict]:
            headers = {
                "User-Agent": "data_pipeline/treasury_settlements (requests)",
                "Accept": "application/json",
            }
            backoff = 1.0

            for i in range(1, attempts + 1):
                try:
                    r = requests.get(url, params=params, headers=headers, timeout=timeout)

                    # Retry on infrastructure/throttling errors
                    if r.status_code in (429, 500, 502, 503, 504):
                        raise requests.HTTPError(f"{r.status_code} {r.reason}", response=r)

                    r.raise_for_status()
                    return r.json()

                except Exception as e:
                    if i == attempts:
                        print(f"Error fetching {label} after {attempts} attempts: {e}")
                        return None
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 30)

            return None
        
        # 1. Fetch HISTORICAL auctions (completed) from auctions_query endpoint
        # Get last 2 years of data
        two_years_ago = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        historical_endpoint = f"{base_url}/v1/accounting/od/auctions_query"
        historical_params = {
            'filter': f'issue_date:gte:{two_years_ago}',
            'sort': '-issue_date',
            'page[size]': 500,
            'fields': 'issue_date,security_type,security_term,offering_amt'
        }
        
        data = get_json_with_retry(historical_endpoint, historical_params, timeout=20, label="historical auctions")
        if data and 'data' in data:
            for auction in data['data']:
                result = process_auction(auction)
                if result:
                    settlements.append(result)
        
        # 2. Fetch UPCOMING auctions (scheduled) from upcoming_auctions endpoint
        upcoming_endpoint = f"{base_url}/v1/accounting/od/upcoming_auctions"
        upcoming_params = {
            'sort': '-issue_date',
            'page[size]': 100
        }
        
        data = get_json_with_retry(upcoming_endpoint, upcoming_params, timeout=15, label="upcoming auctions")
        if data and 'data' in data:
            for auction in data['data']:
                issue_date = auction.get('issue_date', '')
                if issue_date >= today:
                    result = process_auction(auction, is_upcoming=True)
                    if result and not any(s['date'] == result['date'] and s['type'] == result['type'] for s in settlements):
                        settlements.append(result)
        
        # If API returned nothing, try stale cache (better old data than no data)
        if not settlements:
            cached = load_cache()
            if cached and is_cache_valid(cached):
                print("  -> Using stale cached treasury settlements data (API unavailable)")
                return cached
        
        # Sort by date (descending - most recent first)
        settlements.sort(key=lambda x: x['date'], reverse=True)
        
        # Individual settlements (no grouping) - for individual view
        individual = settlements.copy()
        
        # Group settlements by date and sum amounts - for grouped view
        grouped = {}
        for s in settlements:
            date = s['date']
            if date not in grouped:
                grouped[date] = {
                    'date': date,
                    'types': [],
                    'total_amount': 0,
                    'rrp_balance': s['rrp_balance'],
                    'coverage_ratio': 0,
                    'risk_level': 'low',
                    'is_future': s['is_future']
                }
            grouped[date]['types'].append(s['type'])
            grouped[date]['total_amount'] += s['amount']
        
        # Recalculate coverage for grouped settlements
        grouped_result = []
        for date, data in grouped.items():
            coverage = data['rrp_balance'] / data['total_amount'] if data['total_amount'] > 0 else 999
            if coverage >= 3:
                risk = 'low'
            elif coverage >= 1.5:
                risk = 'medium'
            else:
                risk = 'high'
            
            grouped_result.append({
                'date': date,
                'types': ', '.join(data['types'][:3]) + ('...' if len(data['types']) > 3 else ''),
                'amount': round(data['total_amount'], 1),
                'rrp_balance': data['rrp_balance'],
                'coverage_ratio': round(coverage, 1),
                'risk_level': risk,
                'is_future': data['is_future']
            })
        
        # Sort grouped by date descending
        grouped_result = sorted(grouped_result, key=lambda x: x['date'], reverse=True)
        
        # Return both individual and grouped data
        result = {
            'individual': individual,
            'grouped': grouped_result,
            'current_rrp': rrp_balance_current
        }
        
        # Save to cache for future use (only if we have valid data)
        if is_cache_valid(result):
            save_cache(result)
        return result
        
    except Exception as e:
        print(f"Error fetching treasury settlements: {e}")
        # Try to use cached data as fallback (only if it has valid data)
        cached = load_cache()
        if cached and is_cache_valid(cached):
            print("  -> Using cached treasury settlements data")
            return cached
        return {'individual': [], 'grouped': [], 'current_rrp': 300.0}

def get_rrp_balance() -> float:
    """
    Get the current Overnight Reverse Repurchase Agreement balance from FRED.
    Series: RRPONTSYD (in billions of dollars)
    """
    try:
        fred_client = Fred(api_key=os.getenv('FRED_API_KEY'))
        series = fred_client.get_series('RRPONTSYD')
        
        if not series.empty:
            # Get latest non-null value
            latest = series.dropna().iloc[-1]
            return float(latest)  # Already in billions
            
    except Exception as e:
        print(f"Error fetching RRP from FRED: {e}")
    
    return 300.0  # Fallback value (current approximate level)

def get_rrp_history() -> Dict[str, float]:
    """
    Get the full history of RRP balances from FRED for historical analysis.
    Returns a dict of date_str -> balance_in_billions
    """
    try:
        fred_client = Fred(api_key=os.getenv('FRED_API_KEY'))
        series = fred_client.get_series('RRPONTSYD')
        
        if not series.empty:
            # Convert to dict with date strings as keys
            result = {}
            for date, value in series.dropna().items():
                date_str = date.strftime('%Y-%m-%d')
                result[date_str] = float(value)
            return result
            
    except Exception as e:
        print(f"Error fetching RRP history from FRED: {e}")
    
    return {}

def fetch_fomc_calendar():
    """
    Fetch upcoming FOMC meeting dates from the Federal Reserve's official calendar.
    Returns a list of meeting dictionaries with date, label, and hasSEP flag.
    """
    try:
        from bs4 import BeautifulSoup
        import re
        
        url = 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        meetings = []
        today = datetime.now()
        
        # Parse all meeting rows from the calendar
        for panel in soup.select('.panel.panel-default'):
            year_header = panel.select_one('.panel-heading')
            if not year_header:
                continue
            year_text = year_header.get_text(strip=True)
            year_match = re.search(r'(\d{4})', year_text)
            if not year_match:
                continue
            year = int(year_match.group(1))
            
            # Find meeting rows
            for row in panel.select('.fomc-meeting'):
                month_elem = row.select_one('.fomc-meeting__month')
                dates_elem = row.select_one('.fomc-meeting__date')
                
                if not month_elem or not dates_elem:
                    continue
                
                month_text = month_elem.get_text(strip=True)
                dates_text = dates_elem.get_text(strip=True)
                
                # Parse month
                month_map = {
                    'January': 1, 'February': 2, 'March': 3, 'April': 4,
                    'May': 5, 'June': 6, 'July': 7, 'August': 8,
                    'September': 9, 'October': 10, 'November': 11, 'December': 12
                }
                month = month_map.get(month_text, 0)
                if not month:
                    continue
                
                # Parse dates (e.g., "28-29" or "18")
                date_match = re.search(r'(\d+)(?:-(\d+))?', dates_text)
                if not date_match:
                    continue
                end_day = int(date_match.group(2) or date_match.group(1))
                
                # Check if SEP meeting (has projection materials)
                has_sep = '*' in dates_text or 'projection' in row.get_text().lower()
                
                # Create meeting date
                try:
                    meeting_date = datetime(year, month, end_day)
                    if meeting_date > today:
                        label = f"{month_text[:3]} {dates_text.replace('*', '').strip()}"
                        meetings.append({
                            'date': meeting_date.strftime('%Y-%m-%d'),
                            'label': label,
                            'hasSEP': has_sep
                        })
                except ValueError:
                    continue
        
        # Sort by date
        meetings.sort(key=lambda x: x['date'])
        
        # Calculate probabilities for upcoming meetings
        if meetings:
            futures_prices = fetch_fed_funds_futures()
            current_rate = get_current_fed_rate()
            meetings = calculate_fed_probabilities(futures_prices, meetings, current_rate)
            
        print(f"  -> Scraped {len(meetings)} upcoming FOMC dates from Fed calendar")
        return meetings[:8]  # Return next 8 meetings
        
    except Exception as e:
        print(f"  -> Warning: Could not fetch FOMC calendar: {e}")
        # Return fallback hardcoded dates
        return [
            {'date': '2025-01-29', 'label': 'Jan 28-29', 'hasSEP': False},
            {'date': '2025-03-19', 'label': 'Mar 18-19', 'hasSEP': True},
            {'date': '2025-05-07', 'label': 'May 6-7', 'hasSEP': False},
            {'date': '2025-06-18', 'label': 'Jun 17-18', 'hasSEP': True},
            {'date': '2025-07-30', 'label': 'Jul 29-30', 'hasSEP': False},
            {'date': '2025-09-17', 'label': 'Sep 16-17', 'hasSEP': True},
            {'date': '2025-10-29', 'label': 'Oct 28-29', 'hasSEP': False},
            {'date': '2025-12-10', 'label': 'Dec 9-10', 'hasSEP': True},
        ]

def fetch_dot_plot_data():
    """
    Fetch latest Dot Plot data from palewire/fed-dot-plot-scraper GitHub repo.
    Source: https://github.com/palewire/fed-dot-plot-scraper
    Returns dict with meeting info, projections by year, and current rate.
    """
    import pandas as pd
    import io
    
    DOT_PLOT_URL = 'https://raw.githubusercontent.com/palewire/fed-dot-plot-scraper/main/data/dotplot.csv'
    
    # Fallback data (December 2024 FOMC)
    FALLBACK_DOT_PLOT = {
        'year': 2024,
        'meeting': 'December 2024',
        'currentRate': 4.375,
        'projections': {
            '2024': [4.375] * 19,
            '2025': [3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125, 4.125, 4.375, 4.375, 4.375, 4.375, 4.375, 4.625, 4.625],
            '2026': [2.875, 3.125, 3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625, 3.625, 3.625, 3.625, 3.875, 3.875, 3.875, 3.875, 4.125, 4.125, 4.125],
            '2027': [2.625, 2.875, 2.875, 2.875, 2.875, 3.125, 3.125, 3.125, 3.125, 3.125, 3.375, 3.375, 3.375, 3.375, 3.625, 3.625, 3.625, 3.875, 3.875],
            'longerRun': [2.625, 2.625, 2.875, 2.875, 2.875, 2.875, 2.875, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.125, 3.125, 3.25, 3.25, 3.5],
        }
    }
    
    try:
        # Fetch CSV from GitHub
        response = requests.get(DOT_PLOT_URL, timeout=15)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Get latest meeting date
        latest_date = df['date'].max()
        latest_df = df[df['date'] == latest_date].copy()
        
        # Parse meeting date for display
        meeting_dt = datetime.strptime(latest_date, '%Y-%m-%d')
        meeting_label = meeting_dt.strftime('%B %Y')  # e.g., "December 2024"
        
        # Get projection years (columns that are numeric years or 'longer_run')
        year_cols = [c for c in df.columns if c.isdigit() or c == 'longer_run']
        
        # Build projections dict
        projections = {}
        for col in year_cols:
            if col not in latest_df.columns:
                continue
            
            # Get rate-count pairs
            col_data = latest_df[['midpoint', col]].dropna(subset=[col])
            col_data = col_data[col_data[col] > 0]
            
            if col_data.empty:
                continue
            
            # Convert to list of rates (repeat by count)
            rates = []
            for _, row in col_data.iterrows():
                count = int(row[col])
                rate = float(row['midpoint'])
                rates.extend([rate] * count)
            
            # Use 'longerRun' key for consistency with frontend
            key = 'longerRun' if col == 'longer_run' else col
            projections[key] = sorted(rates)
        
        # Calculate current rate (median of current year's projections)
        current_year = str(datetime.now().year)
        current_rate = 4.375  # default
        if current_year in projections and projections[current_year]:
            rates = projections[current_year]
            current_rate = rates[len(rates) // 2]
        
        result = {
            'year': meeting_dt.year,
            'meeting': meeting_label,
            'currentRate': current_rate,
            'projections': projections
        }
        
        print(f"  -> Fetched Dot Plot data from {meeting_label} ({len(projections)} years)")
        return result
        
    except Exception as e:
        print(f"  -> Warning: Could not fetch Dot Plot: {e}")
        return FALLBACK_DOT_PLOT

def calculate_market_stress_analysis(df, silent=False):
    """
    Calculates comprehensive market stress analysis based on multiple indicators.
    Returns dict with stress scores for inflation, liquidity, credit, and volatility.
    """
    import numpy as np
    
    def safe_get_last(series, default=0):
        """Get last valid value from series"""
        if series is None or len(series) == 0:
            return default
        valid = series.dropna()
        return float(valid.iloc[-1]) if len(valid) > 0 else default
    
    def calculate_zscore(series, window=252):
        """Calculate rolling Z-score"""
        if series is None or len(series) < window:
            return pd.Series(dtype=float)
        mean = series.rolling(window=window, min_periods=window//2).mean()
        std = series.rolling(window=window, min_periods=window//2).std()
        return (series - mean) / (std + 1e-10)
    
    def calculate_roc(series, periods):
        """Calculate Rate of Change"""
        if series is None or len(series) < periods:
            return pd.Series(dtype=float)
        return (series / series.shift(periods) - 1) * 100
    
    analysis = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'inflation_stress': {'score': 0, 'max_score': 7, 'level': 'LOW', 'color': 'green', 'signals': [], 'metrics': {}},
        'liquidity_stress': {'score': 0, 'max_score': 7, 'level': 'LOW', 'color': 'green', 'signals': [], 'metrics': {}},
        'credit_stress': {'score': 0, 'max_score': 7, 'level': 'LOW', 'color': 'green', 'signals': [], 'metrics': {}},
        'volatility_stress': {'score': 0, 'max_score': 4, 'level': 'LOW', 'color': 'green', 'signals': [], 'metrics': {}},
        'global_stress': {'total_score': 0, 'max_score': 25, 'percentage': 0, 'level': 'LOW', 'color': '#16a34a', 'assessment': ''},
        'chart_analyses': {},
        'overall_assessment': {'headline': '', 'key_risks': [], 'key_positives': [], 'recommendation': ''}
    }
    
    try:
        # ============================================================
        # 1. INFLATION STRESS ANALYSIS
        # ============================================================
        tips_be = df.get('TIPS_BREAKEVEN', pd.Series(dtype=float))
        tips_5y5y = df.get('TIPS_5Y5Y_FORWARD', pd.Series(dtype=float))
        tips_real = df.get('TIPS_REAL_RATE', pd.Series(dtype=float))
        clev_10y = df.get('CLEV_EXPINF_10Y', pd.Series(dtype=float))
        clev_5y = df.get('CLEV_EXPINF_5Y', pd.Series(dtype=float))
        inf_risk_prem = df.get('INF_RISK_PREM_10Y', pd.Series(dtype=float))
        umich = df.get('UMICH_INFL_EXP', pd.Series(dtype=float))
        
        last_tips_be = safe_get_last(tips_be, 2.2)
        last_clev_10y = safe_get_last(clev_10y, 2.3)
        last_clev_5y = safe_get_last(clev_5y, 2.2)
        last_5y5y = safe_get_last(tips_5y5y, 2.3)
        last_real = safe_get_last(tips_real, 1.5)
        last_inf_risk = safe_get_last(inf_risk_prem, 0.1)
        last_umich = safe_get_last(umich, 3.0)
        
        tips_clev_divergence = abs(last_tips_be - last_clev_10y)
        tips_be_zscore = safe_get_last(calculate_zscore(tips_be), 0)
        tips_be_roc_1m = safe_get_last(calculate_roc(tips_be, 21), 0)
        tips_be_roc_3m = safe_get_last(calculate_roc(tips_be, 63), 0)
        
        inflation_score = 0
        inflation_signals = []
        
        if last_tips_be > 2.5:
            inflation_score += 2
            inflation_signals.append({"text": "⚠️ Breakeven inflation above 2.5% - hawkish Fed pressure", "key": "ms_infl_be_high"})
        elif last_tips_be > 2.2:
            inflation_score += 1
            inflation_signals.append({"text": "🔶 Breakeven inflation slightly elevated (2.2-2.5%)", "key": "ms_infl_be_elevated"})
        elif last_tips_be < 1.8:
            inflation_score -= 1
            inflation_signals.append({"text": "🔵 Breakeven inflation below target - potential easing", "key": "ms_infl_be_low"})
        else:
            inflation_signals.append({"text": "✅ Breakeven inflation near 2% target", "key": "ms_infl_be_normal"})
        
        if tips_clev_divergence > 0.3:
            inflation_score += 1
            inflation_signals.append({"text": f"⚠️ High TIPS/Swap divergence ({tips_clev_divergence:.2f}pp)", "key": "ms_infl_div_high"})
        
        if last_5y5y > 2.5:
            inflation_score += 1
            inflation_signals.append({"text": "⚠️ Long-term inflation expectations elevated (>2.5%)", "key": "ms_infl_5y5y_high"})
        
        if last_inf_risk > 0.3:
            inflation_score += 1
            inflation_signals.append({"text": "⚠️ Elevated inflation risk premium", "key": "ms_infl_risk_high"})
        
        if tips_be_roc_3m > 20:
            inflation_score += 2
            inflation_signals.append({"text": "🔴 Rapid rise in inflation expectations (>20% 3M)", "key": "ms_infl_roc_high"})
        
        inf_level = 'HIGH' if inflation_score >= 4 else 'MODERATE' if inflation_score >= 2 else 'LOW'
        inf_color = 'red' if inflation_score >= 4 else 'yellow' if inflation_score >= 2 else 'green'
        
        analysis['inflation_stress'] = {
            'score': max(0, inflation_score),
            'max_score': 7,
            'level': inf_level,
            'color': inf_color,
            'signals': inflation_signals,
            'metrics': {
                'tips_breakeven_10y': round(last_tips_be, 3),
                'tips_breakeven_10y_zscore': round(tips_be_zscore, 2),
                'cleveland_10y': round(last_clev_10y, 3),
                'cleveland_5y': round(last_clev_5y, 3),
                'tips_clev_divergence': round(tips_clev_divergence, 3),
                '5y5y_forward': round(last_5y5y, 3),
                'real_rate_10y': round(last_real, 3),
                'inflation_risk_premium': round(last_inf_risk, 3),
                'umich_expectations': round(last_umich, 2),
                'breakeven_roc_1m': round(tips_be_roc_1m, 2),
                'breakeven_roc_3m': round(tips_be_roc_3m, 2)
            }
        }
        
        # ============================================================
        # 2. LIQUIDITY STRESS ANALYSIS
        # ============================================================
        sofr = df.get('SOFR', pd.Series(dtype=float))
        iorb = df.get('IORB', pd.Series(dtype=float))
        reserves = df.get('BANK_RESERVES', pd.Series(dtype=float))
        rrp = df.get('RRP_USD', pd.Series(dtype=float))
        tga = df.get('TGA_USD', pd.Series(dtype=float))
        fed_assets = df.get('FED_USD', pd.Series(dtype=float))
        
        last_sofr = safe_get_last(sofr, 5.0)
        last_iorb = safe_get_last(iorb, 5.0)
        last_reserves = safe_get_last(reserves, 3.0)
        last_rrp = safe_get_last(rrp, 0.5)
        last_tga = safe_get_last(tga, 0.7)
        last_fed = safe_get_last(fed_assets, 7.0)
        
        sofr_iorb_spread = (last_sofr - last_iorb) * 100
        net_liquidity = last_fed - last_tga - last_rrp
        reserves_roc_3m = safe_get_last(calculate_roc(reserves, 63), 0)
        
        liquidity_score = 0
        liquidity_signals = []
        
        if sofr_iorb_spread > 5:
            liquidity_score += 2
            liquidity_signals.append({"text": f"🔴 SOFR trading {sofr_iorb_spread:.0f}bps above IORB - funding stress", "key": "ms_liq_sofr_high"})
        elif sofr_iorb_spread > 2:
            liquidity_score += 1
            liquidity_signals.append({"text": f"🔶 SOFR slightly above IORB (+{sofr_iorb_spread:.0f}bps)", "key": "ms_liq_sofr_elevated"})
        else:
            liquidity_signals.append({"text": f"✅ SOFR-IORB spread normal ({sofr_iorb_spread:.0f}bps)", "key": "ms_liq_sofr_normal"})
        
        if last_reserves < 2.8:
            liquidity_score += 2
            liquidity_signals.append({"text": f"🔴 Bank reserves critically low (${last_reserves:.2f}T)", "key": "ms_liq_reserves_critical"})
        elif last_reserves < 3.2:
            liquidity_score += 1
            liquidity_signals.append({"text": "🔶 Bank reserves approaching stress zone", "key": "ms_liq_reserves_low"})
        else:
            liquidity_signals.append({"text": f"✅ Bank reserves adequate (${last_reserves:.2f}T)", "key": "ms_liq_reserves_adequate"})
        
        if last_rrp < 0.1:
            liquidity_score += 1
            liquidity_signals.append({"text": "⚠️ RRP nearly depleted", "key": "ms_liq_rrp_depleted"})
        
        if net_liquidity < 5.5:
            liquidity_score += 1
            liquidity_signals.append({"text": f"⚠️ Net liquidity contracting (${net_liquidity:.2f}T)", "key": "ms_liq_net_contracting"})
        
        liq_level = 'HIGH' if liquidity_score >= 4 else 'MODERATE' if liquidity_score >= 2 else 'LOW'
        liq_color = 'red' if liquidity_score >= 4 else 'yellow' if liquidity_score >= 2 else 'green'
        
        analysis['liquidity_stress'] = {
            'score': max(0, liquidity_score),
            'max_score': 7,
            'level': liq_level,
            'color': liq_color,
            'signals': liquidity_signals,
            'metrics': {
                'sofr': round(last_sofr, 3),
                'iorb': round(last_iorb, 3),
                'sofr_iorb_spread_bps': round(sofr_iorb_spread, 1),
                'bank_reserves_t': round(last_reserves, 3),
                'rrp_t': round(last_rrp, 3),
                'tga_t': round(last_tga, 3),
                'net_liquidity_t': round(net_liquidity, 3),
                'reserves_roc_3m': round(reserves_roc_3m, 2)
            }
        }
        
        # ============================================================
        # 3. CREDIT STRESS ANALYSIS
        # ============================================================
        hy_spread = df.get('HY_SPREAD', pd.Series(dtype=float))
        ig_spread = df.get('IG_SPREAD', pd.Series(dtype=float))
        nfci = df.get('NFCI', pd.Series(dtype=float))
        nfci_credit = df.get('NFCI_CREDIT', pd.Series(dtype=float))
        nfci_risk = df.get('NFCI_RISK', pd.Series(dtype=float))
        lending_std = df.get('LENDING_STD', pd.Series(dtype=float))
        
        last_hy = safe_get_last(hy_spread, 400)
        last_ig = safe_get_last(ig_spread, 100)
        last_nfci = safe_get_last(nfci, 0)
        last_nfci_credit = safe_get_last(nfci_credit, 0)
        last_nfci_risk = safe_get_last(nfci_risk, 0)
        last_lending = safe_get_last(lending_std, 0)
        hy_zscore = safe_get_last(calculate_zscore(hy_spread), 0)
        ig_zscore = safe_get_last(calculate_zscore(ig_spread), 0)
        
        credit_score = 0
        credit_signals = []
        
        if last_hy > 500:
            credit_score += 2
            credit_signals.append({"text": f"🔴 HY spreads elevated ({last_hy:.0f}bps)", "key": "ms_cred_hy_high"})
        elif last_hy > 400:
            credit_score += 1
            credit_signals.append({"text": f"🔶 HY spreads above average ({last_hy:.0f}bps)", "key": "ms_cred_hy_elevated"})
        elif last_hy < 300:
            credit_signals.append({"text": f"🟢 HY spreads tight ({last_hy:.0f}bps)", "key": "ms_cred_hy_tight"})
        else:
            credit_signals.append({"text": f"✅ HY spreads normal ({last_hy:.0f}bps)", "key": "ms_cred_hy_normal"})
        
        if last_ig > 150:
            credit_score += 1
            credit_signals.append({"text": f"⚠️ IG spreads elevated ({last_ig:.0f}bps)", "key": "ms_cred_ig_high"})
        
        if last_nfci > 0.5:
            credit_score += 2
            credit_signals.append({"text": f"🔴 NFCI signals tight conditions ({last_nfci:.2f})", "key": "ms_cred_nfci_tight"})
        elif last_nfci > 0:
            credit_score += 1
            credit_signals.append({"text": f"🔶 NFCI slightly tight ({last_nfci:.2f})", "key": "ms_cred_nfci_elevated"})
        else:
            credit_signals.append({"text": f"✅ NFCI neutral/loose ({last_nfci:.2f})", "key": "ms_cred_nfci_normal"})
        
        cred_level = 'HIGH' if credit_score >= 4 else 'MODERATE' if credit_score >= 2 else 'LOW'
        cred_color = 'red' if credit_score >= 4 else 'yellow' if credit_score >= 2 else 'green'
        
        analysis['credit_stress'] = {
            'score': max(0, credit_score),
            'max_score': 7,
            'level': cred_level,
            'color': cred_color,
            'signals': credit_signals,
            'metrics': {
                'hy_spread_bps': round(last_hy, 1),
                'hy_zscore': round(hy_zscore, 2),
                'ig_spread_bps': round(last_ig, 1),
                'ig_zscore': round(ig_zscore, 2),
                'nfci': round(last_nfci, 3),
                'nfci_credit': round(last_nfci_credit, 3),
                'nfci_risk': round(last_nfci_risk, 3),
                'lending_standards': round(last_lending, 1)
            }
        }
        
        # ============================================================
        # 4. VOLATILITY STRESS ANALYSIS
        # ============================================================
        vix = df.get('VIX', pd.Series(dtype=float))
        treasury_10y = df.get('TREASURY_10Y_YIELD', pd.Series(dtype=float))
        
        last_vix = safe_get_last(vix, 18)
        vix_zscore = safe_get_last(calculate_zscore(vix), 0)
        vix_roc_1w = safe_get_last(calculate_roc(vix, 5), 0)
        
        # Calculate 10Y yield volatility (20-day rolling std of yield changes in bps)
        if treasury_10y is not None and len(treasury_10y) > 20:
            yield_changes = treasury_10y.diff() * 100  # Convert to bps
            yield_vol_20d = yield_changes.rolling(window=20, min_periods=10).std()
            last_yield_vol = safe_get_last(yield_vol_20d, 5)
            yield_vol_zscore = safe_get_last(calculate_zscore(yield_vol_20d), 0)
        else:
            last_yield_vol = 5.0  # Default ~5bps daily vol
            yield_vol_zscore = 0
        
        last_10y_yield = safe_get_last(treasury_10y, 4.0)
        
        vol_score = 0
        vol_signals = []
        
        # VIX signals
        if last_vix > 30:
            vol_score += 2
            vol_signals.append({"text": f"🔴 VIX elevated ({last_vix:.1f}) - high fear", "key": "ms_vol_vix_high"})
        elif last_vix > 20:
            vol_score += 1
            vol_signals.append({"text": f"🔶 VIX above average ({last_vix:.1f})", "key": "ms_vol_vix_elevated"})
        elif last_vix < 12:
            vol_signals.append({"text": f"⚠️ VIX very low ({last_vix:.1f}) - complacency", "key": "ms_vol_vix_complacency"})
        else:
            vol_signals.append({"text": f"✅ VIX normal ({last_vix:.1f})", "key": "ms_vol_vix_normal"})
        
        if vix_zscore > 2:
            vol_score += 1
            vol_signals.append({"text": f"🔴 VIX Z-score extreme ({vix_zscore:.2f})", "key": "ms_vol_vix_z_extreme"})
        
        if vix_roc_1w > 30:
            vol_score += 1
            vol_signals.append({"text": f"⚠️ VIX spiking ({vix_roc_1w:.0f}% weekly)", "key": "ms_vol_vix_spike"})
        
        # Treasury yield volatility signals (MOVE proxy)
        if last_yield_vol > 10:
            vol_score += 2
            vol_signals.append({"text": f"🔴 10Y yield volatility HIGH ({last_yield_vol:.1f}bps/day)", "key": "ms_vol_yield_high"})
        elif last_yield_vol > 7:
            vol_score += 1
            vol_signals.append({"text": f"🔶 10Y yield volatility elevated ({last_yield_vol:.1f}bps/day)", "key": "ms_vol_yield_elevated"})
        else:
            vol_signals.append({"text": f"✅ 10Y yield volatility normal ({last_yield_vol:.1f}bps/day)", "key": "ms_vol_yield_normal"})
        
        # Update max score to account for new yield vol signals
        vol_max_score = 6  # VIX (4) + Yield Vol (2)
        vol_level = 'HIGH' if vol_score >= 4 else 'MODERATE' if vol_score >= 2 else 'LOW'
        vol_color = 'red' if vol_score >= 4 else 'yellow' if vol_score >= 2 else 'green'
        
        analysis['volatility_stress'] = {
            'score': max(0, vol_score),
            'max_score': vol_max_score,
            'level': vol_level,
            'color': vol_color,
            'signals': vol_signals,
            'metrics': {
                'vix': round(last_vix, 2),
                'vix_zscore': round(vix_zscore, 2),
                'vix_roc_1w': round(vix_roc_1w, 1),
                'yield_10y': round(last_10y_yield, 3),
                'yield_vol_20d': round(last_yield_vol, 2),
                'yield_vol_zscore': round(yield_vol_zscore, 2)
            }
        }
        
        # ============================================================
        # 5. GLOBAL STRESS SCORE
        # ============================================================
        total_score = (
            analysis['inflation_stress']['score'] +
            analysis['liquidity_stress']['score'] +
            analysis['credit_stress']['score'] +
            analysis['volatility_stress']['score']
        )
        max_total = 27  # 7+7+7+6 (inflation, liquidity, credit, volatility)
        
        if total_score >= 15:
            global_level = 'CRITICAL'
            global_color = '#dc2626'
            global_assessment = {"text": "🚨 CRITICAL STRESS - Multiple systemic risk indicators elevated", "key": "ms_global_critical"}
        elif total_score >= 10:
            global_level = 'HIGH'
            global_color = '#ea580c'
            global_assessment = {"text": "⚠️ HIGH STRESS - Significant tensions across markets", "key": "ms_global_high"}
        elif total_score >= 5:
            global_level = 'MODERATE'
            global_color = '#ca8a04'
            global_assessment = {"text": "🔶 MODERATE STRESS - Some warning signs present", "key": "ms_global_moderate"}
        else:
            global_level = 'LOW'
            global_color = '#16a34a'
            global_assessment = {"text": "✅ LOW STRESS - Market conditions relatively stable", "key": "ms_global_low"}
        
        analysis['global_stress'] = {
            'total_score': total_score,
            'max_score': max_total,
            'percentage': round(total_score / max_total * 100, 1),
            'level': global_level,
            'color': global_color,
            'assessment': global_assessment,
            'breakdown': {
                'inflation': analysis['inflation_stress']['score'],
                'liquidity': analysis['liquidity_stress']['score'],
                'credit': analysis['credit_stress']['score'],
                'volatility': analysis['volatility_stress']['score']
            }
        }
        
        # ============================================================
        # 6. CHART ANALYSES
        # ============================================================
        analysis['chart_analyses'] = {
            'tips_market': {
                'title': 'Inflation Expectations (TIPS Market)',
                'summary': f"10Y Breakeven at {last_tips_be:.2f}%. 5Y5Y Forward at {last_5y5y:.2f}%. Real rates at {last_real:.2f}%.",
                'summary_key': 'ms_chart_tips_summary',
                'signal': 'CAUTION' if last_tips_be > 2.5 or last_tips_be < 1.5 else 'NEUTRAL',
                'signal_key': 'ms_signal_caution' if last_tips_be > 2.5 or last_tips_be < 1.5 else 'ms_signal_neutral',
                'signal_color': 'yellow' if last_tips_be > 2.5 or last_tips_be < 1.5 else 'green'
            },
            'tips_vs_swaps': {
                'title': 'TIPS vs Cleveland Fed (Inflation Swaps)',
                'summary': f"TIPS ({last_tips_be:.2f}%) vs Cleveland Fed ({last_clev_10y:.2f}%). Divergence: {tips_clev_divergence:.2f}pp.",
                'summary_key': 'ms_chart_tips_swaps_summary',
                'signal': 'DIVERGENCE' if tips_clev_divergence > 0.3 else 'ALIGNED',
                'signal_key': 'ms_signal_divergence' if tips_clev_divergence > 0.3 else 'ms_signal_aligned',
                'signal_color': 'yellow' if tips_clev_divergence > 0.3 else 'green'
            },
            'bank_reserves': {
                'title': 'Bank Reserves vs Net Liquidity',
                'summary': f"Reserves at ${last_reserves:.2f}T. Net Liquidity: ${net_liquidity:.2f}T.",
                'summary_key': 'ms_chart_reserves_summary',
                'signal': 'STRESS' if last_reserves < 3.0 else 'OK',
                'signal_key': 'ms_signal_stress' if last_reserves < 3.0 else 'ms_signal_ok',
                'signal_color': 'red' if last_reserves < 3.0 else 'green'
            },
            'repo_stress': {
                'title': 'Repo Market Stress (SOFR vs IORB)',
                'summary': f"SOFR at {last_sofr:.3f}%, IORB at {last_iorb:.3f}%. Spread: {sofr_iorb_spread:.1f}bps.",
                'summary_key': 'ms_chart_repo_summary',
                'signal': 'STRESS' if sofr_iorb_spread > 5 else 'NORMAL',
                'signal_key': 'ms_signal_stress' if sofr_iorb_spread > 5 else 'ms_signal_normal',
                'signal_color': 'red' if sofr_iorb_spread > 5 else 'green'
            },
            'credit_conditions': {
                'title': 'Credit Conditions (CLI)',
                'summary': f"HY spread: {last_hy:.0f}bps. NFCI: {last_nfci:.2f}.",
                'summary_key': 'ms_chart_credit_summary',
                'signal': 'TIGHT' if last_nfci > 0 else 'NORMAL',
                'signal_key': 'ms_signal_tight' if last_nfci > 0 else 'ms_signal_normal',
                'signal_color': 'yellow' if last_nfci > 0 else 'green'
            },
            'volatility': {
                'title': 'Volatility (VIX)',
                'summary': f"VIX at {last_vix:.1f} (Z: {vix_zscore:.1f}).",
                'summary_key': 'ms_chart_vol_summary',
                'signal': 'FEAR' if last_vix > 25 else 'COMPLACENT' if last_vix < 12 else 'NEUTRAL',
                'signal_key': 'ms_signal_fear' if last_vix > 25 else 'ms_signal_complacent' if last_vix < 12 else 'ms_signal_neutral',
                'signal_color': 'red' if last_vix > 25 else 'yellow' if last_vix < 12 else 'green'
            }
        }
        
        # ============================================================
        # 7. OVERALL ASSESSMENT
        # ============================================================
        key_risks = []
        key_positives = []
        
        if inflation_score >= 3:
            key_risks.append({"text": "Inflation expectations deviating from target", "key": "ms_risk_infl"})
        if liquidity_score >= 3:
            key_risks.append({"text": "Liquidity conditions tightening", "key": "ms_risk_liq"})
        if credit_score >= 3:
            key_risks.append({"text": "Credit spreads widening", "key": "ms_risk_cred"})
        if vol_score >= 2:
            key_risks.append({"text": "Elevated market volatility", "key": "ms_risk_vol"})
        
        if inflation_score <= 1:
            key_positives.append({"text": "Inflation expectations well-anchored", "key": "ms_pos_infl"})
        if liquidity_score <= 1:
            key_positives.append({"text": "Ample liquidity in the system", "key": "ms_pos_liq"})
        if credit_score <= 1:
            key_positives.append({"text": "Credit conditions supportive", "key": "ms_pos_cred"})
        if vol_score <= 1:
            key_positives.append({"text": "Low volatility environment", "key": "ms_pos_vol"})
        
        analysis['overall_assessment'] = {
            'headline': global_assessment,
            'key_risks': key_risks if key_risks else [{"text": "No major stress signals detected", "key": "ms_risk_none"}],
            'key_positives': key_positives if key_positives else [{"text": "Market in transition phase", "key": "ms_pos_transition"}],
            'recommendation': (
                {"text": "Consider defensive positioning", "key": "ms_rec_defensive"} if total_score >= 10 
                else {"text": "Monitor closely for changes", "key": "ms_rec_monitor"} if total_score >= 5 
                else {"text": "Environment supportive for risk assets", "key": "ms_rec_supportive"}
            )
        }
        
        if not silent:
            print(f"  -> Stress analysis complete: {global_level} ({total_score}/{max_total})")
        
    except Exception as e:
        print(f"  -> Warning: Stress analysis error: {e}")
    
    return analysis

def calculate_net_repo_operations(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Calculates the net repo operations of the Fed.
    Net Repo = SRF Usage (Injection) - RRP Usage (Drain)
    
    Returns:
        Dict with series:
        - net_repo: Net operations in $B
        - srf_usage: SRF usage in $B
        - rrp_usage: RRP usage in $B
        - net_repo_zscore: Z-score of net repo
        - net_repo_momentum: 4-week momentum of net repo
        - cumulative_30d: 30-day rolling sum of net repo
    """
    idx = df.index
    
    # SRF Usage comes in $B from FRED
    srf_usage = df.get('SRF_USAGE', pd.Series(0.0, index=idx)).fillna(0)
    
    # RRP - usually in Trillions in our df_t, convert to Billions
    rrp_t = df.get('RRP_USD', df.get('RRP', pd.Series(0.0, index=idx)))
    rrp_usage = rrp_t * 1000  # T -> B
    rrp_usage = rrp_usage.fillna(0)
    
    # Net Repo: Positive = Injection, Negative = Drain
    net_repo = srf_usage - rrp_usage
    
    # Derived Metrics
    net_mean = net_repo.rolling(252, min_periods=60).mean()
    net_std = net_repo.rolling(252, min_periods=60).std().replace(0, np.nan)
    net_repo_zscore = (net_repo - net_mean) / net_std
    
    net_repo_momentum = net_repo.diff(20)  # 4 weeks
    cumulative_30d = net_repo.rolling(30, min_periods=1).sum()
    
    return {
        'srf_usage': srf_usage,
        'rrp_usage': rrp_usage,
        'net_repo': net_repo,
        'net_repo_zscore': pd.Series(net_repo_zscore, index=idx),
        'net_repo_momentum': net_repo_momentum,
        'cumulative_30d': cumulative_30d
    }

# tvDatafeed import
try:
    from tvDatafeed import TvDatafeed, Interval
    TV_AVAILABLE = True
except ImportError:
    print("WARNING: tvDatafeed not found. Please install it using: pip install git+https://github.com/rongardF/tvdatafeed.git")
    TvDatafeed = None
    Interval = None
    TV_AVAILABLE = False

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================
load_dotenv()

FRED_API_KEY = os.environ.get('FRED_API_KEY')
TV_USERNAME = os.environ.get('TV_USERNAME')
TV_PASSWORD = os.environ.get('TV_PASSWORD')
DATA_SOURCE = os.environ.get('DATA_SOURCE', 'FRED') # Default to FRED

if not FRED_API_KEY:
    print("WARNING: FRED_API_KEY not found in environment. Please add it to your .env file.")

fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None

def try_tv_login(username, password, max_retries=10, delay=3):
    """
    Attempts to log in to TradingView with aggressive retry loop.
    Keeps trying until success, with exponential-ish backoff.
    """
    if not TV_AVAILABLE:
        return None

    attempt = 0
    while True:
        attempt += 1
        try:
            print(f"Attempting TV Login ({attempt})...")
            if username and password:
                tv_instance = TvDatafeed(username, password)
            else:
                tv_instance = TvDatafeed()
            
            # Verify login worked by making a simple request
            test = tv_instance.get_hist("BTCUSD", "BITSTAMP", Interval.in_daily, n_bars=5)
            if test is not None and len(test) > 0:
                print("TV Login Successful!")
                return tv_instance
            else:
                raise Exception("Login succeeded but test fetch failed")
                
        except Exception as e:
            print(f"TV Login failed (Attempt {attempt}): {e}")
            if attempt >= max_retries:
                print("Max retries reached. Falling back to Guest mode...")
                try:
                    return TvDatafeed()
                except:
                    return None
            wait_time = min(delay * (1.5 ** (attempt - 1)), 30)  # Max 30s wait
            time.sleep(wait_time)

tv = try_tv_login(TV_USERNAME, TV_PASSWORD) if TV_AVAILABLE else None

# Output directory and cache setup
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)
CACHE_FILE = os.path.join(OUTPUT_DIR, 'data_cache_info.json')

def check_data_freshness(symbol_name, cache_hours=12):
    """
    Checks if cached data for a symbol is still fresh (within cache_hours).
    Returns True if data needs refresh, False if cache is still valid.
    """
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_info = json.load(f)
            if symbol_name in cache_info:
                last_update = datetime.fromisoformat(cache_info[symbol_name])
                hours_elapsed = (datetime.now() - last_update).total_seconds() / 3600
                if hours_elapsed < cache_hours:
                    return False  # Cache is still fresh
    except Exception:
        pass
    return True  # Needs refresh

def update_cache_timestamp(symbol_name):
    """Updates the cache timestamp for a symbol."""
    try:
        cache_info = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                cache_info = json.load(f)
        cache_info[symbol_name] = datetime.now().isoformat()
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_info, f)
    except Exception:
        pass

START_DATE = '1970-01-01'

def max_bars_from_start(start_date: str, interval) -> int:
    """
    Calculates the maximum number of bars from start_date to now.
    Prevents requesting timestamps before 1970 which causes OSError on Windows.
    """
    start = pd.Timestamp(start_date)
    now = pd.Timestamp.now().normalize()  # Use tz-naive now() to match start

    if interval == Interval.in_monthly:
        return (now.year - start.year) * 12 + (now.month - start.month) + 1
    if interval == Interval.in_weekly:
        return int((now - start).days // 7) + 1
    if interval == Interval.in_daily:
        return int((now - start).days) + 1

    return 1500  # Default fallback

# ============================================================
# SERIES DEFINITIONS
# ============================================================
# Mapping: FRED_ID -> Internal Name
FRED_CONFIG = {
    'WALCL': 'FED',
    'ECBASSETSW': 'ECB',
    'JPNASSETS': 'BOJ',
    # 'UKASSETS': 'BOE',  # DISCONTINUED - DO NOT USE
    # 'MABMM301CNA189S': 'PBOC', # WRONG CONCEPT (M3 NOT ASSETS) - DO NOT USE
    'DEXUSEU': 'EURUSD',
    'DEXJPUS': 'USDJPY',
    'DEXUSUK': 'GBPUSD',
    'DEXCHUS': 'USDCNY',
    'WTREGEN': 'TGA',
    'RRPONTSYD': 'RRP',
    'BAMLH0A0HYM2': 'HY_SPREAD',
    'BAMLC0A0CM': 'IG_SPREAD',
    'NFCI': 'NFCI',
    'NFCICREDIT': 'NFCI_CREDIT',
    'NFCIRISK': 'NFCI_RISK',
    'DRTSCILM': 'LENDING_STD',
    'VIXCLS': 'VIX',
    # TIPS / Inflation Expectations (high-frequency, FRED-exclusive)
    'T10YIE': 'TIPS_BREAKEVEN',           # 10-Year Breakeven Inflation Rate
    'DFII10': 'TIPS_REAL_RATE',           # 10-Year Real Interest Rate (TIPS Yield)
    'T5YIFR': 'TIPS_5Y5Y_FORWARD',        # 5-Year, 5-Year Forward Inflation Expectation
    'WRESBAL': 'BANK_RESERVES',           # Bank Reserves (Total, Weekly, Millions $)
    'SOFR': 'SOFR',                       # Secured Overnight Financing Rate
    'IORB': 'IORB',                        # Interest on Reserve Balances
    'SOFRVOL': 'SOFR_VOLUME',              # SOFR Transaction Volume ($ Billions)
    # Repo Corridor Rates (Fed Rate Corridor Bounds)
    'SRFTSYD': 'SRF_RATE',                 # Standing Repo Facility Rate (ceiling, since 2021-07-29)
    'RRPONTSYAWARD': 'RRP_AWARD',          # ON RRP Award Rate (lower floor)
    'RPONTSYD': 'SRF_USAGE',               # SRF/Repo Operations Volume ($B) - usage signals stress
    # Note: RPONAGYD removed - not a counterparty count series, only amounts available in FRED
    # Note: EVZCLS removed - EVZ discontinued Jan 2025. Using DXY realized vol instead.
    # Fed Forecasts tab - Macro Indicators
    'CPIAUCSL': 'CPI',                     # Consumer Price Index (All Urban)
    'CPILFESL': 'CORE_CPI',                # Core CPI (excl. Food & Energy)
    'PCEPI': 'PCE',                        # Personal Consumption Expenditures
    'PCEPILFE': 'CORE_PCE',                # Core PCE (Fed's preferred gauge)
    'UNRATE': 'UNEMPLOYMENT',              # Unemployment Rate
    'FEDFUNDS': 'FED_FUNDS_RATE',          # Effective Federal Funds Rate
    # Inflation Expectations (TIPS Breakeven + Cleveland Fed Model)
    # Note: ICE Swap Rates (ICERATES1100USD*) discontinued Jan 2022
    'T5YIEM': 'INFLATION_EXPECT_5Y',       # 5-Year TIPS Breakeven Inflation Rate
    'T10YIEM': 'INFLATION_EXPECT_10Y',     # 10-Year TIPS Breakeven Inflation Rate
    'EXPINF1YR': 'INFLATION_EXPECT_1Y',    # 1-Year Expected Inflation (Cleveland Fed)
    # Cleveland Fed Expected Inflation (incorporates Treasury yields, CPI, and Inflation Swaps)
    'EXPINF2YR': 'CLEV_EXPINF_2Y',         # 2-Year Expected Inflation (Cleveland Fed)
    'EXPINF5YR': 'CLEV_EXPINF_5Y',         # 5-Year Expected Inflation (Cleveland Fed)
    'EXPINF10YR': 'CLEV_EXPINF_10Y',       # 10-Year Expected Inflation (Cleveland Fed)
    # Note: Removed discontinued FRED series:
    # - INFRISPR1YR, INFRISPR10YR (Inflation Risk Premium) - no longer available
    # - REAINT1YR, REAINT10YR (Real Interest Rate) - no longer available
    # - T2YIE (2-Year Breakeven) - no longer available
    # University of Michigan Inflation Expectations (Survey-based)
    'MICH': 'UMICH_INFL_EXP',              # UMich 1-Year Ahead Inflation Expectations
    # Additional TIPS Breakeven for curve construction
    'T5YIE': 'TIPS_BREAKEVEN_5Y',          # 5-Year Breakeven Inflation Rate
    # Treasury Yields for stress analysis
    'DGS30': 'TREASURY_30Y_YIELD',         # 30-Year Treasury Constant Maturity Yield
    'DGS10': 'TREASURY_10Y_YIELD',         # 10-Year Treasury Constant Maturity Yield
    'DGS5': 'TREASURY_5Y_YIELD',           # 5-Year Treasury Constant Maturity Yield
    'DGS2': 'TREASURY_2Y_YIELD',           # 2-Year Treasury Constant Maturity Yield
    'PAYEMS': 'NFP',                       # All Employees, Total Nonfarm
    'JTSJOL': 'JOLTS',                     # Job Openings: Total Nonfarm
    # Additional financial stress indices (for robustness/sanity check)
    'STLFSI4': 'ST_LOUIS_STRESS',          # St. Louis Fed Financial Stress Index
    'KCFSI': 'KANSAS_CITY_STRESS',         # Kansas City Financial Stress Index
    'BAA': 'BAA_YIELD',                    # Moody's Seasoned Baa Corporate Bond Yield
    'AAA': 'AAA_YIELD',                    # Moody's Seasoned Aaa Corporate Bond Yield
    'SWPT': 'CB_LIQ_SWAPS',                # Assets: Central Bank Liquidity Swaps
    # Offshore Liquidity (Eurodollar / Shadow Banking Stress)
    'OBFR': 'OBFR',                         # Overnight Bank Funding Rate (includes offshore)
    'EFFR': 'EFFR',                         # Effective Federal Funds Rate (onshore only)
    # Index-based compounded rates for XCCY basis calculation
    'SOFRINDEX': 'SOFR_INDEX',              # SOFR Compounded Index (daily)
    'SOFR90DAYAVG': 'SOFR_90D_AVG',          # 90-Day Average SOFR (sanity check)
    'IUDZOS2': 'SONIA_INDEX',               # SONIA Compounded Index (daily)
    'ECBESTRVOLWGTTRMDMNRT': 'ESTR',     # €STR Volume-Weighted Trimmed Mean Rate (daily)
}

# Mapping: Symbol -> Internal Name (TradingView ECONOMICS)
# Matches the PineScript GLI indicator by QuantitativeAlpha
TV_CONFIG = {
    # ==========================================================
    # CENTRAL BANK BALANCE SHEETS (17 banks)
    # ==========================================================
    # Major CBs
    'USCBBS': ('ECONOMICS', 'FED'),      # Federal Reserve
    'EUCBBS': ('ECONOMICS', 'ECB'),      # European Central Bank
    'JPCBBS': ('ECONOMICS', 'BOJ'),      # Bank of Japan
    'CNCBBS': ('ECONOMICS', 'PBOC'),     # People's Bank of China
    'GBCBBS': ('ECONOMICS', 'BOE'),      # Bank of England
    # Additional CBs (from "other_active" in PineScript)
    'CACBBS': ('ECONOMICS', 'BOC'),      # Bank of Canada
    'AUCBBS': ('ECONOMICS', 'RBA'),      # Reserve Bank of Australia
    'INCBBS': ('ECONOMICS', 'RBI'),      # Reserve Bank of India
    'CHCBBS': ('ECONOMICS', 'SNB'),      # Swiss National Bank
    'RUCBBS': ('ECONOMICS', 'CBR'),      # Central Bank of Russia
    'BRCBBS': ('ECONOMICS', 'BCB'),      # Banco Central do Brasil
    'KRCBBS': ('ECONOMICS', 'BOK'),      # Bank of Korea
    'NZCBBS': ('ECONOMICS', 'RBNZ'),     # Reserve Bank of New Zealand
    'SECBBS': ('ECONOMICS', 'SR'),       # Sveriges Riksbank (Sweden)
    'MYCBBS': ('ECONOMICS', 'BNM'),      # Bank Negara Malaysia
    
    # ==========================================================
    # M2 MONEY SUPPLY (14 economies)
    # ==========================================================
    # Major M2s
    'USM2': ('ECONOMICS', 'USM2'),       # USA
    'EUM2': ('ECONOMICS', 'EUM2'),       # EU
    'CNM2': ('ECONOMICS', 'CNM2'),       # China
    'JPM2': ('ECONOMICS', 'JPM2'),       # Japan
    # Additional M2s (from "other_m2_active" in PineScript)
    'GBM2': ('ECONOMICS', 'GBM2'),       # UK
    'CAM2': ('ECONOMICS', 'CAM2'),       # Canada
    'AUM3': ('ECONOMICS', 'AUM3'),       # Australia (M3)
    'INM2': ('ECONOMICS', 'INM2'),       # India
    'CHM2': ('ECONOMICS', 'CHM2'),       # Switzerland
    'RUM2': ('ECONOMICS', 'RUM2'),       # Russia
    'BRM2': ('ECONOMICS', 'BRM2'),       # Brazil
    'KRM2': ('ECONOMICS', 'KRM2'),       # Korea
    'MXM2': ('ECONOMICS', 'MXM2'),       # Mexico
    'IDM2': ('ECONOMICS', 'IDM2'),       # Indonesia
    'ZAM2': ('ECONOMICS', 'ZAM2'),       # South Africa
    'MYM2': ('ECONOMICS', 'MYM2'),       # Malaysia
    'SEM2': ('ECONOMICS', 'SEM2'),       # Sweden
    
    # ==========================================================
    # FX RATES (all needed for conversions)
    # ==========================================================
    'EURUSD': ('FX_IDC', 'EURUSD'),
    'JPYUSD': ('FX_IDC', 'JPYUSD'),
    'GBPUSD': ('FX_IDC', 'GBPUSD'),
    'CNYUSD': ('FX_IDC', 'CNYUSD'),
    'CADUSD': ('FX_IDC', 'CADUSD'),
    'AUDUSD': ('FX_IDC', 'AUDUSD'),
    'INRUSD': ('FX_IDC', 'INRUSD'),
    'CHFUSD': ('FX_IDC', 'CHFUSD'),
    'RUBUSD': ('FX_IDC', 'RUBUSD'),
    'BRLUSD': ('FX_IDC', 'BRLUSD'),
    'KRWUSD': ('FX_IDC', 'KRWUSD'),
    'NZDUSD': ('FX_IDC', 'NZDUSD'),
    'SEKUSD': ('FX_IDC', 'SEKUSD'),
    'MYRUSD': ('FX_IDC', 'MYRUSD'),
    'MXNUSD': ('FX_IDC', 'MXNUSD'),
    'IDRUSD': ('FX_IDC', 'IDRUSD'),
    'ZARUSD': ('FX_IDC', 'ZARUSD'),
    
    # ==========================================================
    # OFFSHORE LIQUIDITY: FX SPOTS FOR XCCY BASIS
    # Reuse existing EURUSD, GBPUSD. Add USDJPY for direct USD/JPY quote.
    # The _SPOT suffix aliases are created in processing below.
    # ==========================================================
    'USDJPY': ('FX_IDC', 'USDJPY'),           # USD/JPY Spot (direct quote)
    
    # ==========================================================
    # OFFSHORE LIQUIDITY: CME FX FUTURES FOR XCCY BASIS
    # ==========================================================
    '6E1!': ('CME', 'EURUSD_FUT'),           # Euro FX Front Month
    '6J1!': ('CME', 'JPYUSD_FUT'),           # Japanese Yen FX Front Month (inverse of USDJPY)
    '6B1!': ('CME', 'GBPUSD_FUT'),           # British Pound FX Front Month
    
    # ==========================================================
    # OTHER & MACRO
    # ==========================================================
    'BTCUSD': ('BITSTAMP', 'BTC'),
    'MOVE': ('TVC', 'MOVE'),             # ICE BofA MOVE Index
    'DXY': ('TVC', 'DXY'),               # US Dollar Index
    'USBCOI': ('ECONOMICS', 'ISM_MFG'),   # US ISM Manufacturing PMI
    'USNMBA': ('ECONOMICS', 'ISM_SVC'),   # US ISM Non-Manufacturing (Services)
    
    # ==========================================================
    # STABLECOINS - Market Caps (CRYPTOCAP)
    # ==========================================================
    'USDT': ('CRYPTOCAP', 'USDT_MCAP'),       # Tether Market Cap
    'USDC': ('CRYPTOCAP', 'USDC_MCAP'),       # USD Coin Market Cap
    'DAI': ('CRYPTOCAP', 'DAI_MCAP'),         # DAI Market Cap
    'TUSD': ('CRYPTOCAP', 'TUSD_MCAP'),       # TrueUSD Market Cap
    'USDD': ('CRYPTOCAP', 'USDD_MCAP'),       # USDD Market Cap
    'USDP': ('CRYPTOCAP', 'USDP_MCAP'),       # Pax Dollar Market Cap
    'USDEE': ('CRYPTOCAP', 'USDEE_MCAP'),     # Ethena USDe (ticker USDEE)
    'PYUSD': ('CRYPTOCAP', 'PYUSD_MCAP'),     # PayPal USD
    'USD1W': ('CRYPTOCAP', 'USD1W_MCAP'),     # USD1W
    'RLUSD': ('CRYPTOCAP', 'RLUSD_MCAP'),     # Ripple USD
    'USDGG': ('CRYPTOCAP', 'USDGG_MCAP'),     # Global Dollar (ticker USDGG)
    'FDUSD': ('CRYPTOCAP', 'FDUSD_MCAP'),     # First Digital USD
    'TOTAL': ('CRYPTOCAP', 'TOTAL_MCAP'),     # Total Crypto Market Cap
    
    # ==========================================================
    # STABLECOINS - Prices (for depeg detection)
    # ==========================================================
    'USDTUSD': ('KRAKEN', 'USDT_PRICE'),      # USDT/USD Price
    'USDCUSD': ('KRAKEN', 'USDC_PRICE'),      # USDC/USD Price
    'DAIUSD': ('COINBASE', 'DAI_PRICE'),      # DAI/USD Price
    'PYUSDUSD': ('KRAKEN', 'PYUSD_PRICE'),    # PYUSD/USD Price
    'FDUSDUSDT': ('BINANCE', 'FDUSD_PRICE'),  # FDUSD/USDT Price (proxy)
    'USDEUSDT': ('BYBIT', 'USDE_PRICE'),      # USDE/USDT Price (proxy)
    'USDDUSDT': ('HTX', 'USDD_PRICE'),        # USDD/USDT Price
    'USD1USD': ('KRAKEN', 'USD1W_PRICE'),    # World Liberty Financial (USD1)
    'RLUSDUSD': ('KRAKEN', 'RLUSD_PRICE'),    # Ripple USD
    'USDGUSD': ('KRAKEN', 'USDG_PRICE'),      # Global Dollar

}

# ============================================================
# DATA FETCHING
# ============================================================
def fetch_fred_series(series_id, name):
    if not fred:
        return pd.Series(dtype=float, name=name)
    try:
        data = fred.get_series(series_id, observation_start=START_DATE)
        data.name = name
        # Apply publication lag to avoid lookahead bias
        return apply_publication_lag(data, series_id)
    except Exception as e:
        print(f"Error fetching FRED {series_id} ({name}): {e}")
        return pd.Series(dtype=float, name=name)

def fetch_tv_series(symbol, exchange, name, n_bars=1500, max_retries=3, return_ohlc=False):
    """
    Fetches TradingView data with smart interval fallback for ECONOMICS.
    ECONOMICS data is typically monthly, so we try monthly → weekly → daily.
    Caps n_bars to avoid pre-1970 timestamps which cause OSError on Windows.
    If return_ohlc is True, returns a DataFrame with OHLC columns.
    """
    if not tv:
        return pd.DataFrame() if return_ohlc else pd.Series(dtype=float, name=name)

    if exchange == 'ECONOMICS':
        # ECONOMICS data is typically monthly, so we try monthly → weekly → daily
        intervals = [Interval.in_monthly, Interval.in_weekly, Interval.in_daily]
    else:
        intervals = [Interval.in_daily]
    last_err = None

    print(f"Fetching TradingView: {symbol} from {exchange} (as {name})...")
    
    for interval in intervals:
        # Cap n_bars to avoid pre-1970 timestamps (causes OSError on Windows)
        if exchange == "ECONOMICS":
            safe_cap = max_bars_from_start(START_DATE, interval)
            effective_n = min(n_bars, safe_cap)
        else:
            effective_n = n_bars

        for attempt in range(1, max_retries + 1):
            try:
                df = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=effective_n)
                
                if df is not None and len(df) > 0:
                    if return_ohlc:
                        print(f"  OK (OHLC): {symbol}")
                        return df[["open", "high", "low", "close"]].copy()
                    
                    if "close" in df.columns:
                        s = df["close"].copy()
                        s.name = name
                        print(f"  OK: {symbol}")
                        return s
                    
            except OSError as e:
                # ... (error handling remains same)
                last_err = e
                if getattr(e, "errno", None) == 22 and effective_n > 200:
                    effective_n = max(200, effective_n // 2)
                time.sleep(1.5 * attempt)
            except Exception as e:
                last_err = e
                time.sleep(1.5 * attempt)

    if last_err:
        print(f"❌ FAILED to fetch TV {symbol} from {exchange} ({name}) after {max_retries} retries: {last_err}")
    else:
        print(f"⚠️ No data found for TV {symbol} from {exchange} ({name})")
    
    return pd.DataFrame() if return_ohlc else pd.Series(dtype=float, name=name)

# ============================================================
# CALCULATIONS & HELPERS
# ============================================================

# Publication lag (days) for slow-release series to avoid lookahead bias
PUBLICATION_LAGS = {
    'DRTSCILM': 45,        # SLOOS: ~6 weeks after quarter end
    'NFCI': 3,             # Weekly, ~3 days lag
    'M2SL': 15,            # M2: ~2 weeks after month end
    'ISM_MFG': 22,         # ISM: ~1 month lag
    'UNEMPLOYMENT': 5,     # BLS: ~5 days after month end
    'CORE_PCE': 30,        # PCE: ~1 month lag
    'NFP': 5,              # NFP: ~5 days after month end
}

def apply_publication_lag(series, fred_id):
    """Shift series by publication lag to avoid lookahead bias."""
    lag = PUBLICATION_LAGS.get(fred_id, 0)
    if lag > 0:
        return series.shift(lag)
    return series
def normalize_zscore(series, window=504, clip=5.0):
    """Normalized z-score with std=0 protection and optional clipping."""
    mean = series.rolling(window=window, min_periods=100).mean()
    std = series.rolling(window=window, min_periods=100).std()
    # Replace 0 with NaN to avoid inf values
    std = std.replace(0, np.nan)
    z = (series - mean) / std
    if clip is not None:
        z = z.clip(-clip, clip)
    return z

def weighted_sum_with_renorm(components: list, index: pd.Index):
    """
    Computes weighted sum of series in components list.
    Renormalizes weights if some series are NaN at a given date.
    components = [(series, weight), ...]
    """
    result = pd.Series(0.0, index=index)
    total_weight = pd.Series(0.0, index=index)
    
    for series, weight in components:
        if series is None:
            continue
        valid = series.notna()
        result += series.fillna(0.0) * weight
        total_weight += valid.astype(float) * weight
    
    # Avoid division by zero
    total_weight_safe = total_weight.replace(0, np.nan)
    return result / total_weight_safe

def calculate_gli_from_trillions(df):
    """
    Summarizes GLI components that are already in Trillions USD.
    Dynamically aggregates ALL available *_USD columns (up to 16 CBs).
    """
    res = pd.DataFrame(index=df.index)
    
    # Find all CB columns ending in _USD (excluding TGA_USD, RRP_USD which are not CBs)
    exclude_cols = ['TGA_USD', 'RRP_USD']
    cb_cols = [c for c in df.columns if c.endswith('_USD') and c not in exclude_cols]
    
    # Copy all CB columns to result
    for col in cb_cols:
        res[col] = df[col]
    
    # Sum all available CBs dynamically with min_count=1 to avoid 0.0 when all are NaN
    if cb_cols:
        cb_df = res[cb_cols].astype(float)
        res['GLI_TOTAL'] = cb_df.sum(axis=1, min_count=1)
        res['CB_COUNT'] = cb_df.notna().sum(axis=1)  # Per-date count of available CBs
    else:
        res['GLI_TOTAL'] = np.nan
        res['CB_COUNT'] = 0
    
    return res


def calculate_gli_constant_fx(df):
    """
    Calculates GLI with FX rates frozen at a base date (2019-12-31).
    This eliminates FX beta contamination, showing only actual CB asset changes.
    Uses frozen conversion factors for each CB to compute USD-equivalent trillions.
    """
    res = pd.Series(0.0, index=df.index)
    
    # Base FX rates as of 2019-12-31 (pre-pandemic snapshot)
    # Mapping: Local Name in df -> Fixed Conversion Rate
    # Note: Units in our DF for balance sheets are typically billions or trillions depending on source.
    # TV ECONOMICS data like USCBBS is in USD, EUCBBS in EUR, etc. normally raw integers or millions.
    # We want result in USD Trillions.
    
    CONV_FACTORS = {
        'FED': 1.0 / 1e12,        # USD -> Trillions
        'ECB': 1.12 / 1e12,       # EUR -> USD -> Trillions
        'BOJ': 0.0092 / 1e12,     # JPY -> USD -> Trillions
        'PBOC': 0.143 / 1e12,     # CNY -> USD -> Trillions
        'BOE': 1.31 / 1e12,       # GBP -> USD -> Trillions
        'BOC': 0.77 / 1e12,       # CAD -> USD -> Trillions
        'RBA': 0.70 / 1e12,       # AUD -> USD -> Trillions
        'RBI': 0.014 / 1e12,      # INR -> USD -> Trillions
        'SNB': 1.03 / 1e12,       # CHF -> USD -> Trillions
        'CBR': 0.016 / 1e12,      # RUB -> USD -> Trillions
        'BCB': 0.25 / 1e12,       # BRL -> USD -> Trillions
        'BOK': 0.00087 / 1e12,    # KRW -> USD -> Trillions
        'RBNZ': 0.67 / 1e12,     # NZD -> USD -> Trillions
        'SR': 0.107 / 1e12,       # SEK -> USD -> Trillions
        'BNM': 0.24 / 1e12,       # MYR -> USD -> Trillions
    }
    
    # Sum all contributing local CBs using fixed conversion
    for col, factor in CONV_FACTORS.items():
        if col in df.columns:
            res += df[col].fillna(0.0) * factor
            
    return res


def calculate_us_net_liq_from_trillions(df):
    """Calculates Net Liq from Trillion-scale components."""
    res = pd.DataFrame(index=df.index)
    # df['FED_USD'] is Trillions. TGA and RRP should also be in Trillions.
    res['NET_LIQUIDITY'] = df.get('FED_USD', 0) - df.get('TGA_USD', 0) - df.get('RRP_USD', 0)
    return res

def calculate_cli(df):
    """
    Calculates Credit Liquidity Index.
    SIGN CONVENTION: Higher CLI = easier credit conditions (bullish).
    Spreads ↑, VIX ↑, lending standards ↑ mean TIGHTER conditions => CLI ↓
    Therefore we NEGATE all z-scores.
    """
    res = pd.DataFrame(index=df.index)
    
    # Negate all z-scores: higher spread/VIX/lending = tighter = LOWER CLI
    # Use get() to handle missing columns gracefully
    if 'HY_SPREAD' in df.columns:
        res['HY_SPREAD_Z'] = -normalize_zscore(df['HY_SPREAD'])
    else:
        res['HY_SPREAD_Z'] = pd.Series(0.0, index=df.index)
        
    if 'IG_SPREAD' in df.columns:
        res['IG_SPREAD_Z'] = -normalize_zscore(df['IG_SPREAD'])
    else:
        res['IG_SPREAD_Z'] = pd.Series(0.0, index=df.index)
        
    if 'NFCI_CREDIT' in df.columns:
        res['NFCI_CREDIT_Z'] = -df['NFCI_CREDIT']  # NFCI already z-scored, negate
    else:
        res['NFCI_CREDIT_Z'] = pd.Series(0.0, index=df.index)
        
    if 'NFCI_RISK' in df.columns:
        res['NFCI_RISK_Z'] = -df['NFCI_RISK']
    else:
        res['NFCI_RISK_Z'] = pd.Series(0.0, index=df.index)
        
    if 'LENDING_STD' in df.columns:
        res['LENDING_STD_Z'] = -normalize_zscore(df['LENDING_STD'])
    else:
        res['LENDING_STD_Z'] = pd.Series(0.0, index=df.index)
        
    if 'VIX' in df.columns:
        res['VIX_Z'] = -normalize_zscore(df['VIX'])
    else:
        res['VIX_Z'] = pd.Series(0.0, index=df.index)
    
    weights_map = {
        'HY_SPREAD_Z': 0.25,
        'IG_SPREAD_Z': 0.15,
        'NFCI_CREDIT_Z': 0.20,
        'NFCI_RISK_Z': 0.20,
        'LENDING_STD_Z': 0.10,
        'VIX_Z': 0.10
    }
    
    # Use dynamic renormalization to handle missing components gracefully
    components = [(res[col], weight) for col, weight in weights_map.items() if col in res.columns]
    res['CLI'] = weighted_sum_with_renorm(components, df.index)
    
    return res


def calculate_gli(df, source='FRED'):
    """
    Calculates Global Liquidity Index in Trillions USD.
    Includes up to 16 central banks matching PineScript GLI indicator.
    """
    res = pd.DataFrame(index=df.index)
    
    if source == 'TV':
        # TradingView Units (ECONOMICS) - All are Raw Units (Units of Currency)
        # All CBs are converted to USD trillions using format: CB_local * XXXUSD / 1e12
        
        # Helper function for CB conversion
        def convert_cb(cb_col, fx_col, fx_fallback):
            if cb_col in df.columns:
                fx = df.get(fx_col, fx_fallback)
                return (df[cb_col] * fx) / 1e12
            return pd.Series(dtype=float)
        
        # Major 5 CBs
        res['FED_USD'] = df.get('FED', 0) / 1e12  # Already USD
        res['ECB_USD'] = convert_cb('ECB', 'EURUSD', 1.08)
        
        # BOJ uses JPYUSD (direct) or 1/USDJPY
        if 'BOJ' in df.columns:
            if 'JPYUSD' in df.columns:
                res['BOJ_USD'] = (df['BOJ'] * df['JPYUSD']) / 1e12
            else:
                res['BOJ_USD'] = df['BOJ'] / 150e12  # Fallback
        
        res['PBOC_USD'] = convert_cb('PBOC', 'CNYUSD', 0.14)
        res['BOE_USD'] = convert_cb('BOE', 'GBPUSD', 1.27)
        
        # Additional 11 CBs (matching PineScript "other_active")
        res['BOC_USD'] = convert_cb('BOC', 'CADUSD', 0.74)
        res['RBA_USD'] = convert_cb('RBA', 'AUDUSD', 0.65)
        res['RBI_USD'] = convert_cb('RBI', 'INRUSD', 0.012)
        res['SNB_USD'] = convert_cb('SNB', 'CHFUSD', 1.13)
        res['CBR_USD'] = convert_cb('CBR', 'RUBUSD', 0.011)
        res['BCB_USD'] = convert_cb('BCB', 'BRLUSD', 0.17)
        res['BOK_USD'] = convert_cb('BOK', 'KRWUSD', 0.00077)
        res['RBNZ_USD'] = convert_cb('RBNZ', 'NZDUSD', 0.60)
        res['SR_USD'] = convert_cb('SR', 'SEKUSD', 0.095)
        res['BNM_USD'] = convert_cb('BNM', 'MYRUSD', 0.22)
            
    else:
        # FRED Units logic (original 5 only):
        res['FED_USD'] = df['FED'] / 1e6
        res['ECB_USD'] = (df['ECB'] / 1e6) * df['EURUSD']
        res['BOJ_USD'] = (df['BOJ'] / 1e4) / df['USDJPY']
        res['BOE_USD'] = (df['BOE'] / 1e3) * df['GBPUSD']
        res['PBOC_USD'] = (df['PBOC'] / 1e12) / df['USDCNY']
    
    # Sum all available CBs dynamically
    cb_cols = [c for c in res.columns if c.endswith('_USD')]
    if cb_cols:
        res['GLI_TOTAL'] = res[cb_cols].sum(axis=1, min_count=1)
        res['CB_COUNT'] = res[cb_cols].notna().sum(axis=1)
    else:
        res['GLI_TOTAL'] = np.nan
        res['CB_COUNT'] = 0
    return res

def calculate_global_m2(df):
    """
    Calculates Global M2 Money Supply in Trillions USD.
    Includes up to 14 economies matching PineScript GLI indicator.
    """
    res = pd.DataFrame(index=df.index)
    
    # Helper function for M2 conversion
    def convert_m2(m2_col, fx_col, fx_fallback):
        if m2_col in df.columns:
            fx = df.get(fx_col, fx_fallback)
            val = df[m2_col] * fx
            
            # Logic to handle Units (TV) vs Billions (FRED)
            # If value is > 1 Trillion (1e12), it's probably in Units
            # If it's < 1 Trillion, it might be in Billions (like USM2 = 21,000)
            # Actually, standardizing: anything > 1e10 is likely Units.
            # 1 billion = 1e9. 10 billion = 1e10.
            # Typical M2 is > 100B.
            if val.mean() > 1e10:
                return val / 1e12  # Units -> Trillions
            else:
                return val / 1e3   # Billions -> Trillions
        return pd.Series(dtype=float)
    
    # Major 4 M2s
    res['US_M2_USD'] = convert_m2('USM2', None, 1.0)
    res['EU_M2_USD'] = convert_m2('EUM2', 'EURUSD', 1.08)
    res['CN_M2_USD'] = convert_m2('CNM2', 'CNYUSD', 0.14)
    
    # Japan M2 uses JPYUSD
    res['JP_M2_USD'] = convert_m2('JPM2', 'JPYUSD', 0.0067)
    
    # Additional 10 M2s (matching PineScript "other_m2_active")
    res['UK_M2_USD'] = convert_m2('GBM2', 'GBPUSD', 1.27)
    res['CA_M2_USD'] = convert_m2('CAM2', 'CADUSD', 0.74)
    res['AU_M2_USD'] = convert_m2('AUM3', 'AUDUSD', 0.65)  # Australia uses M3
    res['IN_M2_USD'] = convert_m2('INM2', 'INRUSD', 0.012)
    res['CH_M2_USD'] = convert_m2('CHM2', 'CHFUSD', 1.13)
    res['RU_M2_USD'] = convert_m2('RUM2', 'RUBUSD', 0.011)
    res['BR_M2_USD'] = convert_m2('BRM2', 'BRLUSD', 0.17)
    res['KR_M2_USD'] = convert_m2('KRM2', 'KRWUSD', 0.00077)
    res['MX_M2_USD'] = convert_m2('MXM2', 'MXNUSD', 0.058)
    res['ID_M2_USD'] = convert_m2('IDM2', 'IDRUSD', 0.000063)
    res['ZA_M2_USD'] = convert_m2('ZAM2', 'ZARUSD', 0.054)
    res['MY_M2_USD'] = convert_m2('MYM2', 'MYRUSD', 0.22)
    res['SE_M2_USD'] = convert_m2('SEM2', 'SEKUSD', 0.095)
    
    # Calculate total dynamically
    m2_cols = [c for c in res.columns if c.endswith('_M2_USD')]
    if m2_cols:
        res['M2_TOTAL'] = res[m2_cols].sum(axis=1)
    else:
        res['M2_TOTAL'] = 0
    
    return res

def calculate_rocs(df, windows={'1M': 21, '3M': 63, '6M': 126, '1Y': 252}):
    """
    Calculates Rate of Change for specified windows.
    NOTE: NaN values are preserved (not filled) to avoid artificial floors
    and contaminated correlations. Convert to None only for JSON output.
    """
    rocs = {}
    for label, window in windows.items():
        # ROC Calculation: (Current / Past) - 1
        roc = (df / df.shift(window) - 1) * 100
        rocs[label] = roc  # Keep NaN, don't fillna(0)
    return rocs

def calculate_cross_correlation(series1, series2, max_lag=90):
    """
    Calculates cross-correlation between two series with different lags.
    Returns dict with lag as key and correlation as value.
    Negative lag means series1 leads series2.
    Positive lag means series2 leads series1.
    
    FIXED: Uses shift() for true lag alignment instead of broken iloc slicing.
    lag > 0  => compare s1(t) vs s2(t+lag) (s1 leads by lag)
    lag < 0  => compare s1(t) vs s2(t+lag) (s2 leads by |lag|)
    """
    correlations = {}
    for lag in range(-max_lag, max_lag + 1):
        # shift(-lag) aligns s2 at t+lag with s1 at t
        # So lag > 0: s1 today vs s2 in 'lag' days (s1 leads)
        aligned = pd.concat([series1, series2.shift(-lag)], axis=1).dropna()
        if len(aligned) > 30:
            correlations[lag] = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
        else:
            correlations[lag] = None
    return correlations

def calculate_lag_correlation_analysis(df, max_lag=30):
    """
    Calculates multi-window ROCs for CLI and BTC, then computes lag correlations.
    Returns a dictionary with ROC series and lag correlation analysis.
    """
    results = {
        'rocs': {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
        },
        'lag_correlations': {}
    }
    
    windows = {'7d': 7, '14d': 14, '30d': 30}
    
    # Calculate ROCs for CLI and BTC at each window
    for label, window in windows.items():
        # CLI ROC
        if 'CLI' in df.columns:
            cli_roc = (df['CLI'] / df['CLI'].shift(window) - 1) * 100
            results['rocs'][f'cli_{label}'] = [float(x) if pd.notnull(x) else None for x in cli_roc.tolist()]
        
        # BTC ROC
        if 'BTC_Price' in df.columns:
            btc_roc = (df['BTC_Price'] / df['BTC_Price'].shift(window) - 1) * 100
            results['rocs'][f'btc_{label}'] = [float(x) if pd.notnull(x) else None for x in btc_roc.tolist()]
            
            # Compute lag correlations for this window
            if 'CLI' in df.columns:
                correlations = []
                lags = list(range(0, max_lag + 1))
                
                cli_roc_clean = cli_roc.dropna()
                btc_roc_clean = btc_roc.dropna()
                
                for lag in lags:
                    # CLI at time t vs BTC at time t+lag (CLI leads)
                    # This means: does CLI's change today predict BTC's change in 'lag' days?
                    if lag == 0:
                        common_idx = cli_roc_clean.index.intersection(btc_roc_clean.index)
                    else:
                        # Shift BTC backward by 'lag' days to see if CLI today correlates with BTC later
                        btc_shifted = btc_roc_clean.shift(-lag)
                        common_idx = cli_roc_clean.index.intersection(btc_shifted.dropna().index)
                        btc_roc_clean_lag = btc_shifted
                    
                    if len(common_idx) > 50:
                        if lag == 0:
                            corr = cli_roc_clean.loc[common_idx].corr(btc_roc_clean.loc[common_idx])
                        else:
                            corr = cli_roc_clean.loc[common_idx].corr(btc_roc_clean_lag.loc[common_idx])
                        correlations.append(round(corr, 4) if pd.notnull(corr) else None)
                    else:
                        correlations.append(None)
                
                # Find optimal lag
                valid_corrs = [(i, c) for i, c in enumerate(correlations) if c is not None]
                if valid_corrs:
                    optimal_idx, max_corr = max(valid_corrs, key=lambda x: abs(x[1]))
                    optimal_lag = lags[optimal_idx]
                else:
                    optimal_lag = 0
                    max_corr = 0
                
                results['lag_correlations'][label] = {
                    'lags': lags,
                    'correlations': correlations,
                    'optimal_lag': optimal_lag,
                    'max_corr': round(max_corr, 4) if max_corr else 0
                }
    
    return results


def calculate_reserves_metrics(df):
    """
    Calculates derived metrics for Bank Reserves analysis:
    1. 3-Month ROC for Reserves and Net Liquidity
    2. Spread (Net Liq - Reserves) with Z-Score
    3. Momentum (12w vs 26w EMA cross)
    4. Liquidity Coverage Ratio (Reserves / Net Liq)
    5. Acceleration Index
    """
    result = {}
    
    reserves = df.get('BANK_RESERVES', pd.Series(dtype=float))
    net_liq = df.get('NET_LIQUIDITY', pd.Series(dtype=float))
    
    if reserves.empty or net_liq.empty:
        return result
    
    # 1. 3-Month ROC (63 trading days)
    result['reserves_roc_3m'] = ((reserves / reserves.shift(63)) - 1) * 100
    result['netliq_roc_3m'] = ((net_liq / net_liq.shift(63)) - 1) * 100
    
    # 2. Spread and Z-Score (1-year rolling window = 252 days)
    spread = net_liq - reserves
    spread_mean = spread.rolling(252, min_periods=100).mean()
    spread_std = spread.rolling(252, min_periods=100).std()
    result['spread'] = spread
    result['spread_zscore'] = (spread - spread_mean) / spread_std
    
    # 3. Momentum (12-week = 60 days, 26-week = 130 days EMA)
    reserves_12w = reserves.ewm(span=60, min_periods=30).mean()
    reserves_26w = reserves.ewm(span=130, min_periods=60).mean()
    result['momentum'] = reserves_12w - reserves_26w
    
    # 4. Liquidity Coverage Ratio (LCR) as percentage
    result['lcr'] = (reserves / net_liq) * 100
    
    # 5. Acceleration (second derivative - diff of ROC)
    result['acceleration'] = result['reserves_roc_3m'].diff()
    
    # 6. Volatility of changes (30-day rolling std of daily pct_change)
    result['volatility'] = reserves.pct_change().rolling(30, min_periods=10).std() * 100
    
    return result


def calculate_us_system_metrics(df):
    """
    Calculates derived metrics for US System components:
    1. ROC 20d for Fed, RRP, TGA, Net Liquidity
    2. RRP Drain Rate (weekly) + weeks to empty
    3. TGA Z-Score (deviation from 90d mean)
    4. Fed Momentum (12w vs 26w EMA)
    5. Composite Liquidity Score
    """
    result = {}
    
    fed = df.get('FED_USD', pd.Series(dtype=float))
    rrp = df.get('RRP_USD', pd.Series(dtype=float))
    tga = df.get('TGA_USD', pd.Series(dtype=float))
    net_liq = df.get('NET_LIQUIDITY', pd.Series(dtype=float))
    
    if fed.empty or net_liq.empty:
        return result
    
    # 1. ROC 20d (monthly velocity)
    result['fed_roc_20d'] = fed.pct_change(20) * 100
    result['rrp_roc_20d'] = rrp.pct_change(20) * 100
    result['tga_roc_20d'] = tga.pct_change(20) * 100
    result['netliq_roc_20d'] = net_liq.pct_change(20) * 100
    
    # 2. RRP Drain Rate (weekly = 5 days)
    result['rrp_drain_weekly'] = rrp.diff(5)
    # Weeks to empty (latest RRP / avg weekly drain)
    weekly_drain = rrp.diff(5).rolling(4).mean().abs()  # 4-week avg drain
    result['rrp_weeks_to_empty'] = rrp / weekly_drain.replace(0, np.nan)
    
    # 3. TGA Z-Score (deviation from 90d mean)
    tga_mean = tga.rolling(90, min_periods=30).mean()
    tga_std = tga.rolling(90, min_periods=30).std()
    result['tga_zscore'] = (tga - tga_mean) / tga_std.replace(0, np.nan)
    
    # 4. Fed Momentum (12w=60d vs 26w=130d EMA)
    fed_12w = fed.ewm(span=60, min_periods=30).mean()
    fed_26w = fed.ewm(span=130, min_periods=60).mean()
    result['fed_momentum'] = fed_12w - fed_26w
    
    # 5. Composite Liquidity Score (z-scores normalized)
    def zscore_252(s):
        return (s - s.rolling(252, min_periods=100).mean()) / s.rolling(252, min_periods=100).std().replace(0, np.nan)
    
    fed_z = zscore_252(fed)
    rrp_z = zscore_252(rrp) * -1  # Inverted: high RRP = bearish
    tga_z = zscore_252(tga) * -1  # Inverted: high TGA = bearish
    result['liquidity_score'] = (fed_z + rrp_z + tga_z) / 3
    
    # 6. Individual z-scores for display
    result['fed_zscore'] = fed_z
    result['rrp_zscore'] = rrp_z
    result['tga_zscore_norm'] = tga_z
    
    # 7. Absolute $ changes (avoid % base effect issues for RRP/TGA)
    result['rrp_delta_4w'] = rrp.diff(20)   # 4 weeks = 20 trading days
    result['rrp_delta_13w'] = rrp.diff(65)  # 13 weeks = 65 trading days
    result['tga_delta_4w'] = tga.diff(20)
    result['tga_delta_13w'] = tga.diff(65)
    
    # 8. Net Liquidity Impulse (Δ in $T - most useful for trading)
    result['netliq_delta_4w'] = net_liq.diff(20)   # Δ4W NetLiq ($T)
    result['netliq_delta_13w'] = net_liq.diff(65)  # Δ13W NetLiq ($T)
    
    return result


def calculate_flow_metrics(df):
    """
    Calculates flow/impulse-based metrics (more useful for trading than levels):
    1. Impulse (Δ4w, Δ13w) for GLI, M2, NetLiq
    2. Acceleration (change in impulse)
    3. Impulse Z-scores (not level z-scores - more stable)
    4. CB contribution decomposition to ΔGLI
    """
    result = {}
    
    # Define z-score function for impulse
    def zscore_252(s):
        return (s - s.rolling(252, min_periods=100).mean()) / s.rolling(252, min_periods=100).std().replace(0, np.nan)
    
    # 1. Impulse (Δ in $T) for major aggregates
    for col in ['GLI_TOTAL', 'M2_TOTAL', 'NET_LIQUIDITY', 'CLI']:
        s = df.get(col, pd.Series(dtype=float))
        if not s.empty:
            if col == 'CLI':
                # CLI is a Z-score, so impulse is a diff of z-score
                result['cli_momentum_4w'] = s.diff(20)
                result['cli_momentum_13w'] = s.diff(65)
                continue
                
            key = col.lower().replace('_total', '')
            result[f'{key}_impulse_4w'] = s.diff(20)   # 4W = 20 days
            result[f'{key}_impulse_13w'] = s.diff(65)  # 13W = 65 days
            
            # 2. Acceleration (change in 13w impulse)
            impulse_13w = s.diff(65)
            result[f'{key}_accel'] = impulse_13w - impulse_13w.shift(65)
            
            # 3. Impulse Z-score (more stable than level z-score)
            result[f'{key}_impulse_zscore'] = zscore_252(impulse_13w)
    
    # 4. CB contribution decomposition to ΔGLI
    gli = df.get('GLI_TOTAL', pd.Series(dtype=float))
    gli_delta_13w = gli.diff(65)
    
    cb_list = ['FED', 'ECB', 'BOJ', 'PBOC', 'BOE', 'BOC', 'RBA', 'SNB', 'CBR', 'BCB', 'BOK', 'RBI', 'RBNZ', 'SR', 'BNM']
    for cb in cb_list:
        cb_col = f'{cb}_USD'
        cb_series = df.get(cb_col, pd.Series(dtype=float))
        if not cb_series.empty and not gli_delta_13w.empty:
            cb_delta = cb_series.diff(65)
            # % contribution = (CB Δ13w / GLI Δ13w) * 100
            result[f'{cb.lower()}_contrib_13w'] = (cb_delta / gli_delta_13w.replace(0, np.nan)) * 100
    
    return result


# ============================================
# STABLECOIN ANALYTICS
# ============================================

def calculate_stablecoins(df: pd.DataFrame) -> dict:
    """
    Calculates stablecoin market caps, aggregate supply, growth metrics and depeg detection.
    
    Returns dict with:
    - market_caps: Individual stablecoin market caps in billions
    - total: Aggregate stablecoin market cap
    - prices: Stablecoin prices for depeg monitoring
    - growth: 7d, 30d, 90d growth percentages
    - depeg_events: Historical depeg alerts
    - dominance: Market share percentages
    """
    result = {
        'market_caps': {},
        'prices': {},
        'total': [],
        'growth': {},
        'depeg_events': [],
        'dominance': {},
        'dates': []
    }
    
    # Map internal names to display names
    stablecoin_map = {
        'USDT_MCAP': 'USDT',
        'USDC_MCAP': 'USDC', 
        'DAI_MCAP': 'DAI',
        'TUSD_MCAP': 'TUSD',
        'USDD_MCAP': 'USDD',
        'USDP_MCAP': 'USDP',
        'USDEE_MCAP': 'USDE',
        'PYUSD_MCAP': 'PYUSD',
        'USD1W_MCAP': 'USD1W',
        'RLUSD_MCAP': 'RLUSD',
        'USDGG_MCAP': 'USDG',
        'FDUSD_MCAP': 'FDUSD',
    }
    
    price_map = {
        'USDT_PRICE': 'USDT',
        'USDC_PRICE': 'USDC', 
        'DAI_PRICE': 'DAI',
        'PYUSD_PRICE': 'PYUSD',
        'FDUSD_PRICE': 'FDUSD',
        'USDE_PRICE': 'USDE',
        'USDD_PRICE': 'USDD',
        'USD1W_PRICE': 'USD1W',
        'RLUSD_PRICE': 'RLUSD',
        'USDG_PRICE': 'USDG',
    }
    
    # Collect available stablecoin market caps (convert to billions)
    available_mcaps = {}
    for col, name in stablecoin_map.items():
        if col in df.columns and df[col].notna().sum() > 0:
            # CRYPTOCAP data is typically in raw units, convert to billions
            series = df[col].ffill() / 1e9
            available_mcaps[name] = series
            result['market_caps'][name] = series.tolist()
    
    # New: Total Crypto Market Cap for general dominance
    total_crypto_mcap = df['TOTAL_MCAP'].ffill() / 1e9 if 'TOTAL_MCAP' in df.columns else None
    if total_crypto_mcap is not None:
        result['total_crypto_mcap'] = total_crypto_mcap.tolist()
    
    # Calculate total stablecoin supply
    if available_mcaps:
        total_df = pd.DataFrame(available_mcaps)
        result['total'] = total_df.sum(axis=1, min_count=1).tolist()
        
        # Calculate dominance (market share %)
        total_series = total_df.sum(axis=1, min_count=1)
        for name, series in available_mcaps.items():
            # Local dominance (share of stablecoins)
            dominance_stables = (series / total_series.replace(0, np.nan)) * 100
            result['dominance'][name] = dominance_stables.tolist()
            
            # Global dominance (share of total crypto market)
            if total_crypto_mcap is not None:
                dominance_total = (series / total_crypto_mcap.replace(0, np.nan)) * 100
                if 'dominance_total' not in result: result['dominance_total'] = {}
                result['dominance_total'][name] = dominance_total.tolist()

        # Aggregate dominance of all stables vs. total crypto
        if total_crypto_mcap is not None:
            result['total_dominance'] = (total_series / total_crypto_mcap.replace(0, np.nan) * 100).tolist()
            
        # Add advanced aggregate metrics
        # 1. Weekly, Monthly and Quarterly ROC
        result['total_roc_7d'] = ((total_series / total_series.shift(7) - 1) * 100).tolist()
        result['total_roc_1m'] = ((total_series / total_series.shift(30) - 1) * 100).tolist()
        result['total_roc_3m'] = ((total_series / total_series.shift(90) - 1) * 100).tolist()
        
        # Z-scores for ROC metrics (normalized against historical distribution)
        roc_7d = (total_series / total_series.shift(7) - 1) * 100
        roc_1m = (total_series / total_series.shift(30) - 1) * 100
        roc_3m = (total_series / total_series.shift(90) - 1) * 100
        
        # 252-day rolling window for 7D and 1M, 504-day for 3M
        def calc_zscore(series, window):
            mean = series.rolling(window, min_periods=window//2).mean()
            std = series.rolling(window, min_periods=window//2).std()
            return ((series - mean) / std.replace(0, np.nan)).tolist()
        
        result['total_roc_7d_z'] = calc_zscore(roc_7d, 252)
        result['total_roc_1m_z'] = calc_zscore(roc_1m, 252)
        result['total_roc_3m_z'] = calc_zscore(roc_3m, 504)
        
        # Percentile ranks for ROC metrics (0-100 scale)
        def calc_percentile(series, window):
            def percentile_rank(arr):
                if len(arr) < window // 2:
                    return np.nan
                current = arr[-1]
                if np.isnan(current):
                    return np.nan
                valid = arr[~np.isnan(arr)]
                if len(valid) < window // 2:
                    return np.nan
                rank = (valid < current).sum() + 0.5 * (valid == current).sum()
                return 100 * rank / len(valid)
            return series.rolling(window, min_periods=window//2).apply(percentile_rank, raw=True).tolist()
        
        result['total_roc_7d_pct'] = calc_percentile(roc_7d, 252)
        result['total_roc_1m_pct'] = calc_percentile(roc_1m, 252)
        result['total_roc_3m_pct'] = calc_percentile(roc_3m, 504)
        
        # 2. Year-over-Year Change
        result['total_yoy'] = ((total_series / total_series.shift(365) - 1) * 100).tolist()
        
        # 3. Acceleration Z-Score (Abnormal Flows)
        # Momentum = 30-day ROC
        momentum = total_series.pct_change(30)
        # Acceleration = change in momentum over last 7 days
        accel = momentum.diff(7)
        # Rolling Z-score of acceleration (90-day window)
        rolling_mean = accel.rolling(90).mean()
        rolling_std = accel.rolling(90).std()
        # Avoid division by zero
        result['total_accel_z'] = ((accel - rolling_mean) / rolling_std.replace(0, np.nan)).tolist()
        
        # 4. Stablecoin Flow Attribution Index (SFAI)
        # Determines if stablecoin changes represent: fresh inflows, profit-taking, or buying pressure
        if total_crypto_mcap is not None:
            # Non-stablecoin crypto market cap
            non_stable_mcap = total_crypto_mcap - total_series
            
            # Changes (7-day)
            delta_stable = total_series.pct_change(7) * 100
            delta_crypto = non_stable_mcap.pct_change(7) * 100
            
            # Rolling correlation (30-day window)
            rolling_corr = delta_stable.rolling(30, min_periods=15).corr(delta_crypto)
            
            # Z-score of stablecoin change
            stable_mean = delta_stable.rolling(90, min_periods=45).mean()
            stable_std = delta_stable.rolling(90, min_periods=45).std()
            stable_z = (delta_stable - stable_mean) / stable_std.replace(0, np.nan)
            
            # SFAI Continuous Index: combines magnitude, direction, and correlation
            # Range approximately -2 to +2, but can exceed in extreme cases
            crypto_sign = np.sign(delta_crypto)
            sfai_continuous = stable_z * crypto_sign * (1 + rolling_corr.abs().fillna(0))
            result['sfai_continuous'] = sfai_continuous.tolist()
            
            # Discrete Regime Classification
            # 0 = Neutral, 1 = Fresh Inflow, 2 = Profit Taking, 3 = Buying Pressure, 4 = Capitulation
            def classify_regime(ds, dc):
                if pd.isna(ds) or pd.isna(dc):
                    return 0
                if ds > 0 and dc > 0:
                    return 1  # Fresh Inflow
                elif ds > 0 and dc < 0:
                    return 2  # Profit Taking (bearish)
                elif ds < 0 and dc > 0:
                    return 3  # Buying Pressure (bullish)
                elif ds < 0 and dc < 0:
                    return 4  # Capitulation
                else:
                    return 0  # Neutral
            
            regime = pd.Series([classify_regime(s, c) for s, c in zip(delta_stable, delta_crypto)], index=total_series.index)
            result['sfai_regime'] = regime.tolist()
            
            # Component metrics
            # Velocity: current change vs average change (normalized)
            avg_change = delta_stable.rolling(30, min_periods=15).mean().abs()
            velocity = delta_stable / avg_change.replace(0, np.nan)
            result['sfai_velocity'] = velocity.tolist()
            
            # Crypto Beta: sensitivity of stables to crypto market
            cov_rolling = delta_stable.rolling(30, min_periods=15).cov(delta_crypto)
            var_crypto = delta_crypto.rolling(30, min_periods=15).var()
            beta = cov_rolling / var_crypto.replace(0, np.nan)
            result['sfai_beta'] = beta.tolist()
        
        # Calculate growth rates
        for name, series in available_mcaps.items():
            growth = {}
            if len(series) >= 7:
                growth['7d'] = float(((series.iloc[-1] / series.iloc[-7]) - 1) * 100) if series.iloc[-7] != 0 else 0
            if len(series) >= 30:
                growth['30d'] = float(((series.iloc[-1] / series.iloc[-30]) - 1) * 100) if series.iloc[-30] != 0 else 0
            if len(series) >= 90:
                growth['90d'] = float(((series.iloc[-1] / series.iloc[-90]) - 1) * 100) if series.iloc[-90] != 0 else 0
            result['growth'][name] = growth
    
    # Collect stablecoin prices for depeg detection
    depeg_threshold = 0.01  # 1% deviation from $1.00
    for col, name in price_map.items():
        if col in df.columns and df[col].notna().sum() > 0:
            price_series = df[col].ffill()
            high_col = f"{col}_HIGH"
            low_col = f"{col}_LOW"
            
            # Use intra-day extremes for depeg detection if available
            if high_col in df.columns and low_col in df.columns:
                high_series = df[high_col].ffill()
                low_series = df[low_col].ffill()
                # Determine max deviation (up or down)
                dev_up = high_series - 1.0
                dev_down = 1.0 - low_series
                extreme_dev = pd.Series(np.where(dev_up > dev_down, dev_up, -dev_down), index=df.index)
            else:
                extreme_dev = price_series - 1.0
                
            result['prices'][name] = price_series.tolist()
            
            # Detect depeg events (price deviation > threshold)
            deviations = abs(extreme_dev)
            depeg_mask = deviations > depeg_threshold
            if depeg_mask.any():
                depeg_dates = extreme_dev.index[depeg_mask]
                for date in depeg_dates:
                    result['depeg_events'].append({
                        'date': date.strftime('%Y-%m-%d'),
                        'stablecoin': name,
                        'price': float(1.0 + extreme_dev.loc[date]), # Extreme price reached intra-day
                        'deviation_pct': float(extreme_dev.loc[date] * 100)
                    })
    
    # Use common dates from the available data
    if available_mcaps:
        result['dates'] = df.index.strftime('%Y-%m-%d').tolist()
    
    # Sort depeg events by date (ascending - natural order for time series)
    result['depeg_events'].sort(key=lambda x: x['date'], reverse=False)
    
    return result


# ============================================
# PERCENTILE CALCULATIONS
# ============================================

def rolling_percentile(series: pd.Series, window: int = 252*5, min_periods: int = 126) -> pd.Series:
    """
    Calcula el percentil rolling de cada valor respecto a su ventana histórica.
    
    Retorna valores entre 0 y 100.
    - 0 = mínimo histórico de la ventana
    - 50 = mediana
    - 100 = máximo histórico de la ventana
    
    Args:
        series: Serie de datos
        window: Ventana en días (default 5 años = 252*5 = 1260 días)
        min_periods: Mínimo de observaciones requeridas
    """
    def percentile_rank(arr):
        if len(arr) < min_periods:
            return np.nan
        current = arr[-1]
        if np.isnan(current):
            return np.nan
        # Rank del valor actual dentro de la ventana (excluyendo NaN)
        valid = arr[~np.isnan(arr)]
        if len(valid) < min_periods:
            return np.nan
        rank = (valid < current).sum() + 0.5 * (valid == current).sum()
        return 100 * rank / len(valid)
    
    return series.rolling(window, min_periods=min_periods).apply(percentile_rank, raw=True)


def compute_signal_metrics(df: pd.DataFrame, cli_df: pd.DataFrame, window: int = 1260) -> dict:
    """
    Calcula métricas de señal para todas las series relevantes.
    Retorna dict con percentiles, z-scores, y señales.
    """
    metrics = {}
    
    def clean_for_json_series(s):
        if s is None: return []
        return [float(x) if np.isfinite(x) else None for x in s]

    # Combine relevant columns from both dataframes
    all_data = pd.DataFrame(index=df.index)
    
    # Map friendly keys to columns in df or cli_df
    series_config = {
        'cli': {
            'source': cli_df,
            'col': 'CLI',
            'invert': False,  # Positivo = bueno
            'bullish_pct': 70,
            'bearish_pct': 30,
        },
        'hy_spread': {
            'source': df,
            'col': 'HY_SPREAD',
            'invert': True,   # Spread bajo = bueno, así que invertimos
            'bullish_pct': 30,  # Percentil bajo del spread = bullish
            'bearish_pct': 75,  # Percentil alto del spread = bearish
        },
        'ig_spread': {
            'source': df,
            'col': 'IG_SPREAD',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 75,
        },
        'vix': {
            'source': df,
            'col': 'VIX',
            'invert': True,   # VIX bajo = bueno
            'bullish_pct': 30,
            'bearish_pct': 85,  # Asimétrico - solo panic extremo es bearish
        },
        'tips_real_rate': {
            'source': df,
            'col': 'TIPS_REAL_RATE',
            'invert': True,   # Real rate bajo = más fácil = bueno
            'bullish_pct': 30,
            'bearish_pct': 80,
        },
        'tips_breakeven': {
            'source': df,
            'col': 'TIPS_BREAKEVEN',
            'invert': False,
            'bullish_pct': 40,  # Reflación moderada es OK
            'bearish_pct': 20,  # Muy bajo = deflación scare
        },
        'move': {
            'source': df,
            'col': 'MOVE',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 85,
        },
        'fx_vol': {
            'source': df,
            'col': 'FX_VOL',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 85,
        },
        'nfp': {
            'source': df,
            'col': 'NFP_CHANGE', # We'll create this helper in-loop
            'invert': False,
            'bullish_pct': 70,
            'bearish_pct': 30,
        },
        'jolts': {
            'source': df,
            'col': 'JOLTS',
            'invert': False,
            'bullish_pct': 70,
            'bearish_pct': 30,
        },
        'cli_gli_divergence': {
            'source': df,
            'col': 'CLI_GLI_DIVERGENCE',
            'invert': False,
            'bullish_pct': 60,
            'bearish_pct': 40,
        },
        'treasury_10y': {
            'source': df,
            'col': 'TREASURY_10Y_YIELD',
            'invert': True,  # Lower yields = easier conditions = bullish
            'bullish_pct': 30,
            'bearish_pct': 80,
        },
        'treasury_2y': {
            'source': df,
            'col': 'TREASURY_2Y_YIELD',
            'invert': True,  # Lower yields = easier conditions = bullish
            'bullish_pct': 30,
            'bearish_pct': 80,
        },
        'yield_curve': {
            'source': df,
            'col': 'YIELD_CURVE',
            'invert': False, # Stealth indicator: usually flattening = late cycle
            'bullish_pct': 60,
            'bearish_pct': 40,
        },
        'nfci_credit': {
            'source': df,
            'col': 'NFCI_CREDIT',
            'invert': True,  # Negative = loose = bullish
            'bullish_pct': 30,
            'bearish_pct': 70,
        },
        'nfci_risk': {
            'source': df,
            'col': 'NFCI_RISK',
            'invert': True,  # Negative = lower risk = bullish
            'bullish_pct': 30,
            'bearish_pct': 70,
        },
        'lending': {
            'source': df,
            'col': 'LENDING_STD',
            'invert': True,  # Negative = loosening = bullish
            'bullish_pct': 30,
            'bearish_pct': 70,
        },
        # NEW: Financial Stress Indices
        'st_louis_stress': {
            'source': df,
            'col': 'ST_LOUIS_STRESS',
            'invert': True,  # Lower stress = bullish
            'bullish_pct': 30,
            'bearish_pct': 70,
        },
        'kansas_city_stress': {
            'source': df,
            'col': 'KANSAS_CITY_STRESS',
            'invert': True,  # Lower stress = bullish
            'bullish_pct': 30,
            'bearish_pct': 70,
        },
        # NEW: Corporate Bond Yields
        'baa_yield': {
            'source': df,
            'col': 'BAA_YIELD',
            'invert': True,  # Lower yields = easier credit = bullish
            'bullish_pct': 30,
            'bearish_pct': 75,
        },
        'aaa_yield': {
            'source': df,
            'col': 'AAA_YIELD',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 75,
        },
        # NEW: 30Y and 5Y Treasury Yields
        'treasury_30y': {
            'source': df,
            'col': 'TREASURY_30Y_YIELD',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 80,
        },
        'treasury_5y': {
            'source': df,
            'col': 'TREASURY_5Y_YIELD',
            'invert': True,
            'bullish_pct': 30,
            'bearish_pct': 80,
        },
        # NEW: Additional Yield Curves
        'yield_curve_30y_10y': {
            'source': df,
            'col': 'YIELD_CURVE_30Y_10Y',
            'invert': False,  # Steepening = bullish (risk-on)
            'bullish_pct': 60,
            'bearish_pct': 30,  # Inversion = bearish
        },
        'yield_curve_30y_2y': {
            'source': df,
            'col': 'YIELD_CURVE_30Y_2Y',
            'invert': False,
            'bullish_pct': 60,
            'bearish_pct': 30,
        },
        # NEW: BAA-AAA Spread (Credit Quality Spread)
        'baa_aaa_spread': {
            'source': df,
            'col': 'BAA_AAA_SPREAD',
            'invert': True,  # Wider spread = more risk aversion = bearish
            'bullish_pct': 30,
            'bearish_pct': 75,
        },
    }

    # Preparation: Add computed columns to source df if needed
    if 'NFP' in df.columns:
        df['NFP_CHANGE'] = df['NFP'].diff(22)  # 1 month change
    
    # Yield Curve calculations
    if 'TREASURY_10Y_YIELD' in df.columns and 'TREASURY_2Y_YIELD' in df.columns:
        df['YIELD_CURVE'] = df['TREASURY_10Y_YIELD'] - df['TREASURY_2Y_YIELD']
    if 'TREASURY_30Y_YIELD' in df.columns and 'TREASURY_10Y_YIELD' in df.columns:
        df['YIELD_CURVE_30Y_10Y'] = df['TREASURY_30Y_YIELD'] - df['TREASURY_10Y_YIELD']
    if 'TREASURY_30Y_YIELD' in df.columns and 'TREASURY_2Y_YIELD' in df.columns:
        df['YIELD_CURVE_30Y_2Y'] = df['TREASURY_30Y_YIELD'] - df['TREASURY_2Y_YIELD']
    
    # Corporate spread calculation
    if 'BAA_YIELD' in df.columns and 'AAA_YIELD' in df.columns:
        df['BAA_AAA_SPREAD'] = df['BAA_YIELD'] - df['AAA_YIELD']

    
    for key, config in series_config.items():
        source = config['source']
        col = config['col']
        if col not in source.columns:
            continue
            
        series = source[col].astype(float)
        
        # Percentil rolling
        pct = rolling_percentile(series, window=window)
        
        # Z-score rolling (para compatibilidad)
        mean = series.rolling(window, min_periods=126).mean()
        std = series.rolling(window, min_periods=126).std().replace(0, np.nan)
        zscore = (series - mean) / std
        
        # Momentum (cambio en 63 días ~ 3 meses)
        momentum = series.diff(63)
        # Momentum relative to its own history
        momentum_pct = rolling_percentile(momentum, window=window)
        
        # Señal basada en percentil
        signals = []
        for val in pct:
            if np.isnan(val):
                signals.append('neutral')
            elif config['invert']:
                # Para series invertidas (spread, VIX): bajo = bullish
                if val <= config['bullish_pct']: signals.append('bullish')
                elif val >= config['bearish_pct']: signals.append('bearish')
                else: signals.append('neutral')
            else:
                # Para series normales: alto = bullish
                if val >= config['bullish_pct']: signals.append('bullish')
                elif val <= config['bearish_pct']: signals.append('bearish')
                else: signals.append('neutral')
        
        metrics[key] = {
            'raw': clean_for_json_series(series),
            'percentile': clean_for_json_series(pct),
            'zscore': clean_for_json_series(zscore),
            'momentum_pct': clean_for_json_series(momentum_pct),
            'signal_series': signals,
            'latest': {
                'value': float(series.iloc[-1]) if not np.isnan(series.iloc[-1]) else None,
                'percentile': float(pct.iloc[-1]) if not np.isnan(pct.iloc[-1]) else None,
                'zscore': float(zscore.iloc[-1]) if not np.isnan(zscore.iloc[-1]) else None,
                'state': signals[-1] if len(signals) > 0 else 'neutral',
            }
        }
    
    # Composite TIPS signal
    if 'TIPS_REAL_RATE' in df.columns and 'TIPS_BREAKEVEN' in df.columns:
        rr = df['TIPS_REAL_RATE'].astype(float)
        be = df['TIPS_BREAKEVEN'].astype(float)
        
        # Simple rolling stats for the composite
        rr_z = (rr - rr.rolling(window, min_periods=126).mean()) / rr.rolling(window, min_periods=126).std()
        be_z = (be - be.rolling(window, min_periods=126).mean()) / be.rolling(window, min_periods=126).std()
        
        # State logic matches front-end (simplified)
        state = 'neutral'
        if be.iloc[-1] > be.rolling(252, min_periods=126).mean().iloc[-1] * 1.1:
            state = 'bullish'
        if rr.iloc[-1] > rr.rolling(252, min_periods=126).mean().iloc[-1] + 0.5:
            state = 'bearish'
            
        metrics['tips'] = {
            'percentile': clean_for_json_series(rolling_percentile(rr, window=window)),
            'zscore': clean_for_json_series(rr_z),
            'latest': {
                'value': float(rr.iloc[-1]),
                'valueBE': float(be.iloc[-1]),
                'percentile': float(rolling_percentile(rr, window=window).iloc[-1]),
                'zscore': float(rr_z.iloc[-1]),
                'state': state
            }
        }
    
    return metrics


def calculate_signals(df, cli_df):
    """
    Calculates operational signals using unified signal_config.
    
    ARCHITECTURE:
    - All thresholds are defined in signal_config.py (single source of truth)
    - Key names are standardized: hy_spread, ig_spread, repo_stress, etc.
    - Each signal includes: state, value, reason, confidence
    
    SIGN CONVENTION: Higher values = better/easier conditions (matching CLI).
    """
    signals = {}
    
    def get_latest(series):
        if series is None or series.empty: return None
        valid = series.dropna()
        if valid.empty: return None
        val = valid.iloc[-1]
        return float(val) if np.isfinite(val) else None

    def get_momentum(series, window=20):
        if series is None or len(series) < window + 1: return 0
        valid = series.dropna()
        if len(valid) < window + 1: return 0
        return float(valid.iloc[-1] - valid.iloc[-window-1])

    # 1. CLI Signal (with momentum confirmation)
    cli_val = get_latest(cli_df['CLI'])
    cli_mom = get_momentum(cli_df['CLI'], 20)
    
    if cli_val is not None:
        result = compute_signal('cli', cli_val, momentum=cli_mom)
        signals['cli'] = {
            "state": result.state, 
            "value": round(cli_val, 2), 
            "momentum": round(cli_mom, 3),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 2. HY Spread (standardized key name: hy_spread)
    hy_z = get_latest(cli_df.get('HY_SPREAD_Z'))
    if hy_z is not None:
        result = compute_signal('hy_spread', hy_z)
        signals['hy_spread'] = {
            "state": result.state, 
            "value": round(hy_z, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 3. IG Spread (standardized key name: ig_spread)
    ig_z = get_latest(cli_df.get('IG_SPREAD_Z'))
    if ig_z is not None:
        result = compute_signal('ig_spread', ig_z)
        signals['ig_spread'] = {
            "state": result.state, 
            "value": round(ig_z, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 4. NFCI Credit (already inverted in NFCI_CREDIT_Z: higher is better)
    nfcic = get_latest(cli_df.get('NFCI_CREDIT_Z'))
    if nfcic is not None:
        result = compute_signal('nfci_credit', nfcic)
        signals['nfci_credit'] = {
            "state": result.state, 
            "value": round(nfcic, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 5. NFCI Risk (Negated)
    nfcir = get_latest(cli_df.get('NFCI_RISK_Z'))
    if nfcir is not None:
        result = compute_signal('nfci_risk', nfcir)
        signals['nfci_risk'] = {
            "state": result.state, 
            "value": round(nfcir, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 6. Lending Standards (Negated)
    lending = get_latest(cli_df.get('LENDING_STD_Z'))
    if lending is not None:
        result = compute_signal('lending', lending)
        signals['lending'] = {
            "state": result.state, 
            "value": round(lending, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 7. VIX (Negated: higher = lower VIX)
    vix_z = get_latest(cli_df.get('VIX_Z'))
    if vix_z is not None:
        result = compute_signal('vix', vix_z)
        signals['vix'] = {
            "state": result.state, 
            "value": round(vix_z, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 8. TIPS Composite (2D grid: BE vs RR)
    rr = df.get('TIPS_REAL_RATE', pd.Series(dtype=float))
    be = df.get('TIPS_BREAKEVEN', pd.Series(dtype=float))
    
    rr_val = get_latest(rr)
    be_val = get_latest(be)
    
    if rr_val is not None and be_val is not None:
        result = compute_signal('tips', 0, be_value=be_val, rr_value=rr_val)
        signals['tips'] = {
            "state": result.state,
            "label": result.label,
            "be_value": round(be_val, 3),
            "rr_value": round(rr_val, 3),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 9. Repo Stress (UNIFIED thresholds from signal_config)
    sofr = df.get('SOFR')
    iorb = df.get('IORB')
    srf_usage = df.get('SRF_USAGE', pd.Series(dtype=float))
    
    if sofr is not None and iorb is not None:
        spread = get_latest(sofr - iorb)
        srf_active = get_latest(srf_usage) is not None and get_latest(srf_usage) > 0
        
        if spread is not None:
            # Convert to basis points for threshold comparison
            spread_bps = spread * 100 if abs(spread) < 1 else spread
            
            # Use 'repo' as canonical key (not 'repo_stress')
            result = compute_signal('repo', spread_bps, srf_usage=srf_active)
            signals['repo'] = {
                "state": result.state,
                "value": round(spread_bps, 2),
                "reason": result.reason,
                "confidence": round(result.confidence, 2),
                "srf_active": srf_active
            }
            # Backward-compat alias: repo_stress -> repo
            signals['repo_stress'] = signals['repo']

    # 10. MOVE Index (Bond Volatility)
    move_val = get_latest(df.get('MOVE', pd.Series(dtype=float)))
    if move_val is not None:
        result = compute_signal('move', move_val)
        signals['move'] = {
            "state": result.state,
            "value": round(move_val, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 11. FX Volatility (DXY Realized Vol)
    fx_vol_val = get_latest(df.get('FX_VOL', pd.Series(dtype=float)))
    if fx_vol_val is not None:
        result = compute_signal('fx_vol', fx_vol_val)
        signals['fx_vol'] = {
            "state": result.state,
            "value": round(fx_vol_val, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    # 12. Yield Curve (10Y-2Y spread in bps)
    y10 = get_latest(df.get('TREASURY_10Y_YIELD', pd.Series(dtype=float)))
    y2 = get_latest(df.get('TREASURY_2Y_YIELD', pd.Series(dtype=float)))
    if y10 is not None and y2 is not None:
        spread_bps = (y10 - y2) * 100  # Convert % to bps
        result = compute_signal('yield_curve', spread_bps)
        signals['yield_curve'] = {
            "state": result.state,
            "value": round(spread_bps, 2),
            "reason": result.reason,
            "confidence": round(result.confidence, 2)
        }

    return signals




def calculate_macro_regime(
    df: pd.DataFrame,
    impulse_days: int = 65,      # ~13 weeks (trading days)
    accel_days: int = 65,
    z_window: int = 252,         # ~1 year (trading days)
    min_periods: int = 100,
    score_clip: float = 3.0,
) -> Dict[str, pd.Series]:
    """
    Multi-factor macro regime:
      - Liquidity (flows): GLI, US Net Liquidity, Global M2 (impulse + accel)
      - Credit: CLI level + momentum
      - Brakes / plumbing: real-rate shock (TIPS), repo stress (SOFR-IORB),
        stress de reservas vs netliq (spread zscore), + breadth/concentration CB

    Requires (if present, uses; if missing, degrades gracefully):
      GLI_TOTAL, NET_LIQUIDITY, M2_TOTAL, CLI,
      BANK_RESERVES, TIPS_REAL_RATE, SOFR, IORB,
      and optionally {FED,ECB,BOJ,PBOC,BOE,BOC,RBA,SNB,CBR,BCB,BOK,RBI,RBNZ,SR,BNM}_USD
    """

    idx = df.index
    out: Dict[str, pd.Series] = {}

    def _zscore_roll(s: pd.Series) -> pd.Series:
        s = s.astype(float).replace([np.inf, -np.inf], np.nan)
        mu = s.rolling(z_window, min_periods=min_periods).mean()
        sd = s.rolling(z_window, min_periods=min_periods).std().replace(0, np.nan)
        return (s - mu) / sd

    # ---------- Core series ----------
    gli = df.get("GLI_TOTAL", pd.Series(index=idx, dtype=float))
    netliq = df.get("NET_LIQUIDITY", pd.Series(index=idx, dtype=float))
    m2 = df.get("M2_TOTAL", pd.Series(index=idx, dtype=float))
    cli = df.get("CLI", pd.Series(index=idx, dtype=float))

    # ---------- Flow / impulse (Δ13W) ----------
    gli_imp = gli.diff(impulse_days)
    netliq_imp = netliq.diff(impulse_days)
    m2_imp = m2.diff(impulse_days)

    # Acceleration (change in impulse)
    gli_accel = gli_imp - gli_imp.shift(accel_days)
    netliq_accel = netliq_imp - netliq_imp.shift(accel_days)

    # Credit momentum (13W for "regime")
    cli_mom = cli.diff(impulse_days)

    # ---------- Breadth / Concentration (CB diffusion + HHI) ----------
    cb_list = ["FED", "ECB", "BOJ", "PBOC", "BOE", "BOC", "RBA", "SNB", "CBR", "BCB", "BOK", "RBI", "RBNZ", "SR", "BNM"]
    cb_cols = [f"{cb}_USD" for cb in cb_list if f"{cb}_USD" in df.columns]

    if cb_cols:
        cb_deltas = df[cb_cols].astype(float).diff(impulse_days)
        # Diffusion: % CBs with Δ13W > 0
        denom = cb_deltas.notna().sum(axis=1).replace(0, np.nan)
        cb_diffusion = (cb_deltas > 0).sum(axis=1) / denom

        # Concentration (HHI) over absolute contributions
        abs_d = cb_deltas.abs()
        abs_sum = abs_d.sum(axis=1).replace(0, np.nan)
        shares = abs_d.div(abs_sum, axis=0)
        cb_hhi = (shares.pow(2)).sum(axis=1)

    else:
        cb_diffusion = pd.Series(np.nan, index=idx)
        cb_hhi = pd.Series(np.nan, index=idx)

    # ---------- Brakes / plumbing ----------
    tips_real = df.get("TIPS_REAL_RATE", pd.Series(index=idx, dtype=float))
    real_rate_shock_4w = tips_real.diff(20)  # ~4 weeks

    sofr = df.get("SOFR", pd.Series(index=idx, dtype=float))
    iorb = df.get("IORB", pd.Series(index=idx, dtype=float))
    repo_stress = sofr - iorb  # >0 typically indicates funding tension

    reserves = df.get("BANK_RESERVES", pd.Series(index=idx, dtype=float))
    # Spread zscore: (NetLiq - Reserves) zscore
    spread = (netliq - reserves).astype(float)
    spread_mu = spread.rolling(z_window, min_periods=min_periods).mean()
    spread_sd = spread.rolling(z_window, min_periods=min_periods).std().replace(0, np.nan)
    reserves_spread_z = (spread - spread_mu) / spread_sd

    # ---------- Z features ----------
    z_gli_imp = _zscore_roll(gli_imp)
    z_netliq_imp = _zscore_roll(netliq_imp)
    z_m2_imp = _zscore_roll(m2_imp)

    z_cli = _zscore_roll(cli)
    z_cli_mom = _zscore_roll(cli_mom)

    z_diffusion = _zscore_roll(cb_diffusion)          # breadth (↑ better)
    z_hhi = _zscore_roll(cb_hhi)                      # concentration (↑ worse)

    z_real_shock = _zscore_roll(real_rate_shock_4w)   # ↑ worse
    z_repo = _zscore_roll(repo_stress)                # ↑ worse

    # ---------- Component blocks (Robust) ----------
    # Liquidity: flows + breadth - concentration
    # Liquidity: GLI + Net Liq + M2 + Breadth
    liquidity_comps = [
        (z_gli_imp, 0.35),
        (z_netliq_imp, 0.35),
        (z_m2_imp, 0.20),
        (z_diffusion, 0.10),
        (z_hhi, -0.10)
    ]
    liquidity_z = weighted_sum_with_renorm(liquidity_comps, idx)

    # Credit: level + momentum
    credit_comps = [
        (z_cli, 0.60),
        (z_cli_mom, 0.40)
    ]
    credit_z = weighted_sum_with_renorm(credit_comps, idx)

    # Brakes: real rates + repo + stress reserves
    brakes_comps = [
        (z_real_shock, -0.35),
        (z_repo, -0.25),
        (reserves_spread_z, -0.25)
    ]
    brakes_z = weighted_sum_with_renorm(brakes_comps, idx)

    total_z = (liquidity_z + credit_z + brakes_z).replace([np.inf, -np.inf], np.nan)

    # ---------- Score 0-100 ----------
    score = 50.0 + 15.0 * np.clip(total_z, -score_clip, score_clip)
    score = score.fillna(50.0)

    # ---------- Regime code ----------
    #  1 = expansion (risk-on), -1 = contraction (risk-off), 0 = mixed/neutral
    bull = (total_z > 0.75) & (liquidity_z > 0) & (credit_z > -0.25)
    bear = (total_z < -0.75) & (liquidity_z < 0) & (credit_z < 0.25)
    regime_code = pd.Series(np.where(bull, 1, np.where(bear, -1, 0)), index=idx).astype(float)

    # "Transition" flag: strong acceleration (regime changing)
    # Suppress warning for all-NaN slices (expected for early dates with insufficient rolling data)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        accel_strength = np.nanmax(
            np.vstack([_zscore_roll(gli_accel).abs().values, _zscore_roll(netliq_accel).abs().values]),
            axis=0
        )
    transition = pd.Series((accel_strength > 1.5).astype(float), index=idx)

    # ---------- CLI-GLI Divergence ----------
    # Normalized difference to highlight decoupling (Positive = Credit leads Liquidity)
    out["cli_gli_divergence"] = (credit_z - liquidity_z)

    # ---------- Output ----------
    out["score"] = score
    out["regime_code"] = regime_code
    out["transition"] = transition

    # Diagnostics (useful for debug + charts)
    out["total_z"] = total_z
    out["liquidity_z"] = liquidity_z
    out["credit_z"] = credit_z
    out["brakes_z"] = brakes_z

    out["gli_impulse_13w"] = gli_imp
    out["netliq_impulse_13w"] = netliq_imp
    out["m2_impulse_13w"] = m2_imp

    out["cb_diffusion_13w"] = cb_diffusion
    out["cb_hhi_13w"] = cb_hhi

    out["real_rate_shock_4w"] = real_rate_shock_4w
    out["repo_stress"] = repo_stress
    out["reserves_spread_z"] = reserves_spread_z

    return out


def calculate_macro_regime_weekly(df: pd.DataFrame, **kwargs):
    """
    Calculates macro regime on weekly frequency (Friday close) 
    to reduce micro-noise and autocorrelation artifacts.
    Then forward-fills to daily for plotting.
    """
    # 1. Resample to weekly
    df_w = df.resample('W-FRI').last()
    
    # 2. Adjust impulse/accel parameters for weekly units
    # Default daily: impulse=65d (~13w), accel=65d, z_window=252d (~1y)
    w_kwargs = kwargs.copy()
    w_kwargs['impulse_days'] = w_kwargs.get('impulse_days', 65) // 5
    w_kwargs['accel_days'] = w_kwargs.get('accel_days', 65) // 5
    w_kwargs['z_window'] = w_kwargs.get('z_window', 252) // 5
    w_kwargs['min_periods'] = w_kwargs.get('min_periods', 100) // 5

    # 3. Calculate on weekly
    reg_w = calculate_macro_regime(df_w, **w_kwargs)
    
    # 4. Forward-fill back to daily index for visualization
    res = {}
    for key, series in reg_w.items():
        res[key] = series.reindex(df.index, method='ffill')
        
    return res


def calculate_btc_fair_value(df_t):
    """
    Calculates dual Bitcoin fair value models:
    1. Standard Quant (Macro Only)
    2. Adoption-Adjusted (Macro + Power Law/Log-Time)
    """
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    result = pd.DataFrame(index=df_t.index)
    
    if 'BTC' not in df_t.columns:
        return result
    
    btc_series = df_t['BTC'].dropna()
    if len(btc_series) < 100:
        return result
    
    # 1. Base Macro Features
    # NOTE: VIX removed to avoid multicollinearity - CLI already includes VIX_Z as component
    raw_features = pd.DataFrame({
        'GLI_TOTAL': df_t.get('GLI_TOTAL', 0).shift(45),
        'CLI': df_t.get('CLI', 0).shift(14),
        'NET_LIQ': df_t.get('NET_LIQUIDITY', 0).shift(30),
    })

    # 2. Adoption Feature (Log Days since Genesis 2009-01-03)
    genesis_date = pd.Timestamp('2009-01-03')
    days_since_genesis = (df_t.index - genesis_date).days
    # Avoid log(0)
    raw_features['ADOPTION'] = np.log(np.maximum(days_since_genesis, 1))

    btc_start = btc_series.index.min()
    valid_mask = (df_t.index >= btc_start)
    
    # Training Data
    y_train_raw = btc_series
    X_train_raw = raw_features.loc[y_train_raw.index]
    train_data = pd.concat([X_train_raw, np.log(y_train_raw)], axis=1).dropna()
    
    if len(train_data) < 100:
        return result
        
    y_train = train_data['BTC'] # log_btc
    scaler = StandardScaler()

    # --- MODEL 1: MACRO ONLY ---
    X_m_train = train_data[['GLI_TOTAL', 'CLI', 'NET_LIQ']]
    X_m_scaled = scaler.fit_transform(X_m_train)
    model_m = LinearRegression()
    model_m.fit(X_m_scaled, y_train.values)
    
    X_m_full = raw_features[['GLI_TOTAL', 'CLI', 'NET_LIQ']].loc[valid_mask].ffill()
    X_m_full_scaled = scaler.transform(X_m_full)
    log_pred_m = pd.Series(model_m.predict(X_m_full_scaled), index=X_m_full.index)
    
    # --- MODEL 2: ADOPTION ADJUSTED (Macro + Time) ---
    X_a_train = train_data[['GLI_TOTAL', 'CLI', 'NET_LIQ', 'ADOPTION']]
    X_a_scaled = scaler.fit_transform(X_a_train)
    # Use Ridge to prevent multicollinearity between Time and Liquidity
    model_a = Ridge(alpha=1.0)
    model_a.fit(X_a_scaled, y_train.values)
    
    X_a_full = raw_features[['GLI_TOTAL', 'CLI', 'NET_LIQ', 'ADOPTION']].loc[valid_mask].ffill()
    X_a_full_scaled = scaler.transform(X_a_full)
    log_pred_a = pd.Series(model_a.predict(X_a_full_scaled), index=X_a_full.index)

    # Helper to calculate bands and metrics
    def build_model_df(log_pred, btc_actual):
        pred_fair = np.exp(log_pred)
        log_actual = np.log(btc_actual.dropna())
        common_idx = log_actual.index.intersection(log_pred.index)
        std_log = (log_actual[common_idx] - log_pred[common_idx]).std()
        
        df = pd.DataFrame(index=log_pred.index)
        df['FAIR_VALUE'] = pred_fair
        df['UPPER_1SD'] = pred_fair * np.exp(std_log)
        df['LOWER_1SD'] = pred_fair * np.exp(-std_log)
        df['UPPER_2SD'] = pred_fair * np.exp(2 * std_log)
        df['LOWER_2SD'] = pred_fair * np.exp(-2 * std_log)
        df['DEVIATION_PCT'] = (btc_actual - pred_fair) / pred_fair * 100
        df['DEVIATION_ZSCORE'] = (np.log(btc_actual) - log_pred) / std_log
        return df

    res_m = build_model_df(log_pred_m, df_t['BTC']).rename(columns=lambda x: f"BTC_{x}")
    res_a = build_model_df(log_pred_a, df_t['BTC']).rename(columns=lambda x: f"ADJ_BTC_{x}")

    result_btc = pd.concat([res_m, res_a], axis=1)
    result_btc['BTC_ACTUAL'] = df_t['BTC']
    
    return result.join(result_btc, how='left')

def calculate_btc_fair_value_v2(df_t):
    """
    QUANT V2: Enhanced Bitcoin Fair Value Model
    
    Key Improvements:
    1. Weekly frequency (W-FRI) to avoid ffill autocorrelation
    2. Models Δlog(BTC) returns instead of log(BTC) levels (avoids spurious regression)
    3. ElasticNet with multiple lags (1-8 weeks) for automatic feature selection
    4. GLI as PCA factor (not sum) to handle colinearity
    5. Rolling 52-week volatility for adaptive bands
    6. Walk-forward cross-validation metrics
    """
    from sklearn.linear_model import ElasticNetCV
    from sklearn.preprocessing import StandardScaler, RobustScaler
    from sklearn.decomposition import PCA
    import numpy as np
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    
    result = {}
    
    if 'BTC' not in df_t.columns:
        return result
    
    # 1. Resample to Weekly (Friday)
    df_weekly = df_t.resample('W-FRI').last().dropna(how='all')
    
    btc_series = df_weekly['BTC'].dropna()
    if len(btc_series) < 100:
        return result
    
    # 2. Calculate Δlog returns (weekly)
    btc_log_ret = np.log(btc_series).diff()
    
    # 3. Build GLI PCA Factor
    gli_cols = ['FED_USD', 'ECB_USD', 'BOJ_USD', 'BOE_USD', 'PBOC_USD']
    gli_available = [c for c in gli_cols if c in df_weekly.columns]
    
    if len(gli_available) >= 3:
        gli_df = df_weekly[gli_available].ffill().bfill()
        # Calculate Δlog for each CB (Protected against 0 and inf)
        gli_dlog = np.log(gli_df.replace(0, np.nan)).diff()
        gli_dlog = gli_dlog.replace([np.inf, -np.inf], np.nan)
        gli_dlog_clean = gli_dlog.dropna()
        
        if len(gli_dlog_clean) > 50:
            scaler_pca = RobustScaler()
            gli_scaled = scaler_pca.fit_transform(gli_dlog_clean)
            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(gli_scaled)
            gli_factor = pd.Series(pca_result[:, 0], index=gli_dlog_clean.index, name='GLI_FACTOR')
        else:
            gli_factor = pd.Series(dtype=float)
    else:
        gli_factor = pd.Series(dtype=float)
    
    # 4. Prepare Features with Multiple Lags (1-8 weeks)
    feature_df = pd.DataFrame(index=df_weekly.index)
    
    # CLI changes
    if 'CLI' in df_weekly.columns:
        cli_series = df_weekly['CLI'].ffill()
        cli_dlog = cli_series.diff()
        for lag in range(1, 9):
            feature_df[f'CLI_L{lag}'] = cli_dlog.shift(lag)
    
    # GLI Factor lags
    if not gli_factor.empty:
        for lag in range(1, 9):
            feature_df[f'GLI_L{lag}'] = gli_factor.shift(lag)
    
    # VIX changes
    if 'VIX' in df_weekly.columns:
        vix_series = df_weekly['VIX'].ffill()
        vix_diff = vix_series.diff()
        for lag in range(1, 5):
            feature_df[f'VIX_L{lag}'] = vix_diff.shift(lag)
    
    # Net Liquidity changes
    if 'NET_LIQUIDITY' in df_weekly.columns:
        netliq = df_weekly['NET_LIQUIDITY'].ffill()
        netliq_dlog = np.log(netliq.replace(0, np.nan)).diff()
        for lag in range(1, 9):
            feature_df[f'NETLIQ_L{lag}'] = netliq_dlog.shift(lag)
    
    # 5. Align data for training - all on weekly index
    btc_start = btc_series.index.min()
    common_idx = btc_log_ret.index.intersection(feature_df.index)
    common_idx = common_idx[common_idx >= btc_start]
    
    y = btc_log_ret.loc[common_idx]
    X = feature_df.loc[common_idx]
    
    # Clean dataset
    train_data = pd.concat([X, y.rename('TARGET')], axis=1).dropna()
    
    if len(train_data) < 100:
        return result
    
    y_train = train_data['TARGET']
    X_train = train_data.drop('TARGET', axis=1)
    
    # 6. ElasticNet with CV for automatic lag selection
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_train)
    
    model = ElasticNetCV(
        l1_ratio=[0.1, 0.5, 0.7, 0.9, 0.95],
        alphas=np.logspace(-4, 0, 20),
        cv=5,
        max_iter=5000,
        random_state=42
    )
    model.fit(X_scaled, y_train)
    
    # 7. Generate predictions using the same common index
    X_full = feature_df.loc[common_idx].ffill().bfill()
    X_full_scaled = scaler.transform(X_full)
    pred_returns = pd.Series(model.predict(X_full_scaled), index=X_full.index)
    
    # 8. Reconstruct log price from cumulative returns
    log_btc_actual = np.log(btc_series)
    first_log = log_btc_actual.iloc[0]
    log_pred_cumulative = pred_returns.cumsum() + first_log
    fair_value = np.exp(log_pred_cumulative)
    
    # 9. Rolling 52-week volatility bands
    residuals = log_btc_actual.loc[fair_value.index] - log_pred_cumulative.loc[log_btc_actual.index.intersection(fair_value.index)]
    rolling_std = residuals.rolling(window=52, min_periods=20).std().ffill().bfill()
    
    # Use median std as fallback for early periods
    median_std = rolling_std.median()
    rolling_std = rolling_std.fillna(median_std)
    
    upper_1sd = fair_value * np.exp(rolling_std)
    lower_1sd = fair_value * np.exp(-rolling_std)
    upper_2sd = fair_value * np.exp(2 * rolling_std)
    lower_2sd = fair_value * np.exp(-2 * rolling_std)
    
    # 10. Deviation metrics
    deviation_pct = (btc_series - fair_value) / fair_value * 100
    deviation_zscore = residuals / rolling_std
    
    # 11. Walk-forward OOS metrics (simplified)
    oos_start = int(len(train_data) * 0.7)
    if oos_start > 50:
        oos_resid = y_train.iloc[oos_start:] - model.predict(X_scaled[oos_start:])
        oos_rmse = np.sqrt((oos_resid ** 2).mean())
        oos_mae = np.abs(oos_resid).mean()
        hit_rate = (np.sign(y_train.iloc[oos_start:]) == np.sign(model.predict(X_scaled[oos_start:]))).mean()
    else:
        oos_rmse, oos_mae, hit_rate = np.nan, np.nan, np.nan
    
    # 12. Feature importance (non-zero coefficients)
    feature_importance = dict(zip(X_train.columns, model.coef_))
    active_features = {k: v for k, v in feature_importance.items() if abs(v) > 1e-6}
    
    # 13. Predicted vs Actual Returns (for returns comparison chart)
    actual_returns = btc_log_ret.loc[common_idx] * 100  # Convert to percentage
    predicted_returns_pct = pred_returns * 100  # Convert to percentage
    
    # 14. Rebalanced Fair Value (quarterly reset to avoid cumulative drift)
    # Reset fair value to actual BTC price every 13 weeks (quarterly)
    rebalanced_fv = pd.Series(index=fair_value.index, dtype=float)
    rebalance_period = 13  # weeks
    
    for i, date in enumerate(fair_value.index):
        if i == 0 or i % rebalance_period == 0:
            # Reset to actual BTC price
            if date in btc_series.index:
                base_log = np.log(btc_series.loc[date])
            else:
                base_log = np.log(fair_value.iloc[i])
            cumulative_pred = 0
        else:
            cumulative_pred += pred_returns.iloc[i] if i < len(pred_returns) else 0
        
        rebalanced_fv.iloc[i] = np.exp(base_log + cumulative_pred)
    
    # Build result dictionary
    result = {
        'dates': fair_value.index.strftime('%Y-%m-%d').tolist(),
        'fair_value': [float(x) if pd.notnull(x) else None for x in fair_value.tolist()],
        'upper_1sd': [float(x) if pd.notnull(x) else None for x in upper_1sd.tolist()],
        'lower_1sd': [float(x) if pd.notnull(x) else None for x in lower_1sd.tolist()],
        'upper_2sd': [float(x) if pd.notnull(x) else None for x in upper_2sd.tolist()],
        'lower_2sd': [float(x) if pd.notnull(x) else None for x in lower_2sd.tolist()],
        'btc_price': [float(x) if pd.notnull(x) else None for x in btc_series.tolist()],
        'deviation_pct': [float(x) if pd.notnull(x) else None for x in deviation_pct.tolist()],
        'deviation_zscore': [float(x) if pd.notnull(x) else None for x in deviation_zscore.tolist()],
        # New: Returns comparison data
        'returns': {
            'dates': actual_returns.index.strftime('%Y-%m-%d').tolist(),
            'actual': [float(x) if pd.notnull(x) else None for x in actual_returns.tolist()],
            'predicted': [float(x) if pd.notnull(x) else None for x in predicted_returns_pct.tolist()],
        },
        # New: Rebalanced fair value
        'rebalanced_fv': [float(x) if pd.notnull(x) else None for x in rebalanced_fv.tolist()],
        'metrics': {
            'oos_rmse': round(oos_rmse, 6) if pd.notnull(oos_rmse) else None,
            'oos_mae': round(oos_mae, 6) if pd.notnull(oos_mae) else None,
            'hit_rate': round(hit_rate, 4) if pd.notnull(hit_rate) else None,
            'r2_insample': round(model.score(X_scaled, y_train), 4),
            'alpha': round(model.alpha_, 6),
            'l1_ratio': round(model.l1_ratio_, 2),
            'n_active_features': len(active_features),
        },
        'active_features': active_features,
        'frequency': 'weekly'
    }
    
    return result

def calculate_us_net_liq(df, source='FRED'):
    """Calculates US Net Liquidity in Trillions USD."""
    res = pd.DataFrame(index=df.index)
    
    if source == 'TV':
        # Everything is RAW (Units of Currency)
        fed_t = df['FED'] / 1e12
        tga_t = df['TGA'] / 1e12
        rrp_t = df['RRP'] / 1e12
    else:
        # Legacy FRED Units: FED: Millions, TGA: Millions, RRP: Billions
        fed_t = df['FED'] / 1e6
        tga_t = df['TGA'] / 1e6
        rrp_t = df['RRP'] / 1e3
    
    res['NET_LIQUIDITY'] = fed_t - tga_t - rrp_t
    return res

# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline():
    print("Starting Data Pipeline...")
    
    # 1. Fetch FRED Baseline and Normalize to Trillions
    print("Fetching FRED Baseline Data (Trillions)...")
    dfs_fred_t = {}
    raw_fred = {}
    cached_fred_file = os.path.join(OUTPUT_DIR, 'fred_cache_data.json')
    
    # Load cached FRED data if exists
    cached_fred = {}
    if os.path.exists(cached_fred_file):
        try:
            with open(cached_fred_file, 'r') as f:
                cached_fred = json.load(f)
        except Exception:
            cached_fred = {}
    
    fred_fetched = 0
    fred_cached = 0
    for sid, name in FRED_CONFIG.items():
        # FRED updates daily, use 24 hour cache
        # Also check if the SID in cache matches the current SID to handle config changes
        cached_sid = cached_fred.get(name, {}).get('sid')
        if not check_data_freshness(f"FRED_{name}", cache_hours=24) and name in cached_fred and cached_sid == sid:
            # Use cached data
            raw_fred[name] = pd.Series(cached_fred[name]['values'], 
                                       index=pd.to_datetime(cached_fred[name]['dates']), 
                                       name=name)
            fred_cached += 1
        else:
            # Fetch fresh data
            s = fetch_fred_series(sid, name)
            if not s.empty:
                raw_fred[name] = s
                update_cache_timestamp(f"FRED_{name}")
                # Cache the data including the SID
                cached_fred[name] = {
                    'sid': sid,
                    'dates': s.index.strftime('%Y-%m-%d').tolist(),
                    'values': s.tolist()
                }
                fred_fetched += 1
    
    # Save updated FRED cache
    try:
        with open(cached_fred_file, 'w') as f:
            json.dump(cached_fred, f)
    except Exception as e:
        print(f"Warning: Could not save FRED cache: {e}")
    
    print(f"  -> Fetched {fred_fetched} FRED symbols, used cache for {fred_cached} symbols")
    
    # Unit Logic for FRED -> Trillions
    df_fred = pd.DataFrame(index=pd.concat(raw_fred.values()).index.unique()).sort_index()
    for name, s in raw_fred.items():
        df_fred[name] = s
    df_fred = df_fred.ffill()  # Only forward-fill to prevent data leakage (no bfill)
    
    # Derived Trillion Columns
    df_fred_t = pd.DataFrame(index=df_fred.index)
    df_fred_t['FED_USD'] = df_fred.get('FED', 0) / 1e6
    df_fred_t['ECB_USD'] = (df_fred.get('ECB', 0) / 1e6) * df_fred.get('EURUSD', 1.0)
    df_fred_t['BOJ_USD'] = (df_fred.get('BOJ', 0) / 1e4) / df_fred.get('USDJPY', 150)
    df_fred_t['BOE_USD'] = (df_fred.get('BOE', 0) / 1e12) * df_fred.get('GBPUSD', 1.3) # Raw GBP -> Trillions
    df_fred_t['PBOC_USD'] = (df_fred.get('PBOC', 0) / 1e12) / df_fred.get('USDCNY', 7.2) # Raw -> Trillions
    df_fred_t['TGA_USD'] = df_fred['TGA'] / 1e6
    df_fred_t['RRP_USD'] = df_fred['RRP'] / 1e3
    df_fred_t['VIX'] = df_fred['VIX']
    df_fred_t['HY_SPREAD'] = df_fred['HY_SPREAD']
    df_fred_t['IG_SPREAD'] = df_fred['IG_SPREAD']
    df_fred_t['NFCI'] = df_fred['NFCI']
    df_fred_t['NFCI_CREDIT'] = df_fred['NFCI_CREDIT']
    df_fred_t['NFCI_RISK'] = df_fred['NFCI_RISK']
    df_fred_t['LENDING_STD'] = df_fred['LENDING_STD']
    # TIPS / Inflation Expectations
    df_fred_t['TIPS_BREAKEVEN'] = df_fred.get('TIPS_BREAKEVEN', pd.Series(dtype=float))
    df_fred_t['TIPS_REAL_RATE'] = df_fred.get('TIPS_REAL_RATE', pd.Series(dtype=float))
    df_fred_t['TIPS_5Y5Y_FORWARD'] = df_fred.get('TIPS_5Y5Y_FORWARD', pd.Series(dtype=float))
    df_fred_t['BANK_RESERVES'] = df_fred.get('BANK_RESERVES', pd.Series(dtype=float)) / 1e6 # Trillions
    df_fred_t['SOFR'] = df_fred.get('SOFR', pd.Series(dtype=float))
    df_fred_t['IORB'] = df_fred.get('IORB', pd.Series(dtype=float))
    df_fred_t['SOFR_VOLUME'] = df_fred.get('SOFR_VOLUME', pd.Series(dtype=float))
    # Repo Corridor Rates (Fed Rate Corridor Bounds)
    df_fred_t['SRF_RATE'] = df_fred.get('SRF_RATE', pd.Series(dtype=float))
    df_fred_t['RRP_AWARD'] = df_fred.get('RRP_AWARD', pd.Series(dtype=float))
    df_fred_t['SRF_USAGE'] = df_fred.get('SRF_USAGE', pd.Series(dtype=float))
    df_fred_t['MOVE'] = df_fred.get('MOVE', pd.Series(dtype=float))
    df_fred_t['FX_VOL'] = df_fred.get('FX_VOL', pd.Series(dtype=float))
    df_fred_t['CLI'] = calculate_cli(df_fred)['CLI']
    # Fed Forecasts tab - Macro Indicators (no conversion needed, raw values)
    df_fred_t['CPI'] = df_fred.get('CPI', pd.Series(dtype=float))
    df_fred_t['CORE_CPI'] = df_fred.get('CORE_CPI', pd.Series(dtype=float))
    df_fred_t['PCE'] = df_fred.get('PCE', pd.Series(dtype=float))
    df_fred_t['CORE_PCE'] = df_fred.get('CORE_PCE', pd.Series(dtype=float))
    df_fred_t['UNEMPLOYMENT'] = df_fred.get('UNEMPLOYMENT', pd.Series(dtype=float))
    df_fred_t['FED_FUNDS_RATE'] = df_fred.get('FED_FUNDS_RATE', pd.Series(dtype=float))
    # Inflation Expectations (TIPS Breakeven + Cleveland Fed)
    df_fred_t['INFLATION_EXPECT_1Y'] = df_fred.get('INFLATION_EXPECT_1Y', pd.Series(dtype=float))
    df_fred_t['CLEV_EXPINF_2Y'] = df_fred.get('CLEV_EXPINF_2Y', pd.Series(dtype=float))
    df_fred_t['CLEV_EXPINF_5Y'] = df_fred.get('CLEV_EXPINF_5Y', pd.Series(dtype=float))
    df_fred_t['CLEV_EXPINF_10Y'] = df_fred.get('CLEV_EXPINF_10Y', pd.Series(dtype=float))
    df_fred_t['INFLATION_EXPECT_5Y'] = df_fred.get('INFLATION_EXPECT_5Y', pd.Series(dtype=float))
    df_fred_t['INFLATION_EXPECT_10Y'] = df_fred.get('INFLATION_EXPECT_10Y', pd.Series(dtype=float))
    # Treasury Yields for stress analysis
    df_fred_t['TREASURY_30Y_YIELD'] = df_fred.get('TREASURY_30Y_YIELD', pd.Series(dtype=float))
    df_fred_t['TREASURY_10Y_YIELD'] = df_fred.get('TREASURY_10Y_YIELD', pd.Series(dtype=float))
    df_fred_t['TREASURY_5Y_YIELD'] = df_fred.get('TREASURY_5Y_YIELD', pd.Series(dtype=float))
    df_fred_t['TREASURY_2Y_YIELD'] = df_fred.get('TREASURY_2Y_YIELD', pd.Series(dtype=float))
    df_fred_t['NFP'] = df_fred.get('NFP', pd.Series(dtype=float))
    df_fred_t['JOLTS'] = df_fred.get('JOLTS', pd.Series(dtype=float))
    # Additional financial stress indices (New in Phase 3)
    df_fred_t['ST_LOUIS_STRESS'] = df_fred.get('ST_LOUIS_STRESS', pd.Series(dtype=float))
    df_fred_t['KANSAS_CITY_STRESS'] = df_fred.get('KANSAS_CITY_STRESS', pd.Series(dtype=float))
    df_fred_t['BAA_YIELD'] = df_fred.get('BAA_YIELD', pd.Series(dtype=float))
    df_fred_t['AAA_YIELD'] = df_fred.get('AAA_YIELD', pd.Series(dtype=float))
    df_fred_t['CB_LIQ_SWAPS'] = df_fred.get('CB_LIQ_SWAPS', pd.Series(dtype=float))
    # Offshore Liquidity series
    df_fred_t['OBFR'] = df_fred.get('OBFR', pd.Series(dtype=float))
    df_fred_t['EFFR'] = df_fred.get('EFFR', pd.Series(dtype=float))
    # FED_CB_SWAPS is alias for CB_LIQ_SWAPS (needed by offshore_liquidity module)
    df_fred_t['FED_CB_SWAPS'] = df_fred.get('CB_LIQ_SWAPS', pd.Series(dtype=float))
    # Indices for XCCY basis
    df_fred_t['SOFR_INDEX'] = df_fred.get('SOFR_INDEX', pd.Series(dtype=float))
    df_fred_t['SONIA_INDEX'] = df_fred.get('SONIA_INDEX', pd.Series(dtype=float))
    df_fred_t['ESTR'] = df_fred.get('ESTR', pd.Series(dtype=float))
    # 2. Fetch TV and Normalize to Trillions
    print("Fetching TradingView Update Data (Trillions)...")
    raw_tv = {}
    cached_data_file = os.path.join(OUTPUT_DIR, 'tv_cache_data.json')
    
    # Load cached TV data if exists
    cached_tv = {}
    if os.path.exists(cached_data_file):
        try:
            with open(cached_data_file, 'r') as f:
                cached_tv = json.load(f)
        except Exception:
            cached_tv = {}
    
    if tv:
        symbols_fetched = 0
        symbols_cached = 0
        for symbol, (exchange, name) in TV_CONFIG.items():
            # Check if cache is still fresh (12 hours for most data)
            cache_hours = 12 if exchange == "ECONOMICS" else 1  # FX updates more frequently
            if not check_data_freshness(name, cache_hours=cache_hours) and name in cached_tv:
                # Use cached data
                raw_tv[name] = pd.Series(cached_tv[name]['values'], 
                                         index=pd.to_datetime(cached_tv[name]['dates']), 
                                         name=name)
                symbols_cached += 1
            else:
                # Fetch fresh data
                # Use OHLC for stablecoin prices to detect intra-day depegs
                is_price = name.endswith("_PRICE")
                s = fetch_tv_series(symbol, exchange, name, n_bars=5000, return_ohlc=is_price)
                
                if isinstance(s, pd.DataFrame) and not s.empty:
                    # Store OHLC components separately for cache/pipeline
                    for col in ["high", "low", "close"]:
                        col_name = f"{name}_{col.upper()}" if col != "close" else name
                        raw_tv[col_name] = s[col]
                        update_cache_timestamp(col_name)
                        cached_tv[col_name] = {
                            'dates': s.index.strftime('%Y-%m-%d').tolist(),
                            'values': s[col].tolist()
                        }
                    symbols_fetched += 1
                elif not s.empty:
                    raw_tv[name] = s
                    update_cache_timestamp(name)
                    # Cache the data
                    cached_tv[name] = {
                        'dates': s.index.strftime('%Y-%m-%d').tolist(),
                        'values': s.tolist()
                    }
                    symbols_fetched += 1
                
                # Add small delay between TV requests to avoid rate limiting
                time.sleep(0.5)
        
        # Save updated cache
        try:
            with open(cached_data_file, 'w') as f:
                json.dump(cached_tv, f)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
        
        print(f"  -> Fetched {symbols_fetched} symbols, used cache for {symbols_cached} symbols")
    
    df_tv_t = pd.DataFrame(index=pd.concat(raw_tv.values()).index.unique() if raw_tv else []).sort_index()
    if raw_tv:
        for name, s in raw_tv.items(): df_tv_t[name] = s
        
        # Only ffill for most series. bfill ONLY for FX rates as they are denominators.
        # All FX rates from TV_CONFIG matching PineScript
        all_fx = ['EURUSD', 'JPYUSD', 'GBPUSD', 'USDJPY', 'CNYUSD', 'CADUSD', 'AUDUSD', 'INRUSD', 'CHFUSD', 
                  'RUBUSD', 'BRLUSD', 'KRWUSD', 'NZDUSD', 'SEKUSD', 'MYRUSD', 'MXNUSD', 'IDRUSD', 'ZARUSD']
        fx_cols = [c for c in all_fx if c in df_tv_t.columns]
        for c in fx_cols:
            df_tv_t[c] = df_tv_t[c].ffill()
        
        # Everything else only ffills (forward in time)
        other_cols = [c for c in df_tv_t.columns if c not in fx_cols]
        for c in other_cols:
            df_tv_t[c] = df_tv_t[c].ffill()
        
        # Unit Logic for TV -> Trillions (Major 5 CBs)
        res_tv_t = pd.DataFrame(index=df_tv_t.index)
        res_tv_t['FED_USD'] = df_tv_t.get('FED', 0) / 1e12
        eurusd = df_tv_t.get('EURUSD', df_fred.get('EURUSD', 1.0))
        res_tv_t['ECB_USD'] = (df_tv_t.get('ECB', 0) * eurusd) / 1e12
        jpyusd = df_tv_t.get('JPYUSD', 1.0 / df_fred.get('USDJPY', 150))  # JPYUSD from TV, fallback to 1/USDJPY from FRED
        res_tv_t['BOJ_USD'] = (df_tv_t.get('BOJ', 0) * jpyusd) / 1e12
        gbpusd = df_tv_t.get('GBPUSD', df_fred.get('GBPUSD', 1.3))
        res_tv_t['BOE_USD'] = (df_tv_t.get('BOE', 0) * gbpusd) / 1e12
        cnynusd = df_tv_t.get('CNYUSD', df_fred.get('CNYUSD', 0.14))
        res_tv_t['PBOC_USD'] = (df_tv_t.get('PBOC', 0) * cnynusd) / 1e12

        # Additional 4 CBs
        if 'BOC' in df_tv_t.columns:
            cadusd = df_tv_t.get('CADUSD', 0.74)  # Fallback
            res_tv_t['BOC_USD'] = (df_tv_t.get('BOC', 0) * cadusd) / 1e12
        if 'RBA' in df_tv_t.columns:
            audusd = df_tv_t.get('AUDUSD', 0.65)  # Fallback
            res_tv_t['RBA_USD'] = (df_tv_t.get('RBA', 0) * audusd) / 1e12
        if 'SNB' in df_tv_t.columns:
            chfusd = df_tv_t.get('CHFUSD', 1.1)  # Fallback
            res_tv_t['SNB_USD'] = (df_tv_t.get('SNB', 0) * chfusd) / 1e12
        if 'BOK' in df_tv_t.columns:
            krwusd = df_tv_t.get('KRWUSD', 0.00077)  # Fallback ~1/1300
            res_tv_t['BOK_USD'] = (df_tv_t.get('BOK', 0) * krwusd) / 1e12
        
        # Additional 6 CBs to reach 16 total
        if 'RBI' in df_tv_t.columns:
            inrusd = df_tv_t.get('INRUSD', 0.012)  # ~1/83
            res_tv_t['RBI_USD'] = (df_tv_t.get('RBI', 0) * inrusd) / 1e12
        if 'CBR' in df_tv_t.columns:
            rubusd = df_tv_t.get('RUBUSD', 0.011)  # ~1/90
            res_tv_t['CBR_USD'] = (df_tv_t.get('CBR', 0) * rubusd) / 1e12
        if 'BCB' in df_tv_t.columns:
            brlusd = df_tv_t.get('BRLUSD', 0.17)  # ~1/6
            res_tv_t['BCB_USD'] = (df_tv_t.get('BCB', 0) * brlusd) / 1e12
        if 'RBNZ' in df_tv_t.columns:
            nzdusd = df_tv_t.get('NZDUSD', 0.60)
            res_tv_t['RBNZ_USD'] = (df_tv_t.get('RBNZ', 0) * nzdusd) / 1e12
        if 'SR' in df_tv_t.columns:
            sekusd = df_tv_t.get('SEKUSD', 0.095)  # ~1/10.5
            res_tv_t['SR_USD'] = (df_tv_t.get('SR', 0) * sekusd) / 1e12
        if 'BNM' in df_tv_t.columns:
            myrusd = df_tv_t.get('MYRUSD', 0.22)  # ~1/4.5
            res_tv_t['BNM_USD'] = (df_tv_t.get('BNM', 0) * myrusd) / 1e12

        # Bitcoin price (already in USD, no conversion needed)
        res_tv_t['BTC'] = df_tv_t.get('BTC', pd.Series(dtype=float))

        # M2 Money Supply data (pass through ALL M2s from TV_CONFIG for calculate_global_m2)
        all_m2 = ['USM2', 'EUM2', 'CNM2', 'JPM2', 'GBM2', 'CAM2', 'AUM3', 'INM2', 'CHM2', 
                  'RUM2', 'BRM2', 'KRM2', 'MXM2', 'IDM2', 'ZAM2', 'MYM2', 'SEM2']
        for m2_col in all_m2:
            if m2_col in df_tv_t.columns:
                res_tv_t[m2_col] = df_tv_t[m2_col]
        
        # Also pass through all FX rates for calculate_global_m2
        for fx_col in all_fx:
            if fx_col in df_tv_t.columns:
                res_tv_t[fx_col] = df_tv_t[fx_col]

        # Offshore Liquidity XCCY Basis: Create _SPOT aliases for FX spots
        # offshore_liquidity.py expects EURUSD_SPOT, USDJPY_SPOT, GBPUSD_SPOT
        if 'EURUSD' in df_tv_t.columns:
            res_tv_t['EURUSD'] = df_tv_t['EURUSD']
        if 'USDJPY' in df_tv_t.columns:
            res_tv_t['USDJPY'] = df_tv_t['USDJPY']
        if 'GBPUSD' in df_tv_t.columns:
            res_tv_t['GBPUSD'] = df_tv_t['GBPUSD']
        
        # Offshore Liquidity XCCY Basis: Pass through CME FX futures
        fx_futures = ['EURUSD_FUT', 'JPYUSD_FUT', 'GBPUSD_FUT']
        for fut_col in fx_futures:
            if fut_col in df_tv_t.columns:
                res_tv_t[fut_col] = df_tv_t[fut_col]

        # TGA/RRP are usually not in TV economics, fallback to FRED baseline
        # We use combine_first to ensure we have the full FRED history for these columns
        # Then we ffill() to carry the last FRED value forward to the latest TV date
        fred_cols_to_sync = ['TGA_USD', 'RRP_USD', 'VIX', 'HY_SPREAD', 'IG_SPREAD', 
                             'NFCI', 'NFCI_CREDIT', 'NFCI_RISK', 'LENDING_STD', 'CLI',
                             'TIPS_BREAKEVEN', 'TIPS_REAL_RATE', 'TIPS_5Y5Y_FORWARD',
                             'BANK_RESERVES', 'SOFR', 'IORB', 'SOFR_VOLUME', 'FX_VOL',
                             'CPI', 'CORE_CPI', 'PCE', 'CORE_PCE', 'UNEMPLOYMENT', 'FED_FUNDS_RATE',
                             'INFLATION_EXPECT_1Y', 'INFLATION_EXPECT_5Y', 'INFLATION_EXPECT_10Y',
                             'TREASURY_10Y_YIELD', 'TREASURY_2Y_YIELD', 'NFP', 'JOLTS',
                             # Offshore liquidity series
                             'OBFR', 'EFFR', 'FED_CB_SWAPS',
                             # Rates Indices
                             'SOFR_INDEX', 'SONIA_INDEX', 'ESTR']
        # Only select columns that actually exist in df_fred_t
        fred_cols_available = [col for col in fred_cols_to_sync if col in df_fred_t.columns]
        res_tv_t = res_tv_t.combine_first(df_fred_t[fred_cols_available]).ffill()
        # Preserve RAW local units in the hybrid dataframe
        df_hybrid_processed = res_tv_t.combine_first(df_tv_t)
    
    # 3. Hybrid Merge (Trillions to Trillions)
    # Clip hybrid to start exactly when FRED starts
    fred_start = df_fred_t.index.min()
    
    if 'df_hybrid_processed' in locals() and not df_hybrid_processed.empty:
        df_hybrid_t = df_hybrid_processed.combine_first(df_fred_t)
        df_hybrid_t = df_hybrid_t[df_hybrid_t.index >= fred_start]
    else:
        df_hybrid_t = df_fred_t

    # 4. Final Processing and JSON Save
    def process_and_save_final(df_t, filename, silent=False):
        # Alignment: Ensure index is strictly daily for charts
        all_dates = pd.date_range(start=df_t.index.min(), end=df_t.index.max(), freq='D')
        df_t = df_t.reindex(all_dates).ffill()

        # Data Trimming: Find the first date where major US series have data
        # Fed Assets (FED_USD) started being populated in FRED from 2002-12-18
        # Trimming helps charts start at the first available data point
        main_series = df_t.get('FED_USD', df_t.get('NET_LIQUIDITY', pd.Series(dtype=float)))
        if not main_series.empty:
            first_valid_idx = main_series.first_valid_index()
            if first_valid_idx:
                df_t = df_t.loc[first_valid_idx:]

        # Units Logic and derived columns for Risk Model
        if 'TREASURY_10Y_YIELD' in df_t.columns and 'TREASURY_2Y_YIELD' in df_t.columns:
            df_t['YIELD_CURVE'] = df_t['TREASURY_10Y_YIELD'] - df_t['TREASURY_2Y_YIELD']
        
        gli = calculate_gli_from_trillions(df_t)
        us_net_liq = calculate_us_net_liq_from_trillions(df_t)
        cli_df = calculate_cli(df_t)

        # Add GLI_TOTAL, NET_LIQUIDITY and M2_TOTAL to df_t
        m2_data = calculate_global_m2(df_t)
        df_t['GLI_TOTAL'] = gli['GLI_TOTAL']
        df_t['NET_LIQUIDITY'] = us_net_liq['NET_LIQUIDITY']
        df_t['M2_TOTAL'] = m2_data['M2_TOTAL']
        
        # Add labels without _USD for date tracking compatibility
        if 'RRP_USD' in df_t.columns: df_t['RRP'] = df_t['RRP_USD']
        if 'TGA_USD' in df_t.columns: df_t['TGA'] = df_t['TGA_USD']
        if 'FED_USD' in df_t.columns: df_t['FED'] = df_t['FED_USD']

        # Bitcoin Analysis
        btc_analysis = calculate_btc_fair_value(df_t)
        btc_analysis_v2 = calculate_btc_fair_value_v2(df_t)  # Quant v2 model
        btc_rocs = {}
        if 'BTC' in df_t.columns and df_t['BTC'].notna().sum() > 0:
            btc_rocs = calculate_rocs(df_t['BTC'])

        # New: ROCs for Risk Model tab indicators
        cli_rocs = calculate_rocs(df_t['CLI']) if 'CLI' in df_t.columns else {}
        vix_rocs = calculate_rocs(df_t['VIX']) if 'VIX' in df_t.columns else {}
        tips_real_rocs = calculate_rocs(df_t['TIPS_REAL_RATE']) if 'TIPS_REAL_RATE' in df_t.columns else {}
        move_rocs = calculate_rocs(df_t['MOVE']) if 'MOVE' in df_t.columns else {}
        
        # Calculate FX Volatility from DXY (realized vol, annualized)
        # EVZ was discontinued Jan 2025, so we compute realized vol from DXY
        if 'DXY' in df_t.columns and df_t['DXY'].notna().sum() > 20:
            dxy_returns = np.log(df_t['DXY']).diff()
            # 21-day rolling realized volatility, annualized (252 trading days)
            df_t['FX_VOL'] = dxy_returns.rolling(21, min_periods=10).std() * np.sqrt(252) * 100
        else:
            df_t['FX_VOL'] = pd.Series(dtype=float, index=df_t.index)
        
        fx_vol_rocs = calculate_rocs(df_t['FX_VOL']) if 'FX_VOL' in df_t.columns and df_t['FX_VOL'].notna().sum() > 0 else {}

        # Calculate signals AFTER FX_VOL is computed (so all data is available)
        signals = calculate_signals(df_t, cli_df)
        
        # Compute aggregate signal score for dashboard
        signal_aggregate = aggregate_signal_score(signals)

        # ================================================================
        # CLI V2 and Regime V2 Calculations (from regime_v2 module)
        # ================================================================
        cli_v2_df = calculate_cli_v2(df_t)
        df_t['CLI_V2'] = cli_v2_df['CLI_V2']  # Add to df_t for regime calculations
        
        # Regime V2A (Inflation-Aware) and V2B (Growth-Aware)
        regime_v2a = calculate_macro_regime_v2a(df_t)
        regime_v2b = calculate_macro_regime_v2b(df_t)
        
        # Historical Stress Dashboard
        stress_historical = calculate_stress_historical(df_t)

        # Stablecoin Analytics
        stablecoins_data = calculate_stablecoins(df_t)

        # Fed Forecasts: FOMC Calendar and Dot Plot
        fomc_dates = fetch_fomc_calendar()
        dot_plot = fetch_dot_plot_data()

        # Cross-Correlations (using ROC/returns for stationarity, not raw levels)
        correlations = {}
        if 'BTC' in df_t.columns and df_t['BTC'].notna().sum() > 100:
            # Use log returns for BTC (stationary)
            btc_log_returns = np.log(df_t['BTC']).diff().dropna()
            
            # GLI vs BTC (using 21-day ROC for macro series)
            gli_roc = gli['GLI_TOTAL'].pct_change(21).loc[btc_log_returns.index].dropna()
            if len(gli_roc) > 100:
                common_idx = gli_roc.index.intersection(btc_log_returns.index)
                correlations['gli_btc'] = calculate_cross_correlation(gli_roc.loc[common_idx], btc_log_returns.loc[common_idx], max_lag=90)

            # CLI vs BTC (CLI is already a z-score, use diff)
            cli_diff = df_t['CLI'].diff().loc[btc_log_returns.index].dropna()
            if len(cli_diff) > 100:
                common_idx = cli_diff.index.intersection(btc_log_returns.index)
                correlations['cli_btc'] = calculate_cross_correlation(cli_diff.loc[common_idx], btc_log_returns.loc[common_idx], max_lag=90)

            # VIX vs BTC (using diff for VIX)
            vix_diff = df_t['VIX'].diff().loc[btc_log_returns.index].dropna()
            if len(vix_diff) > 100:
                common_idx = vix_diff.index.intersection(btc_log_returns.index)
                correlations['vix_btc'] = calculate_cross_correlation(vix_diff.loc[common_idx], btc_log_returns.loc[common_idx], max_lag=90)

            # Net Liq vs BTC (using 21-day ROC)
            netliq_roc = us_net_liq['NET_LIQUIDITY'].pct_change(21).loc[btc_log_returns.index].dropna()
            if len(netliq_roc) > 100:
                common_idx = netliq_roc.index.intersection(btc_log_returns.index)
                correlations['netliq_btc'] = calculate_cross_correlation(netliq_roc.loc[common_idx], btc_log_returns.loc[common_idx], max_lag=90)


        # Predictive Lag Correlation Analysis (CLI vs BTC ROC)
        predictive = {}
        if 'BTC' in df_t.columns and 'CLI' in df_t.columns:
            analysis_df = pd.DataFrame({
                'CLI': df_t['CLI'],
                'BTC_Price': df_t['BTC']
            })
            predictive = calculate_lag_correlation_analysis(analysis_df.dropna(), max_lag=30)

        # Bank Reserves Derived Metrics
        reserves_df = pd.DataFrame({
            'BANK_RESERVES': df_t.get('BANK_RESERVES', pd.Series(dtype=float)),
            'NET_LIQUIDITY': us_net_liq.get('NET_LIQUIDITY', pd.Series(dtype=float))
        }).ffill()
        reserves_metrics = calculate_reserves_metrics(reserves_df)

        # US System Composite Metrics
        us_system_df = pd.DataFrame({
            'FED_USD': df_t.get('FED_USD', pd.Series(dtype=float)),
            'RRP_USD': df_t.get('RRP_USD', pd.Series(dtype=float)),
            'TGA_USD': df_t.get('TGA_USD', pd.Series(dtype=float)),
            'NET_LIQUIDITY': us_net_liq.get('NET_LIQUIDITY', pd.Series(dtype=float))
        }).ffill()
        us_system_metrics = calculate_us_system_metrics(us_system_df)

        # Net Repo Operations
        net_repo_data = calculate_net_repo_operations(df_t)

        # Flow/Impulse Metrics (more useful for trading than levels)
        flow_df = pd.DataFrame({
            'GLI_TOTAL': gli['GLI_TOTAL'],
            'M2_TOTAL': m2_data.get('M2_TOTAL', pd.Series(dtype=float)),
            'NET_LIQUIDITY': us_net_liq.get('NET_LIQUIDITY', pd.Series(dtype=float)),
            'CLI': df_t.get('CLI', pd.Series(dtype=float)),
            **{f'{cb}_USD': df_t.get(f'{cb}_USD', pd.Series(dtype=float)) for cb in ['FED', 'ECB', 'BOJ', 'PBOC', 'BOE', 'BOC', 'RBA', 'SNB', 'CBR', 'BCB', 'BOK', 'RBI', 'RBNZ', 'SR', 'BNM']}
        }).ffill()
        flow_metrics = {k: clean_for_json(v) for k, v in calculate_flow_metrics(flow_df).items()}

        # --- Macro Regime (multi-factor) ---
        regime_metrics = calculate_macro_regime(df_t)
        if 'cli_gli_divergence' in regime_metrics:
            df_t['CLI_GLI_DIVERGENCE'] = regime_metrics['cli_gli_divergence']


        # Helper for Series Metadata (Last Real Date & Coverage)
        def get_series_info(series, df_ref):
            if series is None or series.empty:
                return {"last_date": None, "freshness": None}
            # Find the last non-NaN index in the RAW data before ffill
            last_idx = series.dropna().index[-1] if not series.dropna().empty else None
            if last_idx:
                last_date_str = last_idx.strftime('%Y-%m-%d')
                days_ago = (df_ref.index[-1] - last_idx).days
                return {"last_date": last_date_str, "freshness": days_ago}
            return {"last_date": None, "freshness": None}

        series_metadata = {
            "GLI": get_series_info(gli['GLI_TOTAL'], df_t) | {"cb_count": int(df_t.get('CB_COUNT', pd.Series([0])).iloc[-1])},
            "M2": get_series_info(m2_data.get('M2_TOTAL'), df_t),
            "CLI": get_series_info(df_t.get('CLI'), df_t),
            "NET_LIQ": get_series_info(us_net_liq.get('NET_LIQUIDITY'), df_t),
            "BTC": get_series_info(df_t.get('BTC'), df_t)
        }

        # JSON structure (same as before)
        # Identify all active M2 columns
        m2_cols_agg = [c for c in m2_data.columns if c.endswith('_M2_USD')]
        m2_keys_agg = [c.replace('_M2_USD', '').lower() for c in m2_cols_agg if c != 'M2_TOTAL']
        
        gli_rocs = calculate_rocs(gli['GLI_TOTAL'])
        m2_rocs_total = calculate_rocs(m2_data.get('M2_TOTAL', pd.Series(dtype=float)))
        # Net Liquidity ROCs (for the sidebar)
        net_liq_rocs = calculate_rocs(us_net_liq['NET_LIQUIDITY'])
        
        # Offshore Liquidity XCCY Basis - Build TV DataFrame
        offshore_tv_cols = ['EURUSD', 'USDJPY', 'GBPUSD', 
                            'EURUSD_FUT', 'JPYUSD_FUT', 'GBPUSD_FUT']
        df_offshore_tv = pd.DataFrame({
            col: df_t[col] for col in offshore_tv_cols if col in df_t.columns
        }, index=df_t.index)
        
        data_output = {
            'dates': df_t.index.strftime('%Y-%m-%d').tolist(),
            'last_dates': {k: get_safe_last_date(df_t[k]) for k in df_t.columns},
            'gli': {
                'total': clean_for_json(gli['GLI_TOTAL']),
                'constant_fx': clean_for_json(calculate_gli_constant_fx(df_t)),
                'cb_count': int(gli.get('CB_COUNT', 5).iloc[0] if hasattr(gli.get('CB_COUNT', 5), 'iloc') else gli.get('CB_COUNT', 5)),
                'data_start_date': df_t.index.min().strftime('%Y-%m-%d'),
                'fed': clean_for_json(gli['FED_USD']),
                'ecb': clean_for_json(gli['ECB_USD']),
                'boj': clean_for_json(gli['BOJ_USD']),
                'boe': clean_for_json(gli['BOE_USD']),
                'pboc': clean_for_json(gli['PBOC_USD']),
                # Additional CBs
                'boc': clean_for_json(gli.get('BOC_USD', pd.Series(dtype=float))),
                'rba': clean_for_json(gli.get('RBA_USD', pd.Series(dtype=float))),
                'snb': clean_for_json(gli.get('SNB_USD', pd.Series(dtype=float))),
                'bok': clean_for_json(gli.get('BOK_USD', pd.Series(dtype=float))),
                'rbi': clean_for_json(gli.get('RBI_USD', pd.Series(dtype=float))),
                'cbr': clean_for_json(gli.get('CBR_USD', pd.Series(dtype=float))),
                'bcb': clean_for_json(gli.get('BCB_USD', pd.Series(dtype=float))),
                'rbnz': clean_for_json(gli.get('RBNZ_USD', pd.Series(dtype=float))),
                'sr': clean_for_json(gli.get('SR_USD', pd.Series(dtype=float))),
                'bnm': clean_for_json(gli.get('BNM_USD', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in gli_rocs.items()}
            },
            'm2': {
                'total': clean_for_json(m2_data.get('M2_TOTAL', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in m2_rocs_total.items()},
                **{k: clean_for_json(m2_data[f"{k.upper()}_M2_USD"]) for k in m2_keys_agg}
            },
            'm2_bank_rocs': (lambda total_m2: {
                k: {
                    roi_key: clean_for_json(calculate_rocs(m2_data[f'{k.upper()}_M2_USD'])[roi_key])
                    for roi_key in ['1M', '3M', '6M', '1Y']
                } | {
                    # Contribution to Global M2 Change
                    f'impact_{i}': clean_for_json(
                        ((m2_data[f'{k.upper()}_M2_USD'] - m2_data[f'{k.upper()}_M2_USD'].shift(w)) / total_m2.shift(w)) * 100
                    ) for i, w in [('1m', 22), ('3m', 66), ('6m', 132), ('1y', 252)]
                }
                for k in m2_keys_agg
            })(m2_data['M2_TOTAL']),
            'm2_weights': (lambda latest_m2: {
                k: float(latest_m2.get(f'{k.upper()}_M2_USD', 0) / latest_m2['M2_TOTAL'] * 100) if latest_m2['M2_TOTAL'] > 0 else 0
                for k in m2_keys_agg
            })(m2_data.iloc[-1] if not m2_data.empty else {}),
            'us_net_liq': clean_for_json(us_net_liq['NET_LIQUIDITY']),
            'us_net_liq_rrp': clean_for_json(df_t.get('RRP_USD', pd.Series(dtype=float))),
            'us_net_liq_tga': clean_for_json(df_t.get('TGA_USD', pd.Series(dtype=float))),
            'us_net_liq_reserves': clean_for_json(df_t.get('BANK_RESERVES', pd.Series(dtype=float))),
            'us_net_liq_rocs': {k: clean_for_json(v) for k, v in net_liq_rocs.items()},
            'repo_operations': {
                'srf_usage': clean_for_json(net_repo_data['srf_usage']),
                'rrp_usage': clean_for_json(net_repo_data['rrp_usage']),
                'net_repo': clean_for_json(net_repo_data['net_repo']),
                'net_repo_zscore': clean_for_json(net_repo_data['net_repo_zscore']),
                'net_repo_momentum': clean_for_json(net_repo_data['net_repo_momentum']),
                'cumulative_30d': clean_for_json(net_repo_data['cumulative_30d']),
            },
            'reserves_metrics': {
                'reserves_roc_3m': clean_for_json(reserves_metrics.get('reserves_roc_3m', pd.Series(dtype=float))),
                'netliq_roc_3m': clean_for_json(reserves_metrics.get('netliq_roc_3m', pd.Series(dtype=float))),
                'spread_zscore': clean_for_json(reserves_metrics.get('spread_zscore', pd.Series(dtype=float))),
                'momentum': clean_for_json(reserves_metrics.get('momentum', pd.Series(dtype=float))),
                'lcr': clean_for_json(reserves_metrics.get('lcr', pd.Series(dtype=float))),
                'acceleration': clean_for_json(reserves_metrics.get('acceleration', pd.Series(dtype=float))),
                'volatility': clean_for_json(reserves_metrics.get('volatility', pd.Series(dtype=float))),
            },
            'us_system_metrics': {
                'fed_roc_20d': clean_for_json(us_system_metrics.get('fed_roc_20d', pd.Series(dtype=float))),
                'rrp_roc_20d': clean_for_json(us_system_metrics.get('rrp_roc_20d', pd.Series(dtype=float))),
                'tga_roc_20d': clean_for_json(us_system_metrics.get('tga_roc_20d', pd.Series(dtype=float))),
                'netliq_roc_20d': clean_for_json(us_system_metrics.get('netliq_roc_20d', pd.Series(dtype=float))),
                'rrp_drain_weekly': clean_for_json(us_system_metrics.get('rrp_drain_weekly', pd.Series(dtype=float))),
                'rrp_weeks_to_empty': clean_for_json(us_system_metrics.get('rrp_weeks_to_empty', pd.Series(dtype=float))),
                'tga_zscore': clean_for_json(us_system_metrics.get('tga_zscore', pd.Series(dtype=float))),
                'fed_momentum': clean_for_json(us_system_metrics.get('fed_momentum', pd.Series(dtype=float))),
                'liquidity_score': clean_for_json(us_system_metrics.get('liquidity_score', pd.Series(dtype=float))),
                # Absolute $ deltas (avoid % base effect)
                'rrp_delta_4w': clean_for_json(us_system_metrics.get('rrp_delta_4w', pd.Series(dtype=float))),
                'rrp_delta_13w': clean_for_json(us_system_metrics.get('rrp_delta_13w', pd.Series(dtype=float))),
                'tga_delta_4w': clean_for_json(us_system_metrics.get('tga_delta_4w', pd.Series(dtype=float))),
                'tga_delta_13w': clean_for_json(us_system_metrics.get('tga_delta_13w', pd.Series(dtype=float))),
                # Net Liquidity Impulse ($T)
                'netliq_delta_4w': clean_for_json(us_system_metrics.get('netliq_delta_4w', pd.Series(dtype=float))),
                'netliq_delta_13w': clean_for_json(us_system_metrics.get('netliq_delta_13w', pd.Series(dtype=float))),
            },
            # Flow/Impulse Metrics (trading-focused)
            'flow_metrics': {
                # GLI impulse and acceleration
                'gli_impulse_4w': clean_for_json(flow_metrics.get('gli_impulse_4w', pd.Series(dtype=float))),
                'gli_impulse_13w': clean_for_json(flow_metrics.get('gli_impulse_13w', pd.Series(dtype=float))),
                'gli_accel': clean_for_json(flow_metrics.get('gli_accel', pd.Series(dtype=float))),
                'gli_impulse_zscore': clean_for_json(flow_metrics.get('gli_impulse_zscore', pd.Series(dtype=float))),
                # M2 impulse and acceleration
                'm2_impulse_4w': clean_for_json(flow_metrics.get('m2_impulse_4w', pd.Series(dtype=float))),
                'm2_impulse_13w': clean_for_json(flow_metrics.get('m2_impulse_13w', pd.Series(dtype=float))),
                'm2_accel': clean_for_json(flow_metrics.get('m2_accel', pd.Series(dtype=float))),
                'm2_impulse_zscore': clean_for_json(flow_metrics.get('m2_impulse_zscore', pd.Series(dtype=float))),
                # CB contributions to ΔGLI (top 5)
                'fed_contrib_13w': clean_for_json(flow_metrics.get('fed_contrib_13w', pd.Series(dtype=float))),
                'ecb_contrib_13w': clean_for_json(flow_metrics.get('ecb_contrib_13w', pd.Series(dtype=float))),
                'boj_contrib_13w': clean_for_json(flow_metrics.get('boj_contrib_13w', pd.Series(dtype=float))),
                'pboc_contrib_13w': clean_for_json(flow_metrics.get('pboc_contrib_13w', pd.Series(dtype=float))),
                'boe_contrib_13w': clean_for_json(flow_metrics.get('boe_contrib_13w', pd.Series(dtype=float))),
            },
            # Macro Regime (multi-factor regime model)
            'macro_regime': {
                'score': clean_for_json(regime_metrics.get('score', pd.Series(dtype=float))),
                'regime_code': clean_for_json(regime_metrics.get('regime_code', pd.Series(dtype=float))),
                'transition': clean_for_json(regime_metrics.get('transition', pd.Series(dtype=float))),
                # optional diagnostics
                'total_z': clean_for_json(regime_metrics.get('total_z', pd.Series(dtype=float))),
                'liquidity_z': clean_for_json(regime_metrics.get('liquidity_z', pd.Series(dtype=float))),
                'credit_z': clean_for_json(regime_metrics.get('credit_z', pd.Series(dtype=float))),
                'brakes_z': clean_for_json(regime_metrics.get('brakes_z', pd.Series(dtype=float))),
                'cb_diffusion_13w': clean_for_json(regime_metrics.get('cb_diffusion_13w', pd.Series(dtype=float))),
                'cb_hhi_13w': clean_for_json(regime_metrics.get('cb_hhi_13w', pd.Series(dtype=float))),
                'repo_stress': clean_for_json(regime_metrics.get('repo_stress', pd.Series(dtype=float))),
                'real_rate_shock_4w': clean_for_json(regime_metrics.get('real_rate_shock_4w', pd.Series(dtype=float))),
                'cli_gli_divergence': clean_for_json(regime_metrics.get('cli_gli_divergence', pd.Series(dtype=float))),
                'reserves_spread_z': clean_for_json(regime_metrics.get('reserves_spread_z', pd.Series(dtype=float))),
            },
            'us_system_rocs': (lambda total_nl: {
                comp: {
                    k: clean_for_json(calculate_rocs(df_t.get(col, pd.Series(0.0, index=df_t.index)))[k])
                    for k in ['1M', '3M', '6M', '1Y']
                } | {
                    # Absolute Dollar Change (in Billions for easier reading)
                    f'delta_{i}': clean_for_json(
                        (df_t.get(col, pd.Series(0.0, index=df_t.index)) - 
                         df_t.get(col, pd.Series(0.0, index=df_t.index)).shift(w)) * 1000 # Convert T to B
                    ) for i, w in [('1m', 22), ('3m', 66), ('1y', 252)]
                } | {
                    # Multi-period Impact on Net Liquidity
                    # Note: RRP and TGA have INVERSE impact (increase = liquidity drain)
                    f'impact_{i}': clean_for_json(
                        ((df_t.get(col, pd.Series(0.0, index=df_t.index)) - 
                          df_t.get(col, pd.Series(0.0, index=df_t.index)).shift(w)) / total_nl.shift(w)) * 100 * (1 if comp == 'fed' else -1)
                    ) for i, w in [('1m', 22), ('3m', 66), ('1y', 252)]
                }
                for comp, col in [('fed', 'FED_USD'), ('rrp', 'RRP_USD'), ('tga', 'TGA_USD')]
            })(us_net_liq['NET_LIQUIDITY']),
            'bank_rocs': (lambda total_gli: {
                b: {
                    k: clean_for_json(calculate_rocs(gli.get(f'{b.upper()}_USD', pd.Series(0.0, index=df_t.index)))[k]) 
                    for k in ['1M', '3M', '6M', '1Y']
                } | {
                    # Multi-period Impact
                    f'impact_{i}': clean_for_json(
                        ((gli.get(f'{b.upper()}_USD', pd.Series(0.0, index=df_t.index)) - 
                          gli.get(f'{b.upper()}_USD', pd.Series(0.0, index=df_t.index)).shift(w)) / total_gli.shift(w)) * 100
                    ) for i, w in [('1m', 22), ('3m', 66), ('6m', 132), ('1y', 252)]
                }
                for b in ['fed', 'ecb', 'boj', 'boe', 'pboc', 'boc', 'rba', 'snb', 'bok', 'rbi', 'cbr', 'bcb', 'rbnz', 'sr', 'bnm']
            })(gli['GLI_TOTAL']),
            'gli_weights': (lambda latest_gli: {
                b: float(latest_gli.get(f'{b.upper()}_USD', 0) / latest_gli['GLI_TOTAL'] * 100) if latest_gli['GLI_TOTAL'] > 0 else 0
                for b in ['fed', 'ecb', 'boj', 'boe', 'pboc', 'boc', 'rba', 'snb', 'bok', 'rbi', 'cbr', 'bcb', 'rbnz', 'sr', 'bnm']
            })(gli.iloc[-1] if not gli.empty else {}),
            'cli': {
                'total': clean_for_json(df_t['CLI']),
                'percentile': clean_for_json(rolling_percentile(df_t['CLI'], window=1260)),
                'rocs': {k: clean_for_json(v) for k, v in cli_rocs.items()}
            },
            'signal_metrics': compute_signal_metrics(df_t, cli_df, window=1260),
            'cli_components': {
                'hy_z': clean_for_json(cli_df.get('HY_SPREAD_Z', pd.Series(dtype=float))),
                'ig_z': clean_for_json(cli_df.get('IG_SPREAD_Z', pd.Series(dtype=float))),
                'nfci_credit_z': clean_for_json(cli_df.get('NFCI_CREDIT_Z', pd.Series(dtype=float))),
                'nfci_risk_z': clean_for_json(cli_df.get('NFCI_RISK_Z', pd.Series(dtype=float))),
                'lending_z': clean_for_json(cli_df.get('LENDING_STD_Z', pd.Series(dtype=float))),
                'vix_z': clean_for_json(cli_df.get('VIX_Z', pd.Series(dtype=float))),
                'weights': {'HY': 0.25, 'IG': 0.15, 'NFCI_CREDIT': 0.20, 'NFCI_RISK': 0.20, 'LENDING': 0.10, 'VIX': 0.10}
            },
            'signals': signals,
            'signal_aggregate': signal_aggregate,
            'schema_version': 2,
            'nfci_credit': clean_for_json(df_t.get('NFCI_CREDIT', pd.Series(dtype=float))),
            'nfci_risk': clean_for_json(df_t.get('NFCI_RISK', pd.Series(dtype=float))),
            'lending': clean_for_json(df_t.get('LENDING_STD', pd.Series(dtype=float))),
            'vix': {
                'total': clean_for_json(df_t['VIX']),
                'rocs': {k: clean_for_json(v) for k, v in vix_rocs.items()}
            },
            'move': {
                'total': clean_for_json(df_t.get('MOVE', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in move_rocs.items()}
            },
            'fx_vol': {
                'total': clean_for_json(df_t.get('FX_VOL', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in fx_vol_rocs.items()}
            },
            'hy_spread': clean_for_json(df_t['HY_SPREAD']),
            'ig_spread': clean_for_json(df_t['IG_SPREAD']),
            # Treasury Yields for stress analysis
            'treasury_30y': clean_for_json(df_t.get('TREASURY_30Y_YIELD', pd.Series(dtype=float))),
            'treasury_10y': clean_for_json(df_t.get('TREASURY_10Y_YIELD', pd.Series(dtype=float))),
            'treasury_5y': clean_for_json(df_t.get('TREASURY_5Y_YIELD', pd.Series(dtype=float))),
            'treasury_2y': clean_for_json(df_t.get('TREASURY_2Y_YIELD', pd.Series(dtype=float))),
            # Yield Curve Spreads
            'yield_curve': clean_for_json(df_t.get('TREASURY_10Y_YIELD', 0) - df_t.get('TREASURY_2Y_YIELD', 0)),
            'yield_curve_30y_10y': clean_for_json(df_t.get('TREASURY_30Y_YIELD', 0) - df_t.get('TREASURY_10Y_YIELD', 0)),
            'yield_curve_30y_2y': clean_for_json(df_t.get('TREASURY_30Y_YIELD', 0) - df_t.get('TREASURY_2Y_YIELD', 0)),
            'yield_curve_10y_5y': clean_for_json(df_t.get('TREASURY_10Y_YIELD', 0) - df_t.get('TREASURY_5Y_YIELD', 0)),
            # Financial Stress Indices
            'st_louis_stress': clean_for_json(df_t.get('ST_LOUIS_STRESS', pd.Series(dtype=float))),
            'kansas_city_stress': clean_for_json(df_t.get('KANSAS_CITY_STRESS', pd.Series(dtype=float))),
            # Corporate Bond Yields (Moody's)
            'baa_yield': clean_for_json(df_t.get('BAA_YIELD', pd.Series(dtype=float))),
            'aaa_yield': clean_for_json(df_t.get('AAA_YIELD', pd.Series(dtype=float))),
            'baa_aaa_spread': clean_for_json(df_t.get('BAA_YIELD', 0) - df_t.get('AAA_YIELD', 0)),
            # Central Bank Liquidity Swaps
            'cb_liq_swaps': clean_for_json(df_t.get('CB_LIQ_SWAPS', pd.Series(dtype=float))),
            # TIPS / Inflation Expectations
            'tips': {
                'breakeven': clean_for_json(df_t.get('TIPS_BREAKEVEN', pd.Series(dtype=float))),
                'real_rate': clean_for_json(df_t.get('TIPS_REAL_RATE', pd.Series(dtype=float))),
                'fwd_5y5y': clean_for_json(df_t.get('TIPS_5Y5Y_FORWARD', pd.Series(dtype=float))),
                'rocs': {k: clean_for_json(v) for k, v in tips_real_rocs.items()}
            },
            'repo_stress': {
                # Core rates
                'sofr': clean_for_json(df_t.get('SOFR', pd.Series(dtype=float))),
                'iorb': clean_for_json(df_t.get('IORB', pd.Series(dtype=float))),
                'sofr_volume': clean_for_json(df_t.get('SOFR_VOLUME', pd.Series(dtype=float))),
                'sofr_volume_roc_5d': clean_for_json(df_t.get('SOFR_VOLUME', pd.Series(dtype=float)).pct_change(5) * 100),
                'sofr_volume_roc_20d': clean_for_json(df_t.get('SOFR_VOLUME', pd.Series(dtype=float)).pct_change(20) * 100),
                # Corridor bounds
                'srf_rate': clean_for_json(df_t.get('SRF_RATE', pd.Series(dtype=float))),      # Ceiling
                'rrp_award': clean_for_json(df_t.get('RRP_AWARD', pd.Series(dtype=float))),    # Floor (lower)
                'srf_usage': clean_for_json(df_t.get('SRF_USAGE', pd.Series(dtype=float))),    # SRF Usage ($B)
                # Derived metrics (in basis points)
                'sofr_to_ceiling': clean_for_json((df_t.get('SRF_RATE', pd.Series(dtype=float)) - df_t.get('SOFR', pd.Series(dtype=float))) * 100),
                'sofr_to_floor': clean_for_json((df_t.get('SOFR', pd.Series(dtype=float)) - df_t.get('IORB', pd.Series(dtype=float))) * 100),
                'corridor_width': clean_for_json((df_t.get('SRF_RATE', pd.Series(dtype=float)) - df_t.get('RRP_AWARD', pd.Series(dtype=float))) * 100),
            },
            'btc': {
                'price': clean_for_json(btc_analysis.get('BTC_ACTUAL', pd.Series(dtype=float))),
                'models': {
                    'macro': {
                        'fair_value': clean_for_json(btc_analysis.get('BTC_FAIR_VALUE', pd.Series(dtype=float))),
                        'upper_1sd': clean_for_json(btc_analysis.get('BTC_UPPER_1SD', pd.Series(dtype=float))),
                        'lower_1sd': clean_for_json(btc_analysis.get('BTC_LOWER_1SD', pd.Series(dtype=float))),
                        'upper_2sd': clean_for_json(btc_analysis.get('BTC_UPPER_2SD', pd.Series(dtype=float))),
                        'lower_2sd': clean_for_json(btc_analysis.get('BTC_LOWER_2SD', pd.Series(dtype=float))),
                        'deviation_pct': clean_for_json(btc_analysis.get('BTC_DEVIATION_PCT', pd.Series(dtype=float))),
                        'deviation_zscore': clean_for_json(btc_analysis.get('BTC_DEVIATION_ZSCORE', pd.Series(dtype=float))),
                    },
                    'adoption': {
                        'fair_value': clean_for_json(btc_analysis.get('ADJ_BTC_FAIR_VALUE', pd.Series(dtype=float))),
                        'upper_1sd': clean_for_json(btc_analysis.get('ADJ_BTC_UPPER_1SD', pd.Series(dtype=float))),
                        'lower_1sd': clean_for_json(btc_analysis.get('ADJ_BTC_LOWER_1SD', pd.Series(dtype=float))),
                        'upper_2sd': clean_for_json(btc_analysis.get('ADJ_BTC_UPPER_2SD', pd.Series(dtype=float))),
                        'lower_2sd': clean_for_json(btc_analysis.get('ADJ_BTC_LOWER_2SD', pd.Series(dtype=float))),
                        'deviation_pct': clean_for_json(btc_analysis.get('ADJ_BTC_DEVIATION_PCT', pd.Series(dtype=float))),
                        'deviation_zscore': clean_for_json(btc_analysis.get('ADJ_BTC_DEVIATION_ZSCORE', pd.Series(dtype=float))),
                    },
                    'quant_v2': btc_analysis_v2  # New Quant v2 model with weekly data
                },
                'rocs': {k: clean_for_json(v) for k, v in btc_rocs.items()} if btc_rocs else {}
            },
            'flow_metrics': clean_for_json(flow_metrics),
            'reserves_metrics': clean_for_json(reserves_metrics),
            'us_system_metrics': clean_for_json(us_system_metrics),
            'series_metadata': series_metadata,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'correlations': correlations,
            'predictive': predictive,
            # Fed Forecasts tab data
            'fed_forecasts': {
                # Inflation (YoY % change calculated from index levels)
                # Using 365.25 for calendar daily ffilled data
                'cpi_yoy': clean_for_json(df_t['CPI'].pct_change(365) * 100) if 'CPI' in df_t.columns else [],
                'core_cpi_yoy': clean_for_json(df_t['CORE_CPI'].pct_change(365) * 100) if 'CORE_CPI' in df_t.columns else [],
                'pce_yoy': clean_for_json(df_t['PCE'].pct_change(365) * 100) if 'PCE' in df_t.columns else [],
                'core_pce_yoy': clean_for_json(df_t['CORE_PCE'].pct_change(365) * 100) if 'CORE_PCE' in df_t.columns else [],
                # PMI data (from TV ECONOMICS)
                'ism_mfg': clean_for_json(df_t.get('ISM_MFG', pd.Series(dtype=float))),
                'ism_svc': clean_for_json(df_t.get('ISM_SVC', pd.Series(dtype=float))),
                # Labor & Rates
                'unemployment': clean_for_json(df_t.get('UNEMPLOYMENT', pd.Series(dtype=float))),
                'nfp': clean_for_json(df_t.get('NFP', pd.Series(dtype=float))),
                'nfp_change': clean_for_json(df_t.get('NFP', pd.Series(dtype=float)).diff(22)), # Approx 1 month
                'jolts': clean_for_json(df_t.get('JOLTS', pd.Series(dtype=float))),
                'fed_funds_rate': clean_for_json(df_t.get('FED_FUNDS_RATE', pd.Series(dtype=float))),
                'fomc_dates': fomc_dates,
                'dot_plot': dot_plot,
            },
            # Inflation Swaps / Cleveland Fed data (for TIPS vs Swaps comparison)
            'inflation_swaps': {
                'cleveland_1y': clean_for_json(df_t.get('INFLATION_EXPECT_1Y', pd.Series(dtype=float))),
                'cleveland_2y': clean_for_json(df_t.get('CLEV_EXPINF_2Y', pd.Series(dtype=float))),
                'cleveland_5y': clean_for_json(df_t.get('CLEV_EXPINF_5Y', pd.Series(dtype=float))),
                'cleveland_10y': clean_for_json(df_t.get('CLEV_EXPINF_10Y', pd.Series(dtype=float))),
                'inf_risk_premium_1y': clean_for_json(df_t.get('INF_RISK_PREM_1Y', pd.Series(dtype=float))),
                'inf_risk_premium_10y': clean_for_json(df_t.get('INF_RISK_PREM_10Y', pd.Series(dtype=float))),
                'real_rate_1y': clean_for_json(df_t.get('REAL_INT_RATE_1Y', pd.Series(dtype=float))),
                'real_rate_10y': clean_for_json(df_t.get('REAL_INT_RATE_10Y', pd.Series(dtype=float))),
                'umich_expectations': clean_for_json(df_t.get('UMICH_INFL_EXP', pd.Series(dtype=float))),
                'tips_breakeven_5y': clean_for_json(df_t.get('TIPS_BREAKEVEN_5Y', pd.Series(dtype=float))),
                'tips_breakeven_2y': clean_for_json(df_t.get('TIPS_BREAKEVEN_2Y', pd.Series(dtype=float))),
            },
            # Market-based Inflation Expectations (TIPS Breakeven + Cleveland Fed)
            'inflation_expect_1y': clean_for_json(df_t.get('INFLATION_EXPECT_1Y', pd.Series(dtype=float))),
            'inflation_expect_5y': clean_for_json(df_t.get('INFLATION_EXPECT_5Y', pd.Series(dtype=float))),
            'inflation_expect_10y': clean_for_json(df_t.get('INFLATION_EXPECT_10Y', pd.Series(dtype=float))),
            # Market Stress Analysis (calculated from current data)
            'stress_analysis': calculate_market_stress_analysis(df_t, silent=silent),
            # Treasury Settlements with RRP liquidity coverage
            'treasury_settlements': fetch_treasury_settlements(),
            # ================================================================
            # NEW: CLI V2 and Regime V2 Data (from regime_v2 module)
            # ================================================================
            'cli_v2': {
                'cli_v2': clean_for_json(cli_v2_df['CLI_V2']),
                'cli_v2_percentile': clean_for_json(cli_v2_df['CLI_V2_PERCENTILE']),
                'hy_spread_z': clean_for_json(cli_v2_df['HY_SPREAD_Z']),
                'hy_momentum_z': clean_for_json(cli_v2_df['HY_MOMENTUM_Z']),
                'ig_spread_z': clean_for_json(cli_v2_df['IG_SPREAD_Z']),
                'nfci_credit_z': clean_for_json(cli_v2_df['NFCI_CREDIT_Z']),
                'nfci_risk_z': clean_for_json(cli_v2_df['NFCI_RISK_Z']),
                'lending_std_z': clean_for_json(cli_v2_df['LENDING_STD_Z']),
                'move_z': clean_for_json(cli_v2_df['MOVE_Z']),
                'fx_vol_z': clean_for_json(cli_v2_df['FX_VOL_Z']),
                'yield_curve_z': clean_for_json(cli_v2_df['YIELD_CURVE_Z']),
                'real_rate_shock_z': clean_for_json(cli_v2_df['REAL_RATE_SHOCK_Z']),
            },
            'regime_v2a': {
                'score': clean_for_json(regime_v2a['score']),
                'regime_code': clean_for_json(regime_v2a['regime_code']),
                'transition': clean_for_json(regime_v2a['transition']),
                'total_z': clean_for_json(regime_v2a['total_z']),
                'liquidity_z': clean_for_json(regime_v2a['liquidity_z']),
                'credit_z': clean_for_json(regime_v2a['credit_z']),
                'brakes_z': clean_for_json(regime_v2a['brakes_z']),
                'cli_gli_divergence': clean_for_json(regime_v2a['cli_gli_divergence']),
                'z_move': clean_for_json(regime_v2a['z_move']),
                'z_fx_vol': clean_for_json(regime_v2a['z_fx_vol']),
                'z_yield_curve': clean_for_json(regime_v2a['z_yield_curve']),
                'z_inf_divergence': clean_for_json(regime_v2a['z_inf_divergence']),
            },
            'regime_v2b': {
                'score': clean_for_json(regime_v2b['score']),
                'regime_code': clean_for_json(regime_v2b['regime_code']),
                'transition': clean_for_json(regime_v2b['transition']),
                'total_z': clean_for_json(regime_v2b['total_z']),
                'liquidity_z': clean_for_json(regime_v2b['liquidity_z']),
                'credit_z': clean_for_json(regime_v2b['credit_z']),
                'growth_z': clean_for_json(regime_v2b['growth_z']),
                'brakes_z': clean_for_json(regime_v2b['brakes_z']),
                'z_ism': clean_for_json(regime_v2b['z_ism']),
                'z_unemployment': clean_for_json(regime_v2b['z_unemployment']),
                'z_pce_deviation': clean_for_json(regime_v2b['z_pce_deviation']),
                'z_nfp_momentum': clean_for_json(regime_v2b['z_nfp_momentum']),
                'z_fed_momentum': clean_for_json(regime_v2b['z_fed_momentum']),
            },
            'stress_historical': {
                'inflation_stress': clean_for_json(stress_historical['inflation_stress']),
                'liquidity_stress': clean_for_json(stress_historical['liquidity_stress']),
                'credit_stress': clean_for_json(stress_historical['credit_stress']),
                'volatility_stress': clean_for_json(stress_historical['volatility_stress']),
                'total_stress': clean_for_json(stress_historical['total_stress']),
                'total_stress_pct': clean_for_json(stress_historical['total_stress_pct']),
            },
            # Stablecoin Market Analytics
            'stablecoins': {
                'dates': stablecoins_data.get('dates', []),
                'market_caps': {k: clean_for_json(v) for k, v in stablecoins_data.get('market_caps', {}).items()},
                'total': clean_for_json(stablecoins_data.get('total', [])),
                'total_roc_7d': clean_for_json(stablecoins_data.get('total_roc_7d', [])),
                'total_roc_1m': clean_for_json(stablecoins_data.get('total_roc_1m', [])),
                'total_roc_3m': clean_for_json(stablecoins_data.get('total_roc_3m', [])),
                'total_roc_7d_z': clean_for_json(stablecoins_data.get('total_roc_7d_z', [])),
                'total_roc_1m_z': clean_for_json(stablecoins_data.get('total_roc_1m_z', [])),
                'total_roc_3m_z': clean_for_json(stablecoins_data.get('total_roc_3m_z', [])),
                'total_roc_7d_pct': clean_for_json(stablecoins_data.get('total_roc_7d_pct', [])),
                'total_roc_1m_pct': clean_for_json(stablecoins_data.get('total_roc_1m_pct', [])),
                'total_roc_3m_pct': clean_for_json(stablecoins_data.get('total_roc_3m_pct', [])),
                'total_yoy': clean_for_json(stablecoins_data.get('total_yoy', [])),
                'total_accel_z': clean_for_json(stablecoins_data.get('total_accel_z', [])),
                'sfai_continuous': clean_for_json(stablecoins_data.get('sfai_continuous', [])),
                'sfai_regime': stablecoins_data.get('sfai_regime', []),
                'sfai_velocity': clean_for_json(stablecoins_data.get('sfai_velocity', [])),
                'sfai_beta': clean_for_json(stablecoins_data.get('sfai_beta', [])),
                'total_dominance': clean_for_json(stablecoins_data.get('total_dominance', [])),
                'total_crypto_mcap': clean_for_json(stablecoins_data.get('total_crypto_mcap', [])),
                'prices': {k: clean_for_json(v) for k, v in stablecoins_data.get('prices', {}).items()},
                'growth': clean_for_json(stablecoins_data.get('growth', {})),
                'dominance': {k: clean_for_json(v) for k, v in stablecoins_data.get('dominance', {}).items()},
                'dominance_total': {k: clean_for_json(v) for k, v in stablecoins_data.get('dominance_total', {}).items()},
                'depeg_events': clean_for_json(stablecoins_data.get('depeg_events', [])[-1000:]),  # Take LATEST 1000 events
            },
            'treasury_maturities': get_treasury_maturity_data(120),
            'treasury_auction_demand': fetch_treasury_auction_demand(silent=True),
            'treasury_refinancing_signal': get_treasury_refinancing_signal(
                auction_data=fetch_treasury_auction_demand(silent=True),
                fred_data={
                    # Note: _USD columns are already in Trillions. Convert back to billions for legacy wrapper
                    'WALCL': {'values': clean_for_json((df_t['FED_USD'] * 1000).dropna().tolist()) if 'FED_USD' in df_t.columns else []},
                    'WTREGEN': {'values': clean_for_json((df_t['TGA_USD'] * 1000).dropna().tolist()) if 'TGA_USD' in df_t.columns else []},
                    'RRPONTSYD': {'values': clean_for_json((df_t['RRP_USD'] * 1000).dropna().tolist()) if 'RRP_USD' in df_t.columns else []},
                },
                sofr_data={
                    'SOFR': {'values': clean_for_json(df_t['SOFR'].dropna().tolist()) if 'SOFR' in df_t.columns else []},
                    'IORB': {'values': clean_for_json(df_t['IORB'].dropna().tolist()) if 'IORB' in df_t.columns else []},
                },
                silent=True
            ),
            # Offshore Dollar Liquidity
            'offshore_liquidity': get_offshore_liquidity_output(df_t, df_offshore_tv if not df_offshore_tv.empty else None).get('offshore_liquidity', {}),

        }

        output_path = os.path.join(OUTPUT_DIR, filename)
        with open(output_path, 'w') as f:
            json.dump(data_output, f)

    # Generate only the hybrid TV+FRED data (primary source)
    # FRED-only generation removed to avoid duplicate API calls and reduce runtime
    process_and_save_final(df_hybrid_t, 'dashboard_data_tv.json', silent=False)
    
    # Copy to dashboard_data.json for backwards compatibility
    import shutil
    shutil.copyfile(os.path.join(OUTPUT_DIR, 'dashboard_data_tv.json'), os.path.join(OUTPUT_DIR, 'dashboard_data.json'))
    print("Pipeline complete.")

if __name__ == "__main__":
    run_pipeline()
