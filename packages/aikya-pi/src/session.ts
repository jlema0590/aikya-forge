import { lstatSync,readdirSync,realpathSync,openSync,closeSync,readSync } from 'node:fs';
import { join } from 'node:path';
import { SessionManager } from '@earendil-works/pi-coding-agent';
import { projectDirectory } from './project.ts';
import { claimSessionRole,readSessionRole,type SessionRole } from './session-roles.ts';
export { projectDirectory } from './project.ts';

export function projectSession(root:string,resume:boolean,role:SessionRole='author'):SessionManager {
  if(!['author','reviewer'].includes(role))throw new Error('Unsupported session role');
  const project=realpathSync(root),directory=projectDirectory(project,['.aikya','pi','sessions']);
  if(!resume) {const manager=SessionManager.create(project,directory);claimSessionRole(project,manager,role);return manager;}
  const candidates:{file:string;mtime:number;size:number}[]=[];
  for(const name of readdirSync(directory)) {
    if(name.endsWith('.jsonl')) {
      const file=join(directory,name),stat=lstatSync(file);
      if(stat.isSymbolicLink())throw new Error('Symlinked session transcript');
      if(!stat.isFile())throw new Error('Invalid session transcript');
      if(candidates.length>=1000)throw new Error('Session history requires reviewed archival');
      candidates.push({file,mtime:stat.mtimeMs,size:stat.size});
    }
  }
  if(resume) {
    let bytes=0,unknown=false;
    for(const candidate of candidates.sort((a,b)=>b.mtime-a.mtime||b.file.localeCompare(a.file))) {
      bytes+=Math.min(candidate.size,16001);if(bytes>16001000)throw new Error('Session inspection exceeded its local bound');
      const fd=openSync(candidate.file,'r'),raw=Buffer.alloc(16001);let size=0;
      try {size=readSync(fd,raw,0,raw.length,0);} finally {closeSync(fd);}
      const end=raw.subarray(0,size).indexOf(10);
      if(end<0||end>16000)throw new Error('Invalid session header');
      const header=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw.subarray(0,end)));
      if(header?.type!=='session'||typeof header.id!=='string'||header.cwd!==project)throw new Error('Foreign session header');
      const known=readSessionRole(project,header.id);
      if(known===undefined) {unknown=true;continue;}
      if(known===role) {
        if(candidate.size>2000000)throw new Error('Large session transcript requires reviewed archival before resume');
        return SessionManager.open(candidate.file,directory);
      }
    }
    if(unknown)throw new Error('Legacy session roles require reviewed adoption');
  }
  const manager=SessionManager.create(project,directory);claimSessionRole(project,manager,role);return manager;
}
