"""Read-only integrity resolution of an explicitly activated managed terminal payload."""
import hashlib
import os
from pathlib import Path,PurePosixPath
import platform
import re
import stat
import sys
from aikya.installation.bootstrap import options,state
from aikya.review import authentication
from aikya.core.package_paths import validate as portable_paths
from aikya.review.contracts import hash_id,parse,read_record
from .managed_versions import parts as release_parts

CURRENT='terminal/current.json'


def host_platform():
    system={'darwin':'darwin','win32':'win32','linux':'linux'}.get(sys.platform)
    architecture={'arm64':'arm64','aarch64':'arm64','amd64':'x64','x86_64':'x64'}.get(platform.machine().lower())
    if not system or not architecture:raise ValueError('No managed terminal payload for this host')
    if system=='linux':
        libc=platform.libc_ver()[0].lower()
        if libc not in ('glibc','musl'):raise ValueError('Linux C runtime is unknown; select a verified compatible distribution')
        return system+'-'+architecture+('-gnu' if libc=='glibc' else '-musl')
    return system+'-'+architecture


def _path(root,relative):
    if (not isinstance(relative,str) or not 1<=len(relative)<=512 or '\\' in relative or ':' in relative
            or PurePosixPath(relative).is_absolute() or any(p in ('','.','..','.git') for p in relative.split('/'))
            or any(ord(c)<32 for c in relative)):
        raise ValueError('Unsafe managed payload path')
    target=state.safe(root/relative)
    if not target.resolve().is_relative_to(root.resolve()):raise ValueError('Escaped terminal payload')
    return target


def _read(path,limit):
    try:handle=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    except OSError as error:raise ValueError('Managed terminal file is unavailable') from error
    with os.fdopen(handle,'rb') as stream:
        record=os.fstat(stream.fileno())
        if not stat.S_ISREG(record.st_mode) or record.st_size>limit:raise ValueError('Oversized/nonregular terminal file')
        value=stream.read(limit+1)
    if len(value)>limit:raise ValueError('Terminal file exceeded its read bound')
    return value


def _version(value):
    if not isinstance(value,str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)',value):raise ValueError('Invalid managed component version')
    return tuple(map(int,value.split('.')))


def _manifest(value,receipt):
    fields={'schema','version','platform','python','node','runtime','versions','files'}
    if (not isinstance(value,dict) or set(value)!=fields or value['schema']!=1 or value['version']!=receipt['version']
            or value['platform']!=receipt['platform'] or not isinstance(value['versions'],dict)
            or set(value['versions'])!={'python','node','pi'} or not isinstance(value['files'],dict)
            or not 1<=len(value['files'])<=50000):raise ValueError('Unknown managed terminal manifest')
    versions=value['versions']
    if not (3,10,0)<=_version(versions['python'])<(3,14,0) or _version(versions['node'])<(22,19,0) or versions['pi']!='1.5.0':raise ValueError('Unsupported managed component versions')
    portable_paths(value['files'],max_files=50000,max_nodes=75000,max_length=512)
    total=0
    for name,entry in value['files'].items():
        if not isinstance(entry,dict) or set(entry)!={'sha256','size','executable'}:raise ValueError('Invalid managed file record')
        hash_id(entry['sha256'])
        if type(entry['size']) is not int or not 0<=entry['size']<=256000000 or type(entry['executable']) is not bool:raise ValueError('Invalid managed file bounds')
        total+=entry['size']
    if total>1500000000:raise ValueError('Managed terminal exceeds its data bound')
    if any(not isinstance(value[k],str) for k in ('python','node','runtime')):raise ValueError('Invalid managed terminal roles')
    roles=(value['python'],value['node'],value['runtime']+'/src/launcher.ts',value['runtime']+'/package.json')
    if len(set(roles))!=4 or any(name not in value['files'] for name in roles):raise ValueError('Missing managed terminal entrypoint')
    if any(value['files'][name]['executable'] is not True for name in roles[:2]):raise ValueError('Managed interpreters are not executable roles')


