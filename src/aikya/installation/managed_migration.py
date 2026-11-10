"""Read-only v7 identity plus exact administrative backups; no session conversion."""
import hashlib
from pathlib import Path
import re
from aikya.review.contracts import parse
from aikya.storage import write_new
from .bootstrap import download,state
from .managed_runtime import _read


FILES=('current.json','launchers.json','user-path.json')
DIRECTORIES=('receipts','components','references')
MAX_RECORD=16_000_000
MAX_TOTAL=64_000_000


def preview(root):
    root=state.safe(Path(root).absolute());current=state.safe(root/'current.json')
    if not current.exists():return None
    value=parse(_read(current,16000))
    if not isinstance(value,dict) or set(value)!={'version','environment','python'}:raise ValueError('Customized legacy installation identity requires review')
    version=download.validate_version(value['version'])
    if not version.startswith('7.') or not all(isinstance(value[k],str) for k in ('environment','python')):raise ValueError('Unknown legacy installation identity')
    environment=state.safe(Path(value['environment']));python=Path(value['python'])
    if not environment.is_absolute() or not environment.is_relative_to(root/'versions') or not environment.is_dir() or not python.is_relative_to(environment):raise ValueError('Foreign legacy interpreter identity is preserved')
    selected=[name for name in FILES if state.safe(root/name).exists()];total=0;hashes={}
    for directory in DIRECTORIES:
        folder=state.safe(root/directory)
        if not folder.exists():continue
        if not folder.is_dir():raise ValueError('Unknown legacy metadata container')
        for path in folder.iterdir():
            state.safe(path)
            if not re.fullmatch('[a-f0-9]{64}\\.json',path.name) or not path.is_file():raise ValueError('Unknown legacy metadata is preserved')
            selected.append(path.relative_to(root).as_posix())
            if len(selected)>500:raise ValueError('Legacy metadata inventory exceeds its bound')
    for name in sorted(selected):
        raw=_read(state.safe(root/name),MAX_RECORD);total+=len(raw)
        if total>MAX_TOTAL:raise ValueError('Legacy metadata backup exceeds its bound')
        hashes[name]=hashlib.sha256(raw).hexdigest()
    return dict(schema=1,version=version,environment=str(environment),files=hashes,
                sessions='retained in their original client; not converted to Pi',project_profiles='separate explicit migration',writes=False)


def backup(root,expected,destination):
    if preview(root)!=expected:raise ValueError('Legacy installation changed before backup')
    if expected is None:return
    captured={name:_read(state.safe(root/name),MAX_RECORD) for name in expected['files']}
    if any(hashlib.sha256(raw).hexdigest()!=expected['files'][name] for name,raw in captured.items()):raise ValueError('Legacy metadata changed during backup')
    for name,raw in captured.items():
        path=state.safe(Path(destination)/name);path.parent.mkdir(parents=True,exist_ok=True);write_new(path,raw,mode=0o600)
