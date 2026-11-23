import assert from "node:assert/strict";
import { test } from "node:test";
const view=await import('../src/usage-view.ts').catch(()=>null);

test('provider header windows stay separate from context and genuine zero is preserved',()=>{
  assert.ok(view,'Provider quota adapter is absent');
  const value=view.quotaFromHeaders('openai-codex',{
    'x-codex-primary-used-percent':'25','x-codex-primary-window-minutes':'300','x-codex-primary-reset-at':'1800000000',
    'x-codex-secondary-used-percent':'0','x-codex-secondary-window-minutes':'10080',
    'authorization':'DO_NOT_RETAIN'},1000);
  assert.deepEqual(value?.windows.map(w=>[w.label,w.usedPercent]),[['5h',25],['week',0]]);
  assert.equal(JSON.stringify(value).includes('DO_NOT_RETAIN'),false);
  assert.equal(view.quotaFromHeaders('other',{'context-percent':'25'},1000),null);
  assert.equal(view.quotaFromHeaders('openai-codex',{'x-codex-primary-used-percent':'25','x-codex-primary-window-minutes':'300oops'},1000),null);
});

test('Anthropic utilization is a fraction while missing quota stays unknown in the panel',()=>{
  assert.ok(view);
  const value=view.quotaFromHeaders('anthropic',{'anthropic-ratelimit-unified-5h-utilization':'0.4',
    'anthropic-ratelimit-unified-5h-reset':'1800000000'},1000);
  assert.equal(value?.windows[0].usedPercent,40);
  const lines=view.renderUsage({status:'unconfigured',recorded_tokens:null,calls:0},[{snapshot:null,stale:true}],120,1000);
  assert.match(lines.join('\n'),/unknown|unavailable/i);
  assert.doesNotMatch(lines.join('\n'),/0%/);
});

test('panel identifies stale provider quota and local incomplete accounting',()=>{
  assert.ok(view);
  const lines=view.renderUsage({status:'unknown_usage',recorded_tokens:12,calls:2,limits:{tokens:100,calls:5}},
    [{snapshot:{provider:'fixture',fetchedAt:1000,windows:[{label:'5h',seconds:18000,usedPercent:25,resetAt:9000}]},stale:true}],120,2000);
  assert.match(lines.join('\n'),/12/);assert.match(lines.join('\n'),/25%/);
  assert.match(lines.join('\n'),/stale/);assert.match(lines.join('\n'),/unknown/);
});

test('out-of-range provider reset clocks never crash the terminal',()=>{
  assert.ok(view);
  const snapshot=view.quotaFromHeaders('anthropic',{'anthropic-ratelimit-unified-5h-utilization':'0.2',
    'anthropic-ratelimit-unified-5h-reset':'99999999999999999'},1000);
  assert.equal(snapshot?.windows[0].resetAt,null);
  assert.doesNotThrow(()=>view.renderUsage({status:'available',recorded_tokens:1,calls:1},
    [{snapshot:{provider:'fixture',fetchedAt:1000,windows:[{label:'5h',seconds:18000,usedPercent:20,resetAt:1e30}]},stale:false}]));
});

test('footer distinguishes local known zero from an unavailable budget without invented percentages',()=>{
  assert.ok(view);assert.equal(typeof view.renderFooter,'function','Truthful local footer is absent');
  const unavailable=view.renderFooter('explore',null,{status:'unconfigured',recorded_tokens:null,calls:0},120);
  assert.match(unavailable,/model disabled/);assert.match(unavailable,/unconfigured/);assert.doesNotMatch(unavailable,/0%|0\/0/);
  const known=view.renderFooter('implement','fixture/model',{status:'available',recorded_tokens:0,calls:0,limits:{tokens:1000,calls:5}},120);
  assert.match(known,/fixture\/model/);assert.match(known,/0 local tokens/);
});
