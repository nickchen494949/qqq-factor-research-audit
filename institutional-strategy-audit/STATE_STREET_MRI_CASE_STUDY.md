# State Street MRI exploratory case study

## Question

Does State Street's Market Regime Indicator / TAA stance behave like a useful directional equity-timing signal, or primarily like a risk-control signal?

## Small point-in-time sample from prior chat

The prior chat assembled six dated State Street observations and compared them with subsequent SPY returns. Approximate observations used:

| Date | Public stance interpreted in prior pass | 3M SPY | 6M SPY |
|---|---|---:|---:|
| 2024-06-18 | Low-risk / equity overweight | +2.4% | +6.9% |
| 2025-03-19 | Risk worsened but modest equity overweight | +5.4% | +16.8% |
| 2025-04-11 | High-risk / equity underweight; more bonds & gold | +16.8% | +22.3% |
| 2025-07-22 | Risk-on improving; global equity mixed, US equity favored | +6.2% | +9.6% |
| 2025-09-22 | Strong risk-on / meaningful equity overweight | +2.7% | -1.7% |
| 2026-01-20 | Constructive / substantial equity overweight | +4.6% | +9.5% |

A crude +1/-1 encoding in the prior chat produced a negative correlation with future SPY returns. **That number is not statistically valid** because n=6, stance coding is subjective, global and US views were mixed in at least one case, and the portfolio objective is multi-asset rather than SPY prediction.

## Stronger evidence from State Street's own research

The more defensible finding comes from State Street's published rebalancing research. In the cited paper, MRI-regime-based rebalancing produced a return profile broadly similar to simple annual rebalancing while improving drawdown/risk characteristics rather than clearly boosting CAGR.

This supports the interpretation:

`MRI -> risk regime / sizing input`

rather than:

`MRI -> standalone buy/sell alpha signal`

## Mechanism

MRI incorporates market-derived risk measures such as equity implied volatility, FX implied volatility, and credit-spread information. These are highly informative about **current** risk conditions, but can become most extreme after prices have already fallen. Therefore a risk-off signal can occur near a market trough and be followed by a sharp rebound.

## Audit verdict

- Directional alpha claim: **NOT ESTABLISHED**.
- Risk-control / position-sizing usefulness: **SUPPORTED**.
- The six-observation SPY correlation: **EXPLORATORY ONLY; DO NOT USE AS A FORMAL RESULT**.

## Required next test

Construct a point-in-time monthly dataset, ideally 2010-2026 or longer, with:

- MRI level/regime available at each date;
- contemporaneous State Street TAA equity weight/stance;
- future 1M/3M/6M/12M global and US equity returns;
- max adverse excursion / drawdown;
- benchmark-relative portfolio outcome;
- no retrospective regime labels.

Only then estimate IC, hit rate, conditional mean return, drawdown reduction, turnover, and transaction-cost-adjusted utility.