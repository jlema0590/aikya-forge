import { lstatSync, readFileSync, writeFileSync, renameSync, rmSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";
import { randomUUID } from "node:crypto";
import { spawnSync } from "node:child_process";
import { devNull } from "node:os";
import { projectDirectory } from "./project.ts";

function inspect(path: string) {
  try { return lstatSync(path); }
  catch (error) { if ((error as NodeJS.ErrnoException).code === "ENOENT") return undefined; throw error; }
}

function git(project: string, args: string[]) {
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("GIT_")));
  const result = spawnSync("git", ["-c", "core.fsmonitor=false", ...args], {
    cwd: project, encoding: "utf8", timeout: 3000, maxBuffer: 16384, windowsHide: true,
    env: {...env, GIT_CONFIG_GLOBAL: devNull, GIT_CONFIG_NOSYSTEM: "1", GIT_OPTIONAL_LOCKS: "0"},
  });
  if (result.error) throw new Error("Cannot inspect Git protection", {cause: result.error});
  return result;
}

function repositoryMarker(project: string): boolean {
  let current = project;
  for (let depth = 0; depth < 128; depth++) {
    if (inspect(join(current, ".git")) || (inspect(join(current, "HEAD"))
        && inspect(join(current, "objects")) && inspect(join(current, "refs")))) return true;
    const parent = dirname(current);
    if (parent === current) return false;
    current = parent;
  }
  throw new Error("Cannot inspect Git ancestry within the supported bound");
}

export function prepareTerminalState(root: string) {
  const project = realpathSync(root);
  const repository = repositoryMarker(project) ? git(project, ["rev-parse", "--is-inside-work-tree"]) : undefined;
  const inGit = repository?.status === 0 && repository.stdout.trim() === "true";
  if (repository && !inGit) throw new Error("Cannot inspect Git repository");
  if (inGit) {
    const tracked = git(project, ["ls-files", "--", ".aikya/pi/"]);
    if (tracked.status !== 0 || tracked.stdout) throw new Error("Tracked terminal state requires operator review");
  }
  const ignore = join(project, ".gitignore");
  const stat = inspect(ignore);
  if (stat?.isSymbolicLink()) throw new Error("Symlinked ignore file");
  if (stat && (!stat.isFile() || stat.size > 1_048_576 || !(stat.mode & 0o222))) throw new Error("Protected ignore file");
  const previous = stat ? readFileSync(ignore) : Buffer.alloc(0);
  const text = new TextDecoder("utf-8", {fatal: true}).decode(previous);
  if (text.includes("\0")) throw new Error("Invalid ignore encoding");
  const rules = text.trimEnd().split(/\r?\n/);
  if (![".aikya/pi/", "/.aikya/pi/"].includes(rules.at(-1) ?? "")) {
    const temp = join(project, ".aikya-durable-terminal-" + randomUUID());
    try {
      const suffix = (text.endsWith("\n") || !text ? "" : "\n") + "\n# Aikya local terminal state\n.aikya/pi/\n";
      writeFileSync(temp, Buffer.concat([previous, Buffer.from(suffix)]), {flag: "wx", mode: stat ? stat.mode & 0o777 : 0o644});
      const now = inspect(ignore);
      if (Boolean(now) !== Boolean(stat) || (now && (!now.isFile() || now.isSymbolicLink()
          || now.ino !== stat?.ino || !readFileSync(ignore).equals(previous)))) {
        throw new Error("Ignore rules changed during startup");
      }
      renameSync(temp, ignore);
    } finally { rmSync(temp, {force: true}); }
  }
  if (inGit && git(project, ["check-ignore", "-q", "--no-index", "--", ".aikya/pi/agent/auth.json"]).status !== 0) {
    throw new Error("Terminal state is not protected by effective Git rules");
  }
  return {project, agentDir: projectDirectory(project, [".aikya", "pi", "agent"])};
}
