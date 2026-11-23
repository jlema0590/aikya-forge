import type { ExtensionContext } from '@earendil-works/pi-coding-agent';
import { matchesKey, Key, wrapTextWithAnsi, truncateToWidth } from '@earendil-works/pi-tui';

/** Keep the decision controls visible even for a complete file replacement. */
export class ApprovalDialog {
  #offset=0; #last=0; #height=1; #rendered=false;
  private title:string; private body:string; private rows:()=>number; private done:(value:boolean)=>void;
  constructor(title:string,body:string,rows:()=>number,done:(value:boolean)=>void) {
    this.title=title;this.body=body;this.rows=rows;this.done=done;
  }
  render(width:number) {
    const safeWidth=Math.max(1,width);
    const lines=this.body.split('\n').flatMap(line=>wrapTextWithAnsi(line,safeWidth));
    this.#height=Math.max(1,Math.min(30,this.rows()-6));
    this.#last=Math.max(0,lines.length-this.#height);
    this.#offset=Math.min(this.#offset,this.#last);this.#rendered=true;
    return [truncateToWidth(this.title,safeWidth),...lines.slice(this.#offset,this.#offset+this.#height),
      truncateToWidth(this.#offset>=this.#last?'Enter: approve · Esc: cancel':'↑/↓/PgDown: review · End: bottom · Esc: cancel',safeWidth)];
  }
  handleInput(data:string) {
    if(matchesKey(data,Key.escape)) {this.done(false);return;}
    if(matchesKey(data,Key.enter)) {if(this.#rendered&&this.#offset>=this.#last)this.done(true);return;}
    if(matchesKey(data,Key.down)) this.#offset=Math.min(this.#last,this.#offset+1);
    if(matchesKey(data,Key.up)) this.#offset=Math.max(0,this.#offset-1);
    if(matchesKey(data,Key.pageDown)) this.#offset=Math.min(this.#last,this.#offset+this.#height);
    if(matchesKey(data,Key.pageUp)) this.#offset=Math.max(0,this.#offset-this.#height);
    if(matchesKey(data,Key.end)) this.#offset=this.#last;
    if(matchesKey(data,Key.home)) this.#offset=0;
  }
  invalidate() {}
}

export async function confirmOperation(ctx:ExtensionContext,title:string,value:unknown) {
  if(!ctx.hasUI) return false;
  return ctx.ui.custom<boolean>((tui,_theme,_keys,done)=>{
    const dialog=new ApprovalDialog(title,JSON.stringify(value,null,2),()=>tui.terminal.rows,done);
    return {render:(width:number)=>dialog.render(width),handleInput:(data:string)=>{dialog.handleInput(data);tui.requestRender();},invalidate:()=>dialog.invalidate()};
  });
}
