# Native doctor and scoped static quality

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `aecc73a` plus this block.
Local environment: macOS ARM64, Python 3.13.18, Node 26.12.1/22.19.0, Pi 1.5.0.
Stable remains 7.2.2 and the private runtime remains 8.0.0-alpha.0.

## Observed verification

| Check | Result |
| --- | --- |
| Native diagnostic host contracts | 11 passed in 0.173 seconds. |
| Existing static-quality contracts in a clean test environment | Five passed in 1.449 seconds. |
| Pi SDK suite, Node 26.12.1 | 59 passed, no failures/skips, 16886.671875 ms on the final Python source. |
| Pi SDK suite, minimum Node 22.19.0 | 59 passed, no failures/skips, 17204.738041 ms; before that correction. |
| Strict/erasable TypeScript | Passed. |
| Wheel build using installed build tools | Passed offline with `--no-isolation`; the initial isolated build could not resolve PyPI to provision build tools. |
| Installed-wheel presence-only profile matrix | 19 development/mobile/infrastructure/DevOps profiles returned configured state without new project files or readiness claims. |
| Dependency-free installed wheel outside checkout imports | All 11 diagnostic contracts passed in 0.237 seconds; all 59 Pi tests on Node 22 passed in 16874.521833 ms. |
| Installed-wheel invalid-input probes | 18 malformed/unsafe explicit-path requests refused; source unchanged and no extra project files. |
| Full clean Python regression with local loopback | 883 tests in 1141.019 seconds; no failures, two skips. |
| Real macOS terminal, minimum Node and installed wheel | Doctor, changed Python source, oversized Dart, private-path refusal and normal exit observed without inference/project documents. |
| Changed-source maintainability | Nine source files; no errors, warnings or reported duplicates. |

The existing `test_loop_never_completes_a_task_with_an_oversized_candidate` case
stopped on configured hooks requiring explicit review in the ambient user environment
and again in a previously populated temporary environment. A fresh disposable test
environment passed the same five contracts without changing permission enforcement.
The initial full regression was deliberately interrupted after adding a Red/Green
contract for the packaged Python minimum (3.10 rather than the legacy SDK's 3.9);
its partial results are not claimed as a complete run. The replacement regression
used the final source and a fresh disposable environment and completed without failures.
The two skips were the optional-dependency fallback with extras already installed
and a PowerShell-only case where PowerShell is unavailable. The changed source hashes
remained identical to the verified installed-wheel snapshot throughout this run.

## Source and output contracts

Doctor uses the existing validated profile and required-tool catalog. It reports the
actual current Python/Node/Pi versions, profile state, required command presence and
selected provider/model plus a configured-auth boolean through public SDK APIs. It
never reads credentials, connects to a provider, invokes SDK/version wrappers or
installs tools. Malformed/unknown profiles are preserved and marked invalid.

Android SDK layout is `not_checked`; Docker Compose reports parent-command presence
without executing its subcommand. Native iOS on other hosts is `unsupported_host`.
Tool versions/framework compatibility/provider connectivity remain unverified, and
`ready:null` prevents presence from being mistaken for acceptance.

Quality reuses the existing maintainability engine over captured explicit source and
size-exception bytes. Inputs are 1–20 unique files, at most 1 MB each/2 MB total;
links, secrets/private/control paths, missing files and unsupported suffixes are
refused. An external edit after capture does not alter the inspected snapshot.
Output identifies captured hashes/scope, at most 20 findings, total counts and three
example locations per duplicate. A Red case produced 110,356 bytes of duplicate
locations; the bounded output now passes the under-50-KB contract with truncation
shown instead of silently overflowing the host response.

Every code-index extension now participates in physical-line checks, including
Dart, JavaScript module extensions and Python stubs. Python/stubs additionally use
AST syntax, long-function and exact nontrivial body-duplication checks. Other
languages do not gain semantic analysis. Size exceptions apply only to their reviewed
file hash. Security scanning, tests, independent review and RDD admission are not run
or fabricated by this command. No project documentation or control state is written.

## Context, terminal and acceptance limits

Actual Pi sessions with fixture provider transport confirm zero provider dispatch
and budget calls for diagnostics. Administrative results stay outside later model
context; the subsequent ordinary request alone records its observed usage. The model
tool allowlist is unchanged. These are host commands, not new model capabilities.

In a real macOS terminal on Node 22 with the dependency-free installed wheel,
doctor displayed the actual versions and disabled provider, with unconfigured profile
and `ready:null`. Quality found a Python syntax error, refused a private auth path,
then observed the corrected Python hash/no syntax error and an oversized 1,001-line
Dart file with physical-line coverage. No project documents were generated; `/quit`
exited zero. These are operator observations of actual terminal output, not a claim
that administrative-only commands persisted an inference transcript. The pinned SDK
also displayed an offline `fd` availability warning; no helper download was enabled.

Nineteen of 28 canonical commands have native adapters with declared limits. Nine
commands, broader ODD/platform orchestration, global/GitHub/skill lifecycle, managed
runtime distribution, native Windows/Linux and live-provider acceptance remain open.
No remote CI, native cross-platform result, model quality or quota saving is claimed.

GENERATED BY AIKYA HARNESS
