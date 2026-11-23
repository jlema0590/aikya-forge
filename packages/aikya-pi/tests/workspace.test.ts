import assert from 'node:assert/strict';
import {test} from 'node:test';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,basename} from 'node:path';
import {stripTerminalSequences,visibleWidth} from '@earendil-works/pi-tui';
import {renderBrandHeader} from '../src/brand-header.ts';
const workspace=await import('../src/workspace.ts').catch(()=>null);

test('startup identifies the selected project, Git branch and user without legacy branding or terminal escapes',()=>{
  const identity={project:'payments-app',branch:'feature/payments',user:'Juan Lema'};
  const value=renderBrandHeader(79,'0.2.0','Local preview',undefined,identity).map(stripTerminalSequences).join('\n');
  assert.match(value,/Aikya Forge v0.2.0/);assert.doesNotMatch(value,/Harness/);
  assert.match(value,/Project: payments-app/);assert.match(value,/Git branch: feature\/payments/);assert.match(value,/Git user: Juan Lema/);
  for(const width of [1,10,20,79])assert.ok(renderBrandHeader(width,'0.2.0','Local preview',undefined,identity).every(s=>visibleWidth(s)<=width));
  const unsafe=renderBrandHeader(79,'0.2.0','Local preview',undefined,{project:'app\x1b[2J',branch:'x\nFAKE',user:'a\r\nUSER'}).map(stripTerminalSequences).join('\n');
  assert.equal(unsafe.split('\n').length,5,'Metadata cannot inject additional terminal rows');
});

test('Git identity uses real project user.name as data and permits no shell interpretation',async()=>{
  assert.ok(workspace,'Workspace identity reader is absent');
  const root=mkdtempSync(join(tmpdir(),'forge-git-'));
  try {
    execFileSync('git',['init','--quiet',root]);
    const user='Forge User; $(touch unexpected-marker)';
    execFileSync('git',['-C',root,'config','user.name',user]);
    assert.equal(await workspace.readGitUser(root),user);assert.equal(existsSync(join(root,'unexpected-marker')),false);
    assert.equal(workspace.projectIdentity(root,user,()=> 'feature/one').project,basename(root));
    let branch='feature/one';const view=workspace.projectIdentity(root,user,()=>branch);
    assert.equal(view.branch,'feature/one');branch='feature/two';assert.equal(view.branch,'feature/two','Branch updates reuse the SDK cache');
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('missing Git retains explicit unavailable fields and does not block startup',async()=>{
  assert.ok(workspace,'Workspace identity reader is absent');
  const key=Object.keys(process.env).find(k=>k.toUpperCase()==='PATH')??'PATH',before=process.env[key];
  try {
    process.env[key]='';assert.equal(await workspace.readGitUser(tmpdir()),null);
    const rows=renderBrandHeader(79,'0.2.0','Local preview',undefined,workspace.projectIdentity(tmpdir(),null,()=>null)).join('\n');
    assert.match(rows,/Git branch: unavailable/);assert.match(rows,/Git user: not configured/);
  } finally {if(before===undefined)delete process.env[key];else process.env[key]=before;}
});
