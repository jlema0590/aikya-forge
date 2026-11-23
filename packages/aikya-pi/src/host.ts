import { canonicalPath } from "./project.ts";
import { execFile } from "node:child_process";

type Operation = "skills.remove-preview" | "skills.remove" | "skills.remove-recovery-preview" | "skills.remove-recover" | "skills.manage-preview" | "skills.manage-apply" | "skills.manage-status" | "skills.source-resolve" | "skills.fetch-preview" | "skills.fetch" | "skills.change-preview" | "task.review-checkpoint" | "task.preview" | "task.start" | "task.status" | "task.guard" | "task.phase" | "task.stop" | "task.resume-preview" | "task.resume" | "task.correct" | "task.completion-preview" | "task.complete" | "task.recovery-preview" | "task.recover" | "batch.recovery-preview" | "batch.recover" | "documentation.recovery-preview" | "documentation.recover" | "engineering.preview" | "engineering.apply" | "bootstrap.preview" | "bootstrap.apply" | "scaffold.preview" | "scaffold.apply" | "scaffold.inspect" | "scaffold.status" | "scaffold.cancel" | "infra-validation.preview" | "infra-validation.apply" | "infra-validation.cancel" | "documentation.catalog" | "documentation.preview" | "documentation.apply" | "workflow.answers-preview" | "diagnostics.doctor" | "diagnostics.quality" | "skills.preview" | "skills.apply" | "skills.resolve" | "skills.verify" | "skills.status" | "odd.preview" | "odd.apply" | "odd.status" | "review.context" | "review.request" | "review.admit" | "workflow.choices" | "workflow.preview" | "workflow.apply" | "workflow.bind" | "sdd.preview" | "sdd.apply" | "sdd.status" | "memory.event" | "migration.preview" | "migration.apply" | "migration.rollback-preview" | "migration.rollback" | "checks.snapshot-preview" | "checks.snapshot" | "checks.run-preview" | "checks.run" | "checks.cancel" | "checks.status" | "checks.recovery-preview" | "checks.recover" | "checks.review-preview" | "checks.refresh-preview" | "checks.iteration-preview" | "checks.iteration";
type FailureCategory='cancelled'|'timeout'|'output_limit'|'unavailable'|'invalid_response'|'refused';
type HostDiagnostic={category:string;stage:string|null};
export class HostOperationError extends Error {
  readonly operation:Operation;
  readonly category:FailureCategory;
  readonly diagnostic?:HostDiagnostic;
  constructor(operation:Operation,category:FailureCategory,diagnostic?:unknown) {
    super('Aikya host operation '+category+' ('+operation+')');
    this.name='HostOperationError';this.operation=operation;this.category=category;
    const item=diagnostic as Record<string,unknown>|null;
    if(item&&!Array.isArray(item)&&typeof item.category==='string'
      &&['filesystem_permission','filesystem_conflict','filesystem_unavailable','invalid_request','policy_refused'].includes(item.category)
      &&(item.stage===null||typeof item.stage==='string'&&/^aikya\.[A-Za-z0-9_.]{1,234}$/.test(item.stage)))
      this.diagnostic={category:String(item.category),stage:item.stage as string|null};
  }
}
export function hostFailure(error:unknown) {
  return error instanceof HostOperationError
    ? {host_failure:{operation:error.operation,category:error.category,...(error.diagnostic?{diagnostic:error.diagnostic}:{})}}
    : {};
}

export async function hostOperation(root: string, action: Operation, args: Record<string, unknown>, python = "python3", signal?:AbortSignal) {
  const project = canonicalPath(root);
  const raw = await new Promise<string>((resolve,reject) => {
    const child = execFile(python,["-I","-B","-m","aikya.services.runtime_state","--root",project],
      {cwd:project,signal,timeout:action==="skills.fetch"?75000:action==="skills.source-resolve"?35000:(action==="checks.run"||action==="checks.iteration"||action==="scaffold.apply"||action==="infra-validation.apply")?380000:10000,maxBuffer:65536,windowsHide:true},
      (error,stdout) => {
        if(!error) {resolve(stdout);return;}
        const category=signal?.aborted?'cancelled':error.code==='ERR_CHILD_PROCESS_STDIO_MAXBUFFER'?'output_limit':error.killed?'timeout':'unavailable';
        reject(new HostOperationError(action,category));
      });
    child.stdin?.on("error",()=>{});
    child.stdin?.end(JSON.stringify({action,arguments:args}));
  });
  let value;
  try {value=JSON.parse(raw);}catch {throw new HostOperationError(action,'invalid_response');}
  if (value?.ok!==true || value.project!==project || !value.result || typeof value.result!=="object" || Array.isArray(value.result)) {
    throw new HostOperationError(action,'refused',value?.diagnostic);
  }
  return value.result as Record<string,unknown>;
}
