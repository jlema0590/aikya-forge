"""Remember this run's admitted acceptance so confirmed recording can resume locally."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.review.controller import assess_candidate
from aikya.review.contracts import dossier,digest,read_record
from aikya.review import authentication
from . import task_runs as runs,task_run_records as records
from .task_run_lifecycle import _owned,_folder,_event


def _proof(root,state):
    if (state['phase']!='review' or safe_file(root,records.BASE+'completions/'+state['run_id']+'.json').exists()
            or runs.source_status(root,state)!='available'):raise ValueError('Current reviewed run source required')
    assessment=assess_candidate(root,state['change_id'])
    if assessment['status']!='reviewed' or assessment['can_close'] is not True:raise ValueError('Current independent acceptance required')
    receipt=read_record(root,dossier(state['change_id'])+'/review.json',65536)
    authentication.verify(root,receipt)
    return dict(candidate=assessment['candidate'],receipt=digest(receipt),security=digest(state['security']))


def current(root,state):
    try:proof=_proof(root,state)
    except (ValueError,OSError,KeyError):return False
    return any(e.get('event')=='review_accepted' and e.get('proof')==proof for e in state['events'])


def remember(root,run_id,session_id):
    root=project_root(root)
    with locked(_folder(root)):
        state=_owned(root,run_id,session_id);proof=_proof(root,state)
        if not current(root,state):_event(state,'review_accepted',proof=proof);records.save(root,state)
    return dict(status='review_checkpointed',run_id=run_id,proof=proof,delivery_authorized=False)
