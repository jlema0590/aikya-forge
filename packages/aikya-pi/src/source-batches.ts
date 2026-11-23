import type {ExtensionCommandContext} from '@earendil-works/pi-coding-agent';
import {WriteAuthority,type BatchIntent} from './permissions.ts';
import {callBridge} from './bridge.ts';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';

export async function editSources(root:string,input:Record<string,unknown>,ctx:ExtensionCommandContext,python?:string) {
  if(Object.keys(input).sort().join(',')!=='action,change_id,operations')throw new Error('Expected edit action, change_id and operations');
  const {action:_,...intent}=input;
  if(!ctx.hasUI) {
    const preview=await callBridge(root,'batch-preview',{python,arguments:{intent,session:ctx.sessionManager.getSessionId()}});
    return {status:'confirmation_required',review:preview};
  }
  const authority=new WriteAuthority(root,ctx.sessionManager.getSessionId(),python);
  return authority.batch(intent as BatchIntent,preview=>confirmOperation(ctx,'Apply this exact scoped source batch?',preview));
}

export async function recoverSourceBatch(root:string,ctx:ExtensionCommandContext,python?:string) {
  const value=await hostOperation(root,'batch.recovery-preview',{session_id:ctx.sessionManager.getSessionId()},python);
  if(!value.plan)return value;
  if(!ctx.hasUI)return {status:'confirmation_required',review:value.review};
  if(await confirmOperation(ctx,'Reconcile this source batch without replay?',value.review)!==true)return {status:'declined'};
  return hostOperation(root,'batch.recover',{plan:value.plan,approved:true},python);
}
