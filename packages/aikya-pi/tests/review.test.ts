import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
import { ModelRuntime } from "@earendil-works/pi-coding-agent";
import { createAssistantMessageEventStream, type AssistantMessage } from "@earendil-works/pi-ai";
const adapter = await import("../src/review.ts").catch(() => null);

test("independent SDK reviewer is admitted only after real checks and measured reviewer execution",async()=>{
  assert.ok(adapter,'Pi reviewer adapter is absent');
  const root=mkdtempSync(join(tmpdir(),'aikya-review-sdk-'));
  try {
    writeFileSync(join(root,'source.py'),'VALUE = 1\n');
    const python=process.env.AIKYA_TEST_PYTHON??'python3';
    execFileSync(python,['-I','-B','-c',
      'import sys;from pathlib import Path;from aikya.review.candidates import freeze_candidate,store_candidate;from aikya.review.executor import run_check,check_binding;from aikya.routing.pi_usage import configure;'+
      'r=Path(sys.argv[1]);d=dict(name="tests",argv=[sys.executable,"-I","-B","-c",\'print("TAP version 13");print("ok 1 - local");print("1..1")\'],cwd=".",report_format="tap",timeout_seconds=3,max_output_bytes=65536);'+
      'c=freeze_candidate(r,"change-1",["source.py"],session_id="author",policy=dict(checks=["tests"],review_required=True,definitions={"tests":check_binding(r,d)}));store_candidate(r,c,approved=True);'+
      'assert run_check(r,"change-1",d,session_id="author",run_id="check-1",approved=True)["status"]=="completed";configure(r,tokens=1000,calls=5,approved=True)',root],{encoding:'utf8'});
    const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/agent/fixture-auth.json'),modelsPath:null,
      modelsStorePath:join(root,'.aikya/pi/agent/fixture-models.json'),allowModelNetwork:false,refreshOnCreate:false});
    let requests=0;
    models.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
      models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:10000,maxTokens:500}],
      streamSimple:()=>{
        requests++; const stream=createAssistantMessageEventStream();
        const message:AssistantMessage={role:'assistant',content:[{type:'text',text:'{"decision":"accept","findings":[]}'}],api:'fixture',provider:'fixture',model:'fixture',
          usage:{input:10,output:5,cacheRead:0,cacheWrite:0,totalTokens:15,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},stopReason:'stop',timestamp:Date.now()};
        stream.push({type:'done',reason:'stop',message}); return stream;
      }});
    await assert.rejects(adapter.performReview(root,'change-1',{python,provider:'fixture',model:'fixture',modelRuntime:models,approved:true,expectedCandidate:'0'.repeat(64)}),/changed/i);
    assert.equal(requests,0);
    const result=await adapter.performReview(root,'change-1',{python,provider:'fixture',model:'fixture',modelRuntime:models,approved:true});
    assert.equal(requests,1); assert.equal(result.status,'reviewed'); assert.equal(result.can_close,true);
    assert.equal(result.delivery_authorized,false);
  } finally {rmSync(root,{recursive:true,force:true});}
});
