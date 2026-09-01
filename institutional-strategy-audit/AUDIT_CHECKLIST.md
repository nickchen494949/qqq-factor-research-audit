# Independent Audit Checklist

Use this to challenge the research rather than confirm it.

## A. Source integrity
- [ ] Every exact return figure points to an official source, exact share class, and date.
- [ ] Net vs gross return is identified.
- [ ] Benchmark definition is exact and contemporaneous.
- [ ] Any one-off gain/litigation/security recovery is disclosed.
- [ ] Secondary sources are not used where a primary source exists.

## B. Framework-to-product mapping
- [ ] Does the product actually implement the public framework being discussed?
- [ ] If not, is it labeled only as a proxy for implementation skill?
- [ ] Are house views kept separate from fund NAVs?

## C. Position data
- [ ] Is the data daily holdings, periodic holdings, asset-class exposure, 13F, or commentary?
- [ ] Are shorts/derivatives/futures/swaps/FX missing?
- [ ] Is notional exposure being confused with capital weight?
- [ ] Is collateral/money-market exposure being mistaken for a bearish cash view?

## D. Performance logic
- [ ] Are raw CAGRs being compared only between strategies with comparable risk?
- [ ] Is benchmark-relative excess return shown where possible?
- [ ] Are volatility, Sharpe and max drawdown considered?
- [ ] Are fees and turnover considered?
- [ ] Are start/end dates cherry-picked?

## E. Point-in-time testing
- [ ] Was the signal actually public at t?
- [ ] Are later revisions/backfilled labels excluded?
- [ ] Is the future-return horizon chosen before looking at results?
- [ ] Is the sample large enough?
- [ ] Is SPY appropriate, or should the strategy be tested against global/multi-asset outcomes?

## F. Manager-specific challenges
- [ ] AQR: does trend still add value after costs and crisis-dependent payoff concentration?
- [ ] Man AHL: do independent product/share-class histories corroborate AQR without selection bias?
- [ ] State Street: does MRI improve utility after turnover/costs, not just reduce drawdown?
- [ ] Research Affiliates: do published signals add incremental alpha beyond simple value + momentum?
- [ ] Fidelity: does business-cycle regime classification have forward IC point-in-time?
- [ ] JPM/BlackRock/PIMCO: do house OW/UW changes beat naive strategic allocations after costs?
- [ ] Bridgewater: does public ALLW achieve risk balance across enough distinct regimes once history grows?
- [ ] GMO: do 7-year expected-return rankings predict realized cross-asset returns out of sample?
- [ ] Oaktree/KKR: can public credit-cycle signals be separated from security-selection/private-market alpha?
- [ ] Goldman: can tactical-tilt changes be reconstructed and benchmarked point-in-time?
- [ ] Morgan Stanley: obtain realized public GTAA record before assigning evidence weight.
- [ ] Vanguard: use strategic balanced allocation as the complexity control.

## G. Falsification tests for the final synthesis
The proposed synthesis should be rejected if any of these hold:

1. Trend adds no incremental forward information after macro/valuation inputs.
2. Credit/liquidity/volatility sizing reduces CAGR more than it improves drawdown/utility.
3. Macro-cycle labels add no OOS information beyond price trend and earnings revisions.
4. Valuation does not improve long-horizon return ranking OOS.
5. The combined model fails to beat a simple strategic allocation on risk-adjusted, cost-adjusted OOS performance.

## Decision rule

No production strategy change should be made from this repository alone. It is an evidence map and hypothesis generator. A frozen, point-in-time, out-of-sample test is required.