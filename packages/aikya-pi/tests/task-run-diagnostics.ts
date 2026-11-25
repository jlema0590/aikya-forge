import {openSync,readSync,closeSync,lstatSync,readdirSync} from 'node:fs';
import {join} from 'node:path';

function record(path:string):Record<string,any>|undefined {
  try {
    if(lstatSync(path).isSymbolicLink())return;
    const file=openSync(path,'r');
    try {
      const buffer=Buffer.alloc(65537),length=readSync(file,buffer,0,buffer.length,0);
      if(length>65536)return;
      const value=JSON.parse(buffer.subarray(0,length).toString('utf8'));
      if(value&&typeof value==='object'&&!Array.isArray(value))return value;
    } finally {closeSync(file);}
  } catch {return;}
}
const number=(value:unknown)=>Number.isSafeInteger(value)?value as number:null;
const word=(value:unknown,allowed:readonly string[])=>typeof value==='string'&&allowed.includes(value)?value:null;
const executionStates=['pending','completed','failed','unverified','invalid_report','candidate_changed',
  'definition_changed','cancelled','timed_out','launch_failed','output_limit'];

/** Diagnostic observations only: never used for admission, recovery or approval. */
export function taskFailureEvidence(root:string,runId:string) {
  const empty={task:null,checks:[]};
  if(!/^[a-f0-9]{32}$/.test(runId))return empty;
  const checkpoint=record(join(root,'.aikya/pi/task-runs',runId+'.json'))?.payload;
  const task=checkpoint&&typeof checkpoint==='object'
    ? {status:word(checkpoint.status,['running','stopped','escalated','recorded']),
      phase:word(checkpoint.phase,['explore','plan','implement','validate','security','review'])}:null;
  const checks:Record<string,unknown>[]=[];
  const base=join(root,'aikya/docs/validation/task-proof/checks');
  try {
    for(const entry of readdirSync(base,{withFileTypes:true}).slice(0,20)) {
      if(!entry.isDirectory()||entry.isSymbolicLink()||!/^[A-Za-z0-9-]{1,80}$/.test(entry.name))continue;
      const value=record(join(base,entry.name,'execution.json'));if(!value)continue;
      checks.push({status:word(value.status,executionStates),exit_code:number(value.exit_code),duration_ns:number(value.duration_ns),
        stdout_bytes:number(value.stdout_bytes),stderr_bytes:number(value.stderr_bytes),
        counts:value.counts&&typeof value.counts==='object'?{executed:number(value.counts.executed),
          failed:number(value.counts.failed),skipped:number(value.counts.skipped)}:null});
    }
  } catch { /* Preserve the original failure when evidence is unavailable. */ }
  return {task,checks};
}
