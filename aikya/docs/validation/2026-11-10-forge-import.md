# Forge 0.1.0 import validation

Date: 2026-11-10. Target: `jlema0590/aikya-forge`, branch `develop`.

## Scope and source preservation

Import all 1,471 nonignored Harness project files from the current local checkout,
including pending native-distribution changes and the uninstall-skills proposal.
Retain the destination initial commit and MIT copyright, and preserve the inherited
copyright and third-party notices. Adapt repository/version consumers, both READMEs,
Forge changelog and current overview. Preserve the previous changelog under
`aikya/docs/history/harness-CHANGELOG.md`.

The final regression froze **1,475 inputs**. Their hashes and file-name set were
unchanged for the complete run. Afterward, only this evidence and its change record
were finalized; source, tests, runtime metadata and installer inputs were unchanged.
No Git history, local dependencies, temporary payloads, client state or credentials
are part of the import. A high-confidence credential-pattern scan found no matches;
this is not a claim of a complete security audit.

## Observed checks

| Check | Observed result |
|---|---|
| Complete Python suite | **1,219 tests; zero failures/errors; two expected skips**, executed in four isolated processes. Longest process: 430.596 s. |
| Pi SDK suite, Node 26.12.1 | **92 passed**, zero failures/skips. |
| Pi SDK suite, Node 22.19.0 | **92 passed**, zero failures/skips. |
| TypeScript type checking | Passed. |
| VERSION/changelog release contract | Passed for `0.1.0` / `v0.1.0`; no tag was created. |
| Source quality, entire imported tree | 595 files; zero errors; 11 inherited warnings (nine long functions and two fixture/body duplicates). |
| Built distribution | `aikya_harness-0.1.0` source archive and wheel built successfully. |
| Installed wheel acceptance | **11 scenarios passed**, outside checkout imports, without the optional Claude SDK. Includes global/project registration, ODD/SDD init/analyze, local memory and scoped context. |
| Native macOS arm64 build | **23,758 files**, 440,813,309 manifest bytes, pinned Python 3.13.18 / Node 26.13.0 / Pi 1.5.0. |
| Native offline lifecycle | Install, doctor reporting 0.1.0, help, repeated install returning up-to-date, and uninstall all passed in a temporary application root. Zero provider calls. |
| Real retained v7 receipt preview | The bundled 0.1.0 core read five records, including a 4,761,331-byte receipt, without writes or changed metadata. This is a preview, not a completed v7 migration acceptance. |
| README local links and generated footer | Passed in English and Spanish. |
| Documentation layout | Base layout passes. Authored Forge changes are checked separately from inherited historical root docs. |

The first full run executed 1,220 Python tests and found two inherited prose checks:
`test_readme_no_manual_terminal_commands` prohibited a source/terminal README, and
`test_version_and_release_notes_in_repo` required old v5.9.1 text in the current
changelog. Remove the superseded README-only test, retain the current VERSION/notes
release validation, and remove only its unrelated historical prose assertions.
The fresh complete 1,219-test run above passed. First-attempt diagnostics are retained.

Native version and terminal identity tests also reproduced the original v8-only
rejection before accepting Forge 0.x. Canonical version validation, stable/preview
separation and retained v8 payload compatibility remain enforced.

## Artifact integrity

These are private local validation artifacts, not published downloads:

- Wheel SHA-256: `c8079b39edeaa05c55073c10e90bd98e4f35a0ebe5ffa4c5875c9f067ec6674f`.
- Source archive SHA-256: `e227841e27015790621314badac15541ed537ce425b2677fd489c779dcb24535`.
- Native ZIP SHA-256: `bfedd945dcbcf036bc39f0737d04994a5765297f2ddf946d2af5e6c5c451686e`.
- Native manifest SHA-256: `786d6ecbb44b7d2b51ca3d3897724750e5e190c640e8803241d01e39ca2551b9`.

Local evidence: `/private/tmp/aikya-forge-final-6mv73ndo/` (Python, packaging,
installed/native lifecycle, source hash stability); Pi SDK/typecheck and first-run
diagnostics: `/private/tmp/aikya-forge-checks-wstuys76/`.

## Preserved boundaries

The initial staged import reports four inherited blank-at-EOF whitespace notices:
`managed_versions.py` and the Ansible, Helm and Kustomize bundled skill files.
Those copied resource bytes are preserved; this is separate from the source quality
check, which reports no blocking errors. No whitespace-clean bulk-import claim is made.

Historical root `docs/` files are copied unchanged under the existing contributor
exception. Treating the whole import as newly generated documentation makes the
strict diff guard flag eleven such inherited pages; they are not relocated or
exempted by a production-code change. New Forge records remain inside `aikya/docs/`.

Native Windows/Linux execution, real-provider acceptance, the observed .NET
build-derived-output issue, additional native parser packaging and Forge release
publication remain open. Older v7/v8 records describe their original snapshots;
this import does not convert them into Forge acceptance. The inherited release/Pages
jobs remain scoped to the original repository; pushing develop publishes source only.

GENERATED BY AIKYA HARNESS
