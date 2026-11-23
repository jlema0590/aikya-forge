import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { confirmOperation } from './confirmation.ts';
import { hostOperation } from './host.ts';
import { memoryLease } from './memory-lifecycle.ts';

export function registerMigration(pi:ExtensionAPI,root:string,python?:string) {
  pi.registerCommand('aikya-migrate',{description:'Preview legacy profile adoption or guarded rollback; explicit methodology or rollback JSON',
    handler:async(args,ctx)=>{
      let input:Record<string,unknown>;
      if(args.trim()) input=JSON.parse(args);
      else {
        if(!ctx.hasUI)throw new Error('Explicit migration methodology or rollback ID required');
        const method=await ctx.ui.select('Preserve the existing engineering methodology',['odd','sdd']);
        if(!method)return;input={methodology:method};
      }
      if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Expected migration JSON');
      const fields=Object.keys(input).join(','),undo=fields==='rollback';
      if(fields!=='methodology'&&!undo)throw new Error('Choose methodology or rollback');
      const preview=undo?await hostOperation(root,'migration.rollback-preview',{ident:input.rollback},python)
        :await hostOperation(root,'migration.preview',{methodology:input.methodology},python);
      const publish=(result:unknown)=>pi.sendMessage({customType:'aikya-migrate',content:JSON.stringify(result),display:true});
      if(!ctx.hasUI) {publish({status:'confirmation_required',preview});return;}
      if(await confirmOperation(ctx,undo?'Restore original project metadata?':'Adopt this project profile for Pi?',preview)!==true) {publish({status:'declined'});return;}
      const result=undo?await hostOperation(root,'migration.rollback',{ident:input.rollback,approved:true},python)
        :await hostOperation(root,'migration.apply',{plan:preview,approved:true},python);
      publish(result);
      if(undo) {ctx.shutdown();return;}
      try {await memoryLease(root,ctx.sessionManager.getSessionId(),'start',python);}
      catch {ctx.ui.notify('Profile migrated; local memory observer is unavailable','warning');}
    }});
}
