import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession} from '../src/runtime.ts';
import {guardedSubmission} from '../src/editor.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native engineering commands expose anchored read-only evidence and require confirmation for records',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-engineering-native-'));
  try {
    mkdirSync(join(root,'.harness'));const profile=join(root,'.harness/project-profile.json');
    writeFileSync(profile,JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
    writeFileSync(join(root,'service.py'),'class Service:\n    pass\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-arc-review '+JSON.stringify({action:'record',title:'Selected architecture',paths:['service.py'],findings:[{path:'service.py',line:1,end_line:1,quote:'class Service:',kind:'observation',severity:'info',message:'A class declaration.'}]}));
      let message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-arc-review');
      assert.ok(message,'Native architecture workflow is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'confirmation_required');
      await runtime.session.prompt('/aikya-bugfix '+JSON.stringify({action:'record',payload:{id:'BUG-001',title:'Observed issue',sections:{summary:'Observed issue',environment:'Local project','steps-to-reproduce':'Select the regression','expected-result':'One value','actual-result':'Another value'}},sources:['service.py']}));
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-bugfix');assert.ok(message);assert.equal(message.role,'custom');
      const bug=JSON.parse(message.content as string);assert.equal(bug.status,'confirmation_required');assert.equal(bug.review.bug_evidence.status,'not_reproduced');
      writeFileSync(profile,JSON.stringify({decisions:{backend:'none',mobile:'android',mobile_framework:'flutter',methodology:'odd',mode:'existing',repository_layout:'singlerepo'}}));
      await runtime.session.prompt('/aikya-mobile-feature '+JSON.stringify({action:'plan',platforms:['android'],files:['lib/screen.dart']}));
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-mobile-feature');assert.ok(message);assert.equal(message.role,'custom');
      const mobile=JSON.parse(message.content as string);assert.equal(mobile.plan,null);assert.equal(mobile.review.mobile.build,'not_run');assert.equal(mobile.review.mobile.acceptance,'not_verified');
      assert.equal(existsSync(join(root,'aikya/docs')),false);assert.equal(calls,0);
      const commands=['aikya-arc-review','aikya-bugfix','aikya-mobile-feature'];
      for(const name of commands)assert.equal(runtime.session.extensionRunner.getRegisteredCommands().filter(c=>c.name===name).length,1);
      const passed:string[]=[],blocked:string[]=[];const submit=guardedSubmission(s=>passed.push(s),s=>blocked.push(s));
      for(const name of commands)submit('/'+name);assert.equal(passed.length,3);assert.deepEqual(blocked,[]);
      assert.deepEqual(runtime.session.getActiveToolNames(),['aikya_status','aikya_context']);
    } finally {await runtime.close();}
    const reviewer=await createReadOnlySession(root,{python,role:'reviewer',reviewCandidate:'a'.repeat(64),reviewChange:'candidate'});
    try {for(const name of ['aikya-arc-review','aikya-bugfix','aikya-mobile-feature'])assert.equal(reviewer.session.extensionRunner.getRegisteredCommands().filter(c=>c.name===name).length,0);}
    finally {await reviewer.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
