"""Stable Windows launcher bootstrap; administrative logic runs from the active payload."""
import os
import subprocess
import sys
from . import managed_runtime,managed_ownership
from .bootstrap import options


def windows():return os.name=='nt'


def application():return managed_ownership.root(options.app_root())


def selected_python(root):
    if (root/managed_runtime.CURRENT).exists():return managed_runtime.resolve(root)['python']
    return sys.executable


def main(argv=None):
    arguments=list(sys.argv[1:] if argv is None else argv)
    if not windows():
        from .managed_cli import main as native
        return native(arguments)
    if arguments and arguments[0]=='uninstall' and '--yes' in arguments and '--dry-run' not in arguments:
        print('ERROR: Windows cannot remove the running manager executable. Use the verified install.ps1 -Action uninstall (with -OfflineDir when offline); no changes were made.',file=sys.stderr)
        return 2
    try:
        root=application();python=selected_python(root)
        process=subprocess.run([python,'-I','-B','-m','aikya.installation.managed_cli',*arguments],
                               env={**os.environ,'AIKYA_INSTALL_ROOT':str(root)},check=False)
        return process.returncode
    except (ValueError,OSError) as error:
        print('ERROR: Current verified Forge manager unavailable: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
