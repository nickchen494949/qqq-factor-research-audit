#!/usr/bin/env python3
"""
TQQQ Momentum Backtest — 3x Leveraged Nasdaq
==============================================
Signal source:  QQQ prices (NOT TQQQ — avoid vol-drag distortion).
Trade vehicle:  TQQQ when signal ON, CASH (0% return) when signal OFF.
Signal:         3M+6M+12M composite momentum on QQQ, skip 1 month.

Three variants:
  1. Original momentum: exit when signal flips, regardless of P&L
  2. Never-sell-at-loss: hold underwater positions until recovery
  3. Buy & hold TQQQ

TQQQ inception: 2010-02-09. Backtest starts 2010-02 onward.
"""

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
log("Downloading QQQ and TQQQ...")
qqq_raw  = yf.download("QQQ",  start="1999-03-10", end="2026-08-31", auto_adjust=True)
tqqq_raw = yf.download("TQQQ", start="2010-02-09", end="2026-08-31", auto_adjust=True)

qqq_close  = qqq_raw["Close"].squeeze()
tqqq_close = tqqq_raw["Close"].squeeze()

# Save raw TQQQ daily
tqqq_daily = pd.DataFrame({"date": tqqq_close.index, "close": tqqq_close.values})
tqqq_daily.to_csv(DATA / "tqqq_daily_prices.csv", index=False)
log(f"  TQQQ daily: {len(tqqq_daily)} rows, {tqqq_daily['date'].iloc[0]} → {tqqq_daily['date'].iloc[-1]}")

# Monthly
qqq_m  = qqq_close.resample("ME").last()
tqqq_m = tqqq_close.resample("ME").last()

tqqq_ret = tqqq_m.pct_change()
qqq_ret  = qqq_m.pct_change()

# ── Momentum signal from QQQ ──────────────────────────────────
# Key: signal is derived from QQQ, NOT TQQQ (vol-drag distorts TQQQ trends)
mom_3m  = qqq_m.pct_change(periods=3).shift(1)
mom_6m  = qqq_m.pct_change(periods=6).shift(1)
mom_12m = qqq_m.pct_change(periods=12).shift(1)
composite = (mom_3m + mom_6m + mom_12m) / 3.0
base_signal = (composite > 0).astype(float)
signal_shifted = base_signal.shift(1)

# ── Align to TQQQ era ────────────────────────────────────────
df = pd.DataFrame({
    "qqq_price": qqq_m,
    "tqqq_price": tqqq_m,
    "tqqq_ret": tqqq_ret,
    "qqq_ret": qqq_ret,
    "mom_signal": signal_shifted,
}).dropna()

# Cash = 0% return
df["cash_ret"] = 0.0

log(f"  Backtest period: {df.index[0].strftime('%Y-%m')} → {df.index[-1].strftime('%Y-%m')}")
log(f"  Total months: {len(df)}")

# Save signals
sig_save = df[["qqq_price", "tqqq_price", "mom_signal"]].copy()
sig_save.index.name = "date"
sig_save.to_csv(DATA / "tqqq_monthly_signals.csv", float_format="%.6f")

# ── Strategy 1: Original momentum on TQQQ ─────────────────────
df["orig_ret"] = df["mom_signal"] * df["tqqq_ret"] + (1 - df["mom_signal"]) * df["cash_ret"]

# ── Strategy 2: Never sell at loss on TQQQ ────────────────────
nsol_returns = []
nsol_state = []
nsol_entry_px = []

in_tqqq = False
entry_px = None
forced_hold = False

for date, row in df.iterrows():
    sig = row["mom_signal"]
    price = row["tqqq_price"]
    
    if not in_tqqq:
        if sig == 1:
            in_tqqq = True
            entry_px = price
            forced_hold = False
            nsol_returns.append(row["tqqq_ret"])
            nsol_state.append("signal_long")
            nsol_entry_px.append(entry_px)
        else:
            nsol_returns.append(0.0)  # cash
            nsol_state.append("signal_cash")
            nsol_entry_px.append(None)
    else:
        if sig == 1 and not forced_hold:
            nsol_returns.append(row["tqqq_ret"])
            nsol_state.append("signal_long")
            nsol_entry_px.append(entry_px)
        elif sig == 0 or forced_hold:
            if price >= entry_px:
                nsol_returns.append(row["tqqq_ret"])
                nsol_state.append("tp_exit")
                nsol_entry_px.append(entry_px)
                in_tqqq = False
                entry_px = None
                forced_hold = False
            else:
                forced_hold = True
                nsol_returns.append(row["tqqq_ret"])
                nsol_state.append("forced_hold")
                nsol_entry_px.append(entry_px)

