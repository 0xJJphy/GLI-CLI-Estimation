import pandas as pd
import numpy as np
import requests
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def fetch_fear_and_greed() -> pd.Series:
    """
    Fetches the Fear & Greed Index from alternative.me
    Returns a pandas Series with timestamp index and values.
    """
    try:
        url = "https://api.alternative.me/fng/?limit=0"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('metadata', {}).get('error'):
            logger.error(f"F&G API Error: {data['metadata']['error']}")
            return pd.Series(dtype=float)
            
        df = pd.DataFrame(data['data'])
        # Convert timestamp and set index
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['value'] = df['value'].astype(float)
        df = df.set_index('timestamp').sort_index()
        
        # Resample to daily to ensure consistency with other data
        # 'D' resampling might lose the latest value if not careful, 
        # but the pipeline usually runs once a day.
        df = df['value'].resample('D').last().ffill()
        return df
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed Index: {e}")
        return pd.Series(dtype=float)

def _zscore_roll_safe(s: pd.Series, window: int = 252, min_periods: int = 100) -> pd.Series:
    """Safe rolling z-score implementation."""
    s = s.astype(float).replace([np.inf, -np.inf], np.nan)
    mu = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std().replace(0, np.nan)
    return (s - mu) / sd

def _percentile_rank_roll(s: pd.Series, window: int = 252) -> pd.Series:
    """Rolling percentile rank (0-100)."""
    return s.rolling(window).rank(pct=True) * 100

def calculate_crypto_regimes(df: pd.DataFrame, custom_stables: pd.Series = None) -> Dict[str, Any]:
    """
    Calculates crypto market regimes based on capital rotation.
    Expects df with columns: TOTAL_MCAP, BTC_MCAP, TOTAL3_MCAP
    Can use custom_stables (Series) for better historical coverage.
    """
    # 1. Data Prep (Convert to Billions)
    m_total = df['TOTAL_MCAP'].ffill() / 1e9
    m_btc = df['BTC_MCAP'].ffill() / 1e9
    
    # Use custom aggregates if provided, otherwise fallback to STABLE.C
    if custom_stables is not None:
        m_stable = custom_stables.ffill().reindex(df.index).fillna(0)
    else:
        m_stable = (df['STABLE_INDEX_MCAP'].ffill() / 1e9) if 'STABLE_INDEX_MCAP' in df.columns else pd.Series(0, index=df.index)
    
    # Calculate m_risk (Pure Risk Assets: Alts excluding Stables)
    # We use (Total - BTC - Stablecoins) as the most robust baseline for history
    m_risk = (m_total - m_btc - m_stable).clip(lower=0.1)

    # 2. Transformations (Log-Ratios)
    # Relative Strength of Risk vs BTC
    rs_risk_btc = np.log(m_risk / m_btc)
    # Relative Strength of Stable vs Risk
    rs_stable_risk = np.log(m_stable / m_risk)

    # 3. Momentum (30-day change in log-ratios)
    delta_rs_risk = rs_risk_btc.diff(30)
    delta_rs_stable = rs_stable_risk.diff(30)
    
    # 4. Returns (30-day ROC)
    r_total = m_total.pct_change(30)
    r_stable = m_stable.pct_change(30)
    r_btc = m_btc.pct_change(30)

    # 5. Hierarchical Regime Classification
    # Priority: Capitulation > Stable Refuge > Flight to Quality > Alt Season > BTC Season
    regime = pd.Series(index=df.index, dtype=object)
    
    # Thresholds
    T_CAPITULATION_TOTAL = -0.15  # -15% total mcap contraction
    T_CAPITULATION_STABLE = -0.01 # Stablecoin outflow
    T_MOMENTUM = 0.005           # 0.5% log-ratio change

    # Apply Logic
    is_capitulation = (r_total < T_CAPITULATION_TOTAL) & (r_stable < T_CAPITULATION_STABLE)
    is_stable_refuge = (r_total < 0) & (delta_rs_stable > T_MOMENTUM)
    is_flight_to_quality = (r_total < 0) & (delta_rs_risk < -T_MOMENTUM)
    is_alt_season = (delta_rs_risk > T_MOMENTUM) & (r_stable >= 0)
    is_btc_season = (delta_rs_risk < -T_MOMENTUM) & (r_btc > 0)

    # Assign with precedence
    regime = np.where(is_capitulation, "Capitulation",
             np.where(is_stable_refuge, "Stable Refuge",
             np.where(is_flight_to_quality, "Flight to Quality",
             np.where(is_alt_season, "Alt Season",
             np.where(is_btc_season, "BTC Season", "Side-ways/Neutral")))))
    
    regime_series = pd.Series(regime, index=df.index)

    # 6. Altseason Index (CAI) - Refactored for better normalization
    # Step 1: 90-day momentum in the log Alts/BTC ratio
    rs_90 = rs_risk_btc.diff(90)
    
    # Step 2: Use expanding window (all available history) for z-score
    # This provides better normalization across market cycles
    rs_90_clean = rs_90.astype(float).replace([np.inf, -np.inf], np.nan)
    
    # Use expanding window with min 90 days for stable statistics
    mu = rs_90_clean.expanding(min_periods=90).mean()
    sd = rs_90_clean.expanding(min_periods=90).std().replace(0, np.nan)
    z_rs_90 = (rs_90_clean - mu) / sd
    
    # Step 3: Convert z-score to 0-100 scale using CDF (sigmoid-like)
    # This naturally handles extremes without saturation
    # z=0 -> 50, z=2 -> ~98, z=-2 -> ~2
    from scipy.stats import norm
    cai_raw = pd.Series(norm.cdf(z_rs_90) * 100, index=df.index)
    
    # Apply a light smoothing to reduce noise
    cai = cai_raw.rolling(7, min_periods=1).mean()

    return {
        "regime": regime_series,
        "cai": cai,
        "rs_risk_btc": rs_risk_btc,
        "delta_rs_risk": delta_rs_risk,
        "m_risk": m_risk
    }

