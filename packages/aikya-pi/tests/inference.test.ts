import assert from "node:assert/strict";
import { test } from "node:test";
const gate = await import("../src/inference.ts").catch(() => null);

test("read-only model boundary refuses every expensive operation before backend dispatch", () => {
  assert.ok(gate, "The read-only provider boundary is absent");
  // The external provider is the only double: an accidental request must fail locally.
  const operations = ["stream", "complete", "streamSimple", "completeSimple", "streamDeferred",
    "fetchDeferred", "generateImages", "classify"] as const;
  const backend = Object.fromEntries(operations.map((name) => [name, () => {
    throw new Error("Unexpected provider dispatch");
  }]));
  gate.lockInference(backend);
  for (const operation of operations) assert.throws(() => backend[operation](), /Model execution is disabled/);
});
