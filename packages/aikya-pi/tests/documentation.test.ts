import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,existsSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession} from '../src/runtime.ts';
import {hostOperation} from '../src/host.ts';
import {guardedSubmission} from '../src/editor.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native answers resolves declarative input and requires confirmation without inference',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-answers-'));
  try {
    mkdirSync(join(root,'.aikya'));writeFileSync(join(root,'.aikya/answers.json'),JSON.stringify({backend:'python',methodology:'odd',mode:'new',repository_layout:'singlerepo'}));
    const runtime=await createReadOnlySession(root,{python});
    try {
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-answers');
      const message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-answers');
      assert.ok(message,'Native answers is absent');assert.equal(message.role,'custom');
      const value=JSON.parse(message.content as string);assert.equal(value.status,'confirmation_required');
      assert.equal(value.preview.answers.methodology,'odd');assert.equal(calls,0);
      assert.equal(existsSync(join(root,'.harness')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('native docs catalogs and concrete previews never write without host confirmation',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-docs-'));
  try {
    mkdirSync(join(root,'.harness'));writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
    writeFileSync(join(root,'main.py'),'VALUE = 1\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-docs {"action":"catalog","document":"architecture"}');
      let message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-docs');
      assert.ok(message,'Native documentation catalog is absent');assert.equal(message.role,'custom');
      assert.ok(JSON.parse(message.content as string).sections['1-purpose-and-scope']);
      const data={action:'write',documents:[{document:'architecture',payload:{title:'Observed architecture',sections:{'1-purpose-and-scope':'A local module.'}}}],sources:['main.py']};
      await runtime.session.prompt('/aikya-docs '+JSON.stringify(data));
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-docs');assert.ok(message);assert.equal(message.role,'custom');
      const result=JSON.parse(message.content as string);assert.equal(result.status,'confirmation_required');
      assert.equal(result.review.documents[0].path,'aikya/docs/architecture/architecture-overview.md');
      assert.equal(existsSync(join(root,'aikya/docs')),false);assert.equal(calls,0);
      const submitted:string[]=[],blocked:string[]=[];const submit=guardedSubmission(s=>submitted.push(s),s=>blocked.push(s));
      for(const command of ['/aikya-answers','/aikya-docs','/aikya-docs-sync'])submit(command);
      assert.equal(submitted.length,3);assert.deepEqual(blocked,[]);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('native docs-sync observes no changes without creating a request or calling a model',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-docs-sync-'));
  try {
    mkdirSync(join(root,'.harness'));writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
    writeFileSync(join(root,'main.py'),'VALUE = 1\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      const session_id=runtime.session.sessionId,change_id='REQ-20261108-abcde123';
      const value=await hostOperation(root,'documentation.preview',{command:'aikya-docs-sync',input_data:{action:'baseline',change_id,sources:['main.py']},session_id},python);
      await hostOperation(root,'documentation.apply',{plan:value.plan,approved:true},python);
      let calls=0;runtime.session.agent.streamFunction=()=>{calls++;throw new Error('NO MODEL');};
      await runtime.session.prompt('/aikya-docs-sync '+JSON.stringify({action:'sync',change_id,summary:'Inspect source only.',documents:[]}));
      const message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-docs-sync');
      assert.ok(message);assert.equal(message.role,'custom');assert.equal(JSON.parse(message.content as string).status,'no_changes');
      assert.equal(existsSync(join(root,'aikya/docs')),false);assert.equal(calls,0);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('profile/documentation administration stays outside subsequent inference context and budget',async()=>{
  const {ModelRuntime}=await import('@earendil-works/pi-coding-agent');
  const {createAssistantMessageEventStream}=await import('@earendil-works/pi-ai');
  const {createControlledSession}=await import('../src/runtime.ts');
  const {RuntimeBudget}=await import('../src/usage.ts');
  const root=mkdtempSync(join(tmpdir(),'aikya-docs-context-'));
  try {
    const budget=new RuntimeBudget(root,python);await budget.configure(100,5,true);
    const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/test-auth.json'),modelsPath:null,modelsStorePath:join(root,'.aikya/pi/test-models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let calls=0;let observed='';
    models.registerProvider('fixture',{api:'fixture',apiKey:'fixture',baseUrl:'http://invalid.local',models:[{id:'fixture',name:'fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:(_model,context)=>{
        calls++;observed=JSON.stringify(context);const stream=createAssistantMessageEventStream();
        stream.push({type:'done',reason:'stop',message:{role:'assistant',content:[{type:'text',text:'Measured response'}],api:'fixture',provider:'fixture',model:'fixture',
          usage:{input:1,output:1,cacheRead:0,cacheWrite:0,totalTokens:2,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:Date.now()}});return stream;
      }});
    const runtime=await createControlledSession(root,{python,provider:'fixture',model:'fixture',modelRuntime:models});
    try {
      await runtime.session.prompt('/aikya-answers '+JSON.stringify({profile:{backend:'python',methodology:'odd',mode:'new',repository_layout:'singlerepo',notes:'ADMIN_PROFILE_SENTINEL'}}));
      mkdirSync(join(root,'.harness'));writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
      await runtime.session.prompt('/aikya-docs {"action":"catalog","document":"architecture"}');
      await runtime.session.prompt('/aikya-docs-sync');
      await runtime.session.prompt('/aikya-project '+JSON.stringify({action:'record',slug:'api',objective:'ADMIN_PROJECT_SENTINEL',modules:[{name:'api',path:'src/api',purpose:'Public API'}],files:['src/api/value.py'],acceptance:['Observable data.'],checks:['tests']}));
      await runtime.session.prompt('/aikya-scaffold');
      writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{project_type:'infrastructure',methodology:'odd',mode:'existing',infrastructure:{iac:'terraform'}}}));
      await runtime.session.prompt('/aikya-infra {"action":"generate","paths":["infra/terraform/versions.tf"]}');
      writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'python',methodology:'odd',mode:'existing'}}));
      await runtime.session.prompt('/aikya-arc-review '+JSON.stringify({action:'record',title:'ADMIN_ARC_SENTINEL',paths:['main.py'],findings:[{path:'main.py',line:1,end_line:1,quote:'VALUE = 1',kind:'observation',severity:'info',message:'A declared value.'}]}));
      await runtime.session.prompt('/aikya-bugfix '+JSON.stringify({action:'record',payload:{id:'BUG-001',title:'ADMIN_BUG_SENTINEL',sections:{summary:'Observed issue',environment:'Local project','steps-to-reproduce':'Run the regression','expected-result':'Expected value','actual-result':'Other value'}},sources:['main.py']}));
      writeFileSync(join(root,'.harness/project-profile.json'),JSON.stringify({decisions:{backend:'none',mobile:'android',mobile_framework:'flutter',methodology:'odd',mode:'existing',repository_layout:'singlerepo'}}));
      await runtime.session.prompt('/aikya-mobile-feature '+JSON.stringify({action:'create',platforms:['android'],feature_id:'selected-mobile',input_data:{title:'ADMIN_MOBILE_SENTINEL',objective:'Render screen',acceptance:['Screen renders'],facts:{understood:false,contained_risk:true,resumable_from_request_diff:true},tasks:[{id:'TASK-001',description:'Render screen',acceptance:['AC-01'],depends_on:[],files:['lib/screen.dart'],checks:['tests']}]}}));
      assert.equal(calls,0);assert.equal((await budget.status()).calls,0);
      await runtime.session.prompt('Inspect the requested source');
      assert.equal(calls,1);assert.equal((await budget.status()).recorded_tokens,2);
      assert.equal(observed.includes('ADMIN_PROFILE_SENTINEL'),false);
      assert.equal(observed.includes('ADMIN_PROJECT_SENTINEL'),false);
      for(const sentinel of ['ADMIN_ARC_SENTINEL','ADMIN_BUG_SENTINEL','ADMIN_MOBILE_SENTINEL'])assert.equal(observed.includes(sentinel),false);
      assert.equal(observed.includes('infra/terraform/versions.tf'),false);
      assert.equal(observed.includes('general-swe/foundations/architecture-overview'),false);
      assert.equal(observed.includes('input_required'),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
