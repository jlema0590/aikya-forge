"""Small signed application records shared by native installation operations."""
from pathlib import Path
from aikya.review import authentication
from aikya.review.contracts import encoded,parse
from aikya.storage import atomic_write
from .bootstrap import state
from .managed_runtime import _read


def root(path):
    path=state.safe(Path(path).absolute())
    if path.exists() and (not path.is_dir() or any(path.iterdir())):
        if parse(_read(state.safe(path/'owner.json'),16000))!=state.OWNER:raise ValueError('Unowned application data is preserved')
    return path


def read(root,relative):
    path=state.safe(root/relative)
    return authentication.verify(root,parse(_read(path,2000000))) if path.exists() else None


def save(root,relative,value):
    atomic_write(state.safe(root/relative),encoded(authentication.seal(root,value))+'\n',mode=0o600)
