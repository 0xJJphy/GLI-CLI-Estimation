"""
Offshore Dollar Liquidity Module
================================
Two separate charts for offshore USD stress monitoring.

CHART 1: FRED PROXY (Opción 3)
------------------------------
Uses freely available FRED data as proxy for offshore USD stress:
- OBFR-EFFR Spread: Onshore vs offshore funding differential
- Fed CB Swaps: Crisis indicator when foreign CBs draw USD liquidity

CHART 2: XCCY BASIS DIY (Opción 2)
----------------------------------
Calculate cross-currency basis from TradingView spot/futures:
- EUR/USD, USD/JPY, GBP/USD basis via CIP deviation
- Composite stress from multiple currency pairs

Data Sources:
- FRED: OBFR, EFFR, SWPT (daily, free, reliable)
- TradingView: FX spots + CME futures (6E, 6J, 6B)

Author: Quantitative Analysis Module
Date: January 2026
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


# ============================================================
# CONFIGURATION
# ============================================================

# FRED series to add (update FRED_CONFIG in data_pipeline.py)
FRED_OFFSHORE_SERIES = {
    'OBFR': 'OBFR',              # Overnight Bank Funding Rate (includes Eurodollars)
    'EFFR': 'EFFR',              # Effective Federal Funds Rate (onshore only)
    'SWPT': 'FED_CB_SWAPS',      # Central Bank Liquidity Swaps Outstanding ($M)
}

# TradingView symbols to add (update TV_CONFIG in data_pipeline.py)
TV_OFFSHORE_SYMBOLS = {
    # FX Spot
    'EURUSD_SPOT': ('FX_IDC', 'EURUSD'),
    'USDJPY_SPOT': ('FX_IDC', 'USDJPY'),
    'GBPUSD_SPOT': ('FX_IDC', 'GBPUSD'),
    # FX Futures
    'EURUSD_FUT': ('CME', '6E1!'),
    'JPYUSD_FUT': ('CME', '6J1!'),
    'GBPUSD_FUT': ('CME', '6B1!'),
}


@dataclass
class CurrencyPairConfig:
    """Configuration for XCCY basis calculation."""
    pair: str
    spot_key: str
    futures_key: str
    futures_quote: str      # 'direct' or 'inverse'
    foreign_rate: float     # Current foreign rate (%, for approximation)
    day_count: int          # 360 or 365
    weight: int             # Importance weight (1-5)
    description: str


CURRENCY_PAIRS = {
    'EURUSD': CurrencyPairConfig(
        pair='EURUSD',
        spot_key='EURUSD_SPOT',
        futures_key='EURUSD_FUT',
        futures_quote='direct',
        foreign_rate=2.90,      # €STR ~2.90%
        day_count=360,
        weight=5,
        description='Euro - European banks'
    ),
    'USDJPY': CurrencyPairConfig(
        pair='USDJPY',
        spot_key='USDJPY_SPOT',
        futures_key='JPYUSD_FUT',
        futures_quote='inverse',  # 6J quotes JPY/USD
        foreign_rate=0.25,        # TONA ~0.25%
        day_count=360,
        weight=5,
        description='Yen - Carry trade'
    ),
    'GBPUSD': CurrencyPairConfig(
        pair='GBPUSD',
        spot_key='GBPUSD_SPOT',
        futures_key='GBPUSD_FUT',
        futures_quote='direct',
        foreign_rate=4.50,        # SONIA ~4.50%
        day_count=365,
        weight=4,
        description='Sterling - London'
    ),
}


# Thresholds for stress levels
class Thresholds:
    """Stress level thresholds based on historical analysis."""
    
    # OBFR-EFFR Spread (basis points)
    # Normal: < 3bp, Elevated: 3-6bp, Stressed: 6-10bp, Critical: > 15bp
    OBFR_EFFR_NORMAL = 3
    OBFR_EFFR_ELEVATED = 6
    OBFR_EFFR_STRESSED = 10
    OBFR_EFFR_CRITICAL = 15
    
    # Fed CB Swaps (billions USD)
    # 2008 peak: $600B, 2020 peak: $449B
    CB_SWAPS_ACTIVE = 0.1
    CB_SWAPS_ELEVATED = 10
    CB_SWAPS_STRESSED = 50
    CB_SWAPS_CRISIS = 100
    
    # XCCY Basis (basis points, more negative = more stress)
    # 2008: EUR -133bp, 2020: EUR -85bp, Normal: -10 to +5bp
    XCCY_NORMAL = -10
    XCCY_ELEVATED = -20
    XCCY_STRESSED = -35
    XCCY_CRISIS = -50


# ============================================================
# CHART 1: FRED PROXY CALCULATIONS
# ============================================================

def calculate_obfr_effr_spread(df: pd.DataFrame) -> pd.Series:
    """
    Calculate OBFR-EFFR spread in basis points.
    
    OBFR includes Eurodollar transactions (offshore USD funding).
    EFFR is purely onshore Fed Funds.
    Positive spread = offshore funding more expensive = USD stress.
    
    Args:
        df: DataFrame with 'OBFR' and 'EFFR' columns (in %)
        
    Returns:
        Spread in basis points
    """
    obfr = df.get('OBFR', pd.Series(dtype=float))
    effr = df.get('EFFR', pd.Series(dtype=float))
    
    if obfr.empty or effr.empty:
        return pd.Series(dtype=float, name='OBFR_EFFR_SPREAD')
    
    # Align and calculate
    aligned = pd.DataFrame({'obfr': obfr, 'effr': effr}).dropna()
    spread = (aligned['obfr'] - aligned['effr']) * 100  # Convert to bp
    spread.name = 'OBFR_EFFR_SPREAD'
    
    return spread


def calculate_cb_swaps_billions(df: pd.DataFrame) -> pd.Series:
    """
    Convert Fed CB Swaps from millions to billions.
    
    Args:
        df: DataFrame with 'FED_CB_SWAPS' column (in $M)
        
    Returns:
        CB Swaps in billions
    """
    swaps = df.get('FED_CB_SWAPS', pd.Series(dtype=float))
    
    if swaps.empty:
        return pd.Series(dtype=float, name='CB_SWAPS_B')
    
    swaps_b = swaps / 1000  # M -> B
    swaps_b.name = 'CB_SWAPS_B'
    
    return swaps_b


def calculate_fred_proxy_stress(
    obfr_effr_spread: pd.Series,
    cb_swaps_b: pd.Series
) -> pd.Series:
    """
    Calculate composite FRED proxy stress index (0-100).
    
    Components:
    - OBFR-EFFR Spread: 70% weight (daily signal)
    - CB Swaps: 30% weight (crisis indicator)
    
    Args:
        obfr_effr_spread: Spread in bp
        cb_swaps_b: CB Swaps in billions
        
    Returns:
        Stress score 0-100
    """
    # Get common index
    idx = obfr_effr_spread.index.union(cb_swaps_b.index)
    stress = pd.Series(0.0, index=idx, name='FRED_PROXY_STRESS')
    
    # Component 1: OBFR-EFFR (70%)
    # Scale: 0bp = 0, 15bp = 100
    if not obfr_effr_spread.empty:
        spread = obfr_effr_spread.reindex(idx).ffill()
        spread_score = (spread / Thresholds.OBFR_EFFR_CRITICAL) * 100
        spread_score = spread_score.clip(0, 100)
        stress += spread_score * 0.70
    
    # Component 2: CB Swaps (30%)
    # Scale: $0B = 0, $200B = 100
    if not cb_swaps_b.empty:
        swaps = cb_swaps_b.reindex(idx).ffill().fillna(0)
        swaps_score = (swaps / 200) * 100
        swaps_score = swaps_score.clip(0, 100)
        stress += swaps_score * 0.30
    
    return stress


def get_chart1_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate all Chart 1 (FRED Proxy) data.
    
    Args:
        df: DataFrame with OBFR, EFFR, FED_CB_SWAPS columns
        
    Returns:
        Dict with series, latest values, signals, stress level
    """
    # Calculate metrics
    spread = calculate_obfr_effr_spread(df)
    swaps_b = calculate_cb_swaps_billions(df)
    stress = calculate_fred_proxy_stress(spread, swaps_b)
    
    # Get latest values
    def safe_last(s):
        if s is None or s.empty:
            return None
        valid = s.dropna()
        return float(valid.iloc[-1]) if not valid.empty else None
    
    latest_spread = safe_last(spread)
    latest_swaps = safe_last(swaps_b)
    latest_stress = safe_last(stress)
    
    # Generate signals
    signals = []
    
    if latest_spread is not None:
        if latest_spread >= Thresholds.OBFR_EFFR_CRITICAL:
            signals.append({
                'level': 'critical',
                'indicator': 'OBFR_EFFR',
                'value': latest_spread,
                'message': f'Severe offshore funding stress: {latest_spread:.1f}bp',
                'implication': 'Eurodollar market severely stressed'
            })
        elif latest_spread >= Thresholds.OBFR_EFFR_STRESSED:
            signals.append({
                'level': 'warning',
                'indicator': 'OBFR_EFFR',
                'value': latest_spread,
                'message': f'Elevated offshore stress: {latest_spread:.1f}bp',
                'implication': 'Offshore USD funding pressure'
            })
        elif latest_spread >= Thresholds.OBFR_EFFR_ELEVATED:
            signals.append({
                'level': 'info',
                'indicator': 'OBFR_EFFR',
                'value': latest_spread,
                'message': f'Mild offshore pressure: {latest_spread:.1f}bp',
                'implication': 'Monitor for deterioration'
            })
    
    if latest_swaps is not None and latest_swaps >= Thresholds.CB_SWAPS_ACTIVE:
        if latest_swaps >= Thresholds.CB_SWAPS_CRISIS:
            signals.append({
                'level': 'critical',
                'indicator': 'CB_SWAPS',
                'value': latest_swaps,
                'message': f'Crisis-level Fed swap usage: ${latest_swaps:.1f}B',
                'implication': 'Global USD liquidity crisis'
            })
        elif latest_swaps >= Thresholds.CB_SWAPS_STRESSED:
            signals.append({
                'level': 'warning',
                'indicator': 'CB_SWAPS',
                'value': latest_swaps,
                'message': f'Significant Fed swap usage: ${latest_swaps:.1f}B',
                'implication': 'Foreign CBs providing USD liquidity'
            })
        else:
            signals.append({
                'level': 'info',
                'indicator': 'CB_SWAPS',
                'value': latest_swaps,
                'message': f'Fed swap lines active: ${latest_swaps:.1f}B',
                'implication': 'Some offshore USD demand'
            })
    
    # Determine stress level
    stress_level = 'normal'
    if latest_stress is not None:
        if latest_stress >= 60:
            stress_level = 'critical'
        elif latest_stress >= 35:
            stress_level = 'stressed'
        elif latest_stress >= 15:
            stress_level = 'elevated'
    
    return {
        'series': {
            'obfr': df.get('OBFR', pd.Series(dtype=float)),
            'effr': df.get('EFFR', pd.Series(dtype=float)),
            'obfr_effr_spread': spread,
            'cb_swaps_b': swaps_b,
            'fred_proxy_stress': stress
        },
        'latest': {
            'obfr': safe_last(df.get('OBFR')),
            'effr': safe_last(df.get('EFFR')),
            'obfr_effr_spread': latest_spread,
            'cb_swaps_b': latest_swaps,
            'fred_proxy_stress': latest_stress
        },
        'signals': signals,
        'stress_level': stress_level,
        'stress_score': latest_stress or 0
    }


