# Pi controlled runtime: host authority, accounting and evidence

Status: experimental implementation on `feat/aikya-v8-pi`. The stable release remains
7.2.2; the private Pi package remains 8.0.0-alpha.0 with Pi 1.5.0 pinned. This document
supersedes the earlier read-only architecture description for the current branch.
It does not certify distribution, native platform acceptance or workflow parity.

## Ownership and transport

Python owns project configuration, canonical ODD/SDD engines, the existing local
code index/notes, documentation and RDD evidence. Pi owns the interactive session,
provider dispatch and terminal. Neither the legacy Claude loop nor a second memory
service is started by this runtime. Repository extensions, instructions, skills,
themes and prompt templates are not discovered automatically.

The bounded Python bridge uses an isolated interpreter and one validated JSON
request. Status/context/memory reads never create authority. A separate local-host
API handles accounting, SDD transitions and reviewer admission. That API is invoked
by trusted host code, not registered as a model tool. Local machine owners remain
trusted; this is not an operating-system sandbox or remote attestation.

## Source writes

The author model has status/context tools and, only in controlled mode, `aikya_write`.
No native shell, general filesystem tool or automatic worktree operation is enabled.
A replacement contains a relative path and complete bounded content. The terminal
shows the destination, old/new hashes, byte count and proposed content in a scrollable
confirmation. Cancellation produces no source effect.

The host creates a one-use HMAC grant with an in-memory random key. It binds project,
session, operation, content, original source hash, workflow revision and expiry.
Python checks that binding again immediately before the effect and reserves the
nonce durably before writing. Replays, drift, expired/foreign grants and uncertain
attempts cannot silently retry. Ordinary permissions are preserved; special mode
bits are not copied. Secrets, client/control files, generated runtime files,
symlinks and canonical documentation destinations are protected.

Writes currently replace at most 12,000 UTF-8 bytes, with an additional 8,000-character
Pi parameter limit; an existing source is inspected only up to 1 MiB. Parent folders
must already exist. General patches, directory creation and arbitrarily large file
editing are not implemented. A local source change can succeed while derived memory
maintenance is degraded; that result is reported separately instead of undoing code.

In SDD projects, historical approvals alone cannot unlock writing. The host must bind
a ready approved specification/task, explicit file scope and current session. That
signed binding includes the SDD state hash. Changed state, completed tasks, missing
dependencies, a different session or an out-of-scope path blocks the write. Changing
methodology or scope requires another explicit host operation.

## Accounting and provider boundary

A project-local usage ledger reserves each call before external dispatch. The real
Pi `ModelRuntime.stream` and `streamSimple` paths are guarded; completion helpers
use those paths. An explicit provider/model and available budget are required.
Missing configured authentication is rejected before reserving a call. This check
does not certify credential validity at the provider.

Usage records input/output/cache-read/cache-write counters once, with project,
session, role, selected English phase, provider/model and reviewer candidate binding
where applicable. Terminal completion is released only after durable recording.
A pending, missing, cancelled or unusable observation blocks further calls. Limits
and accumulated use survive resume and model changes. Raising a limit requires host
confirmation and preserves usage. A model runtime cannot acquire two wrappers.

Admission is a local threshold, not a hard provider spending cap: an admitted request
can cross its token limit before usage is reported. The implementation does not
measure subscription billing or derive account percentages from context size.
Automatic retries, cache warming and automatic compaction remain disabled; explicit
`/compact` uses the same model/budget boundary and may consume tokens. Native/provider
acceptance of long-session compaction remains open.

Before admission, serialized UTF-8 bounds are 32,768 bytes for system instructions,
16,384 for tool declarations and 131,072 for the complete context. Duplicate tool
names are rejected. These are conservative local byte policies, not token estimates.
The SDK integration fixture verifies tool declarations below 4,000 bytes and total
context below 10,000 bytes for its small request; it is not a production workload
benchmark or an asserted saving.

The local `/aikya-models` catalog returns at most 20 entries per page without provider
refresh or credential disclosure. Model selection remains explicit at launch.
Administrative catalog, budget, theme, phase and migration display messages are
removed from model context through the public Pi context event. Explicit scoped
source queries remain available. The real-SDK test reproduced catalog leakage before
this filter and verifies its absence in the assembled provider context afterward.

The quota panel observes only whitelisted numeric response headers. Anthropic 5h/7d
and Codex primary/secondary header fixtures are covered, without account endpoints,
credential import or extra inference. Missing data is unavailable, genuine zero is
preserved, invalid dates cannot crash rendering, and failed refresh retains the last
observation marked stale. These adapters require live-provider acceptance before
being advertised as supported subscription integrations. Local totals are separate.

## Independent review and TDD evidence

Execution-bound checks use the existing frozen executable/environment/definition
contracts and fresh JUnit, TAP 13, TRX or Go JSON results. A failed or uncertain run
never becomes passing evidence. Known durable execution metadata can be reconciled
with host approval; a pending attempt or a result file alone requires manual review.
Reconciliation never starts another process.