def calculate_narratives(df: pd.DataFrame, m_risk: pd.Series) -> Dict[str, Any]:
    """
    Calculates narrative-specific metrics: Relative Strength and Share of Alts.
    """
    narrative_map = {
        'DEFI_MCAP': 'DeFi',
        'MEME_MCAP': 'Meme',
        'AI_MCAP': 'AI',
        'LAYER1_MCAP': 'L1',
        'DEPIN_MCAP': 'DePIN',
        'RWA_MCAP': 'RWA'
    }
    
    results = {}
    for col, name in narrative_map.items():
        if col in df.columns:
            m_narrative = df[col].ffill() / 1e9
            
            # 1. log(Narrative / BTC)
            rs_btc = np.log(m_narrative / (df['BTC_MCAP'] / 1e9))
            mom_btc = rs_btc.diff(30)
            
            # 2. Share of Alts: log(Narrative / TotalRisk)
            share_of_alts = np.log(m_narrative / m_risk)
            mom_share = share_of_alts.diff(30)
            
            results[name] = {
                "mcap": m_narrative.tolist(),
                "mom_btc": mom_btc.tolist(),
                "mom_share": mom_share.tolist(),
                "current_mcap": float(m_narrative.iloc[-1]) if not m_narrative.empty else 0,
                "current_mom_btc": float(mom_btc.iloc[-1]) if not mom_btc.empty else 0,
                "current_mom_share": float(mom_share.iloc[-1]) if not mom_share.empty else 0
            }
            
    return results


