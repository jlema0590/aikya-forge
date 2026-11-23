import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,rmSync,existsSync,mkdirSync,symlinkSync,writeFileSync,readFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createReadOnlySession} from '../src/runtime.ts';
import {removeProject} from './project-cleanup.ts';
import {ModelRuntime,initTheme,type ExtensionCommandContext} from '@earendil-works/pi-coding-agent';
import {configureProvider} from '../src/provider-settings.ts';
const secret=await import('../src/secret-input.ts').catch(()=>null);

test('settings command reaches the real SDK without inference or credentials in the transcript',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-settings-sdk-'));
  try {
    const {session,close}=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});
    try {
      session.agent.streamFunction=()=>{throw new Error('Model must not run');};
      await session.prompt('/aikya-settings');
      const message=session.messages.find(m=>m.role==='custom'&&m.customType==='aikya-settings');
      assert.ok(message,'Settings command is not registered');
      assert.equal(message.role,'custom');
      assert.equal(JSON.parse(message.content as string).status,'interactive_terminal_required');
      assert.equal(session.messages.filter(m=>m.role==='assistant').length,0);
      assert.equal(existsSync(join(root,'.aikya/pi/console.json')),false);
    } finally {await close();}
  } finally {await removeProject(root);}
});

test('runtime refuses an auth-file link before reading or changing another location',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-auth-link-'));
  let close:(()=>Promise<void>)|undefined;
  try {
    const folder=join(root,'.aikya/pi/agent');mkdirSync(folder,{recursive:true});
    const outside=join(root,'outside.json');writeFileSync(outside,'{}');symlinkSync(outside,join(folder,'auth.json'));
    await assert.rejects(async()=>{const session=await createReadOnlySession(root,{python:process.env.AIKYA_TEST_PYTHON});close=session.close;},/credential/i);
    await close?.();assert.equal(readFileSync(outside,'utf8'),'{}');
  }finally {await close?.();await removeProject(root);}
});

test('native provider connection persists only in the credential store and completes the dialog once',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-provider-ui-'));
  try {
    initTheme('dark',false);
    mkdirSync(join(root,'.aikya/pi/agent'),{recursive:true});const auth=join(root,'.aikya/pi/agent/auth.json');
    const runtime=await ModelRuntime.create({authPath:auth,modelsPath:null,modelsStorePath:join(root,'models.json'),allowModelNetwork:false,refreshOnCreate:false});
    const selections=['anthropic · not configured','Connect','api_key'];let finishes=0;
    const rendered:string[]=[],notices:string[]=[];
    const ctx={cwd:root,isIdle:()=>true,ui:{select:async()=>selections.shift(),notify:(s:string)=>notices.push(s),
      custom:async(factory:Function)=>new Promise(resolve=>{
        let component:{render:(w:number)=>string[];handleInput:(s:string)=>void;dispose?:()=>void};
        const finish=(value:unknown)=>{finishes++;if(finishes>2){resolve(value);return;}component?.dispose?.();resolve(value);};
        component=factory({requestRender:()=>{}},{},{},finish);
        queueMicrotask(()=>{
          const rows=component.render(80).join('\n');rendered.push(rows);
          if(rows.includes('Enter: save credential')){component.handleInput('\x1b[200~sk-fixture-only\x1b[201~');rendered.push(component.render(80).join('\n'));component.handleInput('\r');}
        });
      })}} as unknown as ExtensionCommandContext;
    await configureProvider(ctx,runtime,{theme:'inherit',textStyle:'normal',sidebar:true,colors:{}},()=>assert.fail('Login does not change model binding'));
    assert.equal(runtime.hasConfiguredAuth('anthropic'),true);
    assert.equal(JSON.parse(readFileSync(auth,'utf8')).anthropic.key,'sk-fixture-only');
    assert.doesNotMatch([...rendered,...notices].join('\n'),/sk-fixture-only/);
    assert.equal(finishes,2,'One secret dialog and one login dialog complete exactly once');
  }finally {rmSync(root,{recursive:true,force:true});}
});

test('secret input masks pasted credentials and never renders submitted bytes',()=>{
  assert.ok(secret,'Masked provider input is absent');
  let value:string|undefined;
  const input=new secret.SecretInput('Provider credential',v=>{value=v;});
  input.handleInput('\x1b[200~sk-private-value\x1b[201~');
  assert.doesNotMatch(input.render(60).join('\n'),/sk-private-value/);
  input.handleInput('\r');assert.equal(value,'sk-private-value');
  assert.doesNotMatch(input.render(60).join('\n'),/sk-private-value/);
  input.handleInput('another-private-value');input.handleInput('\x1b');
  assert.equal(value,undefined);assert.equal(input.getValue(),'');
});
