"""Bounded immutable payload manifests and deterministic portable ZIP artifacts."""
import hashlib
from contextlib import ExitStack
import gzip
import io
import os
from pathlib import Path
import stat
import tarfile
import zipfile
from aikya.review.contracts import encoded,parse
from aikya.storage import write_new
from .bootstrap.state import safe
from . import managed_runtime
from .managed_versions import parts


def seal(folder,*,version,target,versions,python,node,runtime):
    parts(version);folder=safe(Path(folder).absolute());files={};pending=[folder];examined=0
    manifest=safe(folder/'manifest.json')
    if manifest.exists():raise ValueError('Existing payload manifest is preserved')
    while pending:
        with os.scandir(pending.pop()) as children:
            for child in children:
                examined+=1
                if examined>75000:raise ValueError('Payload discovery bound exceeded')
                path=safe(Path(child.path));name=path.relative_to(folder).as_posix()
                if child.is_dir(follow_symlinks=False):pending.append(path);continue
                if not child.is_file(follow_symlinks=False):raise ValueError('Payload contains an unsupported object')
                raw=managed_runtime._read(path,256000000);record=child.stat(follow_symlinks=False)
                files[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),executable=name in (python,node) or bool(record.st_mode&stat.S_IXUSR))
    value=dict(schema=1,version=version,platform=target,python=python,node=node,runtime=runtime,versions=versions,files=files)
    managed_runtime._manifest(value,dict(version=version,platform=target));managed_runtime._inventory(folder,files)
    # Identity is checked before creating the manifest, preserving unknown staging data.
    package=parse(managed_runtime._read(safe(folder/runtime/'package.json'),64000))
    if (not isinstance(package,dict) or package.get('name')!='@aikya/pi-runtime' or package.get('version')!=version
            or not isinstance(package.get('dependencies'),dict)
            or package['dependencies'].get('@earendil-works/pi-coding-agent')!=versions['pi']):raise ValueError('Staged runtime identity is inconsistent')
    raw=encoded(value).encode();write_new(manifest,raw,mode=0o600)
    return dict(manifest_hash=hashlib.sha256(raw).hexdigest(),files=len(files),bytes=sum(entry['size'] for entry in files.values()))


def archive(folder,destination,*,format='zip'):
    if format not in ('zip','tar.gz'):raise ValueError('Select a ZIP or POSIX gzip terminal archive')
    folder=safe(Path(folder).absolute());destination=safe(Path(destination).absolute())
    if destination.exists():raise ValueError('Existing terminal archive is preserved')
    manifest=parse(managed_runtime._read(safe(folder/'manifest.json'),16000000))
    if not isinstance(manifest,dict):raise ValueError('Unknown terminal archive input')
    checked=managed_runtime.inspect(folder,version=manifest.get('version'),target=manifest.get('platform'))
    entries=dict(checked['manifest']['files']);raw=managed_runtime._read(folder/'manifest.json',16000000)
    entries['manifest.json']=dict(sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),executable=False)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with ExitStack() as stack:
        output=stack.enter_context(destination.open('xb'))
        if format=='zip':container=stack.enter_context(zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6))
        else:
            compressed=stack.enter_context(gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0,compresslevel=6))
            container=stack.enter_context(tarfile.open(fileobj=compressed,mode='w|',format=tarfile.PAX_FORMAT))
        for name,entry in sorted(entries.items()):
            raw=managed_runtime._read(safe(folder/name),entry['size'])
            if hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Payload changed during archive creation')
            if format=='zip':
                info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.create_system=3
                info.external_attr=(0o100700 if entry['executable'] else 0o100600)<<16;info.compress_type=zipfile.ZIP_DEFLATED
                container.writestr(info,raw)
            else:
                info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o700 if entry['executable'] else 0o600
                container.addfile(info,io.BytesIO(raw))
    raw=managed_runtime._read(destination,256000000)
    return dict(archive=str(destination),sha256=hashlib.sha256(raw).hexdigest(),size=len(raw),manifest_hash=checked['manifest_hash'])
