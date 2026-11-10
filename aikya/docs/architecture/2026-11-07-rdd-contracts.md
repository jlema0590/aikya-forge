# Initial RDD candidate and receipt contracts

Status: experimental route B work. This implements local persistence and
descriptive assessment. An approved process executor was added on November 8;
the reviewer and approval authority remain open. See
[executor boundaries](2026-11-08-executor-terminal.md).

## Candidate boundary

`freeze_candidate` captures a canonical project identity, Git HEAD when available,
change ID, session ID, explicit work scope, check/review policy and a content-hash
manifest. New and deleted files, tests and configuration affect freshness.
Non-Git projects are supported without creating a repository or worktree.

The manifest covers project files beyond the declared edit scope. Fixed exclusions
come from the existing index privacy/generated-directory policy; the candidate's
own validation dossier is excluded to avoid invalidating itself. Git ignore rules
do not silently exclude otherwise eligible source. Nested repositories and
nonexcluded symlinks are rejected. The initial limits are 12,000 files, 100 MB total,
10 MB per file and 1.9 MB serialized metadata. Exceeding a limit refuses capture
rather than describing a partial snapshot as complete.

Snapshots contain hashes, not source text. `is_current` rechecks the manifest and
Git base. It does not make the working directory immutable. Capturing and comparing
hashes is local computation and does not invoke a model.

`store_candidate(..., approved=True)` is a trusted host API. It writes immutable
historical manifests before atomically replacing the current pointer. A successor
must reference the current parent. A crash after the history write leaves a
retryable historical object; a pointer without its matching history is rejected.
Existing custom or inconsistent records are preserved and require reconciliation.

## Receipts and trust

Runtime data remains under `aikya/docs/validation/<change-id>/`:

- `candidate.json`: current candidate projection.
- `candidates/<sha256>.json`: immutable candidate manifests.
- `receipts.jsonl`: bounded, hash-linked process records.
- `checks/<run-id>/execution.json`: bounded executor metadata for bound checks.
- `checks/<file>`: legacy evidence supplied by the trusted host for unbound checks.

JSON records do not receive Markdown footers. New generated Markdown reports will
use the repository footer/index contract when the reviewer projection is added.

`record_process` records an observation submitted by the host. It does **not** run
the command or infer test counts from a log. It is now refused for checks with
frozen definition bindings; those must use `run_check` and `record_execution`.
Legacy unbound checks remain host observations, not execution attestations. Command arguments
are hashed instead of copied into the journal because they may contain credentials.
The journal records check ID, candidate/session identity, exit code, observed
executed/skipped counts and an evidence path/hash. Raw output is not duplicated.
Evidence must be nonempty, at most 64 KiB and inside the dossier's checks directory.
The new executor retains output hashes and sizes instead of copying stdout/stderr
to durable records. XML report files exist briefly inside the owned run directory
and are normally removed after parsing; a crash can leave one for reconciliation.

Writes use the existing cross-platform lock and atomic replacement primitives.
Duplicate submissions are idempotent; conflicting replays, foreign candidates,
unplanned checks, altered logs, broken chains and malformed schemas are rejected.
The journal is bounded to 200 receipts and 2 MB. History must be preserved when
new evidence is created; replacing an old log invalidates its existing receipt.

Hashes detect inconsistency; they do not authenticate execution or defend against
the machine owner replacing all records. Repository artifacts alone are not
consent. The host executor is trusted, model output is not, and no mutation or
receipt-authoring operation is exposed to Pi tools in this slice.

## Assessment and support CLI

`assess_candidate` reads stored state rather than accepting verdict arrays from a
model. It distinguishes stale source, missing checks, failed checks, unverified
counts, required review and checks passed. Zero executed tests or any skips remain
unverified under the initial conservative policy. JUnit, TAP 13, TRX and Go JSON
adapters are implemented; framework-specific native acceptance and policy
exceptions remain separate work.

Assessment is descriptive: `can_close` and `delivery_authorized` remain false.
A successful process receipt cannot stand in for review, workflow consent, commit,
push or deployment. The real reviewer adapter, event admission and legal review
transitions belong to the open R2 work.

The installed Python support CLI exposes previews and status:

```sh
aikya review snapshot --root . --id change-1 --session author --file src/service.py
aikya review snapshot --root . --id change-1 --session author --file src/service.py --approved
aikya review status --root . --id change-1
```

The first command writes nothing. The second stores the candidate; it does not
execute tests. A successor uses `--parent <current-candidate-id>`. These are support
CLI operations, not additions to the 28 public slash-command registrations.

See [route B status](../plan/2026-11-07-aikya-v8-implementation-status.es.md).

GENERATED BY AIKYA HARNESS
