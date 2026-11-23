"""Trusted native selected-skill installation and bounded immutable resource reads."""
from pathlib import Path
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.layout import content,stamp,generated,index_paths,write_document
from aikya.documentation.language import resolve as language
from aikya.review import authentication
from aikya.review.contracts import encoded,digest,read_record
from aikya.storage import atomic_write
from .skill_source import snapshot,sha
from .skill_sources import capture as capture_source
from . import skill_packages as packages

REGISTRY='.aikya/pi/skills/registry.json'
COMPARISON='aikya/docs/tools/skill-comparison.md'
MARKER='<!-- AIKYA PI SELECTED SKILLS -->'


def _registry(root):
    path=safe_file(root,REGISTRY)
    if not path.exists():return None
    value=authentication.verify(root,read_record(root,REGISTRY,65536))
    if (not isinstance(value,dict) or set(value)!={'schema','project','skills','comparison_hash','language'}
            or value['schema']!=1 or value['project']!=identity(root) or not isinstance(value['skills'],dict)
            or len(value['skills'])>20 or value['language'] not in ('en','es')):
        raise ValueError('Unknown native skill registry is preserved')
    return value


def _comparison(root,registry):
    path=safe_file(root,COMPARISON)
    if not path.exists():
        if registry:raise ValueError('Managed skill comparison is missing')
        return None
    raw=read_source(root,COMPARISON,64000)
    if not generated(raw.decode('utf8')):raise ValueError('Custom comparison is preserved')
    if registry:
        if sha(raw)!=registry['comparison_hash'] or raw.decode('utf8').count(MARKER)!=1:
            raise ValueError('Changed comparison is preserved')
    elif MARKER in raw.decode('utf8'):raise ValueError('Unknown native comparison is preserved')
    return raw


def _capture(source,root=None):
    return snapshot(source) if isinstance(source,str) else capture_source(source,root)


def make_entry(destination,data,manifest):
    base=destination+'/files'
    entry=dict(name=data['name'],description=data['description'],source=data['source'],source_hash=data['source_hash'],
               files=data['installed'],base=base,file=base+'/SKILL.md',activation='explicit_only')
    if manifest is not None:entry['package_manifest_hash']=digest(manifest)
    return entry


def change_preview(root,**arguments):
    from .skill_project_changes import preview
    return preview(root,**arguments)


def recovery_preview(root):
    from .skill_project_changes import recovery_preview as preview
    return preview(root)


def recover(root,plan,approved=False):
    from .skill_project_changes import recover as apply
    return apply(root,plan,approved)


def preview(root,source):
    from .skill_project_changes import guard
    root=project_root(root);guard(root);data=_capture(source,root);registry=_registry(root);index_paths(root)
    lang=language(root);comparison=_comparison(root,registry)
    if registry and (data['name'] in registry['skills'] or len(registry['skills'])>=20 or registry['language']!=lang):
        raise ValueError('Existing skills and language choices require explicit reviewed migration')
    destination='.aikya/pi/skills/packages/'+data['source_hash']+'/'+data['name']
    packages.preflight(root,destination,data)
    if safe_file(root,destination).exists():raise ValueError('Existing skill package is preserved')
    draft=make_entry(destination,data,None);draft['package_manifest_hash']='0'*64
    entries={**(registry['skills'] if registry else {}),data['name']:draft}
    body=_render_comparison(comparison,entries,lang)
    value=dict(schema=1,project=identity(root),skills=entries,comparison_hash=sha(body.encode()),language=lang)
    if len(encoded(value).encode())>64000:raise ValueError('Project skill registry exceeds its read bound')
    operation=digest(dict(project=identity(root),source=data['source_hash'],registry=digest(registry)))
    reservation='.aikya/pi/skills/operations/'+operation+'.json'
    if safe_file(root,reservation).exists():raise ValueError('Skill operation exists; reconcile without replay')
    plan=dict(schema=1,project=identity(root),source=dict(source) if isinstance(source,dict) else data['source'],source_hash=data['source_hash'],destination=destination,
              registry_before=digest(registry),comparison_before=sha(comparison) if comparison is not None else None,
              language=lang,reservation=reservation)
    from .skill_project_changes import audit_available
    audit_available(root,plan)
    review=dict(name=data['name'],description=data['description'],content=data['body'],files=data['files'],
                ignored_fields=data['ignored_fields'],activation='explicit_only',execution='none',
                paths=[destination,COMPARISON,'aikya/docs/operations/skill-install-'+operation+'.md','aikya/docs/indice.md'])
    if len(encoded(dict(plan=plan,review=review)).encode())>18000:raise ValueError('Skill preview exceeds its bounded review packet')
    return dict(plan=plan,review=review)


