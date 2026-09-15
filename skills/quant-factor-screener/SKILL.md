---
name: quant-factor-screener
description: Score a supplied list of equity candidates with deterministic valuation, ROE quality-proxy, medium-term momentum, and low-volatility factors. Use when an agent or application must rank already-retrieved candidates, explain component scores, normalize custom non-negative weights, and handle missing metrics without fetching data or modifying the source list.
---

# Quant Factor Screener

1. Accept only candidates already supplied by the caller. Do not fetch, replace, or silently enrich the candidate universe.
2. Read [references/input-contract.md](references/input-contract.md) before mapping fields.
3. Read [references/methodology.md](references/methodology.md) when explaining scores, changing weights, or comparing methodology versions.
4. Call `scoreQuantFactorCandidate` from `scripts/scorer.mjs` for every candidate.
5. Preserve the caller's original order when scores tie. Sort only a derived copy when ranking is requested.
6. Keep missing metrics missing. Do not convert missing values to zero or infer them with a language model.
7. Report `methodologyVersion`, total score, component scores, completeness, effective weights, confidence, and missing factor groups.
8. Describe the result as a rules-based analytical ranking, never as a return forecast or investment recommendation.

The script performs no network access, environment reads, filesystem writes, trades, or source-data mutations.

