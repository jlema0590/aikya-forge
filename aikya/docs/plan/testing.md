# Token efficiency verification

The offline acceptance battery executes support contracts for all 28 public
commands in disposable projects. It includes expected denials, ODD/SDD onboarding,
checks that fail and unchanged files outside `aikya/docs/`. It does not ask a model
to implement all 28 workflows and does not install third-party skills or deploy.

The language matrix covers all 29 index suffixes. Python uses AST; optional pinned
Java, JavaScript, TypeScript, C#, Go and Dart grammars have semantic fixtures and
forced missing-dependency cases. Other extensions remain inventory-only. Tests
exercise edits, renames, deletion, allowed-file scope and separate project identity.
Workflow fixtures validate stack profiles and specialist selection; application
compilation needs its toolchain and is reported separately, not inferred.

Loop tests check that Review shares the total-turn budget, usage survives replay
and resume, unknown/empty usage is unavailable and exhausted model budgets preserve
local validation before stopping another model query. Documentation preflight and
Stop share one rule; neither creates passing evidence. Explicit deterministic check
reuse requires matching source, command definition, executable/environment binding
and successful prior process evidence. Checks with external/unknown inputs must not
opt in to reuse.

Synthetic browser tests cover both viewer languages, inventory isolation, layout,
dragging, animation, inspection, reduced motion and offline behavior. Installed-wheel
and clean-installer tests run in separate temporary homes. The exact executed
results and remaining native/model experiments are recorded in
[validation](../validation/2026-10-29-token-efficiency.es.md). Never replace unknown
provider usage with zero or claim quota savings from fixture character counts.

## Command registration and workspace regression — 7.2.2

Use temporary homes/projects to reproduce global plus project command duplication,
then verify fresh registration, onboarding, old managed provenance, backup integrity,
legacy aliases, customized/extended folders, read-only preview and standalone local
fallback. Global registration must not scan unrelated project directories.

Execute the installed workspace hook outside the source checkout. Worktree creation
through recognized Git/Claude commands, Agent/Task isolation and EnterWorktree must ask
for permission. Editing files, creating branches and listing worktrees remain normal.
Verify custom settings and hook idempotence. Test inputs never create a worktree.

Wheel, clean-installer and public-command acceptance run separately from the isolated
regression suite. Their results and unexecuted real-host/native-platform checks are
recorded in the 2026-11-05 validation report; passing an offline contract is not proof
of provider quota savings or a model completing every command.

## PR #30 native CI corrections

Byte-preservation acceptance now includes historical command-renaming fixtures.
Exercise a real Git checkout with Windows line-ending conversion enabled; fixtures
must preserve the bytes used by the strict migration catalog. Native Windows
command-scope acceptance must retire the known alias and preserve its exact backup.

Installer preservation tests resolve temporary roots before calling the API so
macOS /var aliases do not silently skip conservative hook registration. Compare
settings bytes before/after repeated installation, retain user hooks and permissions,
reject duplicate registered commands and require exactly one workspace guard.
Do not replace these behavior checks with an assumed total number of hook groups.

See [CI bug record](../bugs/2026-11-05-pr30-ci-regressions.md).

## Pi service and SDK contracts — v8 development

Run `python -B -m unittest discover -s tests -p test_service_bridge.py -v`
for the real-process service contract. In `packages/aikya-pi`, run `npm ci
--ignore-scripts`, `npm test` and `npm run typecheck`. The SDK tests dispatch a
local command without prompting a model, persist and resume separate project
conversations, reject unsafe state paths and suppress repository extension loading.

Run the Python regression from a temporary user configuration and an installed
checkout package, without inherited PYTHONPATH exposing distribution metadata to
pip in newly created environments. Live-memory tests require loopback sockets;
permission-denied results are environment failures, never evidence of correctness.
Record initial failures and targeted reruns separately instead of calling the
whole suite green after only rerunning affected modules.

Native Pi jobs exercise Node 22.19.0/24 and Python 3.13 on the three OS families.
No job outcome is claimed before execution. Live models, full RDD, production TUI and short-install
acceptance remain open in the [v8 validation report](../validation/2026-11-07-aikya-v8-first-slice.md).

## Scoped context and initial RDD acceptance

