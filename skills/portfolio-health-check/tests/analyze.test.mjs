import assert from "node:assert/strict";
import test from "node:test";
import { analyzePortfolioHealth } from "../scripts/analyze.mjs";

const positions = [
  { accountName: "Account A", symbol: "AAA", name: "Company A", assetClass: "Equity", currency: "CNY", marketValueCny: 200, valuationMissing: false },
  { accountName: "Account B", symbol: "AAA", name: "Company A", assetClass: "Equity", currency: "CNY", marketValueCny: 100, valuationMissing: false },
  { accountName: "Account A", symbol: "BBB", name: "Fund B", assetClass: "Fund", currency: "USD", marketValueCny: 150, valuationMissing: false },
  { accountName: "Account A", symbol: "CCC", name: "Missing C", assetClass: "Equity", currency: "CNY", marketValueCny: 0, valuationMissing: true },
];

test("aggregates an instrument across accounts without mutation", () => {
  const original = structuredClone(positions);
  const result = analyzePortfolioHealth({ positions, totalAssetCny: 600, cashCny: 150 });
  assert.equal(result.exposures.instruments[0].valueCny, 300);
  assert.equal(result.maxPositionRatio, 0.5);
  assert.deepEqual(positions, original);
});

test("derives exposures and reports missing valuation", () => {
  const result = analyzePortfolioHealth({ positions, totalAssetCny: 600, cashCny: 150 });
  assert.deepEqual(result.exposures.accounts.map((item) => [item.key, item.valueCny]), [["Account A", 350], ["Account B", 100]]);
  assert.equal(result.missingValuationCount, 1);
  assert.equal(result.valuationCoverage, 0.75);
  assert.equal(result.alerts[0].code, "VALUATION_MISSING");
});

test("returns a safe insufficient result for an empty portfolio", () => {
  const result = analyzePortfolioHealth({ positions: [], totalAssetCny: 0, cashCny: 0 });
  assert.equal(result.status, "insufficient");
  assert.equal(result.maxPositionRatio, 0);
});
