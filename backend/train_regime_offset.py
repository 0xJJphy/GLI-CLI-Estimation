#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
train_regime_offset.py

Optimiza el OFFSET (lead) para el régimen Risk-On/Risk-Off de BTC usando:
- Macro regime score (liquidez + crédito - brakes)
- Evaluación robusta con walk-forward (mediana OOS)
- Selección estable: elige el offset más pequeño dentro del 95% del mejor

Input:
  ./data/dashboard_data.json  (generado por data_pipeline.py)

Outputs:
  ./data/regime_params.json            (offset recomendado actual)
  ./data/regime_offset_grid.csv        (tabla de métricas por offset)
  opcional (si --simulate-live):
    ./data/regime_params_history.csv
    ./data/regime_live_backtest.csv
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

# -----------------------------
# JSON helpers
# -----------------------------
def jget(d, path, default=None):
    cur = d
    for p in path.split("."):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return default
    return cur

def to_float_series(values, index):
    if values is None:
        return pd.Series(np.nan, index=index, dtype=float)
    arr = np.array([np.nan if v is None else float(v) for v in values], dtype=float)
    if len(arr) != len(index):
        # Ajuste defensivo
        if len(arr) > len(index):
            arr = arr[: len(index)]
        else:
            arr = np.pad(arr, (0, len(index) - len(arr)), constant_values=np.nan)
    return pd.Series(arr, index=index, dtype=float)

def load_dashboard_json(json_path: str) -> pd.DataFrame:
    with open(json_path, "r") as f:
        data = json.load(f)

    dates = pd.to_datetime(data["dates"])
    df = pd.DataFrame(index=dates)

    # Core
    df["BTC"] = to_float_series(jget(data, "btc.price"), df.index)
    df["GLI_TOTAL"] = to_float_series(jget(data, "gli.total"), df.index)
    df["NET_LIQUIDITY"] = to_float_series(jget(data, "us_net_liq"), df.index)
    df["M2_TOTAL"] = to_float_series(jget(data, "m2.total"), df.index)
    df["CLI"] = to_float_series(jget(data, "cli.total"), df.index)

    # Plumbing / brakes
    df["BANK_RESERVES"] = to_float_series(jget(data, "us_net_liq_reserves"), df.index)
    df["TIPS_REAL_RATE"] = to_float_series(jget(data, "tips.real_rate"), df.index)
    df["SOFR"] = to_float_series(jget(data, "repo_stress.sofr"), df.index)
    df["IORB"] = to_float_series(jget(data, "repo_stress.iorb"), df.index)

    # CB series para diffusion/HHI (si existen en JSON)
    banks = ["fed", "ecb", "boj", "pboc", "boe", "boc", "rba", "snb", "cbr", "bcb", "bok", "rbi", "rbnz", "sr", "bnm"]
    for b in banks:
        s = jget(data, f"gli.{b}")
        if s is not None:
            df[f"{b.upper()}_USD"] = to_float_series(s, df.index)

    # limpieza
    df = df.sort_index()
    return df


# -----------------------------
# Regime score (tu fórmula)
# -----------------------------
def _zscore_roll(s: pd.Series, window: int, min_periods: int) -> pd.Series:
    s = s.astype(float).replace([np.inf, -np.inf], np.nan)
    mu = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std().replace(0, np.nan)
    return (s - mu) / sd

