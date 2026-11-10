# Run the private Pi controlled preview

This is a contributor preview on `feat/aikya-v8-pi`, not the stable one-command
installer. Keep the stable 7.2.2 installation instructions separate. Use Node 22.19.0
or later, an installed Python Aikya package built from the same branch snapshot,
and the reviewed locked dependencies in
`packages/aikya-pi`. Runtime selection is an explicit operator trust decision.

```sh
aikya terminal --runtime-dir /absolute/path/to/packages/aikya-pi --target /absolute/path/to/project
```

The default mode disables model dispatch. Local administrative commands can still
write after a native host confirmation. Sessions, authentication and preferences live
under the selected project's ignored `.aikya/pi/`; do not commit or copy credentials.
No personal Claude/Codex configuration is imported.

The [private managed distribution](pi-managed-terminal.md) additionally builds an
owned self-contained terminal without a development runtime path. Its installed
acceptance is tracked separately; these contributor commands remain supported.

## First project

Use `/aikya-init` for a new project or `/aikya-analyze` for existing source. The interview
asks project kind, documentation language, explicit ODD/SDD, application stacks and
relevant infrastructure choices. Native Android language and iOS UI are selected
explicitly for the platforms involved. Preview paths, scroll through the complete
operation and confirm; Escape cancels. Known managed 7.x profiles use the confirmed migration command below; unknown or
custom profiles are preserved for manual review.

An explicit profile can also be submitted. For example, in a new empty project:

```text
/aikya-init {"profile":{"backend":"python","methodology":"sdd","repository_layout":"singlerepo"},"language":"en"}
/aikya-tokens {"tokens":10000,"calls":20}
/aikya-theme light
/aikya-memory
```

The token/call limits are examples chosen by the operator, not recommended costs.
Changing limits keeps accumulated accounting. The memory command reads status, or
accepts JSON `query`/`max_chars` to search current reviewed notes. Initialization and
approved source writes maintain an enabled local index/HTML without model calls.
An enabled watch policy also observes external edits while Pi is open. Local
heartbeats maintain the lease during idle time; closing the last session stops the
observer. Neither path calls a model.

## Explicit controlled inference

Inspect `/aikya-models` for the pinned local catalog, `/aikya-models PROVIDER_ID` for
one provider, or JSON `provider`/`offset` for subsequent pages of 20. These commands
perform no provider refresh or model call. Their administrative output is excluded
from subsequent model context. Quit, then select a catalog provider/model explicitly:

```sh
aikya terminal --runtime-dir /absolute/path/to/packages/aikya-pi --target /absolute/path/to/project --resume --provider PROVIDER_ID --model MODEL_ID
```

Replace both IDs with the chosen catalog values. In the interactive terminal, native
`/login` and `/logout` manage supported Pi authentication. Do not paste credentials
into prompts. Authentication support and quota adapters remain experimental until
validated against the selected real provider in the designated test environment.

`/aikya-phase explore|plan|implement|validate|security|review` selects usage attribution
for subsequent calls; it does not grant workflow permissions. Native onboarding/bootstrap and the selected-task cycle also select phases. Other
commands may still need explicit attribution; selecting a phase never proves its execution. `/aikya-tokens` shows local use separately
from available provider headers. Unavailable quota is not zero. `/compact` is explicit,
uses the budgeted model and can consume tokens. A pending/unknown usage record requires
trusted reconciliation; restarting does not erase it.

The model's source-write proposal requires host confirmation of the actual replacement.
Use the scroll controls to inspect long content; the approval controls stay visible.
The current bound is 12,000 UTF-8 bytes/8,000 Pi characters per complete replacement,
with an existing parent folder. Shell execution and worktrees are not available tools.

The same write tool also accepts `{change_id,operations}` for a current native
author-owned frozen change. A batch selects up to 20 unique in-scope files; each
operation supplies `content`, exact original-text `edits` (`old`/`new`), or explicit
`delete:true`. Anchors must match once in the original and cannot overlap, including
self-overlapping matches. The exact reviewed changes and complete file hashes bind
the grant; dialog mutation, source/task/candidate/locale drift and replay refuse it.
The canonical intent stays within 12,000 JSON bytes and the existing 16 KB wire bound.
Text files may be up to 1 MB, with the same physical-line policy. An exact deletion
must fit its complete original content in the reviewed packet; it is not truncated.
Case-aliased destinations and file/parent collisions are rejected before writing.

A local host operator can propose the same batch without model dispatch:

```text
/aikya-implement {"action":"edit","change_id":"local-fix","operations":[{"path":"src/value.py","edits":[{"old":"VALUE = 1","new":"VALUE = 2"}]}]}
/aikya-verify {"action":"recover-batch"}
```

