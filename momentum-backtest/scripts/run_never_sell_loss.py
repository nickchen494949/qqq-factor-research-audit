#!/usr/bin/env python3
"""
QQQ Momentum Backtest — "Never Sell at Loss" variant
=====================================================
Base signal: same 3M+6M+12M composite momentum.
Twist:       when signal says EXIT, only exit if current price >= entry price.
             If underwater, hold QQQ until price recovers above entry, then exit.

Comparison:  original momentum vs never-sell-at-loss vs buy-and-hold.
"""

import csv
import sys
import io
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
RESULTS = BASE / "results"
DATA.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)

output_buffer = io.StringIO()

def log(msg=""):
    print(msg)
    output_buffer.write(msg + "\n")

log(f"Run timestamp: {datetime.now().isoformat()}")
log()

# ── Download data ──────────────────────────────────────────────
log("Downloading QQQ and SHY...")
qqq_raw = yf.download("QQQ", start="1999-03-10", end="2026-08-31", auto_adjust=True)
shy_raw = yf.download("SHY", start="2002-07-22", end="2026-08-31", auto_adjust=True)

qqq_close = qqq_raw["Close"].squeeze()
shy_close = shy_raw["Close"].squeeze()

qqq_m = qqq_close.resample("ME").last()
shy_m = shy_close.resample("ME").last()

qqq_ret = qqq_m.pct_change()
shy_ret = shy_m.pct_change()

# ── Momentum signal (same as original) ────────────────────────
mom_3m  = qqq_m.pct_change(periods=3).shift(1)
mom_6m  = qqq_m.pct_change(periods=6).shift(1)
mom_12m = qqq_m.pct_change(periods=12).shift(1)
composite = (mom_3m + mom_6m + mom_12m) / 3.0
base_signal = (composite > 0).astype(float)

# ── Build three strategies ────────────────────────────────────
signal_shifted = base_signal.shift(1)

df = pd.DataFrame({
    "qqq_price": qqq_m,
    "qqq_ret": qqq_ret,
    "shy_ret": shy_ret,
    "mom_signal": signal_shifted,
}).dropna()

# Strategy 1: Original momentum (sell regardless of P&L)
df["orig_ret"] = df["mom_signal"] * df["qqq_ret"] + (1 - df["mom_signal"]) * df["shy_ret"]

# Strategy 2: Never sell at loss — only take profit
#   Track entry price. When signal says exit:
#     if current price >= entry → sell (TP), go SHY
#     if current price <  entry → hold QQQ, wait for recovery

nsol_position = []   # 1 = in QQQ, 0 = in SHY
nsol_entry_price = []
nsol_returns = []
nsol_state = []      # 'signal_long', 'forced_hold', 'signal_cash', 'tp_exit'

in_qqq = False
entry_px = None
forced_hold = False  # signal says exit but we're underwater

for i, (date, row) in enumerate(df.iterrows()):
    sig = row["mom_signal"]
    price = row["qqq_price"]
    
    if not in_qqq:
        # Currently in SHY
        if sig == 1:
            # Signal says enter → buy QQQ
            in_qqq = True
            entry_px = price
            forced_hold = False
            nsol_position.append(1)
            nsol_entry_price.append(entry_px)
            nsol_returns.append(row["qqq_ret"])
            nsol_state.append("signal_long")
        else:
            # Stay in SHY
            nsol_position.append(0)
            nsol_entry_price.append(None)
            nsol_returns.append(row["shy_ret"])
            nsol_state.append("signal_cash")
    else:
        # Currently in QQQ
        if sig == 1 and not forced_hold:
            # Signal still says hold → stay
            nsol_position.append(1)
            nsol_entry_price.append(entry_px)
            nsol_returns.append(row["qqq_ret"])
            nsol_state.append("signal_long")
        elif sig == 0 or forced_hold:
            # Signal says exit (or we were already forced holding)
            if price >= entry_px:
                # In profit → take profit, go to SHY
                # But we already earned QQQ return this month while holding
                # Now we exit at end of this month
                nsol_position.append(1)  # still held QQQ this month
                nsol_entry_price.append(entry_px)
                nsol_returns.append(row["qqq_ret"])
                nsol_state.append("tp_exit")
                in_qqq = False
                entry_px = None
                forced_hold = False
            else:
                # Underwater → refuse to sell, keep holding
                forced_hold = True
                nsol_position.append(1)
                nsol_entry_price.append(entry_px)
                nsol_returns.append(row["qqq_ret"])
                nsol_state.append("forced_hold")