def compute_macro_regime_score(
    df: pd.DataFrame,
    impulse_days: int = 65,   # ~13W
    mom_days: int = 65,       # CLI momentum ~13W (puedes bajar a 20 si quieres más reactivo)
    z_window: int = 252,
    min_periods: int = 100,
    score_scale: float = 15.0,
    score_clip: float = 3.0,
    # Pesos por bloques (por defecto 1)
    w_liquidity: float = 1.0,
    w_credit: float = 1.0,
    w_brakes: float = 1.0,
):
    idx = df.index

    gli = df.get("GLI_TOTAL", pd.Series(np.nan, index=idx))
    netliq = df.get("NET_LIQUIDITY", pd.Series(np.nan, index=idx))
    m2 = df.get("M2_TOTAL", pd.Series(np.nan, index=idx))
    cli = df.get("CLI", pd.Series(np.nan, index=idx))

    # Impulsos (flows)
    gli_imp = gli.diff(impulse_days)
    netliq_imp = netliq.diff(impulse_days)
    m2_imp = m2.diff(impulse_days)

    z_gli_imp = _zscore_roll(gli_imp, z_window, min_periods)
    z_netliq_imp = _zscore_roll(netliq_imp, z_window, min_periods)
    z_m2_imp = _zscore_roll(m2_imp, z_window, min_periods)

    # Crédito
    cli_mom = cli.diff(mom_days)
    z_cli = _zscore_roll(cli, z_window, min_periods)
    z_cli_mom = _zscore_roll(cli_mom, z_window, min_periods)

    # Breadth / concentration (si hay CBs)
    cb_cols = [c for c in df.columns if c.endswith("_USD")]
    if cb_cols:
        cb_deltas = df[cb_cols].astype(float).diff(impulse_days)
        denom = cb_deltas.notna().sum(axis=1).replace(0, np.nan)
        cb_diffusion = (cb_deltas > 0).sum(axis=1) / denom

        abs_d = cb_deltas.abs()
        abs_sum = abs_d.sum(axis=1).replace(0, np.nan)
        shares = abs_d.div(abs_sum, axis=0)
        cb_hhi = shares.pow(2).sum(axis=1)

        z_diffusion = _zscore_roll(cb_diffusion, z_window, min_periods)
        z_hhi = _zscore_roll(cb_hhi, z_window, min_periods)
    else:
        z_diffusion = pd.Series(np.nan, index=idx)
        z_hhi = pd.Series(np.nan, index=idx)

    # Brakes / plumbing
    tips_real = df.get("TIPS_REAL_RATE", pd.Series(np.nan, index=idx))
    real_rate_shock_4w = tips_real.diff(20)  # ~4W
    z_real_shock = _zscore_roll(real_rate_shock_4w, z_window, min_periods)

    sofr = df.get("SOFR", pd.Series(np.nan, index=idx))
    iorb = df.get("IORB", pd.Series(np.nan, index=idx))
    repo_stress = (sofr - iorb)
    z_repo = _zscore_roll(repo_stress, z_window, min_periods)

    reserves = df.get("BANK_RESERVES", pd.Series(np.nan, index=idx))
    spread = (netliq - reserves).astype(float)
    spread_mu = spread.rolling(z_window, min_periods=min_periods).mean()
    spread_sd = spread.rolling(z_window, min_periods=min_periods).std().replace(0, np.nan)
    reserves_spread_z = (spread - spread_mu) / spread_sd  # ya es z

    # --- Fórmula (similar a la que enseñas en UI) ---
    liquidity_z = (
        0.35 * z_gli_imp +
        0.35 * z_netliq_imp +
        0.20 * z_m2_imp +
        0.10 * z_diffusion -
        0.10 * z_hhi
    )

    credit_z = 0.60 * z_cli + 0.40 * z_cli_mom

    # brakes: más stress => peor => entra con signo negativo
    brakes_z = (
        -0.35 * z_real_shock +
        -0.25 * z_repo +
        -0.25 * reserves_spread_z
    )

    total_z = (w_liquidity * liquidity_z + w_credit * credit_z + w_brakes * brakes_z).replace([np.inf, -np.inf], np.nan)

    # Score 0-100 centrado en 50
    total_z_clip = np.clip(total_z, -score_clip, score_clip)
    score = (50.0 + score_scale * total_z_clip).astype(float)

    return {
        "score": score,
        "liquidity_z": liquidity_z,
        "credit_z": credit_z,
        "brakes_z": brakes_z,
        "total_z": total_z,
    }


# -----------------------------
# Offset optimization (walk-forward)
# -----------------------------
def _walk_forward_splits(n: int, train_min: int, test: int, step: int):
    train_end = train_min
    while train_end + test <= n:
        yield (slice(0, train_end), slice(train_end, train_end + test))
        train_end += step

def _ann_sharpe(r: pd.Series, periods_per_year: int = 52) -> float:
    r = r.dropna()
    if len(r) < 30 or r.std() == 0:
        return np.nan
    return float((r.mean() / r.std()) * np.sqrt(periods_per_year))

