# Forge 0.2.0 interactive acceptance

Status: technical acceptance passed; external acceptance and publication pending.
Updated November 20, 2026. [Machine-readable evidence](2026-11-20-interactive-acceptance.json)
records exact results, hashes, limitations and the distinction between primary PR
checks and cancelled duplicate push checks.

## Source identity

- Last packaged implementation: 64f4a2e; accepted test harness: 3238bc2.
- Native CI source merge: 52fcd6ccb570f276773c7ab2d09aa53c26422efa.
- Runtime fingerprint: a6ce603f08d0a015fbc3c598da224038f2a1d5b7c0cc6e7d2aea946e0be540cb.
- Final records and CI-trigger cleanup do not change packaged runtime inputs.

The previous 40d7d8e/fc4ff9fa and 97daaf8/50bf7294 snapshots remain historical.
Their artifacts are not mixed with this accepted seven-target set.

## Resulting behavior

Reviewed fd 10.5.2/ripgrep 15.2.0 archives, executable hashes, architectures and
complete licenses are bound to native payloads. Startup uses verified tools offline.
Project executable caches are preserved and refused. Windows native entry disables
implicit current-directory executable lookup; preflight rejects installation roots
containing the platform PATH separator. Terminal title/help use the Forge version.

Host failures expose bounded static categories/stages without exception contents,
request values or private paths. A second failure while stopping retains the original
diagnostic and reports an unconfirmed stop with inference blocked. No write is retried.
The earlier intermittent Windows recording failure was not reproduced: three additional
focused resumptions per Node version passed. Its underlying cause remains unknown.

## Executed validation

| Check | Observed result |
|---|---|
| Frozen local Python regression | 1,309 cases; zero failures/errors; one optional-parser fallback skip passed separately |
| Frozen input stability | 1,562 inputs; no changes during execution |
| Local Node 22.19.0 and 26.12.1 | 102 SDK cases each; 101 passed, one Windows-only case skipped on macOS |
| Remote Node 22.19.0 / 26.13.0 | All six macOS/Linux/Windows jobs passed; Windows ran 102/102 |
| Python / memory / synthetic browser CI | 11/11 jobs passed across Python 3.10–3.13 and native hosts |
| Clean installers CI | 16/16 jobs passed, including Alpine, Debian and Fedora |
| Fresh installed wheel | 11 cases passed without checkout imports or an AI SDK |
| Primary PR checks | 43/43 passed on 3238bc2 |
| Native lifecycle | 7/7 targets; each 20 steps, 29 registrations and 24 profiles |
| Universal assembly | 16 checksummed assets independently rechecked; one source commit/fingerprint |
| Universal installer smoke | Actual fresh macOS ARM installation and doctor passed with no PATH modification |

The six source-mode and seven installed-mode console flows exercised actual
POSIX PTY/Windows ConPTY input, recursive completion of a known nested file,
confirmed light theme, 100x32 resize, clean exit and preserved/refused project cache.
Installed mode began with an empty PATH; the collector supplied no tool directories.
Five real-process collector tests cover input/size, byte/deadline bounds, owned-group
cleanup and input gaps. A TERM/HUP-ignoring descendant cannot escape its owned group.
These are automated console results, not human/device visual acceptance.

Native fixtures cover 29 file extensions. Six targets index declarations for 12
extensions and retain file-only evidence for 17. Windows ARM64 indexes 11 and retains
18 file-only extensions because its reviewed Dart wheel is unavailable. No declarations
are invented for inventory-only languages.

The local frozen snapshot SHA-256 is
5c6caeb12c00070d7dfd22c1cb26611c2664973463a5ffd278b2c03f3ecd1270.
The fresh wheel SHA-256 is
e8ea9f758f891b6106aae9d540e35b072fe2c6e42678fce63287ffa37380936f.
Native calls to real providers: zero. Unknown/unconfigured usage and account quota
remain unknown; no subscription percentage or token saving is inferred.

## CI provenance and observed failures

- [Native seven-target acceptance](https://github.com/jlema0590/aikya-forge/actions/runs/44636884909)
- [Six OS/Node contracts and focused Windows resumptions](https://github.com/jlema0590/aikya-forge/actions/runs/44636884765)
- [Python, memory and browser acceptance](https://github.com/jlema0590/aikya-forge/actions/runs/44636884777)
- [Clean installers](https://github.com/jlema0590/aikya-forge/actions/runs/44636884899)

Earlier Windows collector failures exposed the missing ConPTY transport, redirected
parent standard handles, an input-handle screen-size query and joined editor
keystrokes. Corrections preserve assertions and application deadlines. Failed
synthetic captures remain separate from acceptance. Obsolete native collector runs
were cancelled; their partial targets were not assembled as a complete release.

The 3238bc2 rollup includes 64 successes and six cancelled duplicate push jobs.
All 43 primary PR checks passed. Python/installers previously ran on both feature
push and PR; final trigger cleanup retains PR, develop/main and manual runs while
removing that duplication. Final documentation/configuration checks are separate
from this accepted code snapshot; the runtime fingerprint remains unchanged.

## External handoff and publication

The four-file packet aikya-forge-external-acceptance-0.2.0-a6ce603f.zip has SHA-256
fae6635c9e4940373b14c12d2cf1ffffe0b94c4eee822306c2145644e1995742.
It is prepared, not executed. Each counted trial requires a pristine copy of the
same fixture and a new project-local ledger/session, exported once per copy.
Different filenames containing cumulative totals are not independent observations.

The local native candidate contains the verified installers, seven target packages,
bootstrap metadata and checksums; it is not a published release. The existing
[provider procedure](forge-provider-procedure.md) and pending dossier require real
authenticated trials and reviewed comparisons in the separately agreed environment.
Human visual/device acceptance also remains pending. The publication gate correctly
refuses the pending dossier; main-branch publication and Pages are not performed.
No real v7 migration, public installer availability or quota/token saving is claimed.
See the [Spanish plan](../plan/2026-11-19-forge-interactive-release.es.md) and
[draft PR](https://github.com/jlema0590/aikya-forge/pull/1).

GENERATED BY AIKYA HARNESS
