"""Deterministic assessment of stored checks; review and delivery are separate."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from .candidates import load_candidate, is_current
from .contracts import dossier
from .receipts import _read


def assess_candidate(root, change_id):
    """Assess the durable candidate; never accept model-supplied verdict arrays."""
    root = project_root(root)
    folder = safe_file(root, dossier(change_id) + '/.lock').parent
    if not folder.is_dir():
        raise ValueError('Review dossier is absent')
    with locked(folder):
        candidate = load_candidate(root, change_id)
        result = dict(candidate=candidate['id'], status='stale', can_close=False,
                      delivery_authorized=False, checks={})
        if not is_current(root, candidate):
            return result
        rows = _read(root, change_id)
        latest = {r['payload']['check']: r['payload'] for r in rows
                  if r['payload']['candidate'] == candidate['id']}
        for check in candidate['policy']['checks']:
            receipt = latest.get(check)
            if receipt is None:
                status = 'pending'
            elif receipt.get('execution_status') not in (None, 'completed', 'unverified'):
                status = 'failed'
            elif receipt['exit_code'] != 0:
                status = 'failed'
            elif candidate['policy'].get('check_types',{}).get(check)=='process':
                status='passed' if receipt.get('execution_status')=='completed' else 'unverified'
            elif receipt['executed'] == 0 or receipt['skipped'] != 0:
                status = 'unverified'
            else:
                status = 'passed'
            result['checks'][check] = dict(status=status, receipt=receipt['id'] if receipt else None)
        states = {v['status'] for v in result['checks'].values()}
        if 'failed' in states:
            result['status'] = 'failed'
        elif 'unverified' in states:
            result['status'] = 'unverified'
        elif 'pending' in states:
            result['status'] = 'pending_checks'
        elif not _tdd_ready(root,candidate,rows):
            result['status']='tdd_red_required'
        elif not _baseline_ready(root,candidate,rows):
            result['status']='baseline_required'
        elif candidate['policy']['review_required']:
            from .admission import admitted_decision
            decision = admitted_decision(root, change_id, candidate)
            result['status'] = {None:'review_required', 'accept':'reviewed', 'changes_requested':'changes_requested',
                                'escalate':'escalated', 'unverified':'review_unverified'}[decision]
            result['can_close'] = decision == 'accept'
        else:
            # A descriptive receipt assessment never creates workflow consent.
            result['status'] = 'checks_passed'
        if not is_current(root, candidate):
            result.update(status='stale', can_close=False)
        return result


def _tdd_ready(root,candidate,rows):
    """A failed, valid executed ancestor is evidence; prose and skipped runs are not."""
    return _lineage_ready(root,candidate,rows,'tdd')


def _baseline_ready(root,candidate,rows):
    return _lineage_ready(root,candidate,rows,'baseline')


def _lineage_ready(root,candidate,rows,field):
    from .contracts import read_record
    from .candidates import validate
    policy=candidate['policy'].get(field)
    if policy is None:return True  # Legacy receipt policies remain explicitly descriptive.
    parent=candidate['parent'];seen=set()
    for _ in range(100):
        if parent is None:return False
        if parent in seen:raise ValueError('Cyclic candidate lineage')
        seen.add(parent)
        ancestor=read_record(root,dossier(candidate['change_id'])+'/candidates/'+parent+'.json')
        validate(root,ancestor)
        if ancestor['change_id']!=candidate['change_id'] or ancestor['session_id']!=candidate['session_id']:
            raise ValueError('Foreign TDD lineage')
        same=(ancestor['policy']==candidate['policy'] and all(ancestor['files'].get(p)==candidate['files'][p] for p in policy['paths']))
        if same and any(_qualifying_test(r['payload'],parent,policy['check'],field) for r in rows):return True
        if not same:return False  # Test edits restart Red; an older matching file cannot bypass it.
        parent=ancestor['parent']
    raise ValueError('TDD lineage exceeds supported bound')


def _qualifying_test(receipt,parent,check,field):
    if (receipt['candidate']!=parent or receipt['check']!=check or type(receipt['executed']) is not int
            or receipt['executed']<=0 or receipt['skipped']!=0):return False
    if field=='baseline':
        return receipt.get('execution_status')=='completed' and receipt.get('failed')==0 and receipt['exit_code']==0
    return (receipt.get('execution_status')=='failed' and type(receipt.get('failed')) is int
            and receipt['failed']>0 and receipt['exit_code']!=0)
