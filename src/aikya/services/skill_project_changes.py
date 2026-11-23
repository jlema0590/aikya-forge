"""Reviewed project skill version changes and recovery of complete, observed effects."""
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation.layout import index_paths,stamp,update_index
from aikya.review import authentication
from aikya.review.contracts import encoded,digest,read_record,hash_id,identifier
from aikya.storage import write_new
from . import selected_skills as selected,skill_packages as packages
from .skill_source import sha

PENDING='.aikya/pi/skills/pending.json'
HISTORY='.aikya/pi/skills/history/'


def guard(root):
    if safe_file(root,PENDING).exists():raise ValueError('Uncertain skill version change requires reviewed reconciliation')


def _history(root,name,version):
    identifier(name);hash_id(version)
    return HISTORY+name+'/'+version+'.json'


def _retained(root,name,version):
    entry=authentication.verify(root,read_record(root,_history(root,name,version),32000))
    if entry.get('name')!=name or entry.get('source_hash')!=version or 'package_manifest_hash' not in entry:raise ValueError('Unknown retained project version')
    data=packages.read(root,entry['base'].removesuffix('/files'))
    manifest=authentication.verify(root,read_record(root,entry['base'].removesuffix('/files')+'/manifest.json',32000))
    if digest(manifest)!=entry['package_manifest_hash'] or data['installed']!=entry['files'] or data['source']!=entry['source']:raise ValueError('Retained project package changed')
    return entry,data


def preview(root,action,source=None,name=None,source_hash=None):
    root=project_root(root);guard(root);registry=selected._registry(root);index_paths(root)
    if action not in ('update','rollback'):raise ValueError('Unknown project skill version action')
    if action=='rollback':
        if source is not None:raise ValueError('Rollback requires a retained version')
        entry,data=_retained(root,name,source_hash);selection=None
    else:
        if name is not None or source_hash is not None:raise ValueError('Choose an explicit update source')
        data=selected._capture(source,root);name=data['name'];source_hash=data['source_hash'];selection=dict(source) if isinstance(source,dict) else data['source']
    old=selected._entry(root,name)
    if 'package_manifest_hash' not in old:raise ValueError('Legacy package needs reviewed manifest migration before update')
    if old['source_hash']==source_hash:raise ValueError('Project skill version is unchanged')
    prior=selected._comparison(root,registry)
    folder=safe_file(root,_history(root,name,source_hash)).parent
    if folder.exists():
        versions=list(folder.iterdir())
        if len(versions)>10 or any(p.is_symlink() or not p.is_file() or p.suffix!='.json' for p in versions):raise ValueError('Unknown or excessive retained version metadata')
        if len(versions)>=10 and not safe_file(root,_history(root,name,source_hash)).exists():raise ValueError('Retained version bound reached')
    destination='.aikya/pi/skills/packages/'+source_hash+'/'+name
    packages.preflight(root,destination,data)
    reuse=safe_file(root,destination+'/.probe').parent.exists()
    if reuse:
        recorded,known=_retained(root,name,source_hash)
        if known['source']!=data['source'] or known['files']!=data['files']:raise ValueError('Retained source identity differs')
    plan=dict(schema=1,project=identity(root),action=action,source=selection,name=name,source_hash=source_hash,
              destination=destination,reuse=reuse,registry_before=digest(registry),comparison_before=sha(prior),language=registry['language'])
    audit_available(root,plan)
    review=dict(scope='project',action=action,name=name,before=old['source_hash'],after=source_hash,source=data['source'],
                description=data['description'],content=data['body'],files=data['files'],ignored_fields=data['ignored_fields'],
                activation='explicit_only',restart_required=True,execution='none')
    if len(encoded(dict(plan=plan,review=review)).encode())>18000:raise ValueError('Project skill review exceeds its bound')
    return dict(plan=plan,review=review)


