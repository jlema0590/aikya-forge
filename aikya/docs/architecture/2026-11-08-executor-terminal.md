# Executable RDD checks and the development terminal

Status: experimental route B, November 8, 2026. Stable Aikya remains 7.2.2;
the private Pi package remains 8.0.0-alpha.0. No release is published.

## Frozen checks and execution evidence

The host selects a check definition with exactly these fields:

```json
{
  "name": "tests",
  "argv": ["node", "--test", "--test-reporter=tap", "check.test.cjs"],
  "cwd": ".",
  "report_format": "tap",
  "timeout_seconds": 120,
  "max_output_bytes": 65536
}
```

The definition file belongs to the project and should contain no credentials.
The support CLI can preview, store and execute it:

```sh
aikya review snapshot --root . --id change-1 --session author --file src/service.js --check-definition check.json
aikya review snapshot --root . --id change-1 --session author --file src/service.js --check-definition check.json --approved
aikya review run --root . --id change-1 --session author --check-definition check.json --run-id run-1 --approved
aikya review status --root . --id change-1
```

The preview writes nothing. Storing metadata does not approve test execution;
the run requires its own explicit host approval. These are Python support commands,
not new public slash-command registrations or tools callable by a model.

The candidate policy freezes a binding over project, template argument hash,
working directory, report format, limits, resolved executable bytes and selected
environment hash. The default environment is a bounded platform whitelist rather
than the entire parent environment. Explicit environment additions are trusted host
API inputs and their values are not copied to receipts. Environment hashes can
still reveal equality; they are not a secret vault or a guarantee that dependencies
and external inputs are deterministic.

Execution uses an argument list with no implicit shell and a fresh owned run
directory at `aikya/docs/validation/<change>/checks/<run>/`. A pending record is
written before starting the child. Reusing that identity never launches it again;
another attempt for the same check is blocked while a pending attempt remains.
Reconciliation is manual in this slice; unknown/custom state is preserved.

Timeout, cancellation and output limits stop capture and prevent passing evidence.
The executor records timestamps, monotonic duration, exit status, output byte
counts/hashes, report hash and derived counters in `execution.json`. Receipts bind
that metadata to the frozen candidate/session/check. Standard output and error are
not copied to durable logs. JUnit/TRX report files are temporary owned artifacts,
normally deleted after parsing. A process crash may leave them inside the dossier;
do not assume crash cleanup or redaction of arbitrary child-written files.

JUnit/TRX use the fresh report file supplied through `{report}` or
`AIKYA_TEST_REPORT`. TAP and Go JSON use captured stdout. Adapters bound report
bytes/case counts, reject inconsistent identities/counters and require complete
streams. Missing reports, zero executed tests and any skips cannot pass. Definition
or candidate drift also prevents passing receipts. An orphaned result after source
changes remains evidence for reconciliation rather than being attached to new code.

The host executor and test runner are trusted. An approved process has ordinary
host privileges and can write files or use the network. This is not an OS sandbox,
a remote attestation or proof that a test itself is correct. POSIX termination
targets the process group; Windows descendant cleanup remains best effort and
requires native acceptance, including exit-status handling. Source freshness and
hashes detect changes without making the filesystem immutable.

`record_process` remains a legacy trusted-host observation API only for unbound
checks. It cannot satisfy an execution-bound policy. `can_close` and
`delivery_authorized` remain false even after successful checks; independent review,
review-result admission and workflow consent remain open RDD work.

## Explicit read-only terminal

Contributors install the trusted Python checkout in a selected interpreter and
use `npm ci --ignore-scripts` in the private package. Then:

```sh
aikya terminal --runtime-dir /absolute/path/to/checkout/packages/aikya-pi --target /absolute/path/to/project
```

`--print-command` previews the argument list and `--resume` selects an owned local
conversation. Runtime selection is explicit operator trust; matching the alpha
manifest is not a signature. Node 22.19.0 or later and a real TTY are required.
Noninteractive refusal and help do not initialize project state.

Startup verifies the installed Python bridge before creating state. It preserves
existing ignore bytes while appending a final `.aikya/pi/` exclusion when needed,
rejects linked/invalid ignore files and refuses already tracked Pi state. It checks
effective Git rules before initializing the local agent directory. No Git repository
is created. Keep this exclusion when later initializing version control.

Before importing the SDK, the launcher sets project-local `PI_CODING_AGENT_DIR`
and `PI_OFFLINE=1`. Native catalog/version/package checks, install telemetry and
managed tool downloads are suppressed. General tools and discovered resources
remain disabled. A per-instance inference boundary refuses the eight model dispatch
APIs in the pinned Pi 1.5.0 runtime, including compaction and auxiliary calls.

The public custom-editor API limits submitted slash commands to `/aikya-status`,
`/aikya-context` and `/quit`; native mutation commands and shell prefixes are
blocked before the native dispatcher. Copied application shortcuts are restricted
to exit/interrupt. Ordinary prompts are consumed by the Aikya extension without
model execution. The native UI's `user_bash` event is also refused. Direct trusted
SDK APIs are outside this UI boundary and are not a security sandbox.

The UI uses the real Pi interactive mode with an Aikya header. Status/context are
local queries; they do not initialize methodology, refresh memory or execute
workflows. Pi may create empty local auth storage without importing credentials.
Custom-message-only sessions are buffered by Pi and do not establish durable
conversation replay. Full transcript/continuity behavior remains part of later
workflow acceptance.

## Verification and remaining phases

Observed macOS results are recorded in
[validation](../validation/2026-11-08-aikya-v8-executor-terminal.md).
Node TAP and Go test JSON ran natively. XML adapters have format fixtures and
controlled-process acceptance, not native acceptance of every JVM/.NET/Python
framework. Language inventory coverage does not imply compiler/runner coverage.

Model budgets/authentication, write approvals, reviewer admission, ODD/SDD command
parity, memory integration, migration and native installers remain open. Follow
[route B status](../plan/2026-11-07-aikya-v8-implementation-status.es.md).

Adapter reference formats:
[TAP 13](https://testanything.org/tap-version-13-specification.html),
[Go test2json](https://pkg.go.dev/cmd/test2json),
[pytest JUnit output](https://docs.pytest.org/en/stable/how-to/output.html).

GENERATED BY AIKYA HARNESS
