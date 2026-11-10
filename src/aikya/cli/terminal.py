"""Launch a verified managed Pi terminal or an explicitly selected development runtime."""
import argparse
import json
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys


def _selection(provider,model):
    if bool(provider)!=bool(model):raise ValueError('Select provider and model together')
    for value in (provider,model):
        if value is not None and (not isinstance(value,str) or not 1<=len(value)<=160 or any(ord(c)<32 for c in value)):
            raise ValueError('Invalid provider/model selection')


def command_for(root, runtime_dir, node=None, resume=False, provider=None, model=None):
    _selection(provider,model)
    root, runtime = Path(root).resolve(strict=True), Path(runtime_dir).resolve(strict=True)
    manifest = runtime / 'package.json'; entry = runtime / 'src/launcher.ts'
    if not root.is_dir() or not entry.is_file() or entry.is_symlink() or manifest.stat().st_size > 65536:
        raise ValueError('Invalid development runtime')
    package = json.loads(manifest.read_text(encoding='utf8'))
    if not isinstance(package, dict) or package.get('name') != '@aikya/pi-runtime':
        raise ValueError('Unsupported development runtime')
    from aikya.installation.managed_versions import parts
    parts(package.get('version'))
    node = node or shutil.which('node')
    if not node: raise ValueError('Node is unavailable')
    result = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=3, check=True)
    version = re.fullmatch(r'v([0-9]+)\.([0-9]+)\.([0-9]+)\s*', result.stdout)
    if not version or tuple(map(int, version.groups())) < (22, 19, 0):
        raise ValueError('Node 22.19.0 or later is required')
    command = [node, '--experimental-strip-types', str(entry), '--target', str(root), '--python', sys.executable]
    return command + (['--resume'] if resume else []) + (['--provider',provider,'--model',model] if provider else [])


def managed_command(root,resume=False,provider=None,model=None):
    _selection(provider,model)
    root=Path(root).resolve(strict=True)
    if not root.is_dir():raise ValueError('Choose an existing project directory')
    from aikya.installation.managed_runtime import resolve
    runtime=resolve()
    command=[runtime['node'],'--experimental-strip-types',str(Path(runtime['runtime'])/'src/launcher.ts'),
             '--target',str(root),'--python',runtime['python']]
    return command+(['--resume'] if resume else [])+(['--provider',provider,'--model',model] if provider else [])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-dir', type=Path,
                        help='Explicit operator-selected development package; not a signature check')
    parser.add_argument('--target', type=Path, default=Path.cwd())
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--provider', help='Explicit provider; controlled inference also requires a configured budget')
    parser.add_argument('--model', help='Explicit model in the pinned runtime catalog')
    parser.add_argument('--print-command', action='store_true')
    args = parser.parse_args(argv)
    try:
        selection=dict(resume=args.resume,provider=args.provider,model=args.model)
        command=command_for(args.target,args.runtime_dir,**selection) if args.runtime_dir is not None else managed_command(args.target,**selection)
        if args.print_command:
            print(json.dumps({'command': command})); return 0
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError('An interactive terminal is required')
        child = subprocess.Popen(command, cwd=args.target.resolve())
        previous = signal.getsignal(signal.SIGINT)
        try:
            # The foreground Node child receives Ctrl+C and restores its own TUI.
            signal.signal(signal.SIGINT, lambda *_: None)
            return child.wait()
        finally:
            signal.signal(signal.SIGINT, previous)
            if child.poll() is None:
                child.terminate()
                try: child.wait(timeout=5)
                except subprocess.TimeoutExpired: child.kill(); child.wait()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        mode='development' if args.runtime_dir is not None else 'managed'
        print('ERROR: '+mode+' terminal unavailable: '+str(error),file=sys.stderr)
        return 2


if __name__ == '__main__': raise SystemExit(main())
