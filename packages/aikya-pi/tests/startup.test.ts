import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,existsSync,rmSync,copyFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {createReadOnlySession,createReadOnlyRuntime} from '../src/runtime.ts';
import {approvingUI} from './task-run-fixture.ts';
import {removeProject} from './project-cleanup.ts';
const startup=await import('../src/startup.ts').catch(()=>null);

test('native tool discovery disables implicit current-directory executable lookup',()=>{
 const root=mkdtempSync(join(tmpdir(),'aikya-search-policy-'));const previous=process.env.NoDefaultCurrentDirectoryInExePath;
 try {
  delete process.env.NoDefaultCurrentDirectoryInExePath;
  assert.equal(typeof startup?.prepareToolSearch,'function','Native tool search policy is absent');
  startup!.prepareToolSearch(root);assert.equal(process.env.NoDefaultCurrentDirectoryInExePath,'1');
  assert.equal(existsSync(join(root,'.aikya')),false);
 }finally {
  if(previous===undefined)delete process.env.NoDefaultCurrentDirectoryInExePath;else process.env.NoDefaultCurrentDirectoryInExePath=previous;
  // No runtime/watcher was created in this test.
  rmSync(root,{recursive:true,force:true});
 }
});

test('Windows ignores an inert project executable and selects the explicit trusted PATH tool',{skip:process.platform!=='win32'},()=>{
 const root=mkdtempSync(join(tmpdir(),'aikya-windows-lookup-')),tools=join(root,'trusted');mkdirSync(tools);
 const beforePath=process.env.PATH,beforePolicy=process.env.NoDefaultCurrentDirectoryInExePath;
 try {
  writeFileSync(join(root,'fd.exe'),'Inert invalid executable, never runnable');copyFileSync(process.execPath,join(tools,'fd.exe'));
  process.env.PATH=tools;delete process.env.NoDefaultCurrentDirectoryInExePath;
  const args=['-e','process.stdout.write("verified-tool")'];
  assert.ok(spawnSync('fd.exe',args,{cwd:root,encoding:'utf8'}).error,'Negative control must encounter the inert project file');
  startup!.prepareToolSearch(root);
  const result=spawnSync('fd.exe',args,{cwd:root,encoding:'utf8'});
  assert.equal(result.status,0);assert.equal(result.stdout,'verified-tool');
  assert.equal(readFileSync(join(root,'fd.exe'),'utf8'),'Inert invalid executable, never runnable');
 }finally {
  if(beforePath===undefined)delete process.env.PATH;else process.env.PATH=beforePath;
  if(beforePolicy===undefined)delete process.env.NoDefaultCurrentDirectoryInExePath;else process.env.NoDefaultCurrentDirectoryInExePath=beforePolicy;
  rmSync(root,{recursive:true,force:true});
 }
});

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
