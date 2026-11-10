# Runtime and parser rollout

The 7.2.0 managed installer accepts `--code-index none|dart|all`. New installations
default to none. An update without the option preserves its scope-specific receipt.
Selection is independent from Mods and methodology. The managed interpreter receives
verified binary wheel artifacts; project adapters use that interpreter/package.
No source compiler, model request or hidden package-index resolution runs during
installation. Missing, corrupt or incompatible wheels stop activation of the new
candidate and leave the previously active interpreter available.

The clean installer builder installs the locally built Aikya wheel before loading
the parser manifest; building a src-layout distribution alone does not make it
importable. This step uses `--no-deps --no-index --find-links dist`.

Release preparation downloads pinned CPython 3.10–3.13 wheels for glibc Linux x86_64/
aarch64, musl x86_64, macOS arm64/x86_64 and Windows amd64. Each asset joins the
release SHA-256 manifest. Linux musl aarch64 lacks the pinned core binary; Windows
ARM64 is not verified. Those platforms can retain dependency-free inventory.
A downloaded platform wheel is not proof of native execution. The native CI matrix
must execute installation/update tests on its host before release approval.

Use `aikya-manage doctor` for observed managed parser capability. The installer
retains custom settings, project documents and prior environments referenced by
initialized projects. Updates do not silently enable automatic compaction or change
models/effort. Native project compaction requires explicit `context-policy` opt-in
and an installed observer; unsupported hosts retain the manual command.

The branch has no deployment authorization implied by passing local tests. Native
CI, live model experiments and publication have separate recorded status in the
[validation report](../validation/2026-10-29-token-efficiency.es.md).

## Scope correction rollout — 7.2.2

Publish the reviewed 7.2.2 release through the existing release pipeline before asking
users to update from public URLs. Update global Aikya first. In each affected project,
run reviewed project registration with aikya-setup --scope project --target <project>,
or use an approved /aikya-analyze --refresh from the updated command. Restart the host
session if its command discovery is cached. Global update alone does not reconcile
every project. Preserve customized conflicts for explicit review.

Verified managed duplicates are backed up under .harness/command-backups/, outside
host skill discovery. Project policies, Memory and existing support runtimes remain.
Registration which reuses global commands creates no redundant .aikya/runtime.
A standalone local installation remains available when global verification fails.

The installers CI matrix includes command-scope and workspace-policy tests on its
native hosts. Local macOS results do not establish Windows/Linux execution. Worktree
checks require a host implementing PreToolUse permissionDecision=ask; external shells
and arbitrary scripts are outside this policy. No account-quota savings are inferred.

## Experimental Pi runtime branch — v8 development

The first route B slice is private source development. `packages/aikya-pi` pins
Pi 1.5.0 and has no globally installed binary. It does not replace the current
Python CLI, add Pi to stable installers or alter stable update resolution. Keep
VERSION at 7.2.2 until prerelease selection and packaging are implemented.

Contributor setup uses `npm ci --ignore-scripts` inside `packages/aikya-pi` and
an installed checkout Python package in a temporary environment. No global Pi or
Gentle installation is needed. Session storage is project-local, and general
execution tools/discovered extensions remain disabled in this prototype.

Before any v8 release, complete launcher distribution, RDD review admission,
command parity, migration and native installation/update/uninstall acceptance.
The new Pi CI matrix is defined for macOS, Windows and Linux; it has not run yet.
See [implementation status](../plan/2026-11-07-aikya-v8-implementation-status.es.md)
and [observed validation](../validation/2026-11-07-aikya-v8-first-slice.md).

## RDD/context development prerequisites

The Pi bridge now uses isolated Python mode (`-I`). Install the checkout package
in the interpreter supplied by the host; setting PYTHONPATH is not a substitute.
Keep the current tools read-only. The new `aikya review` CLI may preview or store
local metadata and explicitly execute frozen checks, but cannot approve delivery. Candidate state
lives under the project's `aikya/docs/validation/<change-id>/` dossier.

The private runtime remains 8.0.0-alpha.0; stable installers remain 7.2.2. No new
release/update artifact is published by this work. Follow the
[RDD trust boundary](../architecture/2026-11-07-rdd-contracts.md) before exposing
mutation or review-result admission in a later phase.

## Development terminal and check executor — November 8

`aikya terminal --runtime-dir <checkout>/packages/aikya-pi --target <project>`
launches the experimental read-only Pi UI. It requires Node 22.19.0 or later,
installed package dependencies and the trusted Python package in the invoking
interpreter. Selecting a package directory authorizes its executable code; manifest
matching is compatibility validation, not a publisher signature. No stable
installer downloads this private runtime yet.

Startup adds the local Pi state exclusion to the target's ignore file, verifies
effective Git rules and refuses already tracked state. It never silently removes
tracked files. Missing/invalid prerequisites stop launch; no global Pi fallback,
credential import, model request, tool download or native self-update is enabled.
The SDK host API itself remains trusted and is not a filesystem sandbox.

The support CLI can run a check only after an approved snapshot freezes its
definition. Test commands have their normal host privileges and may have side
effects; no OS containment is claimed. Do not automatically replay interrupted
attempts. Manual reconciliation and reviewer admission remain open. See the
[executor/terminal contract](../architecture/2026-11-08-executor-terminal.md) and
[observed acceptance](../validation/2026-11-08-aikya-v8-executor-terminal.md).

