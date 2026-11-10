# Token and context policy

## Retrieval and output

Implementation workflows share a local current-source packet with a default total
serialized budget of 6,000 characters. The context API accepts 512–16,000 characters;
this is a character bound, not a tokenizer or a limit on necessary follow-up reading.
Source hashes, project identity and allowed paths are verified before reuse. Missing
parsers/indexes use explicit limited fallback instead of stale declarations.

Backend `--summary` responses target 2,000 characters while retaining required
blockers. If blockers exceed the preferred budget, the output reports that condition
rather than truncating them. Full responses remain available. Static instruction
footprints and tool-output bytes are reported separately from model usage.

## Measured usage and budgets

Recorded model usage separates input, output, cache creation and cache reads.
Duplicate cumulative snapshots are deduplicated. A temporal session interval is
labeled as such; it is not exact per-command billing. Missing values remain unknown.
The account five-hour/seven-day quota requires fresh provider telemetry and cannot
be inferred from these sums.

The opt-in agent loop retains per-query `max_turns` and adds optional cumulative
`max_total_turns` and `max_recorded_tokens`. Implement and Review share the ledger,
including after resume. Missing recorded usage blocks an enabled cumulative budget
instead of treating it as zero. Limits prevent the next query; reported tokens can
arrive after the current query has already exceeded its remaining margin. Local
Validate/Security checks can still record their real evidence before a query stop.
These controls do not cap unrelated interactive host requests or account quota.

## Long sessions

Native compaction is manual by default. `aikya context-policy` prints the manual
recommendation without writes. Explicit `--native-auto --approved` can configure a
project when the installed host advertises support and an execution observer exists;
custom model/window/environment overrides require review. The requested default
working window is 200,000 tokens, not proof of the host's effective window.

The 75% warning requires fresh verified effective-window telemetry. Standard native
model context percentage is insufficient and normally leaves this warning N/D.
Compaction can consume tokens and rebuild cache; it never resets prior quota.
Aikya does not issue `/clear`, run `/compact` in a shell or add a summarizing model.
Pending checks, approvals and accumulated budgets survive compaction.

## Acceptance and evidence

Routing preserves explicit model choices and required independent security/review.
Small contained ODD work need not create an empty dossier or add specialists by
ritual. Skills from external sources remain user-selected; no vendor is preselected.

[The local v7.2.0 report](../validation/2026-10-29-token-efficiency.es.md) measures
bounded context and tool-output characters. Real token/quota savings remain unmeasured
until equivalent accepted tasks run with controlled model, effort, cache and budget.

## Pi controlled preview

Pi uses a separate project-local `.aikya/pi/usage.json` ledger because it owns the
provider calls; it does not concurrently start the legacy Claude agent loop. Each
call is reserved before dispatch and durably reconciled before completion. Unknown
usage blocks subsequent calls. Resume, model changes and explicit limit increases
preserve prior use. Missing configured credentials and oversized prompts are refused
before admission. An admitted call may exceed the remaining token margin.

`/aikya-tokens` separates local observed counts from whitelisted provider response
headers. Missing/stale quota remains marked as such; header fixtures are not live
subscription acceptance. `/aikya-phase` explicitly labels subsequent usage; it does
not approve a task. Manual `/compact` is budgeted and can consume tokens.

The serialized UTF-8 request bounds are 32,768 system bytes, 16,384 tool bytes and
131,072 total bytes; duplicate tool names are refused. These are byte limits, not
estimated tokens. See the [current architecture](../architecture/2026-11-08-pi-controlled-runtime.md)
for measured fixture bounds and the remaining long-session/provider acceptance.

## Administrative context and idle memory

The local paginated model catalog performs no provider refresh. Catalog, budget,
theme, phase and migration display messages are excluded from subsequent model
context; explicit scoped source/notes queries are retained. A real-SDK fixture first
reproduced catalog leakage, then verified its removal before provider dispatch.
No production token-saving percentage is inferred from that fixture.

Memory observation and idle lease renewal are local processes without inference.
The footer separates local recorded tokens from unavailable provider/context data;
missing telemetry is never rendered as a zero account percentage.

## Native checks and independent review

Freezing, running, cancelling or reconciling a check performs no inference. Results
are bounded identifiers, counts and assessment; raw test output is not persisted in
public metadata. The surrounding author conversation still consumes its measured
provider calls. An approved independent reviewer uses the same durable project budget
with distinct reviewer/session/candidate attribution, and can be cancelled. Model-
disabled launch cannot accidentally infer from an SDK default model. Passing checks
never silently dispatches a reviewer or authorizes delivery.

## Native ODD commands

ODD preparation, status, selection, reconciliation and guarded recording use local
services and no model dispatch. Status pages contain at most 20 tasks; preparation
returns a compact result instead of repeating the complete worklist. The author may
still use budgeted inference while implementing; independent review requires its own
explicit confirmation and shares the durable project budget. Exact intent/check/scope
bindings prevent reusing an unrelated review to record a task. No token-saving amount
is inferred from these bounds or fixture runs.

## Explicit skill context

Skill status/planning/installation use no inference. Admin displays are filtered from
model context; installation does not advertise full skill bodies automatically.
An explicit invocation contributes one bounded verified body, and references require
that verified author context, with at most 6,000 characters per read. The prompt byte
limits and durable call accounting remain unchanged; no new model tool was added.
Altered/forged expansions are refused before provider dispatch/budget reservation.
Compaction may require explicit reinvocation. These bounds do not certify real token
or account-quota savings; SDK transport fixtures are measured separately.

## Diagnostic queries

Native doctor and static quality dispatch no model call and are excluded from later
model context as administrative output. Source inspection and temporary local work
consume no inference tokens. Copying those results into a later model request does
consume that request's context; no subscription quota savings are inferred.

## Profile/documentation administration

Declarative profile validation, template catalogs, reviewed composition, selected
source comparisons, footer/index and incremental memory maintenance make no model
calls. Native administrative output is excluded from subsequent model context.
Documents must contain supplied reviewed facts; these host commands do not generate
prose by inference. Any later model-assisted drafting is counted separately.

## Bootstrap administration

Project/infrastructure plans, exact generator resolution, staged execution/content
inspection, confirmed file copying and local validator receipts dispatch no model
call. Their administrative messages are excluded from later inference context.
SDK/package downloads are separate network activity, not inference accounting.
Model-assisted design or interpretation remains budgeted separately; no account-quota
saving percentage is inferred from these administrative operations.

## Engineering evidence administration

Selected architecture inspection/recording, bug status/reporting and mobile metadata
transitions use local source/receipt checks and canonical renderers. They dispatch no
inference and administrative messages stay outside later model context. Source
interpretation or independent review requested through a configured model is budgeted
separately. Local tool presence and a fixture reviewer do not establish quota savings.

GENERATED BY AIKYA HARNESS
