import {Theme,type ExtensionUIContext} from '@earendil-works/pi-coding-agent';
import {colorToHex} from '@earendil-works/pi-tui';
import type {ConsoleSettings} from './console-preferences.ts';

export function applyAppearance(ui:ExtensionUIContext,settings:ConsoleSettings) {
  const base=ui.getTheme(settings.theme==='inherit'?(ui.theme.name??'dark'):settings.theme);
  if(!base)throw new Error('Installed theme unavailable');
  if(!Object.keys(settings.colors).length) {
    if(!ui.setTheme(base).success)throw new Error('Theme activation refused');return;
  }
  const colors=Object.fromEntries(Object.entries(base.colors).map(([name,color])=>[name,colorToHex(color)]));
  for(const token of ['accent','text','muted'] as const)if(settings.colors[token])colors[token]=settings.colors[token]!;
  const theme=new Theme(colors as ConstructorParameters<typeof Theme>[0],colors as ConstructorParameters<typeof Theme>[1],
    base.getColorMode(),{name:base.name,appearance:base.appearance});
  if(!ui.setTheme(theme).success)throw new Error('Custom palette activation refused');
}
