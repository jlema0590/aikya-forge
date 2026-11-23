import assert from 'node:assert/strict';
import {test} from 'node:test';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,basename} from 'node:path';
import {Container,stripTerminalSequences,visibleWidth} from '@earendil-works/pi-tui';
import {renderBrandHeader} from '../src/brand-header.ts';
import {renderSidebar} from '../src/console-sidebar.ts';
import {ForgeWorkbench} from '../src/console-layout.ts';
const workspace=await import('../src/workspace.ts').catch(()=>null);

test('project and Git identity render only in the reserved right column with safe bounded rows',()=>{
  const identity={project:'payments-app',branch:'feature/payments',user:'Juan Lema'};
  const snapshot={phase:'explore',state:'idle',model:null,workspace:identity,budget:{status:'unconfigured' as const,recorded_tokens:null,calls:0},quotas:[]};
  const body=new Container();body.addChild({render:(width:number)=>renderBrandHeader(width,'0.2.0','Local preview'),invalidate:()=>{}});
  const workbench=new ForgeWorkbench(body,width=>renderSidebar(snapshot,width),()=>true);
  const value=workbench.render(120).map(stripTerminalSequences);
  const left=value.map(row=>row.split(' │ ')[0]).join('\n'),right=value.map(row=>row.split(' │ ')[1]??'').join('\n');
  assert.match(left,/Aikya Forge v0.2.0/);assert.doesNotMatch(left,/Harness|Project:|Branch:|User:/);
  assert.match(right,/Project & Git/);assert.match(right,/Project: payments-app/);assert.match(right,/Branch: feature\/payments/);assert.match(right,/User: Juan Lema/);
  for(const width of [1,10,20,79])assert.ok(renderSidebar(snapshot,width).every(s=>visibleWidth(s)<=width));
  const unsafe=renderSidebar({...snapshot,workspace:{project:'app\x1b[2J',branch:'x\nFAKE',user:'a\r\nUSER'}},79).map(stripTerminalSequences);
  assert.ok(unsafe.every(row=>!/[\r\n]/.test(row)),'Metadata cannot inject additional terminal rows');
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
    const rows=renderSidebar({phase:'explore',state:'idle',model:null,budget:{status:'unconfigured',recorded_tokens:null,calls:0},quotas:[],workspace:workspace.projectIdentity(tmpdir(),null,()=>null)},79).join('\n');
    assert.match(rows,/Branch: unavailable/);assert.match(rows,/User: not configured/);
  } finally {if(before===undefined)delete process.env[key];else process.env[key]=before;}
});
