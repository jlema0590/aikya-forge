import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';

/** Canonical documentation is a confirmed host action, never a model tool. */
export function registerDocumentation(pi:ExtensionAPI,root:string,python?:string) {
  for(const command of ['aikya-docs','aikya-docs-sync'])pi.registerCommand(command,{
    description:command==='aikya-docs'?'Inspect templates or record reviewed living documents with native confirmation':'Capture selected source baselines and synchronize reviewed documents/REQ records after observed changes',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(value),display:true});
      if(!args.trim()&&command==='aikya-docs-sync') {publish({status:'input_required',actions:['baseline','sync'],checks:'not_run'});return;}
      const input=args.trim()?JSON.parse(args):{action:'catalog'};
      if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Explicit documentation JSON required');
      if(input.action==='recover') {
        if(Object.keys(input).some(k=>k!=='action'))throw new Error('Recovery uses the current host session');
        const value=await hostOperation(root,'documentation.recovery-preview',{session_id:ctx.sessionManager.getSessionId()},python);
        if(!value.plan) {publish(value);return;}
        if(!ctx.hasUI) {publish({status:'confirmation_required',review:value.review});return;}
        if(await confirmOperation(ctx,'Reconcile these observed effects without replay?',value.review)!==true) {publish({status:'declined'});return;}
        publish(await hostOperation(root,'documentation.recover',{plan:value.plan,approved:true},python));return;
      }
      if(command==='aikya-docs'&&input.action==='catalog') {
        if(Object.keys(input).some(k=>!['action','document'].includes(k)))throw new Error('Choose an optional document');
        publish(await hostOperation(root,'documentation.catalog',input.document===undefined?{}:{document:input.document},python));return;
      }
      const value=await hostOperation(root,'documentation.preview',{command,input_data:input,session_id:ctx.sessionManager.getSessionId()},python);
      if(!value.plan) {publish(value);return;}
      if(!ctx.hasUI) {publish({status:'confirmation_required',review:value.review});return;}
      if(await confirmOperation(ctx,'Apply '+command+'?',value.review)!==true) {publish({status:'declined'});return;}
      publish(await hostOperation(root,'documentation.apply',{plan:value.plan,approved:true},python));
    }});
}
