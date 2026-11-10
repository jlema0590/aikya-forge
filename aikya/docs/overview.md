# Aikya Forge project overview

Forge starts at version **0.1.0** in `jlema0590/aikya-forge`. It imports the current
Harness implementation and preserves its v7/v8 records as historical evidence.
See [the Forge change record](changes/REQ-20261110-f0900100.md) for versioning,
compatibility and outstanding acceptance boundaries.

Aikya Forge is a Python package that installs project workflows, Claude Code
instructions and local execution tools. The distributed command catalog contains
28 Forge commands. New and existing projects select ODD or SDD through their
onboarding workflow; methodology approvals remain explicit.

The authoritative implementation is under `src/aikya/`. Installation provisions
managed runtimes and generated project adapters rather than requiring consumers
to import repository-root scripts. Resources include commands, engineering
agents/skills, documentation templates and the local Memory viewer.

Project documentation and audit records live in `aikya/docs/`. Derived per-project
state lives in `.harness/state/`; reviewed code-index policy lives in
`.aikya/code-index.json`. Memory indexing and HTML export are local operations
without model calls. Assistant interpretation of retrieved source still consumes
tokens. Static source relationships do not establish runtime behavior.

Version 7.2.0 adds bounded current-source context, explicit pinned Dart parser
installation, compact backend output, documentation preflight, cumulative loop
budgets and manual-first native compaction continuity. Existing files, approvals
and security checks retain their independent controls.

- [Architecture](architecture/architecture-overview.md)
- [Local Memory and viewer](architecture/local-memory.md)
- [Token policy](tools/token-policy.md)
- [Observability](operations/observability.md)
- [Installation and rollout](operations/deployment.md)
- [Testing](plan/testing.md)
- [v7.2.0 local validation](validation/2026-10-29-token-efficiency.es.md)

The current validation is local to macOS ARM64/Python 3.13. Native CI on other
supported hosts and a real Claude SDK/token experiment remain separate pending
checks. This document does not authorize deployment or claim measured quota savings.

## Private v8 controlled preview

The Pi branch adds host-confirmed source writes, durable local budgets, reviewed
notes, light/dark preferences and portable ODD/SDD onboarding. It reuses the canonical
SDD engine without installing Claude assets. Execution/reviewer evidence and optional
TDD policies are implemented as bounded host contracts. Full terminal workflows,
migration and managed distribution remain open; stable installers are still 7.2.2.

See the [preview guide](deployment/pi-controlled-preview.md),
[current architecture](architecture/2026-11-08-pi-controlled-runtime.md) and
[implementation status](plan/2026-11-07-aikya-v8-implementation-status.es.md).

## Local continuity and migration progress

The Pi preview now observes external source edits, maintains an idle local lease and
releases session ownership on shutdown. Known managed legacy profiles have explicit
migration/rollback with signed originals and indexed audit Markdown; onboarding can
recover from an interruption after a fresh preview. `/aikya-models` reads a bounded
local catalog. Administrative displays are excluded from model context.

See the [continuity evidence](validation/2026-11-08-pi-memory-migration.md).
Integrated installation and full command/native/provider acceptance remain open.

## Native executed checks and review

Thirteen canonical commands now have native Pi adapters, with limited coverage
clearly marked. `/aikya-tests` freezes intent/scope/ordered policy and executes only
a confirmed frozen check; `/aikya-verify` exposes current assessment, independent
budgeted review and known private host-observation recovery. Cancellation waits for
the observed result. The author check tool cannot bypass UI confirmation. Role-bound
resumption preserves author/reviewer separation. Generated reports follow project
language; passing tests and technical closure still do not authorize delivery.

See [native validation](validation/2026-11-08-pi-native-checks.md) and the
[current command matrix](validation/2026-11-08-pi-command-coverage.md).

## Native ODD task progress

Fourteen canonical commands have native adapters. `/aikya-feature` now reuses canonical
ODD templates/state, signed task scope and current matching independent evidence for
completion recording. Previews and uncertain effects stay guarded; SDD remains separate.
This is bounded workflow adaptation, with remaining platform/skill/distribution and
real-provider acceptance still open. See [ODD validation](validation/2026-11-08-pi-odd-workflow.md).

## Explicit local skill adaptation

Native skill status/planning/installation brings canonical adapter coverage to
seventeen commands. Only chosen local project packages are copied as immutable data;
explicit verified author invocation is required for model context/reference access.
The actual model gate checks integrity before spending a call. Original bytes,
localized audit/comparison and index remain local. Other source/scope/lifecycle and
standalone release acceptance remain open. See [skill evidence](validation/2026-11-08-pi-selected-skills.md).

## Native diagnostic commands

The private Pi preview exposes `/aikya-doctor` for configuration/tool presence and
`/aikya-quality` for bounded explicit-file static inspection. Both are local queries
without inference or project documentation writes. Neither establishes framework
compatibility, security acceptance, passing tests or delivery authorization.

## Native profile/documentation commands

The private Pi preview now supports declarative `/aikya-answers`, verified template
catalogs/reviewed pages through `/aikya-docs`, and selected-source baseline/REQ sync
through `/aikya-docs-sync`. All effects require native confirmation. No-change queries
create no documents; localized records retain footer/index and do not certify tests.

## Native bootstrap preview

The private v8 terminal now adapts explicit project plans/records, named infrastructure
artifacts and staged known generators. Source/profile/locale/task-bound confirmations
preserve owner files and retain actual generation/process observations. Infrastructure
validators share the canonical catalog and do not certify tests or deployment.
See the [preview guide](deployment/pi-controlled-preview.md). Stable 7.2.2 and private
8.0.0-alpha.0 remain unchanged; full product acceptance is still in progress.

## Native engineering preview

Limited native adapters now cover all 28 canonical commands. Architecture recording
uses current source excerpts, bug status derives from observed native regression and
independent review, and mobile task context stays explicit in the canonical engines.
These commands preserve localized documents and use no administrative inference.
Adapter presence does not complete end-to-end workflow, distribution, mobile SDK or
real-provider acceptance. See the [command matrix](validation/2026-11-08-pi-command-coverage.md).


## Forge branding and native installation

The Python distribution is `aikya-forge`. New documents use the Forge signature;
known inherited signatures and functional paths remain readable. Native builds
produce an offline installer ZIP with macOS/Windows double-click entries and a
manual platform matrix. See [installation](deployment/pi-managed-terminal.md).

GENERATED BY AIKYA FORGE
