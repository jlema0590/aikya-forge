"""Confirmed native skill withdrawal/restoration; exact packages remain recoverable."""
import secrets
from aikya.core.checkpoints import identity,safe_file
from aikya.documentation.language import resolve
from aikya.documentation.layout import index_paths,update_index,stamp
from aikya.review import authentication
from aikya.review.contracts import digest,encoded,hash_id,read_record
from aikya.code_index.policy import read_source
from aikya.storage import atomic_write
from . import skill_removal_state as state,selected_skills as project


def _audit(plan):return 'aikya/docs/operations/skill-removal-'+digest(plan)+'.md'


def _prepare(root,scope,names,action,operation_id,nonce):
    ctx=state.context(root,scope);selected=state.names(names);registry=ctx['registry']
    if registry is None:raise ValueError('No owned skill registry exists')
    if action not in ('remove','restore'):raise ValueError('Choose remove or restore')
    if action=='remove':
        if operation_id is not None:raise ValueError('Removal does not reuse an operation identity')
        if any(n not in registry['skills'] for n in selected):raise ValueError('No active owned skill with this name')
        backup={name:registry['skills'][name] for name in selected};source=None
    else:
        previous=state.original(ctx,operation_id)
        if any(n not in previous['backup'] or n in registry['skills'] for n in selected):raise ValueError('Restore name is missing or already selected; preserved')
        backup={name:previous['backup'][name] for name in selected};source=digest(previous)
    for name,entry in backup.items():state.cached(ctx,name,entry)
    prior=state.comparison(ctx)
    language=registry.get('language',resolve(ctx['root'])) if scope=='project' else 'en'
    plan=dict(schema=1,project=identity(ctx['folder']),scope=scope,action=action,names=selected,
        before=digest(registry),entries=digest(backup),restore_from=operation_id,source_operation=source,
        comparison_before=project.sha(prior) if prior is not None else None,language=language,nonce=nonce)
    target=ctx['operations']+digest(plan)+'.json'
    if safe_file(ctx['folder'],target).exists():raise ValueError('Operation already exists; do not replay')
    if scope=='project':
        index_paths(ctx['root'])
        if safe_file(ctx['root'],_audit(plan)).exists():raise ValueError('Existing skill audit is preserved')
    entries=dict(registry['skills'])
    if action=='remove':
        for name in selected:del entries[name]
    else:entries.update(backup)
    if len(entries)>20:raise ValueError('Active skill capacity exceeded')
    value={**registry,'skills':entries};body=None
    if scope=='project':
        body=project._render_comparison(prior,entries,language);value['comparison_hash']=project.sha(body.encode())
    if len(encoded(value).encode())>63000:raise ValueError('Registry exceeds its read bound')
    return ctx,plan,backup,value,body


def preview(root,scope='project',names=None,action='remove',operation_id=None):
    if names=='all':
        ctx=state.context(root,scope)
        names=sorted(state.original(ctx,operation_id)['backup'] if action=='restore' else (ctx['registry'] or {}).get('skills',{}))
        if not names:return dict(plan=None,review=dict(scope=scope,names=[],execution='none',reason='No active owned skills'))
    return _preview(root,scope,names,action,operation_id,secrets.token_hex(32))


def _preview(root,scope,names,action,operation_id,nonce):
    hash_id(nonce);ctx,plan,backup,value,body=_prepare(root,scope,names,action,operation_id,nonce)
    review=dict(scope=scope,action=action,names=plan['names'],execution='none',restart_required=scope=='project',
        effects='Change active selection only; retain exact original packages as recoverable backup',
        other_scopes='Unchanged; global withdrawal does not delete independent project copies',
        backup='Signed entry snapshot and existing immutable package archives',writes=True)
    if scope=='project':review['documents']=[project.COMPARISON,_audit(plan),'aikya/docs/indice.md']
    return dict(plan=plan,review=review)


