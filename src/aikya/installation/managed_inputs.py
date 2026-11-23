"""Explicit official build inputs; an available asset pair is not native acceptance."""
from importlib.resources import files
from pathlib import Path
import re
from urllib.parse import quote
from aikya.review.contracts import parse,hash_id
from .bootstrap.state import safe
from .managed_runtime import host_platform,_read,_version

TARGETS={'darwin-arm64':('aarch64-apple-darwin','darwin-arm64'),'darwin-x64':('x86_64-apple-darwin','darwin-x64'),
 'linux-x64-gnu':('x86_64-unknown-linux-gnu','linux-x64'),'linux-arm64-gnu':('aarch64-unknown-linux-gnu','linux-arm64'),
 'linux-x64-musl':('x86_64-unknown-linux-musl','linux-x64-musl'),'win32-x64':('x86_64-pc-windows-msvc','win-x64'),'win32-arm64':('aarch64-pc-windows-msvc','win-arm64')}


def path():return Path(str(files('aikya')/'resources/terminal-inputs.json'))


def _requirements(target,node):
    if node!='26.13.0':raise ValueError('Review upstream system requirements before changing the bundled Node pin')
    if target.startswith('darwin'):minimum=dict(macos='13.5')
    elif target.startswith('win32'):minimum=dict(windows='10',server='2016' if target=='win32-x64' else None)
    elif target.endswith('-gnu'):minimum=dict(kernel='4.18',glibc='2.28',libraries=['libatomic'])
    else:minimum=dict(kernel='6.12',musl='1.2.5',libraries=['libatomic'])
    return dict(node=minimum,source='https://github.com/nodejs/node/blob/v26.13.0/BUILDING.md',
                acceptance='Upstream Node prerequisites, not combined native Aikya/Python acceptance; no system packages are installed automatically')


def _asset(value,expected):
    if not isinstance(value,dict) or set(value)!={'file','url','sha256','prefix','executable'}:raise ValueError('Unknown pinned component recipe')
    hash_id(value['sha256'])
    if any(value[key]!=expected[key] for key in expected):raise ValueError('Component identity/origin differs from its pinned recipe')
    return dict(value)


def load(target=None,source=None):
    target=target or host_platform();value=parse(_read(safe(Path(source) if source is not None else path()),128000))
    if (not isinstance(value,dict) or set(value)!={'schema','pins','platforms'} or value['schema']!=1
            or not isinstance(value['pins'],dict) or set(value['pins'])!={'python','python_release','node','pi'}
            or not isinstance(value['platforms'],dict) or set(value['platforms'])-set(TARGETS) or target not in value['platforms']):
        raise ValueError('No pinned runtime recipe for this platform/ABI')
    pins=value['pins']
    if (not (3,10,0)<=_version(pins['python'])<(3,14,0) or _version(pins['node'])<(22,19,0) or pins['pi']!='1.5.0'
            or not isinstance(pins['python_release'],str) or not re.fullmatch('[0-9]{8}',pins['python_release'])):raise ValueError('Unsupported component pin set')
    triple,node_target=TARGETS[target];win=target.startswith('win32');py=pins['python'];release=pins['python_release'];node=pins['node']
    pyname='cpython-'+py+'+'+release+'-'+triple+'-install_only_stripped.tar.gz';node_prefix='node-v'+node+'-'+node_target;node_name=node_prefix+('.zip' if win else '.tar.gz')
    selected=value['platforms'][target]
    if not isinstance(selected,dict) or set(selected)!={'python','node'}:raise ValueError('Incomplete platform recipe')
    python=_asset(selected['python'],dict(file=pyname,url='https://github.com/astral-sh/python-build-standalone/releases/download/'+release+'/'+quote(pyname,safe=''),prefix='python',executable='python.exe' if win else 'bin/python'+'.'.join(py.split('.')[:2])))
    node_input=_asset(selected['node'],dict(file=node_name,url='https://nodejs.org/dist/v'+node+'/'+node_name,prefix=node_prefix,executable='node.exe' if win else 'bin/node'))
    return dict(platform=target,versions={key:pins[key] for key in ('python','node','pi')},python=python,node=node_input,requirements=_requirements(target,node))
