import assert from 'node:assert/strict';
import {test} from 'node:test';
import {visibleWidth} from '@earendil-works/pi-tui';
const panels=await import('../src/provider-panel.ts').catch(()=>null);
const budget={status:'available',recorded_tokens:100,calls:2,grouped_calls:2,groups:[
  {role:'author',phase:'implement',provider:'anthropic',model:'a',calls:1,recorded_tokens:75,usage_complete:true},
  {role:'reviewer',phase:'review',provider:'openai-codex',model:'b',calls:1,recorded_tokens:25,usage_complete:true}]};
const snapshot={budget,quotas:[],contextProvider:'anthropic',context:{tokens:200,contextWindow:1000,percent:20}};

test('provider panels distinguish active context, project tokens and exact account windows',()=>{
  assert.ok(panels,'Provider panels are absent');
  const data={...snapshot,quotas:[{stale:false,snapshot:{provider:'anthropic',fetchedAt:1000,windows:[
    {label:'5h',seconds:18000,usedPercent:40,resetAt:100000},{label:'week',seconds:604800,usedPercent:12,resetAt:900000}]}},
    {stale:false,snapshot:{provider:'openai-codex',fetchedAt:1000,windows:[
      {label:'secondary',seconds:18000,usedPercent:0,resetAt:100000},{label:'primary',seconds:604800,usedPercent:60,resetAt:900000}]}}]};
  const claude=panels.renderProviderPanel('anthropic',data,2000).join('\n');
  assert.match(claude,/Claude\nContext: 20% \(estimated\)/);assert.match(claude,/Tokens: 75.*75% project/);
  assert.match(claude,/Usage 5h: 40% used/);assert.match(claude,/Usage 7d: 12% used/);
  const codex=panels.renderProviderPanel('openai-codex',data,2000).join('\n');
  assert.match(codex,/Codex\nContext: unavailable/);assert.match(codex,/Tokens: 25.*25% project/);
  assert.match(codex,/Usage 5h: 0% used/);assert.match(codex,/Usage 7d: 60% used/);
  assert.match(codex,/Source: headers.*1s old/);
});

test('missing windows and unrelated durations do not become account zero or a five-hour quota',()=>{
  assert.ok(panels);
  const data={...snapshot,contextProvider:undefined,quotas:[{stale:false,snapshot:{provider:'openai-codex',fetchedAt:1000,windows:[
    {label:'5h',seconds:3600,usedPercent:99,resetAt:null}]}}]};
  const rows=panels.renderProviderPanel('openai-codex',data,2000).join('\n');
  assert.match(rows,/Usage 5h: unavailable/);assert.match(rows,/Usage 7d: unavailable/);assert.doesNotMatch(rows,/99%|0%/);
});

test('unknown attribution stays partial and stale or reset quotas remain marked',()=>{
  assert.ok(panels);
  const data={...snapshot,budget:{...budget,status:'unknown_usage',grouped_calls:1,groups:[{...budget.groups[0],usage_complete:false}]},
    quotas:[{stale:false,snapshot:{provider:'anthropic',fetchedAt:1000,windows:[{label:'5h',seconds:18000,usedPercent:40,resetAt:1500}]}}]};
  const claude=panels.renderProviderPanel('anthropic',data,2000).join('\n');
  assert.match(claude,/Tokens: 75 \+ unknown/);assert.doesNotMatch(claude,/75% project/);assert.match(claude,/Usage 5h: 40% used.*stale/);
  assert.match(panels.renderProviderPanel('openai-codex',data,2000).join('\n'),/Tokens: unknown/);
  data.quotas[0].snapshot.windows[0].resetAt=900000;
  assert.match(panels.renderProviderPanel('anthropic',data,62001).join('\n'),/stale/);
});

test('known zero project tokens and context survive while missing tokens stay unknown',()=>{
  assert.ok(panels);
  const zero={budget:{status:'available',recorded_tokens:0,calls:0,grouped_calls:0,groups:[]},quotas:[],
    contextProvider:'openai-codex',context:{tokens:0,contextWindow:1000,percent:0}};
  const rows=panels.renderProviderPanel('openai-codex',zero,1000).join('\n');
  assert.match(rows,/Context: 0% \(estimated\)/);assert.match(rows,/Tokens: 0/);assert.match(rows,/Usage 5h: unavailable/);
  const missing={...zero,budget:{status:'unconfigured',recorded_tokens:null,calls:0},context:{tokens:null,contextWindow:1000,percent:null}};
  const unknown=panels.renderProviderPanel('openai-codex',missing,1000).join('\n');
  assert.match(unknown,/Context: unavailable/);assert.match(unknown,/Tokens: unknown/);assert.doesNotMatch(unknown,/0%/);
});
