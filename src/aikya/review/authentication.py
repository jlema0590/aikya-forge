"""Host-owned local signatures. Model tools cannot read or write this key."""
import hashlib
import hmac
import os
from aikya.code_index.policy import project_root, read_source
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from .contracts import encoded

KEY = '.aikya/pi/agent/review.key'


def key(root, *, create=False):
    root=project_root(root); path=safe_file(root,KEY)
    if not path.exists() and create:
        path.parent.mkdir(parents=True,exist_ok=True)
        with locked(path.parent):
            if not path.exists(): atomic_write(path,os.urandom(32),mode=0o600)
    if not path.is_file(): raise ValueError('Review authority is unavailable')
    stat=path.stat()
    if os.name!='nt' and (stat.st_mode & 0o077 or stat.st_uid!=os.getuid()): raise ValueError('Review key ownership is unsafe')
    raw=read_source(root,KEY,32)
    if len(raw)!=32: raise ValueError('Custom review authority is preserved')
    return raw


def seal(root, payload):
    return dict(payload=payload,mac=hmac.new(key(root),encoded(payload).encode(),hashlib.sha256).hexdigest())


def verify(root, value):
    if not isinstance(value,dict) or set(value)!={'payload','mac'} or not isinstance(value['mac'],str):
        raise ValueError('Unsigned review data has no host authority')
    signature=hmac.new(key(root),encoded(value['payload']).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,value['mac']): raise ValueError('Review signature mismatch')
    return value['payload']
