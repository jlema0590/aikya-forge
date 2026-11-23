"""Conservative Linux ABI identification without executing helpers from PATH."""
import os
from pathlib import Path
import platform
import re
import stat
import struct
import sys
from contextlib import contextmanager


@contextmanager
def _image(path):
    fd=os.open(Path(path).resolve(strict=True),os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0))
    with os.fdopen(fd,'rb') as stream:
        record=os.fstat(stream.fileno())
        if not stat.S_ISREG(record.st_mode) or record.st_size>256000000:raise ValueError('Invalid native image')
        yield stream,record.st_size


def _bytes(path,limit):
    with _image(path) as (stream,_):return stream.read(limit)


def _interpreter(path):
    with _image(path) as (stream,total):
        raw=stream.read(65536)
        if len(raw)<64 or raw[:6]!=b'\x7fELF\x02\x01':raise ValueError('Unknown active ELF image')
        offset=struct.unpack_from('<Q',raw,32)[0];size=struct.unpack_from('<H',raw,54)[0];count=struct.unpack_from('<H',raw,56)[0]
        if size!=56 or not 1<=count<=128 or offset<64 or offset+size*count>len(raw):raise ValueError('Invalid ELF program headers')
        for index in range(count):
            start=offset+size*index
            if struct.unpack_from('<I',raw,start)[0]!=3:continue
            location=struct.unpack_from('<Q',raw,start+8)[0];length=struct.unpack_from('<Q',raw,start+32)[0]
            if not 2<=length<=256 or location+length>total:raise ValueError('Invalid ELF loader bounds')
            stream.seek(location);value=stream.read(length)
            if len(value)!=length or not value.endswith(b'\0') or b'\0' in value[:-1]:raise ValueError('Invalid ELF loader path')
            return value[:-1].decode('ascii')
    return None


def _system_musl():
    architecture={'x86_64':'x86_64','amd64':'x86_64','aarch64':'aarch64','arm64':'aarch64'}.get(platform.machine().lower())
    if architecture is None:return False
    candidate=Path('/lib/ld-musl-'+architecture+'.so.1')
    if not candidate.exists():return False
    resolved=candidate.resolve(strict=True)
    if not any(resolved.is_relative_to(Path(folder).resolve()) for folder in ('/lib','/usr/lib')):return False
    raw=_bytes(resolved,2000000)
    machine=62 if architecture=='x86_64' else 183
    return (len(raw)>=64 and raw[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',raw,18)[0]==machine
            and b'musl libc' in raw)


def linux_runtime():
    reported=platform.libc_ver()[0].lower()
    if reported in ('glibc','musl'):return reported
    try:
        loader=_interpreter(sys.executable)
        if loader and re.fullmatch(r'/(?:usr/)?lib/ld-musl-(?:x86_64|aarch64)\.so\.1',loader):return 'musl'
        if loader is None and _system_musl():return 'musl'  # A static bundled Python has no PT_INTERP.
    except (OSError,ValueError,UnicodeError,struct.error):pass
    return 'unknown'
