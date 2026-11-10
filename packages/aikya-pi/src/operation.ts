import type { ExtensionContext } from '@earendil-works/pi-coding-agent';
import { matchesKey,Key,truncateToWidth } from '@earendil-works/pi-tui';

/** Keep an approved operation visible until execution/cancellation has settled. */
export async function runOperation<T>(ctx:ExtensionContext,title:string,work:(signal:AbortSignal)=>Promise<T>,parent?:AbortSignal):Promise<T> {
  if(!ctx.hasUI)throw new Error('Interactive operation context required');
  const outcome=await ctx.ui.custom<{ok:true;value:T}|{ok:false}>((tui,theme,_keys,done)=>{
    const controller=new AbortController();let finished=false;
    const abort=()=>{controller.abort();tui.requestRender();};
    parent?.addEventListener('abort',abort,{once:true});if(parent?.aborted)abort();
    void Promise.resolve().then(()=>work(controller.signal)).then(value=>{finished=true;done({ok:true,value});},()=>{finished=true;done({ok:false});})
      .finally(()=>parent?.removeEventListener('abort',abort));
    return {render:(width:number)=>[theme.fg('accent',truncateToWidth(title,width)),
      theme.fg('muted',truncateToWidth(controller.signal.aborted?'Cancelling · waiting for the observed result':'Running · Esc/Ctrl+C: cancel',width))],
      handleInput:(data:string)=>{if(matchesKey(data,Key.escape)||matchesKey(data,Key.ctrl('c')))abort();},
      invalidate:()=>{},dispose:()=>{if(!finished)abort();}};
  });
  if(!outcome.ok)throw new Error('Operation did not produce a verified result; inspect its state before retrying');
  return outcome.value;
}
