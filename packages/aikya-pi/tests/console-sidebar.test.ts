import assert from 'node:assert/strict';
import {test} from 'node:test';
import {Container,visibleWidth} from '@earendil-works/pi-tui';
const sidebar=await import('../src/console-sidebar.ts').catch(()=>null);
const layout=await import('../src/console-layout.ts').catch(()=>null);

test('sidebar keeps project budget, agent share, context and account quota as distinct measures',()=>{
  assert.ok(sidebar,'Sidebar is absent');
  const rows=sidebar.renderSidebar({phase:'implement',state:'running',model:'anthropic/example',context:{tokens:200,contextWindow:1000,percent:20},
    budget:{status:'available',recorded_tokens:100,calls:2,limits:{tokens:400,calls:10},grouped_calls:2,groups:[
      {role:'author',phase:'implement',provider:'anthropic',model:'example',recorded_tokens:75,calls:1,usage_complete:true},
      {role:'reviewer',phase:'review',provider:'openai-codex',model:'example',recorded_tokens:25,calls:1,usage_complete:true}]},
    quotas:[{snapshot:{provider:'openai-codex',fetchedAt:1000,windows:[{label:'5h',seconds:18000,usedPercent:42,resetAt:null}]},stale:true}]},44,62000).join('\n');
  assert.match(rows,/25(?:\.0)?%.*local budget/);assert.match(rows,/20(?:\.0)?%.*context/);
  assert.match(rows,/Claude.*75.*75(?:\.0)?%/);assert.match(rows,/Codex.*25.*25(?:\.0)?%/);
  assert.match(rows,/reviewer.*25/);assert.match(rows,/5h.*42.*%/);assert.match(rows,/stale/);
});

test('unknown and truncated usage never becomes zero percent or complete agent attribution',()=>{
  assert.ok(sidebar);
  const unknown=sidebar.renderSidebar({phase:'review',state:'idle',model:null,
    budget:{status:'unknown_usage',recorded_tokens:20,calls:2,limits:{tokens:100,calls:10},grouped_calls:1,
      groups:[{role:'author',phase:'review',provider:'anthropic',model:'a',calls:1,recorded_tokens:20,usage_complete:false}]},quotas:[]},44).join('\n');
  assert.match(unknown,/unknown/);assert.match(unknown,/partial/);assert.doesNotMatch(unknown,/100%/);
  assert.match(unknown,/Claude quota: unavailable/);assert.match(unknown,/Codex quota: unavailable/);
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