def _cagr(r: pd.Series, periods_per_year: int = 52) -> float:
    r = r.dropna()
    if r.empty:
        return np.nan
    eq = (1.0 + r).prod()
    years = len(r) / periods_per_year
    if years <= 0:
        return np.nan
    return float(eq ** (1.0 / years) - 1.0)

def _max_dd(r: pd.Series) -> float:
    r = r.dropna()
    if r.empty:
        return np.nan
    eq = (1.0 + r).cumprod()
    peak = eq.cummax()
    dd = eq / peak - 1.0
    return float(dd.min())

def _hysteresis_pos(score: pd.Series, on: float, off: float) -> pd.Series:
    s = score.astype(float)
    pos = np.zeros(len(s), dtype=float)
    state = 0.0
    for i, v in enumerate(s.values):
        if np.isnan(v):
            pos[i] = state
            continue
        if state == 0.0 and v >= on:
            state = 1.0
        elif state == 1.0 and v <= off:
            state = 0.0
        pos[i] = state
    return pd.Series(pos, index=s.index)

def evaluate_offset_on_window(
    dfw: pd.DataFrame,
    score: pd.Series,
    offsets_days,
    on: float,
    off: float,
    cost_bps: float,
    train_min_weeks: int,
    test_weeks: int,
    step_weeks: int,
):
    """
    Evalúa offsets en un window dfw (semanal). Usa estrategia long/cash:
      aligned_score(t) = score(t - offset)
    y mide Sharpe/CAGR/MDD OOS por folds internos.
    """
    price = dfw["BTC"].astype(float)
    ret = price.pct_change()

    splits = list(_walk_forward_splits(len(dfw), train_min_weeks, test_weeks, step_weeks))
    if not splits:
        return pd.DataFrame(), None

    cost = cost_bps / 10000.0
    rows = []

    for L in offsets_days:
        Lw = int(round(L / 7.0))
        aligned = score.shift(Lw)  # macro adelantado => a t le llega score(t-L)

        pos = _hysteresis_pos(aligned, on=on, off=off)
        pos_exec = pos.shift(1)  # ejecuta en la siguiente vela
        turnover = pos_exec.diff().abs().fillna(0.0)
        strat = (pos_exec * ret) - (turnover * cost)

        fold_sh, fold_cagr, fold_mdd, fold_expo = [], [], [], []

        for _, te in splits:
            idx_te = dfw.index[te]
            sr = strat.reindex(idx_te).dropna()
            pr = pos_exec.reindex(idx_te).dropna()

            fold_sh.append(_ann_sharpe(sr))
            fold_cagr.append(_cagr(sr))
            fold_mdd.append(_max_dd(sr))
            fold_expo.append(float(pr.mean()) if len(pr) else np.nan)

        rows.append({
            "offset_days": int(L),
            "offset_weeks": int(Lw),
            "sharpe_med": float(np.nanmedian(fold_sh)),
            "cagr_med": float(np.nanmedian(fold_cagr)),
            "mdd_med": float(np.nanmedian(fold_mdd)),
            "exposure_med": float(np.nanmedian(fold_expo)),
            "sharpe_mean": float(np.nanmean(fold_sh)),
        })

    res = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan).dropna(subset=["sharpe_med"])
    if res.empty:
        return res, None

    # Selección estable: mejor sharpe_med, pero elige el offset más pequeño dentro del 95% del mejor
    best = res.sort_values(["sharpe_med", "cagr_med"], ascending=False).iloc[0]
    best_sh = best["sharpe_med"]
    near = res[res["sharpe_med"] >= 0.95 * best_sh].sort_values("offset_days")
    recommended = int(near.iloc[0]["offset_days"]) if not near.empty else int(best["offset_days"])

    return res.sort_values("offset_days").reset_index(drop=True), recommended


