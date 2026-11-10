"""Reviewed inert global skill versions; no project activation or global memory."""
from aikya.installation.bootstrap import state as installer
from aikya.core.checkpoints import identity,safe_file
from aikya.review import authentication
from aikya.review.contracts import digest,encoded,hash_id,identifier,read_record
from aikya.storage import atomic_write
from . import skill_library_state as state,skill_packages as packages
from .skill_sources import capture


def preview(source):return change_preview(action='install',source=source)


def change_preview(action,source=None,name=None,source_hash=None):
    folder=state.root();state.guard(folder);registry=state.load(folder);entries=registry['skills'] if registry else {}
    if action not in ('install','update','rollback'):raise ValueError('Unknown global skill change')
    if action=='rollback':
        if source is not None:raise ValueError('Rollback uses a retained package, not a new source')
        data=package(name,source_hash);selection=dict(kind='global',name=name,source_hash=source_hash)
    else:
        if name is not None or source_hash is not None:raise ValueError('Choose the source package explicitly')
        data=capture(source);name=data['name'];source_hash=data['source_hash'];selection=dict(source) if isinstance(source,dict) else data['source']
    current=entries.get(name)
    if action=='install' and (current or len(entries)>=20):raise ValueError('Global name exists or library bound reached; use an explicit reviewed update')
    if action!='install':
        if not current:raise ValueError('No selected global skill to change')
        package(name,current['current'])
        if current['current']==source_hash:raise ValueError('Skill version is unchanged')
        if source_hash not in current['versions'] and len(current['versions'])>=10:raise ValueError('Retained skill version bound reached; preserve and review archive options')
    destination='packages/'+source_hash+'/'+name
    packages.preflight(folder,destination,data)
    reuse=safe_file(folder,destination+'/.probe').parent.exists()
    if reuse:
        if not current or source_hash not in current['versions']:raise ValueError('Existing package data is preserved')
        existing=package(name,source_hash)
        if existing['files']!=data['files'] or existing['source']!=data['source']:raise ValueError('Retained content has a different origin; select its explicit retained version')
    plan=dict(schema=1,root=str(folder),action=action,source=selection,source_hash=source_hash,name=name,
              destination=destination,registry_before=digest(registry),reuse=reuse)
    review=dict(scope='global',action=action,activation='none',execution='none',source=data['source'],name=name,
                before=current['current'] if current else None,after=source_hash,description=data['description'],content=data['body'],
                files=data['files'],ignored_fields=data['ignored_fields'],destination=str(folder/destination))
    if len(encoded(dict(plan=plan,review=review)).encode())>18000:raise ValueError('Global skill review exceeds its bound')
    return dict(plan=plan,review=review)


