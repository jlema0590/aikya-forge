import {readFileSync} from 'node:fs';
import {rm} from 'node:fs/promises';
import {join} from 'node:path';

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
    if(Date.now()>=deadline)throw new Error('The fixture observer did not stop after its final lease closed');
    await new Promise(resolve=>setTimeout(resolve,50));
  }
  await rm(root,{recursive:true,force:true,maxRetries:10,retryDelay:100});
}
