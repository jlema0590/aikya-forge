# Security boundaries of the private Pi runtime

The v8 branch separates model tools from trusted host operations. Its initial
controlled mode is not an operating-system sandbox. Test commands, the selected
Python/Node runtime and local machine owner retain their normal host privileges.
Stable 7.2.2 installation/update behavior remains separate from the private alpha.

## Model-accessible operations

Only bounded status/context queries and the author-only source replacement tool
are active. The reviewer receives read tools only. Shell, arbitrary native tools,
repository extension/skill/context discovery and automatic worktrees are disabled.
Auxiliary inference APIs without an accounting contract are refused.

Source replacement requires interactive host confirmation. An ephemeral host key
signs project/session/operation/content/source/workflow/expiry bindings. Python
rechecks them and reserves the nonce durably before the write. A consumed or uncertain
attempt cannot replay; concurrent submission has at most one admitted effect. Paths
are relative and bounded, protected control/secret paths and links are rejected, and
source drift preserves the newer content. SDD additionally requires a signed current
ready-task binding and explicit file scope for the active session.

Model-readable repository metadata is not an approval. Host-only API calls and native
confirmation callbacks are not registered as tools. Local owner tampering, hostile
native code and same-user filesystem races are outside the claimed isolation boundary.

## Inference, state and disclosure

The local ledger admits calls once and records observed counters before releasing
completion. Missing/pending/unknown use blocks further dispatch. Selected model,
request-size and configured-authentication checks run before admission. This neither
certifies remote credentials nor hard-caps an already admitted provider response.

Private sessions, credentials, approvals and accounting live in ignored project-local
state. Startup rejects already tracked `.aikya/pi` state and ineffective ignore rules;
it does not silently untrack user files or import personal credentials. The Python
child uses isolated mode, bounded JSON and generic errors. Write keys/grants and raw
execution output are not copied into public result metadata. Source queries still
require bounded paths and freshness; stale/unreviewed notes are omitted.

## Evidence and closure

An execution-bound check needs its frozen executable/definition/environment, current
candidate and fresh valid result. Zero/skipped/missing results, timeouts, cancellation,
changed source or uncertain attempts do not pass. Recovery attaches only already
known execution metadata with host approval and never starts a process.

Independent acceptance needs a different measured reviewer session and candidate-bound
host request, signed admitted history and a current report. Model prose/JSON alone
cannot close a candidate. Blocking findings cannot be accepted, stale evidence is
invalid, and successors require fresh checks/review. Optional TDD policies require
executed failed ancestors with unchanged tests. Technical closure does not authorize
push, merge, deployment or release.

See the [current architecture](../architecture/2026-11-08-pi-controlled-runtime.md),
[observed tests](../validation/2026-11-08-pi-controlled-runtime.md) and
[open release gates](../plan/2026-11-07-aikya-v8-implementation-status.es.md).
Native process cleanup, complete migration/rollback, live-provider acceptance and
full workflow enforcement remain open; passing contract fixtures does not certify them.

## Migration and asynchronous lifecycle

Managed legacy-profile adoption stores signed local records and exact original
bytes before metadata effects. A stale preview, unknown owner/selection/folder,
changed backup or customized report is refused. Known partial metadata commits can
be rolled back explicitly; unrelated source and memory policy are not restored over
newer work. The audit document remains indexed under `aikya/docs/operations/`.

Pi shutdown cancels future local lease renewal, awaits any in-flight renewal and
releases only its own session. Other sessions remain active. Headless integrations
must await the provided `close()` helper. Full native installation/runtime migration
and compatibility acceptance remain separate release gates.

## Native check and reviewer controls

The author-only `aikya_check` tool accepts frozen identifiers, never arbitrary argv,
consent or a result. Native UI confirms the concrete operation; no-UI consumers cannot
execute it. Terminal cancellation requests stop only the owned approved run and waits
for settlement. Native policies require a private signed host witness matching final
metadata before evidence admission or known-result recovery. Public JSON alone cannot
supply that proof. The local owner and approved processes remain trusted; no remote
attestation or system sandbox is claimed.

Successor source changes must remain within declared review scope. Independent review
rechecks the candidate across confirmation and ticket creation, uses a distinct
read-only measured session and preserves delivery separation. Explicit local session
roles constrain resume; unknown or corrupt transcripts/role records are not adopted.
Generated report language is bound before publication to preserve signed identity.

## Native ODD task controls

