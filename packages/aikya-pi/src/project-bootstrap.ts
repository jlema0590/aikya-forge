import {randomUUID} from 'node:crypto';
import type {ExtensionAPI,ExtensionCommandContext} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';
import {runOperation} from './operation.ts';

type Input=Record<string,unknown>;
function input(args:string):Input {
  const value=JSON.parse(args);
  if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Explicit bootstrap JSON required');
  return value;
}

async function validation(root:string,value:Input,ctx:ExtensionCommandContext,python?:string) {
  if(Object.keys(value).some(key=>!['action','validator','run_id'].includes(key)))throw new Error('Unexpected validation input');
  const result=await hostOperation(root,'infra-validation.preview',{validator:value.validator,run_id:value.run_id??randomUUID(),session_id:ctx.sessionManager.getSessionId()},python);
  if(!result.plan)return result;
  if(!ctx.hasUI)return {status:'confirmation_required',review:result.review};
  if(await confirmOperation(ctx,'Execute this local validator?',result.review)!==true)return {status:'declined'};
  return runOperation(ctx,'validate · infrastructure',async signal=>{
    if(signal.aborted)return {status:'cancelled_before_launch'};
    let cancellation:Promise<unknown>|undefined;
    const cancel=()=>{cancellation=hostOperation(root,'infra-validation.cancel',{plan:result.plan},python).catch(()=>undefined);};
    signal.addEventListener('abort',cancel,{once:true});
    try {return await hostOperation(root,'infra-validation.apply',{plan:result.plan,approved:true},python);}
    finally {signal.removeEventListener('abort',cancel);await cancellation;}
  });
}

async function scaffold(root:string,value:Input,ctx:ExtensionCommandContext,python?:string) {
  const session_id=ctx.sessionManager.getSessionId();
  if(value.action==='inspect') {
    if(Object.keys(value).some(key=>!['action','run_id','path','offset','max_chars'].includes(key)))throw new Error('Unexpected staged inspection input');
    const {action:_action,...args}=value;
    return hostOperation(root,'scaffold.inspect',{...args,session_id},python);
  }
  if(value.action==='status') {
    if(Object.keys(value).some(key=>!['action','run_id'].includes(key)))throw new Error('Choose a staged run');
    return hostOperation(root,'scaffold.status',{run_id:value.run_id,session_id},python);
  }
  if(value.action==='resolve'&&!value.run_id)value={...value,run_id:randomUUID()};
  const result=await hostOperation(root,'scaffold.preview',{input_data:value,session_id},python);
  if(!result.plan)return result;
  if(!ctx.hasUI)return {status:'confirmation_required',review:result.review};
  if(await confirmOperation(ctx,'Confirm scaffold '+String(value.action)+'?',result.review)!==true)return {status:'declined'};
  if(value.action!=='prepare')return hostOperation(root,'scaffold.apply',{plan:result.plan,approved:true},python);
  return runOperation(ctx,'implement · staged generator',async signal=>{
    if(signal.aborted)return {status:'cancelled_before_launch'};
    let cancellation:Promise<unknown>|undefined;
    const cancel=()=>{cancellation=hostOperation(root,'scaffold.cancel',{run_id:value.run_id,session_id},python).catch(()=>undefined);};
    signal.addEventListener('abort',cancel,{once:true});
    try {return await hostOperation(root,'scaffold.apply',{plan:result.plan,approved:true},python);}
    finally {signal.removeEventListener('abort',cancel);await cancellation;}
  });
}

/** Native host operations; none of these commands add a model execution tool. */
export function registerProjectBootstrap(pi:ExtensionAPI,root:string,python?:string,phase={value:'explore'}) {
  for(const command of ['aikya-project','aikya-infra','aikya-scaffold'])pi.registerCommand(command,{
    description:command==='aikya-project'?'Plan explicit project modules and confirm a localized plan record':command==='aikya-infra'?'Plan/preserve named infrastructure artifacts or confirm a local validator':'Plan known generators, resolve exact versions, execute in staging and inspect before confirmed copy',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(value),display:true});
      if(!args.trim()&&command==='aikya-project') {publish({status:'input_required',actions:['plan','record'],fields:['slug','objective','modules','files','acceptance','checks']});return;}
      const value=args.trim()?input(args):{action:'plan'};
      phase.value=value.action==='validate'?'validate':['prepare','copy','generate'].includes(String(value.action))?'implement':['inspect','status'].includes(String(value.action))?'explore':'plan';
      if(ctx.hasUI)ctx.ui.setStatus('aikya',phase.value+' · local bootstrap');
      if(command==='aikya-infra'&&value.action==='validate') {publish(await validation(root,value,ctx,python));return;}
      if(command==='aikya-scaffold'&&value.action!=='plan') {publish(await scaffold(root,value,ctx,python));return;}
      const result=await hostOperation(root,'bootstrap.preview',{command,input_data:value,session_id:ctx.sessionManager.getSessionId()},python);
      if(!result.plan) {publish(result);return;}
      if(!ctx.hasUI) {publish({status:'confirmation_required',review:result.review});return;}
      if(await confirmOperation(ctx,'Apply '+command+'?',result.review)!==true) {publish({status:'declined'});return;}
      publish(await hostOperation(root,'bootstrap.apply',{plan:result.plan,approved:true},python));
    }});
}