Select the task and freeze the native change first. This `edit` action uses the
existing ODD/SDD binding; it does not select a task or approve methodology.
The batch previews exact edits/creation/deletion and requires native confirmation.
New files are created exclusively, parents are checked, source is rechecked before
each effect and actual bytes are read back. Reports use the owned validation dossier,
footer/index and local memory. They report checks not run and authorize no delivery.

Multiple files are not one atomic filesystem transaction. A concurrent edit or crash
may leave a partial batch; preserve and inspect it. Pending/orphan reservations block
new batch and single-file grants. Recovery requires a fresh confirmation and only
finishes bookkeeping when every signed reserved effect and surrounding source still
match. It never repeats source writes or renews an expired grant; partial/foreign/
changed effects stay manual. A larger patch does not expand the 6,000-byte complete
reviewer packet: split or escalate review when the complete scope cannot fit.

## SDD transitions

The native stage commands accept explicit JSON using the canonical engine's field
names. Templates and state remain under `aikya/docs/specs/<project-type>/SPEC-NNN/`.
No stage automatically approves the next one.

| Command | Explicit input |
| --- | --- |
| `/aikya-specify` | `{"input_data": <specification object>}` |
| `/aikya-clarify` | `{"ident":"SPEC-001","answers":{"answers":{<question>:<answer>}}}` |
| `/aikya-plan` | `{"ident":"SPEC-001","raw": <design/decisions/risks/testing object>}` |
| `/aikya-tasks` | `{"ident":"SPEC-001","raw":{"tasks":[<canonical task objects>]}}` |
| `/aikya-approve` | `{"ident":"SPEC-001","stage":"spec|plan|tasks","actor":"project-owner"}` |
| `/aikya-sdd-status` | `SPEC-001` |
| `/aikya-implement` | `{"spec_id":"SPEC-001","task_id":"TASK-001","files":["src/example.py"]}` |

`/aikya-implement` binds the ready task/scope to this session; it is not an automatic
end-to-end implementation loop. All three SDD stages must already be approved. New
source state or scope requires review and a new binding where appropriate.

## Adopt or restore a managed legacy profile

In the target project, submit the existing methodology explicitly:

```text
/aikya-migrate {"methodology":"odd"}
```

Use `sdd` for an existing SDD profile. This operation preserves the methodology;
changing methodology is a separate workflow. Review metadata hashes, destinations,
backup location and audit report, then confirm. It preserves existing source, document
bodies, notes/index policy, client settings and installed skills. Custom/unknown
profiles, runtime selections or backup folders are refused rather than adopted.

The result supplies a migration ID. To restore the original metadata:

```text
/aikya-migrate {"rollback":"MIGRATION_ID"}
```

Replace the ID with the returned 32-character value. Rollback previews the scope,
requires another confirmation, preserves changed/custom artifacts and exits Pi after
restoration. Original bytes and signed records stay local in `.aikya/pi/migrations/`;
localized audit Markdown stays under `aikya/docs/operations/` with the footer/index.
This profile migration does not replace global launchers, uninstall client hooks or
provide the final v8 installer.

An interrupted onboarding can be retried only from a newly reviewed preview. Existing
managed documents and source are preserved. SDK integrations without the interactive
runtime must await the session result's `close()` helper to release memory ownership.

## Evidence and acceptance

Use `/aikya-tests` to freeze a bounded change and explicit executable definitions.
The first definition is the TDD regression check; `tdd_paths` identifies unchanged
regression-test files. Code scopes require TDD; documentation-only scopes require
an explicit `not_applicable` reason instead. For example, replace the Python path
with the trusted installed interpreter and use actual project files:

```text
/aikya-tests {"action":"snapshot","change_id":"local-fix","objective":"Return the expected value","acceptance":["The regression test verifies the expected value"],"scope":["src/value.py","tests/test_value.py"],"tdd_paths":["tests/test_value.py"],"definitions":[{"name":"tests","argv":["/absolute/path/to/python","-I","-B","tests/test_value.py"],"cwd":".","report_format":"tap","timeout_seconds":30,"max_output_bytes":65536}]}
/aikya-tests {"action":"run","change_id":"local-fix","check":"tests"}
/aikya-verify {"action":"status","change_id":"local-fix"}
```

The example test must actually produce TAP 13. JUnit, TRX and Go JSON use their
corresponding report contracts. There is no automatic runner detection or shell.
Review the frozen executable/environment, actual scope, intent and paths, then
confirm. Test processes have normal host privileges. They may write files or access
the network; this control is not operating-system containment.

The first observed failing regression provides Red. After an approved implementation
change, the same `run` command proposes a fresh in-scope snapshot and check together,
keeping the ordered definitions and TDD paths. It cannot hide changes outside the
scope or silently change the execution environment. `/aikya-tests` with `action:refresh`
is also available explicitly. Escape during execution requests cancellation and
waits for the owned process result. Cancelled, missing, skipped, zero or uncertain
results never count as success. Inspect an uncertain run before considering another
operation; it is never replayed automatically.

