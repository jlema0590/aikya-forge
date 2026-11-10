# Aikya Forge native installation

Forge starts independently at **0.1.0**. The native builder creates a complete
installer ZIP for its current host. A successful build is distinct from native
installation acceptance on other systems and from release publication.

## Install an extracted package

Obtain the installer matching your computer and extract every file together:

| Platform | Local entry |
|---|---|
| macOS Apple Silicon | `install.command` in the `darwin-arm64` installer |
| macOS Intel | `install.command` in the `darwin-x64` installer |
| Windows x64 | `install.cmd` in the `win32-x64` installer |
| Linux x64 / glibc | `sh ./install.sh --offline-dir .` in the `linux-x64-gnu` installer |

The package includes Python, Node and Pi; the end user does not prepare Python,
Node or npm. The macOS/Windows entries locate their adjacent files even when the
extracted directory contains spaces. Windows uses PowerShell with execution policy
bypass scoped to that process; the launcher does not change the machine policy.
macOS/Linux need their system shell, tar and a SHA-256 tool. The offline package
requires no download during installation and checks payload integrity before use.

For an inert preview or an explicit terminal invocation:

```sh
sh ./install.sh --offline-dir . --dry-run
sh ./install.sh --offline-dir .
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -OfflineDir . -DryRun
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -OfflineDir .
```

Open a new terminal after installation and run `aikya`. Use `aikya-manage doctor`
to inspect installation health. Installation does not initialize a project, choose
ODD/SDD, register Claude skills or call a model.

## Build locally

Prepare the contributor environment described in the root README, then run:

```sh
python scripts/ci/build_terminal_bundle.py --version 0.1.0 --output dist/forge-native --fetch-components
```

The output directory must be new. The builder captures source hashes, builds the
`aikya-forge` wheel, verifies pinned official interpreter archives and installs
locked npm dependencies in isolated configuration. `--assets <directory>` accepts
previously downloaded interpreter archives; their hashes are still checked and
fresh npm resolution may still need network access.

The output contains `aikya-forge-0.1.0-<platform>-installer.zip`, payload archives,
local entry scripts, `terminal-bootstrap.json`, `SHA256SUMS`, provenance and logs.
The installer ZIP contains its own checksums and only its required entry/payload
files. POSIX scripts retain executable mode in the ZIP. None of these commands
publishes a package, release, tag or Pages site.

## Exercise the real installation

```sh
python scripts/ci/terminal_installer_smoke.py --assets dist/forge-native --target /absolute/new/forge-smoke --output dist/forge-smoke.json
```

Choose a new writable directory. The smoke uses isolated application/home/project
paths, disables PATH edits and observes preview, install, help, doctor, reinstall
and uninstall. It retains process output and checks that owner data and the project
remain intact. An existing smoke directory or report is preserved rather than
adopted or overwritten. The test uses no model/provider credentials.

## Build the other systems

The manual [native installer workflow](../../../.github/workflows/forge-installers.yml)
builds macOS ARM64/x64, Windows x64 and Linux GNU x64 independently. Run it only
after the reviewed source is available in GitHub. Successful jobs retain installer
artifacts and evidence; the acceptance job requires every matrix entry to succeed.
A failed platform is visible and does not become verified through another host.

Runner labels were checked against the [official GitHub runner documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-where-workflows-run/choose-the-runner-for-a-job).
The workflow has read-only repository permissions and does not invoke release/Pages
publication. Retained Windows ARM64 and Linux ARM64/musl recipes are not part of this
initial four-platform acceptance matrix.

## Management and compatibility

```sh
aikya-manage doctor
aikya-manage update --dry-run
aikya-manage rollback --yes
aikya-manage uninstall --yes
```

Update requires separately available verified release assets; no unpublished version
is implied. Repeating the same installer returns `up-to-date`. Changed bytes under
the same version and update downgrades are refused; retained rollback is explicit.
Uninstall removes owned active commands and preserves project data, selected skills
and retained payloads. On Windows the temporary interpreter used by
`install.ps1 -Action uninstall -OfflineDir .` avoids deleting a running manager.

Interrupted operations remain pending for reviewed recovery. `aikya-manage recover
--yes` only reconciles a fully matching completed promotion; it does not replay
unknown effects. Customized/unowned command bytes block replacement.

New Python distributions are `aikya-forge`, while imports and commands remain
`aikya`. Known v7/v8 package identities and previous document ownership signatures
remain readable. `.harness/`, `harness.json` and `aikya/scripts/harness/` retain
their functional paths; installation does not relocate project data.

Bundled Node 26.13.0 prerequisites remain pinned in the recipes: macOS 13.5+,
Windows 10+ (x64 Server 2016+), Linux glibc 2.28+/kernel 4.18+ or x64 musl
1.2.5+/kernel 6.12+, plus libatomic on Linux. These are the recorded
[upstream Node requirements](https://github.com/nodejs/node/blob/v26.13.0/BUILDING.md),
not combined Aikya/Python acceptance. The installer does not add system packages.

See the [implementation plan](../plan/2026-11-10-forge-brand-installers.es.md)
and the [validation record](../validation/2026-11-10-forge-brand-installers.md).

GENERATED BY AIKYA FORGE
