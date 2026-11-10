import {taskActions} from './task-run-policy.ts';
import type {TaskHandler} from './task-run.ts';
import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';

export function registerOddWorkflow(pi:ExtensionAPI,root:string,python?:string,phase={value:'explore'},task?:TaskHandler) {
  pi.registerCommand('aikya-feature',{description:'Prepare, select and record an ODD task using current independently reviewed evidence',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:'aikya-feature',content:JSON.stringify(value),display:true});
      if(!args.trim()) {publish({status:'input_required',actions:['create','status','bind','complete','reconcile','release',...taskActions]});return;}
      const value=JSON.parse(args);
      if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Explicit ODD workflow JSON required');
      if(task&&await task(value,ctx))return;
      const {action='status',...arguments_}=value;
      if(action==='status') {publish(await hostOperation(root,'odd.status',arguments_,python));return;}
      const plan=await hostOperation(root,'odd.preview',{action,arguments:arguments_,session_id:ctx.sessionManager.getSessionId()},python);
      if(!ctx.hasUI) {publish({status:'confirmation_required',action});return;}
      if(await confirmOperation(ctx,'Apply ODD '+action+'?',plan)!==true) {publish({status:'declined'});return;}
      const result=await hostOperation(root,'odd.apply',{plan,approved:true},python);
      phase.value=action==='create'||action==='reconcile'?'plan':action==='bind'?'implement':action==='complete'?'review':'explore';
      publish(result);
    }});
}
