"""Small inert managed terminal data for installer filesystem contracts."""
import json
from pathlib import Path
from aikya.installation.managed_payload import seal


def payload(root,version='8.0.0-alpha.0'):
    root=Path(root);root.mkdir(parents=True)
    for name,raw in {'python/bin/python3':b'Inert interpreter fixture','node/bin/node':b'Inert interpreter fixture',
                     'runtime/src/launcher.ts':b'// Inert runtime fixture',
                     'runtime/package.json':json.dumps(dict(name='@aikya/pi-runtime',version=version,dependencies={'@earendil-works/pi-coding-agent':'1.5.0'})).encode()}.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);path.chmod(0o700 if '/bin/' in name else 0o600)
    return seal(root,version=version,target='darwin-arm64',versions=dict(python='3.13.18',node='26.13.0',pi='1.5.0'),python='python/bin/python3',node='node/bin/node',runtime='runtime')


def snapshot(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
