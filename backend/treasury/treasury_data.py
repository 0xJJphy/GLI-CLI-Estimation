"""
Treasury Data Module
====================
Fetches Treasury maturity data from free government APIs.

Data Sources:
1. FiscalData.Treasury.gov API - Monthly Statement of Public Debt (MSPD)
2. TreasuryDirect API - Securities information

Author: Quantitative Analysis Assistant
Date: January 2026
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import json
from typing import Dict, List, Any, Optional

# ==============================================================================
# GLOBAL CONFIGURATION
# ==============================================================================

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ==============================================================================
# API CONFIGURATION
# ==============================================================================

FISCAL_DATA_BASE_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"

ENDPOINTS = {
    "marketable_securities_detail": "/v1/debt/mspd/mspd_table_3_market",
    "debt_summary": "/v1/debt/mspd/mspd_table_1",
    "auctions": "/v1/debt/treas_auctions/auction_data",
}

TREASURY_DIRECT_BASE_URL = "https://www.treasurydirect.gov/TA_WS"


# ==============================================================================
# DATA FETCHING FUNCTIONS
# ==============================================================================

def fetch_fiscal_data(endpoint: str, params: dict = None, page_size: int = 10000, max_pages: int = 10) -> pd.DataFrame:
    """
    Fetches data from FiscalData.Treasury.gov API with pagination.
    
    Parameters:
        endpoint: API endpoint path
        params: Additional query parameters
        page_size: Records per page
        max_pages: Maximum pages to fetch
        
    Returns:
        DataFrame with fetched data
    """
    url = f"{FISCAL_DATA_BASE_URL}{endpoint}"
    all_data = []
    page = 1
    
    default_params = {
        "page[size]": page_size,
        "format": "json"
    }
    
    if params:
        default_params.update(params)
    
    while page <= max_pages:
        default_params["page[number]"] = page
        
        try:
            response = requests.get(url, params=default_params, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            records = data.get("data", [])
            
            if not records:
                break
                
            all_data.extend(records)
            
            meta = data.get("meta", {})
            total_pages = meta.get("total-pages", 1)
            
            print(f"  [Treasury] Page {page}/{total_pages} - {len(records)} records")
            
            if page >= total_pages:
                break
                
            page += 1
            time.sleep(0.1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"  [Treasury] Request error: {e}")
            break
    
    return pd.DataFrame(all_data)


def get_marketable_securities_outstanding() -> pd.DataFrame:
    """
    Gets marketable securities outstanding with maturity dates.
    Primary source for maturity schedule calculation.
    """
    print("  [Treasury] Fetching marketable securities outstanding...")
    
    params = {
        "sort": "-record_date",
        "fields": "record_date,security_type_desc,security_class1_desc,maturity_date,outstanding_amt"
    }
    
    df = fetch_fiscal_data(ENDPOINTS["marketable_securities_detail"], params)
    
    if df.empty:
        print("  [Treasury] No data from primary endpoint, trying TreasuryDirect...")
        return get_securities_from_treasury_direct()
    
    # Filter to latest record_date only
    if 'record_date' in df.columns and len(df) > 0:
        latest_date = df['record_date'].max()
        df = df[df['record_date'] == latest_date]
        print(f"  [Treasury] Data as of: {latest_date}")
    
    return df


def get_securities_from_treasury_direct() -> pd.DataFrame:
    """
    Fallback: Gets securities from TreasuryDirect API.
    """
    print("  [Treasury] Fetching from TreasuryDirect API...")
    
    all_securities = []
    
    for sec_type in ['Bill', 'Note', 'Bond']:
        url = f"{TREASURY_DIRECT_BASE_URL}/securities/search"
        params = {"type": sec_type, "format": "json"}
        
        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
                df['security_type_desc'] = sec_type
                all_securities.append(df)
                print(f"    {sec_type}: {len(df)} records")
                
        except requests.exceptions.RequestException as e:
            print(f"    {sec_type}: Error - {e}")
    
    if all_securities:
        return pd.concat(all_securities, ignore_index=True)
    
    return pd.DataFrame()


def categorize_security(security_type: str) -> str:
    """Categorizes security type into standard categories."""
    if pd.isna(security_type):
        return 'Unknown'
    
    security_type = str(security_type).upper()
    
    if 'BILL' in security_type or 'CASH MANAGEMENT' in security_type:
        return 'Bills'
    elif 'NOTE' in security_type:
        return 'Notes'
    elif 'BOND' in security_type:
        return 'Bonds'
    elif 'TIP' in security_type:
        return 'TIPS'
    elif 'FRN' in security_type or 'FLOAT' in security_type:
        return 'FRN'
    else:
        return 'Other'


# ==============================================================================
# DATA PROCESSING FUNCTIONS
# ==============================================================================

def calculate_maturity_schedule(df: pd.DataFrame, months_ahead: int = 24) -> Dict[str, Any]:
    """
    Calculates maturity schedule aggregated by month and security type.
    
    Parameters:
        df: DataFrame with securities data
        months_ahead: Number of months to include in forecast
        
    Returns:
        Dictionary with schedule data for frontend charts
    """
    if df.empty:
        return {"months": [], "bills": [], "notes": [], "bonds": [], "tips": [], "frn": [], "total": []}
    
    # Find maturity date column
    maturity_col = None
    amount_col = None
    type_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'maturity' in col_lower and 'date' in col_lower:
            maturity_col = col
        elif 'outstanding' in col_lower or 'amount' in col_lower or 'total_accepted' in col_lower:
            amount_col = col
        elif 'security_class1' in col_lower:  # Use security_class1_desc for categorization
            type_col = col
        elif type_col is None and ('security_type' in col_lower or 'type' in col_lower):
            type_col = col
    
    if not maturity_col:
        print("  [Treasury] No maturity date column found")
        return {"months": [], "bills": [], "notes": [], "bonds": [], "tips": [], "frn": [], "total": []}
    
    # Parse dates
    df['maturity_date_parsed'] = pd.to_datetime(df[maturity_col], errors='coerce')
    df = df.dropna(subset=['maturity_date_parsed'])
    
    # Filter future maturities only
    today = datetime.now()
    max_date = today + timedelta(days=months_ahead * 30)
    df = df[(df['maturity_date_parsed'] >= today) & (df['maturity_date_parsed'] <= max_date)]
    
    if df.empty:
        return {"months": [], "bills": [], "notes": [], "bonds": [], "tips": [], "frn": [], "total": []}
    
    # Convert amounts to numeric (amounts are in millions, convert to billions)
    if amount_col:
        # Handle string 'null' values and convert from millions to billions
        df['amount_numeric'] = pd.to_numeric(df[amount_col].replace('null', None), errors='coerce').fillna(0) / 1000
    else:
        df['amount_numeric'] = 1
    
    # Create month period
    df['maturity_month'] = df['maturity_date_parsed'].dt.to_period('M')
    
    # Categorize security type
    if type_col:
        df['category'] = df[type_col].apply(categorize_security)
    else:
        df['category'] = 'Unknown'
    
    # Aggregate by month and category
    agg = df.groupby(['maturity_month', 'category'])['amount_numeric'].sum().reset_index()
    
    # Pivot to wide format
    pivot = agg.pivot(index='maturity_month', columns='category', values='amount_numeric').fillna(0)
    pivot = pivot.reset_index()
    pivot = pivot.sort_values('maturity_month')
    
    # Convert to output format
    months = [str(m) for m in pivot['maturity_month'].tolist()]
    
    result = {
        "months": months,
        "bills": pivot.get('Bills', pd.Series([0]*len(months))).tolist(),
        "notes": pivot.get('Notes', pd.Series([0]*len(months))).tolist(),
        "bonds": pivot.get('Bonds', pd.Series([0]*len(months))).tolist(),
        "tips": pivot.get('TIPS', pd.Series([0]*len(months))).tolist(),
        "frn": pivot.get('FRN', pd.Series([0]*len(months))).tolist(),
    }
    
    # Calculate totals
    result["total"] = [
        sum(x) for x in zip(
            result["bills"], result["notes"], result["bonds"], 
            result["tips"], result["frn"]
        )
    ]
    
    return result


def calculate_refinancing_metrics(schedule: Dict[str, Any], securities_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates key refinancing metrics.
    
    Returns:
        Dictionary with metrics for frontend display
    """
    metrics = {}
    
    if not schedule.get("months"):
        return metrics
    
    totals = schedule.get("total", [])
    months = schedule.get("months", [])
    bills = schedule.get("bills", [])
    
    # Peak maturity month
    if totals:
        peak_idx = totals.index(max(totals))
        metrics["peak_month"] = months[peak_idx] if peak_idx < len(months) else "N/A"
        metrics["peak_amount"] = max(totals)
    
    # Bills outstanding (sum of all bill maturities)
    metrics["bills_outstanding"] = sum(bills) if bills else 0
    
    # Total outstanding (sum of all maturities in schedule)
    metrics["total_outstanding"] = sum(totals) if totals else 0
    
    # Next 12 months refinancing
    next_12_months = totals[:12] if len(totals) >= 12 else totals
    metrics["next_12m_refinancing"] = sum(next_12_months)
    
    # Forecast horizon (months in schedule)
    metrics["forecast_horizon"] = len(months)
    
    # Record date (from securities data if available)
    if 'record_date' in securities_df.columns:
        metrics["record_date"] = securities_df['record_date'].max()
    else:
        metrics["record_date"] = datetime.now().strftime("%Y-%m-%d")
    
    return metrics


