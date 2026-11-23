import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createReadOnlySession } from '../src/runtime.ts';

test('native migration previews a real legacy profile and refuses headless mutation',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-pi-migrate-'));
  try {
    mkdirSync(join(root,'.harness'));
    const profile=JSON.stringify({_generated_by:'claude-dev-harness-interactive',schema_version:1,
      decisions:{backend:'python',methodology:'odd'}});
    writeFileSync(join(root,'.harness/project-profile.json'),profile);
    const result=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});
    try {
      result.session.agent.streamFunction=()=>{throw new Error('MODEL MUST NOT RUN');};
      await result.session.prompt('/aikya-migrate {"methodology":"odd"}');
      const message=result.session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-migrate');
      assert.ok(message,'Native migration command is absent');assert.equal(message.role,'custom');
      const value=JSON.parse(message.content as string);assert.equal(value.status,'confirmation_required');
      assert.equal(value.preview.methodology,'odd');
      assert.equal(readFileSync(join(root,'.harness/project-profile.json'),'utf8'),profile);
      assert.equal(existsSync(join(root,'.aikya/pi/migrations')),false);
    } finally {await result.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
