"""Assemble private native release assets without publishing or mutating a stable tag."""
import hashlib
from pathlib import Path
import zipfile
from aikya.storage import atomic_write,write_new
from . import managed_entries,managed_payload,managed_runtime
from .bootstrap.state import safe
from .managed_versions import parts


def _installer(destination,version,target,names):
    """One download carries the local entry scripts and their verified native payload."""
    path=destination/('aikya-forge-'+version+'-'+target+'-installer.zip')
    raw={name:managed_runtime._read(safe(destination/name),256000000) for name in names}
    raw['SHA256SUMS']=''.join(hashlib.sha256(value).hexdigest()+'  '+name+'\n' for name,value in sorted(raw.items())).encode()
    with zipfile.ZipFile(path,'x') as archive:
        for name,value in sorted(raw.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.create_system=3;info.external_attr=(0o100755 if name.endswith(('.sh','.command')) else 0o100644)<<16
            archive.writestr(info,value)
    return path


def finish(payload,destination,version,target):
    parts(version);payload=safe(Path(payload).absolute());destination=safe(Path(destination).absolute())
    managed_runtime.inspect(payload,version=version,target=target)
    prefix='aikya-terminal-'+version+'-'+target
    installer='aikya-forge-'+version+'-'+target+'-installer.zip'
    names=[prefix+'.zip','SHA256SUMS','entries','terminal-bootstrap.json','install.ps1' if target.startswith('win32') else 'install.sh',installer,'install.command','install.cmd']
    if not target.startswith('win32'):names.append(prefix+'.tar.gz')
    if any(safe(destination/name).exists() for name in names):raise ValueError('Existing native release assets are preserved')
    destination.mkdir(parents=True,exist_ok=True)
    result=managed_payload.archive(payload,destination/(prefix+'.zip'));archives=[result]
    if not target.startswith('win32'):archives.append(managed_payload.archive(payload,destination/(prefix+'.tar.gz'),format='tar.gz'))
    initial=''.join(item['sha256']+'  '+Path(item['archive']).name+'\n' for item in archives).encode()
    write_new(destination/'SHA256SUMS',initial,mode=0o600)
    entries=managed_entries.build(version,destination,destination/'entries')
    additional={}
    for name in (*entries['entries'],'terminal-bootstrap.json'):
        raw=managed_runtime._read(destination/'entries'/name,128000);write_new(destination/name,raw,mode=0o700 if name.endswith(('.sh','.command')) else 0o600)
        additional[name]=hashlib.sha256(raw).hexdigest()
    package=_installer(destination,version,target,[*entries['entries'],'terminal-bootstrap.json',Path(archives[-1]['archive']).name])
    additional[package.name]=hashlib.sha256(package.read_bytes()).hexdigest()
    if managed_runtime._read(destination/'SHA256SUMS',128000)!=initial:raise ValueError('Release checksums changed during assembly')
    atomic_write(destination/'SHA256SUMS',initial+''.join(sha+'  '+name+'\n' for name,sha in sorted(additional.items())).encode(),mode=0o600)
    result['bootstrap_archive']=archives[-1]['archive']
    result['installer']=str(package)
    return result
