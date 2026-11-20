import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';

/** Explicit host administration only; packages are retained, never executed. */
export function registerSkillRemoval(pi:ExtensionAPI,root:string,python?:string) {
  pi.registerCommand('aikya-uninstall-skills',{
    description:'Preview and confirm scoped skill withdrawal, restore or known-operation recovery; retain exact packages',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:'aikya-uninstall-skills',content:JSON.stringify(value),display:true});
      if(!args.trim()) {publish({status:'input_required',actions:['remove','restore','recover'],scopes:['project','global'],selection:'names or all:true'});return;}
      const input:unknown=JSON.parse(args);
      if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Explicit skill removal JSON required');
      const value=input as Record<string,unknown>;
      if(Object.keys(value).some(k=>!['scope','action','names','all','operation_id'].includes(k)))throw new Error('Unexpected withdrawal field');
      const scope=value.scope==='local'?'project':value.scope??'project',action=value.action??'remove';
      if(!['project','global'].includes(String(scope))||!['remove','restore','recover'].includes(String(action)))throw new Error('Choose explicit scope and action');
      if(value.all!==undefined&&typeof value.all!=='boolean'||value.all===true&&value.names!==undefined)throw new Error('Select names or all, not both');
      if(action==='recover'&&(value.names!==undefined||value.all!==undefined||value.operation_id!==undefined))throw new Error('Recovery uses its pending operation');
      const preview=action==='recover'?await hostOperation(root,'skills.remove-recovery-preview',{scope},python):
        await hostOperation(root,'skills.remove-preview',{scope,action,names:value.all===true?'all':value.names,operation_id:value.operation_id},python);
      if(preview.plan===null) {publish({status:'no_op',review:preview.review});return;}
      if(!ctx.hasUI) {publish({status:'confirmation_required',review:preview.review});return;}
      if(await confirmOperation(ctx,'Confirm skill '+action+'?',preview.review)!==true) {publish({status:'declined'});return;}
      publish(await hostOperation(root,action==='recover'?'skills.remove-recover':'skills.remove',{plan:preview.plan,approved:true},python));
    }
  });
}
