import {readFileSync,openSync,readSync,closeSync} from 'node:fs';
import {rm} from 'node:fs/promises';
import {join} from 'node:path';

function metadata(root:string,name:string) {
  try {
    const file=openSync(join(root,'.harness/state/memory-view',name),'r');
    try {
      const buffer=Buffer.alloc(16001),length=readSync(file,buffer,0,buffer.length,0);
      return length<=16000?JSON.parse(buffer.subarray(0,length).toString('utf8')):undefined;
    } finally {closeSync(file);}
  } catch {return undefined;}
}

/** Whitelist state and counts, never paths, session IDs, source or note content. */
function diagnostic(root:string) {
  const state=metadata(root,'status.json'),sessions=metadata(root,'sessions.json');
  return JSON.stringify({state:['Starting','Updating','Watching','Up to date','Partial','Stopped'].includes(state?.state)?state.state:'unavailable',
    pid:Number.isSafeInteger(state?.pid)&&state.pid>0?state.pid:null,
    active_sessions:sessions&&typeof sessions==='object'&&!Array.isArray(sessions)?Math.min(Object.keys(sessions).length,100):null});
}

/** Wait only for the observer owned by this disposable SDK fixture. */
export async function removeProject(root:string) {
  const deadline=Date.now()+10000;
  for(;;) {
    try {
      const state=JSON.parse(readFileSync(join(root,'.harness/state/memory-view/status.json'),'utf8'));
      if(state.state==='Stopped')break;
    } catch(error) {
      if((error as NodeJS.ErrnoException).code==='ENOENT')break;
      if(!['EPERM','EACCES'].includes((error as NodeJS.ErrnoException).code??''))throw error;
    }
    if(Date.now()>=deadline)throw new Error('The fixture observer did not stop after its final lease closed; '+diagnostic(root));
    await new Promise(resolve=>setTimeout(resolve,50));
  }
  await rm(root,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
