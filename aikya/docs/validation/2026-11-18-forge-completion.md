# Forge 0.2.0 implementation and validation

Branch: feat/forge-0.2.0-completion, based on develop 43a71ea. The active plan is
[Forge completion](../plan/2026-11-18-forge-completion.es.md). Machine-readable results
are in [the evidence record](2026-11-18-forge-evidence.json).

## Verified local results

- Complete Python 3.13.18 regression: **1270 tests, zero failures/errors,
  two declared skips**, across four isolated process environments. All input hashes
  and names remained unchanged for the full run. One skip was the dependency-free
  fallback case, subsequently passed in a separate installed wheel without parsers;
  PowerShell remains unavailable on this Mac.
- Actual Pi SDK: **93 tests passed on Node 22.19.0 and 93 on Node 26.12.1**;
  TypeScript checking passed. Provider transports in these contracts are fixtures,
  not real provider acceptance. The native bundle separately uses Node 26.13.0.
- Chromium: **110 checks passed** (21 English, 21 Spanish, 48 interactions, 20
  dense/live). Inventory remains exclusive, grouped nodes are draggable, links follow
  positions, flow animation is bounded, reduced motion and responsive layouts work.
- Fresh final wheel build and installed-package smoke passed. Catalog checking found
  30 engineering agents, 29 engineering skills and 29 canonical commands. Example
  profiles and documentation structure passed. Changed-source quality: 58 files,
  no errors, warnings or duplicate blocks. actionlint 1.7.12 accepted all three workflows.
- Real offline .NET 8 build passed: generated assembly/declaration outputs stayed in
  the private run directory, with the source candidate current and no new bin/obj.
  Actual source in bin/obj remains inventoried; process evidence has null test counts.

## Actual installed macOS ARM cycle

Two private native bundles, **0.2.0 and test successor 0.2.1**, were built using the
reviewed Python 3.13.18, Node 26.13.0 and Pi 1.5.0 inputs. Both grammar probes parsed
Java, JavaScript, TypeScript, C#, Go and Dart declarations with symbols. The installed
project exercised every one of the 29 code suffixes: 12 indexed and 17 file-only on
this host. Unsupported semantic capabilities remain explicit inventory.

Final acceptance passed: shell offline installation; actual installed launcher command
resolution; native CLI skill withdrawal preview/apply and exact restoration; real
installed SDK command uniqueness; all 24 portable type/method/mode/language profiles;
external create/edit/rename/delete memory and HTML publication; light-theme persistence;
verified runtime observation export; inert reinstall; update to 0.2.1; active manager
core identity; rollback to 0.2.0; retained reviewed notes/selected skill/project source;
owned activation uninstall and retained project data. **Provider calls: zero.**

Runtime source fingerprint: `2c5d929948b5a19241e483fa637d5732535d67c2e7303c4880ddc8c5707bbe84`.
Manifest hash: `2c4630f91cd06dcda5d2fa523914386005e02754e5abe2aaa997d77c7fb9e695`. The installed fingerprint matched the final
packaged source. This local archive predates the branch commit, so no commit identity
is invented. CI binds future artifacts to its actual GITHUB_SHA.

After full Python verification, only the native acceptance script was extended with
installed launcher and skill lifecycle assertions, then that complete native cycle was
rerun against the same verified bundles. Product runtime source remained unchanged.
Subsequent documentation/evidence updates do not change packaged runtime inputs.

## Failed attempts and corrections

The first full pass found three stale contracts: the old Linux application-root
expectation, a fixed command set without the new command, and an unexercised command
in the offline battery. Their expectations/actual command coverage were updated and
the whole suite rerun successfully. The temporary result collector initially could
not serialize skipped TestCase objects; it now stores test IDs/reasons. Its malformed
summary was not used as passing evidence.

Installed acceptance exposed a real export bug: managed_runtime.resolve does not
return a full manifest. The exporter now reads the manifest bound to the verified
payload hash and checks provenance against it. A failing regression preceded the
fix; the fresh native cycle proved the corrected export and matching fingerprint.
Parser-input negative tests were also corrected to use real nonlinked temp paths,
then malformed URL types were rejected explicitly after observed failures.

The first browser launch lacked macOS process permissions; the isolated browser was
rerun with the needed permission. An incorrectly prepared live fixture was initially
passed to an offline-only interaction test; separate static/live fixtures then passed
all checks. No CSP/security restriction was weakened to make that run pass.

## Remaining external gates

Seven native targets are configured, but Windows/Linux/other-architecture results
must actually pass in remote CI before being called accepted. Headless SDK checks do
not establish visual terminal/device/SDK acceptance. Real authenticated provider
trials remain reserved for the separate agreed environment; the procedure and pending
forge-provider-acceptance.json make that gap explicit and block publication.

No real migration of a user's v7 installation is in scope. Historical migration
fixtures remain regression tests. No stable release/tag/Pages, subscription-quota
percentage or token saving is claimed. The release pipeline defaults to preparation
only and requires current externally reviewed evidence plus an explicit main publish.

## Follow-up after the first PR CI run

The local results above describe the 6de7008 runtime snapshot. Remote CI subsequently
found Linux terminfo aliases and Windows SDD newline/proof errors, plus a transient
macOS Intel DNS failure and Windows fixture portability errors. The implemented
corrections and focused passing regressions are recorded in
[the CI dossier](../bugs/2026-11-18-native-ci.md). They change runtime source: current
remote acceptance and a final full regression are still pending. The earlier local
bundle/fingerprint remains evidence for its stated snapshot, not the new corrected
runtime. External provider acceptance remains pending throughout.

The first correction run (4b268dc) failed before downloads because the builder's
boolean fetch option shadowed the imported transport function. The constructor now
calls the component_download module explicitly. A regression that traverses the
actual component constructor failed before this fix and now passes along with all
94 managed contracts. The failed run is retained as a failed attempt, not acceptance.

GENERATED BY AIKYA HARNESS
