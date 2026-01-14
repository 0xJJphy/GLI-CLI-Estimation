"""
Domain Tests

Tests for domain processors to ensure:
- Output schema validation
- Data integrity (no NaN where not expected)
- Backward compatibility with legacy format
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domains.base import BaseDomain, MetadataDomain, clean_for_json, calculate_rocs
from domains.currencies import CurrenciesDomain


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def sample_df():
    """Create sample DataFrame with test data."""
    dates = pd.date_range(start='2020-01-01', end='2024-01-01', freq='D')
    np.random.seed(42)
    
    n = len(dates)
    
    return pd.DataFrame({
        'DXY': 100 + np.cumsum(np.random.randn(n) * 0.1),
        'EURUSD': 1.1 + np.cumsum(np.random.randn(n) * 0.001),
        'JPYUSD': 0.0067 + np.cumsum(np.random.randn(n) * 0.0001),
        'GBPUSD': 1.25 + np.cumsum(np.random.randn(n) * 0.001),
        'AUDUSD': 0.65 + np.cumsum(np.random.randn(n) * 0.001),
        'CADUSD': 0.75 + np.cumsum(np.random.randn(n) * 0.001),
        'CHFUSD': 1.1 + np.cumsum(np.random.randn(n) * 0.001),
        'CNYUSD': 0.14 + np.cumsum(np.random.randn(n) * 0.0001),
        'BTC': 30000 + np.cumsum(np.random.randn(n) * 100),
    }, index=dates)


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    domains_dir = tmp_path / "domains"
    domains_dir.mkdir()
    return str(tmp_path)


# ============================================================
# BASE DOMAIN TESTS
# ============================================================

class TestCleanForJson:
    """Tests for clean_for_json utility."""
    
    def test_handles_series(self):
        s = pd.Series([1.0, 2.0, np.nan, 4.0])
        result = clean_for_json(s)
        assert result == [1.0, 2.0, None, 4.0]
    
    def test_handles_numpy_types(self):
        assert clean_for_json(np.int64(42)) == 42
        assert clean_for_json(np.float64(3.14)) == 3.14
        assert clean_for_json(np.nan) is None
        assert clean_for_json(np.inf) is None
    
    def test_handles_datetime(self):
        dt = datetime(2024, 1, 15, 10, 30)
        result = clean_for_json(dt)
        assert '2024-01-15' in result
    
    def test_handles_nested_dicts(self):
        data = {
            'series': pd.Series([1, 2, 3]),
            'nested': {'value': np.float64(1.5)}
        }
        result = clean_for_json(data)
        assert result['series'] == [1, 2, 3]
        assert result['nested']['value'] == 1.5


class TestCalculateRocs:
    """Tests for ROC calculation."""
    
    def test_returns_all_periods(self):
        s = pd.Series([100.0] * 300)
        rocs = calculate_rocs(s)
        assert '1M' in rocs
        assert '3M' in rocs
        assert '6M' in rocs
        assert '1Y' in rocs
    
    def test_empty_series_returns_empty(self):
        rocs = calculate_rocs(pd.Series(dtype=float))
        assert rocs == {}


class TestMetadataDomain:
    """Tests for MetadataDomain."""
    
    def test_generates_dates(self, sample_df):
        domain = MetadataDomain()
        result = domain.process(sample_df)
        
        assert 'dates' in result
        assert len(result['dates']) == len(sample_df)
        assert result['dates'][0] == '2020-01-01'
    
    def test_tracks_last_dates(self, sample_df):
        domain = MetadataDomain()
        result = domain.process(sample_df)
        
        assert 'last_dates' in result
        assert 'DXY' in result['last_dates']
    
    def test_includes_timestamp(self, sample_df):
        domain = MetadataDomain()
        result = domain.process(sample_df)
        
        assert 'timestamp' in result


# ============================================================
# CURRENCIES DOMAIN TESTS
# ============================================================

class TestCurrenciesDomain:
    """Tests for CurrenciesDomain."""
    
    def test_process_returns_required_keys(self, sample_df):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        
        assert 'dates' in result
        assert 'dxy' in result
        assert 'pairs' in result
        assert 'btc' in result
    
    def test_dxy_has_all_metrics(self, sample_df):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        
        dxy = result['dxy']
        assert 'absolute' in dxy
        assert 'roc_7d' in dxy
        assert 'roc_30d' in dxy
        assert 'volatility' in dxy
        assert 'roc_7d_z' in dxy
        assert 'roc_7d_pct' in dxy
    
    def test_pairs_has_major_currencies(self, sample_df):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        
        pairs = result['pairs']
        assert 'EUR' in pairs
        assert 'JPY' in pairs
        assert 'GBP' in pairs
    
    def test_btc_has_rocs(self, sample_df):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        
        btc = result['btc']
        assert 'absolute' in btc
        assert 'roc_7d' in btc
        assert 'roc_yoy' in btc
    
    def test_validation_passes(self, sample_df):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        clean_result = clean_for_json(result)
        
        assert domain.validate(clean_result) is True
    
    def test_save_creates_file(self, sample_df, temp_output_dir):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        
        output_path = domain.save_json(result, temp_output_dir)
        
        assert os.path.exists(output_path)
        assert 'currencies.json' in output_path
    
    def test_saved_json_is_valid(self, sample_df, temp_output_dir):
        domain = CurrenciesDomain()
        result = domain.process(sample_df)
        output_path = domain.save_json(result, temp_output_dir)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['dates'][0] == '2020-01-01'
        assert 'dxy' in loaded


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
