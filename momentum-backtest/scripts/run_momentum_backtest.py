#!/usr/bin/env python3
"""
QQQ Time-Series Momentum Backtest
==================================
Signal:  average of 3M, 6M, 12M past returns (skip most recent 1 month).
Rule:    composite > 0 → long QQQ, else → hold SHY (short-term treasury).
Rebal:   monthly, end-of-month.

Outputs (all saved to ../data/ and ../results/):
  - data/qqq_daily_prices.csv          raw daily close prices
  - data/shy_daily_prices.csv          cash proxy daily close prices
  - data/monthly_prices.csv            end-of-month prices for both
  - data/monthly_signals.csv           3M/6M/12M momentum + composite + binary signal
  - data/monthly_returns_full.csv      strategy vs buy-hold returns per month
  - results/backtest_summary.txt       full text output
  - results/yearly_comparison.csv      year-by-year results
  - results/crisis_analysis.csv        crisis period analysis

Reproducibility: pip install yfinance pandas numpy
                 python3 run_momentum_backtest.py
"""

import csv
import sys
import io
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
RESULTS = BASE / "results"
DATA.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

# Capture all output to both stdout and file
output_buffer = io.StringIO()

def log(msg=""):
    print(msg)
    output_buffer.write(msg + "\n")

log(f"Run timestamp: {datetime.now().isoformat()}")
log(f"Python: {sys.version}")
log()

# ── 1. Download raw data ──────────────────────────────────────
log("=" * 60)
log("  STEP 1: Download raw price data")
log("=" * 60)

qqq_raw = yf.download("QQQ", start="1999-03-10", end="2026-08-31", auto_adjust=True)
shy_raw = yf.download("SHY", start="2002-07-22", end="2026-08-31", auto_adjust=True)

# Save raw daily prices
qqq_close = qqq_raw["Close"].squeeze()
shy_close = shy_raw["Close"].squeeze()

qqq_daily = pd.DataFrame({"date": qqq_close.index, "close": qqq_close.values})
qqq_daily.to_csv(DATA / "qqq_daily_prices.csv", index=False)
log(f"  QQQ daily prices: {len(qqq_daily)} rows, {qqq_daily['date'].iloc[0]} → {qqq_daily['date'].iloc[-1]}")

shy_daily = pd.DataFrame({"date": shy_close.index, "close": shy_close.values})
shy_daily.to_csv(DATA / "shy_daily_prices.csv", index=False)
log(f"  SHY daily prices: {len(shy_daily)} rows, {shy_daily['date'].iloc[0]} → {shy_daily['date'].iloc[-1]}")

# ── 2. Monthly prices ─────────────────────────────────────────
log()
log("=" * 60)
log("  STEP 2: Compute monthly end-of-month prices")
log("=" * 60)

qqq_m = qqq_close.resample("ME").last()
shy_m = shy_close.resample("ME").last()

monthly_prices = pd.DataFrame({"qqq_close": qqq_m, "shy_close": shy_m}).dropna()
monthly_prices.index.name = "date"
monthly_prices.to_csv(DATA / "monthly_prices.csv")
log(f"  Monthly prices (aligned): {len(monthly_prices)} months")
log(f"  Period: {monthly_prices.index[0].strftime('%Y-%m')} → {monthly_prices.index[-1].strftime('%Y-%m')}")

# Monthly returns
qqq_ret = qqq_m.pct_change()
shy_ret = shy_m.pct_change()

# ── 3. Momentum signals ───────────────────────────────────────
log()
log("=" * 60)
log("  STEP 3: Compute momentum signals")
log("=" * 60)
log("  Method: skip most recent 1 month (avoid short-term reversal)")
log("  mom_3m  = price return from t-4 to t-1")
log("  mom_6m  = price return from t-7 to t-1")
log("  mom_12m = price return from t-13 to t-1")
log("  composite = (mom_3m + mom_6m + mom_12m) / 3")
log("  signal = 1 if composite > 0, else 0")

mom_3m  = qqq_m.pct_change(periods=3).shift(1)
mom_6m  = qqq_m.pct_change(periods=6).shift(1)
mom_12m = qqq_m.pct_change(periods=12).shift(1)
composite = (mom_3m + mom_6m + mom_12m) / 3.0
signal = (composite > 0).astype(float)

