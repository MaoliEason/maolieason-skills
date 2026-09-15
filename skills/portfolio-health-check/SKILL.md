---
name: portfolio-health-check
description: Diagnose a supplied portfolio with deterministic valuation completeness, cross-account instrument concentration, top-three concentration, cash ratio, and account, asset-class, and currency exposures. Use when an agent or application must inspect existing holdings without fetching data, inventing missing valuations, modifying positions, or issuing trades.
---

# Portfolio Health Check

1. Accept only positions and totals supplied by the caller. Do not fetch portfolio data or reconstruct an alternative ledger.
2. Read [references/input-contract.md](references/input-contract.md) before adapting a project's position model.
3. Read [references/methodology.md](references/methodology.md) before explaining thresholds or changing the methodology.
4. Call `analyzePortfolioHealth` from `scripts/analyze.mjs`.
5. Aggregate the same `symbol + currency` across accounts before measuring single-instrument concentration.
6. Exclude missing or invalid valuations from monetary exposure and report the reduced count-based valuation coverage.
7. Return the method version, status, exposures, alerts, completeness, and totals. Preserve the source input unchanged.
8. Present alerts as review prompts, never automatic allocation or trading instructions.

The script performs no network access, environment reads, filesystem writes, trades, or source-data mutations.

