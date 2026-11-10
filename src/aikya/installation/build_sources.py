"""Bounded source snapshots for release builders; never copy personal client state."""
import os
from pathlib import Path
from aikya.installation.bootstrap.state import safe
from aikya.installation.managed_runtime import _read

IGNORED={'__pycache__','node_modules','.git','.DS_Store','build','dist'}


def capture(root,files=(),directories=()):
    root=Path(root).resolve(strict=True);result={};total=0;examined=0
    pending=[root/name for name in directories]
    chosen=[root/name for name in files]
    def admit(path):
        nonlocal total
        safe(path)
        if not path.is_relative_to(root) or not path.is_file():raise ValueError('Unknown builder source input')
        value=_read(path,64000000);total+=len(value)
        if len(result)>=20000 or total>256000000:raise ValueError('Builder source snapshot exceeds its bound')
        result[path.relative_to(root).as_posix()]=value
    for path in chosen:admit(path)
    while pending:
        current=pending.pop();safe(current)
        with os.scandir(current) as entries:
            for entry in entries:
                examined+=1
                if examined>25000:raise ValueError('Builder source discovery exceeds its bound')
                name=entry.name
                if name in IGNORED or name.endswith(('.egg-info','.pyc','.pyo')) or (name.startswith('.env') and name!='.env.example'):continue
                path=Path(entry.path);safe(path)
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                elif entry.is_file(follow_symlinks=False):admit(path)
                else:raise ValueError('Unsupported builder input object')
    return result


def environment(home):
    home=Path(home);home.mkdir(parents=True,exist_ok=True)
    allowed=('PATH','LANG','LC_ALL','TERM','TMPDIR','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','SSL_CERT_FILE','SSL_CERT_DIR','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY')
    env={k:os.environ[k] for k in allowed if k in os.environ}
    env.update(HOME=str(home),USERPROFILE=str(home),XDG_CONFIG_HOME=str(home/'.config'),XDG_CACHE_HOME=str(home/'.cache'),
               PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1',DO_NOT_TRACK='1',npm_config_userconfig=str(home/'empty-npmrc'),npm_config_cache=str(home/'npm-cache'))
    (home/'empty-npmrc').touch(exist_ok=True)
    return env
