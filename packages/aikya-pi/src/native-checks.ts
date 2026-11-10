import { randomUUID } from 'node:crypto';
import type { ExtensionAPI,ExtensionContext,ExtensionCommandContext } from '@earendil-works/pi-coding-agent';
import { hostOperation } from './host.ts';
import { confirmOperation } from './confirmation.ts';
import { runOperation } from './operation.ts';
import { RuntimeBudget } from './usage.ts';
import {recoverSourceBatch} from './source-batches.ts';

type Input=Record<string,unknown>;
function input(args:string):Input {
  const value=JSON.parse(args);
  if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Expected explicit workflow JSON');
  return value;
}
function fields(value:Input,allowed:string[]) {
  if(Object.keys(value).some(key=>!allowed.includes(key)))throw new Error('Unexpected workflow field');
}

export async function runApprovedCheck(root:string,changeId:string,check:string,ctx:ExtensionContext,python?:string,signal?:AbortSignal) {
  const runId=randomUUID(),session=ctx.sessionManager.getSessionId();
  const plan=await hostOperation(root,'checks.iteration-preview',{change_id:changeId,check,session_id:session,run_id:runId},python);
  if(!ctx.hasUI)return {status:'confirmation_required',change_id:changeId,check,candidate:plan.candidate};
  if(signal?.aborted||await confirmOperation(ctx,'Execute this frozen check?',plan)!==true||signal?.aborted)return {status:'declined'};
  return runOperation(ctx,'validate · '+check,async active=>{
    if(active.aborted)return {status:'cancelled_before_launch',run_id:runId};
    let cancellation:Promise<unknown>|undefined;
    const cancel=()=>{cancellation=hostOperation(root,'checks.cancel',{change_id:changeId,session_id:session,run_id:runId,candidate:plan.candidate},python).catch(()=>undefined);};
    active.addEventListener('abort',cancel,{once:true});
    try {return await hostOperation(root,'checks.iteration',{plan,approved:true},python);}
    catch {return {status:'unverified',change_id:changeId,run_id:runId,diagnostic:'Execution result unavailable; inspect status/recovery before retrying'};}
    finally {active.removeEventListener('abort',cancel);await cancellation;}
  },signal);
}

async function snapshot(root:string,value:Input,ctx:ExtensionCommandContext,python?:string) {
  const action=value.action;
  fields(value,action==='refresh'?['action','change_id']:['action','change_id','scope','definitions','objective','acceptance','tdd_paths','not_applicable','change_kind','baseline_paths']);
  const {action:_action,...args}=value;
  const plan=action==='refresh'?await hostOperation(root,'checks.refresh-preview',{change_id:value.change_id,session_id:ctx.sessionManager.getSessionId()},python)
    :await hostOperation(root,'checks.snapshot-preview',{...args,session_id:ctx.sessionManager.getSessionId()},python);
  if(!ctx.hasUI)return {status:'confirmation_required',candidate:plan.candidate,change_id:value.change_id};
  if(await confirmOperation(ctx,'Freeze this scope, intent and check policy?',plan)!==true)return {status:'declined'};
  return hostOperation(root,'checks.snapshot',{plan,approved:true},python);
}

async function recover(root:string,value:Input,ctx:ExtensionCommandContext,python?:string) {
  fields(value,['action','change_id','run_id']);
  const plan=await hostOperation(root,'checks.recovery-preview',{change_id:value.change_id,run_id:value.run_id,session_id:ctx.sessionManager.getSessionId()},python);
  if(!ctx.hasUI)return {status:'confirmation_required',run_id:value.run_id};
  if(await confirmOperation(ctx,'Attach this known observation without executing again?',plan)!==true)return {status:'declined'};
  return hostOperation(root,'checks.recover',{plan,approved:true},python);
}

async function review(root:string,value:Input,ctx:ExtensionCommandContext,controlled:boolean,python?:string) {
  fields(value,['action','change_id']);
  if(!ctx.hasUI)return {status:'interactive_terminal_required'};
  if(!controlled||!ctx.model)return {status:'explicit_provider_model_required'};
  const budget=await new RuntimeBudget(root,python).status();
  if(budget.status!=='available')return {status:budget.status,diagnostic:'An available project budget is required for reviewer inference'};
  const plan=await hostOperation(root,'checks.review-preview',{change_id:value.change_id,session_id:ctx.sessionManager.getSessionId()},python);
  const model=ctx.model;
  if(await confirmOperation(ctx,'Run an independent budgeted reviewer?',{...plan,provider:model.provider,model:model.id,budget})!==true)return {status:'declined'};
  const {performReview}=await import('./review.ts');
  return runOperation(ctx,'review · independent candidate review',signal=>performReview(root,String(value.change_id),
    {python,provider:model.provider,model:model.id,expectedCandidate:plan.candidate as string,approved:true,signal}));
}

export function registerNativeChecks(pi:ExtensionAPI,root:string,python?:string,controlled=false,phase={value:'explore'},refreshUsage=async()=>{}) {
  for(const command of ['aikya-tests','aikya-verify'])pi.registerCommand(command,{
    description:command==='aikya-tests'?'Freeze/refresh/run explicit checks or inspect status using JSON':'Inspect current evidence, reconcile known execution or run an independent reviewer using JSON',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(value),display:true});
      if(!args.trim()) {publish({status:'input_required',required:'change_id',actions:command==='aikya-tests'?['snapshot','refresh','run','status']:['status','review','recover','recover-batch']});return;}
      const value=input(args),action=value.action??'status';
      if(command==='aikya-verify'&&action==='recover-batch') {
        fields(value,['action']);publish(await recoverSourceBatch(root,ctx,python));return;
      }
      if(typeof value.change_id!=='string')throw new Error('A change_id is required');
      let result:unknown;
      if(action==='status') {fields(value,['action','change_id']);result=await hostOperation(root,'checks.status',{change_id:value.change_id},python);}
      else if(command==='aikya-tests'&&(action==='snapshot'||action==='refresh'))result=await snapshot(root,value,ctx,python);
      else if(command==='aikya-tests'&&action==='run') {
        fields(value,['action','change_id','check']);if(typeof value.check!=='string')throw new Error('A frozen check name is required');
        if(ctx.hasUI)phase.value='validate';result=await runApprovedCheck(root,value.change_id,value.check,ctx,python);
      } else if(command==='aikya-verify'&&action==='recover')result=await recover(root,value,ctx,python);
      else if(command==='aikya-verify'&&action==='review') {if(ctx.hasUI)phase.value='review';result=await review(root,value,ctx,controlled,python);}
      else throw new Error('Unsupported workflow action');
      await refreshUsage();publish(result);
    }});
}
