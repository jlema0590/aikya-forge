"""Trusted native documentation composition; never source execution or approval."""
from pathlib import Path
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.documentation import composition
from aikya.documentation.language import resolve
from aikya.documentation.layout import stamp,content,generated,index_paths,write_document
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import encoded,digest,identifier
from aikya.storage import atomic_write
from . import documentation_inputs as inputs


def catalog(root,document=None):
    root=project_root(root);inputs.profile(root)
    if document is None:return dict(documents=list(inputs.ROLES),effects='none')
    if document not in inputs.ROLES:raise ValueError('Choose a supported living document')
    key,template=composition.foundation(document)
    return dict(document=document,templates=[key],sections=template['sections'],language=resolve(root),effects='none')


def _documents(root,items,profile,language,pages):
    if not isinstance(items,list) or not 1<=len(items)<=3:raise ValueError('Select 1–3 reviewed documents')
    result=[];seen=set()
    for item in items:
        if not isinstance(item,dict) or set(item)-{'document','payload','slug'} or not {'document','payload'}<=set(item):raise ValueError('Invalid reviewed document')
        if not isinstance(item['payload'],dict):raise ValueError('Reviewable document payload required')
        role=item['document']
        if role not in inputs.ROLES:raise ValueError('Use the dedicated workflow for reserved documents')
        command,document=inputs.ROLES[role]
        selected=composition.select(profile,command,document=document)
        relative=composition.destination(role,item.get('slug'));name='aikya/docs/'+relative
        if name in seen:raise ValueError('Duplicate document destination')
        seen.add(name);target=safe_file(root,name)
        before=read_source(root,name,12000).decode('utf8') if target.exists() else None
        if before is not None and not generated(before):raise ValueError('Customized document is preserved')
        if name in pages and (before is None or inputs.sha(before.encode())!=pages[name]):raise ValueError('Managed document changed outside this workflow')
        evidence=inputs.sources(root,item['payload'].get('evidence'),allow_docs=True) if role=='summary' else {}
        if any(v is None for v in evidence.values()):raise ValueError('Summary evidence must exist')
        body=composition.render(selected,item['payload'],language,root=root,relative=relative)
        if before is not None:body=composition.merge_sections(before,body)
        if len(body.encode())>12000:raise ValueError('Split documentation into smaller reviewed updates')
        result.append(dict(path=name,before=before,after=body,templates=selected['templates'],evidence_hashes=evidence))
    return result


def _request(ident,summary,changes,documents,language):
    if not isinstance(summary,str) or not 1<=len(summary)<=1000 or '\x00' in summary:raise ValueError('Supply a bounded change summary')
    summary=composition.prose(summary,'change summary',1000)
    es=language=='es';headings=('Cambios','Evidencias','Documentos actualizados') if es else ('Changes','Evidence','Updated documents')
    note='Comprobaciones no ejecutadas por este comando. Registro documental; no es aprobación técnica.' if es else 'Checks not run by this command. Documentation record; not technical acceptance.'
    return stamp('# '+ident+'\n\n## '+headings[0]+'\n\n'+summary+'\n\n## '+headings[1]+'\n\n'+note+'\n\n```json\n'+encoded(changes)+'\n```\n\n## '+headings[2]+'\n\n'+'\n'.join('- `'+p['path']+'`' for p in documents+[dict(path='aikya/docs/changes/'+ident+'.md')]))


def _assemble(root,command,data,session):
    if not isinstance(data,dict) or len(encoded(data))>8000:raise ValueError('Documentation input exceeds its bound')
    action=data.get('action');profile=inputs.profile(root);language=resolve(root);pages=inputs.registry(root)
    if safe_file(root,inputs.PENDING).exists():raise ValueError('Pending documentation operation; reconcile without replay')
    index_paths(root);detail={};baseline=None;changes={}
    if command=='aikya-docs-sync' and action=='baseline':
        if set(data)!={'action','change_id','sources'}:raise ValueError('Expected change_id and explicit sources')
        path=inputs.baseline_path(data['change_id'])
        if safe_file(root,path).exists() or safe_file(root,'aikya/docs/changes/'+data['change_id']+'.md').exists():raise ValueError('Existing baseline/request is preserved')
        detail=dict(path=path,sources=inputs.sources(root,data['sources']))
    else:
        if command=='aikya-bugfix' and action=='append':
            if set(data)!={'action','payload','sources'}:raise ValueError('Expected canonical bug payload and sources')
            source=inputs.sources(root,data['sources'])
            if any(v is None for v in source.values()):raise ValueError('Bug sources must exist')
            detail['sources']=source
        elif command=='aikya-docs' and action=='write':
            if set(data)!={'action','documents','sources'}:raise ValueError('Expected reviewed documents and source paths')
            source=inputs.sources(root,data['sources'])
            if not any(v is not None for v in source.values()):raise ValueError('At least one existing source is required')
            detail['sources']=source
        elif command=='aikya-docs-sync' and action=='sync':
            if set(data)!={'action','change_id','summary','documents'}:raise ValueError('Expected change_id, summary and documents')
            baseline=inputs.baseline(root,data['change_id'],session);current=inputs.sources(root,list(baseline['sources']))
            changes={p:dict(before=old,after=current[p]) for p,old in baseline['sources'].items() if old!=current[p]}
            if not changes:return None,dict(status='no_changes',changes={},checks='not_run')
            detail.update(baseline_hash=digest(baseline),changes=changes)
        else:raise ValueError('Unknown native documentation action')
        if command=='aikya-bugfix':
            from .bug_document import document
            documents=[document(root,data['payload'],profile,language,pages)]
        else:documents=_documents(root,data['documents'],profile,language,pages)
        documents=[item for item in documents if item['before']!=item['after']]
        if baseline is not None:
            documents.append(dict(path='aikya/docs/changes/'+data['change_id']+'.md',before=None,
                                  after=_request(data['change_id'],data['summary'],changes,documents,language),templates=['aikya:request-record']))
        projected={**pages,**{item['path']:inputs.sha(item['after'].encode()) for item in documents}}
        if len(projected)>200 or len(encoded(projected))>60000:raise ValueError('Documentation registry requires archival')
        if any(len(item['after'].encode())>12000 or item['after'].splitlines().count('GENERATED BY AIKYA HARNESS')!=1 for item in documents):
            raise ValueError('Documentation output exceeds its bound or contains duplicate footers')
        documents=[item for item in documents if item['before']!=item['after']]
        if not documents:return None,dict(status='up_to_date',checks='not_run')
        detail['documents']=documents
    return dict(profile=profile,language=language,pages=pages,detail=detail),None


