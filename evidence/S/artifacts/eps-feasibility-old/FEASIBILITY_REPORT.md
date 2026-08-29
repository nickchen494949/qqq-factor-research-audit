# True Point-in-Time QQQ EPS Feasibility (Local-Only Audit)

Date: 2026-08-26  
Scope: read-only inspection of `[LOCAL_TMP_PROJECT]` and `[LOCAL_QQQ_RISK_PROJECT]`  
Production files changed: none  
Network used: none

## Bottom line

**A true constituent-weighted, point-in-time QQQ EPS growth/revision series cannot be constructed from the currently local files from 2009 onward.**

The local machine has usable QQQ holdings/weight snapshots, but it does not have constituent-level EPS actuals or analyst-estimate vintages. The two local earnings datasets are market-level aggregates, not QQQ constituent panels.

## What is locally available

### 1. QQQ point-in-time holdings and weights

Files:

- `[LOCAL_TMP_PROJECT]/normalized/qqq_snapshots.csv`
- `[LOCAL_TMP_PROJECT]/normalized/qqq_holdings.csv`
- `[LOCAL_TMP_PROJECT]/raw/sec_qqq/`

Verified coverage:

- 38 SEC snapshots, report dates 2008-09-30 through 2026-03-31.
- 11 legacy N-30B-2 snapshots: annual September reports from 2008 through 2018.
- 27 N-PORT snapshots: every quarter from 2019Q3 through 2026Q1.
- Legacy filing lag: 82 to 122 days, median 107 days.
- N-PORT filing lag: 50 to 62 days, median 58 days.
- Legacy market-value weights are reconstructable from the raw schedules.
- N-PORT contains explicit percentage weights.

Important limitation:

- From 2009 through 2018, only one holding snapshot per year is local. Quarterly QQQ composition is missing for three quarters each year.
- A report's weights are not public until its filing date. Using them on the earlier report date would be lookahead.

### 2. Local identifier mapping

Files:

- `normalized/cusip_ticker_map.csv`
- `normalized/intersection_cusip_map_additions.csv`
- `normalized/legacy_name_ticker_map.csv`
- `normalized/intersection_legacy_map_additions.csv`

Verified explicit mapping inventory:

- 32 CUSIP mappings.
- 77 legacy issuer-name mappings.
- 58 unique tickers across both mapping sets.

Coverage of current explicit maps:

- Modern N-PORT snapshots: about 18%-20% of holdings by count, but 58.9%-69.3% by portfolio weight.
- Legacy snapshots, after only punctuation/case normalization: about 12%-21% by count and 38.8%-66.3% by weight.

Interpretation:

- The maps cover many mega-cap names but not the complete index.
- A top-holdings proxy might be possible after adding earnings data, but it would not be a full QQQ earnings series.

### 3. S&P 500 aggregate trailing earnings growth

File:

- `[LOCAL_QQQ_RISK_PROJECT]/market_data/multpl_earnings_growth.csv`

Verified coverage:

- 63 consecutive quarterly observations, 2010Q1 through 2025Q3.
- No missing quarter ends.

Limitations:

- It is S&P 500 aggregate earnings growth, not QQQ.
- There are no constituent rows.
- There are no observation/publication timestamps or vintage history in the file.
- A 45-day availability lag can prevent obvious lookahead, but cannot make a current-vintage series truly point-in-time.

### 4. LSEG I/B/E/S aggregate forward EPS/revisions

File:

- `[LOCAL_QQQ_RISK_PROJECT]/research/challengers/macro_observer_2026_08/strategy_comparison/lseg_backtest_results_v3.csv`

Verified coverage:

- 400 aggregate observations, 2016-10-14 through 2026-07-03.
- `forward_eps`: 400/400 populated.
- `eps_mom_26w`: 374/400 populated (93.5%); usable only after its warm-up, roughly 2017 onward.
- `revision_ratio` and `revision_breadth`: 246/400 populated (61.5%).
- No constituent identifier, ticker, CUSIP, company EPS, or company weight columns.

Universe assessment:

- The `price` field ranges from 2,126 to 7,483, which matches the scale of the S&P 500 index, not QQQ.
- The local README calls it LSEG I/B/E/S but does not provide constituent-level provenance or an extraction script.
- Therefore it is an aggregate market earnings proxy and cannot be reweighted to QQQ. Its exact point-in-time provenance cannot be independently reconstructed from the examined package.

