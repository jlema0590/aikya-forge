import assert from "node:assert/strict";
import { test } from "node:test";
const module = await import("../src/editor.ts").catch(() => null);

test("preview editor blocks native mutation commands before the Pi dispatcher", async () => {
  assert.ok(module, "Preview editor gate is absent");
  const native: string[] = [], blocked: string[] = [];
  const dispatch = module.guardedSubmission((text: string) => { native.push(text); }, (text: string) => { blocked.push(text); });
  for (const text of ["/login", "/export report.html", "/import foreign.jsonl", "/compact", "/settings", "!touch marker", "/aikya-status-extra"]) {
    await dispatch(text);
  }
  assert.equal(native.length, 0);
  assert.equal(blocked.length, 7);
  for (const text of ["/aikya-status", '/aikya-context {"query":"A","paths":["a.py"],"max_chars":512}', "/quit", "implement this"]) {
    await dispatch(text);
  }
  assert.equal(native.length, 4);
});