def calculate_series_analytics(s: pd.Series, window_z: int = 90, window_pct: int = 365) -> Dict[str, Any]:
    """
    Generalized analytics for any sentiment or momentum series.
    Calculates ROCs, Z-Scores, and Percentiles for 7d, 30d, 90d, 180d, and 365d.
    """
    if s.empty:
        return {}

    # 1. ROCs (absolute change)
    rocs = {
        "7d": s.diff(7),
        "30d": s.diff(30),
        "90d": s.diff(90),
        "180d": s.diff(180),
        "365d": s.diff(365),
    }

    # 2. Z-Scores and Percentiles
    results = {}
    for period, roc in rocs.items():
        w_z = window_z if period in ["7d", "30d"] else (window_z * 2 if period == "90d" else window_pct)
        w_p = window_pct if period in ["7d", "30d"] else (window_pct * 2 if period == "90d" else window_pct * 3)
        
        results[f"roc_{period}"] = roc
        results[f"roc_{period}_z"] = _zscore_roll_safe(roc, window=w_z, min_periods=max(14, w_z // 3))
        results[f"roc_{period}_pct"] = _percentile_rank_roll(roc, window=w_p)

    # 3. Current values
    def safe_last(series):
        vals = series.dropna()
        return float(vals.iloc[-1]) if len(vals) > 0 else None

    for k in list(results.keys()):
        results[f"current_{k}"] = safe_last(results[k])

    return results

def calculate_fng_analytics(fng_series: pd.Series) -> Dict[str, Any]:
    """Fear & Greed specific analytics wrapper."""
    return calculate_series_analytics(fng_series)

def calculate_crypto_regimes(df: pd.DataFrame, custom_stables: pd.Series = None) -> Dict[str, Any]:
    """
    Calculates crypto market regimes based on capital rotation.
    Expects df with columns: TOTAL_MCAP, BTC_MCAP, TOTAL3_MCAP
    Can use custom_stables (Series) for better historical coverage.
    """
    # 1. Data Prep (Convert to Billions)
    m_total = df['TOTAL_MCAP'].ffill() / 1e9
    m_btc = df['BTC_MCAP'].ffill() / 1e9
    
    # Use custom aggregates if provided, otherwise fallback to STABLE.C
    if custom_stables is not None:
        m_stable = custom_stables.ffill().reindex(df.index).fillna(0)
    else:
        m_stable = (df['STABLE_INDEX_MCAP'].ffill() / 1e9) if 'STABLE_INDEX_MCAP' in df.columns else pd.Series(0, index=df.index)
    
    # Calculate m_risk (Pure Risk Assets: Alts excluding Stables)
    m_risk = (m_total - m_btc - m_stable).clip(lower=0.1)

    # 2. Transformations (Log-Ratios)
    rs_risk_btc = np.log(m_risk / m_btc)
    rs_stable_risk = np.log(m_stable / m_risk)

    # 3. Momentum (30-day change in log-ratios)
    delta_rs_risk = rs_risk_btc.diff(30)
    delta_rs_stable = rs_stable_risk.diff(30)
    
    # 4. Returns (30-day ROC)
    r_total = m_total.pct_change(30)
    r_stable = m_stable.pct_change(30)
    r_btc = m_btc.pct_change(30)

    # 5. Hierarchical Regime Classification
    T_CAPITULATION_TOTAL = -0.15
    T_CAPITULATION_STABLE = -0.01
    T_MOMENTUM = 0.005

    is_capitulation = (r_total < T_CAPITULATION_TOTAL) & (r_stable < T_CAPITULATION_STABLE)
    is_stable_refuge = (r_total < 0) & (delta_rs_stable > T_MOMENTUM)
    is_flight_to_quality = (r_total < 0) & (delta_rs_risk < -T_MOMENTUM)
    is_alt_season = (delta_rs_risk > T_MOMENTUM) & (r_stable >= 0)
    is_btc_season = (delta_rs_risk < -T_MOMENTUM) & (r_btc > 0)

    regime = np.where(is_capitulation, "Capitulation",
             np.where(is_stable_refuge, "Stable Refuge",
             np.where(is_flight_to_quality, "Flight to Quality",
             np.where(is_alt_season, "Alt Season",
             np.where(is_btc_season, "BTC Season", "Side-ways/Neutral")))))
    
    regime_series = pd.Series(regime, index=df.index)

    # 6. Altseason Index (CAI)
    rs_90 = rs_risk_btc.diff(90)
    rs_90_clean = rs_90.astype(float).replace([np.inf, -np.inf], np.nan)
    
    mu = rs_90_clean.expanding(min_periods=90).mean()
    sd = rs_90_clean.expanding(min_periods=90).std().replace(0, np.nan)
    z_rs_90 = (rs_90_clean - mu) / sd
    
    from scipy.stats import norm
    cai_raw = pd.Series(norm.cdf(z_rs_90) * 100, index=df.index)
    cai = cai_raw.rolling(7, min_periods=1).mean()

    # Expand CAI analytics (ROCs, Z-Scores, etc)
    cai_analytics = calculate_series_analytics(cai)

    return {
        "regime": regime_series,
        "cai": cai,
        "cai_analytics": cai_analytics,
        "rs_risk_btc": rs_risk_btc,
        "delta_rs_risk": delta_rs_risk,
        "m_risk": m_risk
    }
