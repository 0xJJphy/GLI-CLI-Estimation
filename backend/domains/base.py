"""
Base Domain Class and Utilities

Provides common functionality for all data domains:
- JSON serialization utilities
- Schema validation
- File I/O operations
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def clean_for_json(obj: Any) -> Any:
    """
    Convert Pandas/NumPy objects to JSON-serializable format.
    
    Handles:
    - pd.Series -> list
    - pd.DataFrame -> dict of lists
    - np.nan/np.inf -> None
    - np.int64/float64 -> Python native types
    - datetime/date -> ISO string
    """
    if obj is None:
        return None
    
    if isinstance(obj, pd.Series):
        return [clean_for_json(x) for x in obj.tolist()]
    
    if isinstance(obj, pd.DataFrame):
        return {col: clean_for_json(obj[col]) for col in obj.columns}
    
    if isinstance(obj, np.ndarray):
        return [clean_for_json(x) for x in obj.tolist()]
    
    if isinstance(obj, (np.integer, np.int64)):
        return int(obj)
    
    if isinstance(obj, (np.floating, np.float64)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple)):
        return [clean_for_json(x) for x in obj]
    
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    
    return obj


def calculate_rocs(series: pd.Series) -> Dict[str, pd.Series]:
    """
    Calculate Rate of Change for multiple periods.
    
    Returns dict with keys: '1M', '3M', '6M', '1Y'
    """
    if series is None or series.empty:
        return {}
    
    return {
        '1M': series.pct_change(22) * 100,    # ~1 month (trading days)
        '3M': series.pct_change(66) * 100,    # ~3 months
        '6M': series.pct_change(132) * 100,   # ~6 months
        '1Y': series.pct_change(252) * 100,   # ~1 year
    }


def calculate_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """Calculate rolling Z-score."""
    if series is None or series.empty:
        return pd.Series(dtype=float)
    
    rolling_mean = series.rolling(window, min_periods=window // 4).mean()
    rolling_std = series.rolling(window, min_periods=window // 4).std()
    return (series - rolling_mean) / rolling_std


def rolling_percentile(series: pd.Series, window: int = 252 * 5, min_periods: int = 126) -> pd.Series:
    """
    Calculate rolling percentile rank of each value.
    
    Returns values between 0 and 100.
    """
    if series is None or series.empty:
        return pd.Series(dtype=float)
    
    def percentile_rank(arr):
        if len(arr) < min_periods:
            return np.nan
        current = arr[-1]
        if np.isnan(current):
            return np.nan
        return (arr[:-1] < current).sum() / (len(arr) - 1) * 100
    
    return series.rolling(window, min_periods=min_periods).apply(percentile_rank, raw=True)


def get_safe_last_date(series: pd.Series) -> Optional[str]:
    """Get last valid date from series, or None if empty."""
    if series is None or series.empty:
        return None
    last_valid = series.dropna().index[-1] if not series.dropna().empty else None
    return last_valid.strftime('%Y-%m-%d') if last_valid else None


class BaseDomain(ABC):
    """
    Abstract base class for all data domains.
    
    Subclasses must implement:
    - name: Domain identifier (e.g., 'gli', 'm2')
    - process(): Main data processing logic
    
    Optional overrides:
    - validate(): Custom schema validation
    - get_schema(): Return JSON schema for validation
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Domain identifier used for file naming and logging."""
        pass
    
    @property
    def output_filename(self) -> str:
        """JSON output filename. Override if custom naming needed."""
        return f"{self.name}.json"
    
    @abstractmethod
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """
        Process raw DataFrame and return domain-specific output.
        
        Args:
            df: Main DataFrame with all columns
            **kwargs: Additional context (e.g., other domain outputs)
        
        Returns:
            Dict ready for JSON serialization
        """
        pass
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate output data against schema.
        Override for custom validation logic.
        
        Returns True if valid, raises ValueError if not.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Domain {self.name}: output must be a dict")
        return True
    
    def get_schema(self) -> Optional[Dict]:
        """
        Return JSON schema for this domain.
        Override to provide validation schema.
        """
        return None
    
    def save_json(self, data: Dict[str, Any], output_dir: str) -> str:
        """
        Save domain data to JSON file.
        
        Args:
            data: Processed domain data
            output_dir: Directory path for output
        
        Returns:
            Full path to saved file
        """
        # Create domains subdirectory if needed
        domains_dir = os.path.join(output_dir, 'domains')
        os.makedirs(domains_dir, exist_ok=True)
        
        output_path = os.path.join(domains_dir, self.output_filename)
        
        # Clean data for JSON serialization
        clean_data = clean_for_json(data)
        
        # Validate before saving
        self.validate(clean_data)
        
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(clean_data, f)
        
        logger.info(f"Saved {self.name} domain to {output_path}")
        return output_path
    
    def load_json(self, output_dir: str) -> Optional[Dict[str, Any]]:
        """
        Load domain data from JSON file.
        
        Returns None if file doesn't exist.
        """
        domains_dir = os.path.join(output_dir, 'domains')
        file_path = os.path.join(domains_dir, self.output_filename)
        
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            return json.load(f)


class MetadataDomain(BaseDomain):
    """
    Special domain for shared metadata (dates, timestamps, series info).
    
    This domain is always processed first and provides the shared date index
    for all other domains.
    """
    
    @property
    def name(self) -> str:
        return "metadata"
    
    def process(self, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Generate metadata with dates and series info."""
        return {
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'last_dates': {
                col: get_safe_last_date(df[col]) 
                for col in df.columns
            },
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_start': df.index.min().strftime('%Y-%m-%d') if not df.empty else None,
            'data_end': df.index.max().strftime('%Y-%m-%d') if not df.empty else None,
            'total_rows': len(df),
            'total_columns': len(df.columns),
        }
