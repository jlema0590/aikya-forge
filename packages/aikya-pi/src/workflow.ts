import {taskActions} from './task-run-policy.ts';
import type {TaskHandler} from './task-run.ts';
import { memoryLease } from "./memory-lifecycle.ts";
import { confirmOperation } from "./confirmation.ts";
import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";
import { hostOperation } from "./host.ts";
import {editSources} from './source-batches.ts';

type Choices=Record<string,string[]>;
async function interview(ctx:ExtensionCommandContext,choices:Choices) {
  const choose=async(title:string,key:string)=>{
    const value=await ctx.ui.select(title,choices[key]);
    if (value===undefined) throw new Error("Onboarding cancelled; no project files written");
    return value;
  };
  const language=await choose('Documentation language / Idioma documental','languages');
  const profile:Record<string,unknown>={project_type:await choose('Project type','project_types'),
    methodology:await choose('Engineering methodology','methodologies'),repository_layout:'singlerepo'};
  if (profile.project_type==='development') {
    profile.backend=await choose('Backend (none if not applicable)','backends');
    profile.frontend=await choose('Frontend (none if not applicable)','frontends');
    profile.mobile=await choose('Mobile platforms (none if not applicable)','mobile');
    if (profile.mobile!=='none') {
      profile.mobile_framework=await choose('Mobile framework','mobile_frameworks');
      if (profile.mobile_framework==='native') {
        if (profile.mobile==='android'||profile.mobile==='both') profile.android_language=await choose('Android language','android_languages');
        if (profile.mobile==='ios'||profile.mobile==='both') profile.ios_ui=await choose('iOS UI framework','ios_ui');
      }
    }
    profile.repository_layout=await choose('Repository layout','layouts');
  } else if (profile.project_type==='infrastructure') {
    const choice=await ctx.ui.select('Infrastructure tool',['terraform','opentofu','ansible']);
    if (!choice) throw new Error('Onboarding cancelled');
    profile.infrastructure=choice==='ansible'?{configuration_management:'ansible'}:{iac:choice};
  } else {
    const choice=await ctx.ui.select('Deployment platform',['docker','kubernetes']);
    if (!choice) throw new Error('Onboarding cancelled'); profile.deployment=choice;
  }
  return {profile,language};
}

export function registerOnboarding(pi:ExtensionAPI,root:string,python?:string,task?:TaskHandler,phase={value:'explore'}) {
  pi.registerCommand('aikya-implement',{description:'Bind an approved SDD task and explicit file scope to this session; JSON spec_id/task_id/files',
    handler:async(args,ctx)=>{
      if(!args.trim()) {pi.sendMessage({customType:'aikya-implement',content:JSON.stringify({status:'input_required',actions:['bind','edit',...taskActions]}),display:true});return;}
      const value=JSON.parse(args);
      if(task&&await task(value,ctx))return;
      if(value?.action==='edit') {
        const result=await editSources(root,value,ctx,python);
        pi.sendMessage({customType:'aikya-source-batch',content:JSON.stringify(result),display:true});return;
      }
      if (!value||Object.keys(value).sort().join(',')!=='files,spec_id,task_id') throw new Error('Expected spec_id, task_id and files');
      if (!ctx.hasUI||await confirmOperation(ctx,'Bind SDD task and file scope?',value)!==true) {
        pi.sendMessage({customType:'aikya-implement',content:JSON.stringify({status:'declined'}),display:true});return;
      }
      const result=await hostOperation(root,'workflow.bind',{...value,session:ctx.sessionManager.getSessionId(),approved:true},python);
      pi.sendMessage({customType:'aikya-implement',content:JSON.stringify(result),display:true});
    }});
  for (const command of ['aikya-init','aikya-analyze','aikya-answers']) {
    pi.registerCommand(command,{description:command==='aikya-init'?'Initialize a new project with explicit ODD/SDD and host confirmation':command==='aikya-analyze'?'Adopt an existing project using a reviewed profile and local evidence':'Apply a declarative new/existing ODD/SDD profile; default .aikya/answers.json',
      handler:async(args,ctx)=>{
        phase.value='explore';
        let input:{profile:Record<string,unknown>;language:string|null};
        let plan:Record<string,unknown>,preview:Record<string,unknown>;
        if(command==='aikya-answers'&&!args.trim()) {
          plan=await hostOperation(root,'workflow.answers-preview',{},python);preview=plan.plan as Record<string,unknown>;
        } else {
        if (args.trim()) {
          const value=JSON.parse(args);
          if (!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).some(k=>!['profile','language'].includes(k))) throw new Error('Expected profile and optional language');
          input={profile:value.profile,language:value.language??null};
        }
        else {
          if (!ctx.hasUI) throw new Error('Interactive onboarding or explicit profile JSON is required');
          input=await interview(ctx,await hostOperation(root,'workflow.choices',{},python) as Choices);
        }
        preview=await hostOperation(root,'workflow.preview',{...input,command},python);plan=preview;
        }
        phase.value='plan';
        if(ctx.hasUI)ctx.ui.setStatus('aikya','plan · local onboarding');
        if (!ctx.hasUI) {pi.sendMessage({customType:command,content:JSON.stringify({status:'confirmation_required',preview}),display:true});return;}
        const accepted=await confirmOperation(ctx,'Apply '+command+'?',{profile:preview.answers,language:preview.language,
          documents:preview.operations,state_paths:preview.state_paths});
        if (accepted!==true) {pi.sendMessage({customType:command,content:JSON.stringify({status:'declined'}),display:true});return;}
        phase.value='implement';ctx.ui.setStatus('aikya','implement · local onboarding');
        const result=await hostOperation(root,'workflow.apply',{plan,approved:true},python);
        phase.value='validate';ctx.ui.setStatus('aikya','validate · local initialization metadata');
        try {await memoryLease(root,ctx.sessionManager.getSessionId(),'start',python);}
        catch {ctx.ui.notify('Project initialized; local memory observer is unavailable','warning');}
        pi.sendMessage({customType:command,content:JSON.stringify(result),display:true});
      }});
  }
}
