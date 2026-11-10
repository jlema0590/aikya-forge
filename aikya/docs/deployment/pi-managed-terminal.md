# Private managed terminal installation

> Forge note (2026-11-10): this inherited guide describes the original v8 preview
> contracts and historical acceptance state. Forge starts independently at 0.1.0;
> use the root README for current source/build instructions. No Forge installer
> release or Pages deployment is implied by these historical examples.

This is a contributor-only v8 distribution under acceptance, not a published stable
release. Stable 7.2.2 and the public installation Pages remain unchanged. The native
builder produces a platform-specific Python/Node/Pi payload and a version-pinned
entry script. The final user does not need a checkout, Python, Node or npm. Installation and
unversioned-project startup do not require Git; existing Git working trees require
Git for tracked-state and effective-ignore verification.
The POSIX bootstrap uses curl, tar and sha256sum or shasum; Windows uses PowerShell
and .NET. Available artifacts do not certify native platform acceptance.

## Build from reviewed inputs

Contributors need the existing Python build frontend and build backend. The builder
copies a bounded source snapshot, versions only the staging wheel and Node package,
uses pinned official interpreter archives, and runs `npm ci --ignore-scripts
--omit=dev` in isolated configuration. It retains source hashes, component origins,
license metadata, lock provenance and local logs. It never publishes assets.

```sh
python -B scripts/ci/build_terminal_bundle.py --version 8.0.0-alpha.0 --output /absolute/new/private-build --fetch-components
```

For offline interpreter inputs, replace `--fetch-components` with
`--assets /absolute/path/to/official-archives`. npm dependency resolution still
needs the pinned public registry packages during a fresh contributor build. No
client credentials or personal npm configuration are copied. The initial bundle
contains the Python AST parser; optional binary grammar availability must be reported
separately. No native application SDK is included by implication.

## Install the reviewed private build

Inspect the generated entry and its checksum. The entry embeds exact bundle hashes,
checks its platform/ABI, verifies transport before extraction and calls the bundled
Python core. A dry run performs no network or installation writes.

```sh
sh /absolute/private-build/install.sh --dry-run
sh /absolute/private-build/install.sh --offline-dir /absolute/private-build --no-path
```

PowerShell builds emit `install.ps1`; use `-DryRun`, `-OfflineDir` and `-NoPath`.
`-Action uninstall` runs through the temporary verified interpreter, so a management
executable need not replace/delete itself while open. Windows execution remains a
native acceptance gate. A user-wide native installation has one application command;
project code, memory, notes, sessions and credentials remain in each selected project.
It does not choose ODD/SDD, register Claude command copies or activate model inference.

After placing the managed `bin` directory on PATH, `aikya` opens the local terminal.
`--runtime-dir` remains an explicit contributor-only development path.

```sh
aikya
aikya --help
aikya terminal --target /absolute/project --print-command
aikya-manage doctor
aikya-manage update --dry-run
aikya-manage update --version 8.0.0-alpha.1 --channel preview --offline-dir /absolute/next-private-build --yes --no-path
aikya-manage rollback --yes
aikya-manage uninstall --yes
```

Repeating the entry command updates an older owned installation. The same exact
current payload returns `up-to-date` without creating an operation. Changed bytes
under the same version and update downgrades are refused; use retained rollback
explicitly.

An installed prerelease defaults to its explicit preview channel on update; stable
resolution excludes prereleases. Offline operations require an exact version. `--yes`
commits a displayed operation; omitting it only previews. A private local `--payload`
is an explicit operator trust decision, not a publisher signature.

## Ownership, recovery and migration

The coordinator reuses the application owner and installation lock. It verifies the
complete listed payload before execution, copies into a new final version directory,
preflights fixed local imports/help, verifies again and atomically promotes the signed
current receipt. Old payloads are retained. Customized commands or data block mutation.
Uninstall restores known prior commands and preserves version payloads, global chosen
skills, project memory and client state; it is not a purge of user data.

`aikya-manage recover --yes` reconciles only a fully matching completed promotion,
without repeating downloads, copies or interpreter probes. Partial/unknown effects
remain pending for manual review; no automatic cleanup/replay is offered. The previous
active receipt remains usable when failure happens before promotion. A legacy 7.x
coordinator refuses application mutations while a native activation exists.

Known v7 installation metadata is shown separately in preview and copied exactly into
the signed operation's local backup before promotion. Original v7 metadata/environments
and client registrations are retained. Project profile migration remains the separate
confirmed `/aikya-migrate` workflow; Claude histories are not converted into Pi sessions.
The management authority key under the application root is not global project memory.

See the [execution plan](../plan/2026-11-09-pi-managed-distribution.es.md) and
[validation report](../validation/2026-11-09-pi-managed-distribution.md). Native
Windows/Linux execution, provider trials and stable publication are separate gates.

Upstream [Node 26.13.0 system requirements](https://github.com/nodejs/node/blob/v26.13.0/BUILDING.md)
are recorded in provenance: macOS 13.5+, Windows 10+ (x64 Server 2016+),
Linux glibc 2.28+/kernel 4.18+ or x64 musl 1.2.5+/kernel 6.12+. Linux also
needs the libatomic runtime. These are upstream Node prerequisites, not combined
Aikya/Python acceptance. The installer does not install system packages or choose
another ABI silently. Native preflight and platform testing remain necessary.

GENERATED BY AIKYA HARNESS