# -----------------------------
# Live monthly recalibration (opcional)
# -----------------------------
def last_friday_each_month(weekly_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    s = pd.Series(weekly_index, index=weekly_index)
    g = s.groupby([weekly_index.year, weekly_index.month]).max()
    return pd.DatetimeIndex(g.values)

def simulate_live_recalibration(
    dfw: pd.DataFrame,
    score_w: pd.Series,
    offsets_days,
    on: float,
    off: float,
    cost_bps: float,
    train_years: int,
    train_min_weeks: int,
    test_weeks: int,
    step_weeks: int,
    change_threshold: float = 0.10,  # requiere +10% Sharpe para cambiar
):
    """
    Cada fin de mes:
      - usa últimos train_years años para evaluar offsets (walk-forward interno)
      - elige offset robusto
      - solo cambia si mejora > change_threshold vs el offset actual (en Sharpe_med)

    Devuelve:
      params_history (fecha_calibración, offset)
      live_backtest (pos/returns con offset variable)
    """
    rebal_dates = last_friday_each_month(dfw.index)
    train_weeks = int(train_years * 52)

    current_offset = None
    current_sh = None
    rows = []

    # backtest: construimos aligned_score por segmentos
    aligned_live = pd.Series(np.nan, index=dfw.index, dtype=float)

    for i, d in enumerate(rebal_dates):
        # necesitamos suficiente historial
        window = dfw.loc[:d].tail(train_weeks)
        if len(window) < max(train_min_weeks + test_weeks + 10, 200):
            continue

        grid, rec = evaluate_offset_on_window(
            dfw=window,
            score=score_w.reindex(window.index),
            offsets_days=offsets_days,
            on=on,
            off=off,
            cost_bps=cost_bps,
            train_min_weeks=train_min_weeks,
            test_weeks=test_weeks,
            step_weeks=step_weeks,
        )
        if grid.empty or rec is None:
            continue

        rec_row = grid.loc[grid["offset_days"] == rec].iloc[0]
        rec_sh = float(rec_row["sharpe_med"])

        # regla de cambio: si no hay offset todavía, toma el recomendado
        if current_offset is None:
            current_offset = rec
            current_sh = rec_sh
        else:
            # calcula sharpe del offset actual en este mismo window
            cur_row = grid.loc[grid["offset_days"] == current_offset]
            cur_sh = float(cur_row.iloc[0]["sharpe_med"]) if not cur_row.empty else (current_sh if current_sh is not None else -np.inf)

            # cambia solo si mejora material
            if np.isfinite(cur_sh) and np.isfinite(rec_sh) and (rec_sh > (1.0 + change_threshold) * cur_sh):
                current_offset = rec
                current_sh = rec_sh

        rows.append({
            "calibration_date": d.strftime("%Y-%m-%d"),
            "offset_days": int(current_offset),
            "sharpe_med_window": float(current_sh) if current_sh is not None else np.nan,
        })

        # aplicar offset desde la semana siguiente hasta próxima calibración (o fin)
        start_pos = dfw.index.get_loc(d)
        start_apply = start_pos + 1
        end_apply = (dfw.index.get_loc(rebal_dates[i + 1]) if i + 1 < len(rebal_dates) else len(dfw.index) - 1)

        seg_idx = dfw.index[start_apply : end_apply + 1]
        Lw = int(round(current_offset / 7.0))
        aligned_seg = score_w.shift(Lw).reindex(seg_idx)
        aligned_live.loc[seg_idx] = aligned_seg

    params = pd.DataFrame(rows)
    # live backtest con offset variable
    price = dfw["BTC"].astype(float)
    ret = price.pct_change()

    pos = _hysteresis_pos(aligned_live, on=on, off=off)
    pos_exec = pos.shift(1)
    cost = cost_bps / 10000.0
    turnover = pos_exec.diff().abs().fillna(0.0)
    strat = (pos_exec * ret) - (turnover * cost)

    out = pd.DataFrame({
        "BTC": price,
        "score": score_w,
        "aligned_score_live": aligned_live,
        "pos": pos_exec,
        "ret": ret,
        "strat_ret": strat,
        "equity": (1.0 + strat.fillna(0.0)).cumprod(),
    }, index=dfw.index)

    return params, out


# -----------------------------
# Main
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=None, help="Path a dashboard_data.json (default: ./data/dashboard_data.json)")
    parser.add_argument("--offset-min", type=int, default=0)
    parser.add_argument("--offset-max", type=int, default=180)
    parser.add_argument("--offset-step", type=int, default=7)

    parser.add_argument("--on", type=float, default=55.0, help="Umbral entrada long (histeresis)")
    parser.add_argument("--off", type=float, default=45.0, help="Umbral salida a cash (histeresis)")
    parser.add_argument("--cost-bps", type=float, default=10.0, help="Coste por flip (ida+vuelta aprox) en bps")

    parser.add_argument("--train-min-weeks", type=int, default=156, help="Min semanas para primer fold interno (~3y)")
    parser.add_argument("--test-weeks", type=int, default=52, help="Semanas test por fold interno (~1y)")
    parser.add_argument("--step-weeks", type=int, default=26, help="Paso entre folds (~6m)")

    parser.add_argument("--simulate-live", action="store_true", help="Simula recalibración mensual en vivo")
    parser.add_argument("--train-years", type=int, default=5, help="Ventana rolling (años) para recalibración mensual")
    parser.add_argument("--change-threshold", type=float, default=0.10, help="Mejora Sharpe relativa necesaria para cambiar offset")

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_json = os.path.join(base_dir, "data", "dashboard_data.json")
    json_path = args.data or default_json

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"No existe {json_path}. Ejecuta primero data_pipeline.py para generar dashboard_data.json")

    df = load_dashboard_json(json_path)

    # Regime score diario (como tu dashboard)
    reg = compute_macro_regime_score(df)
    score = reg["score"]

    # Resample semanal para evaluación (evita artefactos de ffill diario)
    dfw = df[["BTC"]].resample("W-FRI").last()
    score_w = score.resample("W-FRI").last()

    # Candidates
    offsets_days = list(range(args.offset_min, args.offset_max + 1, args.offset_step))

    # Optimización "actual" (full window semanal) con folds internos
    grid, recommended = evaluate_offset_on_window(
        dfw=dfw,
        score=score_w,
        offsets_days=offsets_days,
        on=args.on,
        off=args.off,
        cost_bps=args.cost_bps,
        train_min_weeks=args.train_min_weeks,
        test_weeks=args.test_weeks,
        step_weeks=args.step_weeks,
    )

    out_dir = os.path.join(base_dir, "data")
    os.makedirs(out_dir, exist_ok=True)

    if not grid.empty:
        grid_path = os.path.join(out_dir, "regime_offset_grid.csv")
        grid.to_csv(grid_path, index=False)

    params_path = os.path.join(out_dir, "regime_params.json")
    params = {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "recommended_offset_days": int(recommended) if recommended is not None else None,
        "hysteresis": {"on": float(args.on), "off": float(args.off)},
        "search_space": {"min": args.offset_min, "max": args.offset_max, "step": args.offset_step},
        "evaluation": {"train_min_weeks": args.train_min_weeks, "test_weeks": args.test_weeks, "step_weeks": args.step_weeks, "cost_bps": args.cost_bps},
    }
    with open(params_path, "w") as f:
        json.dump(params, f, indent=2)

    print(f"[OK] Recommended offset_days = {recommended}")
    print(f"[OK] Wrote: {params_path}")
    if not grid.empty:
        print(f"[OK] Wrote: {grid_path}")

    # Opcional: simulación live recalibration
    if args.simulate_live:
        ph, live = simulate_live_recalibration(
            dfw=dfw,
            score_w=score_w,
            offsets_days=offsets_days,
            on=args.on,
            off=args.off,
            cost_bps=args.cost_bps,
            train_years=args.train_years,
            train_min_weeks=args.train_min_weeks,
            test_weeks=args.test_weeks,
            step_weeks=args.step_weeks,
            change_threshold=args.change_threshold,
        )

        ph_path = os.path.join(out_dir, "regime_params_history.csv")
        live_path = os.path.join(out_dir, "regime_live_backtest.csv")
        ph.to_csv(ph_path, index=False)
        live.to_csv(live_path)

        print(f"[OK] Wrote: {ph_path}")
        print(f"[OK] Wrote: {live_path}")
        # resumen rápido
        sh = _ann_sharpe(live["strat_ret"])
        cg = _cagr(live["strat_ret"])
        mdd = _max_dd(live["strat_ret"])
        print(f"[LIVE SIM] Sharpe={sh:.2f}  CAGR={cg:.2%}  MDD={mdd:.2%}")

if __name__ == "__main__":
    main()