# ============================================================
# CHART 2: XCCY BASIS DIY CALCULATIONS
# ============================================================

def calculate_xccy_basis_single(
    spot: float,
    futures: float,
    usd_rate: float,
    foreign_rate: float,
    days: int = 91,
    day_count: int = 360,
    futures_quote: str = 'direct'
) -> float:
    """
    Calculate cross-currency basis from spot/futures using CIP.
    
    Formula:
    - CIP Forward = Spot * (1 + r_USD * t) / (1 + r_foreign * t)
    - Basis = Implied foreign rate - Observed foreign rate
    
    Args:
        spot: FX spot rate
        futures: FX futures price (front month)
        usd_rate: USD rate (SOFR) as decimal
        foreign_rate: Foreign currency rate as decimal
        days: Days to expiry (~91 for 3M)
        day_count: Day count convention (360 or 365)
        futures_quote: 'direct' (EUR/USD) or 'inverse' (6J = JPY/USD)
        
    Returns:
        Basis in basis points (negative = USD shortage)
    """
    if spot <= 0 or futures <= 0:
        return np.nan
    
    t = days / day_count
    
    if futures_quote == 'inverse':
        # 6J is JPY/USD (inverse), convert to USD/JPY
        futures_adj = 1 / futures if futures != 0 else np.nan
        # USD/JPY (indirect): F = S * (1 + r_JPY * t) / (1 + r_USD * t)
        implied_foreign = ((futures_adj / spot) * (1 + usd_rate * t) - 1) / t
    else:
        # Direct quote (EUR/USD, GBP/USD)
        # F = S * (1 + r_USD * t) / (1 + r_foreign * t)
        implied_foreign = ((1 + usd_rate * t) / (futures / spot) - 1) / t
    
    basis_bps = (implied_foreign - foreign_rate) * 10000
    return basis_bps


