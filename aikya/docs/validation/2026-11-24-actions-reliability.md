# Forge Actions reliability validation — 2026-11-24

## Reproduction and focused correction

Release run [45211872718](https://github.com/jlema0590/aikya-forge/actions/runs/45211872718)
ran 1,265 source tests with 24 errors and two failures. A disposable regular-wheel
environment reproduced seven missing-helper errors in four document-path tests.
The same environment, after contributor build prerequisites and editable source
installation, passed all four document-path and four template-path tests. This
matches the corrected verify job's installation mode. Separate installed-wheel
acceptance was retained.

Release planner: eight tests passed. External acceptance gate policy: four tests
passed. The real pending acceptance report was also checked and correctly rejected;
its status or evidence was not modified. Release version contract passed for the
unpublished 0.2.0 version.

## Pi runtime

The exact Node 26.13.0 runtime passed twelve focused repetitions of the previously
intermittent final-record resumption case. A complete diagnostic run passed, and
temporary instrumentation was removed. The final complete run with the strengthened
fixture passed: 130 cases, 129 passed, one Windows-only test skipped, zero failures
or cancellations. TypeScript type checking passed.

The fixture now checks the actual declined recording reason/dialog before resume,
the second recording confirmation and the absence of SDK errors. Call counters,
original deadlines and source bytes/mtime checks remain. No runtime workaround,
longer deadline, model replay or automatic retry was introduced. These passing
runs do not establish the historical intermittent production cause.

## Workflow syntax and hosted runner diagnosis

Actionlint 1.7.12 initially rejected only queue:max, a newer supported GitHub
concurrency property. A second check excluding exactly that unsupported-schema
diagnostic passed. The setting is documented in
[GitHub's concurrency guide](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
and was preserved; the existing hosted workflow already accepted it.

Native run [45211782923](https://github.com/jlema0590/aikya-forge/actions/runs/45211782923)
passed six targets and had an unstarted macOS ARM job. GitHub annotations identify
hosted-runner acquisition/capacity constraints. Its job-only retry passed.
The failed macOS Node job in [45211783306](https://github.com/jlema0590/aikya-forge/actions/runs/45211783306)
was also retried without code or limit changes and passed.

## Complete Python and hosted correction checks

The complete isolated Python baseline passed 1,335 tests with five skips. The
correction branch has not been merged; hosted results and the remaining native
observer investigation are recorded below.

Publication still requires genuine current real-provider acceptance in the agreed
external environment. No release, tag or installer Pages is published by these
local checks.

## Windows observer shutdown test

The new PR run exposed Local memory / Windows / Python 3.13 failure at
`MemoryIntegrationTests.test_session_hooks_start_and_stop_only_the_project_observer`.
It asserted Stopped before awaiting the owned observer's exit. The status could
still be Up to date while the final writer/exit was completing; the existing
bounded child cleanup subsequently finished without error.

The tests now await that actual exit before reading the final status, reusing
the existing 12-second wait and kill-on-timeout behavior. The independent early
8/10-second status poll is removed; observer/runtime limits are not increased.
The same coordination is used by the Pi lifecycle case. No production observer
behavior or SessionEnd semantics changed. All ten memory integration tests and
both Pi lifecycle tests passed locally after the correction.

## Hosted results and remaining installed-observer investigation

Latest-head PR b7f163a completed all 43 checks successfully, including all four
Python versions, all six Pi OS/Node combinations, memory/browser acceptance,
clean installers and seven native targets. Hosted Python 3.13 passed 1,335 tests
with seven skips. The complete isolated local baseline passed 1,335 tests with
five skips. The original macOS Node and native macOS ARM job-only retries passed.

Preparation run 45352336115 passed verify (1,335 Python tests, asset/profile checks
and the complete Pi suite) and six native targets, but Windows ARM failed at
installed external-create observation; assembly therefore did not run. This
failure remains visible and is not treated as a passing preparation.

Temporary installed-observer diagnostic run 45364336123 passed ten fresh installed
project trials on Windows ARM, each observing create/edit/rename/delete with zero
provider calls. This does not establish the historical intermittent cause.
Its setup verifies the retained artifact against its tested PR merge source; an
initial setup attempt refused the artifact because it expected the branch head
instead of the tested merge commit, before any diagnostic package execution.
The local actual SDK observer test passed create/edit/rename/delete with zero
provider calls. An intentionally disabled observer also failed as expected and
retained its exact pre-teardown Stopped status, disabled policy and empty leases.
Production observer behavior and all acceptance deadlines remain unchanged while
the historical Windows ARM failure remains unconfirmed. The final acceptance
script retains these bounded diagnostics; temporary hard-coded probe/workflow
files are not included in the PR. Only the failed preparation job was retried,
with final results recorded in PR 6 after observation.

## Retried-run artifact selection regression

The retained preparation failure artifact also matched the old native download
pattern. The new functional regression failed before the change because the
selected set contained `forge-native-failure-windows-11-arm-arm64` in addition to
the seven platform artifacts. After narrowing the workflow selection, all five
assembly cases passed, including real fixture archive verification, universal
entry generation and preservation of the original diagnostic. No assembler
integrity or seven-platform requirement was relaxed.

The final current-head platform checks and an isolated assembly using successful
same-commit native CI artifacts are recorded in PR 6 after observation. The
older preparation attempt uses the old selection pattern and cannot establish
the corrected assembly result by retrying it.

GENERATED BY AIKYA FORGE
