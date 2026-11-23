import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
import { ModelRuntime } from "@earendil-works/pi-coding-agent";
import { createAssistantMessageEventStream, type AssistantMessage } from "@earendil-works/pi-ai";
import { RuntimeBudget } from "../src/usage.ts";
const gate = await import("../src/budgeted-inference.ts").catch(() => null);

test("real Pi model runtime is budgeted once before its external provider and durably records completion", async () => {
  assert.ok(gate,"Budgeted Pi inference boundary is absent");
  const root=mkdtempSync(join(tmpdir(),"aikya-inference-gate-"));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON); await budget.configure(10,5,true);
    const runtime=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let dispatched=0;
    runtime.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:()=>{
        dispatched++;
        const stream=createAssistantMessageEventStream();
        const message:AssistantMessage={role:'assistant',content:[{type:'text',text:'local transport fixture'}],api:'fixture',provider:'fixture',model:'fixture',
          usage:{input:7,output:4,cacheRead:0,cacheWrite:0,totalTokens:11,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:Date.now()};
        stream.push({type:'done',reason:'stop',message}); return stream;
      }});
    gate.installBudgetedInference(runtime,budget,()=>({session:'author',role:'author',phase:'implement',provider:'fixture',model:'fixture'}));
    const model=runtime.getModel('fixture','fixture'); assert.ok(model);
    const oversized=await runtime.completeSimple(model,{messages:[],systemPrompt:'x'.repeat(40000)});
    assert.equal(oversized.stopReason,'error');assert.equal(dispatched,0);
    assert.equal((await budget.status()).calls,0);
    const first=await runtime.completeSimple(model,{messages:[]});
    assert.equal(first.stopReason,'stop'); assert.equal(dispatched,1);
    assert.equal((await budget.status()).recorded_tokens,11);
    const second=await runtime.completeSimple(model,{messages:[]});
    assert.equal(second.stopReason,'error'); assert.equal(dispatched,1);
    assert.equal((await budget.status()).calls,1);
    await assert.rejects(runtime.generateImages({} as never,{} as never));
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('a runtime cannot silently acquire two independent budget wrappers',async()=>{
  assert.ok(gate);
  const root=mkdtempSync(join(tmpdir(),'aikya-double-gate-'));
  try {
    const runtime=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON);
    const context=()=>({session:'author',role:'author',phase:'implement',provider:'fixture',model:'fixture'});
    gate.installBudgetedInference(runtime,budget,context);
    assert.throws(()=>gate.installBudgetedInference(runtime,budget,context),/already/i);
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('missing configured authentication is refused before reserving chargeable usage',async()=>{
  assert.ok(gate);
  const root=mkdtempSync(join(tmpdir(),'aikya-no-auth-'));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON);await budget.configure(100,5,true);
    const runtime=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let dispatched=0;
    runtime.registerProvider('aikya-no-auth-fixture',{api:'fixture',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:()=>{dispatched++;throw new Error('No external dispatch expected');}});
    gate.installBudgetedInference(runtime,budget,()=>({session:'author',role:'author',phase:'implement',provider:'aikya-no-auth-fixture',model:'fixture'}));
    const model=runtime.getModel('aikya-no-auth-fixture','fixture');assert.ok(model);
    const result=await runtime.completeSimple(model,{messages:[]});assert.equal(result.stopReason,'error');
    assert.equal(dispatched,0);assert.equal((await budget.status()).calls,0);
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('an asynchronous native task gate settles before any provider dispatch or charge reservation',async()=>{
  assert.ok(gate);
  const root=mkdtempSync(join(tmpdir(),'aikya-async-task-gate-'));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON);await budget.configure(100,5,true);
    const runtime=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let dispatched=0;
    runtime.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50}],
      streamSimple:()=>{dispatched++;throw new Error('No dispatch after refused task checkpoint');}});
    gate.installBudgetedInference(runtime,budget,()=>({session:'author',role:'author',phase:'implement',provider:'fixture',model:'fixture'}),undefined,
      async()=>{await new Promise(resolve=>setTimeout(resolve,10));throw new Error('Original task deadline exhausted');});
    const model=runtime.getModel('fixture','fixture');assert.ok(model);
    const result=await runtime.completeSimple(model,{messages:[]});
    assert.equal(result.stopReason,'error');assert.match(result.errorMessage??'',/deadline/);
    assert.equal(dispatched,0);assert.equal((await budget.status()).calls,0);
  } finally {rmSync(root,{recursive:true,force:true});}
});
