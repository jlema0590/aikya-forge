import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';
import { Type } from 'typebox';
import { runApprovedCheck } from './native-checks.ts';

export function registerCheckTool(pi:ExtensionAPI,root:string,python?:string) {
  const identifier=()=>Type.String({minLength:1,maxLength:80,pattern:'^[A-Za-z0-9][A-Za-z0-9_-]*$'});
  pi.registerTool({name:'aikya_check',label:'Approved frozen check',
    description:'Execute only an existing author-owned frozen check. A fresh scoped snapshot and host confirmation are required; arbitrary command arguments are unavailable.',
    parameters:Type.Object({change_id:identifier(),check:identifier()},{additionalProperties:false}),
    execute:async(_id,args,signal,_update,ctx)=>{
      let result:Record<string,unknown>;
      if(signal?.aborted||!ctx.hasUI)result={status:'declined',needs_host_action:true,diagnostic:'An interactive host must confirm frozen check execution'};
      else {
        try {result=await runApprovedCheck(root,args.change_id,args.check,ctx,python,signal);}
        catch {result={status:'unverified',needs_host_action:true,change_id:args.change_id,check:args.check,
          diagnostic:'Inspect scope, frozen policy and existing execution state with /aikya-tests or /aikya-verify before retrying'};}
      }
      return {content:[{type:'text',text:JSON.stringify(result)}],details:result};
    }});
}