A host-confirmed signed selection limits source writes by project/session/current
ready task and exact files. Profile, language, prior selection and source drift invalidate
native previews. Rebinding revokes prior grants; known selection release requires
another confirmation and preserves documents. Unknown signed-state schemas/custom
artifacts are not adopted. SDD cannot be replaced by this ODD facade.

Recording `done` needs current matching task intent, scope, check names, native workflow
identity and independent admitted acceptance. A private signed reservation precedes
the worklist effect. Afterward, source/Git/unrelated files and actual report fingerprints
are rechecked; changed evidence blocks or invalidates completion. Interrupted effects
stay uncertain and cannot automatically replay. Local account/native-process trust
limits remain; completion is neither remote attestation nor delivery authorization.

## Selected skill data and hard dispatch checks

Native source planning is read-only and accepts only explicit local packages with
bounded regular files, protected-path/link refusal and basic metadata validation.
Installation requires a fresh native confirmation, reserves before effects, keeps
exact originals and signs current private ownership. Partial copies without committed
registry cannot activate; unknown/custom data is preserved. No code, hooks or package
manager runs during installation, and frontmatter cannot grant tools or permissions.

Only approved normalized entries reach Pi's explicit resource API; default discovery
and automatic prompt listings remain disabled. Verified author invocations unlock
only signed current references. Reviewers and uninvoked authors cannot read them.
The real model-stream gate checks expanded instructions before budget admission and
dispatch, including forged/stale blocks. SDK hook exceptions are insufficient as a
stop mechanism; public input hooks return handled denials and the hard gate remains
independent. Same-account/native code control is outside the sandbox claim, as before.

## Native diagnostic limits

Native doctor never runs toolchain wrappers or inspects provider secrets: it reports
command presence and a configured-auth boolean. Native quality accepts explicit
bounded regular source bytes, refuses private/control/secret paths and inspects a
frozen temporary snapshot using existing maintainability rules. Diagnostics do not
execute code, write project documents, create grants, admit receipts or approve
delivery. A clean static result does not mean security validation succeeded.

## Native documentation ownership

Native document writes require the actual host confirmation of exact before/after
content and selected sources. Reserved workflow/control paths and private summary
references are refused. Signed current page hashes protect later custom edits;
initial generated-page updates require explicit content review. Private operation
reservation precedes effects; interrupted/external-drift outcomes remain pending.
Completed sync identities cannot be reused by deleting public Markdown. Baselines
bind the original author and selected paths; records say checks were not executed
and provide neither ODD/SDD stage approval nor delivery authority.

## Bootstrap and local validator boundaries

Native project records require concrete reviewed intent. Generated artifacts are
bounded, source/profile/locale/task-bound and created exclusively, preserving files
introduced concurrently. Private reservations precede effects and prevent replay.
Post-copy task/source drift refuses success and preserves the uncertain outcome.
Protected paths, links, secrets and workflow controls use the existing path policies.

Known generator recipes resolve exact registry identity/SHA-512 bytes separately
from confirmed execution. Source/profile/executable/environment/staged-manifest drift
blocks copying. Target-project helpers are never imported. Generator/package-manager
and validator code retain normal host privileges, network/cache/configuration access;
these controls do not isolate the operating system or attest every SDK dependency.
No cloud apply/deploy recipe or general model shell tool is enabled. Local validator
process observations have no test counts, method approvals or delivery authority.

## Native engineering evidence

Architecture findings bind exact source lines and hashes, rejecting private/missing/
changed sources and unsupported claims of runtime verification. Bug reproduction
requires native observed failed regression counts; zero tests, environment failures,
borrowed intent/author evidence and stale source cannot certify a fix. Positive
checks and current independent acceptance remain separate from deployment authority.
The canonical bug register uses signed document ownership and pending reservations;
custom edits/duplicate IDs remain preserved.

Mobile scope is explicit typed canonical context. ODD cannot silently switch the
recorded feature platform; signed SDD reselection revokes older source grants. Native
SDK presence queries execute no wrappers and make no compatibility/build/simulator
claims. Metadata transitions preserve the existing source execution controls.

## Native validation types and recovery

Frozen process validators carry actual exit/timing/hashes and no test counts. An
exit-zero validator cannot supply behavior Red/Green or refactor test baselines.
Explicit nonbehavior classification requires compatible scope and a reviewed reason;
refactors require executed positive ancestors with unchanged tests and final review.
This classification cannot prove semantic equivalence or contain tool side effects.