Run `python -B -m unittest discover -s tests -p 'test_review_*.py' -v` alongside
the bridge and Pi suites. Use an installed checkout interpreter for CLI tests and
set `AIKYA_TEST_PYTHON` for npm tests when the default Python is not that interpreter.
Context suffix fixtures cover retrieval, not native language compiler/test support.

RDD tests verify source/configuration drift, Git HEAD, untracked/deleted files,
custom records, immutable-manifest consistency, duplicate/concurrent submissions,
log alteration, journal schemas and command-argument privacy. Process-result
fixtures test the recording contract; they do not certify an executor or reviewer.
The descriptive assessment must keep workflow closure and delivery unavailable.

## Executable RDD and terminal acceptance — November 8

The review suite now includes actual child processes, native Node TAP/Go JSON,
strict XML/TAP/JSON adapters, approval/session/definition drift, missing/zero/skipped
results, cancellation, timeout, output bounds, raw-output privacy and uncertain
attempt recovery blocking. XML fixtures and controlled Python producers do not
establish native Java/.NET/framework acceptance. Keep that distinction in reports.

Run `test_terminal_entrypoint.py` for explicit runtime/interpreter selection and
the npm suite for the real SDK, project state protection, restricted editor,
native shell gateway and per-instance inference refusal. Perform a separate PTY
smoke with status/context, an ordinary prompt, blocked export/shell and `/quit`.
No live provider is required for these read-only checks. Windows/Linux PTY and
native process cleanup require their own recorded execution.

The full Python regression completed 772 tests in 992.577 seconds with two skips
and no failures. The 19 Pi tests and typecheck passed separately after the final
terminal changes. See [exact scope and limits](../validation/2026-11-08-aikya-v8-executor-terminal.md).

See [observed validation](../validation/2026-11-07-aikya-v8-rdd-context.md) for exact
runs, including the separate broad regression and later targeted checks.

## Controlled Pi contracts — current November 8 snapshot

The complete Python snapshot completed **817 tests in 1002.121 seconds**, without
failures and with two skips, using an installed checkout, isolated temporary home,
no inherited PYTHONPATH and permitted local loopback tests. Later TypeScript-only
changes have their separate Pi/typecheck verification. Do not interpret these results
as live inference or native Windows/Linux acceptance.

Run `test_service_authorization.py`, `test_pi_*.py` and `test_review_*.py` for one-use
grants, source/session drift, budgets, current reviewed notes, memory/HTML write events,
portable onboarding, task scope, canonical SDD transitions, reviewer admission,
recovery and optional executed Red/Green policies. The Pi suite uses real SDK sessions
and real Python subprocesses with fixture provider transports; no model request is
sent. It also checks prompt size, duplicate budget wrappers, unavailable credentials,
invalid quota clocks and scrollable confirmation controls.

The macOS PTY test verified theme cancellation/application/reopen, persisted budget,
no-call memory status, cancellation without profile writes, and approved SDD onboarding
with local HTML and no Claude assets. The locked npm dependencies installed offline
in a disposable directory with scripts disabled. Native CI definitions now include
the new Python service/Pi contracts; their remote execution is still pending.

## Pi local continuity and profile migration

The new full Python snapshot completed **829 tests in 1095.316 seconds**, without
failures and with two skips. The Pi suite completed **46 tests**; strict/erasable
TypeScript and isolated installed-wheel acceptance pass. Keep the earlier 817/40
figures as evidence of their earlier snapshots rather than adding them together.

The lifecycle suite uses the actual project watcher and SDK runtime/headless teardown,
checks external edits, multiple leases and idle renewal without inference, and waits
for owned closure. Migration tests use actual installer profiles for all three project
kinds and both methodologies, plus interrupted metadata effects and customized backups.
Portable onboarding tests require a new confirmed preview after interruption.

Model-catalog tests verify bounded pagination and no credential/provider exposure.
An SDK integration first reproduced catalog output leaking into model context, then
verified administrative filtering in the actual assembled request. The real terminal
also exercised migration/rollback, exact original restoration and the local footer.
See [the current evidence and open gates](../validation/2026-11-08-pi-memory-migration.md).

## Native check/review continuity

Run `test_pi_checks.py`, `test_review_*.py` and the Pi SDK suite. Verify executed Red
and Green, preserved ordered policy, in-scope successors, missing-count failure,
private host-witness recovery, headless refusal, cancellation before/after launch,
and author/reviewer resumption. Project-language tests cover snapshot preview drift
and idempotent signed review after a later language-policy edit. The macOS PTY smoke
uses actual local processes; its review stays blocked in model-disabled mode.

