import assert from "node:assert/strict";
import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
import { createReadOnlySession } from "../src/runtime.ts";

test("local memory and token commands use project state without model dispatch", async () => {
  const root=mkdtempSync(join(tmpdir(),"aikya-local-commands-"));
  try {
    const {session,close}=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});
    try {
      session.agent.streamFunction=()=>{throw new Error("MODEL MUST NOT RUN");};
      await session.prompt('/aikya-memory {"query":"decision","max_chars":512}');
      const memory=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-memory');
      assert.ok(memory); assert.equal(memory.role,'custom');
      assert.deepEqual(JSON.parse(memory.content as string).notes,[]);
      await session.prompt('/aikya-tokens');
      const usage=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-tokens');
      assert.ok(usage); assert.equal(usage.role,'custom');
      assert.equal(JSON.parse(usage.content as string).status,'unconfigured');
      assert.equal(existsSync(join(root,'aikya/docs/memory')),false);
      assert.equal(existsSync(join(root,'.aikya/pi/usage.json')),false);
    } finally {await close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
