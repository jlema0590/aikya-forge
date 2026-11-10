import type {ExtensionAPI,ExtensionContext,ExtensionCommandContext} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';
import {runApprovedCheck} from './native-checks.ts';
import {taskActions,taskPrompt,type TaskState,type TaskControl,type ReviewRuntimeFactory} from './task-run-policy.ts';
import {validateTask} from './task-run-validation.ts';

type Input=Record<string,unknown>;
export function registerTaskRun(pi:ExtensionAPI,root:string,python:string|undefined,controlled:boolean,
  phase:{value:string},control:TaskControl,reviewRuntime?:ReviewRuntimeFactory) {
  let current:{state:TaskState;change:string;session:string;abort:AbortController;timer:ReturnType<typeof setTimeout>}|undefined;
  const publish=(value:unknown)=>pi.sendMessage({customType:'aikya-task-run',content:JSON.stringify(value),display:true});
  async function stop(ctx:ExtensionContext,reason='needs_host_action',abortAgent=true) {
    const run=current;if(!run)return;
    current=undefined;clearTimeout(run.timer);run.abort.abort();control.blocked=true;if(abortAgent)ctx.abort();
    const result=await hostOperation(root,'task.stop',{run_id:run.state.run_id,session_id:run.session,reason},python);
    if(abortAgent)publish(result);return result;
  }
  async function advance(ctx:ExtensionContext,value:string) {
    const run=current;if(!run||run.abort.signal.aborted)throw new Error('Task was interrupted');
    await hostOperation(root,'task.phase',{run_id:run.state.run_id,session_id:run.session,phase:value},python);
    phase.value=value;if(ctx.hasUI)ctx.ui.setStatus('aikya',value+' · '+(ctx.model?.id??'model disabled'));
  }
  async function record(ctx:ExtensionContext) {
    const run=current;if(!run)throw new Error('Task is no longer active');
    const plan=await hostOperation(root,'task.completion-preview',{run_id:run.state.run_id,session_id:run.session},python);
    if(run.abort.signal.aborted||await confirmOperation(ctx,'Record independently accepted task completion?',plan)!==true||run.abort.signal.aborted) return stop(ctx,'declined',false);
    try {
      const completed=await hostOperation(root,'task.complete',{plan,approved:true},python);
      clearTimeout(run.timer);current=undefined;return completed;
    } catch {
      clearTimeout(run.timer);current=undefined;run.abort.abort();control.blocked=true;
      return {status:'needs_host_action',run_id:run.state.run_id,action:'recover-run',delivery_authorized:false};
    }
  }
  async function arm(ctx:ExtensionCommandContext,result:Input,change:string) {
    const session=ctx.sessionManager.getSessionId();
    const state=await hostOperation(root,'task.status',{session_id:session,run_id:result.run_id},python) as unknown as TaskState;
    const remaining=Number(BigInt(state.deadline_ns)-BigInt(Date.now())*1000000n)/1000000;
    const abort=new AbortController();
    const timer=setTimeout(()=>{void stop(ctx,'timeout').catch(()=>{control.blocked=true;ctx.abort();});},Math.max(0,Math.min(remaining,600000)));
    timer.unref();current={state,change,session,abort,timer};control.blocked=false;
    try {
      if(state.completion_ready) {await advance(ctx,'review');publish(await record(ctx));return;}
      await advance(ctx,'explore');await advance(ctx,'plan');
      for(const item of state.pre_checks) {
        await advance(ctx,'validate');
        const observed=await runApprovedCheck(root,change,item.check,ctx,python,abort.signal);
        if(observed.status!==item.expected)throw new Error('Required preimplementation evidence was not observed');
      }
      await advance(ctx,'implement');
      pi.sendUserMessage(taskPrompt(state),{deliverAs:'followUp',expandPromptTemplates:false});
    } catch {await stop(ctx);}
  }
  pi.on('agent_before_settle',async(event,ctx)=>{
    const run=current;if(!run)return;
    const report=(value:unknown)=>({entries:[...event.entries,{type:'custom_message' as const,customType:'aikya-task-run',content:JSON.stringify(value??{status:'needs_host_action'}),display:true}],continue:false});
    const last=event.context.contextMessages.findLast(m=>m.role==='assistant');
    if(event.outcome!=='completed'||!last||last.role!=='assistant'||last.stopReason!=='stop') return report(await stop(ctx,'needs_host_action',false));
    try {
      const result=await validateTask(root,run.change,run.state,ctx,value=>advance(ctx,value),python,run.abort.signal,reviewRuntime);
      if(current!==run||run.abort.signal.aborted)return;
      if(result.status==='changes_requested') {
        const correction=await hostOperation(root,'task.correct',{run_id:run.state.run_id,session_id:run.session},python);
        await advance(ctx,'implement');
        return {entries:[...event.entries,{type:'custom_message',customType:'aikya-task-correction',content:taskPrompt(run.state,correction.findings),display:true}],continue:true};
      }
      if(result.status!=='reviewed'||result.can_close!==true)throw new Error('Task review did not independently accept');
      await hostOperation(root,'task.review-checkpoint',{run_id:run.state.run_id,session_id:run.session},python);
      return report(await record(ctx));
    } catch {return report(await stop(ctx,'needs_host_action',false));}
  });
  pi.on('agent_settled',async(event,ctx)=>{if(event.aborted&&current)await stop(ctx,'user_stop');});
  pi.on('tool_call',async(event,ctx)=>{
    if(current&&event.toolName==='aikya_write'&&(!Array.isArray(event.input.operations)||event.input.change_id!==current.change)) {
      await stop(ctx,'needs_host_action');
      return {block:true,reason:'Use the current task change_id and a scoped batch with recoverable reservations'};
    }
  });
  pi.on('tool_result',async(event,ctx)=>{
    if(!current||!['aikya_write','aikya_check'].includes(event.toolName))return;
    const details=event.details as Input|undefined;
    const valid=event.toolName==='aikya_write'?'written':'completed';
    if(event.isError||details?.status!==valid)await stop(ctx,details?.status==='declined'?'declined':'needs_host_action');
  });
  pi.on('session_shutdown',async(_event,ctx)=>{if(current)await stop(ctx,'user_stop');});
  return async function handle(value:Input,ctx:ExtensionCommandContext):Promise<boolean> {
    const action=value.action;if(typeof action!=='string'||!taskActions.includes(action))return false;
    const session_id=ctx.sessionManager.getSessionId();
    if(action==='run-status') {publish(await hostOperation(root,'task.status',{session_id,...(value.run_id?{run_id:value.run_id}:{})},python));return true;}
    if(action==='stop-run') {
      if(current)await stop(ctx,'user_stop');
      else {const state=await hostOperation(root,'task.status',{session_id,...(value.run_id?{run_id:value.run_id}:{})},python);
        if(!state.run_id)publish(state);else {control.blocked=true;ctx.abort();publish(await hostOperation(root,'task.stop',{session_id,run_id:state.run_id,reason:'user_stop'},python));}}
      return true;
    }
    if(!ctx.hasUI) {publish({status:'confirmation_required',action});return true;}
    if(action==='recover-run') {
      const preview=await hostOperation(root,'task.recovery-preview',{session_id,run_id:value.run_id},python);
      if(!preview.plan) {publish(preview);return true;}
      if(await confirmOperation(ctx,'Reconcile known task completion without replay?',preview.review)!==true) {publish({status:'declined'});return true;}
      publish(await hostOperation(root,'task.recover',{plan:preview.plan,approved:true},python));return true;
    }
    if(!controlled||!ctx.model) {publish({status:'explicit_provider_model_required'});return true;}
    if(current)throw new Error('Stop the active task before changing run configuration');
    const model={provider:ctx.model.provider,model:ctx.model.id};
    const plan=action==='run'?await hostOperation(root,'task.preview',{change_id:value.change_id,session_id,...model,
      ...(value.limits?{limits:value.limits}:{}),security:value.security},python)
      :await hostOperation(root,'task.resume-preview',{run_id:value.run_id,session_id,...model},python);
    if(await confirmOperation(ctx,action==='run'?'Start bounded selected-task cycle?':'Resume original task limits?',plan)!==true) {publish({status:'declined'});return true;}
    const result=await hostOperation(root,action==='run'?'task.start':'task.resume',{plan,approved:true},python);
    publish(result);
    const state=await hostOperation(root,'task.status',{session_id,run_id:result.run_id},python);
    await arm(ctx,result,action==='run'?String(value.change_id):String((state as Input).change_id??(plan as Input).change_id??''));return true;
  };
}
export type TaskHandler=ReturnType<typeof registerTaskRun>;
