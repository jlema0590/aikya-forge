import { confirmOperation } from "./confirmation.ts";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { registerCheckTool } from "./check-tool.ts";
import { Type } from "typebox";
import { WriteAuthority } from "./permissions.ts";

export function registerControlledTools(pi: ExtensionAPI, root: string, python?: string) {
  registerCheckTool(pi,root,python);
  pi.registerTool({name: "aikya_write", label: "Approved project write",
    description: "Propose one replacement or a scoped native-change batch with unique original-text anchors. Every effect requires host confirmation; controls are protected.",
    parameters: Type.Union([
      Type.Object({path:Type.String({minLength:1,maxLength:240}),content:Type.String({maxLength:8000})},{additionalProperties:false}),
      Type.Object({change_id:Type.String({minLength:1,maxLength:80}),operations:Type.Array(Type.Union([
        Type.Object({path:Type.String({minLength:1,maxLength:240}),content:Type.String({maxLength:8000})},{additionalProperties:false}),
        Type.Object({path:Type.String({minLength:1,maxLength:240}),edits:Type.Array(Type.Object({old:Type.String({minLength:1,maxLength:4000}),new:Type.String({maxLength:4000})},{additionalProperties:false}),{minItems:1,maxItems:20})},{additionalProperties:false}),
        Type.Object({path:Type.String({minLength:1,maxLength:240}),delete:Type.Literal(true)},{additionalProperties:false})
      ]),{minItems:1,maxItems:20})},{additionalProperties:false})]),
    execute: async (_id, intent, signal, _update, ctx) => {
      if (signal?.aborted || !ctx.hasUI) return {content: [{type: "text", text: "Write requires interactive host confirmation"}], details: {status: "declined"}};
      const authority = new WriteAuthority(root, ctx.sessionManager.getSessionId(), python);
      if('operations' in intent) {
        const result=await authority.batch(intent,async preview=>{
          if(signal?.aborted)return false;
          return await confirmOperation(ctx,'Apply this exact scoped source batch?',preview)===true&&!signal?.aborted;
        },signal);
        return {content:[{type:'text',text:JSON.stringify(result)}],details:result};
      }
      const result = await authority.write(intent, async (preview) => {
        if (signal?.aborted) return false;
        const accepted = await confirmOperation(ctx,"Write " + JSON.stringify(preview.path),
          {before: preview.before, after: preview.after, bytes: preview.bytes, content: preview.content});
        return accepted === true && !signal?.aborted;
      },signal);
      return {content: [{type: "text", text: JSON.stringify(result)}], details: result};
    }});
}
