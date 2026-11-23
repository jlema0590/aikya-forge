# Forge 0.2.0 operations

This is the current Forge guide. Earlier v7/v8 distribution records describe their
own snapshots. Forge starts independently; no real v7 installation migration is in scope.
The Python distribution remains aikya-forge and the CLI/import namespace is aikya.

## Native installation and lifecycle

A contributor builds with Python 3.13, build/setuptools>=77/wheel, npm and the pinned
public components: `python scripts/ci/build_terminal_bundle.py --version 0.2.0
--output /new/private/path --fetch-components`. The output must not exist. Reviewed
binary parsers are included by default; --code-index none explicitly omits them.
The reviewed catalog covers seven targets; Windows ARM64 Dart remains file-only.

The resulting install.sh/install.ps1 select exact version-bound archives with SHA-256.
Use the generated shell installer with --offline-dir /verified/bundle --no-path, or
PowerShell -OfflineDir /verified/bundle -NoPath for isolated acceptance. End users do
not need a Python/Node installation for these native bundles. Short Pages URLs are
not advertised as available until an actual release and deployment are accepted.

For isolated external trials, use the prepared native candidate folder and select
a fresh AIKYA_INSTALL_ROOT. Run that candidate application's bin/aikya or
bin/aikya.exe by its absolute path. This keeps the QA installation and project
ledgers distinct; its exported fingerprint must match the external packet.

Default application roots are ~/Library/Application Support/AikyaForge,
%LOCALAPPDATA%/AikyaForge and $XDG_DATA_HOME/aikya-forge (or ~/.local/share/aikya-forge).
AIKYA_INSTALL_ROOT can select a reviewed independent root. A v7 current.json is refused
before adoption; older PATH entries and installations are preserved. Forge's managed
PATH entry takes precedence. Project memory remains inside each project.

Use aikya-manage doctor, update --yes and rollback --yes to inspect/select verified
native versions. Consult --help before choosing a version/channel or offline payload.
Windows keeps the small manager launcher and forwards administration to the verified
active core. On Windows, uninstall with the verified external install.ps1 -Action
uninstall; the running manager refuses self-uninstall before effects. On POSIX,
aikya-manage uninstall --yes removes owned activation, retaining project data and
recoverable packages. Arbitrary customized bytes block destructive ownership changes.

## Skill withdrawal and recovery

Use /aikya-uninstall-skills JSON: {"scope":"project","names":["example-skill"]}.
The host previews exact names/selection identity and requires native confirmation;
headless requests cannot approve effects. Scope global affects only the global
library selection; project/local affects only that project's independent copy.
An explicit all:true selects the reviewed current set; no matches is a no-op.

The Python equivalent is aikya skills uninstall --scope project --name example-skill
--target /absolute/project, followed by the same command with --yes after review.
Completed results return an operation_id. Restore using aikya skills restore --scope
project --all --operation OPERATION_ID --target /absolute/project, then --yes.
The Pi JSON action restore accepts operation_id and names or all. Consult command
help for the exact schema. Restart the author session after selection changes.

Withdrawal disables registry selection while retaining exact immutable packages and
signed backups. It is not disk purging or external-client/plugin cleanup. Customized
cache, comparison document, changed registry or restore-name conflicts are preserved
and refused. Exact withdrawn bytes are restored explicitly; updates do not silently
re-enable them. Global selection changes do not remove project copies.

If interrupted, use aikya skills recover --scope project --target /absolute/project
for a preview, then --yes; Pi action recover also confirms. Recovery completes only
a signed matching observed metadata outcome, never downloads or replays package code.
Project operations write indexed audit Markdown and regenerate the owned comparison.
Global operations keep their own signed library ledger without creating project docs.

## Frozen .NET checks

For .NET SDK 8+, define argv such as ["dotnet","build","App.csproj",
"--artifacts-path","{artifacts}"]. Forge freezes the original definition, allocates
.aikya/pi/check-artifacts/<change>/<run>, and substitutes the complete token only at
execution. Existing or linked destinations fail before reservation. Independent runs
must restore/build their own inputs; --no-build/--no-restore cannot share prior private
outputs implicitly. Real bin/obj sources remain candidate inputs. This is output
isolation, not an operating-system sandbox for approved project build scripts.

## Release preparation and publication

forge-native.yml builds two versions on macOS Intel/ARM, Windows x64/ARM, Linux GNU
x64/ARM and Linux musl x64. Each host installs, runs all portable onboarding profiles,
checks installed memory/HTML external edits, themes, update, rollback and uninstall.
Installed acceptance also exercises actual POSIX PTY/Windows ConPTY input, empty-PATH
recursive completion, confirmed theme, resize and cache refusal. Human/device
visual review and authenticated provider acceptance remain separate requirements.
Archive downloads and a configured job are not proof that its host passed.

forge-release.yml is manually dispatched with publish=false by default. It requires
full tests and all seven same-commit native artifacts, verifies complete ZIP content
and checksums, and emits a reviewable universal installer artifact. Publication needs
main plus separately reviewed current real-provider evidence. The read-only gate
checks evidence shape/current source; a human must assess real transport provenance.
It does not authorize a deployment itself. Only explicit publish=true requests the
GitHub release and Pages steps. Existing releases/assets are never replaced.

Pages copies exact checksum-bound bytes downloaded from that published release.
PowerShell uses install.ps1.txt. The earlier Harness publication jobs remain scoped
to their original repository. No release/tag/Pages is created by local tests.

See the [external procedure](../validation/forge-provider-procedure.md) and
[current evidence](../validation/2026-11-19-interactive-acceptance.md).

## Windows SDK environment

Reviewed checks preserve APPDATA and LOCALAPPDATA in the signed environment binding.
When isolating SDK state, provide existing private directories for both, together
with HOME/USERPROFILE/DOTNET_CLI_HOME and any reviewed package cache. Omitting the
Windows cache locations caused NuGet to create NuGet/Migrations/1 in the working
project. Such a change remains a failed candidate; it is never hidden by exclusions.
A changed environment location requires a fresh reviewed binding.

GENERATED BY AIKYA FORGE
