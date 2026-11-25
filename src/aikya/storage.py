"""Shared durable replacement for authoritative documents and checkpoints."""
from __future__ import annotations
import os
import tempfile
import time
from pathlib import Path


def _replace_prepared(source,path):
    # Open readers/antivirus can briefly deny rename on Windows. Retry only the
    # same fsynced sibling, never the caller's effects or admission operation.
    deadline=time.monotonic()+.25
    while True:
        if path.is_symlink() or path.parent.is_symlink():
            raise ValueError('Symlinked durable destination')
        try:
            os.replace(source,path)
            return
        except OSError as error:
            remaining=deadline-time.monotonic()
            if getattr(error,'winerror',None) not in (5,32,33) or remaining<=0:
                raise
            time.sleep(min(.01,remaining))


def atomic_write(path, raw, *, mode=None):
    path=Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('Symlinked durable destination')
    path.parent.mkdir(parents=True,exist_ok=True)
    payload=raw.encode('utf8') if isinstance(raw,str) else raw
    fd,name=tempfile.mkstemp(prefix='.aikya-durable-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            if mode is not None and hasattr(os,'fchmod'):os.fchmod(stream.fileno(),mode)
            stream.write(payload);stream.flush();os.fsync(stream.fileno())
        _replace_prepared(name,path)
        if hasattr(os,'O_DIRECTORY'):
            directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
    finally:
        if os.path.exists(name):os.unlink(name)


def write_new(path, raw, *, mode=0o666):
    """Create exclusively; never replace a file introduced after a prior inspection."""
    path=Path(path)
    if path.is_symlink() or path.parent.is_symlink():raise ValueError('Symlinked exclusive destination')
    payload=raw.encode('utf8') if isinstance(raw,str) else raw
    handle=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),mode)
    with os.fdopen(handle,'wb') as stream:
        stream.write(payload);stream.flush();os.fsync(stream.fileno())
