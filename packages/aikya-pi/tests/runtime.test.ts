import assert from "node:assert/strict";
import { mkdtempSync, rmSync, mkdirSync, symlinkSync, realpathSync, writeFileSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

const python = process.env.AIKYA_TEST_PYTHON ?? "python3";
const runtime = await import("../src/session.ts").catch(() => null);
const bridge = await import("../src/bridge.ts").catch(() => null);

test("bridge reads a project with spaces without a shell or initialization", async () => {
  assert.ok(bridge, "Python bridge transport is not implemented");
  const root = mkdtempSync(join(tmpdir(), "aikya project "));
  try {
    assert.deepEqual(await bridge.callBridge(root, "status", { python }), {
      configured: false, methodology: null, project_type: null,
    });
    await assert.rejects(bridge.callBridge(root, "bash" as never, { python }));
    await assert.rejects(bridge.callBridge(root, "status", {python, signal: AbortSignal.abort()}));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("session files remain in each project and resume the same local lineage", async () => {
  assert.ok(runtime, "Project-local Pi sessions are not implemented");
  const root = mkdtempSync(join(tmpdir(), "aikya-session-"));
  try {
    const first = runtime.projectSession(root, false);
    first.appendMessage({role: "user", content: "Local test conversation", timestamp: 1});
    first.appendCustomEntry("aikya-test", { observed: true });
    const filename = first.getSessionFile();
    assert.ok(filename?.startsWith(join(realpathSync(root), ".aikya", "pi", "sessions")));
    const resumed = runtime.projectSession(root, true);
    assert.equal(resumed.getSessionId(), first.getSessionId());
    const otherRoot = join(root, "other");
    mkdirSync(otherRoot);
    assert.notEqual(runtime.projectSession(otherRoot, true).getSessionId(), first.getSessionId());
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("symlinked session directory cannot redirect transcripts", () => {
  assert.ok(runtime, "Project-local Pi sessions are not implemented");
  const root = mkdtempSync(join(tmpdir(), "aikya-link-"));
  try {
    mkdirSync(join(root, "outside"));
    symlinkSync(join(root, "outside"), join(root, ".aikya"), "dir");
    assert.throws(() => runtime.projectSession(root, false), /symlink/i);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("context transport reads only explicit paths without initializing project state", async () => {
  assert.ok(bridge);
  const root = mkdtempSync(join(tmpdir(), "aikya-context-"));
  try {
    writeFileSync(join(root, "user.ts"), "export class UserService {}\n");
    const packet = await bridge.callBridge(root, "context", {python, arguments: {
      paths: ["user.ts"], query: "UserService", max_chars: 1000,
    }}) as {context: {text: string}[]};
    assert.match(packet.context[0].text, /UserService/);
    assert.deepEqual(readdirSync(root), ["user.ts"]);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("project Python modules cannot shadow the trusted service package", async () => {
  assert.ok(bridge);
  const root = mkdtempSync(join(tmpdir(), "aikya-shadow-"));
  try {
    writeFileSync(join(root, "aikya.py"), 'from pathlib import Path\nPath("IMPORT_HIJACKED").write_text("bad")\n');
    const result = await bridge.callBridge(root, "status", {python});
    assert.deepEqual(result, {configured: false, methodology: null, project_type: null});
    assert.deepEqual(readdirSync(root), ["aikya.py"]);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("transport rejects malformed or cross-project service responses", () => {
  assert.ok(bridge);
  assert.equal(typeof bridge.decodeReply, "function", "Response contract decoder is absent");
  const envelope = {schema: 1, id: "request-1", project: "/project", ok: true, result: {configured: false}};
  assert.deepEqual(bridge.decodeReply(JSON.stringify(envelope), "request-1", "/project"), {configured: false});
  for (const changed of [{result: []}, {schema: true}, {project: "/other"}, {id: "other-request"}, {ok: false}]) {
    assert.throws(() => bridge.decodeReply(JSON.stringify({...envelope, ...changed}), "request-1", "/project"));
  }
  assert.throws(() => bridge.decodeReply("SECRET_INVALID_INPUT", "request-1", "/project"),
    (error: unknown) => error instanceof Error && !error.message.includes("SECRET_INVALID_INPUT"));
});
