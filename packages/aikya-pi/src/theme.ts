import { openSync, closeSync, readFileSync, fstatSync, constants, realpathSync, lstatSync,
  writeFileSync, renameSync, rmSync } from "node:fs";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { colorToRgb, parseColor } from "@earendil-works/pi-tui";
import { projectDirectory } from "./project.ts";

const validName = (name: string) => /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/.test(name);
function bounded(path: string, max: number) {
  if (lstatSync(path).isSymbolicLink()) throw new Error("Symlinked theme data");
  const fd = openSync(path, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0));
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile() || stat.size > max) throw new Error("Invalid theme data size");
    const raw = readFileSync(fd);
    if (raw.length > max) throw new Error("Theme data exceeds limit");
    return new TextDecoder("utf-8", {fatal: true}).decode(raw);
  } finally { closeSync(fd); }
}

export function previewTheme(name: string, path: string) {
  if (!validName(name)) throw new Error("Invalid theme identity");
  const value = JSON.parse(bounded(path, 256000));
  if (value?.name !== name || !value.colors || typeof value.colors !== "object" || Array.isArray(value.colors)
      || (value.vars !== undefined && (!value.vars || typeof value.vars !== "object" || Array.isArray(value.vars)))) throw new Error("Invalid theme source");
  const variables = value.vars ?? {};
  function resolve(input: unknown) {
    let current = input; const seen = new Set<string>();
    while (typeof current === "string" && /^[A-Za-z][A-Za-z0-9_-]*$/.test(current)) {
      if (seen.size > 64 || seen.has(current) || !Object.hasOwn(variables, current)) throw new Error("Invalid palette reference");
      seen.add(current); current = variables[current];
    }
    if (current === "") return null;
    if (typeof current === "number" && (!Number.isInteger(current) || current < 0 || current > 255)) throw new Error("Invalid color index");
    if (typeof current !== "string" && typeof current !== "number") throw new Error("Invalid palette color");
    return colorToRgb(parseColor(current));
  }
  for (const item of Object.values(value.colors)) resolve(item);
  for (const item of Object.values(variables)) resolve(item);
  const accent = resolve(value.colors.accent), text = resolve(value.colors.text);
  const escape = (c: ReturnType<typeof resolve>, background = false) => c ? `\x1b[${background ? 48 : 38};2;${c.r};${c.g};${c.b}m` : "";
  return {title: name + " · source palette", sample: escape(accent, true) + "  \x1b[0m " + escape(text) + "sample text\x1b[0m"};
}

export class ThemePreferences {
  #project: string;
  constructor(root: string) { this.#project = realpathSync(root); }
  #path() {
    let path = this.#project;
    for (const part of [".aikya", "pi", "theme.json"]) {
      path = join(path, part);
      try { if (lstatSync(path).isSymbolicLink()) throw new Error("Symlinked theme state"); }
      catch (error) { if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error; }
    }
    return path;
  }
  load(installed: string[]): {name: string; diagnostic?: string} {
    try {
      const value = JSON.parse(bounded(this.#path(), 16384));
      if (!value || value.schema !== 1 || value.generated_by !== "aikya-theme" || value.project !== this.#project
          || typeof value.name !== "string" || !validName(value.name) || !installed.includes(value.name)) throw new Error("Invalid theme preference");
      return {name: value.name};
    } catch (error) {
      return {name: installed.includes("dark") ? "dark" : installed[0] ?? "dark",
        ...((error as NodeJS.ErrnoException).code === "ENOENT" ? {} : {diagnostic: "Theme preference unavailable; preserved and using fallback"})};
    }
  }
  save(name: string, installed: string[]) {
    if (!validName(name) || !installed.includes(name)) throw new Error("Theme is not installed");
    if (this.load(installed).diagnostic) throw new Error("Custom or invalid theme preference is preserved");
    const folder = projectDirectory(this.#project, [".aikya", "pi"]), path = this.#path();
    const temp = join(folder, ".aikya-durable-theme-" + randomUUID());
    try {
      writeFileSync(temp, JSON.stringify({schema: 1, generated_by: "aikya-theme", project: this.#project, name}) + "\n", {flag: "wx", mode: 0o600});
      this.#path(); renameSync(temp, path);
    } finally { rmSync(temp, {force: true}); }
  }
}
