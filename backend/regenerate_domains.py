
import json
import pandas as pd
import numpy as np
import os
import sys

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from domains.cli import CLIDomain
from domains.core import USSystemDomain, SharedDomain
from domains.base import clean_for_json

def regenerate():
    print("Loading backend/data/dashboard_data.json for source data...")
    try:
        with open('backend/data/dashboard_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: backend/data/dashboard_data.json not found.")
        return

    print("Loading frontend/public/domains/shared.json for master dates...")
    try:
        with open('frontend/public/domains/shared.json', 'r') as f:
            shared_data = json.load(f)
        master_dates = pd.to_datetime(shared_data['dates'])
    except FileNotFoundError:
        print("Warning: frontend/public/domains/shared.json not found. Falling back to dashboard_data dates.")
        master_dates = pd.to_datetime(data['dates'])

    df = pd.DataFrame(index=master_dates)
    
    # Helper to safe load series from data and align to df index
    def get_series(key, subkey=None):
        if key not in data:
            return pd.Series(np.nan, index=master_dates)
        
        val = data[key]
        if subkey:
            if isinstance(val, dict) and subkey in val:
                val = val[subkey]
            else:
                return pd.Series(np.nan, index=master_dates)
        
        if not isinstance(val, list):
            return pd.Series(np.nan, index=master_dates)
            
        # Create series with source dates and then reindex to master_dates
        source_dates = pd.to_datetime(data['dates'])
        if len(val) != len(source_dates):
            # Try to handle cases where subkey might have different length
            # Some segments like maturities/auctions inside 'treasury' are not series
            return pd.Series(np.nan, index=master_dates)
            
        s = pd.Series(val, index=source_dates)
        return s.reindex(master_dates)

    # Reconstruct columns for CLI
    print("Reconstructing CLI inputs...")
    df['HY_SPREAD'] = get_series('hy_spread')
    df['IG_SPREAD'] = get_series('ig_spread')
    df['NFCI_CREDIT'] = get_series('nfci_credit')
    df['NFCI_RISK'] = get_series('nfci_risk')
    df['LENDING_STD'] = get_series('lending')
    df['VIX'] = get_series('vix')
    df['MOVE'] = get_series('move')
    df['FX_VOL'] = get_series('fx_vol')

    # Reconstruct columns for US System
    print("Reconstructing US System inputs...")
    df['SOFR'] = get_series('repo_stress', 'sofr')
    df['IORB'] = get_series('repo_stress', 'iorb')
    df['SRF_RATE'] = get_series('repo_stress', 'srf_rate')
    df['RRP_AWARD'] = get_series('repo_stress', 'rrp_award')
    df['SRF_USAGE'] = get_series('repo_stress', 'srf_usage')
    
    # Financial Stress
    df['ST_LOUIS_STRESS'] = get_series('st_louis_stress')
    df['KANSAS_CITY_STRESS'] = get_series('kansas_city_stress')
    
    # US Net Liq components are flattened in dashboard_data.json
    df['RRP_USD'] = get_series('us_net_liq_rrp')
    df['TGA_USD'] = get_series('us_net_liq_tga')
    df['BANK_RESERVES'] = get_series('us_net_liq_reserves')
    
    # Net Liquidity is under 'us_net_liq' key directly (as list)
    net_liq = get_series('us_net_liq')
    
    df['FED_USD'] = net_liq + df['TGA_USD'] + df['RRP_USD']

    # Treasury Inputs
    print("Reconstructing Treasury inputs...")
    df['TREASURY_2Y_YIELD'] = get_series('treasury_2y')
    df['TREASURY_5Y_YIELD'] = get_series('treasury_5y')
    df['TREASURY_10Y_YIELD'] = get_series('treasury_10y')
    df['TREASURY_30Y_YIELD'] = get_series('treasury_30y')
    df['BAA_YIELD'] = get_series('baa_yield')
    df['AAA_YIELD'] = get_series('aaa_yield')

    # Fed Forecasts Inputs
    print("Reconstructing Fed Forecasts inputs...")
    # Map dashboard_data keys to what FedForecastsDomain expects
    df['INFLATION_EXPECT_1Y'] = get_series('inflation_expect_1y')
    df['CLEV_EXPINF_5Y'] = get_series('inflation_expect_5y') # Mapping to 5Y slot
    df['CLEV_EXPINF_10Y'] = get_series('inflation_expect_10y') # Mapping to 10Y slot
    # Also grab inflation if available
    # cpi_yoy not in top keys list? 
    # Use what we have.

    # Process CLI
    print("Processing CLI Domain...")
    cli_dom = CLIDomain()
    cli_res = cli_dom.process(df)
    
    # Process US System
    print("Processing US System Domain...")
    us_dom = USSystemDomain()
    us_res = us_dom.process(df)

    # Process Treasury
    print("Processing Treasury Domain...")
    from domains.treasury import TreasuryDomain
    treasury_dom = TreasuryDomain()
    treasury_res = treasury_dom.process(df)

    # Process Fed Forecasts
    print("Processing Fed Forecasts Domain...")
    from domains.fed_forecasts import FedForecastsDomain
    fed_dom = FedForecastsDomain()
    fed_res = fed_dom.process(df)

    # Save
    os.makedirs('frontend/public/domains', exist_ok=True)
    
    with open('frontend/public/domains/cli.json', 'w') as f:
        json.dump(cli_res, f)
    print("Saved frontend/public/domains/cli.json")
    
    with open('frontend/public/domains/us_system.json', 'w') as f:
        json.dump(us_res, f)
    print("Saved frontend/public/domains/us_system.json")
 
    with open('frontend/public/domains/treasury.json', 'w') as f:
        json.dump(treasury_res, f)
    print("Saved frontend/public/domains/treasury.json")
 
    with open('frontend/public/domains/fed_forecasts.json', 'w') as f:
        json.dump(fed_res, f)
    print("Saved frontend/public/domains/fed_forecasts.json")

if __name__ == "__main__":
    regenerate()
