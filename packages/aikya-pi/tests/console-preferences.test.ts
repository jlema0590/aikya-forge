import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,readFileSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {Theme,type ExtensionUIContext} from '@earendil-works/pi-coding-agent';
import {colorToHex} from '@earendil-works/pi-tui';
import {applyAppearance} from '../src/console-appearance.ts';
const config=await import('../src/console-preferences.ts').catch(()=>null);
const launch=await import('../src/console-launch.ts').catch(()=>null);

test('console preferences persist presentation and next-launch selection without accepting secrets',()=>{
  assert.ok(config,'Console preferences are absent');
  const root=mkdtempSync(join(tmpdir(),'aikya-console-'));
  try {
    const store=new config.ConsolePreferences(root);
    const value={...store.load().value,theme:'light' as const,colors:{accent:'#123456'},textStyle:'bold' as const,
      provider:{id:'openai-codex',model:'example-model'}};
    store.save(value);
    assert.deepEqual(new config.ConsolePreferences(root).load().value,value);
    const path=join(root,'.aikya/pi/console.json'),before=readFileSync(path,'utf8');
    assert.throws(()=>store.save({...value,apiKey:'must-not-persist'}));
    assert.throws(()=>store.save({...value,colors:{accent:'\x1b[31m'}}));
    assert.throws(()=>store.save({...value,provider:{id:'x',model:'bad\nmodel'}}));
    assert.equal(readFileSync(path,'utf8'),before);
  } finally {rmSync(root,{recursive:true,force:true});}
});

test('resetting a custom palette restores the installed palette instead of retaining the override',()=>{
  const path=new URL('../node_modules/@earendil-works/pi-coding-agent/dist/modes/interactive/theme/dark.json',import.meta.url);
  const raw=JSON.parse(readFileSync(path,'utf8'));
  const colors=Object.fromEntries(Object.entries(raw.colors).map(([key,v])=>{
    let value=v;while(typeof value==='string'&&value in raw.vars)value=raw.vars[value];return [key,value];
  }));
  const base=new Theme(colors as ConstructorParameters<typeof Theme>[0],colors as ConstructorParameters<typeof Theme>[1],'truecolor',{name:'dark'});
  let active=base;
  const ui={get theme(){return active;},getTheme:()=>base,setTheme:(t:Theme)=>{active=t;return {success:true};}} as unknown as ExtensionUIContext;
  applyAppearance(ui,{theme:'inherit',textStyle:'normal',sidebar:true,colors:{accent:'#123456'}});
  assert.equal(colorToHex(active.colors.accent),'#123456');
  applyAppearance(ui,{theme:'inherit',textStyle:'normal',sidebar:true,colors:{}});
  assert.notEqual(colorToHex(active.colors.accent),'#123456');
});

test('saved providers require an available budget and explicit flags override saved selection',()=>{
  assert.ok(launch,'Console launch selection is absent');
  const prefs={theme:'dark' as const,textStyle:'normal' as const,sidebar:true,colors:{},provider:{id:'anthropic',model:'saved'}};
  assert.equal(launch.resolveConsoleLaunch(prefs,{status:'unconfigured',recorded_tokens:null,calls:0}).provider,undefined);
  assert.equal(launch.resolveConsoleLaunch(prefs,{status:'unknown_usage',recorded_tokens:1,calls:1}).provider,undefined);
  assert.equal(launch.resolveConsoleLaunch(prefs,{status:'available',recorded_tokens:0,calls:0}).model,'saved');
  assert.equal(launch.resolveConsoleLaunch(prefs,{status:'unconfigured',recorded_tokens:null,calls:0},'openai-codex','explicit').model,'explicit');
  assert.throws(()=>launch.resolveConsoleLaunch(prefs,{status:'available',recorded_tokens:0,calls:0},'anthropic'));
});

test('corrupt or redirected console settings are preserved instead of overwritten',()=>{
  assert.ok(config);
  const root=mkdtempSync(join(tmpdir(),'aikya-console-owned-'));
  try {
    const store=new config.ConsolePreferences(root),value=store.load().value;store.save(value);
    const path=join(root,'.aikya/pi/console.json');writeFileSync(path,'CUSTOM');
    assert.ok(store.load().diagnostic);assert.throws(()=>store.save(value));
    assert.equal(readFileSync(path,'utf8'),'CUSTOM');
    rmSync(path);const outside=join(root,'outside');writeFileSync(outside,'USER');symlinkSync(outside,path);
    assert.throws(()=>store.save(value));assert.equal(readFileSync(outside,'utf8'),'USER');
  } finally {rmSync(root,{recursive:true,force:true});}
});