df["nsol_ret"] = nsol_returns
df["nsol_state"] = nsol_state
df["nsol_entry_px"] = nsol_entry_px

# ── Strategy 3: Buy & hold TQQQ ──────────────────────────────
df["bh_ret"] = df["tqqq_ret"]

# Cumulative
df["orig_cumret"] = (1 + df["orig_ret"]).cumprod()
df["nsol_cumret"] = (1 + df["nsol_ret"]).cumprod()
df["bh_cumret"]   = (1 + df["bh_ret"]).cumprod()

# Save full data
save_df = df.copy()
save_df.index.name = "date"
save_df.to_csv(DATA / "tqqq_monthly_returns_full.csv", float_format="%.6f")

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

m_orig = calc_metrics(df["orig_ret"], "Momentum → TQQQ/Cash")
m_nsol = calc_metrics(df["nsol_ret"], "Never Sell Loss → TQQQ/Cash")
m_bh   = calc_metrics(df["bh_ret"],   "Buy & Hold TQQQ")
m_qqq  = calc_metrics(df["qqq_ret"],  "Buy & Hold QQQ (reference)")

# ── Print results ─────────────────────────────────────────────
log()
log("=" * 78)
log("  STRATEGY RULES")
log("=" * 78)
log()
log("  Signal source:    QQQ (unleveraged) — NOT TQQQ")
log("  Trade vehicle:    TQQQ (3x leveraged Nasdaq-100)")
log("  Cash vehicle:     CASH (0% return)")
log()
log("  ENTRY:")
log("    At end of month, compute:")
log("      mom_3m  = QQQ return from t-4 to t-1")
log("      mom_6m  = QQQ return from t-7 to t-1")
log("      mom_12m = QQQ return from t-13 to t-1")
log("      composite = (mom_3m + mom_6m + mom_12m) / 3")
log("    If composite > 0 → BUY TQQQ at next month open")
log()
log("  EXIT (Original):")
log("    If composite ≤ 0 → SELL TQQQ, hold CASH. No questions asked.")
log()
log("  EXIT (Never Sell Loss):")
log("    If composite ≤ 0 AND current TQQQ price ≥ entry price → SELL (take profit)")
log("    If composite ≤ 0 AND current TQQQ price < entry price → HOLD (wait for recovery)")
log("    Once price recovers above entry → SELL at next month end")
log()
log("  Rebalance:        Monthly, end of month")
log("  Signal lag:        1 month (decide at t, execute at t+1)")
log()

log("=" * 78)
log("  HEAD-TO-HEAD COMPARISON")
log("=" * 78)
log()
log(f"  {'Metric':<22} {'Mom→TQQQ':>14} {'NeverSellLoss':>16} {'B&H TQQQ':>14} {'B&H QQQ':>14}")
log(f"  {'─'*22} {'─'*14} {'─'*16} {'─'*14} {'─'*14}")
log(f"  {'CAGR':<22} {m_orig['cagr']*100:>+13.2f}% {m_nsol['cagr']*100:>+15.2f}% {m_bh['cagr']*100:>+13.2f}% {m_qqq['cagr']*100:>+13.2f}%")
log(f"  {'Annual Vol':<22} {m_orig['vol']*100:>13.2f}% {m_nsol['vol']*100:>15.2f}% {m_bh['vol']*100:>13.2f}% {m_qqq['vol']*100:>13.2f}%")
log(f"  {'Sharpe':<22} {m_orig['sharpe']:>14.3f} {m_nsol['sharpe']:>16.3f} {m_bh['sharpe']:>14.3f} {m_qqq['sharpe']:>14.3f}")
log(f"  {'Max Drawdown':<22} {m_orig['max_dd']*100:>13.1f}% {m_nsol['max_dd']*100:>15.1f}% {m_bh['max_dd']*100:>13.1f}% {m_qqq['max_dd']*100:>13.1f}%")
log(f"  {'Max DD Date':<22} {m_orig['max_dd_date']:>14} {m_nsol['max_dd_date']:>16} {m_bh['max_dd_date']:>14} {m_qqq['max_dd_date']:>14}")
log(f"  {'Total Return':<22} {m_orig['total_ret']*100:>13.1f}% {m_nsol['total_ret']*100:>15.1f}% {m_bh['total_ret']*100:>13.1f}% {m_qqq['total_ret']*100:>13.1f}%")