[Current native evidence](../validation/2026-11-08-pi-native-checks.md) records the full
regression separately from SDK transport fixtures, wheel acceptance and PTY results.
Do not infer Windows/Linux, provider compatibility or token savings from those runs.

## Native ODD workflow coverage

`test_pi_odd_workflow.py` exercises canonical localized preparation, no-dossier small
work, scope/session/state binding, prior-grant revocation, SDD separation, actual Red/
Green and admitted fixture review. Test stale source/profile/prior selection, changed
review during the metadata effect, uncertain completion without replay, reconciliation
and preservation of custom records. SDK tests require no effects without UI consent.
A separate actual macOS Node 22 terminal checks cancellation, English phases, prepared
Spanish documents/index, unobserved completion refusal and confirmed release.

The [ODD report](../validation/2026-11-08-pi-odd-workflow.md) records final full-suite,
minimum-Node, installed-wheel and SDK results independently. Local loopback must be
available for the existing live viewer; an environment-denied run stays recorded as
failed rather than being relabelled from a narrower repetition.

## Selected-skill acceptance

Run `test_pi_selected_skills.py` and the complete Pi SDK suite. Verify empty/read-only
state, preview drift, unknown/custom data, exact originals, preserved comparison rows,
partial copy without activation and manifest-only current resource reads. The real SDK
fixtures check absent ordinary context, one explicit body, changed/forged instructions,
reference denial for uninvoked authors/reviewers and allowed reads after invocation.
Assert captured results outside fixture stream callbacks: the SDK can convert their
exceptions into assistant errors. The hard model-stream gate must refuse before budget
admission even if extension hook errors are reported and execution continues.

A separate macOS Node 22 PTY exercises cancellation and confirmed local installation
without inference, then verifies localized audit/footer/index and original archive.
[Skill validation](../validation/2026-11-08-pi-selected-skills.md) records full regression,
installed-wheel and native limitations independently.

## Native diagnostic contracts

Exercise unconfigured/malformed profiles, command presence versus compatibility,
unsupported iOS hosts, no SDK subprocess/credential disclosure, bounded explicit
source/exception snapshots, every indexed suffix, Dart/ES modules/Python-stub coverage,
changed source during inspection, reviewed size-exception hash drift and oversized
duplicate-location output. Real SDK calls must observe zero provider dispatch/budget
calls for diagnostics and omit admin reports from later context. No local diagnostic
is evidence that tests/security checks passed.

## Declarative profiles and documentation

Test new/existing answers, explicit ODD/SDD, selected-file hash/links/duplicate fields,
established method preservation and bounded wire plans. Exercise native template
catalogs and exact before/after confirmation; source/profile/language drift including
a change after the last preview; custom/modified pages; retained unrelated sections;
private summary evidence; duplicate footer; registry/output bounds; interrupted effects;
selected-source creation/deletion; no-change/no-op behavior; actual updated-document
lists; and completed-request replay after public record deletion. Verify no inference
administration, context exclusion and canonical metadata rather than fabricated tests.
Run the complete regression, real Pi SDK, installed package and native terminal flow.

## Native bootstrap contracts

Exercise plan-only project/infra/scaffold paths without effects, required native
confirmation, stale source/profile/locale/task rejection, exclusive no-overwrite
creation and durable uncertain outcomes. Check known generator resolution,
SHA-512 archive identity, installed executable/environment drift, staged content
inspection, failed/empty/linked output, cancellation before/during execution and
separate confirmed copying. Never import target-project helpers.

The shared infrastructure validator catalog must preserve legacy behavior. Native
validator fixtures establish process outcome/cancellation and replay protection,
with no fabricated test counts or delivery admission. Official SDK/framework/native
platform acceptance remains separate. Test real Pi routing, command uniqueness,
headless refusal and administrative context/budget exclusion. Verify the installed
wheel with minimum Node and a real terminal, then record full regression results
for the frozen source snapshot before committing.

## Native engineering contracts