def calculate_xccy_basis_series(
    spot_series: pd.Series,
    futures_series: pd.Series,
    sofr_series: pd.Series,
    config: CurrencyPairConfig
) -> pd.Series:
    """
    Calculate XCCY basis time series for a currency pair.
    
    Args:
        spot_series: FX spot rate series
        futures_series: FX futures price series
        sofr_series: SOFR rate series (in %)
        config: Currency pair configuration
        
    Returns:
        Basis series in bp
    """
    # Align all series
    df = pd.DataFrame({
        'spot': spot_series,
        'futures': futures_series,
        'sofr': sofr_series
    }).dropna()
    
    if df.empty:
        return pd.Series(dtype=float, name=f'XCCY_{config.pair}')
    
    # Convert rates to decimals
    sofr_dec = df['sofr'] / 100
    foreign_dec = config.foreign_rate / 100
    
    # Calculate basis
    basis_values = []
    for idx, row in df.iterrows():
        basis = calculate_xccy_basis_single(
            spot=row['spot'],
            futures=row['futures'],
            usd_rate=sofr_dec.loc[idx],
            foreign_rate=foreign_dec,
            days=91,
            day_count=config.day_count,
            futures_quote=config.futures_quote
        )
        basis_values.append(basis)
    
    result = pd.Series(basis_values, index=df.index, name=f'XCCY_{config.pair}')
    return result


