"""Confirm complete signed source effects without using or renewing an old grant."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import identity,safe_file
from aikya.core.state import locked
from aikya.review.contracts import digest,identifier
from . import batch_records as records,source_batches as batches


def _pending(root,session):
    pending=records.signed(root,records.PENDING)
    if pending['status']!='pending' or pending['session']!=session:raise ValueError('Original native batch author required')
    reservation=records.RESERVATIONS+pending['nonce']+'.json'
    if safe_file(root,reservation).exists():
        if records.signed(root,reservation)!=pending:raise ValueError('Batch reservation and pointer disagree')
    else:
        value=records.signed(root,records.OPERATIONS+pending['nonce']+'.json')
        if value['status']!='written' or {**{k:value[k] for k in pending},'status':'pending'}!=pending:
            raise ValueError('Complete operation differs from the reserved source effects')
    return pending


def preview(root,session_id):
    root=project_root(root);identifier(session_id)
    if not safe_file(root,records.PENDING).exists():
        try:records.guard(root)
        except ValueError:return dict(status='manual_reconciliation',plan=None,reason='Orphan or unknown source reservation is preserved')
        return dict(status='nothing_pending',plan=None)
    pending=_pending(root,session_id)
    try:batches.observed(root,pending)
    except (ValueError,OSError):
        return dict(status='manual_reconciliation',plan=None,reason='Complete exact source effects cannot be established')
    plan=dict(schema=1,project=identity(root),session_id=session_id,pending_hash=digest(pending),nonce=pending['nonce'])
    return dict(status='reconciliation_ready',plan=plan,review=dict(change_id=pending['change_id'],files=pending['files'],
                effects='bookkeeping only; no source replay',checks='not_run',delivery_authorized=False))


def apply(root,plan,approved=False):
    if approved is not True:raise ValueError('Explicit native source reconciliation confirmation required')
    root=project_root(root)
    if not isinstance(plan,dict) or set(plan)!={'schema','project','session_id','pending_hash','nonce'}:
        raise ValueError('Invalid source reconciliation preview')
    def fresh():
        if preview(root,plan['session_id']).get('plan')!=plan:raise ValueError('Pending source effects changed')
    fresh()
    with locked(safe_file(root,records.PENDING).parent):
        fresh();pending=_pending(root,plan['session_id']);result=batches.finish(root,pending)
        return {**result,'status':'reconciled'}
