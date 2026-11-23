import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,writeFileSync,existsSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ModelRuntime } from '@earendil-works/pi-coding-agent';
import { createAssistantMessageEventStream,type AssistantMessage } from '@earendil-works/pi-ai';
import { createControlledSession } from '../src/runtime.ts';
import { RuntimeBudget } from '../src/usage.ts';
import { hostOperation } from '../src/host.ts';

test('an actual model tool request cannot execute an otherwise valid frozen check in headless mode',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-check-tool-')),python=process.env.AIKYA_TEST_PYTHON??'python3';
  try {
    writeFileSync(join(root,'source.py'),'VALUE=1\n');writeFileSync(join(root,'test.py'),'print("TAP version 13")\nprint("1..1")\nprint("ok 1 - local")\n');
    const budget=new RuntimeBudget(root,python);await budget.configure(100,1,true);
    const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/agent/fixture-auth.json'),modelsPath:null,
      modelsStorePath:join(root,'.aikya/pi/agent/fixture-models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let dispatched=0;
    models.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:10000,maxTokens:500}],
      streamSimple:()=>{
        dispatched++;const stream=createAssistantMessageEventStream();
        const message:AssistantMessage={role:'assistant',api:'fixture',provider:'fixture',model:'fixture',
          content:[{type:'toolCall',id:'check-request',name:'aikya_check',arguments:{change_id:'tool-check',check:'tests'}}],
          usage:{input:10,output:3,cacheRead:0,cacheWrite:0,totalTokens:13,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'toolUse',timestamp:Date.now()};
        stream.push({type:'done',reason:'toolUse',message});return stream;
      }});
    const runtime=await createControlledSession(root,{python,provider:'fixture',model:'fixture',modelRuntime:models});
    try {
      const plan=await hostOperation(root,'checks.snapshot-preview',{change_id:'tool-check',scope:['source.py','test.py'],session_id:runtime.session.sessionId,
        objective:'Verify the source value',acceptance:['A value exists'],tdd_paths:['test.py'],
        definitions:[{name:'tests',argv:[python,'-I','-B','test.py'],cwd:'.',report_format:'tap',timeout_seconds:3,max_output_bytes:65536}]},python);
      await hostOperation(root,'checks.snapshot',{plan,approved:true},python);
      await runtime.session.prompt('Run the frozen check');
      assert.equal(dispatched,1);assert.equal((await budget.status()).calls,1);
      const result=runtime.session.messages.find(m=>m.role==='toolResult');assert.ok(result);
      assert.match(JSON.stringify(result),/interactive host/i);
      assert.equal(existsSync(join(root,'aikya/docs/validation/tool-check/checks')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
