import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {removeProject} from './project-cleanup.ts';
import * as host from '../src/host.ts';

test('real host refusals expose bounded categories without request values or paths',async()=>{
 assert.equal(typeof host.HostOperationError,'function','Typed host failures are absent');
 const root=mkdtempSync(join(tmpdir(),'aikya-host-failure-'));
 try {
  await assert.rejects(host.hostOperation(root,'task.status',{'private-secret-argument':'secret-value'},process.env.AIKYA_TEST_PYTHON),error=>{
   assert.ok(error instanceof host.HostOperationError);
   assert.equal(error.operation,'task.status');assert.equal(error.category,'refused');
   assert.equal(error.diagnostic?.category,'invalid_request');
   assert.ok(!JSON.stringify(error).includes('secret'));assert.ok(!String(error).includes(root));
   return true;
  });
 }finally {await removeProject(root);}
});

test('an unavailable child and an aborted operation remain distinct and never retry',async()=>{
 assert.equal(typeof host.HostOperationError,'function','Typed host failures are absent');
 const root=mkdtempSync(join(tmpdir(),'aikya-host-transport-'));
 try {
  await assert.rejects(host.hostOperation(root,'task.status',{},process.execPath),error=>error instanceof host.HostOperationError&&error.category==='unavailable');
  const controller=new AbortController();controller.abort();
  await assert.rejects(host.hostOperation(root,'task.status',{},process.env.AIKYA_TEST_PYTHON,controller.signal),error=>error instanceof host.HostOperationError&&error.category==='cancelled');
 }finally {await removeProject(root);}
});

test('malformed diagnostics cannot invoke coercion or expose unexpected fields',()=>{
 for(const diagnostic of [{category:{toString:'private-secret'},stage:'aikya.storage.atomic_write'},
     {category:'filesystem_permission',stage:'/private/secret/path'},['private-secret']]) {
  const error=new host.HostOperationError('task.status','refused',diagnostic);
  assert.equal(error.diagnostic,undefined);assert.ok(!JSON.stringify(error).includes('secret'));
 }
});
