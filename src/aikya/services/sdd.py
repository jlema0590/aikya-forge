"""Canonical SDD transitions reached only through the trusted local host."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file,identity
from aikya.core.state import locked
from aikya.review.candidates import freeze_candidate
from aikya.review.contracts import encoded
from aikya.workflows.sdd import engine

FIELDS={'specify':{'input_data'},'clarify':{'ident','answers'},'plan':{'ident','raw'},
        'tasks':{'ident','raw'},'approve':{'ident','stage','actor'}}
CALLS={'specify':engine.initialize,'clarify':engine.clarify,'plan':engine.create_plan,
       'tasks':engine.create_tasks,'approve':engine.approve}


def preview(root,action,arguments):
    root=project_root(root)
    if action not in FIELDS or not isinstance(arguments,dict) or set(arguments)!=FIELDS[action] or len(encoded(arguments))>12000:
        raise ValueError('Invalid SDD host transition')
    kind,profile=engine.load_profile(root)
    if profile.get('methodology')!='sdd':raise ValueError('SDD is not selected')
    revision=freeze_candidate(root,'pi-workflow',['aikya/docs/overview.md'],session_id='workflow')['id']
    return dict(schema=1,project=identity(root),action=action,arguments=arguments,source_revision=revision)


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit host confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','action','arguments','source_revision'}:
        raise ValueError('Invalid SDD preview')
    if preview(root,plan['action'],plan['arguments'])!=plan:raise ValueError('Stale SDD preview')
    folder=safe_file(root,'.aikya/pi/workflow-lock/.lock').parent;folder.mkdir(parents=True,exist_ok=True)
    with locked(folder):
        if preview(root,plan['action'],plan['arguments'])!=plan:raise ValueError('SDD source changed before transition')
        result=CALLS[plan['action']](root,**plan['arguments'])
        return dict(status='transition_recorded',result=result)


def status(root,ident):
    root=project_root(root);folder,data=engine.load(root,ident)
    return engine.status_data(data)
