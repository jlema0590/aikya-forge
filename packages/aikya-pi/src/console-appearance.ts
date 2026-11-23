import {Theme,type ExtensionUIContext} from '@earendil-works/pi-coding-agent';
import {colorToHex} from '@earendil-works/pi-tui';
import type {ConsoleSettings} from './console-preferences.ts';
import {AIKYA_COLORS} from './brand.ts';

export function applyAppearance(ui:ExtensionUIContext,settings:ConsoleSettings) {
  const selected=settings.theme==='inherit'?(ui.theme.name??'dark'):settings.theme;
  const base=ui.getTheme(selected==='aikya'?'dark':selected);
  if(!base)throw new Error('Installed theme unavailable');
  if(selected!=='aikya'&&!Object.keys(settings.colors).length) {
    if(!ui.setTheme(base).success)throw new Error('Theme activation refused');return;
  }
  const colors=Object.fromEntries(Object.entries(base.colors).map(([name,color])=>[name,colorToHex(color)]));
  if(selected==='aikya')Object.assign(colors,{accent:AIKYA_COLORS.accent,text:AIKYA_COLORS.text,muted:AIKYA_COLORS.muted,
    dim:AIKYA_COLORS.muted,border:AIKYA_COLORS.border,borderAccent:AIKYA_COLORS.accent,borderMuted:AIKYA_COLORS.border,
    success:AIKYA_COLORS.success,warning:AIKYA_COLORS.warning,error:AIKYA_COLORS.error,
    selectedBg:AIKYA_COLORS.panel,userMessageBg:AIKYA_COLORS.panel,userMessageText:AIKYA_COLORS.text,
    customMessageBg:AIKYA_COLORS.panel,customMessageText:AIKYA_COLORS.text,customMessageLabel:AIKYA_COLORS.accent,
    toolPendingBg:AIKYA_COLORS.panel,toolSuccessBg:AIKYA_COLORS.panel,toolErrorBg:AIKYA_COLORS.panel,
    toolTitle:AIKYA_COLORS.text,toolOutput:AIKYA_COLORS.muted});
  for(const token of ['accent','text','muted'] as const)if(settings.colors[token])colors[token]=settings.colors[token]!;
  const theme=new Theme(colors as ConstructorParameters<typeof Theme>[0],colors as ConstructorParameters<typeof Theme>[1],
    base.getColorMode(),{name:selected,appearance:selected==='aikya'?'dark':base.appearance});
  if(!ui.setTheme(theme).success)throw new Error('Custom palette activation refused');
}
