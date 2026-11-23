# Managed terminal distribution — execution evidence

Date: 2026-11-09. Branch: `feat/aikya-v8-pi`. Base commit: `2869d91`.
Status: implementation and targeted checks observed; final regression and native
installed acceptance are in progress. Stable VERSION is 7.2.2. Private staging can
produce coherent 8.0.0-alpha.0 and alpha.1 identities without editing that file.

## Implemented controls

A signed managed receipt selects Python, Node and the terminal from one exact listed
payload. Bare `aikya` opens that terminal; help/support/development entry behavior is
preserved. Source modules are separated by responsibility. Malformed legacy loop JSON
is refused before effects. The portable resource validator is shared with chosen
skills, including UTF-8 component and combined cache-path bounds before reservations.

The native builder verifies official interpreter hashes before execution, captures
bounded source inputs, builds a private wheel, installs fixed npm production packages
without lifecycle scripts and retains original inputs/provenance/license metadata.
Regular data replaces contained archive/bin aliases; external/directory/cyclic links,
collisions, unknown paths, special objects and excessive data are refused. Deterministic
ZIP/POSIX gzip archives carry a complete file manifest. Generated entry scripts embed
transport hashes and require no preinstalled Python/Node. A dry run needs neither.

Install/update/rollback/uninstall use the existing owner/lock, signed reservations,
exclusive final-path copies, fixed probes, readback, retained versions and atomic
current promotion. Known complete effects reconcile without replay. Partial/custom
state blocks further mutation. Global skills and project data are preserved. V7
installation metadata gets an exact backup; profile/session migration stays separate.

## Evidence collected so far

- Targeted managed contracts passed 77 tests before the macOS temporary-alias fix.
  This is not the complete Python regression. TypeScript/SDK/installed checks will
  be recorded separately for the final snapshot.
- The first actual composed macOS arm64 build contained 23,747 files and 440,796,651
  bytes of data; ZIP transport was 137,754,332 bytes. Extraction into a different
  space/Unicode path and isolated core/terminal help both passed with no provider calls.
- Full hash inspection took 7.659 seconds before redundant ancestor walks were
  removed. The same 23,747-file payload then verified in 2.394 seconds; nine integrity
  contracts stayed green. These are local measurements, not guaranteed startup times.
- Two subsequent private native builds produced 23,758 listed files each. Initial
  clean-install acceptance exposed the macOS `/var` temporary alias. The CLI refused
  that path before application writes. A new Red/Green shell test now requires the
  bootstrap to resolve its own temporary directory physically; user path link checks
  remain intact. Fresh rebuilt installed acceptance is required before closing D.

## Limits and remaining evidence

Seven official interpreter asset pairs are pinned in `resources/terminal-inputs.json`:
macOS x64/arm64, Linux glibc x64/arm64, Linux musl x64 and Windows x64/arm64. An absent
pair has no silent fallback. Availability is not native execution. Platform minimums,
proxy/permission/long-path behavior and open Windows executables remain acceptance
items. Windows launcher containers have structural tests, not native execution proof.

No personal credentials, paid provider calls, stable tags, release assets, published
Pages or user projects are modified. Real provider accounting stays in the external
environment previously designated by the user. Optional parsers and application SDKs
must be observed explicitly; source extensions alone do not prove semantic coverage.

[Private installation guide](../deployment/pi-managed-terminal.md),
[D execution plan](../plan/2026-11-09-pi-managed-distribution.es.md).

Upstream [Node 26.13.0 system requirements](https://github.com/nodejs/node/blob/v26.13.0/BUILDING.md)
are recorded in provenance: macOS 13.5+, Windows 10+ (x64 Server 2016+),
Linux glibc 2.28+/kernel 4.18+ or x64 musl 1.2.5+/kernel 6.12+. Linux also
needs the libatomic runtime. These are upstream Node prerequisites, not combined
Aikya/Python acceptance. The installer does not install system packages or choose
another ABI silently. Native preflight and platform testing remain necessary.

## First frozen full regression and resulting corrections

The first full D run executed 1,213 Python tests in 1,650.394 seconds: six failures
and two expected skips. All 1,470 frozen input hashes remained unchanged. All six
failures came from direct execution of `cli/main.py`, whose newly extracted imports
were relative. They are now absolute package imports; the nine execution and seven
methodology contracts pass, and the four legacy-loop contracts pass in the isolated
home. An unisolated diagnostic correctly refused unrelated configured global hooks;
that configuration was not imported or weakened for the isolated retry.

Both Pi runs passed 88 tests: Node 26.13.0 in 86,977.591708 ms and minimum Node
22.19.0 with the installed native Python in 215,306.36925 ms. Strict TypeScript
passed. The installed native host passed 79 managed contracts with one missing-build-
frontend skip and all 78 chosen-skill contracts. These results precede the new Git
startup and idempotent-install regressions; a new frozen final run is required.

The rebuilt actual macOS install passed without Python/Node/npm/Git in PATH. Bare
terminal startup then exposed an unconditional Git requirement even outside a repo.
A new three-case Red/Green regression now permits genuinely unversioned ancestry
while keeping Git/gitfile/bare markers fail-closed. Original tracked-state, ignore
negation and linked-state tests still pass. A diagnostic with Git available completed
real terminal sessions on alpha.0 → alpha.1 → alpha.0, followed by uninstall, preserving
global skills, project source/documents, reviewed/pending notes and the light preference.
That diagnostic is not final no-Git terminal acceptance. Its first resume driver had
a missing local variable, fixed only in the disposable test driver before completion.

Repeated one-command installation now updates an older owned version, returns inert
`up-to-date` for identical current bytes, and rejects replaced same-version payloads
or update downgrades. New filesystem/CLI Red/Green cases verify those policies.

GENERATED BY AIKYA HARNESS
