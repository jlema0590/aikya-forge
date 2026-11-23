"""Confirmed canonical local validators with signed process observations, not tests."""
from pathlib import Path
import os
from aikya.code_index.policy import project_root,read_source
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.documentation.layout import write_document,stamp
from aikya.documentation.language import resolve
from aikya.review import authentication
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import identifier,encoded,digest,parse
from aikya.review.definitions import selected_environment
from aikya.review.process import capture_process
from aikya.storage import atomic_write
from aikya.tools.infrastructure import validation_commands
from .documentation_inputs import profile
from .scaffold_recipes import tool

NAMES={'Terraform fmt':'terraform-fmt','OpenTofu fmt':'opentofu-fmt','Ansible syntax':'ansible-syntax',
       'Compose config':'compose-config','Helm lint':'helm-lint','Helm template':'helm-template','Kustomize build':'kustomize-build'}


def _path(root,run_id,name='record.json'):return safe_file(root,'.aikya/pi/infra-validation/'+identifier(run_id)+'/'+name)


def _save(root,run_id,value):
    authentication.key(root,create=True);atomic_write(_path(root,run_id),encoded(authentication.seal(root,value))+'\n',mode=0o600)


def _guard_pending(root,validator):
    folder=safe_file(root,'.aikya/pi/infra-validation/.aikya-scope-marker').parent
    if not folder.exists():return
    with os.scandir(folder) as entries:
        for index,entry in enumerate(entries):
            if index>=200:raise ValueError('Archive local validation history before continuing')
            if entry.is_symlink():raise ValueError('Linked validation state is preserved')
            if not entry.is_dir():continue
            relative='.aikya/pi/infra-validation/'+identifier(entry.name)+'/record.json'
            if not safe_file(root,relative).exists():continue
            value=authentication.verify(root,parse(read_source(root,relative,60000)))
            if not isinstance(value,dict) or value.get('plan',{}).get('project')!=identity(root):raise ValueError('Foreign validation state is preserved')
            if value.get('status')=='pending' and value['plan'].get('validator')==validator:
                raise ValueError('Uncertain prior validator; reconcile without replay')


def preview(root,validator,session_id,run_id):
    root=project_root(root);identifier(session_id);identifier(run_id)
    if validator not in NAMES.values():raise ValueError('Choose a known local infrastructure validator')
    _guard_pending(root,validator)
    if _path(root,run_id).exists():raise ValueError('Validation run identity exists; do not replay')
    p=profile(root);source=freeze_candidate(root,'pi-infra-validation',['aikya/docs/overview.md'],session_id=session_id)
    if p['project_type'] not in ('infrastructure','devops'):raise ValueError('Infrastructure profile required')
    checks=[args for label,args in validation_commands(root,p) if NAMES[label]==validator]
    if not checks:return dict(status='not_configured',plan=None,review=dict(validator=validator,reason='No configured artifacts',tests='not_run'))
    if len(checks)!=1:raise ValueError('Select one chart in the profile before native validation')
    argv=checks[0]
    try:binding=tool(argv[0])
    except ValueError:return dict(status='not_configured',plan=None,review=dict(validator=validator,reason='Tool is missing',tests='not_run'))
    plan=dict(validator=validator,session_id=session_id,run_id=run_id,source_revision=source['id'],project=identity(root),
              profile_hash=digest(p),language=resolve(root),tool=binding,argv=[binding['path'],*argv[1:]],timeout_seconds=90)
    return dict(status='review_ready',plan=plan,review={**plan,'tests':'not_run','scope':'local validator; no cloud apply/deploy',
                   'notice':'Tool configuration may read SDK caches, plugins or referenced files. This is not operating-system isolation.'})


def _cancelled(root,plan):
    path=_path(root,plan['run_id'],'cancel.json')
    def requested():
        try:
            if not path.exists():return False
            value=authentication.verify(root,parse(read_source(root,path.relative_to(root).as_posix(),8000)))
            if value!=plan:raise ValueError('Foreign validation cancellation')
            return True
        except (ValueError,OSError):return True
    return requested


def cancel(root,plan):
    root=project_root(root)
    if not isinstance(plan,dict) or plan.get('project')!=identity(root):raise ValueError('Owned validation preview required')
    identifier(plan['session_id']);target=_path(root,plan['run_id'],'cancel.json');target.parent.mkdir(parents=True,exist_ok=True)
    authentication.key(root,create=True);atomic_write(target,encoded(authentication.seal(root,plan))+'\n',mode=0o600)
    return dict(status='cancellation_requested',run_id=plan['run_id'])


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit local validator confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or not {'validator','session_id','run_id'}<=set(plan):raise ValueError('Invalid local validator preview')
    def fresh():
        value=preview(root,plan['validator'],plan['session_id'],plan['run_id'])
        if value['plan']!=plan:raise ValueError('Validation source, executable or environment changed')
    fresh();folder=_path(root,plan['run_id']).parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder.parent):
        fresh();_save(root,plan['run_id'],dict(plan=plan,status='pending'))
    process,_=capture_process(plan['argv'],root,selected_environment(),plan['timeout_seconds'],1048576,_cancelled(root,plan))
    status=process['status']
    if status=='completed':status='validated' if process['exit_code']==0 else 'failed'
    after=freeze_candidate(root,'pi-infra-validation',['aikya/docs/overview.md'],session_id=plan['session_id'])
    if after['id']!=plan['source_revision'] or digest(profile(root))!=plan['profile_hash'] or resolve(root)!=plan['language']:status='source_changed'
    try:
        if tool(Path(plan['tool']['path']).name)!=plan['tool']:status='definition_changed'
    except (ValueError,OSError):status='definition_changed'
    report='aikya/docs/operations/infra-validation-'+plan['run_id']+'.md'
    if safe_file(root,report).exists():raise ValueError('Existing validator report is preserved; inspect pending state')
    result=dict(status=status,validator=plan['validator'],run_id=plan['run_id'],process=process,tests='not_run',counts=None,delivery_authorized=False,report=report)
    es=plan['language']=='es';body=('# Validación local de infraestructura' if es else '# Local infrastructure validation')+'\n\n'
    body+=('Observación de proceso; no acredita pruebas, build ni despliegue.' if es else 'Process observation; this does not certify tests, a build or deployment.')
    write_document(root,report,stamp(body+'\n\n```json\n'+encoded(result)+'\n```'))
    _save(root,plan['run_id'],dict(plan=plan,status='recorded',result=result))
    from .maintenance import after_write
    result['memory']=after_write(root)
    return result
