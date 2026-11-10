import {VERSION,type ExtensionAPI,type ModelRuntime} from '@earendil-works/pi-coding-agent';
import {hostOperation} from './host.ts';

/** Host-only queries; no inference, shell or provider connection test. */
export function registerDiagnostics(pi:ExtensionAPI,root:string,python?:string,models?:ModelRuntime,controlled=false) {
  pi.registerCommand('aikya-doctor',{description:'Inspect runtime/profile/tool presence without executing SDKs; versions and compatibility remain unverified',
    handler:async(args,ctx)=>{
      if(args.trim())throw new Error('Doctor accepts no arguments');
      const report=await hostOperation(root,'diagnostics.doctor',{},python);
      const provider=controlled&&ctx.model?{status:'selected',provider:ctx.model.provider,model:ctx.model.id,
        configured_auth:models?.hasConfiguredAuth(ctx.model.provider)??null,connectivity:'not_tested'}:
        {status:'disabled',configured_auth:null,connectivity:'not_tested'};
      pi.sendMessage({customType:'aikya-doctor',content:JSON.stringify({...report,runtime:{node:process.versions.node,pi:VERSION},provider}),display:true});
    }});
  pi.registerCommand('aikya-quality',{description:'Inspect up to 20 explicit source paths: physical lines and Python AST; no security scanner or tests',
    handler:async(args)=>{
      if(!args.trim()) {
        pi.sendMessage({customType:'aikya-quality',content:JSON.stringify({status:'input_required',required:{paths:['relative/source.py']},scope:'explicit_source_files'}),display:true});return;
      }
      const query=JSON.parse(args);
      if(!query||typeof query!=='object'||Array.isArray(query)||Object.keys(query).join(',')!=='paths')throw new Error('Select explicit source paths');
      const result=await hostOperation(root,'diagnostics.quality',query,python);
      pi.sendMessage({customType:'aikya-quality',content:JSON.stringify(result),display:true});
    }});
}
