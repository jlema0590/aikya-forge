"""Lock-backed private Node staging; dependency installation never runs lifecycle scripts."""
import hashlib
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit
from aikya.review.contracts import encoded,parse
from aikya.storage import write_new
from .bootstrap.state import safe
from . import build_sources
from .managed_runtime import _read
from .managed_versions import parts


def prepare(source,destination,version):
    parts(version);destination=safe(Path(destination).absolute());source=Path(source).resolve(strict=True)
    if destination.exists():raise ValueError('Existing Node staging is preserved')
    raw=build_sources.capture(source,files=('package.json','package-lock.json'),directories=('src',))
    package=parse(raw['package.json']);lock=parse(raw['package-lock.json'])
    if (not isinstance(package,dict) or package.get('name')!='@aikya/pi-runtime' or not isinstance(lock,dict)
            or not isinstance(package.get('dependencies'),dict)
            or lock.get('lockfileVersion')!=3 or not isinstance(lock.get('packages'),dict) or len(lock['packages'])>2000
            or not isinstance(lock['packages'].get(''),dict)
            or lock['packages'].get('',{}).get('dependencies')!=package.get('dependencies')
            or any(package.get('dependencies',{}).get(name)!='1.5.0' for name in ('@earendil-works/pi-coding-agent','@earendil-works/pi-ai','@earendil-works/pi-tui'))):
        raise ValueError('Staged Node identity/lock/Pi pins are inconsistent')
    for name,entry in lock['packages'].items():
        if not name:continue
        if not isinstance(entry,dict) or not isinstance(entry.get('resolved'),str) or not isinstance(entry.get('integrity'),str):raise ValueError('Unknown Node dependency metadata')
        url=urlsplit(entry.get('resolved',''));integrity=entry.get('integrity','')
        if (not name.startswith('node_modules/') or entry.get('link') or url.scheme!='https' or url.hostname!='registry.npmjs.org'
                or url.username or url.password or url.query or url.fragment or not re.fullmatch(r'sha512-[A-Za-z0-9+/]{86}==',integrity)):
            raise ValueError('Node dependency lacks a pinned registry origin/integrity')
    if build_sources.capture(source,files=('package.json','package-lock.json'),directories=('src',))!=raw:raise ValueError('Node source changed during capture')
    fingerprints={name:hashlib.sha256(value).hexdigest() for name,value in raw.items()}
    package['version']=version;lock['version']=version;lock['packages']['']['version']=version
    raw['package.json']=encoded(package).encode();raw['package-lock.json']=encoded(lock).encode()
    destination.mkdir(parents=True)
    for name,value in sorted(raw.items()):
        path=destination/name;path.parent.mkdir(parents=True,exist_ok=True);write_new(path,value,mode=0o600)
    return dict(files=fingerprints,staged_lock_sha256=hashlib.sha256(raw['package-lock.json']).hexdigest())


def flatten(runtime):
    runtime=safe(Path(runtime).absolute());modules=safe(runtime/'node_modules');pending=[modules];links=[];examined=0
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                examined+=1
                if examined>50000:raise ValueError('Node dependency discovery exceeds its bound')
                path=Path(child.path)
                if child.is_symlink():
                    target=path.resolve(strict=True)
                    if path.parent.name!='.bin' or not target.is_relative_to(modules) or not safe(target).is_file():raise ValueError('Unreviewed Node dependency link')
                    raw=_read(target,64000000);links.append((path,os.readlink(path),raw,bool(target.stat().st_mode&0o111)))
                elif child.is_dir(follow_symlinks=False):safe(path);pending.append(path)
                elif not child.is_file(follow_symlinks=False):raise ValueError('Unsupported Node dependency object')
    for path,original,raw,executable in links:
        if not path.is_symlink() or os.readlink(path)!=original:raise ValueError('Node alias changed during materialization')
        path.unlink();write_new(path,raw,mode=0o700 if executable else 0o600)
    return len(links)


def install(runtime,node,home,log):
    runtime=safe(Path(runtime).absolute());node=safe(Path(node).absolute())
    npm=node.parent/'node_modules/npm/bin/npm-cli.js' if os.name=='nt' else node.parent.parent/'lib/node_modules/npm/bin/npm-cli.js'
    safe(npm)
    process=subprocess.run([str(node),str(npm),'ci','--ignore-scripts','--omit=dev','--no-audit','--no-fund','--no-progress'],
                           cwd=runtime,env=build_sources.environment(home),capture_output=True,timeout=600)
    write_new(log,process.stdout+process.stderr,mode=0o600)
    if process.returncode:raise ValueError('Pinned Node installation failed; retained local build log requires review')
    return flatten(runtime)
