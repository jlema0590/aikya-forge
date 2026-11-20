# Forge 0.2.0 implementation and validation

Updated November 19, 2026. Branch: feat/forge-0.2.0-completion, based on develop
43a71eac0f01ca1517644a7ae523344870996729. See the
[Spanish active plan](../plan/2026-11-18-forge-completion.es.md) and
[machine-readable evidence](2026-11-18-forge-evidence.json).

## Implemented scope

- Reviewed .NET 8+ checks use unique private artifact directories. Real source in
  bin/obj stays in the candidate; source drift detection remains intact.
- Native skill withdrawal/restoration supports project/global scope, confirmation,
  exact retained packages and interruption recovery. The canonical set contains
  29 workflows, including /aikya-uninstall-skills; external plugins are not deleted.
- Native bundles include reviewed compatible binary parsers with pinned origins,
  SHA-256, ABI/architecture checks and actual declaration probes. Unavailable
  grammars remain explicit file-only inventory; no source compilation is implied.
- Forge owns independent activation/PATH markers, refuses legacy adoption and runs
  Windows administration through the verified active payload core.
- Local per-project memory/HTML, themes and anonymized bounded usage exports are
  integrated. Observation and HTML maintenance require no model inference.
- Same-commit seven-target assembly, version-pinned sh/PowerShell entries and Pages
  preparation are implemented. Publication remains an explicit separate action.

## Verified code and local regression

Code snapshot: 40d7d8e672d18638bf8d096cb2d1659b75729f67. Packaged runtime source has
not changed since 97c9304; 40d7d8e fixes checkout policy and assembly checks. Its
canonical fingerprint is
`fc4ff9faaf96e2ce26708133cda129ec66137288a744c537192bae54819f1590`.

The complete Python 3.13.18 run executed **1,288 tests, zero failures/errors and one
optional-parser fallback skip**. Four isolated shards froze 1,538 working-tree
input paths and hashes, including then-current local documentation, with no drift.
The skipped fallback passed separately against the installed wheel without parser
dependencies. Actual private PowerShell 7.7.0 executed its cases; there is no
PowerShell skip in this run. Both new checkout/assembly regressions failed before
correction and passed afterwards.

A preceding restricted attempt had four loopback bind permission errors and one
live-client failure. The same inputs passed with required local-server permission;
that failed attempt is retained separately, not combined with passing totals.

The current 0.2.0 wheel built and passed installed-package smoke without checkout
imports or the optional author SDK. It covers registration reuse, mobile hooks and
ODD/SDD init/analyze in project/global scopes. Wheel SHA-256:
`db5d16c3246e5e8bb842c7b274741f600832e05013b9e722cdf55a20459a1156`.
Source quality against develop covers **104 files**, with zero errors, warnings or
duplicate Python bodies. actionlint accepted native/release/Pi workflows.

## Remote acceptance on 40d7d8e

| Battery | Observed result |
| --- | --- |
| [Native Forge lifecycle](https://github.com/jlema0590/aikya-forge/actions/runs/44525961641) | All seven jobs passed: macOS Intel/ARM, GNU Linux x64/ARM, Alpine/musl x64 and Windows x64/ARM. All artifacts were downloaded and verified. |
| [Pi contracts](https://github.com/jlema0590/aikya-forge/actions/runs/44525961694) | All six latest jobs passed: macOS/Linux/Windows with Node 22.19.0/26.13.0; SDK suites 94/94 without skips. One original Windows Node 26 failure is retained below. |
| [Python and memory](https://github.com/jlema0590/aikya-forge/actions/runs/44525961433) | All 11 jobs passed: Python 3.10–3.13, memory on three OS families and synthetic browser acceptance. Dependency/platform skips remain explicit in logs. |
| [Clean installers](https://github.com/jlema0590/aikya-forge/actions/runs/44525961508) | All 16 jobs passed, including Debian, Alpine and Fedora. Inherited Python-based installer checks are separate from native payload acceptance. |

Actual offline .NET builds passed on macOS and Windows. Windows review suites ran
79 tests with three explicit POSIX lifecycle skips; the real .NET build passed.
The unchanged viewer passed **110 Chromium checks**: English 21, Spanish 21,
interactions 48 and dense/live 20. Browser fixtures are synthetic/offline and live
snapshot transport is mocked; no real provider is represented by those checks.

## Native archives and assembly

All seven artifacts bind actual PR merge commit
`9385e2c2c4bb7f3ded62ea4614c505bddb4f82ac` and the same canonical runtime fingerprint.
Each passed 19 lifecycle steps, 29 command registrations and 24 portable profiles,
with **zero provider calls**: installation/doctor/launcher, skill withdrawal and
exact restoration, external create/edit/rename/delete memory and HTML, light-theme
persistence, observation export, inert reinstall, private update to 0.2.1, active
manager core identity, rollback to 0.2.0, retained data and uninstall.
Windows uninstall uses a verified external installer to avoid a locked running EXE.
The private test successor 0.2.1 was not published.

All 29 suffixes were inventoried. Six targets indexed 12 suffixes; Windows ARM
indexed 11 because no reviewed Dart wheel is available. Remaining suffixes are
file-only. Inventory does not establish semantic support or successful builds for
every language. Exact per-target coverage and hashes are recorded in the JSON.

Local assembly verified archive SHA-256, complete ZIP contents and matching TAR
manifests for the full same-commit set, generated universal version-pinned entries,
and independently rechecked all 16 output checksums. This is a prepared artifact;
no release, tag or Pages site was published.

## Interactive preview and open acceptance

The current macOS ARM artifact was separately installed under a private root with
NoPath and opened in a temporary project's real PTY. Startup, slash-command
completion and /aikya-tokens output were rendered in a read-only xterm viewport and
captured. These are real CLI output captures, not native macOS Terminal screenshots.
No model was enabled: the budget correctly showed unconfigured, recorded tokens
unknown, calls zero and provider quota unavailable.

That preview exposed an fd-not-found offline warning. Pi's installed interactive
code uses fd for file autocomplete and probes rg too. Review clean-host availability
and pinned packaging/fallback rather than enabling unreviewed runtime downloads.
The source also retains an Aikya v8 window title although the visible banner shows
0.2.0. Both are explicit interactive follow-up work. Full visual/input/theme/resize
acceptance on all supported OS families remains open.

The original Windows Node 26 task-resumption test returned needs_host_action rather
than recorded (93/94 SDK cases). Windows Node 22 and the focused local case passed;
a single failed-job rerun passed all Node 26 SDK/Python contracts without changing
code or limits. Its intermittent cause is unknown; no production fix is claimed.

Real-provider trials and measured comparisons remain in the other agreed
environment. The external dossier stays pending and is correctly rejected by the
publication gate. Local document validation cannot establish actual provider
provenance. No quota percentage, financial cost or token savings were measured.
Real user v7 migration is excluded; historical fixtures are regression coverage.

Earlier failed/cancelled runs, including the functional 4000e3a set rejected for
Windows CRLF source identity, remain in the [CI dossier](../bugs/2026-11-18-native-ci.md).
Cumulative PR filters may start native reruns for final evidence-only commits; the
validated runtime and same-commit set above remain explicitly identified.

GENERATED BY AIKYA HARNESS
