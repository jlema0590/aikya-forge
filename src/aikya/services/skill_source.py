"""Bounded local Agent Skill inspection; imported code is never executed."""
import hashlib
import json
import os
from pathlib import Path
from aikya.code_index.policy import excluded,read_source
from aikya.documentation.layout import content,stamp
from aikya.review.contracts import digest,encoded
from aikya.tools.skills_lint import inspect_text,metadata_fields
from aikya.catalogs.skill_paths import validate as validate_paths


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _regular_files(folder):
    pending=[folder];examined=0
    while pending:
        current=pending.pop()
        if current.is_symlink() or (hasattr(current,'is_junction') and current.is_junction()):raise ValueError('Unsafe skill directory')
        # Do not suppress unreadable subdirectories or materialize an unbounded tree.
        with os.scandir(current) as entries:
            for entry in entries:
                examined+=1
                if examined>160:raise ValueError('Skill discovery entry budget exceeded')
                path=Path(entry.path);relative=path.relative_to(folder).as_posix()
                if entry.is_symlink() or excluded(relative) or len(relative)>160 or (hasattr(path,'is_junction') and path.is_junction()):
                    raise ValueError('Unsafe skill package entry')
                if entry.is_dir(follow_symlinks=False):pending.append(path)
                elif entry.is_file(follow_symlinks=False):yield path
                else:raise ValueError('Unsupported skill package entry')


def from_bytes(raws,source,expected_name=None):
    """Compose the same reviewed package from local or verified remote source bytes."""
    if not isinstance(source,str) or not 1<=len(source)<=2000 or not isinstance(raws,dict):raise ValueError('Explicit bounded skill source required')
    validate_paths(raws)
    if any(not isinstance(raw,bytes) or len(raw)>1000000 for raw in raws.values()) or sum(map(len,raws.values()))>5000000:
        raise ValueError('Skill package exceeds its review bound')
    files={name:sha(raw) for name,raw in raws.items()}
    if len(encoded(files).encode())>8000:raise ValueError('Skill resource manifest exceeds its review bound')
    raw=raws.get('SKILL.md')
    if raw is None or len(raw)>8000:raise ValueError('A bounded SKILL.md is required')
    text=raw.decode('utf8').replace('\r\n','\n').replace('\r','\n')
    front,body=text.split('---\n',2)[1:]
    fields=metadata_fields(front)
    name=fields.get('name','');description=fields.get('description','')
    if inspect_text(text,expected_name or name,source):raise ValueError('Unsupported Agent Skill metadata')
    if name.startswith('aikya-') or len(description)>300 or len(description.encode())>800:
        raise ValueError('Reserved name or oversized skill description')
    if len(body.encode())>6000 or not body.strip():raise ValueError('Split skill instructions before native activation')
    normalized='---\nname: '+json.dumps(name)+'\ndescription: '+json.dumps(description)+'\ndisable-model-invocation: true\n---\n'+content(body)
    installed={}
    for path,value in raws.items():
        installed[path]=(stamp(normalized).encode() if path=='SKILL.md' else stamp(value.decode('utf8')).encode() if Path(path).suffix.lower()=='.md' else value)
    return dict(source=source,name=name,description=description,files=files,source_hash=digest(files),
                installed={p:sha(v) for p,v in installed.items()},ignored_fields=sorted(set(fields)-{'name','description'}),
                body=text,raws=raws,prepared=installed)



def snapshot(source):
    if not isinstance(source,str) or len(source)>2000:raise ValueError('Explicit local skill directory required')
    folder=Path(source)
    if not folder.is_absolute() or folder.is_symlink():raise ValueError('Select a regular absolute skill directory')
    folder=folder.resolve(strict=True)
    if not folder.is_dir():raise ValueError('Skill source must be a directory')
    raws={};total=0
    for path in _regular_files(folder):
        relative=path.relative_to(folder).as_posix()
        raw=read_source(folder,relative,1000000);total+=len(raw)
        if total>5000000 or len(raws)>=80:raise ValueError('Skill package exceeds its review bound')
        raws[relative]=raw
    return from_bytes(raws,str(folder),expected_name=folder.name)
