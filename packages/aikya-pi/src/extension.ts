import {runtimeVersion} from './identity.ts';
import {registerTaskRun} from "./task-run.ts";
import type {ReviewRuntimeFactory} from "./task-run-policy.ts";
import type { ExtensionAPI,ModelRuntime } from "@earendil-works/pi-coding-agent";
import { registerMemoryLifecycle } from "./memory-lifecycle.ts";
import { registerMigration } from "./migration.ts";
import {registerEngineeringWorkflows} from "./engineering-workflows.ts";
import {registerProjectBootstrap} from "./project-bootstrap.ts";
import { registerDocumentation } from "./documentation.ts";
import { registerDiagnostics } from "./diagnostics.ts";
import { registerModelCatalog } from "./catalog.ts";
import { registerOddWorkflow } from "./odd-workflow.ts";
import { registerNativeChecks } from "./native-checks.ts";
import { registerSelectedSkills,type SelectedSkill } from "./selected-skills.ts";
import { Type } from "typebox";
import { callBridge } from "./bridge.ts";
import { ownedSessionFile } from "./project.ts";
import { ReadOnlyEditor, ControlledEditor } from "./editor.ts";
import { registerLocalCommands } from "./local-commands.ts";
import { registerControlledTools } from "./tools.ts";
import { registerSddCommands } from "./sdd.ts";
import { registerOnboarding } from "./workflow.ts";

const version=runtimeVersion();