Only completed signed same-author/base operations can authorize canonical living
Markdown deltas across a native check iteration. Manual gaps, changed bytes and
methodology controls stay protected. Final review includes observed pages within the
shared complete-source bound; previous checks and acceptance never transfer.
Document recovery validates a signed pre-effect reservation, all exact effects and
unchanged surrounding source/profile/language before completing bookkeeping. It
never replays writes or promotes partial/uncertain outcomes. Proposed native source
bytes use the shared size policy; content-bound exceptions are rechecked at execution.

## Native source batches

The existing write tool accepts source batches only for a current native author
candidate and approved ODD/SDD scope. Exact original-text anchors, complete content
hashes, locale and workflow bind the ephemeral grant. Dialog mutation, ambiguity,
case/parent collisions, out-of-scope/control/binary destinations and replay are
refused. No general shell, extra model approval argument or independent-reviewer
write permission is introduced. Each changed file retains the shared size policy.

Reservation precedes effects; source is rechecked before each operation and actual
bytes are read back. Several files are not one atomic filesystem transaction and
external processes do not share the host lock. Preserve partial/uncertain effects
and concurrent edits for reconciliation; never roll back user edits automatically.
Pending/orphan reservations block new writes. Confirmed recovery only completes
known matching effects without source replay or grant renewal; audit stays in the
owned candidate dossier and does not authorize tests, acceptance or delivery.

## Bounded native task ownership and inference admission

One signed task run owns the project while active. Bind its original author,
canonical task intent/scope/check policy, provider/model, call cap, absolute deadline
and one correction allowance. Every author/reviewer/summary stream awaits the host
guard before provider dispatch and records observed use in the existing ledger.
Unknown accounting, unresolved completion, changed source/selection and original
caps block further inference. Local limits cannot predict the final size of an
already admitted provider response or claim provider subscription quota enforcement.

Run source changes require the reserved batch protocol; the legacy single-file
path remains available outside task cycles. A declined/blocked tool stops the loop.
Local checks keep normal host privileges and independent reviews keep separate
sessions with no author write/check tools. Security applicability selects existing
frozen checks or a confirmed reason reviewed as data; a label is not a scan.
Only current independent acceptance can propose native task metadata recording,
with separate confirmation and delivery unauthorized. Known metadata recovery
requires the original signed proof and unchanged effects, never another write grant.

Task data stays bounded and is reinstated from local signed state after explicit
compaction. Summarization is charged like any model call and cannot restore grants,
reset caps or select a reviewer transcript as author. Only canonical link-projection
indexes are replaceable: the generated footer alone never authorizes custom prose
replacement. Source, sessions and memory remain project-local.

## Native skill source and version boundaries

Native skill administration is separate from model tools. Global storage is inert;
only an explicitly selected, signed project copy can supply an author skill. Every
provider stream checks the effective selection, so retained rollback bytes cannot
keep superseded instructions active. Reviewers remain isolated. Imported tool/hook
metadata, executable resource modes and dependencies grant no execution authority.

Shared public GitHub capture validates commit/tree identity, regular-file modes,
truncation, bounded paths/data and Git blob identities before materializing bytes.
There is no checkout, source execution, client credential/helper discovery or redirect
adoption. The generic legacy chosen-skill installer shares capture while retaining
its distinct legacy data limits. Other historical explicitly requested vendor
installers are not the native path and are not installed/recommended by default.

Signed pending records precede writes; exclusive package creation refuses replacement.
Known complete promotions can be reconciled without copy/download replay. Partial or
customized packages, archives, registries, comparisons and audits are preserved for
review. A generated footer alone never proves ownership of an operation audit. These
are cooperative local-host boundaries, not isolation from a process holding the same
OS identity and private signing key. Native Windows/Linux execution remains a release
gate even when portable-name/junction cases pass on the development host.

## Managed native distribution under acceptance

The administrative installer is not a model tool. It verifies fixed official inputs,
uses isolated npm configuration with scripts disabled, materializes only bounded
regular archive data, and binds the full final payload to a signed active receipt.
Transport SHA-256 is integrity evidence, not an independent publisher signature.
The native payload has ordinary user privileges; no OS sandbox is claimed.

Reservations precede final copies. Fixed import/help probes run only on explicitly
selected verified data; a second inspection refuses generated/changed bytes before
promotion. Launcher ownership is checked again after preparation. Partial effects
remain pending without automatic replay; old payloads and user data are retained.
The application signing key is administrative metadata, not global project memory.

GENERATED BY AIKYA HARNESS