def calculate_xccy_composite_stress(xccy_series: Dict[str, pd.Series]) -> pd.Series:
    """
    Calculate composite XCCY stress from multiple pairs.
    
    Weighted by importance. More negative = more stress.
    
    Args:
        xccy_series: Dict mapping pair -> basis series
        
    Returns:
        Stress score 0-100
    """
    if not xccy_series:
        return pd.Series(dtype=float, name='XCCY_COMPOSITE_STRESS')
    
    # Get common index
    all_idx = pd.DatetimeIndex([])
    for s in xccy_series.values():
        if not s.empty:
            all_idx = all_idx.union(s.index)
    
    if len(all_idx) == 0:
        return pd.Series(dtype=float, name='XCCY_COMPOSITE_STRESS')
    
    composite = pd.Series(0.0, index=all_idx, name='XCCY_COMPOSITE_STRESS')
    total_weight = 0
    
    for pair, series in xccy_series.items():
        if series.empty:
            continue
        
        config = CURRENCY_PAIRS.get(pair)
        weight = config.weight if config else 3
        
        aligned = series.reindex(all_idx).ffill()
        
        # Scale: 0bp = 0, -50bp = 100
        stress = (-aligned / abs(Thresholds.XCCY_CRISIS)) * 100
        stress = stress.clip(0, 100)
        
        composite += stress * weight
        total_weight += weight
    
    if total_weight > 0:
        composite = composite / total_weight
    
    return composite