/** Pi host commands are separate from the model tool allowlist. */
export function aikyaExtension(root: string, python?: string, controlled = false, reviewer = false, phase={value:"explore"},modelRuntime?:ModelRuntime,skills:SelectedSkill[]=[],activeSkills=new Set<string>(),taskControl={blocked:false},reviewRuntime?:ReviewRuntimeFactory) {
  return (pi: ExtensionAPI) => {
    const administrative=new Set(['aikya-task-run','aikya-source-batch','aikya-arc-review','aikya-bugfix','aikya-mobile-feature','aikya-project','aikya-infra','aikya-scaffold','aikya-models','aikya-answers','aikya-docs','aikya-docs-sync','aikya-doctor','aikya-quality','aikya-tokens','aikya-theme','aikya-phase','aikya-migrate','aikya-skills-status','aikya-skills-plan','aikya-install-skill','aikya-skill-unavailable']);
    pi.on('context',event=>({messages:event.messages.filter(message=>
      message.role!=='custom'||!administrative.has(message.customType))}));
    registerSelectedSkills(pi,root,python,skills,reviewer);
    registerModelCatalog(pi,modelRuntime);
    if(!reviewer) {registerDiagnostics(pi,root,python,modelRuntime,controlled);registerDocumentation(pi,root,python);registerProjectBootstrap(pi,root,python,phase);registerEngineeringWorkflows(pi,root,python);}
    registerMemoryLifecycle(pi,root,python);
    const local=registerLocalCommands(pi, root, python,()=>phase.value,controlled);
    const task=!reviewer?registerTaskRun(pi,root,python,controlled,phase,taskControl,reviewRuntime):undefined;
    if(!reviewer)registerOddWorkflow(pi,root,python,phase,task);
    if(!reviewer)registerNativeChecks(pi,root,python,controlled,phase,local.refreshUsage);
    if (!reviewer) pi.registerCommand('aikya-phase',{description:'Select the English phase for subsequent local usage attribution',handler:async(args,ctx)=>{
      const phases=['explore','plan','implement','validate','security','review'];
      const value=args.trim()||(ctx.hasUI?await ctx.ui.select('Engineering phase',phases):undefined);
      if (!value||!phases.includes(value)) throw new Error('Choose a supported engineering phase');
      phase.value=value;
      if(ctx.hasUI)ctx.ui.setStatus('aikya',value+' · '+(ctx.model?.id??'model disabled'));
      pi.sendMessage({customType:'aikya-phase',content:JSON.stringify({phase:value}),display:true});
    }});
    if (!reviewer) {registerMigration(pi,root,python);registerOnboarding(pi,root,python,task,phase);registerSddCommands(pi,root,python);}
    if (controlled && !reviewer) registerControlledTools(pi, root, python);
    pi.on("session_before_switch", (event) => {
      if (event.reason === "resume" && !ownedSessionFile(root, event.targetSessionFile)) return {cancel: true};
    });
    pi.on("session_start", (_event, ctx) => {
      if (!ctx.hasUI) return;
      ctx.ui.setEditorComponent((...args) => controlled ? new ControlledEditor(...args).permitSkills(skills.map(s=>s.name)) : new ReadOnlyEditor(...args));
      ctx.ui.setTitle("Aikya v8 · " + (controlled ? "Controlled preview" : "Local preview · model disabled"));
      ctx.ui.setStatus("aikya", controlled ? phase.value+" · "+(ctx.model?.id??"model unavailable") : "Local preview · model disabled");
      ctx.ui.setHeader((_tui, theme) => ({
        render: (width: number) => [theme.fg("accent", "AIKYA v"+version),
          ((controlled ? phase.value+" · "+(ctx.model?.provider??"unknown")+"/"+(ctx.model?.id??"unknown") : "Local preview · model disabled") + " · /aikya-status").slice(0, width)],
        invalidate: () => {},
      }));
    });
    pi.on("input", () => {
      if (controlled) return;
      pi.sendMessage({customType: "aikya-read-only", display: true,
        content: "AIKYA read-only preview: use /aikya-status or /aikya-context. Model execution is not enabled."});
      return {action: "handled"};
    });
    pi.on("user_bash", () => ({result: {output: "Shell commands are disabled in this read-only preview.",
      exitCode: 1, cancelled: false, truncated: false}}));
    pi.on("tool_call", (event) => {
      if(event.toolName==="aikya_context"&&Array.isArray(event.input.paths)) {
        const aliases=event.input.paths.filter((p:unknown)=>typeof p==="string"&&p.startsWith("@skill/")) as string[];
        if(aliases.length&&(reviewer||aliases.some(p=>!activeSkills.has(p.split('/')[1]))))return {block:true,reason:"Invoke the approved author skill explicitly before reading its resources"};
      }
      if (!["aikya_status", "aikya_context", ...(controlled && !reviewer ? ["aikya_write","aikya_check"] : [])].includes(event.toolName)) {
        return {block: true, reason: "This Aikya runtime permits only local read queries"};
      }
    });
    pi.registerCommand("aikya-status", {
      description: "Inspect local Aikya configuration without model calls",
      handler: async () => {
        const result = await callBridge(root, "status", {python});
        pi.sendMessage({customType: "aikya-status", content: JSON.stringify(result), display: true});
      },
    });
    pi.registerCommand("aikya-context", {
      description: "Read bounded context using JSON query, paths and max_chars",
      handler: async (args) => {
        const result = await callBridge(root, "context", {python, arguments: JSON.parse(args)});
        pi.sendMessage({customType: "aikya-context", content: JSON.stringify(result), display: true});
      },
    });
    pi.registerTool({
      name: "aikya_status", label: "Aikya local status",
      description: "Read public Aikya project configuration. No model, network or writes.",
      parameters: Type.Object({}, {additionalProperties: false}),
      execute: async (_id, _params, signal) => {
        const status = await callBridge(root, "status", {python, signal});
        return {content: [{type: "text", text: JSON.stringify(status)}], details: {status}};
      },
    });
    pi.registerTool({
      name: "aikya_context", label: "Aikya scoped context",
      description: "Read bounded source or one @skill/name/resource#offset alias without refreshing the index.",
      parameters: Type.Object({
        query: Type.String({maxLength: 1000}),
        paths: Type.Array(Type.String({minLength: 1, maxLength: 240}), {minItems: 1, maxItems: 20, uniqueItems: true}),
        max_chars: Type.Integer({minimum: 512, maximum: 6000}),
      }, {additionalProperties: false}),
      execute: async (_id, args, signal) => {
        const packet = await callBridge(root, "context", {python, signal, arguments: args});
        return {content: [{type: "text", text: JSON.stringify(packet)}], details: {packet}};
      },
    });
  };
}
