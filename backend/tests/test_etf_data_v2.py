
import os
import json
import pandas as pd
import numpy as np
from sqlalchemy import create_all, text
from dotenv import load_dotenv
from etf_data import fetch_etf_data, get_db_connection

load_dotenv()

def test():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to DB")
        return
        
    try:
        data = fetch_etf_data(conn)
        print("Keys in data:", data.keys())
        
        # Check summary
        df_summary = pd.DataFrame(data['summary'])
        print("\nSummary Columns:", df_summary.columns.tolist())
        print("Sample Summary data (first 3):")
        print(df_summary[['ticker', 'premium_discount', 'aum_usd']].head(3))
        
        # Check flows_agg
        df_agg = pd.DataFrame(data['flows_agg'])
        print("\nAggregated flows columns:", df_agg.columns.tolist())
        print("Sample Rolling Flows (last 5):")
        print(df_agg[['date', 'total_flow_usd', 'flow_usd_7d', 'flow_usd_30d', 'flow_usd_ma20']].tail(5))
        
        # Save to output file for manual check
        with open('backend/data/etf_data_test.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\nSaved to backend/data/etf_data_test.json")
        
    finally:
        conn.close()

if __name__ == "__main__":
    test()
