import { execFile } from "node:child_process";
import { realpathSync } from "node:fs";

type Operation = "skills.manage-preview" | "skills.manage-apply" | "skills.manage-status" | "skills.source-resolve" | "skills.fetch-preview" | "skills.fetch" | "skills.change-preview" | "task.review-checkpoint" | "task.preview" | "task.start" | "task.status" | "task.guard" | "task.phase" | "task.stop" | "task.resume-preview" | "task.resume" | "task.correct" | "task.completion-preview" | "task.complete" | "task.recovery-preview" | "task.recover" | "batch.recovery-preview" | "batch.recover" | "documentation.recovery-preview" | "documentation.recover" | "engineering.preview" | "engineering.apply" | "bootstrap.preview" | "bootstrap.apply" | "scaffold.preview" | "scaffold.apply" | "scaffold.inspect" | "scaffold.status" | "scaffold.cancel" | "infra-validation.preview" | "infra-validation.apply" | "infra-validation.cancel" | "documentation.catalog" | "documentation.preview" | "documentation.apply" | "workflow.answers-preview" | "diagnostics.doctor" | "diagnostics.quality" | "skills.preview" | "skills.apply" | "skills.resolve" | "skills.verify" | "skills.status" | "odd.preview" | "odd.apply" | "odd.status" | "review.context" | "review.request" | "review.admit" | "workflow.choices" | "workflow.preview" | "workflow.apply" | "workflow.bind" | "sdd.preview" | "sdd.apply" | "sdd.status" | "memory.event" | "migration.preview" | "migration.apply" | "migration.rollback-preview" | "migration.rollback" | "checks.snapshot-preview" | "checks.snapshot" | "checks.run-preview" | "checks.run" | "checks.cancel" | "checks.status" | "checks.recovery-preview" | "checks.recover" | "checks.review-preview" | "checks.refresh-preview" | "checks.iteration-preview" | "checks.iteration";
export async function hostOperation(root: string, action: Operation, args: Record<string, unknown>, python = "python3", signal?:AbortSignal) {
  const project = realpathSync(root);
  const raw = await new Promise<string>((resolve,reject) => {
    const child = execFile(python,["-I","-B","-m","aikya.services.runtime_state","--root",project],
      {cwd:project,signal,timeout:action==="skills.fetch"?75000:action==="skills.source-resolve"?35000:(action==="checks.run"||action==="checks.iteration"||action==="scaffold.apply"||action==="infra-validation.apply")?380000:10000,maxBuffer:65536,windowsHide:true},
      (error,stdout) => error ? reject(new Error("Aikya host operation unavailable")) : resolve(stdout));
    child.stdin?.on("error",()=>{});
    child.stdin?.end(JSON.stringify({action,arguments:args}));
  });
  const value=JSON.parse(raw);
  if (value?.ok!==true || value.project!==project || !value.result || typeof value.result!=="object" || Array.isArray(value.result)) {
    throw new Error("Aikya host operation refused");
  }
  return value.result as Record<string,unknown>;
}