def get_chart2_data(df_tv: pd.DataFrame, sofr_series: pd.Series) -> Dict[str, Any]:
    """
    Calculate all Chart 2 (XCCY DIY) data.
    
    Args:
        df_tv: DataFrame with TradingView FX data
        sofr_series: SOFR rate series from FRED (in %)
        
    Returns:
        Dict with series, latest values, signals, stress level
    """
    xccy_series = {}
    xccy_latest = {}
    
    for pair, config in CURRENCY_PAIRS.items():
        spot = df_tv.get(config.spot_key, pd.Series(dtype=float))
        futures = df_tv.get(config.futures_key, pd.Series(dtype=float))
        
        if spot.empty or futures.empty:
            print(f"  -> Missing data for {pair} (spot: {not spot.empty}, futures: {not futures.empty})")
            continue
        
        basis = calculate_xccy_basis_series(spot, futures, sofr_series, config)
        
        if not basis.empty:
            xccy_series[pair] = basis
            valid = basis.dropna()
            xccy_latest[pair] = float(valid.iloc[-1]) if not valid.empty else None
            print(f"  -> {pair}: {xccy_latest[pair]:.1f}bp" if xccy_latest[pair] else f"  -> {pair}: No data")
    
    # Calculate composite
    composite = calculate_xccy_composite_stress(xccy_series)
    
    def safe_last(s):
        if s is None or s.empty:
            return None
        valid = s.dropna()
        return float(valid.iloc[-1]) if not valid.empty else None
    
    latest_composite = safe_last(composite)
    
    # Generate signals
    signals = []
    for pair, basis in xccy_latest.items():
        if basis is None:
            continue
        
        config = CURRENCY_PAIRS.get(pair)
        desc = config.description if config else pair
        
        if basis <= Thresholds.XCCY_CRISIS:
            signals.append({
                'level': 'critical',
                'indicator': f'XCCY_{pair}',
                'value': basis,
                'message': f'{pair} basis at {basis:.1f}bp - severe USD shortage',
                'implication': f'Crisis in {desc}'
            })
        elif basis <= Thresholds.XCCY_STRESSED:
            signals.append({
                'level': 'warning',
                'indicator': f'XCCY_{pair}',
                'value': basis,
                'message': f'{pair} basis at {basis:.1f}bp - elevated USD cost',
                'implication': f'Stress in {desc}'
            })
        elif basis <= Thresholds.XCCY_ELEVATED:
            signals.append({
                'level': 'info',
                'indicator': f'XCCY_{pair}',
                'value': basis,
                'message': f'{pair} basis at {basis:.1f}bp - mild pressure',
                'implication': f'Monitor {desc}'
            })
    
    # Determine stress level
    stress_level = 'normal'
    if latest_composite is not None:
        if latest_composite >= 60:
            stress_level = 'critical'
        elif latest_composite >= 35:
            stress_level = 'stressed'
        elif latest_composite >= 15:
            stress_level = 'elevated'
    
    return {
        'series': {
            'xccy_eurusd': xccy_series.get('EURUSD', pd.Series(dtype=float)),
            'xccy_usdjpy': xccy_series.get('USDJPY', pd.Series(dtype=float)),
            'xccy_gbpusd': xccy_series.get('GBPUSD', pd.Series(dtype=float)),
            'xccy_composite_stress': composite
        },
        'latest': {
            'xccy_eurusd': xccy_latest.get('EURUSD'),
            'xccy_usdjpy': xccy_latest.get('USDJPY'),
            'xccy_gbpusd': xccy_latest.get('GBPUSD'),
            'xccy_composite_stress': latest_composite
        },
        'signals': signals,
        'stress_level': stress_level,
        'stress_score': latest_composite or 0
    }


# ============================================================
# PROFESSIONAL STATISTICAL ANALYTICS
# ============================================================

def calculate_series_statistics(series: pd.Series, lookback_years: int = 5) -> Dict[str, Any]:
    """
    Calculate comprehensive statistics for a time series.
    
    Returns percentiles, z-scores, and descriptive stats for professional analysis.
    Uses a rolling lookback window to avoid look-ahead bias.
    
    Args:
        series: Pandas Series with datetime index
        lookback_years: Years of history for percentile/z-score calculation
        
    Returns:
        Dict with current value, percentile, z-score, and descriptive stats
    """
    if series is None or series.empty:
        return {}
    
    valid = series.dropna()
    if len(valid) < 20:  # Need minimum data
        return {}
    
    current = float(valid.iloc[-1])
    lookback_days = lookback_years * 252  # Trading days
    
    # Use rolling lookback for percentile (avoid look-ahead)
    lookback_series = valid.iloc[-lookback_days:] if len(valid) > lookback_days else valid
    
    # Current percentile rank (0-100)
    percentile = float((lookback_series < current).mean() * 100)
    
    # Z-score vs lookback period
    mean = float(lookback_series.mean())
    std = float(lookback_series.std())
    zscore = float((current - mean) / std) if std > 0 else 0
    
    # Descriptive stats
    stats = {
        'current': round(current, 2),
        'percentile': round(percentile, 1),  # 0-100 rank
        'zscore': round(zscore, 2),
        'mean': round(mean, 2),
        'std': round(std, 2),
        'median': round(float(lookback_series.median()), 2),
        'min': round(float(lookback_series.min()), 2),
        'max': round(float(lookback_series.max()), 2),
        'p10': round(float(lookback_series.quantile(0.10)), 2),
        'p25': round(float(lookback_series.quantile(0.25)), 2),
        'p75': round(float(lookback_series.quantile(0.75)), 2),
        'p90': round(float(lookback_series.quantile(0.90)), 2),
        'lookback_days': len(lookback_series),
    }
    
    return stats


