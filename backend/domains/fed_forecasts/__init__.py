"""
Fed Forecasts Domain - FOMC, Dot Plot, Inflation

Contains:
- FOMC calendar
- Dot plot projections
- Macro indicators (CPI, PCE, Unemployment, NFP)
- Fed Funds futures probabilities
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

from ..base import BaseDomain, clean_for_json


class FedForecastsDomain(BaseDomain):
    """Fed Forecasts domain."""
    
    @property
    def name(self) -> str:
        return "fed_forecasts"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Process Fed forecasts data."""
        result = {}
        
        # Inflation YoY (from index levels, using 365 day change for daily data)
        inflation_cols = {
            'cpi_yoy': 'CPI',
            'core_cpi_yoy': 'CORE_CPI',
            'pce_yoy': 'PCE',
            'core_pce_yoy': 'CORE_PCE'
        }
        
        for name, col in inflation_cols.items():
            if col in df.columns:
                series = df[col].ffill()
                yoy = series.pct_change(365) * 100
                result[name] = clean_for_json(yoy)
        
        # Labor market
        if 'UNEMPLOYMENT' in df.columns:
            result['unemployment'] = clean_for_json(df['UNEMPLOYMENT'].ffill())
        
        if 'NFP' in df.columns:
            nfp = df['NFP'].ffill()
            result['nfp'] = clean_for_json(nfp)
            result['nfp_change'] = clean_for_json(nfp.diff(22))
        
        if 'JOLTS' in df.columns:
            result['jolts'] = clean_for_json(df['JOLTS'].ffill())
        
        # Fed Funds Rate
        if 'FED_FUNDS_RATE' in df.columns:
            result['fed_funds_rate'] = clean_for_json(df['FED_FUNDS_RATE'].ffill())
        
        # ISM PMIs (from TV data)
        if 'ISM_MFG' in df.columns:
            result['ism_mfg'] = clean_for_json(df['ISM_MFG'].ffill())
        if 'ISM_SVC' in df.columns:
            result['ism_svc'] = clean_for_json(df['ISM_SVC'].ffill())
        
        # Inflation expectations
        inf_expect_cols = {
            'cleveland_1y': 'INFLATION_EXPECT_1Y',
            'cleveland_2y': 'CLEV_EXPINF_2Y',
            'cleveland_5y': 'CLEV_EXPINF_5Y',
            'cleveland_10y': 'CLEV_EXPINF_10Y',
        }
        
        result['inflation_expectations'] = {}
        for name, col in inf_expect_cols.items():
            if col in df.columns:
                result['inflation_expectations'][name] = clean_for_json(df[col].ffill())
        
        # TIPS breakevens (from treasury domain reference)
        result['tips_ref'] = 'treasury.tips'
        
        # Note: FOMC calendar and Dot Plot are fetched via separate API calls
        # in data_pipeline.py - not duplicated here
        result['fomc_dates_ref'] = 'external_api'
        result['dot_plot_ref'] = 'external_api'
        
        return result
