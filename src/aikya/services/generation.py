"""Native confirmed batches with exclusive creation and durable uncertain outcomes."""
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.documentation.layout import index_paths,write_document
from aikya.documentation.language import resolve
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import encoded,digest
from aikya.review import authentication
from aikya.storage import atomic_write,write_new
from . import generation_inputs as inputs
from .task_binding import candidate_revision


def preview(root,files,session_id,category,details):
    root=project_root(root)
    if not isinstance(details,dict) or len(encoded(details))>6000:raise ValueError('Bounded generation provenance required')
    if safe_file(root,inputs.PENDING).exists():raise ValueError('Pending generation; reconcile without replay')
    data=inputs.artifacts(root,files,session_id,category);index_paths(root)
    review={k:v for k,v in data.items() if k!='prepared'}
    review.update(category=category,details=details,checks='not_run',delivery_authorized=False)
    if not data['prepared']:return dict(status='nothing_to_generate',plan=None,review=review)
    source=freeze_candidate(root,'pi-generation',['aikya/docs/overview.md'],session_id=session_id)
    plan=dict(schema=1,project=identity(root),source_revision=source['id'],profile_hash=digest(inputs.profile(root)),
              language=resolve(root),session_id=session_id,category=category,details=details,manifest_hash=digest(review))
    if len(encoded(plan))>12000 or len(encoded(dict(plan=plan,review=review)))>50000:raise ValueError('Generation review exceeds its host bound')
    return dict(status='review_ready',plan=plan,review=review)


def apply(root,plan,files,approved=False):
    if approved is not True:raise ValueError('Explicit native generation confirmation required')
    root=project_root(root)
    keys={'schema','project','source_revision','profile_hash','language','session_id','category','details','manifest_hash'}
    if not isinstance(plan,dict) or set(plan)!=keys:raise ValueError('Invalid generation preview')
    def fresh():
        value=preview(root,files,plan['session_id'],plan['category'],plan['details'])
        if value['plan']!=plan:raise ValueError('Generation source or reviewed artifacts changed')
        return value
    fresh();folder=safe_file(root,inputs.PENDING).parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        value=fresh();data=inputs.artifacts(root,files,plan['session_id'],plan['category'])
        if (digest(inputs.profile(root))!=plan['profile_hash'] or resolve(root)!=plan['language']
                or digest({**{k:v for k,v in data.items() if k!='prepared'},'category':plan['category'],'details':plan['details'],'checks':'not_run','delivery_authorized':False})!=plan['manifest_hash']):
            raise ValueError('Generation inputs changed after final preview')
        before=freeze_candidate(root,'pi-generation',['aikya/docs/overview.md'],session_id=plan['session_id'])
        if before['id']!=plan['source_revision']:raise ValueError('Source changed before generation')
        operation=digest(plan);record='.aikya/pi/generation/operations/'+operation+'.json'
        if safe_file(root,record).exists():raise ValueError('Generation identity exists; do not replay')
        report='aikya/docs/operations/generation-'+operation+'.md'
        if safe_file(root,report).exists():raise ValueError('Existing generation report is preserved')
        authentication.key(root,create=True);pending=dict(schema=1,project=identity(root),status='pending',plan=plan)
        atomic_write(safe_file(root,inputs.PENDING),encoded(authentication.seal(root,pending))+'\n',mode=0o600)
        for name,raw in data['prepared'].items():
            target=safe_file(root,name);target.parent.mkdir(parents=True,exist_ok=True);safe_file(root,name)
            write_new(target,raw)
            if inputs.sha(read_source(root,name,1001000))!=inputs.sha(raw):raise ValueError('Generated artifact readback failed')
        body=inputs.report(root,operation,plan['category'],data['files'],data['preserved'],plan['language'])
        write_document(root,report,body)
        # Maintain the canonical index for any generated Markdown alongside the receipt.
        after=freeze_candidate(root,'pi-generation',['aikya/docs/overview.md'],session_id=plan['session_id'])
        scope=[name for name in data['prepared'] if not name.startswith('aikya/docs/')]
        workflow=candidate_revision(root,scope,plan['session_id']) if scope else None
        drift={p for p in before['files'].keys()|after['files'].keys() if before['files'].get(p)!=after['files'].get(p)}
        if (drift-set(data['prepared'])-{report} or before['base']!=after['base']
                or digest(inputs.profile(root))!=plan['profile_hash'] or resolve(root)!=plan['language']
                or workflow!=data['workflow_revision']):
            raise ValueError('Concurrent generation change; pending outcome preserved')
        from .maintenance import after_write
        result=dict(status='generated',created=sorted(data['prepared']),preserved=data['preserved'],report=report,
                    checks='not_run',delivery_authorized=False,memory=after_write(root))
        atomic_write(safe_file(root,record),encoded(authentication.seal(root,{**pending,'status':'recorded','result':result}))+'\n',mode=0o600)
        safe_file(root,inputs.PENDING).unlink()
    return result