df["nsol_position"] = nsol_position
df["nsol_entry_price"] = nsol_entry_price
df["nsol_ret"] = nsol_returns
df["nsol_state"] = nsol_state

# Strategy 3: Buy & hold
df["bh_ret"] = df["qqq_ret"]

# ── Cumulative returns ────────────────────────────────────────
df["orig_cumret"] = (1 + df["orig_ret"]).cumprod()
df["nsol_cumret"] = (1 + df["nsol_ret"]).cumprod()
df["bh_cumret"]   = (1 + df["bh_ret"]).cumprod()

# ── Save full data ────────────────────────────────────────────
save_df = df.copy()
save_df.index.name = "date"
save_df.to_csv(DATA / "monthly_returns_never_sell_loss.csv", float_format="%.6f")

# ── Performance metrics ───────────────────────────────────────
def calc_metrics(returns, label):
    cum = (1 + returns).cumprod()
    n_years = len(returns) / 12
    cagr = (cum.iloc[-1]) ** (1 / n_years) - 1
    vol = returns.std() * np.sqrt(12)
    sharpe = (returns.mean() * 12) / vol if vol > 0 else 0
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin().strftime('%Y-%m')
    total_ret = cum.iloc[-1] - 1
    
    return {
        "label": label, "cagr": cagr, "vol": vol, "sharpe": sharpe,
        "max_dd": max_dd, "max_dd_date": max_dd_date, "total_ret": total_ret,
    }

m_orig = calc_metrics(df["orig_ret"], "Original Momentum")
m_nsol = calc_metrics(df["nsol_ret"], "Never Sell at Loss")
m_bh   = calc_metrics(df["bh_ret"],   "Buy & Hold QQQ")

# ── Print comparison ──────────────────────────────────────────
log()
log("=" * 70)
log("  HEAD-TO-HEAD COMPARISON")
log("=" * 70)
log()
log(f"  {'Metric':<22} {'Original Mom':>14} {'Never Sell Loss':>16} {'Buy & Hold':>14}")
log(f"  {'─'*22} {'─'*14} {'─'*16} {'─'*14}")
log(f"  {'CAGR':<22} {m_orig['cagr']*100:>+13.2f}% {m_nsol['cagr']*100:>+15.2f}% {m_bh['cagr']*100:>+13.2f}%")
log(f"  {'Annual Vol':<22} {m_orig['vol']*100:>13.2f}% {m_nsol['vol']*100:>15.2f}% {m_bh['vol']*100:>13.2f}%")
log(f"  {'Sharpe':<22} {m_orig['sharpe']:>14.3f} {m_nsol['sharpe']:>16.3f} {m_bh['sharpe']:>14.3f}")
log(f"  {'Max Drawdown':<22} {m_orig['max_dd']*100:>13.1f}% {m_nsol['max_dd']*100:>15.1f}% {m_bh['max_dd']*100:>13.1f}%")
log(f"  {'Max DD Date':<22} {m_orig['max_dd_date']:>14} {m_nsol['max_dd_date']:>16} {m_bh['max_dd_date']:>14}")
log(f"  {'Total Return':<22} {m_orig['total_ret']*100:>13.1f}% {m_nsol['total_ret']*100:>15.1f}% {m_bh['total_ret']*100:>13.1f}%")

# ── Forced hold analysis ─────────────────────────────────────
log()
log("=" * 70)
log("  FORCED HOLD ANALYSIS (months where signal said EXIT but held at loss)")
log("=" * 70)

forced = df[df["nsol_state"] == "forced_hold"]
tp_exits = df[df["nsol_state"] == "tp_exit"]
signal_long = df[df["nsol_state"] == "signal_long"]
signal_cash = df[df["nsol_state"] == "signal_cash"]

