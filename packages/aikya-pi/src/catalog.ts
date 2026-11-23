import type { ExtensionAPI,ModelRuntime } from '@earendil-works/pi-coding-agent';

/** Read the pinned local catalog only; do not refresh providers or credentials. */
export function registerModelCatalog(pi:ExtensionAPI,runtime?:ModelRuntime) {
  pi.registerCommand('aikya-models',{description:'Inspect the local model catalog; provider ID or JSON provider/offset, 20 entries per page',
    handler:async(args,ctx)=>{
      if(!runtime)throw new Error('Local model catalog is unavailable');
      const query=args.trim().startsWith('{')?JSON.parse(args):{provider:args.trim()||undefined};
      if(!query||typeof query!=='object'||Array.isArray(query)||Object.keys(query).some(k=>!['provider','offset'].includes(k)))throw new Error('Expected provider and optional offset');
      const provider=query.provider,offset=query.offset??0;
      if((provider!==undefined&&(typeof provider!=='string'||!/^[A-Za-z0-9_-]{1,80}$/.test(provider)))
          ||!Number.isSafeInteger(offset)||offset<0||offset>100000)throw new Error('Invalid catalog page');
      const models=runtime.getModels(provider);
      const rows=models.slice(offset,offset+20).map(model=>({provider:model.provider,id:model.id,name:model.name.slice(0,160),
        contextWindow:model.contextWindow,maxTokens:model.maxTokens,configuredAuth:runtime.hasConfiguredAuth(model.provider)}));
      pi.sendMessage({customType:'aikya-models',display:true,content:JSON.stringify({status:'local_catalog',
        total:models.length,offset,next:offset+20<models.length?offset+20:null,models:rows,
        selected:ctx.model?{provider:ctx.model.provider,id:ctx.model.id}:null,
        selection:'Select provider/model explicitly when launching the controlled runtime; no network refresh performed'})});
    }});
}