signals_df = pd.DataFrame({
    "qqq_price": qqq_m,
    "mom_3m": mom_3m,
    "mom_6m": mom_6m,
    "mom_12m": mom_12m,
    "composite": composite,
    "signal": signal,
})
signals_df.index.name = "date"
signals_df.to_csv(DATA / "monthly_signals.csv", float_format="%.6f")
log(f"  Signals computed: {signals_df['signal'].dropna().shape[0]} months with signal")
log(f"  Signal ON  (long QQQ): {int(signal.dropna().sum())} months")
log(f"  Signal OFF (hold SHY): {int(len(signal.dropna()) - signal.dropna().sum())} months")

# ── 4. Backtest ───────────────────────────────────────────────
log()
log("=" * 60)
log("  STEP 4: Backtest")
log("=" * 60)

# Signal at end of month t → position during month t+1
signal_shifted = signal.shift(1)

df = pd.DataFrame({
    "qqq_ret": qqq_ret,
    "shy_ret": shy_ret,
    "signal": signal_shifted,
}).dropna()

df["strat_ret"] = df["signal"] * df["qqq_ret"] + (1 - df["signal"]) * df["shy_ret"]
df["buyhold_ret"] = df["qqq_ret"]
df["strat_cumret"] = (1 + df["strat_ret"]).cumprod()
df["buyhold_cumret"] = (1 + df["buyhold_ret"]).cumprod()

# Save full monthly returns
save_df = df.copy()
save_df.index.name = "date"
save_df.to_csv(DATA / "monthly_returns_full.csv", float_format="%.6f")
log(f"  Backtest period: {df.index[0].strftime('%Y-%m')} → {df.index[-1].strftime('%Y-%m')}")
log(f"  Total months: {len(df)}")

# ── 5. Performance metrics ────────────────────────────────────
log()
log("=" * 60)
log("  STEP 5: Performance Summary")
log("=" * 60)

results = {}

def calc_metrics(returns, label, signal_col=None):
    cum = (1 + returns).cumprod()
    total_ret = cum.iloc[-1] - 1
    n_years = len(returns) / 12
    cagr = (cum.iloc[-1]) ** (1 / n_years) - 1
    vol = returns.std() * np.sqrt(12)
    sharpe = (returns.mean() * 12) / vol if vol > 0 else 0
    
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin().strftime('%Y-%m')
    
    hit_rate = (returns > 0).mean()
    
    log(f"\n  ┌─────────────────────────────────────────────┐")
    log(f"  │  {label:<43} │")
    log(f"  ├─────────────────────────────────────────────┤")
    log(f"  │  Period:         {df.index[0].strftime('%Y-%m')} → {df.index[-1].strftime('%Y-%m'):<24} │")
    log(f"  │  Total months:   {len(returns):<27} │")
    if signal_col is not None:
        m_in = int(signal_col.sum())
        m_out = len(signal_col) - m_in
        log(f"  │  Months in QQQ:  {m_in} ({m_in/len(returns)*100:.0f}%){' '*(20-len(str(m_in))-len(f'({m_in/len(returns)*100:.0f}%)'))} │")
        log(f"  │  Months in SHY:  {m_out} ({m_out/len(returns)*100:.0f}%){' '*(20-len(str(m_out))-len(f'({m_out/len(returns)*100:.0f}%)'))} │")
    log(f"  │  CAGR:           {cagr*100:>+8.2f}%{' '*18} │")
    log(f"  │  Annual Vol:     {vol*100:>8.2f}%{' '*18} │")
    log(f"  │  Sharpe Ratio:   {sharpe:>8.3f}{' '*19} │")
    log(f"  │  Max Drawdown:   {max_dd*100:>8.1f}%  ({max_dd_date}){' '*(11-len(max_dd_date))} │")
    log(f"  │  Hit Rate:       {hit_rate*100:>8.1f}%{' '*18} │")
    log(f"  │  Total Return:   {total_ret*100:>8.1f}%{' '*18} │")
    log(f"  └─────────────────────────────────────────────┘")
    
    results[label] = {
        "cagr": cagr, "vol": vol, "sharpe": sharpe, 
        "max_dd": max_dd, "max_dd_date": max_dd_date,
        "hit_rate": hit_rate, "total_ret": total_ret
    }