def _repeat(plan):
    fields={'schema','root','action','source','source_hash','name','destination','registry_before','reuse'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid global skill preview')
    if plan['action']=='rollback':value=change_preview(action='rollback',name=plan['name'],source_hash=plan['source_hash'])
    else:value=change_preview(action=plan['action'],source=plan['source'])
    if value['plan']!=plan:raise ValueError('Global skill preview changed')


def _package_digest(data):return digest({k:data[k] for k in ('name','source','source_hash','files','installed')})


def _finish(folder,pending):
    value=pending['next_registry'];plan=pending['plan']
    atomic_write(safe_file(folder,state.REGISTRY),encoded(authentication.seal(folder,value))+'\n',mode=0o600)
    completed={**pending,'status':'installed','registry_hash':digest(value)}
    atomic_write(safe_file(folder,'operations/'+digest(plan)+'.json'),encoded(authentication.seal(folder,completed))+'\n',mode=0o600)
    safe_file(folder,state.PENDING).unlink()
    return dict(status='installed',scope='global',action=plan['action'],activation='none',name=plan['name'],
                source_hash=plan['source_hash'],package=str(folder/plan['destination']))


def apply(plan,approved=False):
    if approved is not True:raise ValueError('Explicit global skill library confirmation required')
    _repeat(plan);folder=state.root()
    with installer.installation_lock(folder.parent):
        _repeat(plan);registry=state.load(folder)
        data=package(plan['name'],plan['source_hash']) if plan['action']=='rollback' else capture(plan['source'])
        if data['source_hash']!=plan['source_hash']:raise ValueError('Global skill bytes changed')
        entries=dict(registry['skills']) if registry else {};old=entries.get(data['name']);versions=list(old['versions']) if old else []
        if data['source_hash'] not in versions:versions.append(data['source_hash'])
        entries[data['name']]=dict(current=data['source_hash'],versions=versions)
        value=dict(schema=1,project=identity(folder),skills=entries)
        if len(encoded(value).encode())>63000:raise ValueError('Global skill registry exceeds its bound')
        folder.mkdir(mode=0o700,parents=True,exist_ok=True)
        installer.write_json(folder/'owner.json',dict(schema=1,generated_by='aikya-pi-skill-library',root=str(folder)))
        authentication.key(folder,create=True)
        pending=dict(schema=1,project=identity(folder),status='pending',plan=plan,next_registry=value,package_digest=_package_digest(data))
        atomic_write(safe_file(folder,state.PENDING),encoded(authentication.seal(folder,pending))+'\n',mode=0o600)
        if not plan['reuse']:
            zipped=packages.write(folder,plan['destination'],data);packages.manifest(folder,plan['destination'],data,zipped)
        if _package_digest(packages.read(folder,plan['destination']))!=pending['package_digest']:raise ValueError('Global package readback changed')
        return _finish(folder,pending)


def package(name,source_hash):
    folder=state.root();state.guard(folder);registry=state.load(folder);identifier(name);hash_id(source_hash)
    entry=registry['skills'].get(name) if registry else None
    if not entry or source_hash not in entry.get('versions',[]):raise ValueError('No owned global skill version')
    data=packages.read(folder,'packages/'+source_hash+'/'+name)
    if data['name']!=name or data['source_hash']!=source_hash:raise ValueError('Global skill identity changed')
    return data


def recovery_preview():
    folder=state.root();pending=authentication.verify(folder,read_record(folder,state.PENDING,64000))
    fields={'schema','project','status','plan','next_registry','package_digest'}
    if not isinstance(pending,dict) or set(pending)!=fields or pending['project']!=identity(folder) or pending['status']!='pending':raise ValueError('Unknown library interruption')
    current=state.load(folder);plan=pending['plan']
    if digest(current) not in (plan['registry_before'],digest(pending['next_registry'])):raise ValueError('Global registry changed after interruption')
    if _package_digest(packages.read(folder,plan['destination']))!=pending['package_digest']:raise ValueError('Incomplete or changed package is preserved')
    return dict(plan=dict(schema=1,root=str(folder),pending_hash=digest(pending)),review=dict(scope='global',action='recover',
                name=plan['name'],source_hash=plan['source_hash'],activation='none',effects='Promote observed complete package; no copy or download replay'))


def recover(plan,approved=False):
    if approved is not True:raise ValueError('Explicit library reconciliation confirmation required')
    if recovery_preview()['plan']!=plan:raise ValueError('Global recovery preview changed')
    folder=state.root()
    with installer.installation_lock(folder.parent):
        if recovery_preview()['plan']!=plan:raise ValueError('Global recovery changed')
        return _finish(folder,authentication.verify(folder,read_record(folder,state.PENDING,64000)))


def status():
    folder=state.root();registry=state.load(folder);entries=registry['skills'] if registry else {};rows=[]
    for name,entry in sorted(entries.items()):
        integrity='verified'
        try:packages.read(folder,'packages/'+entry['current']+'/'+name)
        except (ValueError,OSError):integrity='changed'
        rows.append(dict(name=name,source_hash=entry['current'],versions=entry['versions'],activation='none',integrity=integrity))
    result='pending' if safe_file(folder,state.PENDING).exists() else 'degraded' if any(r['integrity']=='changed' for r in rows) else 'available'
    return dict(scope='global',status=result,skills=rows)