def generate_stress_analysis(spread_stats: Dict, swaps_stats: Dict, 
                            xccy_stats: Dict = None) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate professional structured analysis.
    
    Returns categorized items with levels (info, warning, critical, success).
    """
    items_en = []
    items_es = []
    
    # OBFR-EFFR Spread Analysis
    if spread_stats and 'percentile' in spread_stats:
        pct = spread_stats['percentile']
        z = spread_stats['zscore']
        current = spread_stats['current']
        
        item = {'title_en': 'Offshore Spread', 'title_es': 'Spread Offshore'}
        if pct >= 90:
            item.update({'icon': '⚠️', 'level': 'critical',
                'en': f"OBFR-EFFR at {current:.1f}bp is in the {pct:.0f}th percentile ({z:+.1f}σ). Severe Eurodollar stress detectec.",
                'es': f"OBFR-EFFR de {current:.1f}bp en percentil {pct:.0f} ({z:+.1f}σ). Estrés severo detectado en Eurodólar."})
        elif pct >= 75:
            item.update({'icon': '⚡', 'level': 'warning',
                'en': f"OBFR-EFFR at {current:.1f}bp is elevated ({pct:.0f}th percentile, {z:+.1f}σ). Increased funding pressure.",
                'es': f"OBFR-EFFR de {current:.1f}bp está elevado (percentil {pct:.0f}, {z:+.1f}σ). Presión de financiación en aumento."})
        elif pct <= 25:
            item.update({'icon': '✅', 'level': 'success',
                'en': f"OBFR-EFFR at {current:.1f}bp is low ({pct:.0f}th percentile). Funding markets remain relaxed.",
                'es': f"OBFR-EFFR de {current:.1f}bp es bajo (percentil {pct:.0f}). Mercados de financiación relajados."})
        else:
            item.update({'icon': '📊', 'level': 'info',
                'en': f"OBFR-EFFR at {current:.1f}bp is within normal historical range ({pct:.0f}th percentile).",
                'es': f"OBFR-EFFR de {current:.1f}bp dentro del rango histórico normal (percentil {pct:.0f})."})
        
        items_en.append({'icon': item['icon'], 'title': item['title_en'], 'text': item['en'], 'level': item['level']})
        items_es.append({'icon': item['icon'], 'title': item['title_es'], 'text': item['es'], 'level': item['level']})
    
    # CB Swaps Analysis
    if swaps_stats and 'current' in swaps_stats:
        current = swaps_stats['current']
        item = {'title_en': 'CB Swap Lines', 'title_es': 'Líneas Swap BC'}
        if current > 50:
            item.update({'icon': '🚨', 'level': 'critical',
                'en': f"Fed CB Swaps at ${current:.1f}B indicate major global liquidity stress. Intense USD demand.",
                'es': f"Swaps BC a ${current:.1f}B indican gran estrés de liquidez global. Intensa demanda de USD."})
        elif current > 1:
            item.update({'icon': '⚡', 'level': 'warning',
                'en': f"CB Swap Lines active at ${current:.1f}B. Foreign banks drawing USD liquidity.",
                'es': f"Líneas Swap activas a ${current:.1f}B. Bancos extranjeros obteniendo liquidez USD."})
        else:
            item.update({'icon': '📉', 'level': 'info',
                'en': f"CB Swap usage is minimal (${current:.1f}B). Global liquidity conditions are stable.",
                'es': f"Uso de Swaps es mínimo (${current:.1f}B). Condiciones de liquidez global estables."})
        
        items_en.append({'icon': item['icon'], 'title': item['title_en'], 'text': item['en'], 'level': item['level']})
        items_es.append({'icon': item['icon'], 'title': item['title_es'], 'text': item['es'], 'level': item['level']})

    # XCCY Basis Analysis
    if xccy_stats and 'percentile' in xccy_stats:
        pct = xccy_stats['percentile']
        current = xccy_stats['current']
        item = {'title_en': 'XCCY Basis', 'title_es': 'Basis XCCY'}
        
        if pct >= 85:
            item.update({'icon': '🌐', 'level': 'critical',
                'en': f"XCCY Composite Stress at {current:.1f} ({pct:.0f}th percentile). Extreme USD scarcity in FX markets.",
                'es': f"Estrés XCCY en {current:.1f} (percentil {pct:.0f}). Escasez extrema de USD en mercados FX."})
        elif pct >= 70:
            item.update({'icon': '⚠️', 'level': 'warning',
                'en': f"XCCY Basis stress is elevated ({pct:.0f}th percentile). USD funding premium rising.",
                'es': f"Estrés en Basis XCCY elevado (percentil {pct:.0f}). Prima de USD en aumento."})
        else:
            item.update({'icon': '📊', 'level': 'info',
                'en': f"XCCY Basis at {current:.1f} is within normal levels ({pct:.0f}th percentile).",
                'es': f"Basis XCCY en {current:.1f} está en niveles normales (percentil {pct:.0f})."})
        
        items_en.append({'icon': item['icon'], 'title': item['title_en'], 'text': item['en'], 'level': item['level']})
        items_es.append({'icon': item['icon'], 'title': item['title_es'], 'text': item['es'], 'level': item['level']})
    
    return {'en': items_en, 'es': items_es}


# ============================================================
# MAIN DASHBOARD OUTPUT
# ============================================================

def clean_series_for_json(s: pd.Series) -> List:
    """Convert series to JSON-safe list."""
    if s is None or s.empty:
        return []
    return [None if pd.isna(x) or np.isinf(x) else round(float(x), 4) for x in s]


def get_offshore_liquidity_output(
    df_fred: pd.DataFrame,
    df_tv: pd.DataFrame = None
) -> Dict:
    """
    Generate complete offshore liquidity output for dashboard.
    
    Args:
        df_fred: DataFrame with FRED data (must have OBFR, EFFR, FED_CB_SWAPS, SOFR)
        df_tv: DataFrame with TradingView FX data (optional)
        
    Returns:
        Dict ready for JSON serialization
    """
    print("Calculating Offshore Dollar Liquidity...")
    
    # Chart 1: FRED Proxy
    print("  Chart 1: FRED Proxy...")
    chart1 = get_chart1_data(df_fred)
    
    # Chart 2: XCCY DIY (if TV data available)
    chart2 = None
    if df_tv is not None and not df_tv.empty:
        print("  Chart 2: XCCY DIY...")
        sofr = df_fred.get('SOFR', pd.Series(dtype=float))
        if not sofr.empty:
            chart2 = get_chart2_data(df_tv, sofr)
        else:
            print("  -> Warning: SOFR not available, skipping Chart 2")
    
    # Get dates for x-axis
    def get_dates(s):
        if s is None or s.empty:
            return []
        return s.index.strftime('%Y-%m-%d').tolist()

    # PROFESSIONAL STATS & ANALYSIS
    print("  Calculating Statistics & Analysis...")
    spread_stats = calculate_series_statistics(chart1['series']['obfr_effr_spread'])
    swaps_stats = calculate_series_statistics(chart1['series']['cb_swaps_b'])
    xccy_stats = calculate_series_statistics(chart2['series']['xccy_composite_stress']) if chart2 else None
    
    analysis = generate_stress_analysis(spread_stats, swaps_stats, xccy_stats)
    
    output = {
        'offshore_liquidity': {
            'analysis': analysis,
            'stats': {
                'spread': spread_stats,
                'swaps': swaps_stats,
                'xccy': xccy_stats
            },
            # Chart 1: FRED Proxy
            'chart1_fred_proxy': {
                'obfr': clean_series_for_json(chart1['series']['obfr']),
                'effr': clean_series_for_json(chart1['series']['effr']),
                'obfr_effr_spread': clean_series_for_json(chart1['series']['obfr_effr_spread']),
                'cb_swaps_b': clean_series_for_json(chart1['series']['cb_swaps_b']),
                'fred_proxy_stress': clean_series_for_json(chart1['series']['fred_proxy_stress']),
                'dates': get_dates(chart1['series']['obfr_effr_spread']),
                'latest': {
                    **chart1['latest'],
                    'spread_zscore': spread_stats.get('zscore', 0),
                    'spread_percentile': spread_stats.get('percentile', 0),
                    'swaps_zscore': swaps_stats.get('zscore', 0),
                    'swaps_percentile': swaps_stats.get('percentile', 0),
                },
                'signals': chart1['signals'],
                'stress_level': chart1['stress_level'],
                'stress_score': round(chart1['stress_score'], 2)
            },
            
            # Chart 2: XCCY DIY (may be null if no TV data)
            'chart2_xccy_diy': {
                'xccy_eurusd': clean_series_for_json(chart2['series']['xccy_eurusd']) if chart2 else [],
                'xccy_usdjpy': clean_series_for_json(chart2['series']['xccy_usdjpy']) if chart2 else [],
                'xccy_gbpusd': clean_series_for_json(chart2['series']['xccy_gbpusd']) if chart2 else [],
                'xccy_composite_stress': clean_series_for_json(chart2['series']['xccy_composite_stress']) if chart2 else [],
                'dates': get_dates(chart2['series']['xccy_eurusd']) if chart2 else [],
                'latest': {
                    **(chart2['latest'] if chart2 else {}),
                    'zscore': xccy_stats.get('zscore', 0) if xccy_stats else 0,
                    'percentile': xccy_stats.get('percentile', 0) if xccy_stats else 0,
                },
                'signals': chart2['signals'] if chart2 else [],
                'stress_level': chart2['stress_level'] if chart2 else 'unknown',
                'stress_score': round(chart2['stress_score'], 2) if chart2 else 0
            } if chart2 else None,
            
            # Thresholds for frontend charts
            'thresholds': {
                'obfr_effr': {
                    'normal': Thresholds.OBFR_EFFR_NORMAL,
                    'elevated': Thresholds.OBFR_EFFR_ELEVATED,
                    'stressed': Thresholds.OBFR_EFFR_STRESSED,
                    'critical': Thresholds.OBFR_EFFR_CRITICAL
                },
                'cb_swaps': {
                    'active': Thresholds.CB_SWAPS_ACTIVE,
                    'elevated': Thresholds.CB_SWAPS_ELEVATED,
                    'stressed': Thresholds.CB_SWAPS_STRESSED,
                    'crisis': Thresholds.CB_SWAPS_CRISIS
                },
                'xccy': {
                    'normal': Thresholds.XCCY_NORMAL,
                    'elevated': Thresholds.XCCY_ELEVATED,
                    'stressed': Thresholds.XCCY_STRESSED,
                    'crisis': Thresholds.XCCY_CRISIS
                }
            }
        }
    }
    
    return output


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("OFFSHORE DOLLAR LIQUIDITY MODULE - TEST")
    print("=" * 70)
    
    # Simulate data for testing
    dates = pd.date_range('2024-01-01', periods=252, freq='B')
    np.random.seed(42)
    
    # FRED mock data
    df_fred = pd.DataFrame({
        'OBFR': 4.33 + np.random.randn(252) * 0.01,
        'EFFR': 4.33 + np.random.randn(252) * 0.01,
        'FED_CB_SWAPS': np.abs(np.random.randn(252) * 100),  # in millions
        'SOFR': 4.30 + np.random.randn(252) * 0.02
    }, index=dates)
    
    # TradingView mock data
    df_tv = pd.DataFrame({
        'EURUSD_SPOT': 1.08 + np.random.randn(252) * 0.01,
        'EURUSD_FUT': 1.082 + np.random.randn(252) * 0.01,
        'USDJPY_SPOT': 150 + np.random.randn(252) * 2,
        'JPYUSD_FUT': 0.00667 + np.random.randn(252) * 0.0001,  # 6J quote
        'GBPUSD_SPOT': 1.27 + np.random.randn(252) * 0.01,
        'GBPUSD_FUT': 1.272 + np.random.randn(252) * 0.01,
    }, index=dates)
    
    # Run calculation
    output = get_offshore_liquidity_output(df_fred, df_tv)
    
    print("\n📊 Chart 1: FRED Proxy")
    print("-" * 50)
    c1 = output['offshore_liquidity']['chart1_fred_proxy']
    print(f"  OBFR-EFFR Spread: {c1['latest']['obfr_effr_spread']:.2f} bp")
    print(f"  CB Swaps: ${c1['latest']['cb_swaps_b']:.2f}B")
    print(f"  Stress Score: {c1['stress_score']:.1f}/100")
    print(f"  Stress Level: {c1['stress_level']}")
    
    if output['offshore_liquidity']['chart2_xccy_diy']:
        print("\n📈 Chart 2: XCCY DIY")
        print("-" * 50)
        c2 = output['offshore_liquidity']['chart2_xccy_diy']
        for pair in ['eurusd', 'usdjpy', 'gbpusd']:
            val = c2['latest'].get(f'xccy_{pair}')
            if val:
                print(f"  {pair.upper()}: {val:.1f} bp")
        print(f"  Composite Stress: {c2['stress_score']:.1f}/100")
        print(f"  Stress Level: {c2['stress_level']}")
    
    print("\n" + "=" * 70)
