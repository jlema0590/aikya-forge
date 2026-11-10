import assert from 'node:assert/strict';
import { test } from 'node:test';
const confirmation=await import('../src/confirmation.ts').catch(()=>null);
test('a bounded confirmation keeps its choices visible and cannot accept unseen overflow',()=>{
  assert.ok(confirmation,'Scrollable host confirmation is absent');
  const done:boolean[]=[];
  const dialog=new confirmation.ApprovalDialog('Review operation',Array.from({length:40},(_,i)=>'Source path '+i).join('\n'),()=>8,v=>done.push(v));
  assert.ok(dialog.render(50).length<=8);
  dialog.handleInput('\r');assert.deepEqual(done,[]);
  dialog.handleInput('\u001b[F');dialog.handleInput('\r');assert.deepEqual(done,[true]);
  const cancelled:boolean[]=[];
  const other=new confirmation.ApprovalDialog('Review operation','content',()=>8,v=>cancelled.push(v));
  other.render(50);other.handleInput('\u001b');assert.deepEqual(cancelled,[false]);
});
