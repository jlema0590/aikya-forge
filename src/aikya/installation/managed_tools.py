"""Reviewed offline terminal binaries; no project cache or startup downloads."""
import hashlib
from importlib.resources import files
import os
from pathlib import Path
import re
from aikya.review.contracts import hash_id,parse
from aikya.storage import write_new
from . import component_download,managed_archives
from .bootstrap import state
from .managed_inputs import TARGETS
from .managed_runtime import _read

PINS={'fd':'10.5.2','rg':'15.2.0'}
REPOSITORIES={'fd':'sharkdp/fd','rg':'BurntSushi/ripgrep'}
LICENSES={'fd':('LICENSE-MIT','LICENSE-APACHE'),'rg':('LICENSE-MIT','UNLICENSE','COPYING')}


def path():return Path(str(files('aikya')/'resources/terminal-tools.json'))


def matches_version(name,output):
    if name not in PINS or not isinstance(output,str) or not 0<len(output)<=16384:return False
    expected=('fd ' if name=='fd' else 'ripgrep ')+PINS[name]
    suffix=r'(?: \(rev [a-f0-9]{7,40}\))?' if name=='rg' else ''
    return re.fullmatch(re.escape(expected)+suffix,output.splitlines()[0]) is not None


def load(target,source=None):
    if target not in TARGETS:raise ValueError('Unsupported terminal tool platform')
    value=parse(_read(state.safe(Path(source) if source is not None else path()),64000))
    if (not isinstance(value,dict) or set(value)!={'schema','versions','platforms'} or value['schema']!=1
            or value['versions']!=PINS or not isinstance(value['platforms'],dict) or set(value['platforms'])!=set(TARGETS)):
        raise ValueError('Invalid reviewed terminal tool catalog')
    selected=value['platforms'][target]
    if not isinstance(selected,dict) or set(selected)!=set(PINS):raise ValueError('Incomplete terminal tool inputs')
    triple=TARGETS[target][0]
    if target.startswith('linux-'):triple=triple.replace('-gnu','-musl')
    for name,item in selected.items():
        version=PINS[name];tag=('v' if name=='fd' else '')+version
        prefix=('fd-v' if name=='fd' else 'ripgrep-')+version+'-'+triple
        filename=prefix+('.zip' if target.startswith('win32') else '.tar.gz')
        expected=dict(file=filename,prefix=prefix,version=version,executable=name+('.exe' if target.startswith('win32') else ''),
                      url='https://github.com/'+REPOSITORIES[name]+'/releases/download/'+tag+'/'+filename)
        if not isinstance(item,dict) or set(item)!=set(expected)|{'sha256'} or any(item[k]!=v for k,v in expected.items()):
            raise ValueError('Terminal tool origin/version/architecture differs from reviewed inputs')
        hash_id(item['sha256'])
    return selected


def prepare(target,assets=None,*,fetch=False,source=None):
    recipe=load(target,source);raws={}
    for name,item in recipe.items():
        if assets is not None:raw=_read(state.safe(Path(assets)/item['file']),16000000)
        elif fetch:raw=component_download.fetch(item['url'],16000000,hosts=frozenset({'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}))
        else:raise ValueError('Provide pinned tool assets or explicitly fetch components')
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Offline terminal tool integrity failed')
        raws[name]=raw
    return recipe,raws


def install(recipe,raws,downloads,payload):
    if set(recipe)!=set(PINS) or set(raws)!=set(PINS):raise ValueError('Incomplete offline terminal tools')
    observed={}
    for name,item in recipe.items():
        raw=raws[name]
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Terminal tool bytes changed before staging')
        archive=state.safe(downloads/item['file']);write_new(archive,raw,mode=0o600)
        destination=state.safe(payload/'tools'/name)
        managed_archives.extract(archive,destination,item['sha256'],item['prefix'])
        binary=state.safe(destination/item['executable'])
        if not binary.is_file():raise ValueError('Pinned terminal tool executable is absent')
        for license in LICENSES[name]:
            if not _read(state.safe(destination/license),1000000):raise ValueError('Terminal tool license is absent')
        observed[name]=dict(path=binary.relative_to(payload).as_posix(),version=item['version'],sha256=hashlib.sha256(_read(binary,16000000)).hexdigest(),licenses=list(LICENSES[name]))
    return observed


def environment(runtime,base=None):
    """Call only after managed_runtime.resolve has verified the entire payload."""
    payload=state.safe(Path(runtime['runtime']).parent);directories=[]
    for name in PINS:
        folder=state.safe(payload/'tools'/name);binary=state.safe(folder/(name+('.exe' if os.name=='nt' else '')))
        if not binary.is_file():raise ValueError('Managed terminal tools are absent; install a current Forge payload')
        if os.pathsep in str(folder):raise ValueError('Managed installation path contains a PATH separator; choose a different installation root')
        directories.append(str(folder))
    result=dict(os.environ if base is None else base);previous=result.get('PATH','')
    result['PATH']=os.pathsep.join(directories+([previous] if previous else []))
    # Windows Node consults its own environment before resolving bare executables.
    result['NoDefaultCurrentDirectoryInExePath']='1'
    return result
