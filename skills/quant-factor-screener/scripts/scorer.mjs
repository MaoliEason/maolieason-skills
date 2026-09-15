const DEFAULT_WEIGHTS = Object.freeze({ valuation: 0.30, qualityProxy: 0.30, momentum: 0.25, lowVolatility: 0.15 });

function finite(value) { return typeof value === "number" && Number.isFinite(value) ? value : null; }
function clamp(value, minimum = 0, maximum = 100) { return Math.min(maximum, Math.max(minimum, value)); }
function higherIsBetter(value, floor, ceiling) { const numeric = finite(value); return numeric === null ? null : clamp(((numeric - floor) / (ceiling - floor)) * 100); }
function lowerIsBetter(value, best, worst) { const numeric = finite(value); return numeric === null ? null : clamp(((worst - numeric) / (worst - best)) * 100); }
function average(values) { const available = values.filter((value) => value !== null); return available.length ? available.reduce((sum, value) => sum + value, 0) / available.length : null; }
function round(value) { return Math.round((value + Number.EPSILON) * 10) / 10; }

export function scoreQuantFactorCandidate(candidate, requestedWeights = {}) {
  const pe = finite(candidate.pe); const pb = finite(candidate.pb); const dividend = finite(candidate.dividendYieldPct);
  const roe = finite(candidate.roe); const performance3m = finite(candidate.performance3mPct);
  const performance6m = finite(candidate.performance6mPct); const volatility = finite(candidate.volatilityPct);
  const components = {
    valuation: average([pe !== null && pe > 0 ? lowerIsBetter(pe, 8, 40) : null, pb !== null && pb > 0 ? lowerIsBetter(pb, 0.8, 5) : null, dividend !== null && dividend >= 0 ? higherIsBetter(dividend, 0, 6) : null]),
    qualityProxy: roe === null ? null : higherIsBetter(roe, -5, 25),
    momentum: average([performance3m === null ? null : higherIsBetter(performance3m, -20, 30), performance6m === null ? null : higherIsBetter(performance6m, -30, 50)]),
    lowVolatility: volatility !== null && volatility >= 0 ? lowerIsBetter(volatility, 10, 50) : null,
  };
  const weights = Object.fromEntries(Object.entries(DEFAULT_WEIGHTS).map(([key, fallback]) => {
    const requested = finite(requestedWeights[key]); return [key, requested !== null && requested >= 0 ? requested : fallback];
  }));
  const weighted = Object.entries(components).filter(([key, value]) => value !== null && weights[key] > 0);
  const availableWeight = weighted.reduce((sum, [key]) => sum + weights[key], 0);
  const totalScore = weighted.length >= 2 && availableWeight > 0 ? round(weighted.reduce((sum, [key, value]) => sum + value * weights[key], 0) / availableWeight) : null;
  const expectedMetrics = [pe && pe > 0 ? pe : null, pb && pb > 0 ? pb : null, dividend, roe, performance3m, performance6m, volatility];
  const completeness = round(expectedMetrics.filter((value) => value !== null).length / expectedMetrics.length * 100);
  return {
    methodologyVersion: "qfs-v1", totalScore, completenessPct: completeness,
    confidence: totalScore === null ? "insufficient" : completeness >= 75 && weighted.length >= 3 ? "high" : "medium",
    components: Object.fromEntries(Object.entries(components).map(([key, value]) => [key, value === null ? null : round(value)])),
    missingFactors: Object.entries(components).filter(([, value]) => value === null).map(([key]) => key),
    effectiveWeights: Object.fromEntries(Object.entries(weights).map(([key, value]) => [key, components[key] === null || availableWeight === 0 ? 0 : round(value / availableWeight * 100)])),
  };
}

export const QUANT_FACTOR_V1 = Object.freeze({ methodologyVersion: "qfs-v1", defaultWeights: DEFAULT_WEIGHTS, growthEnabled: false, minimumAvailableFactorGroups: 2 });

