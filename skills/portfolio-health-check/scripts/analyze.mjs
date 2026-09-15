const VERSION = "portfolio-health-v1";

function finitePositive(value) { const number = Number(value); return Number.isFinite(number) && number > 0 ? number : 0; }
function ratio(value, denominator) { return denominator > 0 ? value / denominator : 0; }
function aggregate(positions, keyOf, labelOf, denominator) {
  const groups = new Map();
  for (const position of positions) {
    const key = keyOf(position) || "UNKNOWN";
    const current = groups.get(key) || { key, label: labelOf(position) || key, valueCny: 0 };
    current.valueCny += finitePositive(position.marketValueCny); groups.set(key, current);
  }
  return [...groups.values()].map((item) => ({ ...item, ratio: ratio(item.valueCny, denominator) })).sort((a, b) => b.valueCny - a.valueCny || a.key.localeCompare(b.key));
}
function alert(code, severity, title, detail) { return { code, severity, title, detail }; }

export function analyzePortfolioHealth({ positions = [], totalAssetCny = 0, cashCny = 0 } = {}) {
  const source = Array.isArray(positions) ? positions : []; const denominator = finitePositive(totalAssetCny);
  const valuedPositions = source.filter((position) => !position?.valuationMissing && finitePositive(position?.marketValueCny) > 0);
  const missingValuationCount = source.length - valuedPositions.length;
  const valuedPositionCny = valuedPositions.reduce((sum, position) => sum + finitePositive(position.marketValueCny), 0);
  const instruments = aggregate(valuedPositions, (position) => `${position.symbol || "UNKNOWN"}|${position.currency || "UNKNOWN"}`, (position) => position.name || position.symbol || "Unknown instrument", denominator);
  const accounts = aggregate(valuedPositions, (position) => position.accountName, (position) => position.accountName, denominator);
  const assetClasses = aggregate(valuedPositions, (position) => position.assetClass, (position) => position.assetClass, denominator);
  const currencies = aggregate(valuedPositions, (position) => position.currency, (position) => position.currency, denominator);
  const cashRatio = ratio(Math.max(0, Number(cashCny) || 0), denominator);
  const maxPositionRatio = instruments[0]?.ratio || 0; const topThreeRatio = instruments.slice(0, 3).reduce((sum, item) => sum + item.ratio, 0);
  const valuationCoverage = source.length ? valuedPositions.length / source.length : 1; const alerts = [];
  if (!denominator || !source.length) alerts.push(alert("INSUFFICIENT_DATA", "info", "Insufficient portfolio data", "Supply valued positions and an authoritative total before interpreting concentration."));
  else {
    if (maxPositionRatio >= 0.25) alerts.push(alert("SINGLE_POSITION", "high", "High single-instrument concentration", `${instruments[0].label} is ${(maxPositionRatio * 100).toFixed(1)}% of total assets.`));
    else if (maxPositionRatio >= 0.15) alerts.push(alert("SINGLE_POSITION", "medium", "Review single-instrument concentration", `${instruments[0].label} is ${(maxPositionRatio * 100).toFixed(1)}% of total assets.`));
    if (topThreeRatio >= 0.7) alerts.push(alert("TOP_THREE", "high", "High top-three concentration", `The top three instruments are ${(topThreeRatio * 100).toFixed(1)}% of total assets.`));
    else if (topThreeRatio >= 0.5) alerts.push(alert("TOP_THREE", "medium", "Review top-three concentration", `The top three instruments are ${(topThreeRatio * 100).toFixed(1)}% of total assets.`));
    if (cashRatio < 0.05) alerts.push(alert("CASH_BUFFER", "medium", "Low cash buffer", `Cash is ${(cashRatio * 100).toFixed(1)}% of total assets; this does not by itself require selling.`));
    if ((accounts[0]?.ratio || 0) >= 0.8 && accounts.length > 1) alerts.push(alert("ACCOUNT_CONCENTRATION", "medium", "High account concentration", `${accounts[0].label} is ${(accounts[0].ratio * 100).toFixed(1)}% of total assets.`));
    if ((assetClasses[0]?.ratio || 0) >= 0.8 && assetClasses.length > 1) alerts.push(alert("ASSET_CLASS_CONCENTRATION", "medium", "High asset-class concentration", `${assetClasses[0].label} is ${(assetClasses[0].ratio * 100).toFixed(1)}% of total assets.`));
    if ((currencies[0]?.ratio || 0) >= 0.8 && currencies.length > 1) alerts.push(alert("CURRENCY_CONCENTRATION", "medium", "High currency concentration", `${currencies[0].label} is ${(currencies[0].ratio * 100).toFixed(1)}% of total assets.`));
  }
  if (missingValuationCount > 0) alerts.unshift(alert("VALUATION_MISSING", "high", "Incomplete valuation data", `${missingValuationCount} positions were excluded; count coverage is ${(valuationCoverage * 100).toFixed(0)}%.`));
  return { methodologyVersion: VERSION, status: !denominator || !source.length ? "insufficient" : alerts.some((item) => item.severity === "high") ? "attention" : "normal", totalAssetCny: denominator, valuedPositionCny, cashCny: Math.max(0, Number(cashCny) || 0), positionCount: source.length, valuedPositionCount: valuedPositions.length, missingValuationCount, valuationCoverage, cashRatio, maxPositionRatio, topThreeRatio, exposures: { instruments, accounts, assetClasses, currencies }, alerts };
}

