# Official Nasdaq Anchor Discovery Audit

## Verdict

**BLOCK — INSUFFICIENT ELIGIBLE SAME-SERIES ANCHORS**

The audit found **zero** new eligible observations. The official anchor set therefore remains at **6**, below the frozen minimum of **8**. The QQQ point-in-time earnings-yield proxy must not be rerun or described as validated against this target yet.

## What was proved

### Verified

- The frozen eligibility contract was copied into this packet and hashed before classification.
- 6,435 timestamped CDX records across three Nasdaq document prefixes were frozen.
- The 2023–2026 filename screen generated 99 keyword candidate URL rows, including every Nasdaq-100 URL named `Quarterly Commentary` in those listings.
- Every distinct archived Nasdaq-100 quarterly-commentary PDF byte variant in that bounded set was inspected.
- Exact `index-weighted EPS` plus `YoY` observations found in those commentaries were all duplicate corroborations of already-frozen 2024-Q1, 2024-Q3, 2024-Q4, or 2025-Q1 anchors.
- Q3 2025 `+35%` is only labelled generic earnings growth.
- Q2/Q3/Q4 2025 updates use partial-reporting, non-GAAP, preliminary, or net-income definitions and therefore fail the frozen target definition.
- The 2026 retrospective and monthly scorecards fail the frozen source-type/definition rule.

### Not inferred

- `+35% earnings growth` was not relabelled `index-weighted EPS`.
- `18% net income growth` was not relabelled EPS.
- Multiple Nasdaq product documents repeating one quarter were not counted as multiple observations.
- The 2026 retrospective Q2 2023 `+17.3%` was not merged with the contemporaneous `-9%` series.

### Still unknown

- Whether Nasdaq published two other qualifying commentaries outside the three archived document prefixes or outside available archived captures.
- Nasdaq's proprietary formula, constituent treatment, adjustment policy, and data vintage for the official series.
- Whether the research proxy would pass its statistical gates if a valid eight-anchor set were eventually obtained.

## Decision arithmetic

```text
Frozen official anchors                 6
+ newly eligible anchors                0
                                       ──
Confirmed same-series anchors           6

Required minimum                        8
Shortfall                               2
                                       ──
Validation gate                    BLOCKED
```

## Why the tempting new numbers do not count

```text
Nasdaq document
      ↓
Is it contemporaneous quarterly commentary?
      ├─ No  → exclude
      └─ Yes
           ↓
Does it explicitly say “index-weighted EPS” and “YoY”?
      ├─ No  → exclude; do not reinterpret
      └─ Yes
           ↓
Is it a new quarter rather than a duplicate product copy?
      ├─ No  → corroboration only
      └─ Yes → new eligible anchor

This run reached the last box zero times.
```

## Evidence map

- Frozen contract copies: `frozen_contract/`
- Raw archived bytes and CDX listings: `raw/`
- Candidate and exclusion ledger: `candidates_and_exclusions.csv`
- URL-screen inventory: `derived/cdx_candidate_urls.csv`
- PDF extraction inventory: `derived/pdf_inventory.json`
- Extracted text and rendered pages: `derived/text/` and `derived/rendered/`
- Source URLs and hashes: `source_metadata.json`
- Machine verdict: `verdict.json`
- Aggregate hash manifests: `raw_manifest.json` and `packet_manifest.json`

## Permitted next actions

1. Request or locate two additional timestamped Nasdaq quarterly commentaries that explicitly print `index-weighted EPS` and `YoY` for new quarters.
2. If Nasdaq supplies a formal methodology reconciling the newer retrospective series to the older commentary series, amend the contract in a new version before any rerun.
3. Until then, keep the proxy validation status blocked. Do not lower the eight-anchor gate after seeing candidate numbers.
