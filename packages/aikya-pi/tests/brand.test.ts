import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,rmSync,readFileSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {visibleWidth,stripTerminalSequences,colorToHex} from '@earendil-works/pi-tui';
import {Theme,type ExtensionUIContext} from '@earendil-works/pi-coding-agent';
import {ConsolePreferences} from '../src/console-preferences.ts';
import {ThemePreferences} from '../src/theme.ts';
import {applyAppearance} from '../src/console-appearance.ts';
const brand=await import('../src/brand.ts').catch(()=>null);
const header=await import('../src/brand-header.ts').catch(()=>null);

test('new projects use the Aikya identity while an explicit legacy or current theme is retained',()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-brand-'));
  try {
    const store=new ConsolePreferences(root);assert.equal(store.load().value.theme,'aikya');
    const legacy=new ThemePreferences(root);legacy.save('light',['dark','light']);
    assert.equal(store.load().value.theme,'inherit');
    store.save({...store.load().value,theme:'dark'});
    assert.equal(new ConsolePreferences(root).load().value.theme,'dark');
    store.save({...store.load().value,theme:'aikya'} as never);
    assert.equal(store.load().value.theme,'aikya');
  }finally {rmSync(root,{recursive:true,force:true});}
});

test('Aikya applies the brand palette and reset removes overrides without losing the brand',()=>{
  assert.ok(brand,'Brand palette is absent');
  const raw=JSON.parse(readFileSync(new URL('../node_modules/@earendil-works/pi-coding-agent/dist/modes/interactive/theme/dark.json',import.meta.url),'utf8'));
  const colors=Object.fromEntries(Object.entries(raw.colors).map(([key,v])=>{let value=v;while(typeof value==='string'&&value in raw.vars)value=raw.vars[value];return [key,value];}));
  const base=new Theme(colors as ConstructorParameters<typeof Theme>[0],colors as ConstructorParameters<typeof Theme>[1],'truecolor',{name:'dark'});
  let active=base;
  const ui={get theme(){return active;},getTheme:(name:string)=>name==='dark'?base:undefined,
    setTheme:(theme:Theme)=>{active=theme;return {success:true};}} as unknown as ExtensionUIContext;
  const settings={theme:'aikya',textStyle:'normal',sidebar:true,colors:{}} as const;
  applyAppearance(ui,settings as never);
  assert.equal(active.name,'aikya');assert.equal(colorToHex(active.colors.text),'#edf4ff');
  applyAppearance(ui,{...settings,colors:{accent:'#123456'}} as never);
  assert.equal(colorToHex(active.colors.accent),'#123456');
  applyAppearance(ui,settings as never);assert.equal(colorToHex(active.colors.accent),brand.AIKYA_COLORS.accent);
});

test('header fits an entire ASCII variant or uses the compact identity at narrow widths',()=>{
  assert.ok(header,'Branded header is absent');
  const banner={generator:'pyfiglet' as const,variants:[{font:'slant',lines:['A'.repeat(35)]},{font:'small',lines:['A'.repeat(15)]}]};
  for(const width of [1,10,40,79,120]) {
    const lines=header.renderBrandHeader(width,'0.2.0','Local preview · model disabled',banner);
    assert.ok(lines.every(line=>visibleWidth(line)<=width));
    if(width>=40)assert.match(lines.map(stripTerminalSequences).join('\n'),/Aikya Harness/);
    if(width>=40)assert.equal(stripTerminalSequences(lines[0]),'A'.repeat(35));
    if(width<=10)assert.ok(lines.length<=3);
  }
  assert.equal(stripTerminalSequences(header.renderBrandHeader(20,'0.2.0','Local preview',banner)[0]),'A'.repeat(15));
  assert.match(header.renderBrandHeader(79,'0.2.0','Local preview').map(stripTerminalSequences).join('\n'),/AIKYA v0.2.0/);
});