When a frozen candidate has a TDD policy, Green requires an executed failed ancestor
with positive failed counts, no skipped tests, the same check definition and unchanged
test files. Test changes restart Red. Missing Red blocks progression to review. Legacy
policies without TDD remain descriptive; full automatic classification/enforcement
across all development commands is still pending.

Independent review uses a different local Pi session with read tools only, a host
request ticket and a measured reviewer call bound to that candidate. Model JSON alone
cannot approve it. The current reviewer packet contains complete scoped UTF-8 source
within 6,000 bytes/20 paths; larger scopes must be split or escalated rather than
silently omitted. Findings, process-evidence identity and source freshness are checked
before signed admission. Blocking findings cannot be accepted. A second correction
request escalates. A successor requires fresh checks and review while retaining history.

Only an admitted current acceptance sets technical `can_close=true`. Delivery remains
unauthorized. Neither a Markdown success claim nor a copied review projection grants
approval. The generated canonical document index is a derived link projection excluded
from candidate identity; custom index prose remains source. Older snapshots may
therefore become stale and need explicit regeneration.

## Local memory, themes and onboarding

Source writes reuse the existing incremental index and HTML exporter without model
calls. Reviewed-note queries verify source freshness, omit unreviewed/stale notes,
respect project identity and return bounded results. An absent index remains absent
on read. Disabled policies stay disabled; customized HTML is preserved. Pi lifecycle
now owns a lease on the existing external-edit watcher. Start/activity events reuse
one observer, local heartbeats keep idle sessions alive, and shutdown awaits in-flight
renewal before releasing only that session. Other sessions retain their leases.
Headless SDK consumers await the returned `close()` helper; synchronous raw SDK
`session.dispose()` does not provide this asynchronous lifecycle contract.

`/aikya-theme` previews installed built-in light/dark themes, confirms activation,
restores the prior theme on persistence failure and saves a local project preference.
The parser checks source links, bounds, colors and variable cycles. External themes
are not installed automatically; terminal theme and HTML appearance remain separate.

Portable onboarding requires explicit ODD/SDD and a validated project profile. It
previews the repository/document footprint, rechecks freshness and composes the
existing canonical localized templates. It preserves source/custom documents and
creates neither Claude assets nor copied runtimes. Known managed legacy profiles can be adopted through an explicit `/aikya-migrate`
preview and confirmation. Signed local records and byte-exact backups protect profile
and runtime-selection changes; source, document bodies, memory policy, client settings
and installed skills are preserved. Audit Markdown is localized and indexed under
`aikya/docs/operations/`. Rollback refuses changed metadata, backups or customized
reports, can restore a known interrupted commit, and closes the interactive Pi session.
It does not change global installation or deactivate existing client settings.

Interrupted onboarding requires a fresh preview/confirmation; it can finish missing
managed documents without replaying an obsolete plan. A project initialized as new
can later be analyzed as existing, preserving its profile choices and source. Source
hidden under the `aikya` top-level folder is not treated as an empty new project.

## Remaining release gates

The private package still requires an explicit development `--runtime-dir`. A single
managed installer, full 28-command parity, ODD execution orchestration, skill lifecycle,
automatic phase transitions, complete runtime/installation migration,
native Windows/Linux workflows and live-provider acceptance are not complete. No
stable update channel is redirected to this alpha and no release has been published.

## Native check and review orchestration

The author tool set now includes `aikya_check` with frozen change/check identifiers.
It cannot supply argv or consent. Native `/aikya-tests` freezes explicit intent,
acceptance, bounded scope, ordered executable/environment bindings and a TDD policy.
A subsequent approved run may refresh only an in-scope candidate while preserving
that policy. `/aikya-verify` exposes current assessment, independent measured review
and known-observation reconciliation. Check/review progress uses public Pi custom UI
with cooperative cancellation and awaited settlement, not dependency patches.

Native execution records a private candidate/session/run/metadata-bound host witness
before final public evidence. Native receipt admission and recovery verify it; absent
or altered observations cannot authorize automatic recovery. Local owner tampering
and hostile approved test processes remain outside this trust claim. Successor storage
rejects source changes outside declared scope. Missing failed-test counts cannot prove
Red; refreshing definitions preserves their frozen order and regression-check identity.

Private exclusive session-role records keep author and reviewer resumption distinct.
Unknown/corrupt role records and legacy unmarked transcripts are preserved and refused.
Snapshot previews bind the resolved documentation language; signed review requests
capture it before execution so later policy changes cannot mutate an attested report.
See [native workflow evidence](../validation/2026-11-08-pi-native-checks.md).

## Canonical ODD adaptation

