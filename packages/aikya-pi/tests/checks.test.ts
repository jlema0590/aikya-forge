import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,writeFileSync,existsSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { createReadOnlySession } from '../src/runtime.ts';
import { hostOperation } from '../src/host.ts';

const python=process.env.AIKYA_TEST_PYTHON??'python3';
test('native tests and verification use real frozen state and never execute without host UI consent',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-checks-'));
  try {
    writeFileSync(join(root,'source.py'),'VALUE = 1\n');
    writeFileSync(join(root,'test.py'),'print("TAP version 13")\nprint("1..1")\nprint("ok 1 - local")\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      runtime.session.agent.streamFunction=()=>{throw new Error('MODEL MUST NOT RUN');};
      const args={change_id:'check-1',scope:['source.py','test.py'],objective:'Return the expected value',acceptance:['A source value exists'],tdd_paths:['test.py'],
        definitions:[{name:'tests',argv:[python,'-I','-B','test.py'],cwd:'.',report_format:'tap',timeout_seconds:3,max_output_bytes:65536}]};
      await runtime.session.prompt('/aikya-tests '+JSON.stringify({action:'snapshot',...args}));
      const preview=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-tests');
      assert.ok(preview,'Native test command is absent');assert.equal(preview.role,'custom');
      assert.equal(JSON.parse(preview.content as string).status,'confirmation_required');
      assert.equal(existsSync(join(root,'aikya/docs/validation/check-1')),false);
      const plan=await hostOperation(root,'checks.snapshot-preview',{...args,session_id:runtime.session.sessionId},python);
      await hostOperation(root,'checks.snapshot',{plan,approved:true},python);
      await runtime.session.prompt('/aikya-tests {"action":"run","change_id":"check-1","check":"tests"}');
      const run=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-tests');assert.ok(run);assert.equal(run.role,'custom');
      assert.equal(JSON.parse(run.content as string).status,'confirmation_required');
      assert.equal(existsSync(join(root,'aikya/docs/validation/check-1/checks')),false);
      await runtime.session.prompt('/aikya-verify {"change_id":"check-1"}');
      const status=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-verify');assert.ok(status);assert.equal(status.role,'custom');
      assert.equal(JSON.parse(status.content as string).status,'pending_checks');
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