The controlled author can propose `aikya_check` using only the frozen change/check
identifiers. Every execution still requires native confirmation. A headless SDK
consumer receives `needs_host_action`; a model argument cannot approve execution.
The independent reviewer has no write or check tool.

After current positive checks and unchanged-test Red/Green evidence:

```text
/aikya-verify {"action":"review","change_id":"local-fix"}
/aikya-verify {"action":"recover","change_id":"local-fix","run_id":"RETURNED_RUN_ID"}
```

Review needs explicit provider/model launch, configured authentication and available
project budget. Confirmation identifies the exact candidate/model/budget. A separate
read-only session receives bounded complete source, intent and verified counts; an
admitted current acceptance can grant technical closure, while delivery remains
unauthorized. Scopes larger than 6,000 source bytes/20 paths require splitting or
escalation. Recovery only attaches a known private host-observed result, with a fresh
preview/confirmation, and never starts a process. Snapshot and admitted-review Markdown
use the project documentation language, footer and index.

### Validators, refactors and living documents

For non-test commands, select `report_format: "process"` in the frozen definition.
The executor retains actual exit, timing and output hashes, with `counts: null`.
It never parses their output as passing tests. Explicit `change_kind` values are
`behavior`, `documentation`, `configuration`, `infrastructure` and `refactor`.
Nonbehavior classifications require `not_applicable` and a compatible file scope:
documentation is Markdown/text; configuration uses structured configuration files;
infrastructure also admits Terraform/HCL. A behavior source file cannot be relabeled
as documentation to avoid TDD. Classification does not prove semantic equivalence.

Refactors require an explicit reason and `baseline_paths` naming present test files.
The first definition must be a test runner. Freeze and execute a positive baseline,
then refactor, refresh and run current checks. Identical tests and an executed positive
ancestor are required; missing/failed/changed-test baselines remain `baseline_required`.
Behavior changes still require `tdd_paths` and an observed failing test ancestor.
Omitting classification preserves the previous policy format and TDD rules.

Confirmed canonical living documents may change between Red and final review. Only
completed signed same-author operations with exact before/after hashes and the same
Git base can extend this iteration. New snapshots require fresh checks and review.
The reviewer receives the changed pages, including earlier pages in the lineage, in
the shared 6,000-byte packet; oversized evidence requires escalation. Manual edits,
unobserved gaps and ODD/SDD control pages cannot use this documentary allowance.

```text
/aikya-docs {"action":"recover"}
```

Recovery previews the exact pending effects and requires native confirmation. It
finalizes ownership, index and local memory only when every reserved effect matches
and surrounding source/profile/language remain current. It never repeats a document
write. Partial, altered, legacy or unknown effects remain pending for manual review.
The same action is available through `/aikya-docs-sync`. A headless caller cannot
approve it. No recovery or documentary command invokes a model.

Native write and generation previews enforce the same 1,000 physical source-line
policy as CI. Existing reviewed size exceptions remain bound to exact bytes and are
rechecked before effects; generated Markdown ends with exactly one Aikya footer.

Author and reviewer transcripts have explicit local roles. `--resume` chooses an
author conversation, ignoring a newer known reviewer. Older alpha transcripts without
role records are preserved and refused for automatic resumption; start a fresh session
without `--resume`. This does not erase project memory, budgets or evidence. A new
session cannot inherit another author's frozen change; resume the owner or start a
new explicitly scoped change.

See the [architecture](../architecture/2026-11-08-pi-controlled-runtime.md) and
[current implementation state](../plan/2026-11-07-aikya-v8-implementation-status.es.md).
Full command parity, integrated runtime migration/distribution, real-provider trials and native
Windows/Linux acceptance remain release gates.

## Native ODD feature tasks

`/aikya-feature` is available for configured ODD projects. Substantial work uses the
canonical feature dossier; small/read-only work needs no new feature folder. Supply
explicit facts and tasks, then review paths, input, profile/source revision and language:

```text
/aikya-feature {"action":"create","feature_id":"expected-value","input_data":{"title":"Expected value","objective":"Return the expected value","acceptance":["The value is one"],"facts":{"understood":false,"contained_risk":true,"resumable_from_request_diff":true},"tasks":[{"id":"TASK-001","description":"Return one","acceptance":["AC-01"],"depends_on":[],"files":["src/value.py","tests/test_value.py"],"checks":["tests"]}]}}
/aikya-feature {"action":"status","feature_id":"expected-value"}
/aikya-feature {"action":"bind","feature_id":"expected-value","task_id":"TASK-001"}
```

