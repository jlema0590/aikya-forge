# Pi local continuity, managed-profile migration and context overhead

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `b66c1aa` plus this
continuity block. Environment: macOS ARM64, Python 3.13.18, Node 26.12.1, Pi 1.5.0.
Stable metadata remains 7.2.2; the private Pi package remains 8.0.0-alpha.0.
No live provider, remote CI run or native Windows/Linux acceptance is claimed.

## Observed results

| Check | Result |
| --- | --- |
| Complete isolated Python regression | 829 tests in 1095.316 seconds; no failures, two skips. |
| Final Pi SDK suite | 46 tests passed; no failures or skips. |
| Strict/erasable TypeScript check | Passed. |
| Wheel build and isolated installed-wheel acceptance | Passed outside the checkout, without source imports or optional Claude SDK. |
| SDK against dependency-free installed wheel | Nine integration tests passed, without checkout Python imports or optional Claude SDK. |
| Changed-source/whitespace checks | 27 source files; no errors, warnings or reported duplicates; whitespace check passed. |
| Actual macOS terminal | Confirmed managed-profile migration, exact rollback and graceful exit; inspected persistent themes/budget and the explicit local footer. |

The Python snapshot was frozen throughout the full run. Later changes were
TypeScript, CI and documentation. The skipped checks were the optional-dependency
fallback case (this interpreter has parser extras) and a PowerShell-only acceptance
case (PowerShell is unavailable). They are not counted as passing native acceptance.
The installed dependency-free host received nine additional SDK integration checks
for writes, migration, review, onboarding and interactive/headless/idle observer
contracts. These use fixture provider transport; they do not duplicate the full
regression count or establish a final bundled Node distribution.

## Memory ownership

Initial Red reproduced the absent lifecycle service and SDK watcher wiring. The
passing tests run the actual local project observer: source changes made outside
Pi appear in generated HTML; closing one session keeps another session active;
closing the last lease stops observation. Both interactive runtime disposal and
awaited headless `close()` are covered through the real SDK and Python services.

A separate Red exposed missing idle renewal. The implemented local owner serializes
renewal, uses an unreferenced periodic timer, cancels future renewal during shutdown,
awaits any current request and then releases its own lease. The test observes actual
session-lease timestamps advancing without a model and verifies release afterward.
Disabled policies and unknown lifecycle events have no unwanted side effects.

## Managed legacy profiles and interrupted onboarding

The migration tests exercise real installer-produced profiles for development,
infrastructure and DevOps in ODD and SDD, using both documentation languages.
Migration preserves the methodology, source/document bodies, index policy, client
settings and skills. It records exact originals and signed metadata locally, writes
localized audit Markdown and updates the generated index. Rollback restores the
original bytes and removes a newly introduced selection file.

Adversarial cases preserve custom/unknown profiles and runtime selections, stale
previews, postmigration edits, unknown backup directories, modified originals and
custom audit reports. A simulated interruption between metadata effects leaves a
pending signed record; replay is refused and explicit rollback restores originals.
This is fault injection at that boundary, not proof for every possible OS crash.

Portable onboarding initially failed to resume after its ignore/profile writes.
It now requires a fresh preview and confirmation, preserves prior managed documents,
and completes missing ones. Initialized new projects can later be analyzed without
rewriting their profile choices. A regression verifies that actual application source
inside the `aikya` folder cannot be hidden during new-project initialization.

The actual terminal exercise adopted a disposable legacy profile, confirmed rollback,
exited normally and verified exact profile restoration, selection removal, unchanged
source and a footer-stamped audit report. It did not import personal credentials or
alter a real user's project installation.

## Local catalog and context filtering

The local model catalog returns at most 20 entries per page. Real-SDK tests verify
pagination, absence of credential values and zero provider dispatch/usage calls.
Model selection remains explicit at launch; no provider refresh is performed.

A transport fixture reproduced administrative catalog content entering the assembled
model context. The public Pi context handler now excludes catalog, budget, theme,
phase and migration display messages. Source/context queries are retained. The
integration verifies the catalog marker is absent from the actual provider context
while ordinary inference still follows the durable budget boundary. This supports a
specific overhead reduction; it does not quantify production token or quota savings.

The custom footer identifies the phase, selected model or disabled inference, local
recorded tokens and budget availability. Missing data is not an invented zero account
percentage. Startup uses Pi's quiet setting plus Aikya's own header; no SDK internals
or dependency source files are patched.

## Limits and next gates

Profile adoption/rollback is not a global/runtime installation migration. It preserves
existing client settings; global launchers, client deactivation, installation/update/
uninstall and native compatibility still need their own acceptance. The project
selection record does not make the stable `aikya` entry point a finished v8 launcher.

The [command matrix](2026-11-08-pi-command-coverage.md) now records eleven canonical
native adapters, with limited implementation/memory/catalog commands. Complete ODD,
skill lifecycle, checks/reviewer terminal orchestration, transverse TDD classification,
managed distribution and native/live-provider tests remain open in the
[implementation state](../plan/2026-11-07-aikya-v8-implementation-status.es.md).

GENERATED BY AIKYA HARNESS
