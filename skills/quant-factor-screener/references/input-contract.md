# Input contract

Pass one candidate at a time to `scoreQuantFactorCandidate(candidate, weights)`.

| Field | Type | Unit | Rule |
|---|---|---|---|
| `pe` | number or null | multiple | Non-positive values are missing |
| `pb` | number or null | multiple | Non-positive values are missing |
| `dividendYieldPct` | number or null | percentage points | Zero is valid |
| `roe` | number or null | percentage points | Negative values remain valid |
| `performance3mPct` | number or null | percentage points | Preserve sign |
| `performance6mPct` | number or null | percentage points | Preserve sign |
| `volatilityPct` | number or null | annualized percentage points | Negative values are missing |

Optional weights: `valuation`, `qualityProxy`, `momentum`, and `lowVolatility`. Accept only finite non-negative values. The scorer normalizes weights over available factor groups.

Do not pass formatted strings such as `"12.3%"`, currency strings, placeholders, or model-estimated values.

