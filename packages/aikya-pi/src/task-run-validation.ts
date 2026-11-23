import type {ExtensionContext} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {runApprovedCheck} from './native-checks.ts';
import {confirmOperation} from './confirmation.ts';
import {runOperation} from './operation.ts';
import {performReview} from './review.ts';
import type {TaskState,ReviewRuntimeFactory} from './task-run-policy.ts';

/** Local processes and independent inference retain distinct native confirmations. */
export async function validateTask(root:string,change:string,state:TaskState,ctx:ExtensionContext,
  phase:(value:string)=>Promise<void>,python?:string,signal?:AbortSignal,reviewRuntime?:ReviewRuntimeFactory) {
  await phase('validate');
  for(const name of state.selection.checks.filter(n=>!state.security.checks.includes(n))) {
    const result=await runApprovedCheck(root,change,name,ctx,python,signal);
    if(result.status!=='completed')throw new Error('Frozen validation did not complete positively');
  }
  await phase('security');
  for(const name of state.security.checks) {
    const result=await runApprovedCheck(root,change,name,ctx,python,signal);
    if(result.status!=='completed')throw new Error('Configured security check did not complete positively');
  }
  const assessment=await hostOperation(root,'checks.status',{change_id:change},python);
  if(assessment.status!=='review_required')throw new Error('Current validation and methodology evidence are required');
  await phase('review');
  const plan=await hostOperation(root,'checks.review-preview',{change_id:change,session_id:ctx.sessionManager.getSessionId()},python);
  if(!ctx.model||signal?.aborted||await confirmOperation(ctx,'Run independent budgeted task review?',{
    ...plan,provider:ctx.model.provider,model:ctx.model.id,security:state.security})!==true||signal?.aborted)throw new Error('Independent review declined or interrupted');
  const models=reviewRuntime?await reviewRuntime():undefined;
  return runOperation(ctx,'review · independent task acceptance',active=>performReview(root,change,{
    python,provider:ctx.model!.provider,model:ctx.model!.id,expectedCandidate:String(plan.candidate),approved:true,
    signal:active,modelRuntime:models,securityContext:state.security}),signal);
}