log(f"  Total months:                    {len(df)}")
log(f"  Signal long (normal):            {len(signal_long)} ({len(signal_long)/len(df)*100:.0f}%)")
log(f"  Signal cash (normal):            {len(signal_cash)} ({len(signal_cash)/len(df)*100:.0f}%)")
log(f"  Forced hold (underwater):        {len(forced)} ({len(forced)/len(df)*100:.0f}%)")
log(f"  Take-profit exit:                {len(tp_exits)} ({len(tp_exits)/len(df)*100:.0f}%)")

if len(forced) > 0:
    log()
    log(f"  Forced hold months breakdown:")
    log(f"    Avg QQQ return during forced hold: {forced['qqq_ret'].mean()*100:+.2f}%")
    log(f"    Months where QQQ went up:          {(forced['qqq_ret'] > 0).sum()} / {len(forced)}")
    log(f"    Months where QQQ went down:        {(forced['qqq_ret'] <= 0).sum()} / {len(forced)}")
    log(f"    Worst month during forced hold:    {forced['qqq_ret'].min()*100:+.1f}%")
    log(f"    Best month during forced hold:     {forced['qqq_ret'].max()*100:+.1f}%")

# ── Show each forced-hold episode ─────────────────────────────
log()
log("=" * 70)
log("  FORCED HOLD EPISODES (each time you got stuck)")
log("=" * 70)

# Identify contiguous episodes of forced_hold + the tp_exit that ends them
episodes = []
current_episode = None

for date, row in df.iterrows():
    state = row["nsol_state"]
    if state == "forced_hold":
        if current_episode is None:
            current_episode = {
                "start": date,
                "entry_px": row["nsol_entry_price"],
                "months": [],
                "returns": [],
            }
        current_episode["months"].append(date)
        current_episode["returns"].append(row["qqq_ret"])
    elif state == "tp_exit" and current_episode is not None:
        current_episode["months"].append(date)
        current_episode["returns"].append(row["qqq_ret"])
        current_episode["end"] = date
        current_episode["exit_px"] = row["qqq_price"]
        episodes.append(current_episode)
        current_episode = None
    else:
        if current_episode is not None:
            # Episode ended without TP (signal went back to long)
            current_episode["end"] = current_episode["months"][-1]
            current_episode["exit_px"] = df.loc[current_episode["end"], "qqq_price"]
            current_episode["note"] = "signal re-entered before TP"
            episodes.append(current_episode)
            current_episode = None

# Handle episode still open at end
if current_episode is not None:
    current_episode["end"] = current_episode["months"][-1]
    current_episode["exit_px"] = df.loc[current_episode["end"], "qqq_price"]
    current_episode["note"] = "STILL HOLDING — never recovered"
    episodes.append(current_episode)

episode_rows = []
for i, ep in enumerate(episodes):
    n_months = len(ep["months"])
    cum_ret = (1 + pd.Series(ep["returns"])).prod() - 1
    note = ep.get("note", "recovered → TP exit")
    log(f"  Episode {i+1}: {ep['start'].strftime('%Y-%m')} → {ep['end'].strftime('%Y-%m')}  "
        f"({n_months} months)  entry: ${ep['entry_px']:.2f}  "
        f"cum QQQ: {cum_ret*100:+.1f}%  [{note}]")
    episode_rows.append({
        "episode": i+1,
        "start": ep["start"].strftime("%Y-%m"),
        "end": ep["end"].strftime("%Y-%m"),
        "months_stuck": n_months,
        "entry_price": round(ep["entry_px"], 2),
        "cumulative_qqq_return_pct": round(cum_ret * 100, 2),
        "outcome": note,
    })

pd.DataFrame(episode_rows).to_csv(RESULTS / "forced_hold_episodes.csv", index=False)

