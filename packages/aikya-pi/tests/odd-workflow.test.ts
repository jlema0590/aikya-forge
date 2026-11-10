import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createReadOnlySession} from '../src/runtime.ts';
import {hostOperation} from '../src/host.ts';

const python=process.env.AIKYA_TEST_PYTHON??'python3';
test('native ODD prepares no dossier without UI consent and reads canonical state without inference',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-odd-'));
  try {
    const runtime=await createReadOnlySession(root,{python});
    try {
      runtime.session.agent.streamFunction=()=>{throw new Error('MODEL MUST NOT RUN');};
      const plan=await hostOperation(root,'workflow.preview',{command:'aikya-init',profile:{backend:'python',methodology:'odd',repository_layout:'singlerepo'},language:'en'},python);
      await hostOperation(root,'workflow.apply',{plan,approved:true},python);
      const input_data={title:'Local feature',objective:'Return a value',acceptance:['The value is one'],facts:{understood:false,contained_risk:true,resumable_from_request_diff:true},
        tasks:[{id:'TASK-001',description:'Return one',acceptance:['AC-01'],depends_on:[],files:['value.py','test.py'],checks:['tests']}]};
      await runtime.session.prompt('/aikya-feature '+JSON.stringify({action:'create',feature_id:'local-feature',input_data}));
      const message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-feature');
      assert.ok(message,'Native feature workflow is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'confirmation_required');
      assert.equal(existsSync(join(root,'aikya/docs/features/local-feature')),false);
      const approved=await hostOperation(root,'odd.preview',{action:'create',arguments:{feature_id:'local-feature',input_data},session_id:runtime.session.sessionId},python);
      await hostOperation(root,'odd.apply',{plan:approved,approved:true},python);
      await runtime.session.prompt('/aikya-feature {"action":"status","feature_id":"local-feature"}');
      const status=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-feature');assert.ok(status);assert.equal(status.role,'custom');
      const value=JSON.parse(status.content as string);assert.equal(value.tasks[0].status,'todo');assert.equal(value.delivery_authorized,false);
      await runtime.session.prompt('/aikya-feature {"action":"bind","feature_id":"local-feature","task_id":"TASK-001"}');
      assert.equal(existsSync(join(root,'.aikya/pi/odd-workflow.json')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
