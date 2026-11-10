import { confirmOperation } from "./confirmation.ts";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { hostOperation } from "./host.ts";

export const SDD_COMMANDS=['aikya-specify','aikya-clarify','aikya-plan','aikya-tasks','aikya-approve','aikya-sdd-status'];

export function registerSddCommands(pi:ExtensionAPI,root:string,python?:string) {
  const publish=(command:string,result:unknown)=>pi.sendMessage({customType:command,content:JSON.stringify(result),display:true});
  for (const command of SDD_COMMANDS) {
    pi.registerCommand(command,{description:command==='aikya-sdd-status'?'Inspect a canonical SDD specification by ID':
      'Apply a canonical SDD transition from explicit JSON after host confirmation',
      handler:async(args,ctx)=>{
        if (command==='aikya-sdd-status') {
          publish(command,await hostOperation(root,'sdd.status',{ident:args.trim()},python));return;
        }
        const input=JSON.parse(args);
        if (!input||typeof input!=='object'||Array.isArray(input)) throw new Error('An explicit SDD JSON object is required');
        if (!ctx.hasUI) {publish(command,{status:'confirmation_required'});return;}
        const preview=await hostOperation(root,'sdd.preview',{action:command.slice(6),arguments:input},python);
        if (await confirmOperation(ctx,'Apply '+command+'?',preview)!==true) {publish(command,{status:'declined'});return;}
        publish(command,await hostOperation(root,'sdd.apply',{plan:preview,approved:true},python));
      }});
  }
}