Status returns at most 20 tasks; JSON `offset` selects a later page. Selection requires
ready unfinished work and confirms its exact files/check names/intent. While active,
a signed selection limits all source-write proposals to those paths and this author.
A changed worklist or new selection revokes prior grants. Each actual source write
still needs its own native confirmation. Dependencies remain in the existing ODD engine.
Native selections are limited to 20 files/10 frozen check names with bounded intent;
legacy descriptive check prose is preserved and needs explicit reviewed reconciliation.

Use the returned task `intent.objective` and `intent.acceptance` exactly when freezing
`/aikya-tests`, with the selected files, matching check names and regression paths.
Run Red, implement the requested change, run Green, then explicitly request independent
review through `/aikya-verify`. No ODD command dispatches that reviewer automatically.

```text
/aikya-feature {"action":"complete","feature_id":"expected-value","task_id":"TASK-001","change_id":"local-fix"}
/aikya-feature {"action":"release"}
/aikya-feature {"action":"reconcile","feature_id":"expected-value","revision":2}
```

Use the actual change ID/revision from this project. Completion requires the selected
session/task, current matching checks and admitted independent acceptance. A signed
reservation prevents replay after uncertain effects; source/report drift refuses
success and preserves evidence. The worklist records acceptance at that transition.
The resulting task metadata changes the full checkout identity and does not approve
later changes or delivery. Release confirms removal of only the known private task
selection; documents and receipts remain. Reconciliation explicitly invalidates stale
outcomes/dependents, with a fresh source/profile/revision preview; custom documents
stay protected. English phases are displayed locally. SDD continues through its
dedicated stage approvals and `/aikya-implement`; this facade cannot replace it.

## Bounded selected-task cycle

Select a canonical ODD task with `/aikya-feature` `bind`, or an approved ready SDD
task with `/aikya-implement`. Freeze its exact objective, acceptance, file scope and
executable check definitions with `/aikya-tests`. Those values must match the selected
task; an arbitrary prompt or selected methodology alone is insufficient. Start the
controlled provider/model session explicitly as above.

```text
/aikya-feature {"action":"run","change_id":"local-fix","limits":{"calls":6,"seconds":300,"corrections":1},"security":{"checks":[],"not_applicable":"No security behavior changes in this bounded constant; independently review this applicability."}}
/aikya-feature {"action":"run-status"}
/aikya-feature {"action":"stop-run"}
/aikya-feature {"action":"resume-run","run_id":"RETURNED_RUN_ID"}
/aikya-feature {"action":"recover-run","run_id":"RETURNED_RUN_ID"}
```

Use the same actions under `/aikya-implement` for the selected SDD task. The empty
security list is an example requiring a reviewed reason, not a default exemption.
For applicable checks use `{"checks":["security-check-name"],"not_applicable":null}`;
those names must already exist in the frozen executable definitions. All selected
checks must finish positively before independent review, which receives this explicit
applicability. A phase label or successful static quality check is not a security scan.

Native confirmation displays the task, intent, scope, model, known budget and exact
limits. Defaults are six project model calls, 300 seconds and at most one correction;
maximums are 20 calls and 600 seconds. The existing project budget may stop inference
earlier. Calls from another session during the run are conservatively counted too.
The original deadline, spend and correction allowance survive restarts/resumption;
model/provider, author, task, source or policy changes cannot silently renew them.
An interrupted running checkpoint must be explicitly stopped before resumption.
A declined final recording can resume directly from this run's signed current review
checkpoint, without another author/reviewer request or check execution. Source,
evidence, security applicability or review drift removes that shortcut; no acceptance
transfers to a changed candidate. Local recording can use an exhausted call allowance
without admitting another model request, but cannot renew the original deadline.

The host selects `explore` while checking context, `plan` for the confirmed intent,
then `implement` for the author. It confirms any required Red/refactor baseline,
confirmed source batches, final `validate` checks, `security` applicability/checks
and a separate `review` session. Phase selection does not attest execution. The host
uses Pi's existing tool loop and public settlement boundary, not another model loop.
The model cannot approve effects, run arbitrary commands, use the legacy single-file
write path inside a task run, modify methodology controls or authorize delivery.

Only current admitted `changes_requested` findings inside the exact source scope
can reserve one corrective continuation. A second rejection, unavailable usage,
failed/declined check, blocked tool, invalid source or deadline stops the cycle.
A current independent acceptance allows a separate confirmation to record the ODD
or SDD task. This records acceptance at that transition; it does not approve an
entire SDD specification, publish code or make later source edits accepted.

Signed checkpoints live under `.aikya/pi/task-runs/`; localized Markdown audit pages
live inside the owned `aikya/docs/validation/<change_id>/task-runs/` dossier. A known
interrupted native completion can be reconciled after confirmation without recording
the task twice; changed, partial or unknown outcomes require manual reconciliation.
`recover-run` never renews model spend or replays source effects. The existing
`recover-batch` action covers source operations separately.