calc_metrics(df["strat_ret"], "Momentum 3M+6M+12M", df["signal"])
calc_metrics(df["buyhold_ret"], "Buy & Hold QQQ")

# ── 6. Signal effectiveness ───────────────────────────────────
log()
log("=" * 60)
log("  STEP 6: Signal Effectiveness")
log("=" * 60)

on_ret = df.loc[df["signal"] == 1, "qqq_ret"]
off_ret = df.loc[df["signal"] == 0, "qqq_ret"]

log(f"  When LONG QQQ (signal=1):")
log(f"    Months:             {len(on_ret)}")
log(f"    Avg monthly ret:    {on_ret.mean()*100:+.2f}%")
log(f"    Annualized:         {on_ret.mean()*12*100:+.2f}%")
log(f"    Monthly vol:        {on_ret.std()*100:.2f}%")
log()
log(f"  When OUT / SHY (signal=0):")
log(f"    Months:             {len(off_ret)}")
log(f"    Avg monthly QQQ:   {off_ret.mean()*100:+.2f}%")
log(f"    Annualized QQQ:    {off_ret.mean()*12*100:+.2f}%")
log(f"    Monthly vol QQQ:   {off_ret.std()*100:.2f}%")
log()
log(f"  Signal discriminates: {on_ret.mean()*12*100:+.2f}% vs {off_ret.mean()*12*100:+.2f}% annualized")
log(f"  Spread:               {(on_ret.mean()-off_ret.mean())*12*100:+.2f}% per year")

# ── 7. Year-by-year ───────────────────────────────────────────
log()
log("=" * 60)
log("  STEP 7: Year-by-Year Comparison")
log("=" * 60)
log(f"  {'Year':<6} {'Momentum':>10} {'Buy&Hold':>10} {'Excess':>10} {'Signal%':>8}")
log(f"  {'─'*4:<6} {'─'*8:>10} {'─'*8:>10} {'─'*6:>10} {'─'*7:>8}")

yearly_rows = []
df["year"] = df.index.year
for year, grp in df.groupby("year"):
    strat_yr = (1 + grp["strat_ret"]).prod() - 1
    bh_yr = (1 + grp["buyhold_ret"]).prod() - 1
    sig_pct = grp["signal"].mean()
    excess = strat_yr - bh_yr
    log(f"  {year:<6} {strat_yr*100:>+9.1f}% {bh_yr*100:>+9.1f}% {excess*100:>+9.1f}% {sig_pct*100:>7.0f}%")
    yearly_rows.append({
        "year": year, 
        "momentum_return_pct": round(strat_yr * 100, 2),
        "buyhold_return_pct": round(bh_yr * 100, 2),
        "excess_return_pct": round(excess * 100, 2),
        "signal_on_pct": round(sig_pct * 100, 0),
    })

yearly_df = pd.DataFrame(yearly_rows)
yearly_df.to_csv(RESULTS / "yearly_comparison.csv", index=False)

# Win/loss years
excess_series = yearly_df["excess_return_pct"]
log(f"\n  Years momentum beats B&H:   {(excess_series > 0).sum()} / {len(excess_series)}")
log(f"  Years momentum trails B&H:  {(excess_series < 0).sum()} / {len(excess_series)}")
log(f"  Avg excess when winning:    {excess_series[excess_series > 0].mean():+.1f}%")
log(f"  Avg excess when losing:     {excess_series[excess_series < 0].mean():+.1f}%")

# ── 8. Crisis periods ────────────────────────────────────────
log()
log("=" * 60)
log("  STEP 8: Crisis Period Analysis")
log("=" * 60)

crises = [
    ("2000-04", "2002-10", "Dot-com crash"),
    ("2007-11", "2009-03", "GFC"),
    ("2018-10", "2018-12", "Q4 2018 selloff"),
    ("2020-02", "2020-03", "COVID crash"),
    ("2022-01", "2022-10", "2022 bear market"),
    ("2025-02", "2025-04", "2025 tariff shock"),
]

