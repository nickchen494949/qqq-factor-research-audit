# Correction Log vs Prior Chat

This file records where the audit repository intentionally narrows, corrects, or withholds claims made earlier in conversation.

## 1. Exact performance figures

Several prior-chat responses quoted exact 1Y/3Y/5Y/10Y returns for multiple managers. In this audit pass, **exact figures are retained only when the official product page/document can be pinned cleanly to the relevant share class and date**.

Where the web surface produced ambiguous or conflicting snapshots (notably some Man AHL, Goldman Sachs, KKR, Fidelity, and other fund-class variants), the repository now uses qualitative/relative conclusions and marks the exact number for re-verification instead of pretending precision.

## 2. House view vs product return

Prior chat sometimes moved too quickly from a firm's public framework to the return of a same-firm product. This is corrected.

Examples:
- Fidelity business-cycle framework != Fidelity Asset Manager 60% NAV.
- BlackRock BII overweight/underweight calls != BlackRock Global Allocation Fund.
- JPM house asset-allocation views != JPMorgan Global Allocation Fund.
- Morgan Stanley GTAA public framework cannot be validated without a complete realized public track record.

These products may be useful proxies for implementation skill, but they do not prove that the public research signal itself has alpha.

## 3. State Street MRI

Prior chat reported a crude correlation from six observations. This remains documented only as an exploratory curiosity. It is **not** a formal statistical result.

The stronger and more defensible conclusion is that MRI is useful as a risk-regime / sizing framework; State Street's own research shows risk/drawdown improvement without a clear long-run CAGR advantage versus simple rebalancing.

## 4. Bridgewater / ALLW

ALLW provides unusually high transparency and is useful for observing risk-balanced implementation. However, its public ETF history begins only in 2025, so no strong long-run performance conclusion is warranted.

All Weather should not be described as an entry/exit timing model.

## 5. GMO

GMO's valuation framework remains potentially useful for long-horizon expected returns. Recent strong product results must be interpreted with gross-vs-net and disclosed one-off-event caveats. Short-horizon timing conclusions are not supported.

## 6. 13F

Any implication that 13F equals a hedge fund's true portfolio is rejected. 13F omits shorts and many derivatives, futures, swaps, FX and non-covered securities.

## 7. "Most institutions fail"

The earlier wording was too broad. The defensible statement is narrower:

> In the public multi-asset products examined here, many managers do not show persistent benchmark-relative macro-timing alpha over long horizons. This does not prove the institutions themselves or their private mandates have no skill.

## 8. Final synthesis

The repository's recommended architecture is a **model synthesis**, not an empirical proof that the combination will outperform:

fundamentals/cycle prior -> valuation -> trend confirmation -> credit/liquidity/volatility risk sizing -> position.

It requires an out-of-sample backtest before production use.