# Changelog

Aikya Forge uses independent semantic versioning, beginning at `0.1.0`.
The inherited Harness v7/v8 changelog remains in
[aikya/docs/history/harness-CHANGELOG.md](aikya/docs/history/harness-CHANGELOG.md).

## Unreleased

- Preserve the memory lease when the pinned Pi SDK binds UI extensions again for
  the same session. Renew the existing owner instead of briefly retiring its
  observer; keep final shutdown and other-session ownership checks intact.
- Serialize observer lease reads with session updates using the existing launcher
  lock, preventing a concurrent open reader from blocking durable release on Windows.
- Bound prepared-file rename retries to 250 ms for Windows sharing/access conflicts;
  preserve the previous destination on persistent denial and never replay caller effects.
  Verify real open-reader replacement and idle lease renewal in Windows matrices.
- Repeat Windows same-session binding and complete ODD/SDD task regressions on
  both supported Node versions without changing their time or inference limits.
- Retain bounded observer-state and lease-count diagnostics on SDK fixture cleanup
  failure, preserving the failed fixture and excluding paths or session contents.
- Capture whitelisted task phase and check execution outcomes before failed SDK
  assertions, so teardown cannot conceal the original validation evidence.
- Exercise SDK rebinding after the observer's initial publication; retain the
  existing cleanup deadline and report bounded process-liveness metadata on failure.

- Run complete reusable PR acceptance for develop/main, including all Python/Pi,
  memory/browser, installer and seven-target native checks plus shared real archive
  assembly. Consolidate failures in one final fail-closed check and summary.
- Allow technically validated code to integrate into develop/main while reporting
  publication readiness separately. Pending real-provider trials permit native
  preparation only; both publication checkpoints retain strict evidence validation.
- Run mandatory acceptance only on PR opening, source updates and reopening;
  title/body edits cannot supersede a validated workflow run. Document reopening
  after retargeting to obtain full acceptance for the protected destination.
- Resolve required-check identities from the target event before jobs run,
  preserving strict GitHub Actions app binding and every mandatory stage.

- Exclude retained native-failure diagnostics from release artifact selection
  after retries, preserving strict seven-platform provenance and checksum checks.

- Retain bounded installed-observer status, leases, policy and SDK diagnostics
  before failed native acceptance teardown, preserving its existing deadlines.

- Synchronize observer shutdown assertions with the actual owned child exit, using
  the existing bounded cleanup instead of reading its status during publication.

- Align release verification with the editable contributor installation used by
  source regression tests, preserving separate installed-wheel validation.
- Require the final-record resumption fixture to observe the actual declined
  recording dialog before resuming; retain SDK diagnostics for unrelated stops.

- Start gated stable releases automatically on main pushes while retaining manual
  preparation/publication, using reviewed VERSION and changelog values.
- Plan publication before builds, preserve published assets/tags, skip unchanged
  versions and recover latest stable Pages from the original release on retry.
  Verify public installer bytes after deployment and document shared portal plus
  independently versioned product Pages.

- Standardize active branding, the Python distribution and generated-document
  signatures on Aikya Forge. Preserve previous generated-footer recognition and
  original third-party license/provenance and historical evidence.
- Add simple shell/PowerShell stable-release bootstraps with bounded downloads,
  checksum verification, offline assets and inert previews; document installation,
  update and administration in English and Spanish. Public one-liners require a
  published stable release; no npm package or release is published by this change.
- Explicitly disable retired publication workflows while retaining the gated
  manual Forge release process.

- Fix isolated Windows pyfiglet startup and native font preflight when APPDATA is
  absent, without importing personal font locations or widening process environments.

- Group Claude/Codex metrics in an expandable Agents sidebar submenu, with heading
  clicks, F3 and F2 → Agents. Preserve cached metrics when collapsed and support
  expansion in compact layouts without changing providers or execution state.

- Add separate Claude/Codex Context, Tokens, Usage 5h and Usage 7d fields. Bind
  context to the active provider, keep project attribution partial when needed,
  and select sourced account windows by exact duration with zero/stale handling.
  Clarify that Aikya local budget is a project token/call execution guard.

- Use Aikya Forge as the terminal/theme display name and show project, Git branch
  and configured Git user in the right-side Project & Git block, with a compact
  summary on narrow terminals. Reuse SDK branch observation, read only
  user.name at startup and retain explicit fallbacks without repaint subprocesses.

- Add the Aikya Forge theme using original-logo navy/cyan/turquoise, preserve
  existing selections and keep the original reference PNG unchanged.
- Draw the Aikya startup wordmark with pinned pyfiglet 1.0.4 and width-aware
  slant/small ASCII fonts. Bundle fonts/license in native Python, validate the wheel
  hash and real rendering before sealing, and cache the bounded local response.
  Retain a plain-text fallback; remove the superseded terminal-cell renderer/assets.
- Add `/aikya-settings` and F2 for project-local provider connection, next-launch
  model selection, appearance, HEX colors, ANSI text style and flow controls.
