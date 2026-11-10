# Native ODD task scope and independently reviewed completion

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `fc1a079` plus this block.
Environment: macOS ARM64, Python 3.13.18, Node 26.12.1 and 22.19.0, Pi 1.5.0.
Stable remains 7.2.2 and private runtime remains 8.0.0-alpha.0. No live provider,
remote CI, native Windows/Linux result or release is claimed.

## Observed checks

| Check | Result |
| --- | --- |
| ODD host contracts | 14 tests passed in 10.434 seconds. |
| Review contracts after workflow binding | 65 passed in 7.981 seconds. |
| Pi service contracts before final added coverage | 46 passed; later ODD assertions have their own results. |
| Pi SDK suite | 52 passed, no failures/skips; fixture external transports, actual SDK/Python services. |
| Minimum Node 22.19.0 | All 52 Pi tests passed, no failures/skips, 17133.274459 ms. |
| Complete isolated Python regression with local loopback | 855 tests in 1147.281 seconds; no failures, two skips. |
| Strict/erasable TypeScript | Passed. |
| Wheel build and isolated package smoke | Passed, without checkout Python imports or optional Claude SDK. |
| Minimum Node plus dependency-free installed wheel | All 52 Pi tests passed, no failures/skips, 16683.582417 ms; all 14 ODD host tests passed in 11.250 seconds outside the checkout. |
| Changed-source maintainability | 12 files, no errors, warnings or reported duplicates. |
| Actual macOS PTY on Node 22.19 | Cancellation, localized canonical preparation, task scope, English phases, unobserved-completion refusal, release and normal exit passed. |

The preceding [native-check report](2026-11-08-pi-native-checks.md) preserves a separate
full run with denied loopback tests and their 14-case permitted repetition. Those
results are not relabelled as a green full regression. This block's full run used
permitted local loopback from the start and completed without failures. Its two skips
were the optional-dependency fallback (parser extras already installed) and a
PowerShell-only case (PowerShell unavailable). Later changes were documentation only.
Provider fixtures do not establish model quality, subscription compatibility or savings.

## Executed ODD workflow

Explicit work facts select contained/read-only work without a feature dossier, or
substantial work using the existing localized canonical feature templates. Native
previews bind source, profile, language and previous task selection. Confirmation
never derives from the feature JSON. Existing custom documents and unknown private
bindings are preserved. A selected task must be ready, unfinished and bounded, with
explicit paths and frozen check names. Rebinding revokes prior source-write grants;
a foreign session, stale worklist or out-of-scope path cannot use the selection.

The complete workflow test prepares an actual ODD feature and selection, runs a real
failed regression, changes the source and runs Green with the same tests/policy.
It then admits a distinct reviewer session with actual durable fixture usage and a
candidate-bound host ticket. Only current reviewed scope, exact task objective,
acceptance criteria, check names and selection identity allow `done` recording.
Different reviewed intent/checks, raw passing claims and another session are refused.

A signed private completion reservation precedes the canonical worklist effect.
Interruption preserves uncertainty and prevents replay. Posteffect verification checks
source, Git base, all unrelated source and the actual admitted report hash. A changed
report/source blocks or invalidates the outcome rather than returning success. Existing
ODD reconciliation invalidates changed outcomes/dependents and preserves custom documents.

## Actual terminal

The model-disabled Node 22.19 terminal first cancelled preparation: no feature document
was created. A confirmed retry wrote Spanish `features/expected-value/spec.md` and
canonical state under `aikya/docs/`, with one footer and an index link. The footer
showed `plan`, then `implement` after confirmed task selection. Completion using an
unobserved change ID was refused and the task remained `todo`. Explicit release removed
only the known private selection, returned to `explore`, preserved documentation and
quit with exit 0. No model call or external skill installation occurred. This PTY
exercise does not establish an interactive real-provider author/reviewer workflow.

## Boundaries and remaining work

Canonical worklist status remains recorded data. Task completion records the accepted
candidate at that transition; writing new task metadata changes the full checkout
identity. It is not a perpetual technical acceptance of later metadata/source or a
delivery permission. The signed local reservation is not remote attestation or an
operating-system sandbox. Uncertain native completion still requires manual review.

The native facade supports bounded ODD tasks. Legacy descriptive check prose needs
explicit reconciliation with frozen check names before selection; it is not rewritten
automatically. SDD stays in its dedicated approved lifecycle. Remaining commands,
mobile/platform orchestration, skill lifecycle, standalone distribution and native/
live-provider acceptance remain open. Fourteen of 28 canonical commands now have
native adapters, with limitations in the [matrix](2026-11-08-pi-command-coverage.md).

GENERATED BY AIKYA HARNESS
