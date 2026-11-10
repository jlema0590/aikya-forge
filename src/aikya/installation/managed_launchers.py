"""Exact launcher ownership; customized commands are never overwritten or removed."""
import base64
from importlib.resources import files
import io
from pathlib import Path
import shlex
import zipfile
from aikya.review.contracts import parse
from aikya.storage import atomic_write
from . import managed_ownership as ownership
from .bootstrap import state
from .managed_runtime import _read

MODULES={'aikya':'aikya','aikya-manage':'aikya.installation.managed_cli','aikya-setup':'aikya.installation.registration'}
RECORD='terminal/launchers.json'


def _raw(path):return _read(state.safe(path),256000) if path.exists() else None

def _encode(raw):return base64.b64encode(raw).decode() if raw is not None else None

def _decode(value):
    if value is None:return None
    if not isinstance(value,str) or len(value)>350000:raise ValueError('Unknown launcher bytes')
    try:return base64.b64decode(value,validate=True)
    except ValueError as error:raise ValueError('Invalid launcher ownership') from error


def capture(root):
    from .managed_runtime import host_platform
    names={name+('.exe' if host_platform().startswith('win32') else '') for name in MODULES};record=ownership.read(root,RECORD)
    if record is not None:
        if not isinstance(record,dict) or set(record)!=names:raise ValueError('Unknown launcher ownership record')
        for name,entry in record.items():
            if not isinstance(entry,dict) or set(entry)!={'before','after'}:raise ValueError('Unknown launcher record')
            _decode(entry['before'])
            if _raw(root/'bin'/name)!=_decode(entry['after']):raise ValueError('Customized application launcher is preserved')
        return record
    legacy=state.safe(root/'launchers.json');old=parse(_read(legacy,2000000)) if legacy.exists() else {}
    if not isinstance(old,dict):raise ValueError('Unknown legacy launcher ownership')
    result={}
    for name in names:
        raw=_raw(root/'bin'/name)
        if raw is not None and _encode(raw)!=old.get(str(root/'bin'/name)):raise ValueError('Existing application launcher is not owned')
        result[name]=dict(before=_encode(raw),after=_encode(raw))
    return result


def contents(root,python):
    from .managed_runtime import host_platform
    if host_platform().startswith('win32'):return windows_contents(root,python,host_platform())
    return {name:('#!/bin/sh\nexport AIKYA_INSTALL_ROOT='+shlex.quote(str(root))+'\nexec '+shlex.quote(str(python))+' -I -B -m '+module+' "$@"\n').encode() for name,module in MODULES.items()}


def windows_contents(root,python,target):
    templates={'win32-x64':'t64.exe','win32-arm64':'t64-arm.exe'}
    if target not in templates:raise ValueError('Unsupported Windows launcher architecture')
    stub=(files('pip._vendor.distlib')/templates[target]).read_bytes()
    if not stub.startswith(b'MZ') or len(stub)>256000:raise ValueError('Unsupported native launcher template')
    result={}
    for name,module in MODULES.items():
        script=('import os,runpy\nos.environ["AIKYA_INSTALL_ROOT"]='+repr(str(root))+'\nrunpy.run_module('+repr(module)+',run_name="__main__")\n').encode()
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as container:
            container.writestr(zipfile.ZipInfo('__main__.py',date_time=(1980,1,1,0,0,0)),script)
        result[name+'.exe']=stub+('#!"'+str(python)+'" -I -B\n').encode()+stream.getvalue()
    return result


def intended(before,after,*,retain_manager=False):
    result={name:dict(before=before[name]['before'],after=_encode(raw)) for name,raw in after.items()}
    if retain_manager and before.get('aikya-manage.exe',{}).get('after') is not None:
        result['aikya-manage.exe']['after']=before['aikya-manage.exe']['after']
    return result


def publish(root,record):
    current=capture(root)
    for name,entry in record.items():
        target=state.safe(root/'bin'/name);raw=_decode(entry['after'])
        if _raw(target)!=_decode(current[name]['after']):raise ValueError('Launcher changed during promotion')
        if raw==_decode(current[name]['after']):continue
        if raw is None:target.unlink(missing_ok=True)
        else:atomic_write(target,raw,mode=0o700)
    ownership.save(root,RECORD,record)


def restored(record):return {name:dict(before=entry['before'],after=entry['before']) for name,entry in record.items()}
