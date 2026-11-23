# Aikya Forge

[English](README.md) | [Español](README.es.md)

**Engineering workflows, project-local memory and controlled AI execution from the terminal.**

Aikya Forge combines a Python core with an interactive Pi terminal. It carries forward
Aikya's command adapters, templates and engineering controls into an independently
versioned repository. The current development version is **0.2.0**.

Native installation and terminal acceptance are tracked per platform in the
[validation report](aikya/docs/validation/2026-11-19-interactive-acceptance.md). Real-provider
acceptance is a separate release gate. Source availability does not mean a public
release or short installer is published.

## Quick start from source

Requirements: Python 3.10–3.13 with pip/venv, Node.js 22.19.0+ with npm, and Git.
Python 3.13 is recommended for the contributor test environment.

```sh
git clone --branch develop https://github.com/jlema0590/aikya-forge.git
cd aikya-forge
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'setuptools>=77' wheel build
python -m pip install --no-build-isolation -e ".[terminal]"
npm --prefix packages/aikya-pi ci --ignore-scripts --no-audit --no-fund
```

On Windows PowerShell, create and activate the environment with these commands,
then run the same `python -m pip` and `npm` commands above:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Choose an existing project directory and launch the development terminal:

```sh
aikya terminal --runtime-dir ./packages/aikya-pi --target /absolute/path/to/project
```

This explicit source-runtime option is required until a managed native payload has
been installed. Bare `aikya` resolves an already installed managed terminal.
Model selection and inference require explicit configuration, credentials and a
positive local budget; opening the terminal does not imply a model call.

## Console settings and flow

Open `/aikya-settings` or press **F2** to connect a provider from the pinned local
catalog, choose a model for the next launch, configure light/dark appearance and
HEX colors, select normal/bold/italic text, or show/hide the right sidebar.
Font family and size remain controlled by your terminal application.

The **Aikya Forge** theme (`aikya`) uses the original logo's navy, cyan and
turquoise. New projects start with this theme; existing selections are retained.
The startup header draws **Aikya** with `pyfiglet` 1.0.4, using slant/small ASCII
fonts according to terminal width. Native installations include the library, fonts
and license for offline startup. Source installs use the `terminal` extra above;
the dependency-free Python core retains a plain-text fallback. The banner is cached
locally and makes no model calls. Select the theme with `/aikya-theme aikya` or
Settings → Appearance.

The right sidebar’s Project & Git block identifies the project directory, observed
Git branch and
`git config user.name`. Email and remotes are not displayed. Branch changes reuse
the SDK cache/watch; repainting runs no Git commands. User identity is read once
at session start; missing Git/configuration is shown explicitly as unavailable.
Narrow terminals retain project/Git fields in the compact summary below the transcript.

The sidebar reserves its own columns for phase, flow controls, local tokens/calls,
budget and estimated context percentages, and Claude/Codex author/reviewer usage.
Account quota appears only from observed provider response headers, with age/stale
labels; otherwise it remains unavailable. Configuring or repainting the panel
does not invoke a model. Saved model selection requires an available local budget
and does not change a live session's binding. See the
[console guide](aikya/docs/features/forge-console-settings.md).

## Components

| Component | Role |
|---|---|
| Python core (`src/aikya/`) | Onboarding, methodology, checks, memory, installation and durable evidence. |
| Pi terminal (`packages/aikya-pi/`) | Interactive commands, confirmations, themes, model selection and bounded sessions. |
| Command adapters | 29 canonical workflows with their documented native coverage and limits. |
| Local memory | Incremental code inventory, supported-language symbols, reviewed notes, observation and HTML visualization. |
| Documentation templates | Bundled templates selected by workflow and project type. |
| Skills | Explicitly chosen, pinned inert packages with project/global administration. |

ODD and SDD define the workflow. TDD controls behavior changes; RDD means
**Receipt Driven Development**, using execution receipts and review evidence.
Checks, independent review and delivery approval remain separate decisions.

## Commands and local state

Start with `/aikya-init` for a new project or `/aikya-analyze` for an existing one;
select ODD or SDD during onboarding. `/aikya-memory` opens local memory functionality.
The [command coverage report](aikya/docs/validation/2026-11-08-pi-command-coverage.md)
documents all canonical commands and current native limits.

