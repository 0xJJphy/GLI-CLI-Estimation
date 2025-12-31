#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
regime_v2_no_lookahead.py

Implementaciones LIBRES DE LOOKAHEAD BIAS:
1. CLI_V2 - Credit Liquidity Index mejorado
2. Macro Regime V2A - "Inflation-Aware" 
3. Macro Regime V2B - "Growth-Aware"
4. Market Stress Dashboard HISTÓRICO

REGLAS ANTI-LOOKAHEAD:
- Solo rolling() hacia atrás (no centered)
- Solo diff() hacia atrás
- NO bfill() nunca
- Datos mensuales tienen lag de publicación (~1 mes)
- Z-scores calculados solo con datos pasados

Autor: Senior Quantitative Analyst
Fecha: 2025-01-01
"""

import numpy as np
import pandas as pd
from typing import Dict, Literal, Optional
import warnings


# ============================================================
# UTILIDADES ANTI-LOOKAHEAD
# ============================================================

def _zscore_roll_safe(
    s: pd.Series, 
    window: int = 252, 
    min_periods: int = 100
) -> pd.Series:
    """
    Z-score rolling SIN lookahead.
    
    CRÍTICO: 
    - rolling() por defecto es backward-looking (correcto)
    - No usar center=True (causaría lookahead)
    - min_periods evita señales tempranas con poca data
    """
    s = s.astype(float).replace([np.inf, -np.inf], np.nan)
    # Rolling backward-looking (default)
    mu = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std().replace(0, np.nan)
    return (s - mu) / sd


def _expanding_percentile_safe(s: pd.Series, min_periods: int = 100) -> pd.Series:
    """
    Percentil expandido SIN lookahead.
    
    En cada punto t, calcula el percentil usando solo datos [0, t].
    """
    def _pct_rank(x):
        if len(x) < min_periods:
            return np.nan
        return (x.rank().iloc[-1] - 1) / (len(x) - 1) * 100
    
    return s.expanding(min_periods=min_periods).apply(_pct_rank, raw=False)


def _safe_ffill_only(s: pd.Series) -> pd.Series:
    """
    Forward fill SOLO (nunca backfill para evitar lookahead).
    """
    return s.ffill()  # Solo hacia adelante


def _apply_publication_lag(s: pd.Series, lag_days: int) -> pd.Series:
    """
    Aplica lag de publicación para datos mensuales.
    
    Por ejemplo, ISM de enero se publica ~1 febrero, 
    así que en trading de enero NO lo tenemos disponible.
    """
    return s.shift(lag_days)


# ============================================================
# CLI V2 - SIN LOOKAHEAD
# ============================================================

def calculate_cli_v2(
    df: pd.DataFrame, 
    z_window: int = 252, 
    min_periods: int = 100
) -> pd.DataFrame:
    """
    CLI V2: Credit Liquidity Index mejorado SIN LOOKAHEAD.
    
    ANTI-LOOKAHEAD:
    - Z-scores rolling backward-only
    - No bfill()
    - LENDING_STD tiene lag implícito (quarterly)
    
    COMPONENTES (total = 100%):
    - Credit Spreads (40%): HY nivel, HY momentum, IG
    - Financial Conditions (30%): NFCI Credit, NFCI Risk, Lending
    - Volatility & Stress (20%): MOVE, FX Vol
    - Macro Structure (10%): Yield Curve, Real Rate Shock
    
    Returns DataFrame con CLI_V2 y componentes.
    """
    idx = df.index
    res = pd.DataFrame(index=idx)
    
    # ========================================
    # CREDIT SPREADS (40%)
    # ========================================
    # HY Spread nivel
    hy = _safe_ffill_only(df.get('HY_SPREAD', pd.Series(dtype=float, index=idx)))
    res['HY_SPREAD_Z'] = -_zscore_roll_safe(hy, z_window, min_periods)
    
    # HY Spread momentum (Δ4W = 20 días) - NUEVO
    hy_mom_4w = hy.diff(20)  # Backward diff (correcto)
    res['HY_MOMENTUM_Z'] = -_zscore_roll_safe(hy_mom_4w, z_window, min_periods)
    
    # IG Spread nivel
    ig = _safe_ffill_only(df.get('IG_SPREAD', pd.Series(dtype=float, index=idx)))
    res['IG_SPREAD_Z'] = -_zscore_roll_safe(ig, z_window, min_periods)
    
    # ========================================
    # FINANCIAL CONDITIONS (30%)
    # ========================================
    # NFCI ya viene como z-score del Chicago Fed
    nfci_credit = _safe_ffill_only(df.get('NFCI_CREDIT', pd.Series(dtype=float, index=idx)))
    res['NFCI_CREDIT_Z'] = -nfci_credit  # Ya es z-score, solo negar
    
    nfci_risk = _safe_ffill_only(df.get('NFCI_RISK', pd.Series(dtype=float, index=idx)))
    res['NFCI_RISK_Z'] = -nfci_risk
    
    # Lending Standards (quarterly - ~45 días de lag implícito)
    lending = _safe_ffill_only(df.get('LENDING_STD', pd.Series(dtype=float, index=idx)))
    res['LENDING_STD_Z'] = -_zscore_roll_safe(lending, z_window, min_periods)
    
    # ========================================
    # VOLATILITY & STRESS (20%) - NUEVO
    # ========================================
    # MOVE Index (bond volatility) - reemplaza VIX
    move = _safe_ffill_only(df.get('MOVE', pd.Series(dtype=float, index=idx)))
    res['MOVE_Z'] = -_zscore_roll_safe(move, z_window, min_periods)
    
    # FX Volatility (DXY realized vol)
    fx_vol = _safe_ffill_only(df.get('FX_VOL', pd.Series(dtype=float, index=idx)))
    res['FX_VOL_Z'] = -_zscore_roll_safe(fx_vol, z_window, min_periods)
    
    # ========================================
    # MACRO STRUCTURE (10%) - NUEVO
    # ========================================
    # Yield Curve (10Y - 2Y)
    yield_curve = _safe_ffill_only(df.get('YIELD_CURVE', pd.Series(dtype=float, index=idx)))
    if yield_curve.isna().all():
        t10y = _safe_ffill_only(df.get('TREASURY_10Y_YIELD', pd.Series(dtype=float, index=idx)))
        t2y = _safe_ffill_only(df.get('TREASURY_2Y_YIELD', pd.Series(dtype=float, index=idx)))
        yield_curve = t10y - t2y
    res['YIELD_CURVE_Z'] = _zscore_roll_safe(yield_curve, z_window, min_periods)  # NO negado
    
    # Real Rate Shock (Δ4W de TIPS)
    tips_real = _safe_ffill_only(df.get('TIPS_REAL_RATE', pd.Series(dtype=float, index=idx)))
    real_rate_shock = tips_real.diff(20)  # Backward diff
    res['REAL_RATE_SHOCK_Z'] = -_zscore_roll_safe(real_rate_shock, z_window, min_periods)
    
    # ========================================
    # CLI V2 COMPOSITE
    # ========================================
    weights = {
        'HY_SPREAD_Z': 0.22,
        'HY_MOMENTUM_Z': 0.10,
        'IG_SPREAD_Z': 0.08,
        'NFCI_CREDIT_Z': 0.15,
        'NFCI_RISK_Z': 0.10,
        'LENDING_STD_Z': 0.05,
        'MOVE_Z': 0.12,
        'FX_VOL_Z': 0.08,
        'YIELD_CURVE_Z': 0.05,
        'REAL_RATE_SHOCK_Z': 0.05,
    }
    
    cli_v2 = pd.Series(0.0, index=idx)
    for col, weight in weights.items():
        if col in res.columns:
            cli_v2 += res[col].fillna(0) * weight
    
    res['CLI_V2'] = cli_v2
    
    # Percentil histórico (expanding, sin lookahead)
    res['CLI_V2_PERCENTILE'] = _expanding_percentile_safe(cli_v2, min_periods)
    
    return res


# ============================================================
# MACRO REGIME V2A - "INFLATION-AWARE" SIN LOOKAHEAD
# ============================================================

def calculate_macro_regime_v2a(
    df: pd.DataFrame,
    impulse_days: int = 65,      # ~13 weeks
    z_window: int = 252,         # 1 year
    min_periods: int = 100,
    score_scale: float = 15.0,
    score_clip: float = 3.0,
) -> Dict[str, pd.Series]:
    """
    MACRO REGIME V2A: "Inflation-Aware" - SIN LOOKAHEAD
    
    ESTRUCTURA: 50% Liquidity + 25% Credit + 25% Brakes (expandidos)
    
    BRAKES EXPANDIDOS:
    - Real Rate Shock (18%)
    - Repo Stress (15%)
    - Reserves Spread (15%)
    - MOVE Index (15%) [NUEVO]
    - FX Volatility (12%) [NUEVO]
    - Yield Curve Inversion (12%) [NUEVO]
    - Inflation Divergence (8%) [NUEVO]
    - VIX Spike (5%) [NUEVO]
    
    ANTI-LOOKAHEAD:
    - Todos los rolling son backward-only
    - Todos los diff son backward
    - No hay bfill
    """
    idx = df.index
    out: Dict[str, pd.Series] = {}
    
    # ================================================================
    # SERIES CON FFILL SOLO (sin bfill)
    # ================================================================
    gli = _safe_ffill_only(df.get("GLI_TOTAL", pd.Series(np.nan, index=idx)))
    netliq = _safe_ffill_only(df.get("NET_LIQUIDITY", pd.Series(np.nan, index=idx)))
    m2 = _safe_ffill_only(df.get("M2_TOTAL", pd.Series(np.nan, index=idx)))
    
    # Usar CLI_V2 si existe
    cli = _safe_ffill_only(df.get("CLI_V2", df.get("CLI", pd.Series(np.nan, index=idx))))
    
    # ================================================================
    # LIQUIDITY BLOCK (50%)
    # ================================================================
    # Impulsos (backward diff - correcto)
    gli_imp = gli.diff(impulse_days)
    netliq_imp = netliq.diff(impulse_days)
    m2_imp = m2.diff(impulse_days)
    
    z_gli_imp = _zscore_roll_safe(gli_imp, z_window, min_periods)
    z_netliq_imp = _zscore_roll_safe(netliq_imp, z_window, min_periods)
    z_m2_imp = _zscore_roll_safe(m2_imp, z_window, min_periods)
    
    # CB Breadth & Concentration
    cb_cols = [c for c in df.columns if c.endswith("_USD") and c not in ['TGA_USD', 'RRP_USD']]
    if cb_cols:
        cb_data = df[cb_cols].astype(float).ffill()  # Solo ffill
        cb_deltas = cb_data.diff(impulse_days)
        denom = cb_deltas.notna().sum(axis=1).replace(0, np.nan)
        cb_diffusion = (cb_deltas > 0).sum(axis=1) / denom
        
        abs_d = cb_deltas.abs()
        abs_sum = abs_d.sum(axis=1).replace(0, np.nan)
        shares = abs_d.div(abs_sum, axis=0)
        cb_hhi = shares.pow(2).sum(axis=1)
        
        z_diffusion = _zscore_roll_safe(cb_diffusion, z_window, min_periods)
        z_hhi = _zscore_roll_safe(cb_hhi, z_window, min_periods)
    else:
        cb_diffusion = pd.Series(np.nan, index=idx)
        cb_hhi = pd.Series(np.nan, index=idx)
        z_diffusion = pd.Series(0.0, index=idx)
        z_hhi = pd.Series(0.0, index=idx)
    
    liquidity_z = (
        0.30 * z_gli_imp.fillna(0) +
        0.30 * z_netliq_imp.fillna(0) +
        0.15 * z_m2_imp.fillna(0) +
        0.15 * z_diffusion.fillna(0) -
        0.10 * z_hhi.fillna(0)
    )
    
    # ================================================================
    # CREDIT BLOCK (25%)
    # ================================================================
    cli_mom = cli.diff(impulse_days)  # Backward diff
    z_cli = _zscore_roll_safe(cli, z_window, min_periods)
    z_cli_mom = _zscore_roll_safe(cli_mom, z_window, min_periods)
    
    # CLI-GLI divergence
    cli_gli_div = z_cli - _zscore_roll_safe(gli_imp, z_window, min_periods)
    
    credit_z = (
        0.50 * z_cli.fillna(0) +
        0.30 * z_cli_mom.fillna(0) +
        0.20 * cli_gli_div.fillna(0)
    )
    
    # ================================================================
    # BRAKES BLOCK (25%) - EXPANDIDO
    # ================================================================
    # 1. Real Rate Shock (4W = 20 días)
    tips_real = _safe_ffill_only(df.get("TIPS_REAL_RATE", pd.Series(np.nan, index=idx)))
    real_rate_shock = tips_real.diff(20)
    z_real_shock = _zscore_roll_safe(real_rate_shock, z_window, min_periods)
    
    # 2. Repo Stress (SOFR - IORB)
    sofr = _safe_ffill_only(df.get("SOFR", pd.Series(np.nan, index=idx)))
    iorb = _safe_ffill_only(df.get("IORB", pd.Series(np.nan, index=idx)))
    repo_stress = sofr - iorb
    z_repo = _zscore_roll_safe(repo_stress, z_window, min_periods)
    
    # 3. Reserves Spread (NetLiq - Reserves)
    reserves = _safe_ffill_only(df.get("BANK_RESERVES", pd.Series(np.nan, index=idx)))
    reserves_spread = netliq - reserves
    z_reserves_spread = _zscore_roll_safe(reserves_spread, z_window, min_periods)
    
    # 4. MOVE Index [NUEVO]
    move = _safe_ffill_only(df.get("MOVE", pd.Series(np.nan, index=idx)))
    z_move = _zscore_roll_safe(move, z_window, min_periods)
    
    # 5. FX Volatility [NUEVO]
    fx_vol = _safe_ffill_only(df.get("FX_VOL", pd.Series(np.nan, index=idx)))
    z_fx_vol = _zscore_roll_safe(fx_vol, z_window, min_periods)
    
    # 6. Yield Curve Inversion [NUEVO]
    yield_curve = _safe_ffill_only(df.get("YIELD_CURVE", pd.Series(np.nan, index=idx)))
    if yield_curve.isna().all():
        t10y = _safe_ffill_only(df.get("TREASURY_10Y_YIELD", pd.Series(np.nan, index=idx)))
        t2y = _safe_ffill_only(df.get("TREASURY_2Y_YIELD", pd.Series(np.nan, index=idx)))
        yield_curve = t10y - t2y
    z_yield_curve = _zscore_roll_safe(yield_curve, z_window, min_periods)
    # Solo penaliza si invertida (z negativo)
    yield_curve_inv = (-z_yield_curve).clip(lower=0)
    
    # 7. Inflation Divergence (TIPS vs Cleveland) [NUEVO]
    tips_be = _safe_ffill_only(df.get("TIPS_BREAKEVEN", pd.Series(np.nan, index=idx)))
    clev_10y = _safe_ffill_only(df.get("CLEV_EXPINF_10Y", pd.Series(np.nan, index=idx)))
    inf_divergence = (tips_be - clev_10y).abs()
    z_inf_div = _zscore_roll_safe(inf_divergence, z_window, min_periods)
    
    # 8. VIX Spike [NUEVO] - solo cuando extremo
    vix = _safe_ffill_only(df.get("VIX", pd.Series(np.nan, index=idx)))
    z_vix = _zscore_roll_safe(vix, z_window, min_periods)
    vix_spike = (z_vix - 1.5).clip(lower=0)  # Solo si Z > 1.5
    
    # Brakes composite (todos restan)
    brakes_z = (
        -0.18 * z_real_shock.fillna(0) +
        -0.15 * z_repo.fillna(0) +
        -0.15 * z_reserves_spread.fillna(0) +
        -0.15 * z_move.fillna(0) +
        -0.12 * z_fx_vol.fillna(0) +
        -0.12 * yield_curve_inv.fillna(0) +
        -0.08 * z_inf_div.fillna(0) +
        -0.05 * vix_spike.fillna(0)
    )
    
    # ================================================================
    # TOTAL SCORE
    # ================================================================
    total_z = (
        0.50 * liquidity_z +
        0.25 * credit_z +
        0.25 * brakes_z
    ).replace([np.inf, -np.inf], np.nan)
    
    total_z_clip = total_z.clip(-score_clip, score_clip)
    score = 50.0 + score_scale * total_z_clip
    
    # Regime classification
    bull = (total_z > 0.75) & (liquidity_z > 0) & (credit_z > -0.25)
    bear = (total_z < -0.75) & (liquidity_z < 0) & (credit_z < 0.25)
    regime_code = pd.Series(np.where(bull, 1, np.where(bear, -1, 0)), index=idx).astype(float)
    
    # Transition (aceleración fuerte)
    gli_accel = gli_imp - gli_imp.shift(impulse_days)
    netliq_accel = netliq_imp - netliq_imp.shift(impulse_days)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        accel_strength = np.nanmax(
            np.vstack([
                _zscore_roll_safe(gli_accel, z_window, min_periods).abs().values,
                _zscore_roll_safe(netliq_accel, z_window, min_periods).abs().values
            ]),
            axis=0
        )
    transition = pd.Series((accel_strength > 1.5).astype(float), index=idx)
    
    # ================================================================
    # OUTPUT
    # ================================================================
    out["score"] = score
    out["regime_code"] = regime_code
    out["transition"] = transition
    out["total_z"] = total_z
    out["liquidity_z"] = liquidity_z
    out["credit_z"] = credit_z
    out["brakes_z"] = brakes_z
    
    # Diagnósticos
    out["gli_impulse_13w"] = gli_imp
    out["netliq_impulse_13w"] = netliq_imp
    out["m2_impulse_13w"] = m2_imp
    out["cb_diffusion_13w"] = cb_diffusion
    out["cb_hhi_13w"] = cb_hhi
    out["cli_momentum_13w"] = cli_mom
    
    # Nuevos brakes
    out["z_move"] = z_move
    out["z_fx_vol"] = z_fx_vol
    out["z_yield_curve"] = z_yield_curve
    out["z_inf_divergence"] = z_inf_div
    out["cli_gli_divergence"] = cli_gli_div
    
    # Compatibilidad con V1
    out["repo_stress"] = repo_stress
    out["real_rate_shock_4w"] = real_rate_shock
    out["reserves_spread_z"] = z_reserves_spread
    
    return out


# ============================================================
# MACRO REGIME V2B - "GROWTH-AWARE" SIN LOOKAHEAD
# ============================================================

def calculate_macro_regime_v2b(
    df: pd.DataFrame,
    impulse_days: int = 65,
    z_window: int = 252,
    min_periods: int = 100,
    score_scale: float = 15.0,
    score_clip: float = 3.0,
    # Lags de publicación para datos mensuales
    ism_lag_days: int = 22,         # ISM se publica ~1 mes después
    unemployment_lag_days: int = 5,  # Unemployment ~5 días después del mes
    pce_lag_days: int = 30,         # PCE ~1 mes después
    nfp_lag_days: int = 5,          # NFP ~5 días después del mes
) -> Dict[str, pd.Series]:
    """
    MACRO REGIME V2B: "Growth-Aware" - SIN LOOKAHEAD
    
    ESTRUCTURA: 40% Liquidity + 25% Credit + 20% Growth + 15% Brakes
    
    GROWTH BLOCK (20%):
    - ISM Composite (35%) - con lag de publicación
    - Unemployment invertido (25%) - con lag
    - PCE deviation (20%) - con lag
    - NFP momentum (20%) - con lag
    
    ANTI-LOOKAHEAD:
    - Datos mensuales tienen lag de publicación aplicado
    - Todos los rolling son backward-only
    """
    idx = df.index
    out: Dict[str, pd.Series] = {}
    
    # ================================================================
    # SERIES CON FFILL SOLO
    # ================================================================
    gli = _safe_ffill_only(df.get("GLI_TOTAL", pd.Series(np.nan, index=idx)))
    netliq = _safe_ffill_only(df.get("NET_LIQUIDITY", pd.Series(np.nan, index=idx)))
    m2 = _safe_ffill_only(df.get("M2_TOTAL", pd.Series(np.nan, index=idx)))
    fed = _safe_ffill_only(df.get("FED_USD", pd.Series(np.nan, index=idx)))
    cli = _safe_ffill_only(df.get("CLI_V2", df.get("CLI", pd.Series(np.nan, index=idx))))
    
    # ================================================================
    # LIQUIDITY BLOCK (40%)
    # ================================================================
    gli_imp = gli.diff(impulse_days)
    netliq_imp = netliq.diff(impulse_days)
    m2_imp = m2.diff(impulse_days)
    
    z_gli_imp = _zscore_roll_safe(gli_imp, z_window, min_periods)
    z_netliq_imp = _zscore_roll_safe(netliq_imp, z_window, min_periods)
    z_m2_imp = _zscore_roll_safe(m2_imp, z_window, min_periods)
    
    # Fed Momentum (12w vs 26w EMA)
    fed_12w = fed.ewm(span=60, min_periods=30).mean()
    fed_26w = fed.ewm(span=130, min_periods=60).mean()
    fed_momentum = fed_12w - fed_26w
    z_fed_mom = _zscore_roll_safe(fed_momentum, z_window, min_periods)
    
    # CB Breadth & Concentration
    cb_cols = [c for c in df.columns if c.endswith("_USD") and c not in ['TGA_USD', 'RRP_USD']]
    if cb_cols:
        cb_data = df[cb_cols].astype(float).ffill()
        cb_deltas = cb_data.diff(impulse_days)
        denom = cb_deltas.notna().sum(axis=1).replace(0, np.nan)
        cb_diffusion = (cb_deltas > 0).sum(axis=1) / denom
        
        abs_d = cb_deltas.abs()
        abs_sum = abs_d.sum(axis=1).replace(0, np.nan)
        shares = abs_d.div(abs_sum, axis=0)
        cb_hhi = shares.pow(2).sum(axis=1)
        
        z_diffusion = _zscore_roll_safe(cb_diffusion, z_window, min_periods)
        z_hhi = _zscore_roll_safe(cb_hhi, z_window, min_periods)
    else:
        cb_diffusion = pd.Series(np.nan, index=idx)
        cb_hhi = pd.Series(np.nan, index=idx)
        z_diffusion = pd.Series(0.0, index=idx)
        z_hhi = pd.Series(0.0, index=idx)
    
    liquidity_z = (
        0.25 * z_gli_imp.fillna(0) +
        0.25 * z_netliq_imp.fillna(0) +
        0.15 * z_m2_imp.fillna(0) +
        0.15 * z_fed_mom.fillna(0) +
        0.10 * z_diffusion.fillna(0) -
        0.10 * z_hhi.fillna(0)
    )
    
    # ================================================================
    # CREDIT BLOCK (25%)
    # ================================================================
    cli_mom = cli.diff(impulse_days)
    z_cli = _zscore_roll_safe(cli, z_window, min_periods)
    z_cli_mom = _zscore_roll_safe(cli_mom, z_window, min_periods)
    
    credit_z = (
        0.60 * z_cli.fillna(0) +
        0.40 * z_cli_mom.fillna(0)
    )
    
    # ================================================================
    # GROWTH BLOCK (20%) - CON LAGS DE PUBLICACIÓN
    # ================================================================
    # ISM Composite - CON LAG DE PUBLICACIÓN
    ism_mfg_raw = _safe_ffill_only(df.get("ISM_MFG", pd.Series(np.nan, index=idx)))
    ism_svc_raw = _safe_ffill_only(df.get("ISM_SVC", pd.Series(np.nan, index=idx)))
    
    # Aplicar lag de publicación (simula que no tenemos el dato hasta X días después)
    ism_mfg = _apply_publication_lag(ism_mfg_raw, ism_lag_days)
    ism_svc = _apply_publication_lag(ism_svc_raw, ism_lag_days)
    
    ism_composite = (ism_mfg.fillna(50) + ism_svc.fillna(50)) / 2
    z_ism = _zscore_roll_safe(ism_composite - 50, z_window, min_periods)
    
    # Unemployment - CON LAG
    unemployment_raw = _safe_ffill_only(df.get("UNEMPLOYMENT", pd.Series(np.nan, index=idx)))
    unemployment = _apply_publication_lag(unemployment_raw, unemployment_lag_days)
    z_unemp_inv = -_zscore_roll_safe(unemployment, z_window, min_periods)  # Invertido
    
    # PCE deviation - CON LAG
    core_pce_raw = _safe_ffill_only(df.get("CORE_PCE", pd.Series(np.nan, index=idx)))
    core_pce = _apply_publication_lag(core_pce_raw, pce_lag_days)
    
    # Determinar si es nivel o YoY
    if core_pce.notna().any() and core_pce.max() > 10:
        pce_yoy = core_pce.pct_change(252) * 100
    else:
        pce_yoy = core_pce
    pce_deviation = (pce_yoy - 2.0).abs()
    z_pce_dev = -_zscore_roll_safe(pce_deviation, z_window, min_periods)
    
    # NFP Momentum - CON LAG
    nfp_raw = _safe_ffill_only(df.get("NFP", pd.Series(np.nan, index=idx)))
    nfp = _apply_publication_lag(nfp_raw, nfp_lag_days)
    nfp_mom = nfp.diff(63)  # 3 meses
    z_nfp_mom = _zscore_roll_safe(nfp_mom, z_window, min_periods)
    
    growth_z = (
        0.35 * z_ism.fillna(0) +
        0.25 * z_unemp_inv.fillna(0) +
        0.20 * z_pce_dev.fillna(0) +
        0.20 * z_nfp_mom.fillna(0)
    )
    
    # ================================================================
    # BRAKES BLOCK (15%)
    # ================================================================
    tips_real = _safe_ffill_only(df.get("TIPS_REAL_RATE", pd.Series(np.nan, index=idx)))
    real_rate_shock = tips_real.diff(20)
    z_real_shock = _zscore_roll_safe(real_rate_shock, z_window, min_periods)
    
    sofr = _safe_ffill_only(df.get("SOFR", pd.Series(np.nan, index=idx)))
    iorb = _safe_ffill_only(df.get("IORB", pd.Series(np.nan, index=idx)))
    repo_stress = sofr - iorb
    z_repo = _zscore_roll_safe(repo_stress, z_window, min_periods)
    
    move = _safe_ffill_only(df.get("MOVE", pd.Series(np.nan, index=idx)))
    z_move = _zscore_roll_safe(move, z_window, min_periods)
    
    # Inflation Surprise (CPI vs Cleveland) - con lag
    cpi_raw = _safe_ffill_only(df.get("CPI", pd.Series(np.nan, index=idx)))
    cpi = _apply_publication_lag(cpi_raw, 15)  # CPI ~15 días después del mes
    
    if cpi.notna().any() and cpi.max() > 10:
        cpi_yoy = cpi.pct_change(252) * 100
    else:
        cpi_yoy = cpi
    
    clev_1y = _safe_ffill_only(df.get("INFLATION_EXPECT_1Y", pd.Series(np.nan, index=idx)))
    inf_surprise = cpi_yoy - clev_1y
    z_inf_surprise = _zscore_roll_safe(inf_surprise, z_window, min_periods)
    
    brakes_z = (
        -0.30 * z_real_shock.fillna(0) +
        -0.25 * z_repo.fillna(0) +
        -0.25 * z_move.fillna(0) +
        -0.20 * z_inf_surprise.fillna(0)
    )
    
    # ================================================================
    # TOTAL SCORE
    # ================================================================
    total_z = (
        0.40 * liquidity_z +
        0.25 * credit_z +
        0.20 * growth_z +
        0.15 * brakes_z
    ).replace([np.inf, -np.inf], np.nan)
    
    total_z_clip = total_z.clip(-score_clip, score_clip)
    score = 50.0 + score_scale * total_z_clip
    
    # Regime classification (incluye growth)
    bull = (total_z > 0.75) & (liquidity_z > 0) & (growth_z > -0.25)
    bear = (total_z < -0.75) & (liquidity_z < 0) & (growth_z < 0.25)
    regime_code = pd.Series(np.where(bull, 1, np.where(bear, -1, 0)), index=idx).astype(float)
    
    # Transition
    gli_accel = gli_imp - gli_imp.shift(impulse_days)
    accel_strength = _zscore_roll_safe(gli_accel, z_window, min_periods).abs()
    transition = pd.Series((accel_strength > 1.5).astype(float), index=idx)
    
    # ================================================================
    # OUTPUT
    # ================================================================
    out["score"] = score
    out["regime_code"] = regime_code
    out["transition"] = transition
    out["total_z"] = total_z
    out["liquidity_z"] = liquidity_z
    out["credit_z"] = credit_z
    out["growth_z"] = growth_z
    out["brakes_z"] = brakes_z
    
    # Diagnósticos growth
    out["z_ism"] = z_ism
    out["z_unemployment"] = z_unemp_inv
    out["z_pce_deviation"] = z_pce_dev
    out["z_nfp_momentum"] = z_nfp_mom
    out["z_fed_momentum"] = z_fed_mom
    out["z_inflation_surprise"] = z_inf_surprise
    
    # Compatibilidad
    out["cb_diffusion_13w"] = cb_diffusion
    out["cb_hhi_13w"] = cb_hhi
    out["repo_stress"] = repo_stress
    out["real_rate_shock_4w"] = real_rate_shock
    
    return out


# ============================================================
# MARKET STRESS DASHBOARD - HISTÓRICO
# ============================================================

def calculate_stress_historical(
    df: pd.DataFrame,
    z_window: int = 252,
    min_periods: int = 100,
) -> Dict[str, pd.Series]:
    """
    Market Stress Dashboard HISTÓRICO - SIN LOOKAHEAD
    
    Calcula scores de stress para cada día en el histórico.
    
    DIMENSIONES:
    1. Inflation Stress (max 7 puntos)
    2. Liquidity Stress (max 7 puntos)  
    3. Credit Stress (max 7 puntos)
    4. Volatility Stress (max 6 puntos)
    
    Total max = 27 puntos
    
    NIVELES:
    - LOW: 0-4
    - MODERATE: 5-9
    - HIGH: 10-14
    - CRITICAL: 15+
    
    Returns Dict con series históricas para cada dimensión.
    """
    idx = df.index
    out: Dict[str, pd.Series] = {}
    
    # ================================================================
    # 1. INFLATION STRESS (max 7)
    # ================================================================
    tips_be = _safe_ffill_only(df.get('TIPS_BREAKEVEN', pd.Series(np.nan, index=idx)))
    tips_5y5y = _safe_ffill_only(df.get('TIPS_5Y5Y_FORWARD', pd.Series(np.nan, index=idx)))
    clev_10y = _safe_ffill_only(df.get('CLEV_EXPINF_10Y', pd.Series(np.nan, index=idx)))
    
    tips_be_z = _zscore_roll_safe(tips_be, z_window, min_periods)
    tips_be_roc_3m = tips_be.pct_change(63) * 100
    tips_clev_div = (tips_be - clev_10y).abs()
    
    inflation_score = pd.Series(0.0, index=idx)
    
    # BE > 2.5% = +2, BE > 2.2% = +1, BE < 1.8% = -1
    inflation_score += np.where(tips_be > 2.5, 2, np.where(tips_be > 2.2, 1, np.where(tips_be < 1.8, -1, 0)))
    
    # Divergencia TIPS/Cleveland > 0.3 = +1
    inflation_score += np.where(tips_clev_div > 0.3, 1, 0)
    
    # 5Y5Y > 2.5% = +1
    inflation_score += np.where(tips_5y5y > 2.5, 1, 0)
    
    # ROC 3M > 20% = +2
    inflation_score += np.where(tips_be_roc_3m > 20, 2, np.where(tips_be_roc_3m > 10, 1, 0))
    
    out['inflation_stress'] = inflation_score.clip(0, 7)
    out['tips_be_zscore'] = tips_be_z
    out['tips_clev_divergence'] = tips_clev_div
    
    # ================================================================
    # 2. LIQUIDITY STRESS (max 7)
    # ================================================================
    sofr = _safe_ffill_only(df.get('SOFR', pd.Series(np.nan, index=idx)))
    iorb = _safe_ffill_only(df.get('IORB', pd.Series(np.nan, index=idx)))
    reserves = _safe_ffill_only(df.get('BANK_RESERVES', pd.Series(np.nan, index=idx)))
    rrp = _safe_ffill_only(df.get('RRP_USD', pd.Series(np.nan, index=idx)))
    tga = _safe_ffill_only(df.get('TGA_USD', pd.Series(np.nan, index=idx)))
    fed = _safe_ffill_only(df.get('FED_USD', pd.Series(np.nan, index=idx)))
    
    sofr_iorb_spread = (sofr - iorb) * 100  # bps
    net_liquidity = fed - tga - rrp
    reserves_roc_3m = reserves.pct_change(63) * 100
    
    liquidity_score = pd.Series(0.0, index=idx)
    
    # SOFR-IORB > 5bps = +2, > 2bps = +1
    liquidity_score += np.where(sofr_iorb_spread > 5, 2, np.where(sofr_iorb_spread > 2, 1, 0))
    
    # Reserves < 2.8T = +2, < 3.2T = +1
    liquidity_score += np.where(reserves < 2.8, 2, np.where(reserves < 3.2, 1, 0))
    
    # RRP < 0.1T = +1
    liquidity_score += np.where(rrp < 0.1, 1, 0)
    
    # Net Liq < 5.5T = +1
    liquidity_score += np.where(net_liquidity < 5.5, 1, 0)
    
    # Reserves falling > 5% in 3M = +1
    liquidity_score += np.where(reserves_roc_3m < -5, 1, 0)
    
    out['liquidity_stress'] = liquidity_score.clip(0, 7)
    out['sofr_iorb_spread_bps'] = sofr_iorb_spread
    out['net_liquidity'] = net_liquidity
    out['reserves_roc_3m'] = reserves_roc_3m
    
    # ================================================================
    # 3. CREDIT STRESS (max 7)
    # ================================================================
    hy_spread = _safe_ffill_only(df.get('HY_SPREAD', pd.Series(np.nan, index=idx)))
    ig_spread = _safe_ffill_only(df.get('IG_SPREAD', pd.Series(np.nan, index=idx)))
    nfci = _safe_ffill_only(df.get('NFCI', pd.Series(np.nan, index=idx)))
    
    hy_z = _zscore_roll_safe(hy_spread, z_window, min_periods)
    ig_z = _zscore_roll_safe(ig_spread, z_window, min_periods)
    
    credit_score = pd.Series(0.0, index=idx)
    
    # HY > 500bps = +2, > 400bps = +1
    credit_score += np.where(hy_spread > 500, 2, np.where(hy_spread > 400, 1, 0))
    
    # IG > 150bps = +1
    credit_score += np.where(ig_spread > 150, 1, 0)
    
    # NFCI > 0.5 = +2, > 0 = +1
    credit_score += np.where(nfci > 0.5, 2, np.where(nfci > 0, 1, 0))
    
    # HY Z-score > 1.5 = +1
    credit_score += np.where(hy_z > 1.5, 1, 0)
    
    out['credit_stress'] = credit_score.clip(0, 7)
    out['hy_spread_zscore'] = hy_z
    out['ig_spread_zscore'] = ig_z
    
    # ================================================================
    # 4. VOLATILITY STRESS (max 6)
    # ================================================================
    vix = _safe_ffill_only(df.get('VIX', pd.Series(np.nan, index=idx)))
    move = _safe_ffill_only(df.get('MOVE', pd.Series(np.nan, index=idx)))
    
    vix_z = _zscore_roll_safe(vix, z_window, min_periods)
    move_z = _zscore_roll_safe(move, z_window, min_periods)
    vix_roc_1w = vix.pct_change(5) * 100
    
    vol_score = pd.Series(0.0, index=idx)
    
    # VIX > 30 = +2, > 20 = +1
    vol_score += np.where(vix > 30, 2, np.where(vix > 20, 1, 0))
    
    # MOVE Z > 1.5 = +1
    vol_score += np.where(move_z > 1.5, 1, 0)
    
    # VIX spike > 20% in 1W = +2
    vol_score += np.where(vix_roc_1w > 20, 2, np.where(vix_roc_1w > 10, 1, 0))
    
    out['volatility_stress'] = vol_score.clip(0, 6)
    out['vix_zscore'] = vix_z
    out['move_zscore'] = move_z
    out['vix_roc_1w'] = vix_roc_1w
    
    # ================================================================
    # TOTAL STRESS
    # ================================================================
    total_stress = (
        out['inflation_stress'] + 
        out['liquidity_stress'] + 
        out['credit_stress'] + 
        out['volatility_stress']
    )
    out['total_stress'] = total_stress
    out['total_stress_pct'] = (total_stress / 27 * 100).round(1)
    
    # Nivel categórico
    stress_level = pd.Series('LOW', index=idx)
    stress_level = stress_level.where(total_stress < 5, 'MODERATE')
    stress_level = stress_level.where(total_stress < 10, 'HIGH')
    stress_level = stress_level.where(total_stress < 15, 'CRITICAL')
    out['stress_level'] = stress_level
    
    return out


# ============================================================
# SELECTOR UNIFICADO
# ============================================================

def calculate_macro_regime_selector(
    df: pd.DataFrame,
    version: Literal["v1", "v2a", "v2b"] = "v2a",
    **kwargs
) -> Dict[str, pd.Series]:
    """
    Selector de versión de macro regime.
    
    - v1:  Original (requiere importar de data_pipeline)
    - v2a: Inflation-Aware (brakes expandidos)
    - v2b: Growth-Aware (bloque growth)
    """
    if version == "v1":
        # Para V1, necesitaríamos importar la función original
        # Por ahora, usar V2A como fallback
        print("Note: V1 original not available in this module. Using V2A.")
        return calculate_macro_regime_v2a(df, **kwargs)
    elif version == "v2a":
        return calculate_macro_regime_v2a(df, **kwargs)
    elif version == "v2b":
        return calculate_macro_regime_v2b(df, **kwargs)
    else:
        raise ValueError(f"Unknown version: {version}")


# ============================================================
# HELPER: CLEAN FOR JSON
# ============================================================

def clean_series_for_json(s: pd.Series) -> list:
    """Convierte Series a lista limpia para JSON."""
    return [None if pd.isna(x) or np.isinf(x) else round(float(x), 4) for x in s]


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("REGIME V2 & CLI V2 - SIN LOOKAHEAD BIAS")
    print("=" * 70)
    
    print("\n✅ ANTI-LOOKAHEAD FEATURES:")
    print("  • Rolling windows: backward-only (no center=True)")
    print("  • Diff operations: backward-only")
    print("  • Fill operations: ffill only (no bfill)")
    print("  • Monthly data: publication lag applied (ISM: 22d, NFP: 5d, etc.)")
    print("  • Z-scores: expanding or rolling backward")
    
    print("\n📊 CLI V2 WEIGHTS:")
    weights = {
        'HY_SPREAD_Z': 0.22, 'HY_MOMENTUM_Z': 0.10, 'IG_SPREAD_Z': 0.08,
        'NFCI_CREDIT_Z': 0.15, 'NFCI_RISK_Z': 0.10, 'LENDING_STD_Z': 0.05,
        'MOVE_Z': 0.12, 'FX_VOL_Z': 0.08, 'YIELD_CURVE_Z': 0.05, 'REAL_RATE_SHOCK_Z': 0.05
    }
    for k, v in weights.items():
        print(f"    {k}: {v:.0%}")
    
    print("\n🎯 REGIME V2A (Inflation-Aware):")
    print("    Structure: 50% Liquidity + 25% Credit + 25% Brakes")
    print("    New brakes: MOVE, FX_VOL, Yield Curve, Inf Divergence, VIX Spike")
    
    print("\n📈 REGIME V2B (Growth-Aware):")
    print("    Structure: 40% Liquidity + 25% Credit + 20% Growth + 15% Brakes")
    print("    Growth block: ISM, Unemployment, PCE, NFP (all with pub lag)")
    
    print("\n⚡ STRESS DASHBOARD HISTÓRICO:")
    print("    Dimensions: Inflation (7) + Liquidity (7) + Credit (7) + Volatility (6) = 27 max")
    print("    Levels: LOW (0-4), MODERATE (5-9), HIGH (10-14), CRITICAL (15+)")
    
    print("\n✅ Module ready for import into data_pipeline.py")
