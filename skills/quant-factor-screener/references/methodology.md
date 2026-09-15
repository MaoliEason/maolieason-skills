# Methodology: qfs-v1

The score is deterministic and bounded from 0 to 100.

| Group | Metrics | Default weight | Direction and v1 bounds |
|---|---|---:|---|
| Valuation | PE, PB, dividend yield | 30% | PE 8–40 lower is better; PB 0.8–5 lower is better; yield 0–6 higher is better |
| Quality proxy | ROE | 30% | −5–25 higher is better |
| Momentum | 3-month and 6-month performance | 25% | −20–30 and −30–50 higher is better |
| Low volatility | Annualized volatility | 15% | 10–50 lower is better |

Average available metrics inside each group. Exclude a missing group and renormalize its weight across available positively weighted groups. Require at least two positively weighted, available groups before returning a total score.

Completeness is the available count among the seven expected raw metrics. High confidence requires at least 75% completeness and three available weighted groups. The thresholds are transparent scoring boundaries, not empirically optimized return forecasts.

