# Aikya Harness architecture overview

## Package boundaries

| Package/resource | Responsibility |
|---|---|
| `src/aikya/cli/` and `installation/` | Command dispatch, onboarding, managed runtime installation and generated adapters |
| `src/aikya/workflows/sdd/` | Specification-stage documents, status and explicit approval workflow |
| `src/aikya/middleware/` | Host lifecycle observation, execution metadata, usage and native compaction continuity |
| `src/aikya/core/` | Opt-in agent loop, durable checkpoints and cumulative query budgets |
| `src/aikya/code_index/` and `context/` | Local verified source index, parser coverage and bounded task packets |
| `src/aikya/memory/` | Reviewed note handling and local HTML projection/observation |
| `src/aikya/documentation/` and `quality/` | Documentation preflight/gates, templates, source checks and content-free efficiency measurements |
| `src/aikya/routing/` and `tools/` | Routing advice and controlled check execution/evidence |
| `src/aikya/resources/` | Distributed commands, agents, skills, project templates and viewer assets |

## Task and data flow

Onboarding discovers the project, collects approved choices and installs managed
assets. Native lifecycle events reach the installed observer. An implementation
prompt can receive a bounded packet from the shared context service, which verifies
checkout identity, scope and source hashes. An unavailable index falls back to a
bounded source read without widening an explicit allowlist.

Python uses the standard-library AST. Optional pinned grammars add Java,
JavaScript/JSX, TypeScript/TSX, C#, Go and Dart declarations. Unsupported formats
remain file inventory. Parser selection is explicit and installed in the effective
managed interpreter from verified binary release artifacts.

The opt-in loop executes its existing phases and records actual result usage.
Review shares accumulated limits with Implement. Local deterministic check evidence
may be reused only after an explicit binding verifies candidate, check and environment.
Documentation preflight uses the same requirements as the closing guard. Neither
metadata nor a compacted summary creates an approval or passing security evidence.

## State and trust boundaries

- `.aikya/code-index.json` holds reviewed project policy. SQLite, execution records,
  budgets and compaction metadata remain project/worktree-local in `.harness/state/`.
- `aikya/docs/memory/` contains reviewed notes and a regenerable viewer projection.
  The observer does not approve notes or overwrite custom documents.
- Context treats source text as untrusted data. Identity/hash validation, exclusions,
  symlink protection and bounded output apply before reuse.
- Native compaction belongs to the host. Aikya stores bounded references and pending
  checks, then refreshes current source on continuation; no additional summarizer runs.

See [Memory details](local-memory.md), [token policy](../tools/token-policy.md),
[observability](../operations/observability.md) and
[validation limits](../validation/2026-10-29-token-efficiency.es.md).
There is no vector store, remote memory service or claim of inferred runtime call graphs.

## Command scopes and workspace policy — 7.2.2

The installation layer verifies the complete global public-command set and required
runtime manifest entries before reusing it. Registration can then avoid a redundant
project bootstrap runtime. Onboarding still installs project policies, stack skills
and its managed support adapters. Existing runtimes and project data are retained.

Reconciliation is limited to the explicitly selected project. Only command folders
containing one unchanged, known managed SKILL.md are retired after a verified backup
under .harness/command-backups/. Preflight retains old runtime provenance across an
upgrade. Edited or extended folders remain visible with a review notice. Preview
reports reuse/retirement without writes; unknown global provenance retains standalone
local installation. Updating global registration does not scan other projects.

middleware.workspace supplies a generated workspace_guard adapter, native PreToolUse
permission checks and concise session guidance. Recognized worktree creation asks the
host for permission; ordinary edits and branch creation do not. This is a host policy
with best-effort command recognition, not a shell sandbox.

## Controlled Pi preview — November 8

The branch now adds one-use host-granted source writes, durable call accounting,
local note/theme commands, portable onboarding and canonical SDD transitions.
A signed current SDD task scope is required for SDD writes. Independent reviewer
admission can grant technical closure after current checks; delivery stays separate.
An optional frozen TDD policy requires an executed failed ancestor and unchanged tests.

The [current controlled-runtime architecture](2026-11-08-pi-controlled-runtime.md)
details bounds, recovery, trust and open gates. The older read-only reports describe
earlier snapshots. No managed v8 installer, full command parity or native/live-provider
acceptance is claimed. Memory remains local; no Engram service was introduced.

## Local continuity and managed-profile migration

Pi lifecycle now reuses the existing observer for external edits, renews its lease
locally during idle periods and awaits renewal before releasing that session.
Headless consumers use the returned async `close()` helper. Reviewed memory remains
project-local; no additional model or store is introduced.

