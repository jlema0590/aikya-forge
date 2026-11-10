import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,writeFileSync,readFileSync,existsSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {WriteAuthority} from '../src/permissions.ts';
import {hostOperation} from '../src/host.ts';
import {createReadOnlySession} from '../src/runtime.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';
type Intent={change_id:string;operations:{path:string;edits:{old:string;new:string}[]}[]};

async function fixture() {
  const root=mkdtempSync(join(tmpdir(),'aikya-native-source-batch-'));
  writeFileSync(join(root,'source.py'),'VALUE = 1\n');writeFileSync(join(root,'test.py'),'print("TAP version 13\\n1..1\\nok 1 - value")\n');
  const plan=await hostOperation(root,'checks.snapshot-preview',{change_id:'batch',scope:['source.py','test.py'],session_id:'author',
    objective:'Use three',acceptance:['The value is three'],tdd_paths:['test.py'],definitions:[{name:'tests',argv:[python,'-I','-B','test.py'],
    cwd:'.',report_format:'tap',timeout_seconds:3,max_output_bytes:65536}]},python);
  await hostOperation(root,'checks.snapshot',{plan,approved:true},python);
  return {root,intent:{change_id:'batch',operations:[{path:'source.py',edits:[{old:'VALUE = 1',new:'VALUE = 3'}]}]} satisfies Intent};
}

test('source batch confirmation binds deeply copied exact edits and preserves approval boundaries',async()=>{
  const {root,intent}=await fixture();
  try {
    const authority=new WriteAuthority(root,'author',python);
    assert.equal(typeof authority.batch,'function','Native batch authority is absent');
    const declined=await authority.batch(intent,async preview=>{
      assert.equal((preview.files[0].edits as {old:string;new:string}[])[0].new,'VALUE = 3');return false;
    });
    assert.equal(declined.status,'declined');assert.equal(readFileSync(join(root,'source.py'),'utf8'),'VALUE = 1\n');
    assert.equal(existsSync(join(root,'.aikya/pi/batches')),false);
    const result=await authority.batch(intent,async preview=>{
      intent.operations[0].edits[0].new='UNAPPROVED = 9';(preview.files[0].edits as {old:string;new:string}[])[0].new='DIALOG MUTATION';return true;
    });
    assert.equal(result.status,'written');assert.equal(result.checks,'not_run');
    assert.equal(readFileSync(join(root,'source.py'),'utf8'),'VALUE = 3\n');
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('source changes during the dialog refuse the batch without overwriting user edits',async()=>{
  const {root,intent}=await fixture();
  try {
    const authority=new WriteAuthority(root,'author',python);
    assert.equal(typeof authority.batch,'function','Native batch authority is absent');
    await assert.rejects(authority.batch(intent,async()=>{
      writeFileSync(join(root,'source.py'),'OWNER = 7\n');return true;
    }));
    assert.equal(readFileSync(join(root,'source.py'),'utf8'),'OWNER = 7\n');
    assert.equal(existsSync(join(root,'.aikya/pi/batches/pending.json')),false);
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('native source-batch edit and recovery commands never write or infer without host confirmation',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-native-batch-command-'));
  try {
    writeFileSync(join(root,'source.py'),'VALUE = 1\n');writeFileSync(join(root,'test.py'),'print("TAP version 13\\n1..1\\nok 1 - value")\n');
    const runtime=await createReadOnlySession(root,{python});
    try {
      runtime.session.agent.streamFunction=()=>{throw new Error('NO MODEL');};
      const plan=await hostOperation(root,'checks.snapshot-preview',{change_id:'batch',scope:['source.py','test.py'],session_id:runtime.session.sessionId,
        objective:'Use three',acceptance:['The value is three'],tdd_paths:['test.py'],definitions:[{name:'tests',argv:[python,'-I','-B','test.py'],
        cwd:'.',report_format:'tap',timeout_seconds:3,max_output_bytes:65536}]},python);
      await hostOperation(root,'checks.snapshot',{plan,approved:true},python);
      await runtime.session.prompt('/aikya-implement '+JSON.stringify({action:'edit',change_id:'batch',operations:[{path:'source.py',edits:[{old:'VALUE = 1',new:'VALUE = 3'}]}]}));
      let message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-source-batch');
      assert.ok(message,'Native batch edit action is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'confirmation_required');
      assert.equal(readFileSync(join(root,'source.py'),'utf8'),'VALUE = 1\n');
      await runtime.session.prompt('/aikya-verify {"action":"recover-batch"}');
      message=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-verify');
      assert.ok(message,'Native batch recovery action is absent');assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'nothing_pending');
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('an actual SDK batch tool request cannot write in a headless author session',async()=>{
  const {ModelRuntime}=await import('@earendil-works/pi-coding-agent');
  const {createAssistantMessageEventStream}=await import('@earendil-works/pi-ai');
  const {createControlledSession}=await import('../src/runtime.ts');
  const {RuntimeBudget}=await import('../src/usage.ts');
  const root=mkdtempSync(join(tmpdir(),'aikya-headless-batch-tool-'));
  try {
    writeFileSync(join(root,'source.py'),'VALUE = 1\n');
    const budget=new RuntimeBudget(root,python);await budget.configure(100,1,true);
    const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/test-auth.json'),modelsPath:null,
      modelsStorePath:join(root,'.aikya/pi/test-models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let calls=0;
    models.registerProvider('fixture',{api:'fixture',apiKey:'fixture',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:10000,maxTokens:500}],
      streamSimple:()=>{
        calls++;const stream=createAssistantMessageEventStream();
        stream.push({type:'done',reason:'toolUse',message:{role:'assistant',api:'fixture',provider:'fixture',model:'fixture',
          content:[{type:'toolCall',id:'batch-request',name:'aikya_write',arguments:{change_id:'batch',operations:[{path:'source.py',edits:[{old:'VALUE = 1',new:'VALUE = 3'}]}]}}],
          usage:{input:5,output:3,cacheRead:0,cacheWrite:0,totalTokens:8,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'toolUse',timestamp:Date.now()}});
        return stream;
      }});
    const runtime=await createControlledSession(root,{python,provider:'fixture',model:'fixture',modelRuntime:models});
    try {
      await runtime.session.prompt('Propose the scoped patch');
      assert.equal(calls,1);assert.equal((await budget.status()).calls,1);
      const result=runtime.session.messages.find(m=>m.role==='toolResult');assert.ok(result);
      assert.match(JSON.stringify(result),/interactive host confirmation/);
      assert.equal(readFileSync(join(root,'source.py'),'utf8'),'VALUE = 1\n');
      assert.equal(existsSync(join(root,'.aikya/pi/batches')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
