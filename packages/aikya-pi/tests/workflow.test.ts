import assert from "node:assert/strict";
import { mkdtempSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
import { createReadOnlySession } from "../src/runtime.ts";

test('Pi onboarding previews a real project plan and refuses writes without an interactive confirmation',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-workflow-'));
  try {
    const {session,close}=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});
    try {
      session.agent.streamFunction=()=>{throw new Error('MODEL MUST NOT RUN');};
      await session.prompt('/aikya-init {"profile":{"backend":"python","methodology":"sdd","repository_layout":"singlerepo"},"language":"en"}');
      const message=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-init');
      assert.ok(message);assert.equal(message.role,'custom');
      const result=JSON.parse(message.content as string);
      assert.equal(result.status,'confirmation_required');
      assert.ok(result.preview.operations.some((op:{path:string})=>op.path==='aikya/docs/overview.md'));
      assert.equal(existsSync(join(root,'.harness/project-profile.json')),false);
      assert.equal(existsSync(join(root,'.claude')),false);
      await session.prompt('/aikya-specify {"input_data":{}}');
      const spec=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-specify');
      assert.ok(spec,'Native SDD command is absent');
      assert.equal(spec.role,'custom');
      assert.equal(JSON.parse(spec.content as string).status,'confirmation_required');
    } finally {await close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
