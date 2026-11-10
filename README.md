# Aikya Forge

[English](README.md) | [Español](README.es.md)

**Engineering workflows, project-local memory and controlled AI execution from the terminal.**

Aikya Forge combines a Python core with an interactive Pi terminal. It carries forward
Aikya's command adapters, templates and engineering controls into an independently
versioned repository. The initial development baseline is **0.1.0**.

This is a development baseline. Native macOS acceptance exists for the inherited
implementation; Windows/Linux native execution and real-provider acceptance remain
open. Source availability does not mean a public release or short installer is published.

## Quick start from source

Requirements: Python 3.10–3.13 with pip/venv, Node.js 22.19.0+ with npm, and Git.
Python 3.13 is recommended for the contributor test environment.

```sh
git clone --branch develop https://github.com/jlema0590/aikya-forge.git
cd aikya-forge
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'setuptools>=77' wheel build
python -m pip install --no-build-isolation -e .
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

## Components

| Component | Role |
|---|---|
| Python core (`src/aikya/`) | Onboarding, methodology, checks, memory, installation and durable evidence. |
| Pi terminal (`packages/aikya-pi/`) | Interactive commands, confirmations, themes, model selection and bounded sessions. |
| Command adapters | 28 canonical workflows with their documented native coverage and limits. |
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
verified payload. It generates checksum-bound shell/PowerShell entry scripts and
supports explicit install/update, retained rollback and conservative uninstall.

```sh
python scripts/ci/build_terminal_bundle.py --version 0.1.0 --output ../forge-native-0.1.0 --fetch-components
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

`VERSION` and the Pi package start at **0.1.0**. Future Forge releases use independent
semantic versioning. The [changelog](CHANGELOG.md) records Forge changes; the
[inherited changelog](aikya/docs/history/harness-CHANGELOG.md) preserves Harness history.

Commands, Python imports (`aikya`) and the Python distribution name (`aikya-harness`)
remain compatible in this first import. Operational update URLs point to this
repository. Older v8 payload identities remain readable for explicit compatibility;
they do not change Forge's version sequence.

Inherited release/Pages publication workflows remain scoped to the original Harness
repository. Tests run here; publication requires a separately reviewed Forge release
pipeline. The [documentation index](aikya/docs/indice.md) preserves previous plans
and evidence; references to v7/v8 inside historical records describe their original
snapshots, not Forge's current version.

## License

MIT. See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_LICENSES.md).

GENERATED BY AIKYA HARNESS