def preview(root,command,input_data,session_id):
    root=project_root(root);identifier(session_id)
    state,noop=_assemble(root,command,input_data,session_id)
    if noop:return dict(**noop,plan=None)
    revision=freeze_candidate(root,'pi-documentation',['aikya/docs/overview.md'],session_id=session_id)['id']
    plan=dict(schema=1,project=identity(root),command=command,input_data=input_data,session_id=session_id,
              source_revision=revision,profile_hash=digest(state['profile']),language=state['language'],
              registry_hash=digest(state['pages']),detail_hash=digest(state['detail']))
    result=dict(status='review_ready',plan=plan,review=state['detail'])
    if len(encoded(plan))>12000 or len(encoded(result))>50000:raise ValueError('Documentation preview exceeds its review bound')
    return result


def _still_owned(root,state,before,changed):
    after=freeze_candidate(root,'pi-documentation',['aikya/docs/overview.md'],session_id=before['session_id'])
    drift={p for p in before['files'].keys()|after['files'].keys() if before['files'].get(p)!=after['files'].get(p)}
    if drift-set(changed) or after['base']!=before['base'] or inputs.profile(root)!=state['profile'] or resolve(root)!=state['language']:
        raise ValueError('External source/profile change during documentation operation; preserve pending state')
    for item in state['detail'].get('documents',[]):
        evidence=item.get('evidence_hashes',{})
        if evidence and inputs.sources(root,list(evidence),allow_docs=True)!=evidence:raise ValueError('Evidence changed during documentation operation')


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Native documentation confirmation required')
    root=project_root(root)
    keys={'schema','project','command','input_data','session_id','source_revision','profile_hash','language','registry_hash','detail_hash'}
    if not isinstance(plan,dict) or set(plan)!=keys:raise ValueError('Invalid documentation preview')
    def fresh():
        value=preview(root,plan['command'],plan['input_data'],plan['session_id'])
        if value['plan']!=plan:raise ValueError('Documentation preview changed')
    fresh();folder=safe_file(root,inputs.PENDING).parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        fresh();state,_=_assemble(root,plan['command'],plan['input_data'],plan['session_id'])
        if (state is None or digest(state['profile'])!=plan['profile_hash'] or state['language']!=plan['language']
                or digest(state['pages'])!=plan['registry_hash'] or digest(state['detail'])!=plan['detail_hash']):
            raise ValueError('Documentation inputs changed after final preview')
        detail=state['detail']
        before=freeze_candidate(root,'pi-documentation',['aikya/docs/overview.md'],session_id=plan['session_id'])
        if before['id']!=plan['source_revision']:raise ValueError('Source changed after final preview')
        authentication.key(root,create=True)
        from .documentation_recovery import reservation,operation
        pending=reservation(root,plan,state,before)
        atomic_write(safe_file(root,inputs.PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        changed=[]
        if plan['input_data']['action']=='baseline':
            value=dict(schema=1,project=identity(root),change_id=plan['input_data']['change_id'],session_id=plan['session_id'],sources=detail['sources'])
            atomic_write(safe_file(root,detail['path']),encoded(authentication.seal(root,value))+'\n',mode=0o600)
            result=dict(status='baseline_recorded',change_id=value['change_id'],sources=value['sources'],checks='not_run')
        else:
            pages=dict(state['pages'])
            for item in detail['documents']:
                write_document(root,item['path'],item['after'],replace_generated=item['before'] is not None)
                if read_source(root,item['path'],12000).decode('utf8')!=item['after']:raise ValueError('Documentation readback failed')
                pages[item['path']]=inputs.sha(item['after'].encode());changed.append(item['path'])
            if len(pages)>200 or len(encoded(pages))>60000:raise ValueError('Documentation registry requires archival')
            value=dict(schema=1,project=identity(root),pages=pages)
            atomic_write(safe_file(root,inputs.REGISTRY),encoded(authentication.seal(root,value))+'\n',mode=0o600)
            result=dict(status='documents_recorded',documents=changed,checks='not_run',delivery_authorized=False)
        _still_owned(root,state,before,changed)
        if plan['input_data']['action']=='sync':
            consumed='.aikya/pi/documentation/completed/'+plan['input_data']['change_id']+'.json'
            atomic_write(safe_file(root,consumed),encoded(authentication.seal(root,dict(schema=1,operation=digest(plan))))+'\n',mode=0o600)
        if changed:
            from .maintenance import after_write
            result['memory']=after_write(root)
        _still_owned(root,state,before,changed)
        record='.aikya/pi/documentation/operations/'+digest(plan)+'.json'
        transition_value=None
        if changed:
            from aikya.review.document_transitions import transition
            transition_value=transition(before,detail['documents'])
        atomic_write(safe_file(root,record),encoded(authentication.seal(root,operation(plan,result,transition_value)))+'\n',mode=0o600)
        safe_file(root,inputs.PENDING).unlink()
    return result
