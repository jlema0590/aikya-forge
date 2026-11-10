import type { ModelRuntime } from "@earendil-works/pi-coding-agent";
import { lazyStream, type Model, type Api, type AssistantMessage,
  type AssistantMessageEventStream, type Context } from "@earendil-works/pi-ai";
import { measurePrompt } from "./prompt-budget.ts";
import { RuntimeBudget, type CallContext, type UsageCounts } from "./usage.ts";

const protectedRuntimes = new WeakSet<ModelRuntime>();

function observed(message: AssistantMessage): UsageCounts | null {
  if (["error", "aborted", "deferred"].includes(message.stopReason) || !message.usage) return null;
  const {input, output, cacheRead, cacheWrite} = message.usage;
  if ([input, output, cacheRead, cacheWrite].some(v => !Number.isSafeInteger(v) || v < 0)
      || input + output + cacheRead + cacheWrite === 0) return null;
  return {input, output, cacheRead, cacheWrite};
}

/** Pinned real-model streams only; completion helpers delegate through these gates. */
export function installBudgetedInference(runtime: ModelRuntime, budget: RuntimeBudget, context: () => CallContext, onCall?: (id:string)=>void, validate?: (transcript:Context)=>void|Promise<void>) {
  if (protectedRuntimes.has(runtime)) throw new Error("Runtime already has a budget authority");
  protectedRuntimes.add(runtime);
  const stream = runtime.stream.bind(runtime), simple = runtime.streamSimple.bind(runtime);
  function guard(model: Model<Api>, transcript: Context, dispatch: (checked:Context) => AssistantMessageEventStream) {
    return lazyStream(model, async () => {
      const checked={...transcript,messages:[...transcript.messages]};
      await validate?.(checked);
      measurePrompt(checked);
      const provenance = {...context()};
      if (model.provider !== provenance.provider || model.id !== provenance.model) throw new Error("Model is outside the selected host policy");
      if (!runtime.hasConfiguredAuth(model.provider)) throw new Error("Configure provider authentication before inference");
      const id = await budget.reserve(provenance);
      let inner: AssistantMessageEventStream;
      try { onCall?.(id); inner = dispatch(checked); }
      catch (error) { await budget.record(id, null); throw error; }
      return (async function* () {
        let recorded = false;
        try {
          for await (const event of inner) {
            if (event.type === "done" || event.type === "error") {
              await budget.record(id, observed(event.type === "done" ? event.message : event.error));
              recorded = true;
            }
            yield event;
          }
        } finally {
          if (!recorded) await budget.record(id, null);
        }
      })();
    });
  }
  runtime.stream = (model, transcript, options) => guard(model, transcript, checked => stream(model, checked, options));
  runtime.streamSimple = (model, transcript, options) => guard(model, transcript, checked => simple(model, checked, options));
  // Do not silently run auxiliary APIs for which this slice has no usage contract.
  const disabled = () => {throw new Error("Auxiliary inference is not enabled by the Aikya budget policy");};
  runtime.streamDeferred = disabled; runtime.fetchDeferred = async () => disabled();
  runtime.generateImages = async () => disabled(); runtime.classify = async () => disabled();
}
