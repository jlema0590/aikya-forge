#!/bin/sh
# Aikya Forge: fetch and verify the native installer for the latest stable release.
set -eu
previous=''; offline_dir=''; version=''; dry_run=''
for argument in "$@"; do
    if [ -n "$previous" ]; then
        case "$previous" in
            --offline-dir) offline_dir="$argument";;
            --version) version="$argument";;
            --channel) [ "$argument" = stable ] || { echo 'The short installer selects stable releases only.' >&2; exit 2; };;
            --scope) [ "$argument" = global ] || { echo 'Native installation is global; project memory stays local.' >&2; exit 2; };;
        esac
        previous=''; continue
    fi
    case "$argument" in
        --offline-dir|--version|--channel|--scope) previous="$argument";;
        --dry-run) dry_run=1;;
        --yes|--no-path) ;;
        --help|-h) printf '%s\n' 'Aikya Forge native installer (latest stable)' 'Usage: sh install.sh [--version X.Y.Z] [--offline-dir DIR] [--no-path] [--dry-run]' 'Requires a published Forge release, curl and a system SHA-256 tool.'; exit 0;;
        *) echo 'Unknown installer option. Use --help.' >&2; exit 2;;
    esac
done
[ -z "$previous" ] || { echo 'Missing installer option value.' >&2; exit 2; }
if [ -n "$version" ]; then
    case "$version" in *[!0-9.]*|'') echo 'Version must be X.Y.Z without a v prefix.' >&2; exit 2;; esac
    printf '%s\n' "$version" | LC_ALL=C awk -F. 'NF!=3 {exit 1} {for(i=1;i<=3;i++) if($i!~/^(0|[1-9][0-9]*)$/) exit 1}' || { echo 'Invalid stable version.' >&2; exit 2; }
fi
if [ -n "$dry_run" ]; then
    printf '{"product":"aikya-forge","release":"%s","network":false,"writes":false}\n' "${version:-latest}"
    exit 0
fi
umask 077
stage="$(mktemp -d "${TMPDIR:-/tmp}/aikya-forge-install.XXXXXXXX")"
trap 'rm -rf "$stage"' 0
trap 'exit 2' HUP INT TERM
if [ -n "$offline_dir" ]; then
    for name in install.sh SHA256SUMS; do
        [ ! -L "$offline_dir/$name" ] && [ -f "$offline_dir/$name" ] || { echo 'Offline installer files must be regular files.' >&2; exit 2; }
        [ "$(wc -c < "$offline_dir/$name")" -le 128000 ] || { echo 'Offline installer file exceeds size limit.' >&2; exit 2; }
        cp "$offline_dir/$name" "$stage/$name"
    done
else
    command -v curl >/dev/null 2>&1 || { echo 'curl is required.' >&2; exit 2; }
    release='latest/download'; [ -z "$version" ] || release="download/v$version"
    for name in install.sh SHA256SUMS; do
        curl -q --fail --silent --show-error --location --proto '=https' --proto-redir '=https' --connect-timeout 15 --max-time 90 --max-filesize 128000 "https://github.com/jlema0590/aikya-forge/releases/$release/$name" -o "$stage/$name" || {
            echo 'No verified Forge release could be downloaded. Check the published releases and your connection.' >&2; exit 2;
        }
        [ "$(wc -c < "$stage/$name")" -le 128000 ] || { echo 'Downloaded installer file exceeds size limit.' >&2; exit 2; }
    done
fi
checksum="$(LC_ALL=C awk '$2=="install.sh" || $2=="*install.sh" {count++; if(NF!=2 || length($1)!=64 || $1~/[^0-9a-f]/) bad=1; digest=$1} END {if(count!=1 || bad) exit 1; print digest}' "$stage/SHA256SUMS")" || { echo 'Installer checksum is missing, malformed or duplicated.' >&2; exit 2; }
if command -v sha256sum >/dev/null 2>&1; then actual="$(sha256sum "$stage/install.sh")"
elif command -v shasum >/dev/null 2>&1; then actual="$(shasum -a 256 "$stage/install.sh")"
else echo 'A system SHA-256 tool is required.' >&2; exit 2; fi
[ "${actual%% *}" = "$checksum" ] || { echo 'Installer checksum mismatch; nothing was installed.' >&2; exit 2; }
sh "$stage/install.sh" "$@"
