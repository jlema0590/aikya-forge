import {LoginDialogComponent,type ExtensionContext,type ModelRuntime} from '@earendil-works/pi-coding-agent';
import type {AuthType} from '@earendil-works/pi-ai';
import {SecretInput} from './secret-input.ts';
import type {ConsoleSettings} from './console-preferences.ts';
import {assertCredentialLocation} from './credential-path.ts';

async function login(ctx:ExtensionContext,runtime:ModelRuntime,id:string,type:AuthType) {
  return ctx.ui.custom<boolean>((tui,_theme,_keys,done)=>{
    let settled=false;
    const finish=(result:boolean)=>{if(!settled){settled=true;done(result);}};
    const dialog=new LoginDialogComponent(tui,id,()=>finish(false));
    void runtime.login(id,type,{
      signal:dialog.signal,
      prompt:async prompt=>{
        let answer:string|undefined;
        if(prompt.type==='secret') answer=await ctx.ui.custom<string|undefined>((_t,_th,_k,finish)=>{
          const input=new SecretInput(prompt.message,finish);
          const abort=()=>finish(undefined);dialog.signal.addEventListener('abort',abort,{once:true});
          prompt.signal?.addEventListener('abort',abort,{once:true});
          if(dialog.signal.aborted||prompt.signal?.aborted)finish(undefined);
          return {render:(w:number)=>input.render(w),handleInput:(data:string)=>input.handleInput(data),invalidate:()=>{},
            dispose:()=>{input.setValue('');dialog.signal.removeEventListener('abort',abort);prompt.signal?.removeEventListener('abort',abort);}};
        });
        else if(prompt.type==='select') {
          const labels=prompt.options.map(p=>p.label);
          const selected=await ctx.ui.select(prompt.message,labels,{signal:prompt.signal??dialog.signal});
          answer=selected===undefined?undefined:prompt.options[labels.indexOf(selected)]?.id;
        }else answer=await dialog.showPrompt(prompt.message,prompt.placeholder);
        if(answer===undefined||dialog.signal.aborted)throw new Error('Provider login cancelled');return answer;
      },
      notify:event=>{
        if(dialog.signal.aborted)return;
        if(event.type==='auth_url')dialog.showAuth(event.url,event.instructions);
        else if(event.type==='device_code')dialog.showDeviceCode(event);
        else if(event.type==='info')dialog.showInfo(event.message,event.links);
        else dialog.showProgress(event.message);
      },
    },{agentName:'Aikya Forge'}).then(()=>finish(true),()=>finish(false));
    return {render:(w:number)=>dialog.render(w),handleInput:(s:string)=>dialog.handleInput(s),invalidate:()=>dialog.invalidate(),
      get focused(){return dialog.focused;},set focused(v:boolean){dialog.focused=v;},dispose:()=>{settled=true;if(!dialog.signal.aborted)dialog.handleInput('\x1b');}};
  });
}

/** Catalog metadata only until an explicit native connect/disconnect action. */
export async function configureProvider(ctx:ExtensionContext,runtime:ModelRuntime,current:ConsoleSettings,
  save:(value:ConsoleSettings)=>void) {
  if(!ctx.isIdle())throw new Error('Stop the active flow before configuring a provider');
  const providers=[...runtime.getProviders()].sort((a,b)=>{
    const rank=(id:string)=>id==='anthropic'?0:id==='openai-codex'?1:2;return rank(a.id)-rank(b.id)||a.id.localeCompare(b.id);
  });
  const labels=providers.map(p=>p.id+' · '+(runtime.hasConfiguredAuth(p.id)?'configured':'not configured'));
  const selected=await ctx.ui.select('Providers · local catalog',labels);if(!selected)return;
  const provider=providers[labels.indexOf(selected)];if(!provider)return;
  const action=await ctx.ui.select(provider.name,['Connect','Choose model for next launch','Disconnect','Clear next-launch selection']);
  if(action==='Connect') {
    assertCredentialLocation(ctx.cwd);
    const methods:AuthType[]=[];
    if(provider.auth.apiKey?.login)methods.push('api_key');if(provider.auth.oauth)methods.push('oauth');
    if(!methods.length){ctx.ui.notify('This provider uses environment credentials configured outside Forge','info');return;}
    const method=await ctx.ui.select('Authentication',methods);if(!method)return;
    const connected=await login(ctx,runtime,provider.id,method as AuthType);
    ctx.ui.notify(connected?'Provider configured locally. Choose a model for the next launch.':'Login cancelled or unavailable; verify provider status before retrying',connected?'info':'warning');
  }else if(action==='Disconnect') {
    if(await ctx.ui.confirm('Disconnect '+provider.id,'Remove this project’s stored credential? Environment credentials remain outside Forge.')!==true)return;
    assertCredentialLocation(ctx.cwd);
    try {await runtime.logout(provider.id);ctx.ui.notify('Stored credential removed','info');}
    catch {ctx.ui.notify('Disconnect did not confirm completion; verify provider status','warning');}
  }else if(action==='Choose model for next launch') {
    const models=runtime.getModels(provider.id);let offset=0;
    for(;;) {
      const page=models.slice(offset,offset+20),names=page.map(m=>m.id);
      const choices=[...names,...(offset+20<models.length?['Next page']:[]),...(offset?['Previous page']:[])];
      if(!choices.length){ctx.ui.notify('No models in the pinned local catalog','warning');return;}
      const model=await ctx.ui.select('Model · '+provider.id,choices);if(!model)return;
      if(model==='Next page'){offset+=20;continue;}if(model==='Previous page'){offset-=20;continue;}
      if(!page.some(m=>m.id===model))return;
      if(await ctx.ui.confirm('Use on next launch',provider.id+'/'+model+'\nThe current session binding stays fixed. A configured budget is required for inference.')===true)
        save({...current,provider:{id:provider.id,model}});
      return;
    }
  }else if(action==='Clear next-launch selection') {
    const {provider:_provider,...next}=current;save(next);
  }
}
