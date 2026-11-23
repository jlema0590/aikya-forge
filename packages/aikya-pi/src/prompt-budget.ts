import type { Context } from "@earendil-works/pi-ai";

/** UTF-8 request bounds, deliberately not token estimates or account quota. */
export const PROMPT_LIMITS=Object.freeze({system:32768,tools:16384,total:131072});
export function measurePrompt(context:Context) {
  const bytes=(value:unknown)=>Buffer.byteLength(JSON.stringify(value)??'', 'utf8');
  const tools=context.tools??[], names=tools.map(t=>t.name);
  if (new Set(names).size!==names.length) throw new Error('Duplicate tool declarations refused');
  const result={system:bytes(context.systemPrompt??''),tools:bytes(tools),total:bytes(context)};
  if (result.system>PROMPT_LIMITS.system||result.tools>PROMPT_LIMITS.tools||result.total>PROMPT_LIMITS.total) {
    throw new Error('Prompt exceeds local byte policy; narrow context or compact explicitly before another call');
  }
  return result;
}
