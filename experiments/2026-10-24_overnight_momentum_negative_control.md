# Overnight research checkpoint — 2026-10-24

Status: **EXPLORATORY NEGATIVE RESULT, NOT A STRATEGY PASS.** This is an additive experiment; existing QQQ Factor Research Audit conclusions are not changed.

## Objective

Find a mechanism-based, reproducible, unlevered stock strategy that exceeds TQQQ buy-and-hold on robust out-of-sample, net-of-cost CAGR. Sector pricing power, fundamentals acceleration, and *point-in-time* EPS revisions remain the intended factors. This first price-only proxy test does **not** establish such a strategy.

## Dataset and periods

- Public third-party Yahoo Finance *adjusted close* archive: `https://github.com/holochart/holochart/blob/main/examples/demos/tqqq-soxl/data/daily.json` and `SOURCES.md` in that folder. Source indicates Yahoo chart API, retrieved 2026-10-01.
- Split- and dividend-adjusted daily closes; shared calendar. The source dataset's current end is **2026-10-01**, not October 23.
- Four ETFs: QQQ, SOXX, TQQQ, SOXL. TQQQ and SOXL are 3x leveraged funds, unsuitable as evidence for the intended *unlevered* strategy.
- Common backtest date: **2011-04-01 through 2026-10-01**, allowing trailing lookbacks. Benchmark holds TQQQ over identical days; separate whole-TQQQ-since-inception 2010-02-11 reference CAGR approximately 43.0%, daily MDD -81.66%.

## Locked exploratory rules

On the first trading day of each month, determine which of a pre-chosen pair had the higher momentum from the month-end **(current month - lookback - 1)** to **(current month - 2)**, i.e. omit last complete month, then switch at the **first trading day's close**. Returns up through that execution-day close accrue to the old holding. Each buy or sell costs 10 basis points of the notional; switching costs 20 basis points. No cash fallback, no intramonth exit, no EPS inputs. Compare 6-1 and 12-1 month momentum signals. Daily drawdown uses the daily adjusted price path.

**This is a retrospectively chosen two-ETF universe. The 2022+ subperiod is a chronological slice, NOT genuinely untouched out-of-sample data.**

## Results (annualized CAGR, percent)

| Rule | 2011-04–2026-10-01 CAGR | Daily MDD | Sortino | Total charged trade legs |
| --- | ---: | ---: | ---: | ---: |
| TQQQ buy and hold | 40.14 | -81.66 | 1.22 | — |
| SOXL buy and hold | 39.61 | -90.46 | 1.20 | — |
| QQQ buy and hold | 18.96 | -35.12 | 1.34 | — |
| SOXX buy and hold | 25.66 | -45.75 | 1.29 | — |
| QQQ/SOXX 12-1, monthly | 23.50 | -34.25 | 1.28 | 65 |
| QQQ/SOXX 6-1, monthly | 26.08 | -34.25 | 1.40 | 81 |
| TQQQ/SOXL 12-1, monthly | 43.48 | -80.38 | 1.22 | 53 |
| TQQQ/SOXL 6-1, monthly | 47.57 | -84.07 | 1.28 | 89 |

## Disqualifying robustness

| Time window | TQQQ buy-hold CAGR | TQQQ/SOXL 6-1 CAGR | TQQQ/SOXL 12-1 CAGR |
| --- | ---: | ---: | ---: |
| 2011-04–2025-12 | **38.69** | 37.86 | 33.84 |
| 2022-01–2025-12 | **7.31** | 0.96 | -8.71 |
| 2011-04–2019-12 | 44.11 | 52.58 | 57.81 |
| 2020-01–2025-12 | **31.19** | 18.93 | 5.26 |
| 2011-04–2026-10-01 | 40.14 | **47.57** | 43.48 |

The apparent full-period winner fails as soon as partial 2026 is excluded; TQQQ 2026-to-October-1 was about **+50.2%**, while the 6-1 TQQQ/SOXL rotation was **+265.9%**. One 2026 semiconductor-led episode overwhelms the whole-period comparison. Thus **no discovery, no pass, no deployment recommendation**.

## Research limitations

1. ETF pair chosen with hindsight; universe selection and instrument inception bias unaddressed.
2. Rotation trades at first trading day close, as assumed; friction is fixed at 0.1% per leg, excludes taxes, execution/market-impact estimation and some ETF costs implicitly embedded in prices.
3. No causal profitability test: does not test EPS revisions or company pricing power; original research audit explicitly blocks missing historical *point-in-time* aggregate EPS/revision inputs.
4. No independent vendor reconciliation, no PIT constituents/delisted-stock coverage, no external walk-forward validation.
5. Chronological 2022–2026 split used for diagnostics only. Do not advertise as genuine OOS performance.

## Next experiments

- Acquire and timestamp universe definitions with former and delisted constituents plus corporate actions. Test individual stocks without leveraged ETFs.
- Gather revision snapshots from a provider preserving as-of dates; otherwise omit revisions from hypothesis tests, rather than substitute today's historical fundamentals.
- Preregister a compact family of price momentum / fundamentals rules; hold out calendar periods and whole industries; compare with TQQQ after full costs and with all dates matched.
- Preserve both null findings and qualifying discoveries in the repository; do not turn a fragile sample-period gain into a live allocation rule.
