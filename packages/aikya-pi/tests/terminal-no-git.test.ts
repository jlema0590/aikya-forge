import assert from 'node:assert/strict';
import { mkdtempSync,mkdirSync,existsSync,rmSync,writeFileSync,realpathSync } from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';
import {prepareTerminalState} from '../src/terminal-state.ts';

test('an unversioned project initializes local private state without a Git executable',()=>{
 const root=realpathSync(mkdtempSync(join(tmpdir(),'aikya-unversioned-'))),previous=process.env.PATH;
 try {
  process.env.PATH=join(root,'no-executables');const value=prepareTerminalState(root);
  assert.equal(value.project,root);assert.ok(existsSync(join(root,'.aikya/pi/agent')));assert.ok(existsSync(join(root,'.gitignore')));
 }finally{process.env.PATH=previous;rmSync(root,{recursive:true,force:true});}
});

test('a nested Git worktree or gitfile still requires real tracked/ignore validation before writes',()=>{
 const root=realpathSync(mkdtempSync(join(tmpdir(),'aikya-with-git-marker-'))),previous=process.env.PATH;
 try {
  const nested=join(root,'nested');mkdirSync(nested);process.env.PATH=join(root,'no-executables');
  for (const kind of ['directory','gitfile']) {
   if(kind==='directory')mkdirSync(join(root,'.git'));else writeFileSync(join(root,'.git'),'gitdir: /not-adopted\n');
   assert.throws(()=>prepareTerminalState(nested),/Git/);assert.equal(existsSync(join(nested,'.gitignore')),false);assert.equal(existsSync(join(nested,'.aikya')),false);
   rmSync(join(root,'.git'),{recursive:true,force:true});
  }
 }finally{process.env.PATH=previous;rmSync(root,{recursive:true,force:true});}
});

test('bare repository metadata cannot be mistaken for an unversioned project',()=>{
 const root=realpathSync(mkdtempSync(join(tmpdir(),'aikya-bare-marker-'))),previous=process.env.PATH;
 try {
  writeFileSync(join(root,'HEAD'),'ref: refs/heads/main\n');mkdirSync(join(root,'objects'));mkdirSync(join(root,'refs'));process.env.PATH=join(root,'no-executables');
  assert.throws(()=>prepareTerminalState(root),/Git/);assert.equal(existsSync(join(root,'.aikya')),false);
 }finally{process.env.PATH=previous;rmSync(root,{recursive:true,force:true});}
});
