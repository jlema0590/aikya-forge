"""Generate version-pinned bootstrap scripts from a verified available native asset set."""
import hashlib
from importlib.resources import files
from pathlib import Path
import shlex
from aikya.review.contracts import encoded
from aikya.storage import write_new
from .bootstrap import download,state
from .managed_inputs import load,TARGETS
from .managed_runtime import _read
from .managed_versions import parts


def build(version,assets,destination):
    identity=parts(version);assets=state.safe(Path(assets).absolute());destination=state.safe(Path(destination).absolute())
    if destination.exists():raise ValueError('Existing native entry output is preserved')
    hashes=download.parse_checksums(_read(state.safe(assets/'SHA256SUMS'),128000));selected={};shell=[];powershell=[]
    for target in TARGETS:
        win=target.startswith('win32');name='aikya-terminal-'+version+'-'+target+('.zip' if win else '.tar.gz')
        if name not in hashes:continue
        raw=_read(state.safe(assets/name),256000000)
        if hashlib.sha256(raw).hexdigest()!=hashes[name]:raise ValueError('Native bootstrap asset integrity checksum mismatch')
        recipe=load(target);python='python/'+recipe['python']['executable'];selected[target]=dict(asset=name,sha256=hashes[name],python=python)
        if win:powershell.append("    '"+target+"'=@{asset='"+name+"';sha256='"+hashes[name]+"';python='"+python+"'}")
        else:shell.append('    '+target+') asset='+shlex.quote(name)+'; checksum='+shlex.quote(hashes[name])+'; python='+shlex.quote(python)+';;')
    if not selected:raise ValueError('No pinned native bootstrap assets were selected')
    rendered={};channel='preview' if identity[3] else 'stable'
    for extension,rows in (('sh',shell),('ps1',powershell)):
        if not rows:continue
        text=(files('aikya')/('resources/terminal-install.'+extension+'.tmpl')).read_text(encoding='utf8')
        text=text.replace('@@VERSION@@',version).replace('@@CHANNEL@@',channel).replace('@@PLATFORMS@@','\n'.join(rows))
        if '@@' in text:raise ValueError('Unresolved native bootstrap placeholder')
        rendered['install.'+extension]=text.encode()
    for extension,available in (('command',any(target.startswith('darwin') for target in selected)),('cmd',bool(powershell))):
        if not available:continue
        text=(files('aikya')/('resources/terminal-install.'+extension+'.tmpl')).read_text(encoding='utf8')
        rendered['install.'+extension]=text.replace('@@VERSION@@',version).encode()
    destination.mkdir(parents=True)
    for name,raw in rendered.items():write_new(destination/name,raw,mode=0o700 if name.endswith(('.sh','.command')) else 0o600)
    record=dict(schema=1,version=version,channel=channel,platforms=selected,entries={name:hashlib.sha256(raw).hexdigest() for name,raw in rendered.items()})
    write_new(destination/'terminal-bootstrap.json',encoded(record)+'\n',mode=0o600)
    return record
