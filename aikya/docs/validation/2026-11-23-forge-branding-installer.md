# Forge branding and simple installer validation

## Result and scope

Active producer text, Python distribution metadata, wheels, native probes, runtime
messages, bundled instructions/templates and new document signatures use Aikya Forge.
The package is `aikya-forge`; imports and public commands remain `aikya`.
New global Claude adapter registrations use `.claude/aikya-forge`; native application
roots were already independent Forge roots. This does not migrate predecessor
installations or overwrite customized registrations. Re-registering predecessor
adapters remains an explicit review, separate from native application update.

Root `install.sh` and `install.ps1` select a stable published Forge release, download
bounded entries over HTTPS, require exactly one valid matching SHA-256 entry and
execute only matching bytes. They support offline assets and an inert preview.
They delegate actual installation to the existing version-bound native entries;
there is no npm package, source-build fallback or extra runtime prerequisite.
README English/Spanish document the native command, source alternative, update,
doctor, uninstall, offline assets and the current publication prerequisite.

## Observed verification

| Check | Observed result |
|---|---|
| Full Python discovery on Python 3.13.18, private home and local test servers | 1,325 cases, 1,300.768 seconds, five skips; six subtest failures in the single historical SDD signature contract described below. No other test failed. |
| Corrected historical/current SDD contract | Both tests passed; six project-type/language combinations each. The original baseline file was preserved. |
| Forge identity/read compatibility/publication guards | Six focused tests passed. |
| Simple entry acceptance on macOS ARM64 | Four passed, including the real version-bound shell entry; two PowerShell cases skipped locally. Windows CI now runs those cases. |
| Pi terminal on Node 26.12.1 | 130 cases: 129 passed, one Windows-only skip, no failures. |
| TypeScript | `npm --prefix packages/aikya-pi run typecheck` passed. |
| Real wheel in clean environment | `aikya_forge-0.2.0-py3-none-any.whl` built; all 11 installed-wheel checks passed, including global/project registration, global reuse and ODD/SDD init/analyze without source imports or an installed model SDK. |
| Template catalog | 120 templates, 155 reference files; installed integrity valid. Original upstream hashes and source URLs unchanged. |
| Synthetic example manifest | All 253 document hashes match the updated distributed bytes. |
| Assets | 30 engineering agents, 29 engineering skills and 29 commands consistent. |
| Project examples | All 14 profile smoke checks passed. |
| Source quality | Zero errors; four existing long-function review diagnostics, no duplicate Python bodies. |
| Release contract, context proxy, shell syntax and diff whitespace | Passed; context proxy remains an estimate rather than a billing measurement. |

The original SDD characterization includes document bytes and dependent state
hashes. Replacing the generated signature intentionally changes those fingerprints.
Restoring only the historical signature reproduced the exact original baseline.
The characterization test now explicitly uses that historical signature; a separate
test runs the current Forge signature through completion and validates its footer
on every generated Markdown document. No expected baseline hashes were regenerated.
Only test code changed after the full run; the corrected contract and new focused
checks were rerun. A second complete local run after that test-only correction was
not performed; the PR matrix must recheck the final commit.

Early exploratory runs were superseded. They exposed historical command-fixture
bytes accidentally changed during rebranding; those fixtures were restored exactly.
A test process also correctly rejected source changing during package preflight.
The complete result above used frozen production files. These protections were not
relaxed to make tests pass.

The clean-wheel SHA-256 is
`25e5729737cc309cd1d4eca289aa7aeca12c1d1c92d7d09e33c184dcf8870c7b`.
The runtime fingerprint is
`8861faeeebf2b6704a5c62887ddcc2efe7ae57392a8f1ab4848eb0659b2031a1`.
Earlier native/provider receipts do not validate this changed runtime.

The new-record location check and canonical index check passed. Eleven pre-existing
root `docs/` guides remain at their original paths under the explicit AGENTS.md
retention rule; passing those guides to the generic project-generated-record guard
reports location warnings. They were checked as retained source guides, without
adding an exemption to the product guard or relocating them in this branding change.

## Deliberately retained original identifiers

- The full template license, copyright, NOTICE and original source URLs/hashes stay
  intact in `THIRD_PARTY_LICENSES.md` and the template catalog. A local adaptation
  must not claim to be the original upstream author.
- Historical plans, research, bugs, change records, validation artifacts and the
  original logo reference retain their original identifiers. Existing migration
  tables and frozen compatibility fixtures retain the bytes they recognize.
- The documentation reader accepts the former generated signature and legacy
  headers. New authorized writes require the Forge signature; an old marker cannot
  confer write approval. Custom documents/index prose remain protected.
- The template provider, active labels and local catalog paths are Aikya; no active
  template directory is named after the original upstream owner.

## Publication and platform limits

The public repository has no anonymously available stable latest release at the
initial check; the npm package endpoint also returned 404. The README one-liners
are explicitly conditional on publishing an accepted stable release and its Pages.
No release, tag, npm publication, Pages deployment or main merge is performed here.
The retired release/bump/Pages jobs are explicitly disabled; Forge keeps its gated
manual publication workflow.

PowerShell/native Windows behavior is not claimed from macOS. The installer matrix
must execute the Windows entry checks on the final commit. No live provider,
personal credentials, account quota or paid inference were used in these checks.

The PowerShell checksum-match behavior was cross-checked against the primary
[PowerShell comparison operator documentation](https://learn.microsoft.com/en-us/PowerShell/module/microsoft.PowerShell.core/about/about_comparison_operators?view=powershell-5.1);
that documentation check does not replace Windows execution.

GENERATED BY AIKYA FORGE