def _inventory(folder,files):
    pending=[folder];actual=set();examined=0
    while pending:
        current=pending.pop();state.safe(current)
        with os.scandir(current) as children:
            for child in children:
                examined+=1
                if examined>75000:raise ValueError('Managed terminal discovery bound exceeded')
                path=Path(child.path);name=path.relative_to(folder).as_posix()
                if child.is_symlink() or (os.name=='nt' and hasattr(path,'is_junction') and path.is_junction()):raise ValueError('Linked managed payload object')
                if child.is_dir(follow_symlinks=False):pending.append(path);continue
                if not child.is_file(follow_symlinks=False):raise ValueError('Unknown managed payload object')
                if name=='manifest.json':continue
                if name not in files:raise ValueError('Unlisted managed payload data is preserved')
                entry=files[name];record=child.stat(follow_symlinks=False)
                if record.st_size!=entry['size'] or (os.name!='nt' and bool(record.st_mode&stat.S_IXUSR)!=entry['executable']):raise ValueError('Managed terminal size/permissions changed')
                if hashlib.sha256(_read(path,entry['size'])).hexdigest()!=entry['sha256']:raise ValueError('Managed terminal bytes changed')
                actual.add(name)
    if actual!=set(files):raise ValueError('Managed terminal files are missing')


def inspect(folder,*,version,target):
    """Validate unactivated data; this grants no authority to execute its code."""
    release_parts(version);folder=state.safe(Path(folder).absolute())
    raw=_read(_path(folder,'manifest.json'),16000000);manifest=parse(raw)
    _manifest(manifest,dict(version=version,platform=target))
    # Portable manifest names and bounded no-follow discovery check every descendant.
    # Rewalking all ancestors for every file adds seconds without another authority.
    _inventory(folder,manifest['files'])
    package=parse(_read(_path(folder,manifest['runtime']+'/package.json'),64000))
    if (not isinstance(package,dict) or package.get('name')!='@aikya/pi-runtime' or package.get('version')!=version
            or not isinstance(package.get('dependencies'),dict) or package['dependencies'].get('@earendil-works/pi-coding-agent')!=manifest['versions']['pi']):
        raise ValueError('Runtime package identity differs from activation')
    return dict(version=version,manifest_hash=hashlib.sha256(raw).hexdigest(),manifest=manifest,
                python=str(folder/manifest['python']),node=str(folder/manifest['node']),runtime=str(folder/manifest['runtime']))


def receipt(root,relative=CURRENT):
    root=state.safe(Path(root))
    if parse(_read(state.safe(root/'owner.json'),16000))!=state.OWNER:raise ValueError('Unowned application data is preserved')
    receipt=authentication.verify(root,read_record(root,relative,16000))
    fields={'schema','generated_by','version','platform','payload','manifest_hash'}
    if (not isinstance(receipt,dict) or set(receipt)!=fields or receipt['schema']!=1
            or receipt['generated_by']!='aikya-managed-terminal' or not isinstance(receipt['version'],str)
            or receipt['platform']!=host_platform()):raise ValueError('Unknown/incompatible managed terminal receipt')
    release_parts(receipt['version']);hash_id(receipt['manifest_hash'])
    if receipt['payload']!='terminal/versions/'+receipt['manifest_hash']:raise ValueError('Foreign managed terminal payload')
    return receipt


def resolve(root=None):
    root=state.safe(Path(root) if root is not None else options.app_root());record=receipt(root)
    folder=_path(root,record['payload']);value=inspect(folder,version=record['version'],target=record['platform'])
    if value['manifest_hash']!=record['manifest_hash']:raise ValueError('Managed manifest changed')
    return dict(root=str(root),version=record['version'],manifest_hash=record['manifest_hash'],
                **{key:value[key] for key in ('python','node','runtime')})
