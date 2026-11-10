# Controlled Pi runtime: observed validation

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `fc1afbf` plus the
controlled-runtime changes in this delivery. Host: macOS ARM64, Python 3.13.18,
Node 26.12.1, npm 11.20.0, pinned Pi 1.5.0. Stable version: 7.2.2; private runtime:
8.0.0-alpha.0. No live provider request, publication or native Windows/Linux run.

## Results

| Check | Observed outcome |
| --- | --- |
| Complete isolated Python regression | 817 tests in 1002.121 seconds; no failures, two skips. |
| Pi SDK/service suite after final TypeScript changes | 40 tests passed, no skips/failures. |
| TypeScript strict/erasable syntax check | Passed. |
| Installed-wheel acceptance | Passed outside the checkout, without source imports or optional SDK. |
| Wheel build | Built `aikya_harness-7.2.2-py3-none-any.whl` outside the checkout. |
| Locked npm installation | Offline disposable `npm ci`, scripts disabled; 125 packages installed. |
| Changed-source size/duplication check | 64 files examined; no errors, warnings or reported duplicates. |
| Whitespace check | `git diff --check` passed. |

Python regression used an installed editable package, a disposable HOME/config/cache,
no inherited PYTHONPATH and local loopback permission for memory-server tests. Later
changes were TypeScript, CI and documentation; no Python source changed after the
full Python run began. The wheel's separate installed-package acceptance passed outside the checkout. These counts are not a native compiler/language acceptance matrix.

## Tests that initially failed and then passed

Observed Red before implementation included absent write authority, durable budget,
reviewed-note service, theme preferences, memory events, reviewer admission, recovery,
controlled SDK dispatch, provider-header panel and portable onboarding. Subsequent
regressions explicitly reproduced missing SDD task binding, absent native SDD stages,
Green without Red, changed tests reusing old Red, Windows-sized failure codes,
invalid quota reset dates, duplicate inference wrappers, oversized prompts, missing
authentication and confirmation controls hidden by long content.

Corrections discovered through real integration included a provided reviewer session
manager being ignored, which broke ticket/session binding; TAP fixtures writing to a
file instead of the actual stdout contract; and TypeScript parameter properties that
passed typechecking but failed Node's strip-only execution. The final suite verifies
the corrected behavior rather than counting those failed attempts as success.

## Real SDK and host boundaries

The integration uses the real Pi ModelRuntime/AgentSession and real isolated Python
subprocesses. Only the external provider transport is a local fixture. Tests observe
admission before dispatch, once-only counters before terminal completion, refusal of
later calls after exhaustion, unknown-usage preservation, separate reviewer identity,
signed admission and technical closure without delivery authority. No real model
quality, credential validity, billing, subscription quota or token saving is asserted.

Source-write tests cover actual file effects, approval denial, content/source/session
and project mismatch, expiry, concurrent replay, protected destinations, symlinks,
footers and absence of secret/grant material in replies. SDD binding tests cover
missing stage approval, out-of-scope files, other sessions, changed state and modified
signed bindings. Portable onboarding spans three project kinds, two methodologies
and new/existing projects, with canonical localized documents and no Claude assets.

Review tests cover current frozen checks, independent measured calls, no self-review,
no JSON-only approval, idempotent replay, tampering, stale candidates, high findings,
successors and history. Recovery attaches only known execution metadata and does not
relaunch. TDD tests execute a genuine failed TAP case, then Green, and reject missing
Red or edited tests. Large Windows exit-code validation is a cross-platform contract
fixture here, not observation of a native Windows process.

## Actual macOS terminal exercise

A disposable project was opened through the Python `aikya terminal` launcher and
real Pi interactive UI. Theme preview cancellation created no theme preference;
confirmation applied light and reopening retained it. A confirmed 1,000-token/five-call
budget survived reopening with no usage events. Memory status remained unavailable
before initialization and did not create an index just by being read.

A long onboarding confirmation initially hid its choices. The corrected scrollable
component keeps controls visible, refuses Enter while content remains below the
viewport, supports scrolling/End, and cancels with Escape. A cancelled onboarding
created no profile. A later approved SDD initialization created canonical documentation,
local index/HTML and no `.claude`, `CLAUDE.md` or copied runtime. Local status reported
SDD/development, and the terminal exited normally with terminal modes restored.

The optional `fd` binary was unavailable; offline mode skipped its download. No tool
or SDK was installed into the test project. The light palette does not reconfigure
the user's terminal-emulator background, and accessibility/contrast on all emulators
has not been certified.

## Open acceptance and implementation work

The [command matrix](2026-11-08-pi-command-coverage.md) records ten canonical native
adapters, including limited memory/implementation commands. It does not call generic
chat complete command parity. The [implementation state](../plan/2026-11-07-aikya-v8-implementation-status.es.md)
retains external-edit watcher integration, 7.x migration/rollback, interrupted
onboarding recovery, full ODD/skill/workflow orchestration, managed installation,
long-session/native compaction, real-provider tests and native release acceptance
as open. Host APIs are not substitutes for missing terminal workflows.

GENERATED BY AIKYA HARNESS
