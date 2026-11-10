import { execFile } from "node:child_process";
import { realpathSync } from "node:fs";
import { randomUUID } from "node:crypto";

type Operation = "status" | "capabilities" | "context" | "write-preview" | "write" | "batch-preview" | "batch" | "memory-status" | "memory-search";

export function decodeReply(raw: string, id: string, project: string): unknown {
  let reply;
  try { reply = JSON.parse(raw); }
  catch { throw new Error("Invalid Aikya service response"); }
  if (!reply || reply.schema !== 1 || reply.id !== id || reply.project !== project || reply.ok !== true
      || !reply.result || typeof reply.result !== "object" || Array.isArray(reply.result)) {
    throw new Error("Invalid Aikya service response");
  }
  return reply.result;
}

export async function callBridge(
  root: string, operation: Operation, options: { python?: string; signal?: AbortSignal;
    arguments?: Record<string, unknown>; hostKey?: string } = {},
): Promise<unknown> {
  if (!["status", "capabilities", "context", "write-preview", "write", "batch-preview", "batch", "memory-status", "memory-search"].includes(operation)) throw new Error("Unknown operation");
  const project = realpathSync(root);
  const id = randomUUID();
  const raw = await new Promise<string>((resolve, reject) => {
    const child = execFile(options.python ?? "python3", ["-I", "-B", "-m", "aikya.services.bridge", "--root", project],
      { cwd: project, timeout: operation==='batch'?120_000:10_000, maxBuffer: 65_536, windowsHide: true, signal: options.signal,
        env: {...process.env, AIKYA_HOST_KEY: options.hostKey ?? ""} },
      (error, stdout) => error ? reject(new Error("Aikya service unavailable", { cause: error })) : resolve(stdout));
    child.stdin?.on("error", () => {}); // Process failure is reported by execFile.
    child.stdin?.end(JSON.stringify({ schema: 1, id, project, operation, arguments: options.arguments ?? {} }));
  });
  return decodeReply(raw, id, project);
}
