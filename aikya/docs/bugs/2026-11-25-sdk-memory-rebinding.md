# Rebinding the SDK UI briefly released its active memory session

## Observed failure

PR 12 [run 45569948452](https://github.com/jlema0590/aikya-forge/actions/runs/45569948452),
Windows Node 22 job 139053914050, passed 129 of 130 SDK tests. The ODD/SDD
completion test failed during fixture removal with "The fixture observer did
not stop after its final lease closed". The reported error came from teardown;
that error could mask an earlier task assertion. The hosted log did not retain
the observer state or lease count. GitHub cleaned
up an orphan Python process at job end. The mandatory aggregate correctly failed.

PR 11 still references the previous develop commit and therefore has neither the
publication-policy correction nor this follow-up. Its genuine provider-readiness
failure must not be bypassed with invented acceptance evidence.

## Reproduced lifecycle defect

The pinned Pi SDK emits `session_start` on every `bindExtensions` call, including
binding a UI to an existing controlled session. Aikya unconditionally stopped
its current memory owner before starting another owner for the same session.
The real SDK regression sampled the actual session registry during rebinding and
observed an empty registry. That incorrectly invites the observer to retire even
though the session remains active. The regression failed before the correction.

Same-session starts now renew the existing owner. Explicit shutdown still stops
renewal and releases its own session. Other sessions retain their ownership.
No model calls, larger budgets, longer deadlines or unconditional test retries
were introduced. The Windows workflow repeats both task completion and binding
regressions alongside the existing resumption case.

The reproduced registry gap is a defect on the failing path; its relationship to
the exact hosted observer state still requires fresh Windows execution. Fixture
timeouts now retain only bounded, whitelisted state, PID and active-session count
to diagnose any remaining failure without exposing paths, session IDs or source.

## Fresh Windows stress evidence

Run 45587069011 on 0a48dfd passed the full SDK suite on both Windows Node versions.
The additional Node 22 repetition then exposed a different result: the task
stopped with `needs_host_action` instead of `recorded`. Cleanup did not mask this
failure. This shows that fixing the reproduced lease gap is not sufficient to
claim the complete Windows flow is stable.

Before another runtime change, the fixture now prints bounded task phase and
actual check execution metadata on failure, including outcome, duration, exit
code and test counts. It reads no authority keys, command arguments, source or
session identifiers. It does not approve or replay checks. This evidence is
needed to distinguish a check timeout, refusal, changed candidate or report error;
the previous failure message did not identify which occurred.

## Isolate the binding contract from first publication

Run 45589860422 passed the Windows Node 22 task repetitions. Node 26 instead
failed the newly added binding fixture's cleanup with saved state `Updating`
and zero active sessions. The saved PID alone did not establish whether the
worker was still finishing a batch or had exited before saving its final state.

The binding test now waits for an established initial publication using its
existing twelve-second readiness bound before sampling rebinding. This tests
continuous ownership rather than adding a shutdown-during-startup performance
requirement. The ten-second shutdown bound is unchanged. Temporarily removing
same-session renewal still caused the registry-gap assertion to fail; restoring
it passed. Cleanup diagnostics now also query process existence without sending
a termination signal and retain bounded heartbeat age, to distinguish remaining
failure categories. The separate earlier task stop still needs stress evidence.

## Coordinate session readers with durable release

Independent runtime run 45593173592 on 464e348 passed the Windows Node 22
full suite, then failed a declined-record repetition during cleanup. Unlike the
earlier zero-session state, its bounded diagnostic showed `Up to date`, a live
observer, a recent heartbeat and one retained session. Waiting longer would
not explain or repair that retained ownership.

Inspection found that session writers used the launcher lock while the observer's
`active_sessions` reader did not. A concurrent real open lease file can deny
replacement on Windows; lifecycle errors were already treated as degraded memory
and could leave the old lease. A new regression holds a real lease descriptor
while closing its session. It first failed because the writer ran during that
read. Sharing the existing launcher lock makes it pass and persists an empty
registry after the reader exits. No generic storage retries, lease expiry,
inference or test budgets changed. Fresh Windows stress must still establish
whether this resolves the observed cleanup failure and the separate task stop.

## Preserve publication across transient Windows sharing conflicts

Run 45595368083 on 6c53e69 passed the Node 26 repetitions. The Windows Node 22
full suite instead exposed a dead observer with zero sessions and a stale saved
`Up to date` status in the idle-renewal case. This is a distinct failure from a
retained live lease. The worker's discarded stderr does not identify its exact
exception; the saved state must not be presented as proof of one.

The durable writer had no handling for Windows denying replacement while a
reader holds the destination open. Its prepared-file replacement is now bounded
to 250 ms for Windows error codes 5, 32 and 33. Only the identical fsynced sibling
file is retried: no model request, source operation, approval or task is replayed.
Other filesystem errors remain immediate failures. Persistent denial still raises,
retains the previous destination and removes the temporary file; redirected
symlink destinations are rechecked before each attempt.

Fault tests first failed without this handling and then passed. A separate test
holds an actual Windows read descriptor until it closes; it is explicitly skipped
on other systems and now runs in the runtime and local-memory platform matrices.
The idle-renewal scenario is included in the three Windows stress trials. These
changes address a reproduced sharing-conflict failure mode; their relationship
to every hosted intermittent failure remains subject to fresh acceptance.

GENERATED BY AIKYA FORGE