exposure_orig = df["mom_signal"].mean()
forced = df[df["nsol_state"] == "forced_hold"]
nsol_in = df[df["nsol_state"].isin(["signal_long", "forced_hold", "tp_exit"])]
log(f"  {'TQQQ Exposure':<22} {exposure_orig*100:>13.0f}% {len(nsol_in)/len(df)*100:>15.0f}% {'100':>13}% {'(QQQ)':>14}")

# ── Dollar growth ─────────────────────────────────────────────
log()
log("  $10,000 invested at start:")
log(f"    Momentum → TQQQ:      ${10000 * (1 + m_orig['total_ret']):>12,.0f}")
log(f"    Never Sell Loss:       ${10000 * (1 + m_nsol['total_ret']):>12,.0f}")
log(f"    Buy & Hold TQQQ:      ${10000 * (1 + m_bh['total_ret']):>12,.0f}")
log(f"    Buy & Hold QQQ:       ${10000 * (1 + m_qqq['total_ret']):>12,.0f}")

# ── Forced hold episodes ─────────────────────────────────────
log()
log("=" * 78)
log("  FORCED HOLD EPISODES (Never-Sell-Loss variant)")
log("=" * 78)

episodes = []
current_episode = None

for date, row in df.iterrows():
    state = row["nsol_state"]
    if state == "forced_hold":
        if current_episode is None:
            current_episode = {
                "start": date, "entry_px": row["nsol_entry_px"],
                "months": [], "returns": [], "prices": [],
            }
        current_episode["months"].append(date)
        current_episode["returns"].append(row["tqqq_ret"])
        current_episode["prices"].append(row["tqqq_price"])
    elif state == "tp_exit" and current_episode is not None:
        current_episode["months"].append(date)
        current_episode["returns"].append(row["tqqq_ret"])
        current_episode["prices"].append(row["tqqq_price"])
        current_episode["end"] = date
        current_episode["outcome"] = "recovered → TP exit"
        episodes.append(current_episode)
        current_episode = None
    else:
        if current_episode is not None:
            current_episode["end"] = current_episode["months"][-1]
            current_episode["outcome"] = "signal re-entered before TP"
            episodes.append(current_episode)
            current_episode = None

if current_episode is not None:
    current_episode["end"] = current_episode["months"][-1]
    current_episode["outcome"] = "STILL HOLDING — never recovered"
    episodes.append(current_episode)

ep_rows = []
for i, ep in enumerate(episodes):
    n = len(ep["months"])
    cum_ret = (1 + pd.Series(ep["returns"])).prod() - 1
    min_px = min(ep["prices"])
    max_loss_from_entry = (min_px - ep["entry_px"]) / ep["entry_px"]
    log(f"  Ep {i+1}: {ep['start'].strftime('%Y-%m')} → {ep['end'].strftime('%Y-%m')}  "
        f"({n}mo)  entry: ${ep['entry_px']:.2f}  "
        f"worst: ${min_px:.2f} ({max_loss_from_entry*100:+.0f}%)  "
        f"cum: {cum_ret*100:+.1f}%  [{ep['outcome']}]")
    ep_rows.append({
        "episode": i+1, "start": ep["start"].strftime("%Y-%m"),
        "end": ep["end"].strftime("%Y-%m"), "months": n,
        "entry_price": round(ep["entry_px"], 2),
        "worst_price": round(min_px, 2),
        "worst_drawdown_from_entry_pct": round(max_loss_from_entry * 100, 1),
        "cumulative_return_pct": round(cum_ret * 100, 1),
        "outcome": ep["outcome"],
    })

pd.DataFrame(ep_rows).to_csv(RESULTS / "tqqq_forced_hold_episodes.csv", index=False)

if len(episodes) == 0:
    log("  (no forced hold episodes)")

log()
log(f"  Total forced hold months: {len(forced)} / {len(df)}")

# ── Year-by-year ──────────────────────────────────────────────
log()
log("=" * 78)
log("  YEAR-BY-YEAR")
log("=" * 78)
log(f"  {'Year':<6} {'Mom→TQQQ':>12} {'NvrSellLoss':>12} {'B&H TQQQ':>12} {'B&H QQQ':>10} {'Signal%':>8}")
log(f"  {'─'*4:<6} {'─'*10:>12} {'─'*10:>12} {'─'*10:>12} {'─'*8:>10} {'─'*7:>8}")

