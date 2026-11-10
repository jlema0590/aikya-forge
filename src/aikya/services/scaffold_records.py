"""Signed staged-run ownership, source freshness and bounded generator output."""
import os
from pathlib import Path
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import identifier,encoded,parse,digest
from aikya.storage import atomic_write
from aikya.documentation.language import resolve
from .documentation_inputs import profile
from .generation_inputs import sha


def relative(run_id):return '.aikya/pi/scaffold/'+identifier(run_id)


def path(root,run_id,name):return safe_file(root,relative(run_id)+'/'+name)


def source(root,session):
    p=profile(root);workflow=None
    from .task_binding import candidate_revision,PATH
    if p['methodology']=='sdd':
        try:selected=authentication.verify(root,parse(read_source(root,PATH,16384)))
        except OSError as exc:raise ValueError('Select a current approved SDD task') from exc
        scope=selected.get('files') if isinstance(selected,dict) else None
        if not isinstance(scope,list) or not scope:raise ValueError('Select a current approved SDD task')
        workflow=candidate_revision(root,scope,session)
    else:
        from .odd_binding import existing,current
        if existing(root) is not None:_,workflow=current(root,session)
    return dict(project=identity(root),session_id=identifier(session),profile_hash=digest(profile(root)),language=resolve(root),
                workflow_revision=workflow,source_revision=freeze_candidate(root,'pi-scaffold',['aikya/docs/overview.md'],session_id=session)['id'])


def save(root,run_id,record):
    target=path(root,run_id,'record.json');target.parent.mkdir(parents=True,exist_ok=True)
    authentication.key(root,create=True)
    atomic_write(target,encoded(authentication.seal(root,record))+'\n',mode=0o600)


def load(root,run_id,session,*,current=True):
    value=authentication.verify(root,parse(read_source(root,relative(run_id)+'/record.json',60000)))
    origin=value.get('source',{}) if isinstance(value,dict) else {}
    if (not isinstance(value,dict) or value.get('run_id')!=run_id or origin.get('project')!=identity(root)
            or origin.get('session_id')!=identifier(session) or (current and origin!=source(root,session))):
        raise ValueError('Staged generator source, profile, locale or session changed')
    return value


def workspace(root,run_id,recipe):
    name=recipe.get('workspace_name')
    if name is not None:
        import re
        if not isinstance(name,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,79}',name):raise ValueError('Invalid named generator workspace')
    return path(root,run_id,'workspace'+('/'+name if name else '')+'/.aikya-stage-marker').parent


def outputs(root,run_id,manifest=None,*,recipe=None):
    stage=workspace(root,run_id,recipe or {});files={};rows=[];total=0;entries=0
    if not stage.is_dir():raise ValueError('Generator workspace is missing')
    for base,dirs,names in os.walk(stage,followlinks=False):
        dirs.sort();names.sort()
        for name in [*dirs,*names]:
            item=Path(base)/name
            if item.is_symlink():raise ValueError('Generator links are not copied')
        dirs[:]=[name for name in dirs if name!='.git']
        for name in dirs:safe_file(root,(Path(base)/name/'.aikya-stage-marker').relative_to(root).as_posix())
        entries+=len(dirs)+len(names)
        if entries>400:raise ValueError('Generator directory tree exceeds its bound')
        for name in names:
            target=Path(base)/name;relative_name=target.relative_to(stage).as_posix()
            raw=read_source(root,target.relative_to(root).as_posix(),1000000);total+=len(raw)
            if total>5000000 or len(files)>=100:raise ValueError('Split generated output into a smaller project')
            files[relative_name]=raw;rows.append(dict(path=relative_name,bytes=len(raw),sha256=sha(raw)))
    if not files:raise ValueError('Generator produced no regular files')
    if manifest is not None and rows!=manifest:raise ValueError('Staged output changed after execution')
    return files,rows


def cancellation(root,run_id,session):
    target=path(root,run_id,'cancel.json')
    def cancelled():
        try:
            if not target.exists():return False
            value=authentication.verify(root,parse(read_source(root,target.relative_to(root).as_posix(),4096)))
            if value!=dict(run_id=run_id,session_id=session):raise ValueError('Foreign cancellation')
            return True
        except (ValueError,OSError):return True
    return cancelled