def _render_comparison(previous,entries,lang):
    prefix=content(previous.decode('utf8')).split(MARKER,1)[0].rstrip() if previous else ''
    title='Skills Pi elegidas' if lang=='es' else 'Selected Pi skills'
    rows=['| Skill | Source SHA-256 | Activation |','|---|---|---|']
    for name,entry in sorted(entries.items()):rows.append('| '+name+' | '+entry['source_hash']+' | explicit |')
    return stamp(prefix+'\n\n'+MARKER+'\n## '+title+'\n\n'+'\n'.join(rows))


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native skill installation confirmation required')
    if isinstance(plan,dict) and plan.get('action') in ('update','rollback'):
        from .skill_project_changes import apply as change
        return change(root,plan,approved)
    root=project_root(root)
    keys={'schema','project','source','source_hash','destination','registry_before','comparison_before','language','reservation'}
    if not isinstance(plan,dict) or set(plan)!=keys or preview(root,plan['source'])['plan']!=plan:
        raise ValueError('Skill preview is stale')
    from .skill_project_changes import PENDING,_finish
    folder=safe_file(root,'.aikya/pi/skills/.lock').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        if preview(root,plan['source'])['plan']!=plan:raise ValueError('Skill source or ownership changed')
        data=_capture(plan['source'],root);registry=_registry(root);previous=_comparison(root,registry)
        if data['source_hash']!=plan['source_hash']:raise ValueError('Skill changed after final preview')
        authentication.key(root,create=True)
        pending=dict(schema=1,project=identity(root),status='pending',plan=plan)
        operation=safe_file(root,plan['reservation'])
        atomic_write(operation,encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        atomic_write(safe_file(root,PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        base=plan['destination']+'/files/'
        zipped=packages.write(root,plan['destination'],data)
        manifest=packages.manifest(root,plan['destination'],data,zipped)
        entries=dict(registry['skills']) if registry else {}
        entry=make_entry(plan['destination'],data,manifest)
        entries[data['name']]=entry
        body=_render_comparison(previous,entries,plan['language'])
        operation_id=Path(plan['reservation']).stem;es=plan['language']=='es'
        audit=stamp(('# Instalación de skill Pi' if es else '# Pi skill installation')+'\n\n'
            +data['name']+('\n\nSHA-256 de origen: `' if es else '\n\nSource SHA-256: `')+data['source_hash']+'`.\n\n'
            +('Paquete local revisado; sin ejecutar scripts/hooks ni instalar dependencias. Activación explícita.' if es else
              'Reviewed local package; no scripts/hooks executed or dependencies installed. Explicit activation.'))
        value=dict(schema=1,project=identity(root),skills=entries,comparison_hash=sha(body.encode()),language=plan['language'])
        pending.update(next_registry=value,comparison=body,audit=audit)
        atomic_write(safe_file(root,PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        return _finish(root,pending)


def _entry(root,name):
    registry=_registry(root)
    if not registry or name not in registry['skills']:raise ValueError('No approved skill with this name')
    entry=registry['skills'][name]
    required={'name','description','source','source_hash','files','base','file','activation'}
    if not isinstance(entry,dict) or set(entry) not in (required,required|{'package_manifest_hash'}) or entry['name']!=name or not isinstance(entry['files'],dict):
        raise ValueError('Invalid skill entry')
    expected='.aikya/pi/skills/packages/'+entry['source_hash']+'/'+name+'/files'
    if entry['base']!=expected or entry['file']!=expected+'/SKILL.md' or entry['activation']!='explicit_only':
        raise ValueError('Foreign skill entry')
    if 'package_manifest_hash' in entry:
        manifest=authentication.verify(root,read_record(root,expected.removesuffix('/files')+'/manifest.json',32000))
        data=packages.read(root,expected.removesuffix('/files'))
        if (digest(manifest)!=entry['package_manifest_hash'] or data['source_hash']!=entry['source_hash']
                or data['installed']!=entry['files'] or data['source']!=entry['source'] or data['name']!=name):
            raise ValueError('Selected immutable skill package changed')
    raw=read_source(root,entry['file'],10000)
    if sha(raw)!=entry['files'].get('SKILL.md'):raise ValueError('Installed skill changed; activation refused')
    return entry


def verify(root,name):
    root=project_root(root);entry=_entry(root,name)
    raw=read_source(root,entry['file'],10000)
    body=raw.decode('utf8').split('---\n',2)[2].strip()
    return {**{k:v for k,v in entry.items() if k in ('name','description','file','base','source_hash')},
            'file_hash':entry['files']['SKILL.md'],'body_hash':sha(body.encode())}


def resolve(root):
    root=project_root(root);registry=_registry(root)
    return dict(skills=[verify(root,name) for name in sorted(registry['skills'])] if registry else [])


def status(root,offset=0):
    root=project_root(root)
    if type(offset) is not int or not 0<=offset<=50:raise ValueError('Invalid skill page offset')
    registry=_registry(root);names=sorted(registry['skills']) if registry else []
    values=[]
    for name in names[offset:offset+20]:
        entry=_entry(root,name);values.append(dict(name=name,source_hash=entry['source_hash'],activation='explicit_only',execution='not_observed'))
    from .skill_project_changes import PENDING
    return dict(skills=values,next_offset=offset+20 if offset+20<len(names) else None,scope='project',
                status='pending' if safe_file(root,PENDING).exists() else 'available')


def read_resource(root,name,path,offset=0,max_chars=6000):
    root=project_root(root);entry=_entry(root,name)
    if type(offset) is not int or offset<0 or type(max_chars) is not int or not 512<=max_chars<=6000:
        raise ValueError('Invalid skill resource window')
    if path not in entry['files']:raise ValueError('Resource is not in the approved skill manifest')
    relative=entry['base']+'/'+path;raw=read_source(root,relative,1001000)
    if sha(raw)!=entry['files'][path]:raise ValueError('Approved resource changed')
    text=raw.decode('utf8')
    if offset>len(text):raise ValueError('Resource offset is outside its content')
    end=min(len(text),offset+max_chars)
    return dict(mode='approved_skill_resource',name=name,path=path,sha256=sha(raw),content=text[offset:end],
                offset=offset,next_offset=end if end<len(text) else None,execution='none')
