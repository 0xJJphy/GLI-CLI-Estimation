# Configuration Package

"""
Configuration modules for signals and data sources.

Contains:
- signal_config: Unified signal configuration and scoring
- rates_sources: Rate source configurations
"""

from .signal_config import (
    compute_signal, 
    SIGNAL_CONFIG, 
    SignalState, 
    STATE_SCORES,
    STANCE_KEYS, 
    aggregate_signal_score, 
    validate_weights
)
