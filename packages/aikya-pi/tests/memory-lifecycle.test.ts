import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,writeFileSync,readFileSync,existsSync,rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createReadOnlyRuntime,createReadOnlySession } from '../src/runtime.ts';

async function until(check:()=>boolean) {
  const deadline=Date.now()+12000;
  while(Date.now()<deadline) {if(check()) return;await new Promise(resolve=>setTimeout(resolve,75));}
  assert.ok(check(),'Project memory observer did not reach its expected state');
}

for(const mode of ['interactive-runtime','headless-session']) test('real Pi '+mode+' observes external edits and releases its watcher',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-pi-observer-'));
  const python=process.env.AIKYA_TEST_PYTHON??'python3';
  const html=join(root,'aikya/docs/memory/view/index.html'),state=join(root,'.harness/state/memory-view/status.json');
  try {
    execFileSync(python,['-I','-B','-c','from pathlib import Path;import sys;from aikya.code_index.policy import configure;configure(Path(sys.argv[1]),approved=True)',root]);
    writeFileSync(join(root,'entity.py'),'class OriginalPiEntity: pass\n');
    const runtime=mode==='interactive-runtime'?await createReadOnlyRuntime(root,{python}):await createReadOnlySession(root,{python});
    try {
      if(mode==='interactive-runtime')await runtime.session.bindExtensions({});
      await until(()=>existsSync(html)&&readFileSync(html,'utf8').includes('OriginalPiEntity'));
      writeFileSync(join(root,'entity.py'),'class ExternallyChangedPiEntity: pass\n');
      await until(()=>readFileSync(html,'utf8').includes('ExternallyChangedPiEntity'));
    } finally {if('close' in runtime)await runtime.close();else await runtime.dispose();}
    await until(()=>existsSync(state)&&JSON.parse(readFileSync(state,'utf8')).state==='Stopped');
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('the session lease renews locally during idle time and stops renewal before releasing ownership',async()=>{
  const lifecycle=await import('../src/memory-lifecycle.ts');
  assert.equal(typeof lifecycle.LocalMemoryLease,'function','Long-session lease ownership is absent');
  const root=mkdtempSync(join(tmpdir(),'aikya-pi-heartbeat-'));
  const python=process.env.AIKYA_TEST_PYTHON??'python3';
  try {
    execFileSync(python,['-I','-B','-c','from pathlib import Path;import sys;from aikya.code_index.policy import configure;configure(Path(sys.argv[1]),approved=True)',root]);
    const owner=new lifecycle.LocalMemoryLease(root,'idle-session',python,50);
    const leases=join(root,'.harness/state/memory-view/sessions.json');
    try {
      await owner.start();
      const initial=Object.values(JSON.parse(readFileSync(leases,'utf8')))[0] as number;
      await until(()=>(Object.values(JSON.parse(readFileSync(leases,'utf8')))[0] as number)>initial);
    } finally {await owner.stop();}
    assert.deepEqual(JSON.parse(readFileSync(leases,'utf8')),{});
    const state=join(root,'.harness/state/memory-view/status.json');
    await until(()=>existsSync(state)&&JSON.parse(readFileSync(state,'utf8')).state==='Stopped');
  } finally {rmSync(root,{recursive:true,force:true});}
});
