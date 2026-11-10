import type {ExtensionAPI} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';
import {confirmOperation} from './confirmation.ts';
import {runOperation} from './operation.ts';
type Input=Record<string,unknown>;
function fields(value:Input,allowed:string[]) {
  if(Object.keys(value).some(key=>!allowed.includes(key)))throw new Error('Unexpected skill administration input');
}

/** All effects require native confirmation. JSON, model output and imported metadata grant none. */
export function registerSkillAdministration(pi:ExtensionAPI,root:string,python?:string) {
  for(const command of ['aikya-skills-status','aikya-skills-plan','aikya-install-skill'])pi.registerCommand(command,{
    description:command==='aikya-skills-status'?'Inspect explicit project selection or inert global skill versions':command==='aikya-skills-plan'?'Review a concrete skill source or version change without effects':'Confirm skill data capture, installation, update, rollback or complete-effect recovery; no automatic activation',
    handler:async(args,ctx)=>{
      const publish=(value:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(value),display:true});
      const input=args.trim()?JSON.parse(args):{};
      if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Explicit skill JSON object required');
      const scope=input.scope??'project';if(!['project','global'].includes(scope))throw new Error('Choose project or global scope');
      if(command==='aikya-skills-status') {
        fields(input,['scope','offset']);publish(await hostOperation(root,'skills.manage-status',input,python));return;
      }
      if(!args.trim()) {publish({status:'input_required',scope:'project',actions:['install','select','update','rollback','recover','resolve','fetch'],source:'Absolute local directory or explicit captured/global version descriptor'});return;}
      const action=input.action??'install';let value:Record<string,unknown>;
      if(action==='resolve') {
        fields(input,['action','repo','ref']);
        if(typeof input.repo!=='string'||!/^https:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(input.repo))throw new Error('Choose an explicit public HTTPS GitHub repository');
        const review={repo:input.repo,ref:input.ref??'repository default branch',network:'Resolve public commit metadata only; no credentials, download or activation'};
        if(command==='aikya-skills-plan') {publish({status:'review_ready',review});return;}
        if(!ctx.hasUI) {publish({status:'confirmation_required',review});return;}
        if(await confirmOperation(ctx,'Resolve this public skill source reference?',review)!==true) {publish({status:'declined'});return;}
        publish(await runOperation(ctx,'explore · public source metadata',signal=>hostOperation(root,'skills.source-resolve',{repo:input.repo,...(input.ref===undefined?{}:{ref:input.ref}),approved:true},python,signal)));return;
      }
      if(action==='fetch') {
        fields(input,['action','repo','path','commit','name']);
        const {action:_action,...source}=input;value=await hostOperation(root,'skills.fetch-preview',source,python);
      } else {
        if(!['install','select','update','rollback','recover'].includes(action))throw new Error('Unknown skill action');
        fields(input,['action','scope','source','name','source_hash']);
        value=await hostOperation(root,'skills.manage-preview',{...input,scope,action:action==='select'?'install':action},python);
      }
      if(command==='aikya-skills-plan') {publish({status:'review_ready',review:value.review});return;}
      if(!ctx.hasUI) {publish({status:'confirmation_required',review:value.review});return;}
      if(await confirmOperation(ctx,'Confirm skill '+String(action)+'?',value.review)!==true) {publish({status:'declined'});return;}
      if(action==='fetch') {
        publish(await runOperation(ctx,'explore · pinned skill data capture',signal=>hostOperation(root,'skills.fetch',{plan:value.plan,approved:true},python,signal)));return;
      }
      publish(await hostOperation(root,'skills.manage-apply',{plan:value.plan,scope,recovery:action==='recover',approved:true},python));
    }});
}
