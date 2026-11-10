import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
import { ModelRuntime } from "@earendil-works/pi-coding-agent";
import { createAssistantMessageEventStream, type AssistantMessage } from "@earendil-works/pi-ai";
import { RuntimeBudget } from "../src/usage.ts";
import { measurePrompt } from "../src/prompt-budget.ts";
import * as sdk from "../src/runtime.ts";

test("controlled session dispatches through real Pi and durable budget without granting shell access", async () => {
  assert.equal(typeof sdk.createControlledSession,'function','Controlled Aikya runtime is absent');
  const root=mkdtempSync(join(tmpdir(),'aikya-controlled-'));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON); await budget.configure(10,5,true);
    const models=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let requests=0;
    models.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'HarnessCatalogOnly',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:(_model,context)=>{
        assert.equal(JSON.stringify(context).includes('HarnessCatalogOnly'),false,'Administrative catalog leaked into model context');
        const size=measurePrompt(context);assert.ok(size.tools<4000);assert.ok(size.total<10000);
        requests++; const stream=createAssistantMessageEventStream();
        const message:AssistantMessage={role:'assistant',content:[{type:'text',text:'A measured response'}],api:'fixture',provider:'fixture',model:'fixture',
          usage:{input:7,output:4,cacheRead:0,cacheWrite:0,totalTokens:11,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:Date.now()};
        stream.push({type:'done',reason:'stop',message}); return stream;
      }});
    const {session,close}=await sdk.createControlledSession(root,{python:process.env.AIKYA_TEST_PYTHON,provider:'fixture',model:'fixture',modelRuntime:models});
    try {
      assert.equal(session.getActiveToolNames().includes('aikya_check'),true,'Controlled check tool is absent');
      await session.prompt('/aikya-models fixture');assert.equal(requests,0);
      const catalog=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-models');
      assert.ok(catalog,'Native local model catalog is absent');
      assert.equal(catalog.role,'custom');
      assert.equal(JSON.parse(catalog.content as string).models[0].id,'fixture');
      await session.prompt('/aikya-phase plan');assert.equal(requests,0);
      await session.prompt('Implement the requested behavior');
      assert.equal(requests,1); assert.equal((await budget.status()).recorded_tokens,11);
      assert.equal(((await budget.status()) as unknown as {groups:{phase:string}[]}).groups[0].phase,'plan');
      await session.prompt('Try another request');
      assert.equal(requests,1);
      assert.equal(session.getActiveToolNames().includes('bash'),false);
      assert.equal(session.getActiveToolNames().includes('aikya_write'),true);
    } finally {await close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('native onboarding attributes the next measured request to planning without treating its preview as initialization',async()=>{
  const {fixtureModels}=await import('./task-run-fixture.ts');
  const {existsSync}=await import('node:fs');
  const root=mkdtempSync(join(tmpdir(),'aikya-native-phase-'));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON);await budget.configure(100,5,true);
    const modelRuntime=await fixtureModels(root,()=>[{type:'text',text:'Planning remains unapproved.'}]);
    const runtime=await sdk.createControlledSession(root,{python:process.env.AIKYA_TEST_PYTHON,provider:'fixture',model:'fixture',modelRuntime});
    try {
      await runtime.session.prompt('/aikya-init '+JSON.stringify({profile:{backend:'python',methodology:'odd',repository_layout:'singlerepo'},language:'en'}));
      assert.equal(existsSync(join(root,'.harness')),false);
      await runtime.session.prompt('Inspect the bounded planning request');
      const status=await budget.status() as unknown as {groups:{phase:string}[]};
      assert.equal(status.groups[0].phase,'plan');assert.equal(existsSync(join(root,'.harness')),false);
    } finally {await runtime.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
