import { parseArgs } from "node:util";
import { callBridge } from "./bridge.ts";
import { prepareTerminalState } from "./terminal-state.ts";

async function main() {
  const {values} = parseArgs({options: {target: {type: "string"}, python: {type: "string"},
    provider: {type: "string"}, model: {type: "string"},
    resume: {type: "boolean"}, help: {type: "boolean"}}, strict: true, allowPositionals: false});
  if (values.help) {
    console.log("Aikya v8 read-only terminal preview by default\n--target PROJECT --python INSTALLED_PYTHON [--resume] [--provider ID --model ID]");
    return;
  }
  if (!process.stdin.isTTY || !process.stdout.isTTY) throw new Error("An interactive terminal is required");
  if (Boolean(values.provider) !== Boolean(values.model)) throw new Error("Select provider and model together");
  const root = values.target ?? process.cwd();
  await callBridge(root, "capabilities", {python: values.python});
  const {project, agentDir} = prepareTerminalState(root);
  // Configure Pi before importing it: its native UI must not use personal global state.
  process.env.PI_CODING_AGENT_DIR = agentDir;
  process.env.PI_OFFLINE = "1";
  const [{createReadOnlyRuntime, createControlledRuntime}, {InteractiveMode}] = await Promise.all([
    import("./runtime.ts"), import("@earendil-works/pi-coding-agent"),
  ]);
  const options = {python: values.python, resume: values.resume};
  const runtime = values.provider && values.model
    ? await createControlledRuntime(project, {...options, provider: values.provider, model: values.model})
    : await createReadOnlyRuntime(project, options);
  try { await new InteractiveMode(runtime).run(); }
  finally { await runtime.dispose(); }
}

try { await main(); }
catch (error) {
  console.error("AIKYA: " + (error instanceof Error ? error.message : "Terminal unavailable"));
  process.exitCode = 2;
}
