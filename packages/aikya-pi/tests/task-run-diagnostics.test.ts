import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';

const diagnostic=await import('./task-run-diagnostics.ts').catch(()=>null);

test('task failure diagnostics retain execution outcomes and phase without fixture secrets',()=>{
  assert.ok(diagnostic,'Bounded task failure evidence is missing');
  const root=mkdtempSync(join(tmpdir(),'aikya-task-diagnostic-')),run='a'.repeat(32);
  try {
    const task=join(root,'.aikya/pi/task-runs'),check=join(root,'aikya/docs/validation/task-proof/checks/owned-check');
    mkdirSync(task,{recursive:true});mkdirSync(check,{recursive:true});
    writeFileSync(join(task,run+'.json'),JSON.stringify({payload:{status:'stopped',phase:'validate',session_id:'PRIVATE_SESSION',source:'PRIVATE_SOURCE'},mac:'PRIVATE_MAC'}));
    writeFileSync(join(check,'execution.json'),JSON.stringify({status:'timed_out',exit_code:1,duration_ns:3000000000,
      stdout_bytes:0,stderr_bytes:0,counts:null,argv:['PRIVATE_COMMAND'],environment:{key:'PRIVATE_KEY'}}));
    const result=diagnostic.taskFailureEvidence(root,run);
    assert.deepEqual(result,{task:{status:'stopped',phase:'validate'},checks:[{status:'timed_out',exit_code:1,
      duration_ns:3000000000,stdout_bytes:0,stderr_bytes:0,counts:null}]});
    const raw=JSON.stringify(result);assert.ok(!raw.includes('PRIVATE')&&!raw.includes(root));
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('unreadable oversized or foreign task diagnostics remain bounded and non-authoritative',()=>{
  assert.ok(diagnostic,'Bounded task failure evidence is missing');
  const root=mkdtempSync(join(tmpdir(),'aikya-task-invalid-diagnostic-')),run='b'.repeat(32);
  try {
    const task=join(root,'.aikya/pi/task-runs');mkdirSync(task,{recursive:true});
    writeFileSync(join(task,run+'.json'),'x'.repeat(70000));
    assert.deepEqual(diagnostic.taskFailureEvidence(root,run),{task:null,checks:[]});
    assert.deepEqual(diagnostic.taskFailureEvidence(root,'../../PRIVATE'),{task:null,checks:[]});
    writeFileSync(join(task,run+'.json'),JSON.stringify({payload:{status:'private_secret',phase:'private_source'}}));
    assert.deepEqual(diagnostic.taskFailureEvidence(root,run),{task:{status:null,phase:null},checks:[]});
  } finally {rmSync(root,{recursive:true,force:true});}
});