- Reserve a right-side terminal column for local budget/context percentages,
  Claude/Codex attribution and sourced provider quota; collapse on narrow terminals.
- Mask API-key entry, keep credentials outside transcripts/preferences, preserve
  uncertain budget accounting and refuse unsafe project credential locations.
- Share the new preference with `/aikya-theme`, retain readable light backgrounds
  and the selected theme when changing text style; keep font family/size host-owned.
- Extend actual PTY acceptance to the provider catalog and settings/style flow.

## v0.2.0 — 2026-11-18

- Include reviewed fd 10.5.2/ripgrep 15.2.0 binaries and licenses for offline native
  autocomplete/search; verify their origin, architecture, hashes and real versions.
- Bind managed startup to verified tools, preserve/refuse project executable caches,
  and show the current Forge version in the terminal title and help.
- Add safe bounded host failure categories/stages and task recording diagnostics
  without exposing exception contents or replaying uncertain effects.
- Disable implicit Windows project executable lookup, reject ambiguous PATH roots,
  and retain original diagnostics when a second stop operation fails. Exercise the
  installed launcher with an empty PATH, real recursive file completion and native
  console input/resize; bound process-tree cleanup and independent external trials.

- Isolate reviewed .NET 8+ check artifacts per execution without hiding bin/obj source.
- Add confirmed native project/global skill withdrawal, retained exact backups,
  restoration, interruption recovery and `/aikya-uninstall-skills` / `aikya skills`.
- Bundle reviewed compatible binary parsers with platform/ABI/integrity validation,
  actual declaration probes and explicit unavailable capabilities.
- Separate Forge application/PATH ownership from Harness; refuse legacy adoption.
  No real migration from v7 is part of this new product.
- Prepare native installation/update/rollback/memory/theme acceptance on seven targets
  and run administrative code from the verified active Windows payload. Windows
  uninstall uses the external verified PowerShell installer to avoid a locked EXE.
- Add bounded anonymized usage exports, a separately reviewed provider-evidence gate,
  same-commit seven-target release assembly and exact published-entry Pages preparation.
  Publication remains explicit and disabled while external acceptance is pending.
- Preserve Linux terminfo case distinctions without relaxing generic package guards;
  bound immutable component-read retries and emit canonical SDD bytes on Windows.
- Parse valid distant ELF loader strings, handle the Darwin exited-child race, share
  verified payload traversal and retain bounded Windows installer timeout diagnostics.
- Preserve and bind Windows AppData SDK cache locations so NuGet migration state
  does not fall back into project source; keep source drift detection intact.
- Correct Windows fixture byte hashing and prepare all private-build tools in Pi CI.
- Canonicalize Windows project identity using native real paths; use Git's NUL
  device on Windows and preserve bound machine/AppData SDK resolver locations.
- Establish bootstrap architecture preconditions inside child PowerShell processes;
  fail explicitly on missing native metadata and yield during owned SDK fixture cleanup.
- Preserve canonical LF source across Git checkouts while retaining byte-pinned
  assets; reject mixed or missing source fingerprints during seven-target assembly.
- Validate 1,309 local Python cases (one dependency fallback checked separately),
  six OS/Node matrices with 102 SDK cases, all 11 Python/memory/browser CI jobs,
  all 16 installer jobs and the fresh installed wheel. All seven native lifecycle
  targets pass 20 steps, 29 registrations and 24 profiles with actual installed
  PTY/ConPTY file completion, themes, resize and cache refusal.
- Verify one source identity across seven downloaded targets and independently
  recheck all 16 universal output checksums. Exercise the assembled universal shell
  installer in a fresh private macOS ARM root without PATH changes.
- Keep the original Windows recording cause unknown after six additional focused
  passing resumptions. Prepare a current-source external trial packet with pristine
  per-trial project ledgers; real-provider and human visual acceptance remain gates.
- Remove simultaneous feature-push/PR Python and installer runs while retaining
  all PR, develop/main and manual checks. Record cancelled duplicates separately
  from the 43 successful primary checks. Publication remains pending.

## v0.1.0 — 2026-11-10

- Import the current Aikya implementation, including its Python core, Pi terminal,
  command adapters, tests, templates, plans and validation evidence.
- Start independent Forge versioning at 0.1.0 for both the Python distribution and
  Pi runtime; keep Python imports, command names and distribution names compatible.
- Point operational source/update URLs to jlema0590/aikya-forge. Preserve historical
  source attribution and explicit retained v8 payload compatibility.
- Add English and Spanish Forge READMEs with source installation, native build
  instructions, architecture and explicit outstanding acceptance work.
- Include managed distribution/migration work, including bounded backups for large
  legacy installation receipts; retain local memory, skills and reviewed ownership.
- Keep inherited release/Pages publishing workflows scoped to the original repository.
  This initial develop import creates no release, package publication or installer URL.

GENERATED BY AIKYA FORGE
