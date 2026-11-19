# Forge 0.2.0 interactive acceptance follow-up

Status: local acceptance complete; revised native CI in progress. Updated November
20, 2026 (Europe/Madrid). Production source: 64f4a2e. Current runtime fingerprint:
`a6ce603f08d0a015fbc3c598da224038f2a1d5b7c0cc6e7d2aea946e0be540cb`.
The 24fb92b frozen local regression ran 1,306 Python tests without failures/errors;
its one optional-dependency fallback skip passed separately against the freshly
installed dependency-free wheel. That wheel passed all 11 isolated acceptance cases.
Independent review then required additional Windows search, ambiguous-path,
dual-host-failure, owned-process-group and installed-terminal coverage. Those
corrections change packaged source and require a fresh full/native run. The old
50bf7294 fingerprint and its prepared packet are superseded, not current evidence.
The [active Spanish plan](../plan/2026-11-19-forge-interactive-release.es.md)
implements the six remaining items requested by the user. Historical 40d7d8e
native assembly and 1,288-test evidence remains in the
[previous snapshot](2026-11-18-forge-completion.md); changed source requires its own
current native acceptance. No previous fingerprint is substituted for the new one.

## Implemented and locally checked

Official pinned fd 10.5.2/ripgrep 15.2.0 inputs cover seven native targets. All
12 distinct archives matched official release digests and staged with complete
licenses. Native macOS ARM executables ran with expected versions; non-native
staging is data verification only. Managed CLI binds PATH to verified payload
binaries. CLI and interactive SDK reject project executable caches without effects.
The current package version appears in terminal title/help.

Host refusals retain only bounded static category/stage metadata. The Node host
transport distinguishes cancellation, timeout, process unavailability and protocol
refusal without copying raw exceptions, inputs or private paths. Task diagnostics
do not replay uncertain completion. Windows intermittence still needs current
reproduction; a passing retry is not claimed as a production correction.

The revised frozen regression ran 1,308 Python tests in 451.66 seconds: zero failures
or errors, one optional-parser fallback skip exercised separately against the fresh
dependency-free wheel. All 1,560 captured inputs remained unchanged; snapshot SHA-256:
`b53f3b010c90aa21495ae2f4814bde40bc5537213e2bb4f8a30c1d65089228f8`.
Both Node 26.12.1 and minimum Node 22.19.0 ran 102 SDK tests: 101 passed, with the
Windows-only executable lookup test skipped on macOS. TypeScript, source quality,
documentation guard, changed workflow lint and focused negative contracts passed.
The new wheel passed all 11 isolated installed cases without source imports or an
AI SDK. Wheel SHA-256:
`e8ea9f758f891b6106aae9d540e35b072fe2c6e42678fce63287ffa37380936f`.
These are executed local results; revised remote/native results remain separate.

## Remaining gates

Actual macOS ARM source and installed-launcher PTYs passed recursive completion of
verified/nested/SearchFixture.java, offline startup, tokens, confirmed light theme,
100x32 resize, graceful exit and cache refusal. Installed mode began with an empty
PATH; the collector did not supply tool directories. Four real-process collector
tests cover actual I/O, size, output/deadline limits and owned-group cleanup,
including a descendant ignoring TERM/HUP. The revised output-descriptor fixture
also passes those four local tests. All captures used zero provider calls and retain
unconfigured budget/unknown usage; no subscription percentage is inferred.
Pi CI now adds real POSIX PTY checks and three focused Windows resumption trials per
Node version. Windows ConPTY/visual acceptance remains explicit until observed.
The first current-runtime Pi run (44541993000, 97daaf8) passed all six OS/Node
combinations; Windows Node 26.13.0 reports 99 SDK tests and successful final-record
resumption. This does not identify the previous intermittent failure's cause.
The next Windows collector tests (44544627024, 84ce171) fail at the explicit POSIX
restriction. A native ConPTY backend now replaces that restriction; its remote
execution is pending, rather than being inferred from the passing POSIX tests.
64f4a2e's Windows run reaches actual console readiness and passes output/deadline
limits, but its size fixture queries the input handle. The follow-up uses the output
screen buffer and preserves all assertions and limits. Current native acceptance is
[run 44633078517](https://github.com/jlema0590/aikya-forge/actions/runs/44633078517).
The earlier 97daaf8 seven-target lifecycle passed with fingerprint 50bf7294; it does
not validate the later Windows lookup correction. Do not mix these artifact sets.
The external preparation tool creates a source-bound, pending nine-scenario packet
for the agreed other environment, without keys, trials or publication authority.
Actual authenticated provider observations and reviewed comparisons are not present.
The existing pending dossier therefore continues blocking publication.
The current four-file external packet is aikya-forge-external-acceptance-0.2.0-a6ce603f.zip,
SHA-256 fae6635c9e4940373b14c12d2cf1ffffe0b94c4eee822306c2145644e1995742.
It requires a pristine project/ledger for every counted trial and one export per copy;
different filenames with cumulative totals cannot prove independent trials. Live
follow-up checks and final acceptance status are recorded on the
[draft PR](https://github.com/jlema0590/aikya-forge/pull/1).

No stable tag/release/Pages, real v7 migration or quota/token savings are claimed.
See the [startup bug record](../bugs/2026-11-19-forge-offline-startup.md) for observed
failures, code paths and the difference between staged and executed evidence.

GENERATED BY AIKYA HARNESS