Explicit `/compact` remains budgeted inference and may use two requests for split
turn summaries. Every measured request counts, including reviewer and summary calls.
The next guarded stream receives the bounded task checkpoint rather than the full
memory store. Compaction grants no permissions and never resets accounting. Fresh
sessions do not scan old histories; resume preserves unknown/oversized author
transcripts and never adopts a known reviewer as author.

Complete independent source review still has a shared 6,000-byte bound. Larger
candidates escalate instead of silently truncating evidence. Real-provider quality,
account quota savings and native Windows/Linux acceptance remain separate gates.

## Explicit selected local skills

The native preview supports local project packages selected by the operator. It does
not download recommendations, run dependencies/scripts/hooks, import global client
skills or activate packages automatically. Use an absolute skill directory whose
`SKILL.md` name matches its folder:

```text
/aikya-skills-status
/aikya-skills-plan {"source":"/absolute/path/to/example-skill"}
/aikya-install-skill {"source":"/absolute/path/to/example-skill"}
```

Planning is read-only. Installation previews original instructions, resource hashes,
ignored metadata and exact paths, then requires native confirmation. Source/registry/
comparison drift invalidates approval. Existing custom/unknown assets and interrupted
effects stay preserved without replay. The private original archive is byte-exact;
the normalized Pi entry forces explicit invocation. Installation writes localized audit
Markdown under `aikya/docs/operations/` and comparison only then, preserving prior
registered rows, footer and index. Installed state is not evidence of model invocation.

Restart the controlled author session after installation, preserving the same project
budget. Invoke `/skill:example-skill` explicitly. Automatic repository/global discovery
and prompt listings remain disabled. Source metadata never adds tools or permissions.
The author may use the existing context tool for a verified resource alias such as
`@skill/example-skill/references/guide.md`; append `#6000` for the next character window.
One alias is read at a time, with at most 6,000 characters and a continuation offset.
Only a verified invocation grants this access; independent reviewers cannot load it.
Expanded instructions are checked before actual model dispatch and budget admission.
After compaction drops an invocation, invoke it again to restore reference access.

Limits: 20 installed project skills; 160 examined entries and 80 files/5 MB per source package; 1 MB per file;
8 KB source entry, 6 KB instruction body and explicit single-line metadata. Unreadable
subdirectories are refused; CRLF entries and uppercase Markdown are normalized while
original bytes remain archived. Exact
originals and source hashes remain local. Global scope, direct GitHub downloads,
update/uninstall and skills requiring external execution remain separate native work.
The stable chosen-skill installer is unchanged. No quota-saving amount is inferred.

## Native local diagnostics

```text
/aikya-doctor
/aikya-quality {"paths":["src/value.py","tests/test_value.py"]}
```

Doctor shows the actual running Python/Node/Pi versions, configured profile state,
profile-required command presence and selected provider/model/auth-configuration
status. It reads no credentials, sends no provider request and executes no SDK wrapper
or version command. Unknown/malformed profiles are preserved and marked explicitly.
Android SDK layout is not checked and Docker Compose presence denotes its parent
command only. Versions/framework compatibility/provider connectivity are unverified;
`ready:null` prevents presence being interpreted as acceptance. Use explicitly
approved frozen checks to collect execution evidence where appropriate.

Quality requires 1–20 unique explicit relative source paths, at most 1 MB each/2 MB
total. Private/control/secret paths, links, missing files and unsupported extensions
are refused. It inspects a captured byte snapshot with the existing quality engine
and includes SHA-256/scope identity; later changes require a fresh query. Reviewed
size exceptions remain bound to their exact file hash. Every indexed language has
physical-line coverage; Python and Python stubs additionally use AST syntax, long
functions and exact nontrivial function-body duplication checks. This is not semantic
analysis of other languages, a security scanner, test execution or reviewer approval.
At most 20 findings and three example locations per duplicate are displayed with
full counts/truncation indicated. No project report/index is written. Both admin
outputs are omitted from later model context; explicitly sending them again would
count toward that subsequent model request.

## Declarative profiles and reviewed documentation

```text
/aikya-answers
/aikya-answers {"profile":{"backend":"python","methodology":"odd","mode":"existing","repository_layout":"singlerepo"},"language":"en"}
/aikya-docs
/aikya-docs {"action":"catalog","document":"architecture"}
/aikya-docs {"action":"write","documents":[{"document":"architecture","payload":{"title":"Observed architecture","sections":{"1-purpose-and-scope":"A local Python module."}}}],"sources":["main.py"]}
```

Without arguments, answers reads the explicit bounded `.aikya/answers.json` profile
and binds its exact bytes until apply. Both forms require explicit new/existing and
ODD/SDD choices, reuse portable onboarding and confirm before effects. Established
language is preserved when omitted; select en/es explicitly to establish new policy.
Existing profile changes remain guarded by the migration workflow. No Claude runtime
assets are installed. Oversized declarative inputs/previews require smaller input.

