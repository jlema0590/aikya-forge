"""Explicit output placeholders, never blanket exclusions of application source."""
from pathlib import Path
from aikya.core.checkpoints import safe_file
from .contracts import identifier

TOKEN = '{artifacts}'


def validate(argv):
    for index, argument in enumerate(argv):
        if TOKEN in argument and (index == 0 or argument.count(TOKEN) != 1
                or not (argument == TOKEN or argument.endswith('=' + TOKEN))):
            raise ValueError('Use the artifacts placeholder as one complete output path')
    if Path(argv[0]).name.lower() not in ('dotnet', 'dotnet.exe') or len(argv) < 2:
        return
    if argv[1] not in ('build', 'test', 'restore', 'publish', 'pack'):
        return
    options = [i for i, arg in enumerate(argv) if arg == '--artifacts-path' or arg.startswith('--artifacts-path=')]
    valid = len(options) == 1 and (argv[options[0]] == '--artifacts-path=' + TOKEN
        or argv[options[0]] == '--artifacts-path' and options[0] + 1 < len(argv) and argv[options[0] + 1] == TOKEN)
    if not valid:
        raise ValueError('Freeze .NET 8+ checks with --artifacts-path {artifacts}; bin/obj source is never hidden')


def location(root, change_id, run_id, argv):
    validate(argv)
    if not any(TOKEN in argument for argument in argv):
        return None
    path = safe_file(root, '.aikya/pi/check-artifacts/' + identifier(change_id) + '/' + identifier(run_id) + '/.probe').parent
    if path.exists():
        raise ValueError('Existing check artifacts are preserved; use a fresh run identity')
    return path
