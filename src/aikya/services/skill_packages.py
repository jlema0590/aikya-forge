"""One immutable package compositor for selected-project and inert global skill data."""
import io
import zipfile
from aikya.code_index.policy import read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.review import authentication
from aikya.review.contracts import encoded,read_record,digest
from aikya.storage import write_new
from .skill_source import sha,_regular_files


def archive(data):
    value=io.BytesIO()
    with zipfile.ZipFile(value,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for path,raw in sorted(data['raws'].items()):bundle.writestr(path,raw)
    return value.getvalue()


def preflight(root,destination,data):
    for name in data['prepared']:safe_file(root,destination+'/files/'+name)
    for name in ('original.zip','manifest.json'):safe_file(root,destination+'/'+name)


def write(root,destination,data):
    preflight(root,destination,data)
    for relative,raw in data['prepared'].items():
        name=destination+'/files/'+relative;target=safe_file(root,name)
        target.parent.mkdir(parents=True,exist_ok=True);safe_file(root,name)
        write_new(target,raw,mode=0o600)
        if sha(read_source(root,name,1001000))!=data['installed'][relative]:raise ValueError('Skill package readback failed')
    zipped=archive(data)
    write_new(safe_file(root,destination+'/original.zip'),zipped,mode=0o600)
    return zipped


def manifest(root,destination,data,zipped):
    value={k:data[k] for k in ('name','description','source','source_hash','files','installed','ignored_fields')}
    value.update(schema=1,project=identity(root),package=destination,archive_hash=sha(zipped))
    write_new(safe_file(root,destination+'/manifest.json'),encoded(authentication.seal(root,value))+'\n',mode=0o600)
    return value


def read(root,destination):
    value=authentication.verify(root,read_record(root,destination+'/manifest.json',32000))
    fields={'schema','project','package','name','description','source','source_hash','files','installed','ignored_fields','archive_hash'}
    if (not isinstance(value,dict) or set(value)!=fields or value['schema']!=1 or value['project']!=identity(root)
            or value['package']!=destination or not isinstance(value['files'],dict) or not isinstance(value['installed'],dict)
            or set(value['files'])!=set(value['installed']) or not 1<=len(value['files'])<=80
            or value['source_hash']!=digest(value['files'])):raise ValueError('Unknown immutable skill manifest is preserved')
    folder=safe_file(root,destination+'/files/.probe').parent
    members={p.relative_to(folder).as_posix() for p in _regular_files(folder)}
    if members!=set(value['installed']):raise ValueError('Unlisted or missing skill package resource')
    prepared={p:read_source(root,destination+'/files/'+p,1001000) for p in members}
    if any(sha(raw)!=value['installed'][p] for p,raw in prepared.items()):raise ValueError('Skill package content changed')
    zipped=read_source(root,destination+'/original.zip',5100000)
    if sha(zipped)!=value['archive_hash']:raise ValueError('Original skill archive changed')
    with zipfile.ZipFile(io.BytesIO(zipped)) as bundle:
        infos=bundle.infolist()
        if len(infos)!=len(value['files']) or {i.filename for i in infos}!=set(value['files']):raise ValueError('Unknown archived skill members')
        if any(i.file_size>1000000 or i.is_dir() for i in infos) or sum(i.file_size for i in infos)>5000000:raise ValueError('Skill archive exceeds its read bound')
        raws={i.filename:bundle.read(i) for i in infos}
    if any(sha(raw)!=value['files'][p] for p,raw in raws.items()):raise ValueError('Original skill bytes differ')
    return {**{k:value[k] for k in ('name','description','source','source_hash','files','installed','ignored_fields')},
            'body':raws['SKILL.md'].decode('utf8').replace('\r\n','\n').replace('\r','\n'),'raws':raws,'prepared':prepared}
