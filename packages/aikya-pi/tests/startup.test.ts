import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession,createReadOnlyRuntime} from '../src/runtime.ts';
import {approvingUI} from './task-run-fixture.ts';
import {removeProject} from './project-cleanup.ts';
const startup=await import('../src/startup.ts').catch(()=>null);

test('the terminal title uses the installed Forge version in a real SDK session',async()=>{
 const root=mkdtempSync(join(tmpdir(),'aikya-title-'));
 try {
  const runtime=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});
  try {
   const titles:string[]=[];const ui=approvingUI();ui.setTitle=value=>titles.push(value);
   await runtime.session.bindExtensions({uiContext:ui,mode:'tui'});
   const version=JSON.parse(readFileSync(new URL('../package.json',import.meta.url),'utf8')).version;
   assert.equal(titles.at(-1),'Aikya Forge v'+version+' · Local preview · model disabled');
  }finally {await runtime.close();}
 }finally {await removeProject(root);}
});

test('a project tool cache cannot supply executables to the native SDK startup',async()=>{
 assert.ok(startup,'Project tool-cache startup guard is absent');
 const root=mkdtempSync(join(tmpdir(),'aikya-tool-cache-'));
 try {
  startup.refuseProjectToolCache(root);assert.equal(existsSync(join(root,'.aikya')),false);
  const bin=join(root,'.aikya/pi/agent/bin');mkdirSync(bin,{recursive:true});
  const file=join(bin,process.platform==='win32'?'fd.exe':'fd');writeFileSync(file,'Unreviewed fixture executable');
  assert.throws(()=>startup.refuseProjectToolCache(root),/project.*tool.*cache/i);
  let opened:Awaited<ReturnType<typeof createReadOnlyRuntime>>|undefined;
  try {
   await assert.rejects(async()=>{opened=await createReadOnlyRuntime(root,{python:process.env.AIKYA_TEST_PYTHON});},/project.*tool.*cache/i);
  }finally {await opened?.dispose();}
  assert.equal(readFileSync(file,'utf8'),'Unreviewed fixture executable');
 }finally {await removeProject(root);}
});