Docs catalogs verified fields for overview, architecture, strategy, design, decision,
case and summary. Use a lowercase `slug` for design/decision/case/summary. Supply
actual reviewed content, up to three documents and 20 explicit source paths. The
review shows full before/after content and source identities; Escape writes nothing.
Sections absent from the update remain intact. Unmarked custom pages and externally
modified native-owned pages are preserved. Dedicated feature/spec/task/control paths
cannot be rewritten here. Summaries require bounded existing non-private evidence
files and retain the canonical supplied-outcomes notice; they do not run checks.

```text
/aikya-docs-sync {"action":"baseline","change_id":"REQ-20261108-abcde123","sources":["main.py"]}
/aikya-docs-sync {"action":"sync","change_id":"REQ-20261108-abcde123","summary":"Describe the observed change.","documents":[{"document":"architecture","payload":{"title":"Observed architecture","sections":{"1-purpose-and-scope":"Describe the current module."}}}]}
```

Choose a new request identifier. Confirm the baseline before the code change, then
sync in the same author session. Only selected-path changes are compared, including
creation/deletion. No changes returns read-only status with no REQ or pages. Sync
records changed hashes, reviewed prose and actual updated pages in a localized REQ;
it neither discovers every repository change nor certifies test results. Completed
request identities cannot replay after a public record is deleted. Interrupted writes
retain private pending state and require explicit reconciliation before another update.

Finalize reviewed living pages before freezing the final check/review candidate.
Page edits change the full candidate identity and can invalidate earlier acceptance;
documentation sync does not transfer or renew an admitted review.

Bounds: 8 KB documentation input, 12 KB per rendered page, 50 KB review packet;
source/evidence reads are at most 1 MB per file/2 MB total per selection. Native page
ownership is limited to 200 entries before archival. The existing full candidate
snapshot bounds still apply. These commands dispatch no inference, preserve source
code and do not approve ODD/SDD transitions or delivery. Admin output is omitted from
later model context; intentionally sending it to a model counts as that request.

## Native project, infrastructure and staged generators

Use the configured profile. Planning runs locally without a model call or application
writes. A project record requires explicit modules, paths, observable criteria and
named checks; recording the plan does not implement the application:

```text
/aikya-project {"action":"plan","slug":"api-boundary","objective":"Expose the selected API","modules":[{"name":"api","path":"src/api","purpose":"Public API boundary"}],"files":["src/api/value.py"],"acceptance":["Returns the expected value"],"checks":["tests"]}
```

Repeat the same JSON with `action:record` to review a localized document under
`aikya/docs/plan/project-api-boundary.md`. Existing owner documents remain intact.

For a configured infrastructure/DevOps project:

```text
/aikya-infra
/aikya-infra {"action":"generate","paths":["infra/terraform/versions.tf","aikya/docs/infrastructure/bootstrap.md"]}
/aikya-infra {"action":"validate","validator":"terraform-fmt"}
```

Select only artifacts actually returned by the plan for this profile. Generation
preserves existing files. Guidance stays under Aikya docs. Validators are the shared
canonical `terraform-fmt`, `opentofu-fmt`, `ansible-syntax`, `compose-config`,
`helm-lint`, `helm-template` and `kustomize-build` recipes. Missing artifacts/tools
return `not_configured`; multiple charts require selecting one in the profile.
Each execution confirms executable/environment/source, waits for cancellation and
records a process receipt under `aikya/docs/operations/`, with `counts:null` and
tests not run. It cannot authorize cloud apply/destroy/deploy or technical delivery.
Tools/configuration may access referenced files, SDK caches or plugins: no OS
containment or complete dependency compatibility is claimed.

Scaffolding is limited to new development profiles. The plan reuses the actual
catalog; manual-only stacks and existing projects cannot silently execute:

```text
/aikya-scaffold
/aikya-scaffold {"action":"resolve","generator":"generator-1","version":"EXACT_SEMVER"}
/aikya-scaffold {"action":"prepare","run_id":"RETURNED_RUN_ID"}
/aikya-scaffold {"action":"inspect","run_id":"RETURNED_RUN_ID","path":"ACTUAL_STAGED_PATH","offset":0,"max_chars":1500}
/aikya-scaffold {"action":"copy","run_id":"RETURNED_RUN_ID","paths":["ACTUAL_STAGED_PATH"]}
/aikya-scaffold {"action":"status","run_id":"RETURNED_RUN_ID"}
```

