import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync, readFileSync, symlinkSync, existsSync, realpathSync, lstatSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { projectSession } from "../src/session.ts";
const state = await import("../src/terminal-state.ts").catch(() => null);
const sdk = await import("../src/runtime.ts");

test("terminal startup protects project-local state without replacing ignore rules", () => {
  assert.ok(state, "Terminal state preparation is absent");
  const root = mkdtempSync(join(tmpdir(), "aikya-terminal-"));
  try {
    const before = "# Team rules\ncustom/\n";
    writeFileSync(join(root, ".gitignore"), before);
    const first = state.prepareTerminalState(root);
    assert.equal(first.agentDir, join(realpathSync(root), ".aikya", "pi", "agent"));
    const value = readFileSync(join(root, ".gitignore"), "utf8");
    assert.ok(value.startsWith(before));
    assert.equal(value.split("\n").filter((line) => line === ".aikya/pi/").length, 1);
    state.prepareTerminalState(root);
    assert.equal(readFileSync(join(root, ".gitignore"), "utf8"), value);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("launcher help and noninteractive refusal never initialize project state", () => {
  const entry = new URL("../src/launcher.ts", import.meta.url);
  const root = mkdtempSync(join(tmpdir(), "aikya-no-tty-"));
  try {
    const helped = spawnSync(process.execPath, ["--experimental-strip-types", fileURLToPath(entry), "--help"], {cwd: root, encoding: "utf8"});
    assert.equal(helped.status, 0, helped.stderr);
    assert.match(helped.stdout, /read-only/i);
    const result = spawnSync(process.execPath, ["--experimental-strip-types", fileURLToPath(entry), "--target", root], {encoding: "utf8"});
    assert.equal(result.status, 2);
    assert.match(result.stderr, /interactive terminal/i);
    assert.equal(existsSync(join(root, ".aikya")), false);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("tracked terminal state is refused and later negations cannot expose new state", () => {
  assert.ok(state);
  const root = mkdtempSync(join(tmpdir(), "aikya-git-state-"));
  const git = (...args: string[]) => {
    const result = spawnSync("git", ["-c", "core.fsmonitor=false", ...args], {cwd: root, encoding: "utf8"});
    assert.equal(result.status, 0, result.stderr); return result.stdout;
  };
  try {
    git("init", "-q");
    writeFileSync(join(root, ".gitignore"), ".aikya/pi/\n!.aikya/pi/\n");
    state.prepareTerminalState(root);
    git("check-ignore", ".aikya/pi/agent/auth.json");
    git("add", "-f", ".aikya/pi"); // Empty directories are not tracked.
    writeFileSync(join(root, ".aikya/pi/agent/auth.json"), "{}\n");
    git("add", "-f", ".aikya/pi/agent/auth.json");
    const before = readFileSync(join(root, ".gitignore"));
    assert.throws(() => state.prepareTerminalState(root), /tracked/i);
    assert.deepEqual(readFileSync(join(root, ".gitignore")), before);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("dangling ignore links and invalid encodings are preserved and refused", () => {
  assert.ok(state);
  const root = mkdtempSync(join(tmpdir(), "aikya-ignore-invalid-"));
  try {
    const ignore = join(root, ".gitignore");
    symlinkSync(join(root, "missing"), ignore);
    assert.throws(() => state.prepareTerminalState(root), /symlink/i);
    assert.equal(lstatSync(ignore).isSymbolicLink(), true);
    rmSync(ignore);
    const original = Buffer.from([0xff, 0x00, 0x61]); writeFileSync(ignore, original);
    assert.throws(() => state.prepareTerminalState(root));
    assert.deepEqual(readFileSync(ignore), original);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("a linked ignore file cannot redirect terminal writes", () => {
  assert.ok(state);
  const root = mkdtempSync(join(tmpdir(), "aikya-ignore-link-"));
  try {
    writeFileSync(join(root, "outside"), "Team file\n");
    symlinkSync(join(root, "outside"), join(root, ".gitignore"));
    assert.throws(() => state.prepareTerminalState(root), /symlink/i);
    assert.equal(readFileSync(join(root, "outside"), "utf8"), "Team file\n");
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("real SDK runtime replacement retains read-only gates and project identity", async () => {
  assert.equal(typeof sdk.createReadOnlyRuntime, "function", "Pi terminal runtime factory is absent");
  const root = mkdtempSync(join(tmpdir(), "aikya-runtime-"));
  try {
    const runtime = await sdk.createReadOnlyRuntime(root, {python: process.env.AIKYA_TEST_PYTHON});
    try {
      await runtime.session.bindExtensions({});
      const first = runtime.session.sessionId;
      await runtime.newSession();
      await runtime.session.bindExtensions({});
      assert.notEqual(runtime.session.sessionId, first);
      await runtime.session.prompt("Implement a feature");
      assert.equal(runtime.session.messages.filter((m) => m.role === "assistant").length, 0);
      assert.ok(runtime.session.messages.some((m) => m.role === "custom" && m.customType === "aikya-read-only"));
      const switched = await runtime.switchSession(join(root, "foreign.jsonl"));
      assert.equal(switched.cancelled, true);
      assert.equal(existsSync(join(root, "foreign.jsonl")), false);
    } finally { await runtime.dispose(); }
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("session resumption rejects linked transcript files", () => {
  const root = mkdtempSync(join(tmpdir(), "aikya-transcript-link-"));
  try {
    projectSession(root, false);
    writeFileSync(join(root, "outside.jsonl"), "{}\n");
    symlinkSync(join(root, "outside.jsonl"), join(root, ".aikya/pi/sessions/foreign.jsonl"));
    assert.throws(() => projectSession(root, true), /symlink/i);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("read-only runtime entry cannot silently accept provider execution options", async () => {
  const root = mkdtempSync(join(tmpdir(), "aikya-readonly-options-"));
  try {
    await assert.rejects(sdk.createReadOnlyRuntime(root, {provider: "fixture", model: "fixture"}), /read-only/i);
  } finally {rmSync(root, {recursive:true,force:true});}
});
