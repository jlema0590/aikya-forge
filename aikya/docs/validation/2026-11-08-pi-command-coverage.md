# Pi command coverage and remaining parity work

Scope: private 8.0.0-alpha.0 branch, November 9. The canonical registry still contains
28 engineering commands. All 28 have a native Pi adapter in this snapshot; this is not
full parity with the stable Claude workflow. A generic model prompt is not counted
as implementing a command. The existing stable adapters remain available separately.

| Canonical command | Native Pi state | Scope or remaining work |
| --- | --- | --- |
| `/aikya-init` | Implemented, experimental | Explicit profile/interview, ODD/SDD, bounded preview and confirmed canonical documentation; no app scaffold. |
| `/aikya-analyze` | Implemented, experimental | Bounded existing-source discovery and explicit profile; managed legacy profiles use the separate migration command; custom profiles are preserved. |
| `/aikya-answers` | Implemented, limited | Confirm explicit new/existing ODD/SDD profile JSON or the bounded project answers file, preserving its hash, established methodology and project sources. Uses portable onboarding without Claude assets; broader profile changes use migration. |
| `/aikya-doctor` | Implemented, limited | Read actual running Python/Node/Pi versions, profile status, tool presence and selected provider/auth configuration without inference or SDK execution. Versions/framework compatibility/connectivity remain unverified; no readiness assertion. |
| `/aikya-project` | Implemented, limited | Explicit module/intent/scope/check planning and confirmed localized record; no automatic application implementation. |
| `/aikya-infra` | Implemented, limited | Captured-input canonical planning, confirmed named no-overwrite artifacts and shared local validator processes with cancellation; no fabricated tests or cloud execution. Official SDK/native acceptance remains pending. |
| `/aikya-scaffold` | Implemented, limited | Confirm exact version/archive resolution, execute a known recipe in private staging, inspect and separately confirm manifest copying. Bind executable/environment/source/task scope; preserve uncertain runs. Existing/manual stacks do not execute; official generators/platform acceptance remains pending. |
| `/aikya-feature` | Implemented, limited | ODD explicit create/status/bind/complete/reconcile/release over the canonical engine; completion requires matching task intent, scope, checks and current independent acceptance. Confirmed bounded run/status/stop/resume and known-completion recovery use the existing Pi loop, current checks, explicit security applicability, independent review and one evidence-bound correction; full live-provider/platform acceptance remains open. |
| `/aikya-bugfix` | Implemented, limited | Native regression/lineage status, supplied canonical reports, append-safe unique IDs and signed document ownership. Source changes/tests/reviewer remain separate guarded operations; no automatic fix. |
| `/aikya-arc-review` | Implemented, limited | Bounded selected context and confirmed canonical architecture findings anchored to exact source excerpts/hashes. Interpretations remain supplied static observations; no implicit model/runtime review. |
| `/aikya-mobile-feature` | Implemented, limited | Explicit platform/path planning and canonical ODD/approved SDD selection with typed mobile context. SDK presence does not execute wrappers or establish build/simulator/device acceptance; native matrix remains open. |
| `/aikya-skills-status` | Implemented, limited | Read signed current local project entries without inference; installation is not observed execution. |
| `/aikya-skills-plan` | Implemented, limited | Inspect an explicitly selected local package, bounded content/resources/hashes and destinations without installation; no recommendations or downloads. |
| `/aikya-quality` | Implemented, limited | Reuse static maintainability over up to 20 selected current-byte snapshots, bounded findings and reviewed size exceptions. Python AST plus physical lines; other indexed languages use physical lines. No security scanner, tests or RDD admission. |
| `/aikya-docs` | Implemented, limited | Inspect verified template fields or confirm up to three reviewed living documents from bounded explicit sources. Preserve sections/custom data, bind signed ownership and locale, update footer/index/memory; no source execution or workflow approvals. |
| `/aikya-tests` | Implemented, experimental | Explicit snapshot/refresh/run/status with frozen intent, scope and check definitions, native confirmation/cancellation and executed TDD evidence. |
| `/aikya-docs-sync` | Implemented, limited | Confirm selected-source baseline, then synchronize reviewed pages and a localized REQ after observed selected-path changes. No changes creates no documents; source/locale/ownership drift and uncertain attempts block without replay. Requires same author session; no automatic prose generation or test certification. |
| `/aikya-verify` | Implemented, limited | Current status, known host-observation recovery without replay, and a separately confirmed independent budgeted reviewer; no delivery authorization. |
| `/aikya-models` | Implemented, limited | Read the pinned local catalog in pages of 20, without provider refresh or credential disclosure; selection stays explicit at startup. |
| `/aikya-tokens` | Implemented, experimental | Durable project limits/accounting and observed quota headers; live provider acceptance pending. |
| `/aikya-install-skill` | Implemented, limited | Confirm local project package installation, exact original archive and signed immutable data; explicit author invocation after restart. Global/GitHub/update/uninstall and external tool compatibility remain pending. |
| `/aikya-specify` | Implemented, experimental | Confirm explicit canonical specification JSON. |
| `/aikya-clarify` | Implemented, experimental | Canonical question/answer transition, preserving approval order. |
| `/aikya-plan` | Implemented, experimental | Canonical SDD design/testing plan transition; no automatic approval. |
| `/aikya-tasks` | Implemented, experimental | Canonical task/dependency/requirement coverage validation. |
| `/aikya-implement` | Implemented, limited | Bind a ready approved SDD task/session and explicit paths; confirmed native source batches and the same bounded selected-task run/status/stop/resume/recovery. Recording a current independently accepted task does not approve the whole specification or delivery. |
| `/aikya-sdd-status` | Implemented, experimental | Read canonical specification status by ID without a model call. |
| `/aikya-memory` | Implemented, limited | Current reviewed-note status/search; local index/HTML maintenance runs after approved onboarding/writes. |

Additional Pi host commands are `/aikya-status`, `/aikya-context`, `/aikya-theme`,
`/aikya-phase`, `/aikya-approve` and `/aikya-migrate`. `/aikya-approve` confirms an SDD stage explicitly; it
is not a PR approval or delivery authorization. Status, context, theme, phase and migration operate locally
without inference. Migration requires native confirmation and guarded local backups. Changing phase changes attribution, not permissions.

The SDK/provider integration tests use actual Pi sessions and Python child services
with fixture external transports. They establish routing, accounting and host
boundaries, not model quality, subscription compatibility or complete workflow
acceptance. The Python onboarding matrix spans development/infrastructure/DevOps,
ODD/SDD and new/existing projects. Existing language suffix tests establish bounded
retrieval, not successful native compilation/testing for every language.

See the [preview guide](../deployment/pi-controlled-preview.md) and
[remaining plan](../plan/2026-11-08-aikya-v8-pendientes.es.md).

GENERATED BY AIKYA HARNESS
