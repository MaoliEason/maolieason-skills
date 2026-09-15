import assert from "node:assert/strict";
import test from "node:test";
import { QUANT_FACTOR_V1, scoreQuantFactorCandidate } from "../scripts/scorer.mjs";

const candidate = { pe: 8, pb: 0.8, dividendYieldPct: 6, roe: 25, performance3mPct: 30, performance6mPct: 50, volatilityPct: 10 };

test("qfs-v1 is deterministic", () => {
  assert.deepEqual(scoreQuantFactorCandidate(candidate), scoreQuantFactorCandidate(candidate));
  assert.equal(scoreQuantFactorCandidate(candidate).totalScore, 100);
  assert.equal(QUANT_FACTOR_V1.growthEnabled, false);
});

test("missing metrics are excluded and weights are normalized", () => {
  const result = scoreQuantFactorCandidate({ pe: 8, roe: 25 });
  assert.equal(result.totalScore, 100);
  assert.equal(result.completenessPct, 28.6);
  assert.deepEqual(result.missingFactors, ["momentum", "lowVolatility"]);
  assert.equal(result.effectiveWeights.valuation, 50);
});

test("one factor group is insufficient", () => {
  assert.equal(scoreQuantFactorCandidate({ performance3mPct: 10, performance6mPct: 20 }).totalScore, null);
});

test("custom weights are normalized", () => {
  const result = scoreQuantFactorCandidate({ pe: 8, pb: 0.8, dividendYieldPct: 6, roe: -5 }, { valuation: 3, qualityProxy: 1, momentum: 0, lowVolatility: 0 });
  assert.equal(result.totalScore, 75);
  assert.equal(result.effectiveWeights.valuation, 75);
});

