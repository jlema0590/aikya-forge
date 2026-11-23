import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { ModelRuntime } from '@earendil-works/pi-coding-agent';
import { createControlledSession } from '../src/runtime.ts';
import { RuntimeBudget } from '../src/usage.ts';

test('local model catalog is bounded and paginated without credential disclosure or provider calls',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-catalog-'));
  try {
    const budget=new RuntimeBudget(root,process.env.AIKYA_TEST_PYTHON);await budget.configure(100,5,true);
    const models=await ModelRuntime.create({authPath:join(root,'auth.json'),modelsPath:null,
      modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    models.registerProvider('fixture',{api:'fixture',apiKey:'PRIVATE_CATALOG_FIXTURE',baseUrl:'http://invalid.local',
      models:Array.from({length:51},(_,i)=>({id:'m'+String(i).padStart(3,'0'),name:'Catalog '+i,reasoning:false,input:['text' as const],
        cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:1000,maxTokens:50})),
      streamSimple:()=>{throw new Error('Provider dispatch is forbidden for a catalog query');}});
    const result=await createControlledSession(root,{python:process.env.AIKYA_TEST_PYTHON,provider:'fixture',model:'m000',modelRuntime:models});
    try {
      await result.session.prompt('/aikya-models {"provider":"fixture","offset":20}');
      const message=result.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-models');
      assert.ok(message);assert.equal(message.role,'custom');
      assert.equal((message.content as string).includes('PRIVATE_CATALOG_FIXTURE'),false);
      const value=JSON.parse(message.content as string);
      assert.equal(value.models.length,20);assert.equal(value.models[0].id,'m020');
      assert.equal(value.total,51);assert.equal(value.next,40);assert.equal((await budget.status()).calls,0);
      const messages=result.session.messages.filter(m=>m.role==='custom'&&m.customType==='aikya-models').length;
      await result.session.prompt('/aikya-models {"provider":"fixture","offset":-1}');
      assert.equal(result.session.messages.filter(m=>m.role==='custom'&&m.customType==='aikya-models').length,messages);
      assert.equal((await budget.status()).calls,0);
    } finally {await result.close();}
  } finally {rmSync(root,{recursive:true,force:true});}
});
