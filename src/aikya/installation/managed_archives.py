"""Verified bounded component data extraction; links are flattened, never executed."""
import hashlib
import io
from pathlib import Path
import posixpath
import stat
import tarfile
import zipfile
from aikya.core.package_paths import validate
from aikya.review.contracts import hash_id
from aikya.storage import write_new
from .bootstrap.state import safe
from .managed_runtime import _read

MAX_FILE=256000000
MAX_TOTAL=1500000000
MAX_MEMBERS=75000


def _name(value):
    if not isinstance(value,str) or not value or len(value)>512 or '\\' in value or value.startswith('/') or any(p in ('','.','..') for p in value.split('/')):
        raise ValueError('Unsafe component archive member')
    return value


def _selected(name,prefix,kind):
    name=_name(name)
    if prefix=='.':return name
    if name==prefix:
        if kind!='directory':raise ValueError('Component prefix must be a directory')
        return None
    if not name.startswith(prefix+'/'):raise ValueError('Archive has data outside the selected component')
    return name[len(prefix)+1:]


def _tar_rows(archive):
    rows=[]
    for member in archive:
        if len(rows)>=MAX_MEMBERS:raise ValueError('Component archive member bound exceeded')
        kind='directory' if member.isdir() else 'file' if member.type in (tarfile.REGTYPE,tarfile.AREGTYPE) else 'link' if member.issym() or member.islnk() else None
        if kind is None:raise ValueError('Unsupported component archive object')
        target=posixpath.normpath(posixpath.join(posixpath.dirname(member.name),member.linkname)) if member.issym() else member.linkname
        rows.append(dict(name=member.name,kind=kind,size=member.size,mode=member.mode,target=target,member=member))
    return rows


def _zip_rows(archive):
    infos=archive.infolist()
    if len(infos)>MAX_MEMBERS:raise ValueError('Component ZIP member bound exceeded')
    rows=[]
    for info in infos:
        mode=info.external_attr>>16
        if info.flag_bits&1 or stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR):raise ValueError('Encrypted/link/nonregular ZIP data is unsupported')
        kind='directory' if info.is_dir() else 'file'
        rows.append(dict(name=info.filename[:-1] if info.is_dir() else info.filename,kind=kind,size=info.file_size,mode=mode,target=None,member=info))
    return rows


def _plan(rows,prefix):
    table={};directories=[]
    for row in rows:
        relative=_selected(row['name'],prefix,row['kind'])
        if relative is None:continue
        if relative in table:raise ValueError('Duplicate component archive member')
        table[relative]=row
        if row['kind']=='directory':directories.append(relative)
        elif not 0<=row['size']<=MAX_FILE:raise ValueError('Component member exceeds its size bound')
    files=[name for name,row in table.items() if row['kind']!='directory']
    validate(files,directories=directories,max_files=50000,max_nodes=MAX_MEMBERS,max_length=512)
    def resolve(name,seen=()):
        if name not in table or name in seen or len(seen)>16:raise ValueError('Unknown or cyclic component link')
        row=table[name]
        if row['kind']=='file':return name
        if row['kind']!='link':raise ValueError('Directory links require separate review')
        target=_selected(row['target'],prefix,'file')
        return resolve(target,(*seen,name))
    resolved={name:resolve(name) for name in files}
    if sum(table[target]['size'] for target in resolved.values())>MAX_TOTAL:raise ValueError('Expanded component data exceeds its bound')
    return table,resolved


def _materialize(archive,destination,table,resolved,is_zip):
    hashes={};count=0
    # Original regular-file order avoids repeated backwards decompression of gzip.
    for name,row in table.items():
        if row['kind']!='file':continue
        stream=archive.open(row['member']) if is_zip else archive.extractfile(row['member'])
        if stream is None:raise ValueError('Missing component file data')
        with stream:raw=stream.read(row['size']+1)
        if len(raw)!=row['size']:raise ValueError('Truncated component file')
        target=safe(destination/name);target.parent.mkdir(parents=True,exist_ok=True);safe(target)
        write_new(target,raw,mode=0o700 if row['mode']&0o111 else 0o600);hashes[name]=hashlib.sha256(raw).hexdigest();count+=1
    for name,original in resolved.items():
        if name==original:continue
        raw=_read(safe(destination/original),table[original]['size'])
        if hashlib.sha256(raw).hexdigest()!=hashes[original]:raise ValueError('Component target changed before link materialization')
        target=safe(destination/name);target.parent.mkdir(parents=True,exist_ok=True);safe(target)
        write_new(target,raw,mode=0o700 if table[original]['mode']&0o111 else 0o600);count+=1
    return dict(files=count,bytes=sum(table[original]['size'] for original in resolved.values()),links_flattened=sum(name!=original for name,original in resolved.items()))


def extract(archive,destination,expected_hash,prefix,*,merge=False):
    hash_id(expected_hash)
    if prefix!='.':_name(prefix)
    if type(merge) is not bool:raise ValueError('Invalid component staging merge selection')
    destination=safe(Path(destination).absolute())
    if destination.exists() and (not merge or not destination.is_dir()):raise ValueError('Existing component output is preserved')
    raw=_read(safe(Path(archive)),MAX_FILE)
    if hashlib.sha256(raw).hexdigest()!=expected_hash:raise ValueError('Component archive checksum changed')
    is_zip=zipfile.is_zipfile(io.BytesIO(raw))
    try:
        container=zipfile.ZipFile(io.BytesIO(raw)) if is_zip else tarfile.open(fileobj=io.BytesIO(raw),mode='r:*')
        with container:
            rows=_zip_rows(container) if is_zip else _tar_rows(container)
            table,resolved=_plan(rows,prefix)
            for name in resolved:
                target=safe(destination/name)
                if target.exists():raise ValueError('Existing component file is preserved')
                for parent in target.parents:
                    if parent==destination:break
                    if parent.exists() and not parent.is_dir():raise ValueError('Existing component parent is not a directory')
            destination.mkdir(parents=True,exist_ok=merge)
            return _materialize(container,destination,table,resolved,is_zip)
    except (zipfile.BadZipFile,tarfile.TarError,OSError) as error:raise ValueError('Component archive unavailable or incomplete; partial data is preserved') from error