def _repeat(root,plan):
    fields={'schema','project','scope','action','names','before','entries','restore_from','source_operation','comparison_before','language','nonce'}
    if not isinstance(plan,dict) or set(plan)!=fields:raise ValueError('Invalid withdrawal preview')
    args=dict(scope=plan['scope'],names=plan['names'],action=plan['action'],operation_id=plan['restore_from'],nonce=plan['nonce'])
    if _preview(root,**args)['plan']!=plan:raise ValueError('Skill withdrawal preview changed')
    return _prepare(root,**{k:v for k,v in args.items() if k!='operation_id'},operation_id=plan['restore_from'])


def _projections(ctx,pending):
    if ctx['scope']!='project':return
    root=ctx['root'];plan=pending['plan'];path=safe_file(root,project.COMPARISON)
    raw=read_source(root,project.COMPARISON,64000) if path.exists() else None
    after=pending['comparison'].encode()
    if (project.sha(raw) if raw is not None else None) not in (plan['comparison_before'],project.sha(after)):
        raise ValueError('Customized comparison is preserved')
    audit=_audit(plan);target=safe_file(root,audit)
    if target.exists() and read_source(root,audit,64000)!=pending['audit'].encode():raise ValueError('Customized withdrawal audit is preserved')
    if not target.exists():project.write_document(root,audit,pending['audit'])
    if raw!=after:project.write_document(root,project.COMPARISON,pending['comparison'],replace_generated=True)
    update_index(root)


def _finish(ctx,pending):
    plan=pending['plan'];target=ctx['operations']+digest(plan)+'.json'
    completed={**pending,'status':'completed'};existing=safe_file(ctx['folder'],target)
    if existing.exists() and authentication.verify(ctx['folder'],read_record(ctx['folder'],target,500000))!=completed:
        raise ValueError('Unknown operation journal is preserved')
    _projections(ctx,pending)
    atomic_write(safe_file(ctx['folder'],ctx['relative']),encoded(authentication.seal(ctx['folder'],pending['next_registry']))+'\n',mode=0o600)
    atomic_write(existing,encoded(authentication.seal(ctx['folder'],completed))+'\n',mode=0o600)
    safe_file(ctx['folder'],ctx['pending']).unlink()
    return dict(status='removed' if plan['action']=='remove' else 'restored',scope=ctx['scope'],names=plan['names'],
                operation_id=digest(plan),restart_required=ctx['scope']=='project',packages_retained=True,execution='none')


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit skill withdrawal/restoration confirmation required')
    ctx,*_=_repeat(root,plan)
    with state.lock(ctx):
        ctx,current,backup,value,body=_repeat(root,plan)
        es=plan['language']=='es'
        audit=stamp(('# Cambio de selección de skills' if es else '# Skill selection change')+'\n\n'+plan['action']+': '+', '.join(plan['names'])
            +'\n\n'+('Paquetes originales conservados. Otras copias no se modifican. No se ejecuta código importado.' if es else
                       'Original packages retained. Other copies remain unchanged. No imported code executed.')) if plan['scope']=='project' else None
        pending=dict(schema=1,generated_by=state.GENERATOR,project=identity(ctx['folder']),status='pending',plan=current,
                     backup=backup,next_registry=value,comparison=body,audit=audit)
        atomic_write(safe_file(ctx['folder'],ctx['pending']),encoded(authentication.seal(ctx['folder'],pending))+'\n',mode=0o600)
        return _finish(ctx,pending)


def recovery_preview(root,scope='project'):
    ctx=state.context(root,scope,guard=False);pending=state.pending(ctx)
    return dict(plan=dict(scope=scope,project=identity(ctx['folder']),pending_hash=digest(pending)),
                review=dict(scope=scope,action='recover',names=pending['plan']['names'],execution='none',
                            effects='Finish the observed selection metadata without package copy or download replay'))


def recover(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit skill recovery confirmation required')
    if not isinstance(plan,dict) or set(plan)!={'scope','project','pending_hash'}:raise ValueError('Invalid recovery preview')
    if recovery_preview(root,plan['scope'])['plan']!=plan:raise ValueError('Withdrawal recovery changed')
    ctx=state.context(root,plan['scope'],guard=False)
    with state.lock(ctx):
        if recovery_preview(root,plan['scope'])['plan']!=plan:raise ValueError('Withdrawal recovery changed before commit')
        return _finish(ctx,state.pending(ctx))
