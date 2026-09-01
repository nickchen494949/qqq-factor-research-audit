# Methodology

## 1. Unit of analysis

The audit separates four objects that must not be conflated:

1. **House view / research framework** — e.g. Fidelity business cycle, BlackRock BII tactical view, State Street MRI.
2. **Investable strategy/product** — e.g. AQR Managed Futures, BlackRock Global Allocation, JPMorgan Global Allocation, ALLW.
3. **Regulatory holdings disclosure** — e.g. 13F, N-PORT.
4. **Actual complete portfolio** — usually not public for hedge funds and institutional mandates.

A product return is only evidence for that product. It is not automatically evidence that the firm's public macro framework has forecasting alpha.

## 2. Evidence hierarchy

Preferred order:

1. Official fund page / official factsheet / SEC filing.
2. Official institutional research paper.
3. Official manager commentary.
4. Secondary databases only when primary source was unavailable.

Every claim in `MANAGER_AUDIT.csv` is tagged by evidence strength.

## 3. Return comparisons

Cross-manager raw CAGR comparisons are not valid unless risk, leverage, benchmark, currency, share class, fee treatment and asset mix are comparable.

Therefore this audit emphasizes:

- fund vs its stated benchmark;
- long-horizon excess return where available;
- realized volatility / Sharpe when explicitly published;
- whether the result is net or gross;
- whether one-off gains distorted the period.

## 4. Position transparency

Transparency grades:

- `HIGH`: daily or frequent full fund holdings / exposure tables.
- `MEDIUM`: periodic holdings or asset-class exposure, but not full derivative book.
- `LOW`: 13F-only, selective commentary, or private fund.

Important: Form 13F excludes short positions and does not reveal the complete futures/swaps/FX/derivative book. A manager can look long in 13F while being hedged or net short elsewhere.

## 5. Point-in-time discipline

For signal tests, only information publicly available at the observation date should be used. Later revisions, retrospective classifications, or backfilled regime labels must not leak into the signal.

The State Street mini-test is explicitly exploratory because the sample is tiny and some observations mix global and US-equity views.

## 6. What counts as validation

A framework gets stronger evidence only when we can connect:

`public signal at t -> actual position at t -> subsequent return/risk outcome`

If one link is missing, verdict is downgraded to `PARTIAL` or `UNVERIFIED`.

## 7. Core interpretation rule

The final model recommendation is intentionally modular:

- fundamentals/cycle = prior/context;
- valuation = long-horizon expected return;
- trend = market confirmation;
- credit/liquidity/volatility = risk sizing;
- strategic balanced allocation = control.

This is a synthesis, not a claim that any one institution uses this exact architecture.