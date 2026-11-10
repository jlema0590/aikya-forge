# Forge branding and native installer validation

Date: 2026-11-10. Authorized by the user's explicit approval of the
[implementation plan](../plan/2026-11-10-forge-brand-installers.es.md).

## Implemented behavior

Current Python metadata, active first-party branding, instructions and generated
Markdown use Forge. Imports, public commands and functional project paths stay
compatible. The shared writer recognizes inherited ownership signatures without
rewriting historical records or claiming unmarked user documents.

The native builder creates one offline installer ZIP per target. macOS includes
`install.command`; Windows includes `install.cmd` and PowerShell; Linux uses the
shell entry. Scripts and payload hashes are covered by the package manifest. The
manual four-platform workflow builds and tests on native hosts, uploads artifacts
and retains evidence, without release/Pages publication.

Adapted reference-template copies received only the current first-party footer.
Their installed hashes were refreshed; upstream commit, upstream source hashes,
licenses and attribution remain intact. Historical migration fixtures and existing
user changes in `.gitignore` remain unchanged.

## Observed checks

- Initial regression tests reproduced rejection of a Forge wheel, the old document
  signature/index and the missing local launcher/single-download installer.
- Forge wheel/document/legacy-memory tests and controlled lifecycle-smoke tests
  passed after implementation.
- Focused document/installer regression: 52 tests passed, one Windows-only skip.
- Pi typecheck passed; all 92 Pi tests passed on the local Node 26.12.1 host.
- Agent metadata, catalog/assets, 120 documentation templates and release contract
  checks passed. Source quality reported no errors or duplication and four function
  length warnings; those warnings were not suppressed.
- Native workflow YAML parsed successfully. Its four runner labels were checked
  against the [official GitHub runner documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job).
- A real macOS ARM64 native build with pinned Python 3.13.18 / Node 26.13.0 / Pi
  1.5.0 passed import/help checks and the isolated install/doctor/reinstall/uninstall
  lifecycle, preserving owner data and an empty project.
- The final ZIP extracted with its executable macOS launcher intact, and invoking
  that launcher with `--dry-run` returned `writes: false` and `network: false`.
- The renamed wheel and source distribution built successfully.

The final extracted-ZIP lifecycle passed all six observed steps, and the installed
wheel passed all 11 scenarios without checkout imports or the optional SDK. The
[macOS artifact record](2026-11-10-forge-native-macos.json) retains the installer
name, size and SHA-256. Every captured final native Python source input still
matched the checkout when verified.

The initial bare full-suite invocation ran 1,230 tests and reported 9 failures,
49 errors and 7 skips. Personal Claude hooks affected loop fixtures; the sandbox
blocked loopback socket tests; six lifecycle comparisons still expected the old
footer. Preserve the [complete initial output](2026-11-10-forge-python-initial.log)
and [every unsuccessful case by name](2026-11-10-forge-python-initial.json).

The existing `scripts/ci/run_isolated_tests.py` supplies temporary child settings,
and the rerun has approved loopback access. No hook approval check was removed.
The SDD characterization now normalizes only the final Forge footer back to the
historical label before comparing the unchanged pinned hashes; all six scenarios
passed. The complete isolated rerun passed: **1,230 tests, zero failures/errors, seven
expected skips**, in 1,171.013 seconds. Preserve the [final output](2026-11-10-forge-python-final.log)
and [check summary](2026-11-10-forge-checks.json). The final source-quality check
included new untracked Python files and retained zero errors/duplication and four
length warnings; see [quality details](2026-11-10-forge-source-quality.json).
The [installed-wheel record](2026-11-10-forge-wheel-smoke.json) retains all 11 cases.

A semantic mutation check also confirmed that
`test_reference_memories_from_the_old_footer_remain_recallable` fails when inherited
footer support is removed. Production files were not changed during that check.

A further 29 release/tag/installer contracts passed after aligning the inactive
release workflow's archive filename and release-check User-Agent with Forge.

Initial dependency/build attempts failed because the restricted environment could
not resolve public package/component hosts. Explicitly approved escalated retries
completed the dependency downloads and native builds; those network failures were
not treated as successful runs.

## Acceptance boundaries

Native execution in this workspace is macOS ARM64 only. Windows x64, Linux GNU x64
and macOS Intel construction/installation require executing the prepared manual
workflow after the reviewed source is available in GitHub. This session has not
pushed source or run remote jobs during local validation. Available recipes do not establish acceptance.

No release, tag, package publication or Pages deployment was performed. Real-provider
trials and separately configured security controls are not established by these tests.
Uninstall intentionally retains known payloads and owner/project data.

GENERATED BY AIKYA FORGE
