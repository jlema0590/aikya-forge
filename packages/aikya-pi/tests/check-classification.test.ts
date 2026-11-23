import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession} from '../src/runtime.ts';
import {hostOperation} from '../src/host.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native non-test snapshot preserves classification, confirmation and observed process counts',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-classified-check-'));
  try {
    writeFileSync(join(root,'main.tf'),'# local infrastructure\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      runtime.session.agent.streamFunction=()=>{throw new Error('NO MODEL');};
      const args={change_id:'classified',scope:['main.tf'],objective:'Validate infrastructure',acceptance:['Local validator succeeds'],
        change_kind:'infrastructure',not_applicable:'Local configuration validation; no application behavior',
        definitions:[{name:'validate',argv:[python,'-I','-B','-c','print("validated")'],cwd:'.',report_format:'process',timeout_seconds:3,max_output_bytes:65536}]};
      await runtime.session.prompt('/aikya-tests '+JSON.stringify({action:'snapshot',...args}));
      const message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-tests');
      assert.ok(message);assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'confirmation_required');
      assert.equal(existsSync(join(root,'aikya/docs/validation/classified')),false);
      const session_id=runtime.session.sessionId;
      const plan=await hostOperation(root,'checks.snapshot-preview',{...args,session_id},python);
      await hostOperation(root,'checks.snapshot',{plan,approved:true},python);
      const execution=await hostOperation(root,'checks.run-preview',{change_id:'classified',check:'validate',session_id,run_id:'observed'},python);
      const result=await hostOperation(root,'checks.run',{plan:execution,approved:true},python);
      assert.equal(result.status,'completed');assert.equal(result.counts,null);
      await runtime.session.prompt('/aikya-verify {"change_id":"classified"}');
      const status=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-verify');
      assert.ok(status);assert.equal(status.role,'custom');
      assert.equal(JSON.parse(status.content as string).status,'review_required');
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('native documentation recovery inspects an empty project without inference or effects',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-document-recovery-'));
  try {
    mkdirSync(join(root,'.harness'));writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
    const runtime=await createReadOnlySession(root,{python});
    try {
      runtime.session.agent.streamFunction=()=>{throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-docs {"action":"recover"}');
      const message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-docs');
      assert.ok(message,'Recovery command is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'nothing_pending');
      assert.equal(existsSync(join(root,'aikya/docs')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
