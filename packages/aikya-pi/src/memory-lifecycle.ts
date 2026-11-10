import type { AgentSession,ExtensionAPI,ExtensionContext } from '@earendil-works/pi-coding-agent';
import { hostOperation } from './host.ts';

export async function memoryLease(root:string,session:string,event:'start'|'activity'|'end',python?:string) {
  return hostOperation(root,'memory.event',{session,event},python);
}

export class LocalMemoryLease {
  #root:string; #session:string; #python?:string; #interval:number; #closed=true;
  #timer?:ReturnType<typeof setInterval>; #pending?:Promise<unknown>;
  constructor(root:string,session:string,python?:string,interval=60000) {
    if(!Number.isSafeInteger(interval)||interval<10)throw new Error('Invalid local heartbeat interval');
    this.#root=root;this.#session=session;this.#python=python;this.#interval=interval;
  }
  async #touch(event:'start'|'activity') {
    if(this.#closed)return;
    if(this.#pending)return this.#pending;
    const request=memoryLease(this.#root,this.#session,event,this.#python);this.#pending=request;
    try {return await request;} finally {if(this.#pending===request)this.#pending=undefined;}
  }
  async start() {
    if(!this.#closed)return;
    this.#closed=false;
    try {await this.#touch('start');}
    finally {if(!this.#closed)this.#timer=setInterval(()=>{void this.renew().catch(()=>{});},this.#interval).unref();}
  }
  async renew() {return this.#touch('activity');}
  async stop() {
    if(this.#closed)return;
    this.#closed=true;clearInterval(this.#timer);
    await this.#pending?.catch(()=>{});
    await memoryLease(this.#root,this.#session,'end',this.#python);
  }
}

export function registerMemoryLifecycle(pi:ExtensionAPI,root:string,python?:string) {
  let owner:LocalMemoryLease|undefined;
  const observe=async(action:()=>Promise<unknown>,ctx:ExtensionContext)=>{
    try {await action();}
    catch {if(ctx.hasUI)ctx.ui.notify('Local memory observer unavailable; source and workflow permissions are unchanged','warning');}
  };
  pi.on('session_start',async(_event,ctx)=>{
    if(owner)await observe(()=>owner!.stop(),ctx);
    owner=new LocalMemoryLease(root,ctx.sessionManager.getSessionId(),python);
    await observe(()=>owner!.start(),ctx);
  });
  pi.on('before_agent_start',async(_event,ctx)=>{if(owner)await observe(()=>owner!.renew(),ctx);});
  pi.on('session_shutdown',async(_event,ctx)=>{if(owner)await observe(()=>owner!.stop(),ctx);owner=undefined;});
}

/** Headless SDK consumers must await teardown; interactive runtime owns this itself. */
export async function closeSession(session:AgentSession) {
  try {
    await session.abort();
    await session.extensionRunner.emit({type:'session_shutdown',reason:'quit'});
  } finally {session.dispose();}
}