Replace example values with the actual selected recipe, exact version and returned
run/path. Local .NET/Flutter recipes omit `version`; their executable bytes and
selected environment are bound, while SDK compatibility stays unverified. Registry
resolution requires confirmation before downloading metadata/archive from npm's
HTTPS registry. It verifies package/version/SHA-512 before storing the archive.
Another confirmation executes the known recipe in private project staging; npm uses
the verified archive, not `@latest`. Generator/package-manager code may access network
and caches. Escape while preparing waits for the owned process result. No project
helper is imported and the model receives no shell tool.

Only successfully prepared, current, unchanged staged output can be copied after a
separate confirmation. Inspect truncated text in windows before copying. Existing
files remain preserved; no `.gitignore` merging is implied. Binary content is
identified by size/hash rather than rendered as text. The manifest is bounded to
100 files, 1 MB each and 5 MB total; source copies still obey the existing ODD/SDD
selection, including its 20-path bound. Split an oversized project instead of
silently widening permissions. Generated README files keep one footer; Aikya records
stay under `aikya/docs/`.

Failed, empty, linked, changed, cancelled or uncertain results never become a
successful copy. Private signed runs stay under `.aikya/pi/scaffold/`. Generation
reserves `.aikya/pi/generation/pending.json` before effects; validator observations
use `.aikya/pi/infra-validation/`. Preserve interrupted state and inspect/reconcile
it explicitly; no automated replay/recovery is provided in this alpha. Official SDK
and native platform acceptance remains separate from disposable process fixtures.
These administrative commands use no inference and their output is omitted from
subsequent model context.

## Native architecture, bug and mobile workflows

Architecture inspection is local and read-only. Recording requires supplied
interpretations anchored to exact current source lines, with file SHA-256:

```text
/aikya-arc-review {"action":"inspect","paths":["service.py"],"query":"Service","max_chars":1000}
/aikya-arc-review {"action":"record","title":"Selected architecture","paths":["service.py"],"findings":[{"path":"service.py","line":1,"end_line":1,"quote":"class Service:","kind":"observation","severity":"info","message":"A class is declared."}]}
```

Replace the example with actual source. Each excerpt covers at most 20 lines;
up to 20 interpretations use `observation`, `hypothesis` or `recommendation`, and
`info`, `warning` or `critical`. Only the excerpt is verified; supplied interpretations
are not independently proven runtime behavior. Native recording reviews the actual
canonical architecture section update, preserves other sections/custom pages and
uses existing source/locale/ownership/uncertain-operation protection. No source
change, test run, automatic model review or delivery approval is performed.

```text
/aikya-bugfix
/aikya-bugfix {"action":"status","change_id":"RETURNED_CHANGE_ID"}
/aikya-bugfix {"action":"record","payload":{"id":"BUG-001","title":"Observed issue","sections":{"summary":"Observed issue","environment":"Local project","steps-to-reproduce":"Run the selected regression","expected-result":"Expected value","actual-result":"Observed value"}},"sources":["service.py"]}
```

Without native evidence, the report remains `not_reproduced`. Add `change_id` to a
record only when its summary/expected result exactly match the frozen objective/
acceptance shown by status and its sources belong to that scope. The native evidence
section is computed; a supplied `evidence` assertion is refused. Actual executed
failed regression counts establish `reproduced`; valid unchanged-test Red/Green
and current positive checks establish `checks_passed`. Only current independent
admission can produce `reviewed`/`fixed:true`; stale source loses that status.
Even then, delivery stays unauthorized. Use the existing frozen check/reviewer
commands for execution; this command does not apply a fix or run a model implicitly.

Recording confirms an append to `aikya/docs/bugs/bugs.md` using the canonical template.
Unique BUG IDs preserve earlier entries, native ownership protects later custom
edits, and the page has one footer/index. The current full-register bound is 12 KB;
reviewed archival is required before exceeding it. A record is an observation
snapshot, not a transferable approval. Living-page writes change full candidate
identity: finalize intended pages before final verification/review, and preserve
uncertain operations for explicit reconciliation.

Mobile planning requires explicit platforms inside the recorded development profile:

```text
/aikya-mobile-feature {"action":"plan","platforms":["android"],"files":["lib/screen.dart"]}
/aikya-mobile-feature {"action":"create","platforms":["android"],"feature_id":"mobile-screen","input_data":{"title":"Selected screen","objective":"Render the selected screen","acceptance":["The screen renders"],"facts":{"understood":false,"contained_risk":true,"resumable_from_request_diff":true},"tasks":[{"id":"TASK-001","description":"Render screen","acceptance":["AC-01"],"depends_on":[],"files":["lib/screen.dart"],"checks":["tests"]}]}}
/aikya-mobile-feature {"action":"bind","platforms":["android"],"feature_id":"mobile-screen","task_id":"TASK-001"}
```

ODD creation/binding/status/completion reuses the canonical feature engine, including
its small-work classification and independent evidence requirements. Substantial
features store optional typed `mobile_scope` context and render the existing mobile
template. A different platform/framework cannot silently relabel the feature.
Older generic features remain available through `/aikya-feature`; the mobile facade
does not adopt unknown platform context automatically.

