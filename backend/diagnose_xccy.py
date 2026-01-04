import json
import pandas as pd
import numpy as np
from offshore_liquidity import calculate_xccy_basis_single, calculate_days_to_maturity, CURRENCY_PAIRS
from rates_sources import ForeignRateFetcher

def diagnose():
    try:
        with open('data/dashboard_data.json', 'r') as f:
            d = json.load(f)
    except Exception as e:
        print(f"Error loading dashboard_data.json: {e}")
        return

    # FRED data
    fred_data = {}
    
    # Load FRED directly from cache for completeness
    try:
        with open('data/fred_cache_data.json', 'r') as f:
            fred_cache = json.load(f)
        for k in ['SOFR', 'OBFR', 'EFFR', 'SOFR_INDEX', 'SONIA_INDEX', 'ESTR']:
            if k in fred_cache:
                fred_data[k] = pd.Series(fred_cache[k]['values'], index=pd.to_datetime(fred_cache[k]['dates']))
    except Exception as e:
        print(f"Error loading fred_cache_data.json: {e}")

    df_fred = pd.DataFrame(fred_data)
    
    # TV data
    try:
        with open('data/tv_cache_data.json', 'r') as f:
            tv_cache = json.load(f)
        
        df_tv = pd.DataFrame()
        for name, data in tv_cache.items():
            s = pd.Series(data['values'], index=pd.to_datetime(data['dates']), name=name)
            df_tv[name] = s
        
        # Add aliases
        df_tv['EURUSD'] = df_tv.get('EURUSD', df_tv.get('FX:EURUSD'))
        df_tv['USDJPY'] = df_tv.get('USDJPY', df_tv.get('FX:USDJPY'))
        df_tv['GBPUSD'] = df_tv.get('GBPUSD', df_tv.get('FX:GBPUSD'))
        df_tv['EURUSD_FUT'] = df_tv.get('EURUSD_FUT', df_tv.get('CME_MINI:E71!'))
        df_tv['JPYUSD_FUT'] = df_tv.get('JPYUSD_FUT', df_tv.get('CME:6J1!'))
        df_tv['GBPUSD_FUT'] = df_tv.get('GBPUSD_FUT', df_tv.get('CME:6B1!'))

        print("\n--- Rates Verification (Latest) ---")
        fetcher = ForeignRateFetcher(df_fred)
        eur_3m = fetcher.get_eur_3m_rate()
        gbp_3m = fetcher.get_gbp_3m_rate()
        jpy_3m = fetcher.get_jpy_3m_rate(lookback_years=1) # Fast check
        sofr = df_fred.get('SOFR', pd.Series(dtype=float))
        
        print(f"SOFR (Daily): {sofr.dropna().iloc[-1] if not sofr.dropna().empty else 'N/A'}%")
        print(f"EUR 3M (€STR): {eur_3m.dropna().iloc[-1] if not eur_3m.dropna().empty else 'N/A'}%")
        print(f"GBP 3M (SONIA): {gbp_3m.dropna().iloc[-1] if not gbp_3m.dropna().empty else 'N/A'}%")
        print(f"JPY 3M (BoJ): {jpy_3m.dropna().iloc[-1] if not jpy_3m.dropna().empty else 'N/A'}%")

        print("\n--- Basis Recalculation (Live Proxy) ---")
        for pair in ['EURUSD', 'USDJPY', 'GBPUSD']:
            config = CURRENCY_PAIRS[pair]
            if config.spot_key in df_tv and config.futures_key in df_tv:
                spot = df_tv[config.spot_key].dropna().iloc[-1]
                futures = df_tv[config.futures_key].dropna().iloc[-1]
                usd_rate = sofr.dropna().iloc[-1] / 100 if not sofr.dropna().empty else 0.045
                
                f_rate_key = config.foreign_leg.key
                f_rate_series = {'EUR_3M': eur_3m, 'GBP_3M': gbp_3m, 'JPY_3M': jpy_3m}.get(f_rate_key)
                f_rate = f_rate_series.dropna().iloc[-1] / 100 if f_rate_series is not None and not f_rate_series.dropna().empty else 0.0
                
                days = calculate_days_to_maturity(pd.Timestamp.now())
                basis = calculate_xccy_basis_single(spot, futures, usd_rate, f_rate, days=days, quote_type=config.futures_quote)
                print(f"{pair}: {basis:+.2f} bp (Spot: {spot:.4f}, Fut: {futures:.4f})")
            else:
                print(f"{pair}: Keys missing in TV data")

    except Exception as e:
        print(f"Error in diagnosis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose()
