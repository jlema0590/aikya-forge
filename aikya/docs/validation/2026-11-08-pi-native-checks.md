# Native Pi checks, review, recovery and role-safe resumption

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `46810c3` plus this block.
Environment: macOS ARM64, Python 3.13.18, Node 26.12.1, Pi 1.5.0.
Stable remains 7.2.2; the private runtime remains 8.0.0-alpha.0. No publication,
remote CI, native Windows/Linux acceptance or live provider use is claimed.

## Observed verification

| Check | Result |
| --- | --- |
| Complete isolated Python regression before the final order/locale corrections | 838 tests in 1157.394 seconds; no failures, two skips. |
| Final Python snapshot in restricted environment | 841 tests in 1203.603 seconds; one failure, four errors and two skips. All five issues involved denied local loopback access; affected modules are repeated separately below. |
| Unchanged memory modules with permitted local loopback | 4 live-view tests passed in 0.696 seconds and 10 integration tests passed in 18.725 seconds; no memory source change. |
| Final targeted check/admission cases | 17 passed; strengthened preview-drift assertion and project-language publication. |
| Final Pi SDK suite | 51 tests passed, no failures/skips, 17374.456917 ms. |
| Minimum supported Node 22.19.0 | All 51 Pi tests passed, no failures/skips, 17002.654166 ms; temporary official binary verified against SHA-256 manifest. |
| Strict/erasable TypeScript | Passed. |
| Wheel build and isolated package smoke | Passed without checkout imports or optional Claude SDK. |
| Pi SDK against dependency-free installed wheel | 12 tests passed, no failures/skips; actual SDK and installed Python services with fixture external transport. |
| Changed-source maintainability | 33 files, no errors, warnings or reported duplicates. |
| Real macOS PTY | Actual Red/Green, explicit review refusal in model-disabled mode, cooperative cancellation and graceful exit. |

The earlier 838 run is a separate snapshot; it does not stand in for the final
regression. The final full run is not reported as green. The four errors were
`test_authorized_snapshot_uses_latest_complete_publication`,
`test_custom_html_or_torn_report_is_not_served_as_current`,
`test_loopback_startup_does_not_require_hostname_resolution` and
`test_no_arbitrary_paths_foreign_host_origin_or_missing_capability`, each failing
at `socket.bind` with `PermissionError`. The failure was
`test_live_client_reuses_session_observer_and_releases_only_its_lease`, whose local
client exited with code 2. The unchanged affected modules are repeated with local
loopback access; their observed totals are recorded separately, not substituted for
the full-suite result. Final targeted check/admission tests pass 17 cases after
strengthening the language-preview-drift assertion; production source stayed fixed. The two known omissions are optional-dependency fallback with extras
already installed, and a PowerShell-only case where PowerShell is unavailable.
Fixture provider tests do not establish subscription compatibility or model quality.
Node 22.19.0 used a temporary official macOS ARM64 archive verified against the
[official SHA-256 manifest](https://nodejs.org/dist/v22.19.0/SHASUMS256.txt). It did
not replace the system Node. Other operating systems and Node 24 remain separate
acceptance targets.

## Native terminal evidence

In a disposable project, `/aikya-tests` confirmed explicit intent, scope, test paths,
Python executable and TAP definition. The first actual process failed with one
executed/failed test and zero skips. After changing the source value, the same native
run command previewed a fresh in-scope snapshot while preserving the frozen policy.
The next process completed with one executed test, zero failures/skips. Assessment
was `review_required`, `can_close=false`, `delivery_authorized=false`.

`/aikya-verify` review in model-disabled launch returned
`explicit_provider_model_required`, without inference. A separately confirmed slow
check was cancelled with Escape: actual status `cancelled`, no success counts,
failed assessment and no closure/delivery. The terminal waited for the result and
quit normally, restoring its modes. Public metadata contains bounded counts/hashes
rather than raw process output; each native run has a private signed host witness.

A separate minimum-Node macOS PTY smoke launched through the installed Python CLI,
read `/aikya-status`, displayed `/aikya-tests` input requirements and quit with exit
0, restoring terminal modes. Pi reported missing optional `fd` and skipped its
download in offline mode; no model, helper download or global Node change occurred.

The dedicated SDK reviewer test exercises a distinct session, actual durable fixture
usage and signed admission. A changed expected candidate is rejected before dispatch.
The headless author check tool cannot execute even an otherwise valid frozen policy;
it returns a host-action requirement. Native checks never become arbitrary shell tools.

## Native runner acceptance and toolchain availability

Separate disposable projects exercised the installed wheel with actual Node 26.12.1
`node:test` TAP and Go 1.27.3 `go test -json`. Each ran one failed regression, changed
only the source, then ran one passing regression through the native check service.
Both ended at `review_required`, without technical closure or delivery. The test
sources and frozen definitions stayed unchanged; temporary home/cache paths avoided
using a real project. These are local native runner results, not model acceptance.

Version probes also found Java 22.0.1, Maven 3.10.0 (using its own Java 27), .NET
8.0.302, Ruby 4.0.9, Swift 6.4.2 and Terraform 1.17.1. They were not treated as
executed application tests or accepted report adapters. Rust/Cargo and PowerShell
were unavailable. Flutter/Dart wrapper version probes attempted cache maintenance
outside the writable test area and failed; no permission escalation or SDK mutation
was performed. Their native workflows remain unverified.

## Reproduced regressions and corrections

Tests first reproduced undeclared successor source changes, a missing-count TDD type
error, definition-key sorting that changed the TDD regression check, reviewer-to-author
session resumption and language-policy omissions. Successor scope is now enforced,
missing counts cannot prove Red, and refresh follows the frozen check ordering.
Snapshot previews bind language; signed reviewer requests capture report language so
later policy changes do not alter idempotent publication. English remains the default.

Private host-observation tests refuse known-result recovery after witness removal,
without relaunching. They exercise cancellation before a refreshed candidate is
stored and during the actual owned process. Uncertain/pending/stale observations
require manual reconciliation. This is trusted local observation, not remote
attestation or protection against the same local account controlling native code.

Session tests resume the author's transcript even when a newer reviewer exists,
refuse role changes and preserve missing/corrupt role records. Older unmarked alpha
transcripts are not silently adopted. Project budgets, memory and evidence are not
erased when a new conversation is needed.

## Remaining product gates

The command matrix now has thirteen canonical native adapters, with documented limits.
Full ODD orchestration, remaining commands and user-selected skill lifecycle,
integrated installation/runtime migration, native OS acceptance and separately
budgeted real-provider trials remain open. The reviewer source packet is bounded to
6,000 UTF-8 bytes/20 paths; larger work must be split or escalated. Configuring CI
and finding a toolchain does not establish successful native workflows for its language.

[Command matrix](2026-11-08-pi-command-coverage.md) ·
[Preview guide](../deployment/pi-controlled-preview.md) ·
[Remaining plan](../plan/2026-11-08-aikya-v8-pendientes.es.md)

GENERATED BY AIKYA HARNESS
