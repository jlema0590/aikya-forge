import assert from "node:assert/strict";
import { mkdtempSync, rmSync, mkdirSync, writeFileSync, existsSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

const sdk = await import("../src/runtime.ts").catch(() => null);
test("real Pi command reaches Python without prompting a model", async () => {
  assert.ok(sdk, "Aikya Pi SDK runtime is not implemented");
  const root = mkdtempSync(join(tmpdir(), "aikya-sdk-"));
  try {
    const extensions = join(root, ".pi", "extensions");
    mkdirSync(extensions, {recursive: true});
    const marker = join(root, "untrusted-extension-loaded");
    writeFileSync(join(extensions, "escape.ts"), `import {writeFileSync} from "node:fs"; writeFileSync(${JSON.stringify(marker)}, "bad"); export default () => {};`);
    const {session,close} = await sdk.createReadOnlySession(root, {python: process.env.AIKYA_TEST_PYTHON});
    try {
      await session.prompt("/aikya-status");
      const message = session.messages.find((m) => m.role === "custom" && m.customType === "aikya-status");
      assert.ok(message);
      assert.equal(message.role, "custom");
      assert.equal(typeof message.content, "string");
      assert.equal(JSON.parse(message.content as string).configured, false);
      assert.equal(session.messages.filter((m) => m.role === "assistant").length, 0);
      assert.deepEqual(session.getActiveToolNames(), ["aikya_status", "aikya_context"]);
      assert.equal(existsSync(marker), false);
    } finally { await close(); }
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("Pi context command returns a bounded source packet without model execution", async () => {
  assert.ok(sdk);
  const root = mkdtempSync(join(tmpdir(), "aikya-sdk-context-"));
  writeFileSync(join(root, "service.java"), "class ScopedService {}\n");
  try {
    const {session,close} = await sdk.createReadOnlySession(root, {python: process.env.AIKYA_TEST_PYTHON});
    try {
      await session.prompt('/aikya-context {"paths":["service.java"],"query":"ScopedService","max_chars":1000}');
      const message = session.messages.find((m) => m.role === "custom" && m.customType === "aikya-context");
      assert.ok(message);
      assert.equal(message.role, "custom");
      const packet = JSON.parse(message.content as string);
      assert.match(packet.context[0].text, /ScopedService/);
      assert.equal(session.messages.filter((m) => m.role === "assistant").length, 0);
    } finally { await close(); }
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("agent configuration cannot be redirected outside the project", async () => {
  assert.ok(sdk);
  const root = mkdtempSync(join(tmpdir(), "aikya-agent-link-"));
  try {
    mkdirSync(join(root, ".aikya", "pi"), {recursive: true});
    mkdirSync(join(root, "outside"));
    symlinkSync(join(root, "outside"), join(root, ".aikya", "pi", "agent"), "dir");
    await assert.rejects(sdk.createReadOnlySession(root), /symlink/i);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("read-only sessions consume ordinary prompts and block native shell shortcuts", async () => {
  assert.ok(sdk);
  const root = mkdtempSync(join(tmpdir(), "aikya-readonly-"));
  try {
    const {session,close} = await sdk.createReadOnlySession(root, {python: process.env.AIKYA_TEST_PYTHON});
    try {
      session.agent.streamFunction = () => { throw new Error("Unexpected inference attempt"); };
      await session.prompt("Implement a change");
      assert.ok(session.messages.find((m) => m.role === "custom" && m.customType === "aikya-read-only"));
      const handled = await session.extensionRunner.emitUserBash({type: "user_bash",
        command: "echo bad > SHELL_SIDE_EFFECT", excludeFromContext: false, cwd: root});
      assert.equal(handled?.result?.exitCode, 1);
      assert.equal(existsSync(join(root, "SHELL_SIDE_EFFECT")), false);
      assert.equal(session.messages.filter((m) => m.role === "assistant").length, 0);
    } finally { await close(); }
  } finally { rmSync(root, {recursive: true, force: true}); }
});
