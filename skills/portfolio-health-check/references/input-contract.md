# Input contract

Call `analyzePortfolioHealth({ positions, totalAssetCny, cashCny })`.

Each position must provide:

| Field | Type | Meaning |
|---|---|---|
| `accountName` | string | Caller-defined account grouping |
| `symbol` | string | Instrument code |
| `name` | string | Display name |
| `assetClass` | string | Caller-defined asset category |
| `currency` | string | ISO currency code when available |
| `marketValueCny` | number | Reliable CNY-converted position value |
| `valuationMissing` | boolean | Whether the caller considers valuation unreliable |

`totalAssetCny` is the caller's authoritative total-asset denominator. `cashCny` is authoritative cash already converted to CNY.

Do not pass formatted money strings. The skill does not perform FX conversion, derive holdings from transactions, or infer missing values.

