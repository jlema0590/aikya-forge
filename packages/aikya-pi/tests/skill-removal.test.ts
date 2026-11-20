import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,mkdirSync,writeFileSync,rmSync,realpathSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {hostOperation} from '../src/host.ts';
import {createReadOnlySession} from '../src/runtime.ts';
import {approvingUI} from './task-run-fixture.ts';
const python=process.env.AIKYA_TEST_PYTHON??'python3';

test('native skill withdrawal requires UI confirmation and restores exact selection without inference',async()=>{
  const base=realpathSync(mkdtempSync(join(tmpdir(),'aikya-skill-removal-'))),root=join(base,'project'),source=join(base,'example-skill');
  mkdirSync(root);mkdirSync(source);writeFileSync(join(source,'SKILL.md'),'---\nname: example-skill\ndescription: Selected project conventions\n---\nApproved conventions.\n');
  const before=await hostOperation(root,'skills.preview',{source},python);
  await hostOperation(root,'skills.apply',{plan:before.plan,approved:true},python);
  const runtime=await createReadOnlySession(root,{python});
  try {
    runtime.session.agent.streamFunction=()=>{throw new Error('Native withdrawal must not call a model');};
    const invoke=async(input:Record<string,unknown>)=>{
      await runtime.session.prompt('/aikya-uninstall-skills '+JSON.stringify(input));
      const m=runtime.session.messages.findLast(m=>m.role==='custom'&&m.customType==='aikya-uninstall-skills');
      assert.ok(m,'Missing native removal result');assert.equal(m.role,'custom');return JSON.parse(m.content as string);
    };
    assert.equal((await invoke({names:['example-skill']})).status,'confirmation_required');
    await runtime.session.bindExtensions({uiContext:approvingUI(()=>false),mode:'tui',onError:e=>{throw new Error(e.error);}});
    assert.equal((await invoke({names:['example-skill']})).status,'declined');
    assert.equal(((await hostOperation(root,'skills.resolve',{},python)).skills as unknown[]).length,1);
    await runtime.session.bindExtensions({uiContext:approvingUI(),mode:'tui',onError:e=>{throw new Error(e.error);}});
    const result=await invoke({scope:'local',names:['example-skill']});assert.equal(result.status,'removed');
    assert.equal(((await hostOperation(root,'skills.resolve',{},python)).skills as unknown[]).length,0);
    assert.equal((await invoke({action:'restore',names:['example-skill'],operation_id:result.operation_id})).status,'restored');
    assert.equal(((await hostOperation(root,'skills.resolve',{},python)).skills as unknown[]).length,1);
  } finally {await runtime.close();rmSync(base,{recursive:true,force:true});}
});
