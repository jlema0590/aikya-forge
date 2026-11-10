import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { callBridge } from "./bridge.ts";
import { RuntimeBudget, QuotaCache, type BudgetStatus } from "./usage.ts";
import { quotaFromHeaders, renderUsage, renderFooter } from "./usage-view.ts";
import { ThemePreferences, previewTheme } from "./theme.ts";

export function registerLocalCommands(pi: ExtensionAPI, root: string, python?: string, phase=()=>"explore", controlled=false) {
  const preferences = new ThemePreferences(root), budget = new RuntimeBudget(root, python), quotas = new QuotaCache();
  const seenProviders = new Set<string>();
  let latest:BudgetStatus={status:'unconfigured',recorded_tokens:null,calls:0};
  const refresh=async()=>{
    try {latest=await budget.status();}
    catch {latest={status:'unavailable',recorded_tokens:null,calls:0};}
  };
  pi.on('agent_end',async(_event,ctx)=>{if(ctx.hasUI)await refresh();});
  const publish = (customType: string, result: unknown) => pi.sendMessage({customType,
    content: JSON.stringify(result), display: true});
  pi.on("after_provider_response",async (event,ctx)=>{
    const provider=ctx.model?.provider;
    if (!provider) return;
    seenProviders.add(provider);
    await quotas.refresh(provider,async()=>quotaFromHeaders(provider,event.headers));
  });
  pi.registerMessageRenderer("aikya-tokens",(message,_options,theme)=>{
    if (typeof message.content!=="string") return;
    try {
      const value=JSON.parse(message.content) as BudgetStatus & {quotas?:ReturnType<QuotaCache['view']>[]};
      if (typeof value.status!=="string" || !("recorded_tokens" in value)) return;
      return {render:(width:number)=>renderUsage(value,value.quotas??[],width).map(line=>theme.fg("text",line)),invalidate:()=>{}};
    } catch { return; }
  });
  pi.on("session_start", async (_event, ctx) => {
    if (!ctx.hasUI) return;
    await refresh();
    ctx.ui.setFooter((_tui,theme)=>({render:(width:number)=>[
      theme.fg('muted',renderFooter(phase(),controlled?(ctx.model?.provider??'unknown')+'/'+(ctx.model?.id??'unknown'):null,latest,width))],invalidate:()=>{}}));
    const names = ctx.ui.getAllThemes().map(t => t.name).filter(n => ["dark", "light"].includes(n));
    const preference = preferences.load(names);
    ctx.ui.setTheme(preference.name);
    if (preference.diagnostic) ctx.ui.notify(preference.diagnostic, "warning");
  });
  pi.registerCommand("aikya-memory", {description: "Read current reviewed project notes using bounded JSON query/max_chars",
    handler: async (args) => {
      const result = args.trim() ? await callBridge(root, "memory-search", {python, arguments: JSON.parse(args)})
        : await callBridge(root, "memory-status", {python});
      publish("aikya-memory", result);
    }});
  pi.registerCommand("aikya-tokens", {description: "Inspect local budget; JSON tokens/calls configuration requires host confirmation",
    handler: async (args, ctx) => {
      if (args.trim()) {
        const value = JSON.parse(args);
        if (!value || Object.keys(value).sort().join(",") !== "calls,tokens") throw new Error("Expected tokens and calls");
        if (!ctx.hasUI || await ctx.ui.confirm("Configure project budget", JSON.stringify(value)) !== true) {
          publish("aikya-tokens", {status: "declined"}); return;
        }
        if ((await budget.status()).status === "unconfigured") await budget.configure(value.tokens, value.calls, true);
        else await budget.adjust(value.tokens, value.calls, true);
      }
      latest=await budget.status();
      publish("aikya-tokens", {...latest,quotas:[...seenProviders].map(p=>quotas.view(p))});
    }});
  pi.registerCommand("aikya-theme", {description: "Preview and select an installed light/dark theme with local persistence",
    handler: async (args, ctx) => {
      if (!ctx.hasUI) { publish("aikya-theme", {status: "interactive_terminal_required"}); return; }
      const available = ctx.ui.getAllThemes().filter(t => ["dark", "light"].includes(t.name));
      const names = available.map(t => t.name);
      const selected = args.trim() || await ctx.ui.select("Aikya theme", names);
      if (!selected) return;
      const source = available.find(t => t.name === selected);
      if (!source?.path || !ctx.ui.getTheme(selected)) throw new Error("Installed theme source is unavailable");
      const preview = previewTheme(selected, source.path);
      if (await ctx.ui.confirm(preview.title, preview.sample + "\nApply this theme?") !== true) return;
      const previous = ctx.ui.theme.name ?? preferences.load(names).name;
      const result = ctx.ui.setTheme(selected);
      if (!result.success) throw new Error("Theme could not be activated");
      try { preferences.save(selected, names); }
      catch (error) { ctx.ui.setTheme(previous); throw error; }
      publish("aikya-theme", {status: "applied", name: selected});
    }});
  return {refreshUsage:refresh};
}