## Current controlled preview

The default launch still disables model calls. Explicit provider/model selection,
an available local budget and configured authentication enable the experimental
controlled path. Native host commands confirm source writes, onboarding, SDD stages,
budget changes and theme activation. Default local mode is not a promise of zero
administrative writes after the operator confirms an operation.

Use the [current preview guide](../deployment/pi-controlled-preview.md). The earlier
read-only descriptions above are historical. Independent admission and known-result
reconciliation are now host APIs, with no automatic delivery or replay of uncertain
processes. The stable installer still does not distribute this private runtime.
Migration, full command parity and native/live-provider release acceptance remain open.

## Local migration and observer lifecycle

`/aikya-migrate` previews adoption of a known managed legacy profile with the existing
methodology. Signed local originals enable a confirmed guarded rollback, including a
known interrupted metadata commit. Source, document bodies, index/notes policy, client
settings and skills remain preserved. Rollback exits the interactive Pi session and
retains its indexed audit Markdown. This does not replace a global installation.

The existing external-edit watcher is now session-owned from Pi, including idle
heartbeats and async headless teardown. See the [preview guide](../deployment/pi-controlled-preview.md)
for exact inputs, limits and remaining distribution/native acceptance.

## Native check preview update

The private terminal now includes `/aikya-tests` and `/aikya-verify` for frozen checks,
independent budgeted review and known host-observation recovery. The author check tool
requires interactive confirmation; test processes retain normal machine privileges.
Session-role records prevent reviewer-to-author resumption. Older unmarked alpha
transcripts need explicit review and remain preserved; start fresh without `--resume`.
This source preview still requires the explicit runtime directory. See the updated
[guide](../deployment/pi-controlled-preview.md) and [validation](../validation/2026-11-08-pi-native-checks.md).

## Native ODD contributor preview

The private source runtime now exposes bounded `/aikya-feature` preparation/status/
selection/completion/reconciliation/release over the canonical engine. Task selection
constrains source writes and binds native checks; current matching independent review
is required before completion recording. This does not change stable installation,
activate legacy client hooks or complete standalone v8 distribution. See the
[preview guide](../deployment/pi-controlled-preview.md) for exact inputs and limits.

## Selected native skill preview

Private source builds can inspect and confirm local project packages through native
skill commands. Installation retains exact originals and normalized data, requires a
restart for explicit controlled-author use, and preserves existing client settings.
No global/GitHub source, dependencies or imported scripts are activated automatically.
This does not replace stable chosen-skill installation or complete the standalone v8
lifecycle. See the [guide](../deployment/pi-controlled-preview.md).

## Native diagnostic operation

Use `/aikya-doctor` to inspect the selected runtime/profile and required command
presence without executing SDKs or contacting providers. Use `/aikya-quality`
with explicit paths for captured-byte maintainability checks. Do not treat found
commands, auth configuration or no static findings as deployment approval.

## Native documentation operations

Validate a declarative new/existing profile with `/aikya-answers`; confirm before
portable onboarding effects. Use `/aikya-docs` to inspect template fields and review
specific living-page changes. Capture a selected-source `/aikya-docs-sync` baseline
before changes, then review sync in the same author session. Preserve custom pages
and pending operations for explicit reconciliation. Documentation recording leaves
technical checks and deployment approval separate.

## Native bootstrap operation

Use project/infra plans before recording/generating. Review named artifact batches;
existing owner files are preserved. Resolve a concrete scaffold recipe/version, then
confirm private staging execution, inspect its returned paths and confirm copying
separately. Local validators report actual process outcome, never fabricated tests.
Preserve pending private operations and original project files after uncertainty;
automated reconciliation remains open. The [preview guide](../deployment/pi-controlled-preview.md)
lists exact commands, limits, status and cancellation behavior. Official SDK/native
platform acceptance and managed v8 installation remain separate release gates.

## Native engineering workflows

Record architecture interpretations only with current source excerpts. Use native
regression status to distinguish a supplied bug report, reproduced failure, positive
checks and independent acceptance; finalize living pages before final candidate
verification. Preserve canonical bug IDs/custom edits and uncertain operations.
For mobile work, choose platforms inside the profile and use the existing ODD or
approved SDD task. SDK presence does not authorize build/deployment or prove device
acceptance. The [preview guide](../deployment/pi-controlled-preview.md) documents the
explicit JSON contracts, localization, limits and remaining native acceptance.

## Private v8 managed entry under acceptance

The [private distribution guide](../deployment/pi-managed-terminal.md) describes
native build artifacts and conservative version management. It does not deploy the
public Pages or change stable 7.2.2. Native entry scripts are version/hash pinned;
repeating installation of the current exact payload is inert, and a newer owned
installation follows the reviewed update path. Replaced same-version bytes and
update downgrades are refused; retained rollback is explicit.

An unversioned directory does not require Git to start the terminal. A Git working
tree, gitfile or bare-repository marker still requires actual Git validation before
private state is written. Client state, project notes and original registrations
remain separate from application activation. Native Windows/Linux and live-provider
acceptance are not inferred from local artifact availability or CI configuration.

GENERATED BY AIKYA HARNESS
