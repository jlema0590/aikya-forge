import {Container,truncateToWidth,visibleWidth,type TuiMouseEvent} from '@earendil-works/pi-tui';
import type {ConsoleSettings} from './console-preferences.ts';

/** Public TUI composition: reserve actual columns instead of covering the transcript. */
export class ForgeWorkbench extends Container {
  #body:Container;#sidebar:(width:number)=>string[];#enabled:()=>boolean;
  #left=0;#offset=0;
  #height=0;#wide=false;#action?: (action:'settings'|'flow'|'stop')=>void;
  #appearance?:()=>ConsoleSettings;
  constructor(body:Container,sidebar:(width:number)=>string[],enabled:()=>boolean,appearance?:()=>ConsoleSettings,action?:(action:'settings'|'flow'|'stop')=>void) {
    super();this.#body=body;this.#sidebar=sidebar;this.#enabled=enabled;
    this.#appearance=appearance;
    this.#action=action;
  }
  originalChildren(){return this.#body.children;}
  #style(lines:string[],width:number) {
    const settings=this.#appearance?.();if(!settings)return lines;
    const text=settings.textStyle==='bold'?'\x1b[1m':settings.textStyle==='italic'?'\x1b[3m':'';
    const bg=settings.colors.background??(settings.theme==='light'?'#ffffff':'#101010');
    const fg=settings.colors.text??(settings.theme==='light'?'#111827':'#e5ebf4');
    const ansi=(hex:string,code:number)=>'\x1b['+code+';2;'+[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)).join(';')+'m';
    const background=ansi(bg,48),foreground=ansi(fg,38),style=background+foreground+text;
    return lines.map(line=>style+line.replaceAll('\x1b[0m','\x1b[0m'+style)
      .replaceAll('\x1b[39m','\x1b[39m'+foreground).replaceAll('\x1b[49m','\x1b[49m'+background)
      +(background?' '.repeat(Math.max(0,width-visibleWidth(line))):'')+'\x1b[0m');
  }
  override render(width:number) {
    const enabled=this.#enabled(),wide=enabled&&width>=110;
    this.#wide=wide;
    const side=wide?Math.min(42,Math.floor(width*.32)):0;
    this.#left=wide?width-side-3:width;
    const left=this.#body.render(Math.max(1,this.#left));
    if(!enabled){this.#offset=0;return this.#style(left,width);}
    if(!wide){this.#offset=0;return this.#style([...left,...this.#sidebar(width).filter(Boolean).slice(0,3).map(s=>truncateToWidth(s,width,'…'))],width);}
    const right=this.#sidebar(side),height=Math.max(left.length,right.length);
    this.#height=height;
    this.#offset=height-left.length;
    return this.#style(Array.from({length:height},(_,i)=>{
      const text=left[i-this.#offset]??'',rhs=right[i-(height-right.length)]??'';
      return text+' '.repeat(Math.max(0,this.#left-visibleWidth(text)))+' │ '+rhs;
    }),width);
  }
  override invalidate(){this.#body.invalidate();}
  override handleMouse(event:TuiMouseEvent) {
    if(this.#wide&&event.type==='click'&&event.button==='left'&&event.y===this.#height-1&&event.x>=this.#left+3&&event.x<this.#left+27) {
      const column=event.x-this.#left-3;
      this.#action?.(column<10?'settings':column<17?'flow':'stop');
      return {handled:true as const,target:{component:this,originX:0,originY:0,width:event.width,height:event.height}};
    }
    if(event.x>=this.#left||event.y<this.#offset)return;
    const result=this.#body.handleMouse({...event,y:event.y-this.#offset,width:this.#left,height:event.height-this.#offset});
    if(result)result.target.originY+=this.#offset;
    return result;
  }
}
