# Route B validation: executable checks and read-only terminal

Date: November 8, 2026. Branch: `feat/aikya-v8-pi`. Platform: macOS arm64.
Python 3.13.18, Node 26.12.1, npm 11.20.0, pinned Pi 1.5.0.
Stable VERSION stays 7.2.2; private runtime stays 8.0.0-alpha.0.

## Observed runs

| Check | Observed outcome | Scope |
| --- | --- | --- |
| Python full regression | 772 tests in 992.577 seconds, no failures, two skips | Temporary HOME; installed editable checkout; no inherited PYTHONPATH; loopback-capable run |
| Directed RDD suite | 48 tests passed in 5.207 seconds | Candidate/receipt contracts, CLI, reports and real executor |
| Python terminal entry point | Two tests passed | Explicit project/runtime/interpreter, no-shell preview and malformed runtime refusal |
| Final Pi suite | 19 tests passed, no skips | Real SDK/Python bridge, state/session isolation, inference/editor/native-shell boundaries |
| TypeScript | `tsc --noEmit`, exit 0 | Private package source and tests |
| Source quality | 28 source files, zero errors, zero duplicate bodies | One long-function warning for the existing Python CLI dispatcher (157 lines) |
| macOS interactive terminal | Started, served local queries, blocked unsupported actions, exited 0 | Actual PTY through the Python launcher and real Pi InteractiveMode |
| Built wheel outside checkout | Built and installed offline into a separate environment; 48 RDD, two terminal and 19 Pi tests passed again | Isolated Python mode, no editable source import or dependency download |

The full Python run finished before documentation and the final TypeScript editor/
launcher changes. Python production/test source was unchanged during that run.
Final npm tests and typecheck cover the later TypeScript changes. The CI definition
also includes terminal entry-point acceptance; remote jobs have not run.

The final artifact check built `aikya_harness-7.2.2-py3-none-any.whl` without build
isolation or downloads. This is a local development artifact, not a stable release
publication. The RDD rerun against that installed wheel completed in 5.317 seconds;
the Pi rerun used its Python interpreter for all bridge children. No source-tree
PYTHONPATH fallback was needed.

Red tests preceded the report/executor implementation and the terminal boundaries.
Terminal-specific failures reproduced an absent launcher, dangling ignore symlink
replacement, later ignore negation and missing native-command gating before fixes.

## Execution evidence behavior

Tests launch actual Python children and verify frozen approval/session/definition,
fresh reports, timing/hash/count records and receipt admission. Refusal occurs
before side effects when authority or frozen inputs differ. A reused run ID never
spawns a second child. A pending uncertain attempt blocks a new run ID for that
check. Manual receipts cannot satisfy execution-bound checks.

Missing and zero-test reports, timeout, cancellation, keyboard interruption and
output overflow remain nonpassing. A child that changes source cannot attach a
passing receipt to the old candidate. Output privacy checks confirm a private
stdout marker is absent from retained dossier files.

One real `node --test --test-reporter=tap` test and one real `go test -json` test
ran successfully with derived counts of one executed, zero failed and zero skipped.
The Go fixture uses local toolchain/cache and disables proxy/module configuration
discovery; it downloads no test dependency. JUnit/TRX fixtures exercise consistency,
skips/failures, truncation, hostile XML and bounds. They are not native framework
execution for every supported Aikya language.

## Actual terminal smoke

A disposable project under `/private/tmp` was opened through `aikya terminal`
with the explicitly selected checkout runtime and installed Python interpreter.
No personal project or configuration was modified.

- The real Pi UI displayed the Aikya alpha header and read-only status.
- `/aikya-status` returned an unconfigured local project.
- `/aikya-context` retrieved only the requested sample file with source hash and
  bounded-fallback diagnostics; no index refresh or model was used.
- An ordinary implementation request returned the read-only notice.
- `/export should-not-exist.html` and a native shell marker command were blocked;
  neither target file was created.
- `/quit` returned exit 0 and restored terminal modes.
- State remained under `.aikya/pi/`; the generated exclusion protected local
  agent/session paths. The SDK created empty local auth storage. No login ran.
- Missing optional `fd` produced an offline warning and no automatic download.

Separate tests preserve existing ignore bytes, refuse tracked state, dangling/
regular symlinks and invalid UTF-8, and verify that later negations cannot expose
new state. The source repository also excludes `.aikya/pi/`.

## Limits and next acceptance

No provider/model execution, token measurement or account-quota saving is claimed.
The per-instance gate blocks model dispatch and the launcher uses Pi offline mode;
direct trusted host APIs and ordinary approved test processes are not OS-contained.

No native Windows/Linux TUI, process-descendant cleanup, packaged terminal,
short-install, update/migration or native JVM/.NET report production was executed.
Large/native Windows exit statuses need acceptance alongside process cleanup.
The existing 29-extension index matrix is not proof of runner support for every
language. Native CI definitions are planned execution, not observed results.

Independent reviewer admission, review transitions, budgets/authentication,
ODD/SDD parity and memory/HTML integration remain open. An interrupted executor
may leave pending metadata or a private temporary XML report; reconciliation is
manual and no uncertain operation is replayed automatically. Successful checks do
not grant workflow closure, commit, push or deployment authority.

GENERATED BY AIKYA HARNESS
