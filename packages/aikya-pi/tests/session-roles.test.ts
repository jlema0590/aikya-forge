import assert from 'node:assert/strict';
import { test } from 'node:test';
import { mkdtempSync,rmSync,utimesSync,readFileSync,writeFileSync,readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { SessionManager } from '@earendil-works/pi-coding-agent';
import { projectSession } from '../src/session.ts';
import { createReadOnlySession } from '../src/runtime.ts';

const withRole=projectSession as (root:string,resume:boolean,role?:'author'|'reviewer')=>SessionManager;
test('resuming an author session cannot select a newer independent reviewer transcript',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-session-role-'));
  try {
    const author=withRole(root,false,'author');author.appendMessage({role:'user',content:'Author task',timestamp:1});
    const reviewer=withRole(root,false,'reviewer');reviewer.appendMessage({role:'user',content:'Independent review',timestamp:2});
    assert.ok(reviewer.getSessionFile());utimesSync(reviewer.getSessionFile()!,new Date(),new Date(Date.now()+60000));
    const resumed=withRole(root,true,'author');assert.equal(resumed.getSessionId(),author.getSessionId());
    await assert.rejects(createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON,sessionManager:reviewer}),/role/i);
  } finally {rmSync(root,{recursive:true,force:true});}
});


test('unknown or corrupted role records are preserved rather than adopted on resume',()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-role-unknown-'));
  try {
    const author=withRole(root,false,'author');author.appendMessage({role:'user',content:'Keep this conversation',timestamp:1});
    const transcript=readFileSync(author.getSessionFile()!);
    const role=join(root,'.aikya/pi/session-roles',author.getSessionId()+'.json');
    rmSync(role);assert.throws(()=>withRole(root,true),/role/i);
    writeFileSync(role,'{"custom":true}');assert.throws(()=>withRole(root,true),/role/i);
    assert.equal(readFileSync(role,'utf8'),'{"custom":true}');
    assert.deepEqual(readFileSync(author.getSessionFile()!),transcript);
  } finally {rmSync(root,{recursive:true,force:true});}
});


test('unsupported session roles are rejected before private state is created',()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-role-invalid-'));
  try {assert.throws(()=>withRole(root,false,'admin' as never),/role/i);assert.deepEqual(readdirSync(root),[]);}
  finally {rmSync(root,{recursive:true,force:true});}
});

test('a fresh session remains possible with oversized or corrupted historical transcripts',()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-fresh-long-history-'));
  try {
    const old=withRole(root,false,'author');old.appendMessage({role:'user',content:'Preserve history',timestamp:1});
    const file=old.getSessionFile()!;const header=readFileSync(file,'utf8').split('\n')[0];
    writeFileSync(file,header+'\n'+'x'.repeat(2000001));
    const created=withRole(root,false,'author');assert.notEqual(created.getSessionId(),old.getSessionId());
    assert.equal(readFileSync(file,'utf8').length,header.length+1+2000001);
    writeFileSync(file,'{corrupted historical content');
    assert.notEqual(withRole(root,false,'author').getSessionId(),old.getSessionId());
    assert.equal(readFileSync(file,'utf8'),'{corrupted historical content');
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('an oversized known reviewer is skipped before opening an author transcript on resume',()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-resume-large-reviewer-'));
  try {
    const author=withRole(root,false,'author');author.appendMessage({role:'user',content:'Author task',timestamp:1});
    const reviewer=withRole(root,false,'reviewer');reviewer.appendMessage({role:'user',content:'Review task',timestamp:1});
    const file=reviewer.getSessionFile()!,header=readFileSync(file,'utf8').split('\n')[0];
    writeFileSync(file,header+'\n'+'x'.repeat(2000001));utimesSync(file,new Date(),new Date(Date.now()+60000));
    assert.equal(withRole(root,true,'author').getSessionId(),author.getSessionId());
    assert.throws(()=>withRole(root,true,'reviewer'),/archiv|large|bound|transcript/i);
  } finally {rmSync(root,{recursive:true,force:true});}
});
