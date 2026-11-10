# Explicit native skills: installation, context and independent review

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`, based on `204a5b5` plus this block.
Local environment: macOS ARM64, Python 3.13.18, Node 26.12.1/22.19.0, Pi 1.5.0.
Stable remains 7.2.2 and the private runtime remains 8.0.0-alpha.0. No release,
remote CI, live-provider result or native Windows/Linux execution is claimed.

## Observed verification

| Check | Result |
| --- | --- |
| Selected-skill host contracts | 17 passed; source/registry drift, partial effects, custom data, manifest reads and comparison continuity. |
| Core service/authorization contracts | 24 tests passed in 5.975 seconds. |
| Pi SDK suite, Node 26.12.1 | 57 passed, no failures/skips, 16751.397583 ms. |
| Pi SDK suite, minimum Node 22.19.0 | 57 passed, no failures/skips, 16823.649208 ms. |
| Strict/erasable TypeScript | Passed. |
| Full isolated Python regression with local loopback | 872 tests in 1137.467 seconds; no failures, two skips. |
| Wheel build and isolated smoke | Passed outside checkout imports, without optional Claude SDK. |
| Minimum Node plus dependency-free installed wheel | 57 Pi tests passed, no failures/skips, 16746.677041 ms; 17 selected-skill host tests passed in 0.899 seconds outside the checkout. |
| Changed-source maintainability | 12 source files; no errors, warnings or reported duplicates. |
| Real macOS Node 22 terminal | Plan/status, cancellation without installation, confirmed installation, localized audit/index, exact originals and normal exit passed without model calls. |

The preceding 855 snapshot and intermediate 868 snapshot each passed with two skips;
they are not substituted for the final regression. Four additional Red cases covered
unreadable directories, discovery-entry budgets, CRLF source entries and uppercase
Markdown. The final Python source stayed frozen throughout the 872 run; later edits
were documentation only. The two skips were optional-dependency fallback with extras
already installed and a PowerShell-only case where PowerShell is unavailable. Fixture transports exercise real Pi and actual
Python child services but do not establish model quality, subscription compatibility
or quota savings. Native lifecycle and live-provider release gates remain open.

## Selected package ownership and documentation

Empty status and source planning have no installation/documentation effects. The
native installer accepts an explicitly selected absolute local directory, never an
automatically recommended external skill. It verifies a flat Agent Skills entry,
name/description/body bounds, regular resources, total bytes and hashes. Unknown
packages, reserved Aikya names, links, protected files, changed previews and custom
comparison documents are refused. Existing generated comparison rows remain intact.

At most 20 native project skills, 160 examined filesystem entries, 80 files/5 MB per
package, 1 MB per resource,
8 KB for the source entry and 6 KB of instructions are supported. Multiline metadata
requires explicit adaptation rather than guessing. Installation is data-only: scripts,
hooks and dependencies are not run. Exact source bytes are archived privately;
normalized Markdown receives the footer. The Pi entry forces explicit invocation and
ignores source fields that could otherwise suggest execution privileges.

Directory errors are never silently omitted: a bounded iterator propagates unreadable
subtrees and refuses excess entries before materializing a whole tree. CRLF metadata
is normalized for activation while the original archive retains exact bytes; uppercase
Markdown resources receive the same footer contract. These are portable fixtures,
not a claim of execution on native Windows.

A private signed reservation precedes effects. A copied package without a committed
registry cannot activate; interrupted/unknown effects remain preserved without replay.
The final source snapshot is checked again after preview. Private state is in the
project's ignored `.aikya/pi/skills/`; localized audit Markdown is under
`aikya/docs/operations/`, comparison is created only on installation and the index
is refreshed. No Claude assets or personal configuration are copied.

## Context and dispatch boundary

The public Pi loader receives only verified installed entries with default discovery
disabled. Automatic skill prompt listings are disabled. A normal model request omits
the test skill body; explicit `/skill:example-skill` includes it exactly once. Admin
status/plan/install messages are excluded from subsequent model context.

A real-SDK Red showed that hook exceptions can be logged and ignored. Integrity now
also checks the actual expanded user payload inside the guarded model stream, before
budget reservation/provider dispatch. Altered files and forged expansion text cause
no provider call or budget admission. The tests assert observations after the real
SDK call, because assertions thrown inside fixture streams can themselves be converted
into assistant errors rather than failing a test.

Verified explicit user expansions determine session resource access. The existing
bounded context tool reads one `@skill/name/resource#offset` alias, validates signed
membership/current bytes and reports a continuation offset. An uninvoked author and
an independent reviewer cannot read these resources. An explicitly invoked author
can read the verified reference. References do not add shell/tools/permissions;
all source writes and checks retain their existing host confirmation boundaries.

## Real terminal and remaining gates

In a disposable Spanish project, planning and cancellation left the registry and
comparison absent. Confirmation installed the chosen local fixture and status showed
`execution:not_observed`, not a fabricated invocation. Original `SKILL.md` matched the
archive exactly, active entry metadata forced explicit invocation, audit/comparison
were footer-stamped/indexed, and the terminal exited normally. A helper containing
an immediate exception was copied without being executed. No model was configured.

The native slice supports local project packages. Global scope, direct GitHub source
adaptation, updates/uninstall, external-tool execution and full skill compatibility
remain pending native work. Stable user-selected installers are preserved. Seventeen
of 28 canonical commands now have native adapters with explicit limits; standalone
installation and native/live-provider acceptance remain open.

GENERATED BY AIKYA HARNESS