# ==============================================================================
# MAIN DATA FUNCTION
# ==============================================================================

def get_treasury_maturity_data(months_ahead: int = 24, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Main function to get all treasury maturity data with 24-hour caching.
    
    Parameters:
        months_ahead: Number of months to forecast
        force_refresh: If True, bypass cache and fetch new data
        
    Returns:
        Dictionary with schedule and metrics for frontend
    """
    cache_file = os.path.join(OUTPUT_DIR, 'treasury_maturities_cache.json')
    cache_hours = 24

    # Cache helper functions
    def is_cache_fresh():
        if not os.path.exists(cache_file):
            return False
        try:
            file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            hours_elapsed = (datetime.now() - file_mtime).total_seconds() / 3600
            return hours_elapsed < cache_hours
        except Exception:
            return False

    if not force_refresh and is_cache_fresh():
        try:
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
                if cached_data.get('schedule', {}).get('months'):
                    print("[Treasury] Using cached maturity data")
                    return cached_data
        except Exception as e:
            print(f"[Treasury] Cache read error: {e}")

    print("[Treasury] Fetching fresh treasury maturity data...")
    
    try:
        # 1. Get securities data
        securities_df = get_marketable_securities_outstanding()
        
        if securities_df.empty:
            print("[Treasury] No securities data available")
            return {
                "schedule": {"months": [], "bills": [], "notes": [], "bonds": [], "tips": [], "frn": [], "total": []},
                "metrics": {},
                "monthly_table": []
            }
        
        print(f"[Treasury] Processing {len(securities_df)} securities records...")
        
        # 2. Calculate maturity schedule
        schedule = calculate_maturity_schedule(securities_df, months_ahead)
        
        # 3. Calculate metrics
        metrics = calculate_refinancing_metrics(schedule, securities_df)
        
        # 4. Create monthly table data (first 12 months)
        monthly_table = []
        for i, month in enumerate(schedule.get("months", [])[:12]):
            monthly_table.append({
                "month": month,
                "bills": schedule["bills"][i] if i < len(schedule["bills"]) else 0,
                "notes": schedule["notes"][i] if i < len(schedule["notes"]) else 0,
                "bonds": schedule["bonds"][i] if i < len(schedule["bonds"]) else 0,
                "total": schedule["total"][i] if i < len(schedule["total"]) else 0,
            })
        
        print(f"[Treasury] Maturity schedule: {len(schedule.get('months', []))} months")
        
        result = {
            "schedule": schedule,
            "metrics": metrics,
            "monthly_table": monthly_table
        }

        # Save to cache
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f)
            print("[Treasury] Data cached successfully")
        except Exception as e:
            print(f"[Treasury] Cache write error: {e}")
            
        return result
        
    except Exception as e:
        print(f"[Treasury] Error fetching data: {e}")
        return {
            "schedule": {"months": [], "bills": [], "notes": [], "bonds": [], "tips": [], "frn": [], "total": []},
            "metrics": {},
            "monthly_table": []
        }


# ==============================================================================
# TEST
# ==============================================================================

if __name__ == "__main__":
    print("="*60)
    print("  TREASURY MATURITY DATA TEST")
    print("="*60)
    
    result = get_treasury_maturity_data(24)
    
    print("\n📊 SCHEDULE:")
    print(f"  Months: {len(result['schedule']['months'])}")
    
    print("\n📈 METRICS:")
    for key, value in result['metrics'].items():
        if isinstance(value, float):
            print(f"  {key}: ${value:.2f}B")
        else:
            print(f"  {key}: {value}")
    
    print("\n📋 MONTHLY TABLE (first 5):")
    for row in result['monthly_table'][:5]:
        print(f"  {row}")
    
    print("\n" + "="*60)
