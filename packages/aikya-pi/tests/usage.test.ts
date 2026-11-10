import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
const module = await import("../src/usage.ts").catch(() => null);
const context = {session: "author", role: "author", phase: "implement", provider: "fixture", model: "fixture"};

test("budget wraps real host accounting and stops the next external call at exhaustion", async () => {
  assert.ok(module, "Pi usage admission is absent");
  const root = mkdtempSync(join(tmpdir(), "aikya-budget-"));
  try {
    const budget = new module.RuntimeBudget(root, process.env.AIKYA_TEST_PYTHON);
    await budget.configure(10, 2, true);
    let dispatches = 0;
    const external = async () => { dispatches++; return {value: "reply", usage: {input: 7, output: 4, cacheRead: 0, cacheWrite: 0}}; };
    assert.equal(await budget.run(context, external), "reply");
    await assert.rejects(budget.run({...context, session: "resumed"}, external));
    assert.equal(dispatches, 1);
    assert.equal((await budget.status()).recorded_tokens, 11);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("unknown external usage survives restart and prevents hidden retries", async () => {
  assert.ok(module);
  const root = mkdtempSync(join(tmpdir(), "aikya-budget-unknown-"));
  try {
    const budget = new module.RuntimeBudget(root, process.env.AIKYA_TEST_PYTHON);
    await budget.configure(100, 3, true);
    await assert.rejects(budget.run(context, async () => {throw new Error("connection lost");}));
    const resumed = new module.RuntimeBudget(root, process.env.AIKYA_TEST_PYTHON);
    assert.equal((await resumed.status()).status, "unknown_usage");
    await assert.rejects(resumed.run(context, async () => {throw new Error("MUST NOT DISPATCH");}), /runtime/i);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("quota refresh preserves marked stale observations without inventing percentages", async () => {
  assert.ok(module);
  const cache = new module.QuotaCache();
  const snapshot = {provider: "fixture", fetchedAt: 1000, windows: [{label: "5h", seconds: 18000, usedPercent: 25, resetAt: 9000}]};
  await cache.refresh("fixture", async () => snapshot);
  assert.equal(cache.view("fixture", 1001).stale, false);
  await cache.refresh("fixture", async () => {throw new Error("offline");});
  assert.equal(cache.view("fixture", 1001).stale, true);
  assert.equal(cache.view("fixture", 1001).snapshot?.windows[0].usedPercent, 25);
  assert.equal(cache.view("absent", 1001).snapshot, null);
  await cache.refresh("bad", async () => ({...snapshot, provider: "bad", windows: [{...snapshot.windows[0], usedPercent: NaN}]}));
  assert.equal(cache.view("bad", 1001).snapshot, null);
});
