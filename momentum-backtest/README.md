# QQQ Momentum Backtest (3M + 6M + 12M)

Run date: 2026-08-31

## Setup

- **Asset**: QQQ (Nasdaq-100 ETF)
- **Cash proxy**: SHY (iShares 1-3 Year Treasury Bond ETF)
- **Period**: 2002-08 → 2026-08 (289 months, ~24 years)
- **Signal**: average of 3-month, 6-month, 12-month past returns, skip most recent 1 month
- **Rule**: composite > 0 → long QQQ, else → hold SHY
- **Rebalance**: monthly, end of month

## Results

|  | Momentum | Buy & Hold QQQ |
|---|---:|---:|
| CAGR | +13.97% | +16.03% |
| Annual Vol | 14.61% | 18.85% |
| Sharpe | 0.972 | 0.887 |
| Max Drawdown | -22.6% | -49.7% |
| Total Return | 2233% | 3488% |
| Exposure | 80% in QQQ | 100% |

## Crisis Performance

| Event | Momentum | Buy & Hold | Loss Avoided |
|---|---:|---:|---:|
| GFC (2007-11 → 2009-03) | -18.8% | -44.6% | +25.8% |
| 2022 Bear (2022-01 → 2022-10) | -12.7% | -29.8% | +17.1% |
| COVID (2020-02 → 2020-03) | -12.9% | -12.9% | 0.0% |
| Q4 2018 | -16.7% | -16.7% | 0.0% |
| 2025 Tariff | -8.8% | -8.8% | 0.0% |

## Verdict

Momentum **improves Sharpe** (+0.085) and **cuts max drawdown in half** (22.6% vs 49.7%), at the cost of **~2% annual CAGR**.

However:
- It only wins 3 out of 25 years — the wins are big (GFC +29%, 2022 +20.6%) but the losses are frequent (-26% in 2003, -24.8% in 2023, etc.)
- It completely missed COVID and 2025 tariff crashes (signal was still ON when they hit)
- It's a slow signal — only catches multi-month drawdowns, not sharp V-shaped crashes

## Caveats

- **In-sample only** — no walk-forward / OOS validation
- **No transaction costs** — monthly rebalance costs not included
- **SHY inception 2002-07** — pre-2002 data excluded
- **Survivorship** — QQQ itself survived the dot-com era; not all Nasdaq funds did

## Files

```
data/
  qqq_daily_prices.csv         6911 rows of raw QQQ close prices
  shy_daily_prices.csv         6060 rows of raw SHY close prices
  monthly_prices.csv           end-of-month aligned prices
  monthly_signals.csv          3M/6M/12M momentum + composite + signal
  monthly_returns_full.csv     monthly strategy vs buy-hold returns + cumulative

results/
  backtest_summary.txt         full text output of the script
  yearly_comparison.csv        year-by-year return comparison
  crisis_analysis.csv          crisis period breakdown

scripts/
  run_momentum_backtest.py     fully reproducible — just run it
```

## Reproduce

```bash
pip install yfinance pandas numpy
python3 momentum-backtest/scripts/run_momentum_backtest.py
```