df["year"] = df.index.year
yearly_rows = []
for year, grp in df.groupby("year"):
    orig_yr = (1 + grp["orig_ret"]).prod() - 1
    nsol_yr = (1 + grp["nsol_ret"]).prod() - 1
    bh_yr = (1 + grp["bh_ret"]).prod() - 1
    qqq_yr = (1 + grp["qqq_ret"]).prod() - 1
    sig_pct = grp["mom_signal"].mean()
    log(f"  {year:<6} {orig_yr*100:>+11.1f}% {nsol_yr*100:>+11.1f}% {bh_yr*100:>+11.1f}% {qqq_yr*100:>+9.1f}% {sig_pct*100:>7.0f}%")
    yearly_rows.append({
        "year": year,
        "momentum_tqqq_pct": round(orig_yr * 100, 2),
        "never_sell_loss_pct": round(nsol_yr * 100, 2),
        "buyhold_tqqq_pct": round(bh_yr * 100, 2),
        "buyhold_qqq_pct": round(qqq_yr * 100, 2),
        "signal_on_pct": round(sig_pct * 100, 0),
    })

pd.DataFrame(yearly_rows).to_csv(RESULTS / "tqqq_yearly_comparison.csv", index=False)

# ── Crisis analysis ───────────────────────────────────────────
log()
log("=" * 78)
log("  CRISIS PERIODS — THIS IS WHERE IT MATTERS FOR TQQQ")
log("=" * 78)

crises = [
    ("2018-10", "2018-12", "Q4 2018"),
    ("2020-02", "2020-03", "COVID crash"),
    ("2022-01", "2022-10", "2022 bear"),
    ("2025-02", "2025-04", "2025 tariff"),
]

for start, end, name in crises:
    try:
        sub = df.loc[start:end]
        if len(sub) == 0:
            continue
        orig_c = (1 + sub["orig_ret"]).prod() - 1
        nsol_c = (1 + sub["nsol_ret"]).prod() - 1
        bh_c   = (1 + sub["bh_ret"]).prod() - 1
        qqq_c  = (1 + sub["qqq_ret"]).prod() - 1
        log(f"  {name:<16} Mom→TQQQ: {orig_c*100:>+7.1f}%  NeverSell: {nsol_c*100:>+7.1f}%  "
            f"B&H TQQQ: {bh_c*100:>+7.1f}%  B&H QQQ: {qqq_c*100:>+7.1f}%")
    except:
        pass

# ── The key question: leverage + momentum ─────────────────────
log()
log("=" * 78)
log("  THE KEY QUESTION: IS MOMENTUM + TQQQ BETTER THAN JUST QQQ?")
log("=" * 78)
log()
log(f"  Momentum → TQQQ:  CAGR {m_orig['cagr']*100:+.2f}%  Sharpe {m_orig['sharpe']:.3f}  MaxDD {m_orig['max_dd']*100:.1f}%")
log(f"  Buy & Hold QQQ:   CAGR {m_qqq['cagr']*100:+.2f}%  Sharpe {m_qqq['sharpe']:.3f}  MaxDD {m_qqq['max_dd']*100:.1f}%")
log()

if m_orig['cagr'] > m_qqq['cagr'] and m_orig['sharpe'] > m_qqq['sharpe']:
    log("  ✅ Momentum + TQQQ beats plain QQQ on BOTH CAGR and Sharpe.")
    log("     This is the real test: can timing + leverage beat unleveraged buy-hold?")
elif m_orig['sharpe'] > m_qqq['sharpe']:
    log("  ⚠️  Momentum + TQQQ has better Sharpe but check CAGR and drawdown tradeoffs.")
else:
    log("  ❌ Momentum + TQQQ does not clearly beat plain QQQ on risk-adjusted basis.")

log()
log("=" * 78)
log("  BOTTOM LINE")
log("=" * 78)
log()
log("  On TQQQ, momentum's value is primarily SURVIVAL.")
log(f"  Buy & hold TQQQ max drawdown: {m_bh['max_dd']*100:.1f}%")
log(f"  Momentum TQQQ max drawdown:   {m_orig['max_dd']*100:.1f}%")
log(f"  That's {(m_bh['max_dd']-m_orig['max_dd'])*100:.0f}pp of drawdown avoided.")
log()
log("  CAVEATS:")
log("  - In-sample only. No walk-forward / OOS validation.")
log("  - No transaction costs or slippage.")
log("  - TQQQ has daily rebalancing costs and tracking error not modeled.")
log("  - TQQQ may not exist in future severe drawdowns (ETF closure risk).")
log("  - Pre-2010 data not available (TQQQ inception 2010-02).")
log()

with open(RESULTS / "tqqq_backtest_summary.txt", "w") as f:
    f.write(output_buffer.getvalue())

log("All TQQQ outputs saved.")
