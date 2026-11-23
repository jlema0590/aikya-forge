import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession} from '../src/runtime.ts';
import {guardedSubmission} from '../src/editor.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native bootstrap commands plan locally and require native confirmation for effects',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-bootstrap-'));
  try {
    mkdirSync(join(root,'.harness'));const profile=join(root,'.harness/project-profile.json');
    writeFileSync(profile,JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing',repository_layout:'singlerepo'}}));
    const runtime=await createReadOnlySession(root,{python});
    try {
      for(const command of ['aikya-project','aikya-infra','aikya-scaffold'])assert.equal(runtime.session.extensionRunner.getRegisteredCommands().filter(c=>c.name===command).length,1);
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      const project={action:'record',slug:'api-boundary',objective:'ADMIN_PROJECT_SENTINEL',modules:[{name:'api',path:'src/api',purpose:'Public API'}],files:['src/api/value.py'],acceptance:['Returns expected data.'],checks:['tests']};
      await runtime.session.prompt('/aikya-project '+JSON.stringify(project));
      let message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-project');
      assert.ok(message,'Native project command is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'confirmation_required');assert.equal(existsSync(join(root,'aikya/docs')),false);
      await runtime.session.prompt('/aikya-scaffold');
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-scaffold');assert.ok(message);assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'existing_project');
      writeFileSync(profile,JSON.stringify({decisions:{project_type:'infrastructure',methodology:'odd',mode:'existing',infrastructure:{iac:'terraform'}}}));
      await runtime.session.prompt('/aikya-infra {"action":"generate","paths":["infra/terraform/versions.tf"]}');
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-infra');assert.ok(message);assert.equal(message.role,'custom');
      const value=JSON.parse(message.content as string);assert.equal(value.status,'confirmation_required');
      assert.equal(value.review.files[0].path,'infra/terraform/versions.tf');assert.equal(existsSync(join(root,'infra')),false);assert.equal(calls,0);
      const submitted:string[]=[],blocked:string[]=[];const submit=guardedSubmission(s=>submitted.push(s),s=>blocked.push(s));
      for(const command of ['/aikya-project','/aikya-infra','/aikya-scaffold'])submit(command);
      assert.equal(submitted.length,3);assert.deepEqual(blocked,[]);
      assert.deepEqual(runtime.session.getActiveToolNames(),['aikya_status','aikya_context']);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