After explicit SDD stage approvals, bind the existing task instead:

```text
/aikya-mobile-feature {"action":"bind","platforms":["android"],"spec_id":"SPEC-001","task_id":"TASK-001","files":["lib/screen.dart"]}
```

SDD selection signs the reviewed mobile context alongside the existing task/file
scope. A newly confirmed platform selection invalidates earlier grants. Opposite
platform directories cannot be included silently. Source writes/tests/review retain
their existing confirmations; selecting task metadata does not execute source.

Tool presence is read without invoking SDK wrappers. Android SDK presence uses the
existing local directory check; iOS tools on unsupported hosts are marked explicitly.
Version/framework compatibility, builds, tests and simulator/device execution remain
separate. Missing tools produce `not_configured` planning, and even found commands
retain unverified acceptance. ODD task recording does not certify a mobile build or
simulator run. Actual Flutter/React Native/Android/iOS acceptance remains in the native
matrix. All these administrative commands use no model call and are excluded from
subsequent inference context.

## Explicit native skill versions

The private Pi preview keeps the same three canonical commands. The default is
`scope:project`; `scope:global` is an inert library under the managed application
root, not automatic discovery, a second command copy or global project memory.
No external skill is recommended or installed by default.

```text
/aikya-skills-status {"scope":"global"}
/aikya-skills-plan {"scope":"global","source":"/absolute/path/example-skill"}
/aikya-install-skill {"scope":"global","source":"/absolute/path/example-skill"}
/aikya-install-skill {"action":"select","source":{"kind":"global","name":"example-skill","source_hash":"<reported SHA-256>"}}
/aikya-install-skill {"action":"update","source":"/absolute/path/example-skill"}
/aikya-install-skill {"action":"rollback","name":"example-skill","source_hash":"<retained SHA-256>"}
/aikya-install-skill {"action":"recover"}
```

The hash placeholders must be replaced with observed complete identities. Add
`scope:global` to update/rollback/recover to change the library instead of a project.
A global update leaves every selected project copy unchanged. A project change
requires restarting the controlled session and invoking `/skill:<name>` explicitly;
old expansions are rejected before another provider call even while the old cache
is retained for rollback. Independent reviewers receive no author skills.

For a public GitHub source, resolve metadata, capture pinned data, inspect it and
install it as separate actions. Use `/aikya-skills-plan` with the same input to
review an action without effects. Native confirmation is required for network or
installation effects; a JSON `approved` field is not accepted as consent.

```text
/aikya-install-skill {"action":"resolve","repo":"https://github.com/OWNER/REPOSITORY","ref":"heads/main"}
/aikya-install-skill {"action":"fetch","repo":"https://github.com/OWNER/REPOSITORY","path":"skills/example-skill","commit":"<observed 40-character commit>","name":"example-skill"}
/aikya-skills-plan {"source":{"kind":"captured","project":"/absolute/current/project","source_hash":"<reported SHA-256>","name":"example-skill"}}
/aikya-install-skill {"source":{"kind":"captured","project":"/absolute/current/project","source_hash":"<reported SHA-256>","name":"example-skill"}}
```

`path:"."` explicitly selects a skill at the repository root. A confirmed capture
can subsequently be installed globally by supplying its returned descriptor with
`scope:global`; it remains bound to the current project during native administration.
Public HTTPS uses no client credentials, Git checkout, scripts, hooks or dependency
installation. Ref resolution does not pin future branch contents automatically:
subsequent capture requires the returned complete commit. Network/rate-limit failure
is explicit; a selected local directory remains available as a separate source.

Packages retain exact source bytes in `original.zip` plus signed prepared-file and
origin manifests. Native limits are 80 regular files, 1 MB per file, 5 MB total,
8 KB `SKILL.md`, 6 KB instruction body, 20 selected names and 10 retained versions
per changed name. Registry/review/context byte limits may refuse a package earlier.
Portable paths reject aliases, device names, links, submodules and secrets. A bounded
scalar metadata subset supports wrapped/folded descriptions; it does not expand YAML
aliases or tags. Imported tool/hook fields remain ignored data, not runtime capabilities.
Installing readable data never proves skill behavior or external tool compatibility.

Selections and their comparison/audit pages live in the project. The global library
has signed administrative records and no project memory. Original/custom files and
uncertain package effects are preserved. `recover` can promote a complete package
whose intended registry and document bytes were sealed before interruption, without
redownloading or copying it. Partial or unknown captures require manual review and
remain blocked; no cleanup, adoption or source-effect replay is automatic. Existing
legacy selections without a native package manifest remain readable, but require
reviewed migration before update/rollback. Skill uninstall remains a separate plan.

GENERATED BY AIKYA HARNESS
