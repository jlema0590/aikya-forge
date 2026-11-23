import assert from 'node:assert/strict';
import {test} from 'node:test';
import {Container,visibleWidth} from '@earendil-works/pi-tui';
const sidebar=await import('../src/console-sidebar.ts').catch(()=>null);
const layout=await import('../src/console-layout.ts').catch(()=>null);

test('sidebar keeps project budget, agent share, context and account quota as distinct measures',()=>{
  assert.ok(sidebar,'Sidebar is absent');
  const rows=sidebar.renderSidebar({phase:'implement',state:'running',model:'anthropic/example',contextProvider:'anthropic',context:{tokens:200,contextWindow:1000,percent:20},
    budget:{status:'available',recorded_tokens:100,calls:2,limits:{tokens:400,calls:10},grouped_calls:2,groups:[
      {role:'author',phase:'implement',provider:'anthropic',model:'example',recorded_tokens:75,calls:1,usage_complete:true},
      {role:'reviewer',phase:'review',provider:'openai-codex',model:'example',recorded_tokens:25,calls:1,usage_complete:true}]},
    quotas:[{snapshot:{provider:'openai-codex',fetchedAt:1000,windows:[{label:'5h',seconds:18000,usedPercent:42,resetAt:null}]},stale:true}]},44,62000).join('\n');
  assert.match(rows,/25(?:\.0)?%.*local budget/);assert.match(rows,/Context: 20(?:\.0)?% \(estimated\)/);
  assert.match(rows,/Claude\n  Context: 20% \(estimated\)\n  Tokens: 75.*75% project/);assert.match(rows,/Codex\n  Context: unavailable\n  Tokens: 25.*25% project/);
  assert.match(rows,/reviewer.*25/);assert.match(rows,/5h.*42.*%/);assert.match(rows,/stale/);
});

test('unknown and truncated usage never becomes zero percent or complete agent attribution',()=>{
  assert.ok(sidebar);
  const unknown=sidebar.renderSidebar({phase:'review',state:'idle',model:null,
    budget:{status:'unknown_usage',recorded_tokens:20,calls:2,limits:{tokens:100,calls:10},grouped_calls:1,
      groups:[{role:'author',phase:'review',provider:'anthropic',model:'a',calls:1,recorded_tokens:20,usage_complete:false}]},quotas:[]},44).join('\n');
  assert.match(unknown,/unknown/);assert.match(unknown,/partial/);assert.doesNotMatch(unknown,/100%/);
  assert.match(unknown,/Claude\n  Context: unavailable\n  Tokens: 20 \+ unknown\n  Usage 5h: unavailable/);assert.match(unknown,/Codex\n  Context: unavailable\n  Tokens: unknown\n  Usage 5h: unavailable/);
});

test('real column composition reserves sidebar width and collapses without clipping Unicode or cursor markers',()=>{
  assert.ok(layout);
  const body=new Container();const widths:number[]=[];
  body.addChild({render:(width:number)=>{widths.push(width);return ['\x1b[31m项目\x1b[0m','prompt\x1b_pi:c\x07'];},invalidate:()=>{}});
  const workbench=new layout.ForgeWorkbench(body,()=>['Flow','implement','tokens: unknown'],()=>true);
  const wide=workbench.render(120);assert.ok(widths.at(-1)!<90);
  assert.ok(wide.some(row=>row.includes('prompt')&&row.includes('tokens: unknown')));
  assert.ok(wide.every(row=>visibleWidth(row)<=120));
  const narrow=workbench.render(60);assert.equal(widths.at(-1),60);
  assert.ok(narrow.some(row=>row.includes('项目')));assert.ok(narrow.every(row=>visibleWidth(row)<=60));
  assert.ok(narrow.some(row=>row.includes('\x1b_pi:c\x07')));
});

