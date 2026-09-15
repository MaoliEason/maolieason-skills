# Methodology: portfolio-health-v1

- Treat a position as valued only when `valuationMissing` is false and `marketValueCny > 0`.
- Measure valuation coverage by valued-position count divided by total-position count. Do not claim value coverage when missing values are unknown.
- Merge the same `symbol + currency` across accounts for instrument concentration.
- Use authoritative `totalAssetCny` as the denominator for instrument, account, asset-class, currency, and cash ratios.
- Keep cash out of security rankings.

Review thresholds:

| Diagnostic | Medium | High |
|---|---:|---:|
| Single instrument | 15% | 25% |
| Top three instruments | 50% | 70% |
| Cash buffer | Below 5% | — |
| Largest account, asset class, or currency | 80% when multiple groups exist | — |

Any missing valuation is a high-severity data-quality alert. Thresholds are transparent discipline prompts and are not universally suitable allocation targets.

