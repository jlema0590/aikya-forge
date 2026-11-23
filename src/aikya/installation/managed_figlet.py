"""A reviewed universal wheel for offline native terminal presentation."""
import hashlib
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit
from aikya.review.contracts import parse,hash_id
from aikya.storage import write_new
from .bootstrap import state
from .managed_runtime import _read


def load(source=None):
    path=Path(source) if source is not None else Path(str(files('aikya')/'resources/terminal-figlet.json'))
    item=parse(_read(state.safe(path),8192))
    if (not isinstance(item,dict) or set(item)!={'schema','version','file','url','sha256'} or type(item['schema']) is not int
            or item['schema']!=1 or item['version']!='1.0.4' or item['file']!='pyfiglet-1.0.4-py3-none-any.whl'
            or not isinstance(item['url'],str)):raise ValueError('Invalid pyfiglet input')
    uri=urlsplit(item['url']);hash_id(item['sha256'])
    if (uri.scheme!='https' or uri.netloc!='files.pythonhosted.org' or uri.query or uri.fragment
            or not uri.path.startswith('/packages/') or uri.path.rsplit('/',1)[-1]!=item['file']):raise ValueError('Invalid pyfiglet origin')
    return item


def prepare(assets=None,*,fetch=False):
    from . import component_download
    recipe=load()
    if assets is not None:raw=_read(state.safe(Path(assets)/recipe['file']),3000000)
    elif fetch:raw=component_download.fetch(recipe['url'],3000000,hosts=frozenset({'files.pythonhosted.org'}))
    else:raise ValueError('Provide the pinned pyfiglet wheel or explicitly fetch components')
    if hashlib.sha256(raw).hexdigest()!=recipe['sha256']:raise ValueError('pyfiglet wheel integrity differs')
    return recipe,raw


def install(recipe,raw,downloads,purelib):
    from .managed_archives import extract
    if recipe!=load() or hashlib.sha256(raw).hexdigest()!=recipe['sha256']:raise ValueError('pyfiglet wheel identity differs')
    wheel=downloads/recipe['file'];write_new(wheel,raw,mode=0o600)
    extract(wheel,purelib,recipe['sha256'],'.',merge=True)


def probe_script():
    return ('import json;from aikya.presentation.banner import banner;v=banner();'
            'assert v["generator"]=="pyfiglet" and v["version"]=="1.0.4" and len(v["variants"])==2;'
            'print(json.dumps(v))')