def _repeat(root,plan):
    if not isinstance(plan,dict):raise ValueError('Invalid project version plan')
    if plan.get('action')=='rollback':value=preview(root,'rollback',name=plan['name'],source_hash=plan['source_hash'])
    else:value=preview(root,'update',source=plan['source'])
    if value['plan']!=plan:raise ValueError('Project skill version preview changed')


def _remember(root,entry):
    path=safe_file(root,_history(root,entry['name'],entry['source_hash']))
    if path.exists():
        if authentication.verify(root,read_record(root,path.relative_to(root).as_posix(),32000))!=entry:raise ValueError('Retained version metadata differs')
    else:
        path.parent.mkdir(parents=True,exist_ok=True);safe_file(root,path.relative_to(root).as_posix())
        write_new(path,encoded(authentication.seal(root,entry))+'\n',mode=0o600)


def _audit_path(plan):
    if 'reservation' in plan:
        return 'aikya/docs/operations/skill-install-'+plan['reservation'].rsplit('/',1)[1].removesuffix('.json')+'.md'
    return 'aikya/docs/operations/skill-change-'+digest(plan)+'.md'


def audit_available(root,plan):
    audit=_audit_path(plan)
    if not safe_file(root,audit).exists():return
    operation=plan.get('reservation','.aikya/pi/skills/operations/'+digest(plan)+'.json')
    previous=authentication.verify(root,read_record(root,operation,200000))
    if (previous.get('status')!='completed' or previous.get('plan')!=plan or not isinstance(previous.get('audit'),str)
            or read_source(root,audit,64000)!=previous['audit'].encode()):raise ValueError('Unknown or customized generated skill audit is preserved')


def _projections(root,pending):
    index_paths(root);audit=_audit_path(pending['plan'])
    if safe_file(root,audit).exists() and read_source(root,audit,64000)!=pending['audit'].encode():raise ValueError('Customized skill audit is preserved')
    current=read_source(root,selected.COMPARISON,64000) if safe_file(root,selected.COMPARISON).exists() else None
    if (sha(current) if current is not None else None) not in (pending['plan']['comparison_before'],sha(pending['comparison'].encode())):
        raise ValueError('Customized skill comparison is preserved')
    if not safe_file(root,audit).exists():selected.write_document(root,audit,pending['audit'])
    if current!=pending['comparison'].encode():selected.write_document(root,selected.COMPARISON,pending['comparison'],replace_generated=True)
    update_index(root)


