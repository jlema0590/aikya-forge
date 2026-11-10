import { execFile } from "node:child_process";
import { realpathSync } from "node:fs";
import { randomUUID } from "node:crypto";

export type UsageCounts = {input: number; output: number; cacheRead: number; cacheWrite: number};
export type CallContext = {session: string; role: string; phase: string; provider: string; model: string; candidate?:string;change_id?:string};
export type BudgetStatus = {status: string; recorded_tokens: number | null; calls: number;
  remaining_tokens?: number; limits?: {tokens: number; calls: number}; uncertain_calls?: string[]};

export class RuntimeBudget {
  #project: string;
  #python: string;
  constructor(root: string, python = "python3") { this.#project = realpathSync(root); this.#python = python; }
  async #invoke(action: string, args: Record<string, unknown>): Promise<Record<string, unknown>> {
    const raw = await new Promise<string>((resolve, reject) => {
      const child = execFile(this.#python, ["-I", "-B", "-m", "aikya.services.runtime_state", "--root", this.#project],
        {cwd: this.#project, timeout: 10000, maxBuffer: 65536, windowsHide: true},
        (error, stdout) => error ? reject(new Error("Aikya runtime state unavailable")) : resolve(stdout));
      child.stdin?.on("error", () => {});
      child.stdin?.end(JSON.stringify({action, arguments: args}));
    });
    const response = JSON.parse(raw);
    if (response?.ok !== true || response.project !== this.#project || !response.result
        || typeof response.result !== "object" || Array.isArray(response.result)) throw new Error("Aikya runtime state refused");
    return response.result;
  }
  async status(): Promise<BudgetStatus> { return await this.#invoke("status", {}) as BudgetStatus; }
  async configure(tokens: number, calls: number, approved: boolean) {
    return this.#invoke("configure", {tokens, calls, approved});
  }
  async adjust(tokens: number, calls: number, approved: boolean) {
    return this.#invoke("adjust", {tokens, calls, approved});
  }
  async reserve(context: CallContext) {
    const id = randomUUID(); await this.#invoke("admit", {call_id: id, context}); return id;
  }
  async record(id: string, counts: UsageCounts | null) { return this.#invoke("record", {call_id: id, counts}); }
  async run<T>(context: CallContext, execute: () => Promise<{value: T; usage: UsageCounts | null}>): Promise<T> {
    const id = await this.reserve(context);
    try {
      const response = await execute(); await this.record(id, response.usage); return response.value;
    } catch (error) { await this.record(id, null).catch(() => {}); throw error; }
  }
}

export type QuotaSnapshot = {provider: string; fetchedAt: number;
  windows: {label: string; seconds: number; usedPercent: number; resetAt: number | null}[]};
function quota(value: unknown, provider: string): QuotaSnapshot {
  if (!value || typeof value !== "object") throw new Error("Invalid quota observation");
  const item = value as QuotaSnapshot;
  if (item.provider !== provider || !Number.isFinite(item.fetchedAt) || item.fetchedAt < 0
      || !Array.isArray(item.windows) || !item.windows.length || item.windows.length > 10) throw new Error("Invalid quota source");
  const labels = new Set<string>();
  for (const window of item.windows) {
    if (!window || typeof window.label !== "string" || !window.label.length || window.label.length > 80
        || /[\x00-\x1f\x7f]/.test(window.label) || labels.has(window.label)
        || !Number.isFinite(window.seconds) || window.seconds <= 0 || !Number.isFinite(window.usedPercent)
        || window.usedPercent < 0 || window.usedPercent > 100
        || (window.resetAt !== null && (!Number.isFinite(window.resetAt) || window.resetAt < 0))) throw new Error("Invalid quota window");
    labels.add(window.label);
  }
  return structuredClone({provider, fetchedAt: item.fetchedAt, windows: item.windows.map(w => (
    {label: w.label, seconds: w.seconds, usedPercent: w.usedPercent, resetAt: w.resetAt}))});
}

export class QuotaCache {
  #snapshots = new Map<string, QuotaSnapshot>();
  #failed = new Set<string>();
  #attempts = new Map<string, string>();
  async refresh(provider: string, source: (signal: AbortSignal) => Promise<unknown>) {
    if (!/^[A-Za-z0-9_-]{1,80}$/.test(provider)) throw new Error("Invalid provider identity");
    const attempt = randomUUID(); this.#attempts.set(provider, attempt);
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      const value = await Promise.race([source(controller.signal), new Promise<never>((_, reject) => {
        timer = setTimeout(() => {controller.abort(); reject(new Error("Quota source timeout"));}, 5000);
      })]);
      const snapshot = quota(value, provider);
      if (this.#attempts.get(provider) === attempt) { this.#snapshots.set(provider, snapshot); this.#failed.delete(provider); }
    } catch {
      if (this.#attempts.get(provider) === attempt) this.#failed.add(provider);
    } finally { clearTimeout(timer); }
  }
  view(provider: string, now = Date.now()) {
    const snapshot = this.#snapshots.get(provider);
    return {snapshot: snapshot ? structuredClone(snapshot) : null,
      stale: !snapshot || this.#failed.has(provider) || now < snapshot.fetchedAt || now - snapshot.fetchedAt > 60000};
  }
}
