import { SDD_COMMANDS } from "./sdd.ts";
import { CustomEditor } from "@earendil-works/pi-coding-agent";

type Submit = (text: string) => unknown;
const LOCAL_COMMANDS = ["/aikya-arc-review", "/aikya-bugfix", "/aikya-mobile-feature", "/aikya-project", "/aikya-infra", "/aikya-scaffold", "/aikya-status", "/aikya-answers", "/aikya-docs", "/aikya-docs-sync", "/aikya-doctor", "/aikya-quality", "/aikya-phase", "/aikya-context", "/aikya-memory", "/aikya-tokens", "/aikya-theme", "/aikya-init", "/aikya-analyze", "/aikya-implement", "/aikya-migrate", "/aikya-models", "/aikya-skills-status", "/aikya-skills-plan", "/aikya-install-skill", "/aikya-feature", "/aikya-tests", "/aikya-verify", ...SDD_COMMANDS.map(c=>"/"+c)];
export function guardedSubmission(submit: Submit, blocked: Submit, allowed = LOCAL_COMMANDS): Submit {
  return (text) => {
    const value = text.trim();
    const command = value.split(/\s/, 1)[0];
    if (value.startsWith("!") || (value.startsWith("/")
        && !allowed.includes(command) && value !== "/quit")) return blocked(value);
    return submit(text);
  };
}

/** Public Pi custom-editor integration; no native dispatcher monkey patches. */
export class ReadOnlyEditor extends CustomEditor {
  protected allowedCommands = LOCAL_COMMANDS;
  constructor(...args: ConstructorParameters<typeof CustomEditor>) {
    super(...args);
    let handler: Submit | undefined;
    Object.defineProperty(this, "onSubmit", {
      configurable: false,
      get: () => handler,
      set: (submit: Submit | undefined) => { handler = submit && guardedSubmission(submit, () => {
        this.setText("Local preview: choose a supported /aikya command or /quit.");
      }, this.allowedCommands); },
    });
  }

  override handleInput(data: string) {
    // The native UI copies its shortcuts after the factory returns. Keep only exit/interrupt.
    for (const action of this.actionHandlers.keys()) {
      if (action !== "app.interrupt" && action !== "app.exit") this.actionHandlers.delete(action);
    }
    this.onPasteImage = undefined;
    super.handleInput(data);
  }
}

export class ControlledEditor extends ReadOnlyEditor {
  protected override allowedCommands = [...LOCAL_COMMANDS, "/login", "/logout", "/compact"];
  permitSkills(names:string[]) {
    if(names.some(n=>!/^([a-z0-9]+-)*[a-z0-9]+$/.test(n)||n.startsWith("aikya-")))throw new Error("Invalid selected skill name");
    this.allowedCommands=[...this.allowedCommands,...names.map(name=>"/skill:"+name)];return this;
  }
}
