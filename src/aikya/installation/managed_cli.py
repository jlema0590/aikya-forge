"""Native v8 administration; previews are inert and stable never selects an alpha."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import subprocess
import tempfile
from aikya.storage import write_new
from . import managed_archives,managed_install,managed_ownership,managed_releases,managed_runtime,managed_versions
from .bootstrap import options,user_path


def parser():
    result=argparse.ArgumentParser(description=__doc__);sub=result.add_subparsers(dest='action',required=True)
    for action in ('install','update','rollback','uninstall','recover','doctor'):
        command=sub.add_parser(action)
        if action in ('install','update'):
            command.add_argument('--channel',choices=('stable','preview'))
            command.add_argument('--version')
            command.add_argument('--offline-dir',type=Path)
            command.add_argument('--payload',type=Path,help='Explicit trusted private payload directory; no download')
            command.add_argument('--no-path',action='store_true')
        if action!='doctor':
            command.add_argument('--scope',choices=('global','project'),default='global',help='Native binaries are user-wide; project memory remains local')
            command.add_argument('--dry-run',action='store_true');command.add_argument('--yes',action='store_true')
    return result


def _summary(plan):
    return {key:plan[key] for key in ('action','root','version','manifest_hash','legacy','writes')}


def _doctor(root):
    result=dict(root=str(root),installed=False,pending=(root/managed_install.PENDING).exists(),errors=[])
    try:
        managed_ownership.root(root)
        if (root/managed_install.CURRENT).exists():result.update(installed=True,version=managed_runtime.resolve(root)['version'])
    except (ValueError,OSError) as error:result['errors'].append(str(error))
    print(json.dumps(result));return 2 if result['pending'] or result['errors'] else 0


def _execute(args,root,source=None):
    plan=managed_install.preview(root,source,action=args.action)
    if args.action in ('install','update') and args.version is not None:
        requested=managed_releases.resolve(args.version,channel=args.channel or ('preview' if managed_versions.parts(plan['version'])[3] else 'stable'),offline=args.offline_dir is not None)
        if requested!=plan['version']:raise ValueError('Selected payload differs from the requested release version')
    if args.dry_run or not args.yes:print(json.dumps(_summary(plan)));return 0
    result=managed_install.apply(plan,approved=True)
    # PATH uses the established narrow ownership record; never register Claude skills here.
    if args.action in ('install','update') and not args.no_path:
        from contextlib import redirect_stdout
        with redirect_stdout(sys.stderr):user_path.ensure_user_path(root/'bin',root=root)
    if args.action=='uninstall' and not any((root/'receipts').glob('*.json')):
        user_path.remove_user_path(root)
    print(json.dumps(result));return 0


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        root=managed_ownership.root(options.app_root())
        if args.action=='doctor':return _doctor(root)
        if args.action=='install' and (root/managed_install.CURRENT).exists():args.action='update'
        if args.scope!='global':raise ValueError('Native installation has one user-wide command; initialize project-local memory inside each project')
        if args.action=='recover':
            value=managed_install.recover(root,approved=True) if args.yes and not args.dry_run else dict(action='recover',root=str(root),writes=False)
            print(json.dumps(value));return 0
        if args.action not in ('install','update'):return _execute(args,root)
        if args.payload is not None:return _execute(args,root,args.payload)
        channel=args.channel
        if channel is None:
            active=managed_runtime.receipt(root) if (root/managed_install.CURRENT).exists() else None
            channel='preview' if active and managed_versions.parts(active['version'])[3] else 'stable'
        if args.dry_run or not args.yes:
            if args.version not in (None,'latest'):managed_releases.resolve(args.version,channel=channel,offline=args.offline_dir is not None)
            elif args.offline_dir is not None:raise ValueError('Offline installation requires an explicit version')
            print(json.dumps(dict(action=args.action,root=str(root),channel=channel,version=args.version or 'latest',writes=False,network=False)));return 0
        version=managed_releases.resolve(args.version,channel=channel,offline=args.offline_dir is not None)
        raw=managed_releases.artifact(version,managed_runtime.host_platform(),offline_dir=args.offline_dir)
        with tempfile.TemporaryDirectory(prefix='aikya-native-') as temporary:
            stage=Path(temporary).resolve();archive=stage/'terminal.zip';write_new(archive,raw,mode=0o600)
            managed_archives.extract(archive,stage/'payload',hashlib.sha256(raw).hexdigest(),'.')
            return _execute(args,root,stage/'payload')
    except (ValueError,OSError,subprocess.SubprocessError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
