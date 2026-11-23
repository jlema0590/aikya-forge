import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,writeFileSync,rmSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {ModelRuntime} from '@earendil-works/pi-coding-agent';
import {createAssistantMessageEventStream,type AssistantMessage} from '@earendil-works/pi-ai';
import {createReadOnlySession,createControlledSession} from '../src/runtime.ts';
import {RuntimeBudget} from '../src/usage.ts';
import {guardedSubmission} from '../src/editor.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native doctor and quality report explicit limits without models or generated documentation',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-diagnostics-'));
  try {
    writeFileSync(join(root,'broken.py'),'def broken(:\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-doctor');
      const doctor=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-doctor');
      assert.ok(doctor,'Native doctor is absent');assert.equal(doctor.role,'custom');
      const diagnosis=JSON.parse(doctor.content as string);assert.equal(diagnosis.ready,null);
      assert.equal(diagnosis.profile.status,'unconfigured');assert.equal(diagnosis.provider.status,'disabled');
      assert.equal(diagnosis.runtime.node,process.versions.node);
      await runtime.session.prompt('/aikya-quality '+JSON.stringify({paths:['broken.py']}));
      const quality=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-quality');
      assert.ok(quality);assert.equal(quality.role,'custom');
      assert.equal(JSON.parse(quality.content as string).errors[0].code,'python_syntax');
      assert.equal(calls,0);assert.equal(existsSync(join(root,'aikya/docs')),false);
      await runtime.session.prompt('/aikya-quality');
      const help=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-quality');assert.ok(help);assert.equal(help.role,'custom');
      assert.equal(JSON.parse(help.content as string).status,'input_required');
      const submitted:string[]=[],blocked:string[]=[];
      const submit=guardedSubmission(s=>submitted.push(s),s=>blocked.push(s));
      submit('/aikya-doctor');submit('/aikya-quality {"paths":["broken.py"]}');
      assert.equal(submitted.length,2);assert.deepEqual(blocked,[]);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('diagnostics do not consume inference budget or remain in subsequent model context',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-diagnostics-context-'));
  try {
    writeFileSync(join(root,'local.py'),'pass\n');
    const budget=new RuntimeBudget(root,python);await budget.configure(100,5,true);
    const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/fixture-auth.json'),modelsPath:null,modelsStorePath:join(root,'.aikya/pi/fixture-models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let calls=0;let observed='';
    models.registerProvider('fixture',{api:'fixture',apiKey:'PRIVATE_DIAGNOSTIC_KEY',baseUrl:'http://invalid.local',models:[{id:'fixture',name:'fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:(_model,context)=>{
        calls++;observed=JSON.stringify(context);
        const stream=createAssistantMessageEventStream();
        const message:AssistantMessage={role:'assistant',content:[{type:'text',text:'Measured response'}],api:'fixture',provider:'fixture',model:'fixture',
          usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:Date.now()};
        stream.push({type:'done',reason:'stop',message});return stream;
      }});
    const runtime=await createControlledSession(root,{python,provider:'fixture',model:'fixture',modelRuntime:models});
    try {
      await runtime.session.prompt('/aikya-doctor');
      const doctor=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-doctor');assert.ok(doctor);assert.equal(doctor.role,'custom');
      const diagnosis=JSON.parse(doctor.content as string);assert.equal(diagnosis.provider.configured_auth,true);
      assert.equal(diagnosis.provider.connectivity,'not_tested');assert.equal(diagnosis.provider.status,'selected');
      assert.equal((doctor.content as string).includes('PRIVATE_DIAGNOSTIC_KEY'),false);
      await runtime.session.prompt('/aikya-quality '+JSON.stringify({paths:['local.py']}));
      assert.equal(calls,0);assert.equal((await budget.status()).calls,0);
      await runtime.session.prompt('Inspect my requested change');
      assert.equal(calls,1);assert.equal((await budget.status()).recorded_tokens,2);
      assert.equal(observed.includes('scope_revision'),false);assert.equal(observed.includes('compatibility'),false);
      assert.equal(observed.includes('/aikya-doctor'),false);assert.equal(observed.includes('PRIVATE_DIAGNOSTIC_KEY'),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
