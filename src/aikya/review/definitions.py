"""Bind approved check definitions to executable bytes and a selected environment."""
import hashlib
import math
import os
from pathlib import Path
import re
import shutil
from aikya.code_index.policy import project_root, excluded
from aikya.core.checkpoints import identity, safe_file
from .contracts import identifier, digest

ENVIRONMENT_KEYS = ('PATH', 'HOME', 'USERPROFILE', 'SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP',
                    'TMPDIR', 'LANG', 'LC_ALL', 'COMSPEC', 'PATHEXT', 'JAVA_HOME', 'DOTNET_ROOT', 'VIRTUAL_ENV')


def selected_environment(extra=None):
    env = {k: os.environ[k] for k in ENVIRONMENT_KEYS if k in os.environ}
    if extra is not None:
        if not isinstance(extra, dict) or len(extra) > 50:
            raise ValueError('Invalid explicit check environment')
        for key, value in extra.items():
            if (not isinstance(key, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,99}', key)
                    or key.startswith('AIKYA_') or not isinstance(value, str) or len(value) > 16000 or '\x00' in value):
                raise ValueError('Invalid explicit check environment')
        env.update(extra)
    if sum(len(k) + len(v) for k, v in env.items()) > 65536:
        raise ValueError('Check environment exceeds the supported bound')
    return env


def _executable_hash(path):
    before = path.stat()
    if not path.is_file() or before.st_size > 268435456:
        raise ValueError('Executable exceeds the inspection bound')
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(65536): result.update(chunk)
    after = path.stat()
    if (before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns):
        raise ValueError('Executable changed during inspection')
    return result.hexdigest()


def prepare_definition(root, definition, environment=None):
    root = project_root(root)
    keys = {'name', 'argv', 'cwd', 'report_format', 'timeout_seconds', 'max_output_bytes'}
    if not isinstance(definition, dict) or set(definition) != keys:
        raise ValueError('Invalid check definition')
    identifier(definition['name'])
    argv = definition['argv']
    if (not isinstance(argv, list) or not 1 <= len(argv) <= 100
            or any(not isinstance(a, str) or not a or len(a) > 1000 or '\x00' in a for a in argv)):
        raise ValueError('A check command must be an argument list')
    if definition['report_format'] not in ('junit', 'tap', 'trx', 'go-json', 'process'):
        raise ValueError('Unknown execution-result format')
    timeout = definition['timeout_seconds']
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not .05 <= timeout <= 300:
        raise ValueError('Invalid check timeout')
    limit = definition['max_output_bytes']
    if type(limit) is not int or not 1024 <= limit <= 1_048_576:
        raise ValueError('Invalid check output limit')
    relative = definition['cwd']
    if not isinstance(relative, str): raise ValueError('Invalid check directory')
    if relative == '.':
        cwd = root
    else:
        safe_file(root, relative + '/.aikya-check-scope')
        cwd = root / relative
        if excluded(relative) or not cwd.is_dir(): raise ValueError('Invalid check directory')
    env = selected_environment(environment)
    executable = shutil.which(argv[0], path=env.get('PATH', os.defpath))
    if not executable: raise ValueError('Check executable unavailable')
    executable = Path(executable).resolve()
    binding = digest(dict(schema=1, project=identity(root), argv_hash=digest(argv), cwd=relative,
                          report_format=definition['report_format'], timeout_seconds=float(timeout),
                          max_output_bytes=limit, executable=str(executable),
                          executable_hash=_executable_hash(executable), environment_hash=digest(env)))
    return binding, cwd, env, str(executable)


def check_binding(root, definition, environment=None):
    return prepare_definition(root, definition, environment)[0]