`services.odd_workflow` reuses `workflows.odd`; it does not duplicate normalization,
templates, dependencies or authoritative state. Native previews bind source/profile/
language/prior selection. A private signed task binding constrains the existing write
path by author, ready-task revision and files; selecting again revokes prior grants.
Native check policies also bind this workflow revision, including approved SDD tasks.

ODD completion requires matching scope/check names/objective/acceptance and current
independent reviewed evidence. A signed reservation precedes the canonical transition;
posteffect checks compare source, unrelated files, Git base and report fingerprints.
Uncertain completion cannot replay. Canonical reconciliation invalidates obsolete
outcomes and preserves custom documents. Completion is recorded at the accepted
candidate transition; task-metadata publication changes full-checkout identity and
is not lasting delivery authority. The native command remains a bounded ODD facade,
with full mobile/platform, skills and distribution acceptance still open.

## Explicit selected skill resources

The native skill facade reuses basic Agent Skills validation, canonical footer/index,
host signing and atomic writes. It inspects chosen local packages, records source
hashes and exact originals, and installs immutable data without executing imports.
A signed registry controls normalized Pi entries; default discovery and automatic
prompt listings stay disabled. Admin planning/status does not become model context.

The public Pi resource API receives only approved entries. Explicit author invocation
is checked against current signed bytes; actual expanded payload integrity is also
checked inside the model stream before admission/dispatch. Hook exceptions alone are
insufficient because the pinned SDK can report them and continue. Validated context
determines reference access through the existing bounded `@skill/` context alias.
Reviewers and uninvoked authors cannot read those resources. This adds no model tool
or execution permission. Scope is local project packages, with other native lifecycle/
source/compatibility work still open. See [skill evidence](../validation/2026-11-08-pi-selected-skills.md).

## Local diagnostic facade

`services/diagnostics.py` reuses validated profiles and the existing requirements
catalog for presence-only diagnosis, without calling SDK version commands. Native
Pi reports its actual runtime/provider selection through public APIs. Static quality
uses a captured bounded source/exception snapshot in a temporary directory and the
canonical quality engine, with source hashes and truncated findings. No diagnostic
result is promoted into an execution receipt or approval. Native admin output stays
outside subsequent model context; the model tool allowlist is unchanged.

## Declarative and documentation host boundaries

`workflows.py` adds explicit declarative onboarding and a hash-bound selected-file
wrapper around portable plans. `documentation_inputs.py` owns bounded profile/source
and signed page/baseline inputs. `documentation.py` reuses canonical template selection,
render/merge, write/index, signatures and maintenance. The Pi host adds native commands
and a scrollable confirmation; model tools are unchanged. Full source, profile,
locale, registry and reviewed-content identities are checked again immediately before
reservation/effects. Post-effect drift remains pending rather than reporting success.
Selected-source baselines are documentation comparisons, not another task/review engine.
They create no technical approvals; uncertain effects are never automatically replayed.

## Confirmed bootstrap operations

The native project/infra/scaffold adapter calls bounded host services; it does not
add model tools. `bootstrap_plans` captures bounded manifest inputs before reusing
canonical project/infrastructure/scaffold planners. `project_bootstrap` separates
read-only plans from confirmed localized records and named generation.
`generation` binds a complete reviewed byte batch to source/profile/language and
current task selection; it reserves effects, creates exclusively, preserves owner
files and records actual paths/hashes before index/memory maintenance.

`scaffold_recipes` binds known recipe arguments, installed executable/environment
and exact registry version/archive integrity. `scaffold_generation` resolves,
executes in private staging and confirms verified manifest copying separately;
`scaffold_records` owns signed provenance/currentness and bounded output inspection.
No helper module from the target project is imported. SDK/network/cache effects are
normal host processes, not OS-contained execution.

The canonical infrastructure validator catalog is shared with the legacy entry
point. `infra_validation` records signed process observations and localized receipts,
without inventing test counts or admitting RDD/ODD/SDD completion. Cancellation is
owned by the host and awaited. Pending/changed/failed results remain distinct from
successful generation/validation; automated pending reconciliation is still open.

## Native engineering adapters

`engineering_workflows` delegates anchored architecture updates and append-only bug
reports to the existing signed documentation transaction. `architecture_findings`
captures explicit source excerpts/hashes; it labels interpretations separately from
runtime proof. `bug_evidence` derives current reproduction/Green/review states from
native signed execution observations and the existing TDD lineage/admission.
`bug_document` renders the canonical register in a captured temporary snapshot;
source/ownership/locale and before/after content remain bound at the effect.

`mobile_workflow` delegates to canonical ODD or approved SDD selection. Optional
`mobile_scope` is backward-compatible typed context in the existing ODD state, not
another task store. SDD selection signs that context so reselection changes grant
identity. Read-only SDK presence remains separate from actual mobile acceptance.
All three adapters are author host commands; reviewer sessions gain no such command
and model tools stay unchanged. Administrative outputs do not enter later prompts.

GENERATED BY AIKYA HARNESS
