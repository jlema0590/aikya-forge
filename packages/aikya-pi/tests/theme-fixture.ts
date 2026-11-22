import {readFileSync} from 'node:fs';
import {Theme} from '@earendil-works/pi-coding-agent';

/** Real pinned palettes for UI interaction tests; the provider transport is separate. */
export function installedTheme(name:'dark'|'light') {
  const raw=JSON.parse(readFileSync(new URL('../node_modules/@earendil-works/pi-coding-agent/dist/modes/interactive/theme/'+name+'.json',import.meta.url),'utf8'));
  const colors=Object.fromEntries(Object.entries(raw.colors).map(([key,v])=>{
    let value=v;while(typeof value==='string'&&value in raw.vars)value=raw.vars[value];return [key,value];
  }));
  return new Theme(colors as ConstructorParameters<typeof Theme>[0],colors as ConstructorParameters<typeof Theme>[1],'truecolor',{name,appearance:name});
}
