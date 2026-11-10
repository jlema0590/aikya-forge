import { lstatSync,readFileSync,writeFileSync,realpathSync } from 'node:fs';
import { join } from 'node:path';
import type { SessionManager } from '@earendil-works/pi-coding-agent';
import { projectDirectory } from './project.ts';
export type SessionRole='author'|'reviewer';

export function readSessionRole(root:string,id:string):SessionRole|undefined {
  if(!/^[A-Za-z0-9_-]{1,80}$/.test(id))throw new Error('Invalid session role identity');
  const path=join(projectDirectory(root,['.aikya','pi','session-roles']),id+'.json');
  let stat;
  try {stat=lstatSync(path);} catch(error) {if((error as NodeJS.ErrnoException).code==='ENOENT')return;throw error;}
  if(!stat.isFile()||stat.isSymbolicLink()||stat.size>16000)throw new Error('Unsafe session role record');
  const value=JSON.parse(readFileSync(path,'utf8'));
  if(!value||Object.keys(value).sort().join(',')!=='project,role,schema,session'||value.schema!==1
      ||value.project!==realpathSync(root)||value.session!==id||!['author','reviewer'].includes(value.role))throw new Error('Unknown session role record is preserved');
  return value.role;
}

export function claimSessionRole(root:string,manager:SessionManager,role:SessionRole) {
  if(!['author','reviewer'].includes(role))throw new Error('Unsupported session role');
  const id=manager.getSessionId(),old=readSessionRole(root,id);
  if(old!==undefined) {if(old!==role)throw new Error('Session role cannot change during resumption');return;}
  if(manager.getEntries().length)throw new Error('Existing session has no verified role; reviewed adoption is required');
  const path=join(projectDirectory(root,['.aikya','pi','session-roles']),id+'.json');
  try {writeFileSync(path,JSON.stringify({schema:1,project:realpathSync(root),session:id,role})+'\n',{flag:'wx',mode:0o600});}
  catch(error) {if((error as NodeJS.ErrnoException).code!=='EEXIST'||readSessionRole(root,id)!==role)throw error;}
}