def _finish(root,pending):
    plan=pending['plan'];action=plan.get('action','install')
    operation=plan.get('reservation','.aikya/pi/skills/operations/'+digest(plan)+'.json')
    _projections(root,pending)
    selected.atomic_write(safe_file(root,selected.REGISTRY),encoded(authentication.seal(root,pending['next_registry']))+'\n',mode=0o600)
    selected.atomic_write(safe_file(root,operation),encoded(authentication.seal(root,{**pending,'status':'completed'}))+'\n',mode=0o600)
    safe_file(root,PENDING).unlink()
    entry=next(e for e in pending['next_registry']['skills'].values() if e['source_hash']==plan['source_hash'])
    return dict(status='installed',action=action,scope='project',name=entry['name'],source_hash=plan['source_hash'],restart_required=True,activation='explicit_only',execution='none')


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit project version change confirmation required')
    root=project_root(root);_repeat(root,plan)
    folder=safe_file(root,'.aikya/pi/skills/.lock').parent
    with locked(folder):
        _repeat(root,plan);registry=selected._registry(root);old=selected._entry(root,plan['name'])
        if plan['action']=='rollback':entry,data=_retained(root,plan['name'],plan['source_hash'])
        else:data=selected._capture(plan['source'],root)
        if data['source_hash']!=plan['source_hash']:raise ValueError('Reviewed update bytes changed')
        # Construct the eventual registry before reserving/copying: bounds cannot leave partial activation.
        entry=selected.make_entry(plan['destination'],data,None)
        # Manifest hash also contains the original ZIP hash, computed after its exclusive write.
        entry['package_manifest_hash']='0'*64
        entries={**registry['skills'],plan['name']:entry}
        comparison=selected._render_comparison(selected._comparison(root,registry),entries,plan['language'])
        value={**registry,'skills':entries,'comparison_hash':sha(comparison.encode())}
        if len(encoded(value).encode())>64000:raise ValueError('Project skill registry exceeds its read bound')
        pending=dict(schema=1,project=identity(root),status='pending',plan=plan,next_registry=None,comparison=comparison,audit=None)
        selected.atomic_write(safe_file(root,PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        _remember(root,old)
        if not plan['reuse']:
            zipped=packages.write(root,plan['destination'],data);packages.manifest(root,plan['destination'],data,zipped)
        actual=packages.read(root,plan['destination'])
        if actual['source']!=data['source'] or actual['files']!=data['files']:raise ValueError('Project package readback changed')
        manifest=authentication.verify(root,read_record(root,plan['destination']+'/manifest.json',32000))
        entry=selected.make_entry(plan['destination'],data,manifest);_remember(root,entry)
        value['skills'][plan['name']]=entry
        es=plan['language']=='es'
        audit=stamp(('# Cambio de versión de skill Pi' if es else '# Pi skill version change')+'\n\n'+plan['name']+'\n\n'+
                    old['source_hash']+' → '+plan['source_hash']+'\n\n'+('Activación explícita tras reiniciar; sin ejecutar código importado.' if es else 'Explicit activation after restart; no imported code executed.'))
        pending.update(next_registry=value,audit=audit)
        selected.atomic_write(safe_file(root,PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        return _finish(root,pending)


def recovery_preview(root):
    root=project_root(root);pending=authentication.verify(root,read_record(root,PENDING,200000));plan=pending.get('plan',{})
    if pending.get('project')!=identity(root) or pending.get('status')!='pending' or not pending.get('next_registry') or not pending.get('audit'):
        raise ValueError('Partial package operation is preserved for review')
    index_paths(root)
    if 'reservation' in plan:
        manifest=authentication.verify(root,read_record(root,plan['destination']+'/manifest.json',32000))
        data=packages.read(root,plan['destination']);entry=selected.make_entry(plan['destination'],data,manifest)
        if entry['source_hash']!=plan['source_hash']:raise ValueError('Initial package identity differs')
    else:entry,data=_retained(root,plan['name'],plan['source_hash'])
    if pending['next_registry']['skills'].get(entry['name'])!=entry:raise ValueError('Recovery selection differs')
    if digest(selected._registry(root)) not in (plan['registry_before'],digest(pending['next_registry'])):raise ValueError('Project registry changed after interruption')
    current=sha(read_source(root,selected.COMPARISON,64000)) if safe_file(root,selected.COMPARISON).exists() else None
    if current not in (plan['comparison_before'],sha(pending['comparison'].encode())):raise ValueError('Customized comparison is preserved')
    audit=_audit_path(plan)
    if safe_file(root,audit).exists() and sha(read_source(root,audit,64000))!=sha(pending['audit'].encode()):raise ValueError('Customized audit is preserved')
    return dict(plan=dict(schema=1,project=identity(root),pending_hash=digest(pending)),review=dict(scope='project',action='recover',name=entry['name'],source_hash=plan['source_hash'],effects='Promote observed package and known documentation; no source download or package copy replay',activation='explicit_only',restart_required=True))


def recover(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit project skill reconciliation required')
    root=project_root(root)
    if recovery_preview(root)['plan']!=plan:raise ValueError('Project skill recovery preview changed')
    folder=safe_file(root,'.aikya/pi/skills/.lock').parent
    with locked(folder):
        if recovery_preview(root)['plan']!=plan:raise ValueError('Project skill recovery changed')
        return _finish(root,authentication.verify(root,read_record(root,PENDING,200000)))
