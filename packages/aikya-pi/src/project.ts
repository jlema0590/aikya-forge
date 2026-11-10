import { lstatSync, mkdirSync, realpathSync } from "node:fs";
import { dirname, join } from "node:path";

export function projectDirectory(root: string, parts: string[]): string {
  let directory = realpathSync(root);
  for (const part of parts) {
    if (!/^[A-Za-z0-9._-]+$/.test(part) || [".", ".."].includes(part)) throw new Error("Invalid state path");
    directory = join(directory, part);
    try {
      if (lstatSync(directory).isSymbolicLink()) throw new Error("Symlinked project state path");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
    mkdirSync(directory, {recursive: true, mode: 0o700});
  }
  return directory;
}

export function ownedSessionFile(root: string, file: string | undefined): boolean {
  if (!file || !file.endsWith(".jsonl")) return false;
  try {
    const stat = lstatSync(file);
    return stat.isFile() && !stat.isSymbolicLink() && stat.size <= 2_000_000
      && realpathSync(dirname(file)) === realpathSync(join(root, ".aikya", "pi", "sessions"));
  } catch { return false; }
}