Explicit managed legacy-profile migration has signed backups, guarded restoration
and localized audit Markdown. It preserves application/document bodies, memory policy
and client settings. Interrupted onboarding uses a fresh confirmed preview. The model
catalog is local/paginated; administrative displays are excluded from model context.
See [current architecture](2026-11-08-pi-controlled-runtime.md).

## Native executed-evidence loop

Pi now exposes frozen check snapshots/runs, independent budgeted review and known
host-observation recovery through native commands. An identifier-only author check
tool still requires host confirmation. Ordered TDD policy and declared successor scope
are preserved; missing counts cannot prove Red. Private host witnesses bind execution
metadata, and explicit session roles prevent reviewer conversations becoming authors.
Generated snapshot/review documents follow project language and indexed footer rules.
See [the detailed architecture](2026-11-08-pi-controlled-runtime.md).

## Native ODD evidence continuity

The native feature command now reuses canonical ODD templates/state with confirmed
preparation, bounded status, signed task scope, guarded completion and reconciliation.
Existing source-write/check controls share that task revision. Independent acceptance
must match task intent/files/checks; a worklist claim is insufficient. Signed pending
operations prevent uncertain replay, and unrelated source/report drift refuses success.
Task metadata remains recorded transition evidence, with delivery separately authorized.
See [ODD validation](../validation/2026-11-08-pi-odd-workflow.md).

## Native selected skills

Selected-skill native adapters include bounded project skill status,
local package planning and confirmed installation. Canonical validation/signing/
documentation are reused; original bytes are retained and imported code is not run.
Only explicit verified author invocations enter context and unlock bounded references;
reviewers stay separate. Integrity is enforced before actual provider dispatch,
with admin output excluded from prompts. Global/GitHub/update/uninstall and full
compatibility remain separate native work. See [current evidence](../validation/2026-11-08-pi-selected-skills.md).

## Native diagnostics

The native diagnostic host facade shares profile requirements and static quality
contracts. Doctor observes runtime/configuration/presence without invoking SDKs;
quality inspects explicit bounded captured bytes. Actual version/framework checks,
security scanning and tests remain separate approved execution evidence.

## Native reviewed documentation

Declarative profiles share portable onboarding. Living-document native adapters
reuse canonical templates/section merging and signed selected-source/page ownership,
with confirmed before/after content, bounded records and existing index/memory
maintenance. Documentation baselines and REQ records remain separate from task state,
executed check evidence and independent-review admission.

## Native project and generator adapters

Project planning/recording, captured-input infrastructure proposals and staged known
generators now use separate bounded host confirmations. Shared generation preserves
owner files, binds current source/profile/locale/task and records actual writes.
Infrastructure validators share one canonical catalog and retain process observations,
not fabricated tests. No model shell or target-project helper import is introduced.
See [bootstrap validation](../validation/2026-11-09-pi-bootstrap-generation.md) and
the [current command matrix](../validation/2026-11-08-pi-command-coverage.md).

## Native engineering context

The experimental terminal now has limited adapters for all 28 canonical commands.
Architecture interpretations require verified selected excerpts; bug reproduction
uses native regression observations and unchanged-test lineage. Canonical document
transactions preserve existing pages/registers. Mobile context is typed inside the
existing ODD state or signed SDD selection, with SDK/build/simulator acceptance kept
separate. See the [command limits](../validation/2026-11-08-pi-command-coverage.md).

## Private native distribution under acceptance

`cli/arguments`, `dispatch`, `queries`, `analysis` and `loop_command` preserve the
support API while bare `aikya` selects `cli/terminal`. `installation/managed_runtime`
reads one signed application receipt and verifies exact Python/Node/runtime roles,
identity, inventory and file hashes. It does not execute payloads while resolving.
The optional development path remains explicit.

`managed_wheel`, `managed_node`, `managed_archives`, `managed_payload` and
`managed_distribution` capture/stage private versions and verified official inputs.
`managed_inputs` fixes origins/architectures and records upstream requirements;
`managed_entries` emits pinned transport-verifying scripts without an external Python.
They share portable paths and bounded transport with existing services.

`managed_install` reuses the application owner/lock for reserved final-path copies,
fixed probes, readback and atomic signed current promotion. Previous versions remain
for rollback; complete effects reconcile without replay, partial/custom effects block.
`managed_migration` backs up v7 installation metadata without transforming client
histories or project memory. Project profile migration stays in `migration_v8`.
Application-level signing data/global chosen skill packages do not create global
project memory. Native platform/provider/stable release acceptance remains separate.

The terminal startup guard scans bounded ancestry before classifying a directory as
unversioned. Git working-tree/gitfile/bare markers retain real tracked/ignore checks.
Identical active installation is an inert success; updates advance immutable semantic
versions, while downgrades use the retained rollback path.

GENERATED BY AIKYA HARNESS