# ── Year by year ──────────────────────────────────────────────
log()
log("=" * 70)
log("  YEAR-BY-YEAR")
log("=" * 70)
log(f"  {'Year':<6} {'Orig Mom':>10} {'NeverSellLoss':>14} {'Buy&Hold':>10}")
log(f"  {'─'*4:<6} {'─'*8:>10} {'─'*13:>14} {'─'*8:>10}")

df["year"] = df.index.year
yearly_rows = []
for year, grp in df.groupby("year"):
    orig_yr = (1 + grp["orig_ret"]).prod() - 1
    nsol_yr = (1 + grp["nsol_ret"]).prod() - 1
    bh_yr = (1 + grp["bh_ret"]).prod() - 1
    log(f"  {year:<6} {orig_yr*100:>+9.1f}% {nsol_yr*100:>+13.1f}% {bh_yr*100:>+9.1f}%")
    yearly_rows.append({
        "year": year,
        "original_momentum_pct": round(orig_yr * 100, 2),
        "never_sell_loss_pct": round(nsol_yr * 100, 2),
        "buyhold_pct": round(bh_yr * 100, 2),
    })

pd.DataFrame(yearly_rows).to_csv(RESULTS / "yearly_comparison_nsol.csv", index=False)

# ── Crisis periods ────────────────────────────────────────────
log()
log("=" * 70)
log("  CRISIS PERIODS")
log("=" * 70)

crises = [
    ("2007-11", "2009-03", "GFC"),
    ("2020-02", "2020-03", "COVID"),
    ("2022-01", "2022-10", "2022 Bear"),
    ("2025-02", "2025-04", "2025 Tariff"),
]

for start, end, name in crises:
    try:
        sub = df.loc[start:end]
        if len(sub) == 0:
            continue
        orig_c = (1 + sub["orig_ret"]).prod() - 1
        nsol_c = (1 + sub["nsol_ret"]).prod() - 1
        bh_c = (1 + sub["bh_ret"]).prod() - 1
        log(f"  {name:<16} Orig: {orig_c*100:>+7.1f}%  NeverSellLoss: {nsol_c*100:>+7.1f}%  B&H: {bh_c*100:>+7.1f}%")
    except:
        pass

# ── Bottom line ───────────────────────────────────────────────
log()
log("=" * 70)
log("  BOTTOM LINE")
log("=" * 70)
log()
log(f"  Original Momentum:    Sharpe {m_orig['sharpe']:.3f}  CAGR {m_orig['cagr']*100:+.2f}%  MaxDD {m_orig['max_dd']*100:.1f}%")
log(f"  Never Sell at Loss:   Sharpe {m_nsol['sharpe']:.3f}  CAGR {m_nsol['cagr']*100:+.2f}%  MaxDD {m_nsol['max_dd']*100:.1f}%")
log(f"  Buy & Hold:           Sharpe {m_bh['sharpe']:.3f}  CAGR {m_bh['cagr']*100:+.2f}%  MaxDD {m_bh['max_dd']*100:.1f}%")
log()

if m_nsol['sharpe'] > m_orig['sharpe']:
    log("  → Never-sell-at-loss IMPROVES Sharpe vs original momentum.")
elif m_nsol['sharpe'] < m_orig['sharpe']:
    log("  → Never-sell-at-loss WORSENS Sharpe vs original momentum.")
else:
    log("  → Never-sell-at-loss has same Sharpe as original momentum.")

if abs(m_nsol['max_dd']) > abs(m_orig['max_dd']):
    log(f"  → Never-sell-at-loss has WORSE max drawdown ({m_nsol['max_dd']*100:.1f}% vs {m_orig['max_dd']*100:.1f}%).")
else:
    log(f"  → Never-sell-at-loss has BETTER max drawdown ({m_nsol['max_dd']*100:.1f}% vs {m_orig['max_dd']*100:.1f}%).")

log()
log(f"  Forced hold months: {len(forced)} — these are months you were STUCK in a losing position")
log(f"  while the original strategy was safely in SHY.")
log()
log("  CAVEAT: In-sample only. No transaction costs.")
log()

# Save output
with open(RESULTS / "backtest_never_sell_loss.txt", "w") as f:
    f.write(output_buffer.getvalue())

log("All outputs saved.")
