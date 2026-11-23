import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';

/** Explicit native metadata/evidence; execution remains in the existing guarded tools. */
export function registerEngineeringWorkflows(pi:ExtensionAPI,root:string,python?:string) {
  const descriptions={
    'aikya-arc-review':'Inspect selected source or confirm static architecture interpretations anchored to exact excerpts',
    'aikya-bugfix':'Inspect native regression evidence or confirm an append-only canonical bug report',
    'aikya-mobile-feature':'Plan selected mobile platforms and confirm canonical ODD/approved SDD task metadata; SDK presence is not acceptance',
  };
  for(const command of Object.keys(descriptions) as (keyof typeof descriptions)[])pi.registerCommand(command,{
    description:descriptions[command],handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(value),display:true});
      if(!args.trim()&&command!=='aikya-bugfix') {
        publish({status:'input_required',actions:command==='aikya-arc-review'?['inspect','record']:['plan','create','bind','status','complete'],
          required:command==='aikya-arc-review'?'Explicit source paths and query/findings':'Explicit platforms inside the recorded profile; ODD create/complete or approved SDD binding',execution:'not_run'});return;
      }
      const value=args.trim()?JSON.parse(args):{action:'status'};
      if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Explicit engineering JSON required');
      const result=await hostOperation(root,'engineering.preview',{command,input_data:value,session_id:ctx.sessionManager.getSessionId()},python);
      if(!result.plan) {publish(result);return;}
      if(!ctx.hasUI) {publish({status:'confirmation_required',review:result.review});return;}
      if(await confirmOperation(ctx,'Confirm '+command+'?',result.review)!==true) {publish({status:'declined'});return;}
      publish(await hostOperation(root,'engineering.apply',{plan:result.plan,approved:true},python));
    }});
}