crisis_rows = []
for start, end, name in crises:
    try:
        sub = df.loc[start:end]
        if len(sub) == 0:
            log(f"  {name:<22} (no data in range)")
            continue
        strat_crisis = (1 + sub["strat_ret"]).prod() - 1
        bh_crisis = (1 + sub["buyhold_ret"]).prod() - 1
        sig_pct = sub["signal"].mean()
        avoided = strat_crisis - bh_crisis
        log(f"  {name:<22} Mom: {strat_crisis*100:>+7.1f}%  B&H: {bh_crisis*100:>+7.1f}%  Avoided: {avoided*100:>+7.1f}%  Signal: {sig_pct*100:.0f}% long")
        crisis_rows.append({
            "period": f"{start} to {end}",
            "event": name,
            "momentum_return_pct": round(strat_crisis * 100, 2),
            "buyhold_return_pct": round(bh_crisis * 100, 2),
            "loss_avoided_pct": round(avoided * 100, 2),
            "signal_on_pct": round(sig_pct * 100, 0),
        })
    except Exception as e:
        log(f"  {name:<22} (error: {e})")

crisis_df = pd.DataFrame(crisis_rows)
crisis_df.to_csv(RESULTS / "crisis_analysis.csv", index=False)

# ── 9. Bottom line ────────────────────────────────────────────
log()
log("=" * 60)
log("  BOTTOM LINE")
log("=" * 60)

m = results["Momentum 3M+6M+12M"]
b = results["Buy & Hold QQQ"]

log(f"  CAGR:       Momentum {m['cagr']*100:+.2f}%  vs  B&H {b['cagr']*100:+.2f}%  →  {(m['cagr']-b['cagr'])*100:+.2f}%")
log(f"  Sharpe:     Momentum {m['sharpe']:.3f}    vs  B&H {b['sharpe']:.3f}    →  {m['sharpe']-b['sharpe']:+.3f}")
log(f"  Max DD:     Momentum {m['max_dd']*100:.1f}%   vs  B&H {b['max_dd']*100:.1f}%   →  {(m['max_dd']-b['max_dd'])*100:+.1f}% less pain")
log(f"  Exposure:   Only in QQQ {df['signal'].mean()*100:.0f}% of months")
log()

if m['sharpe'] > b['sharpe']:
    log("  ✅ Momentum improves risk-adjusted returns (higher Sharpe).")
else:
    log("  ❌ Momentum does NOT improve risk-adjusted returns.")

if abs(m['max_dd']) < abs(b['max_dd']):
    log(f"  ✅ Momentum reduces worst drawdown by {(b['max_dd']-m['max_dd'])*100:.1f}pp.")
else:
    log(f"  ❌ Momentum does NOT reduce worst drawdown.")

if m['cagr'] > b['cagr']:
    log(f"  ✅ Momentum improves CAGR by {(m['cagr']-b['cagr'])*100:.2f}pp.")
else:
    log(f"  ⚠️  Momentum trails CAGR by {(b['cagr']-m['cagr'])*100:.2f}pp (expected: fewer months exposed).")

log()
log("  CAVEAT: This is in-sample. No walk-forward / OOS split applied.")
log("  CAVEAT: No transaction costs or slippage included.")
log("  CAVEAT: SHY used as cash proxy; SHY inception 2002-07, pre-2002 months excluded.")
log()

# ── Save full output ──────────────────────────────────────────
with open(RESULTS / "backtest_summary.txt", "w") as f:
    f.write(output_buffer.getvalue())

log(f"All outputs saved to:")
log(f"  {DATA}/qqq_daily_prices.csv")
log(f"  {DATA}/shy_daily_prices.csv")
log(f"  {DATA}/monthly_prices.csv")
log(f"  {DATA}/monthly_signals.csv")
log(f"  {DATA}/monthly_returns_full.csv")
log(f"  {RESULTS}/backtest_summary.txt")
log(f"  {RESULTS}/yearly_comparison.csv")
log(f"  {RESULTS}/crisis_analysis.csv")