## Why the true QQQ series is impossible locally

The required join is:

```text
as-of date
   -> exact QQQ members and weights known on that date
   -> permanent security identifier history
   -> each company's EPS actual/forecast known on that date
   -> corporate-action-safe aggregation
   -> QQQ EPS growth and revision signal
```

The local machine currently has the first item partially, the second item partially, and no constituent-level dataset for the third item.

In particular, analyst revisions cannot be reconstructed from SEC filings. Revisions require archived analyst-consensus vintages. SEC filings can support lagged realized earnings, not consensus revision history.

## Correct aggregation rule

Do not average raw EPS dollars across companies; one company's per-share unit is not comparable with another's.

A practical revision signal is:

```text
QQQ forward-EPS revision_t
  ~= sum over constituents(
       lagged QQQ weight_i,t
       * change in log(forward EPS_i,t)
     )
```

Another valid signal is weight-adjusted revision breadth:

```text
sum(weight of upward-revised companies)
  - sum(weight of downward-revised companies)
```

Both require company-level estimate vintages and as-of timestamps.

## Honest proxy choices with current local data

### Proxy A — S&P aggregate trailing EPS growth

- Period: 2010Q1-2025Q3.
- Use a conservative publication lag (for example 45 days).
- Label it **S&P aggregate realized-earnings proxy**, not QQQ EPS.
- Suitable only as a macro earnings-state challenger.

### Proxy B — LSEG aggregate forward EPS momentum/revision breadth

- Period: roughly 2017 onward after 26-week warm-up.
- Label it **aggregate market forward-EPS proxy**, not constituent-weighted QQQ EPS.
- Better than trailing EPS for timeliness, but shorter history and incomplete revision fields.
- Do not claim 2009 coverage.

### Proxy C — Dynamic QQQ composition/exposure features

- Use concentration, top-10 weight, effective number of names, and later sector weights.
- These account for the fact that macro shocks affect different QQQ structures differently.
- They are composition/risk-exposure variables, not earnings.

### Proxy D — Partial mega-cap realized-earnings basket

- Not buildable from the current local package because constituent earnings are absent.
- If SEC company-facts are later acquired, the present mapping covers roughly 40%-69% of QQQ weight depending on era.
- Must be labeled partial and selection-biased until identifier coverage is near complete.

## What must be added for a defensible full build

Minimum additional inputs:

1. Complete permanent identifier mapping: QQQ holding -> CUSIP/FIGI/PERMID -> company/security through ticker changes and mergers.
2. Exact point-in-time QQQ weights at the chosen signal frequency; annual-only pre-2019 local snapshots are insufficient for quarterly truth.
3. For realized EPS: SEC company-facts plus original filing timestamps and restatement handling.
4. For forward EPS/revisions: analyst-consensus estimate vintages by company and observation date (LSEG/FactSet/Bloomberg or equivalent licensed archive).
5. Corporate-action handling, dual share-class rules, negative-EPS rules, and survivorship-safe delisted-company history.
6. A frozen aggregation contract before seeing results.

## Recommended decision

- Do not call the current model's earnings input “QQQ EPS.”
- Keep the completed v1 as an explicitly labeled proxy experiment.
- If a free-data continuation is desired, build lagged constituent realized earnings from SEC; this still will not produce analyst revisions.
- If actual forward revisions are the thesis, obtain a Nasdaq-100/QQQ aggregate forward-EPS series or constituent-level consensus-vintage archive. That is the shortest defensible path.

## Plain-language flow

```text
Local QQQ holdings/weights        Local earnings files
38 snapshots                      S&P aggregate only
annual before 2019                no company rows
quarterly from 2019Q3             no full revision vintages
          \                         /
           \                       /
            -> cannot build true constituent-weighted QQQ EPS
                         |
                         +-> honest now: market EPS proxy + QQQ structure
                         |
                         +-> true later: full identifiers + company EPS vintages
```

One-sentence conclusion: **本地资料足够测“市场盈利代理 × QQQ结构”，但不够声称已经建立真正的历史QQQ成分加权EPS或盈利修正序列。**