Each project retains its own memory and session data. Generated engineering records
belong under `aikya/docs/`; private runtime state belongs under `.aikya/`.
Local index/HTML updates use local processing and do not call a model. Inference
accounting is local and does not invent a provider's subscription quota.

## Managed native distribution

The contributor builder assembles pinned Python, Node and Pi components into one
verified payload. Reviewed fd/ripgrep binaries are included for offline file
autocomplete and search; startup does not download tools from project caches.
It generates checksum-bound shell/PowerShell entry scripts and
supports explicit install/update, retained rollback and conservative uninstall.

```sh
python scripts/ci/build_terminal_bundle.py --version 0.2.0 --output ../forge-native-0.2.0 --fetch-components
```

The output directory must be new. Building downloads pinned public components and
npm packages; the builder only targets the current supported native platform.
It does not publish a release. See the
[native distribution guide](aikya/docs/deployment/pi-managed-terminal.md) and
[Forge migration record](aikya/docs/changes/REQ-20261110-f0900100.md).
No Forge Pages installation URL is advertised before deployment and acceptance.

## Development and validation

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
npm --prefix packages/aikya-pi run typecheck
npm --prefix packages/aikya-pi test
python scripts/ci/release_contract.py check
python -m build --no-isolation
```

Optional supported-language parsers can be installed with
`python -m pip install '.[code-index]'`. Languages without an available semantic
parser remain explicit file inventory; the report does not infer unsupported symbols.

```text
src/aikya/             Python package and bundled resources
packages/aikya-pi/     Pi terminal and TypeScript tests
tests/                Python and browser contracts
scripts/ci/           Validation and distribution builders
aikya/docs/           Plans, architecture, bugs, changes and evidence
examples/             Example profiles and generated documentation
```

## Versioning and compatibility

`VERSION` and the Pi package are **0.2.0**, following the initial 0.1.0 import. Future Forge releases use independent
semantic versioning. The [changelog](CHANGELOG.md) records Forge changes; the
[inherited changelog](aikya/docs/history/harness-CHANGELOG.md) preserves Harness history.

Commands, Python imports (`aikya`) and the Python distribution name (`aikya-harness`)
remain compatible in this first import. Operational update URLs point to this
repository. Older v8 payload identities remain readable for explicit compatibility;
they do not change Forge's version sequence.

Inherited publication workflows remain scoped to the original Harness repository.
Forge has its own seven-target build/acceptance workflow and manual release preparation.
Publication is disabled by default and requires main, all native checks and separately
reviewed real-provider evidence. No stable release or Pages URL is published by this change. The [documentation index](aikya/docs/indice.md) preserves previous plans
and evidence; references to v7/v8 inside historical records describe their original
snapshots, not Forge's current version.

## License

MIT. See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_LICENSES.md).

## Forge administration and acceptance

`/aikya-uninstall-skills` previews confirmed withdrawal of Forge-owned skill selections.
It retains exact packages for restoration; it does not erase external plugins or other
projects. Use `aikya skills --help` for project/local/global scope, preview, restore and
interrupted-operation recovery. Restart the author session after a selection change.

```sh
aikya skills uninstall --target /absolute/project --scope project --name example-skill
# Add --yes only after reviewing the preview.
aikya skills restore --target /absolute/project --scope project --all --operation OPERATION_ID
```

Native Forge uses an independent application root (AikyaForge on macOS/Windows,
aikya-forge on Linux), preserving older Harness installations. No v7 migration is
included. Windows uninstall runs through the verified external PowerShell installer
with `-Action uninstall`; a running manager EXE cannot safely remove itself.

Native builds bundle hash-pinned compatible binary parsers by default. Windows ARM64
currently has no reviewed Dart wheel and reports file inventory for Dart. Use
`--code-index none` only for an explicitly reduced bundle. Contributor source installs
still need the optional code-index extra for these parsers.

Reviewed .NET 8+ build/test/restore/publish/pack checks require
`--artifacts-path {artifacts}`. Forge allocates a unique private output per run while
continuing to inventory real source files in bin/obj. Each run must build its own
inputs; a later `--no-build` check cannot assume another run's private outputs.

The [Forge completion guide](aikya/docs/deployment/forge-0.2.0.md) documents installation,
release gates and the [external acceptance procedure](aikya/docs/validation/forge-provider-procedure.md).
Local memory, HTML updates and skill administration perform no inference. Measured
model tokens do not establish subscription quota percentages or token savings.

GENERATED BY AIKYA HARNESS