test('sidebar controls receive their own clicks without submitting chat input',()=>{
  assert.ok(layout);
  const body=new Container();body.addChild({render:()=>['chat'],invalidate:()=>{}});
  const actions:string[]=[];
  const workbench=new layout.ForgeWorkbench(body,()=>['Flow','[Settings] [Flow] [Stop]'],()=>true,undefined,action=>actions.push(action));
  workbench.render(120);
  workbench.handleMouse({type:'click',button:'left',x:103,y:1,screenX:103,screenY:1,width:120,height:2,shift:false,alt:false,ctrl:false});
  assert.deepEqual(actions,['stop']);
});

test('light appearance paints a readable background even when the host terminal stays dark',()=>{
  assert.ok(layout);
  const body=new Container();body.addChild({render:()=>['body text'],invalidate:()=>{}});
  const workbench=new layout.ForgeWorkbench(body,()=>[],()=>false,()=>({theme:'light',textStyle:'normal',sidebar:false,colors:{}}));
  assert.match(workbench.render(60)[0],/\x1b\[48;2;255;255;255m/);
});


test('compact layout retains Git context below the transcript when columns cannot fit',()=>{
  assert.ok(sidebar&&layout);
  const snapshot={phase:'explore',state:'idle',model:null,workspace:{project:'app',branch:'feature/api',user:'Forge User'},budget:{status:'unconfigured' as const,recorded_tokens:null,calls:0},quotas:[]};
  const body=new Container();body.addChild({render:()=>['Aikya Forge'],invalidate:()=>{}});
  const workbench=new layout.ForgeWorkbench(body,(width:number)=>sidebar.renderSidebar(snapshot,width),()=>true,undefined,undefined,
    (width:number)=>sidebar.renderCompactSidebar(snapshot,width));
  const rows=workbench.render(60);
  assert.ok(rows.every(row=>visibleWidth(row)<=60));
  assert.match(rows.join('\n'),/Project: app/);assert.match(rows.join('\n'),/Branch: feature\/api/);assert.match(rows.join('\n'),/User: Forge User/);
});

test('Agents disclosure groups provider metrics and collapses without hiding project or budget',()=>{
  assert.ok(sidebar);
  const snapshot={phase:'explore',state:'idle',model:null,workspace:{project:'app',branch:'feature/api',user:'Forge User'},budget:{status:'unconfigured' as const,recorded_tokens:null,calls:0},quotas:[]};
  const expanded=sidebar.renderSidebar(snapshot,44).join('\n');
  assert.match(expanded,/\[-\] Agents \(F3\)\n  Claude/);
  assert.match(expanded,/  Codex\n  Context: unavailable/);
  const collapsed=sidebar.renderSidebar({...snapshot,agentsExpanded:false},44).join('\n');
  assert.match(collapsed,/\[\+\] Agents \(F3\)/);assert.doesNotMatch(collapsed,/Claude|Codex|Usage 5h|Usage 7d/);
  assert.match(collapsed,/Project: app/);assert.match(collapsed,/Aikya local budget/);
  const compact=sidebar.renderCompactSidebar({...snapshot,agentsExpanded:false},60).join('\n');
  assert.match(compact,/\[\+\] Agents \(F3\)/);
});

test('clicking Agents toggles only its submenu and cannot reach chat or flow controls',()=>{
  assert.ok(sidebar&&layout);
  let expanded=true;const actions:string[]=[];
  const body=new Container();body.addChild({render:()=>['chat'],invalidate:()=>{}});
  const workbench=new layout.ForgeWorkbench(body,width=>sidebar.renderSidebar({phase:'explore',state:'idle',model:null,
    budget:{status:'unconfigured',recorded_tokens:null,calls:0},quotas:[],agentsExpanded:expanded},width),()=>true,undefined,
    action=>{actions.push(action);if(action==='agents')expanded=!expanded;});
  const rows=workbench.render(120),y=rows.findIndex(row=>row.includes('[-] Agents'));
  assert.ok(y>=0,'Agents disclosure row is absent');
  const result=workbench.handleMouse({type:'click',button:'left',x:90,y,screenX:90,screenY:y,width:120,height:rows.length,shift:false,alt:false,ctrl:false});
  assert.equal(result?.handled,true);assert.deepEqual(actions,['agents']);
  assert.doesNotMatch(workbench.render(120).join('\n'),/Claude|Codex/);
});