Verify exact excerpt/line/hash anchoring and source drift before architecture writes.
Exercise native failing regression, unchanged-test Green, zero-test/environment
failure, independent admission and post-review source drift before labeling a bug.
Preserve unique bug IDs, existing sections/registers, locale and pending writes.
Verify mobile profile/platform/path scope, missing tools without SDK execution,
canonical ODD context and approved SDD selection. Rebinding context must revoke
previous write grants; embedded footer input must fail before effects. Test actual
Pi command uniqueness, reviewer exclusion, headless confirmation and administrative
context/budget exclusion. Keep real mobile SDK/device and provider acceptance separate.

## Native check types and documentary continuity

Verify actual process success/failure/cancellation/output limits with null test
counters and frozen check types. Prevent process evidence from supplying TDD Red or
positive refactor baselines; preserve legacy policy identity, ordered checks and
explicit classification through refresh. Test positive unchanged-test ancestors,
missing/failed/edited baselines and incompatible nonbehavior scopes.

Exercise same-author/base signed documentary chains, manual gaps, altered signatures,
methodology controls, oversized final reviewer packets and fresh-check requirements.
Recover only exact fully reserved effects after confirmation; partial, stale, foreign
or legacy outcomes remain pending. Assert no document replay, unchanged user bytes,
index/ownership recovery and source changes during maintenance. Verify proposed-source
line boundaries/content-bound exceptions, one Markdown footer, macOS exited-child
cleanup and explicit .NET/npm staging names. Record full regression, installed-host,
minimum-Node SDK, real terminal and official generator evidence separately.

## Native source batches

Exercise unique original-text anchors, self-overlapping matches, overlapping edits,
case aliases, parent/file conflicts, source/candidate/author/workflow/locale drift,
no-ops and wire/source-size bounds. Verify actual multiple-file patches, exclusive
creation, explicit bounded deletion, per-effect rechecks, readback and owned audit
paths. Test deep copies across confirmation, expired/foreign/replayed grants and
backward-compatible single-file grants through the isolated bridge.

Inject failures before the pending pointer, between effects and before bookkeeping.
Retain partial/unknown outcomes, block new writes and reconcile only exact signed
complete effects after confirmation. Assert no source replay, preserved user bytes
and unchanged modification times. Use the actual SDK for headless refusal and native
command routing; test the installed wheel/minimum Node and real terminal separately.

## Bounded selected-task cycles and session continuity

Exercise actual canonical ODD/approved SDD selection, intent/scope/check equality,
explicit native confirmation and one project run owner. Persist calls/deadline and
correction allowance across stop/resume; test unavailable usage, exhausted caps,
foreign sessions/models, changed source/policy and nanosecond JSON round trips.
Validate current positive checks and independent measured acceptance before task
recording; reconcile known completion without replay and preserve unknown effects.

Use real Pi sessions and isolated Python services with only UI/provider transports
simulated. Test positive ODD/SDD completion, refused edits with no subsequent
provider dispatch, reserved batch-only task writes and exactly one evidence-bound
correction before stopping. Exercise the public settlement boundary, explicit split
turn compaction (including both measured requests), bounded checkpoint reinjection,
source unchanged on cancellation and no headless approval. Preserve large/corrupted
histories for a fresh session and skip a known other role before resume size checks.
Do not infer real-provider or native-platform acceptance from these fixtures.

## Native skill lifecycle regression

Exercise local and pinned public data sources, independent global/project choices,
exact original archives, prepared manifests, explicit invocation, stale expansions,
retained rollback, capacity preflight and complete-effect recovery. Transport fixtures
replace external HTTP only; the real package/host/SDK/filesystem paths run locally.
Native confirmation simulations complement actual terminal checks and do not replace
them. Do not use personal skills, credentials or real provider inference for these
local tests. Full-suite evidence must refer to the final unchanged source snapshot;
interrupted earlier attempts remain separate. Installed-wheel and minimum-Node
contracts are recorded apart from editable-checkout tests.

## Managed v8 native product acceptance

Run `test_managed_*.py` for bounded recipes/archive data, private versions, channel
selection, ownership, CLI entry, migration, reservation/reconciliation and deterministic
bootstrap assets. Run the complete Python/Node regressions on a frozen input snapshot;
targeted passes do not replace them. Build two native private releases, use isolated
HOME/PATH with no Python/Node/npm/Git, and observe install → bare terminal → update →
rollback → uninstall, retained global skills and unchanged project files. Archive
availability/Windows executable containers are distinct from native OS execution.
Record each failed attempt and its regression before repeating installed acceptance.

GENERATED BY AIKYA HARNESS
