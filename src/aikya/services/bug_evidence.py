"""Native bug reproduction derives from observed regression results, never prose."""
from aikya.review.candidates import load_candidate,is_current
from aikya.review.controller import assess_candidate,_tdd_ready
from aikya.review.receipts import load_receipts
from aikya.review.contracts import encoded
from aikya.documentation.language import resolve
from . import checks
from .documentation_inputs import profile,sources


def status(root,change_id,session):
    profile(root)
    result=dict(status='not_reproduced',fixed=False,review_required=True,delivery_authorized=False,change_id=change_id)
    if change_id is None:return result
    registry=checks._registry(root,change_id);candidate=load_candidate(root,change_id)
    if (registry['session_id']!=session or candidate['session_id']!=session or registry['candidate']!=candidate['id']
            or candidate['policy'].get('native_observations') is not True):raise ValueError('Current native author evidence required')
    result.update(candidate=candidate['id'],scope=candidate['scope'],intent=checks.bound_intent(root,candidate))
    if not is_current(root,candidate):return {**result,'status':'stale_evidence'}
    rows=load_receipts(root,change_id);tdd=candidate['policy'].get('tdd')
    current=[r['payload'] for r in rows if r['payload']['candidate']==candidate['id']]
    result['checks']={r['check']:{k:r.get(k) for k in ('execution_status','executed','failed','skipped')} for r in current}
    if not tdd:return result
    red=any(r['check']==tdd['check'] and r.get('execution_status')=='failed' and r.get('exit_code') not in (None,0)
            and type(r.get('failed')) is int and r['failed']>0 and r.get('executed',0)>0 and r.get('skipped')==0 for r in current)
    lineage=_tdd_ready(root,candidate,rows)
    if not red and not lineage:return result
    result['status']='reproduced';assessment=assess_candidate(root,change_id)
    if assessment['status'] in ('review_required','reviewed','changes_requested','escalated','review_unverified'):
        result['status']='checks_passed'
    if assessment['status']=='reviewed' and assessment['can_close']:
        result.update(status='reviewed',fixed=True,review_required=False)
    return result


def prepare(root,data,session):
    if data.get('action')=='status':
        if set(data)-{'action','change_id'}:raise ValueError('Choose a native change identifier')
        proof=status(root,data.get('change_id'),session)
        return dict(status=proof['status'],plan=None,review=dict(bug_evidence=proof))
    if data.get('action')!='record' or set(data)-{'action','payload','sources','change_id'} or not {'payload','sources'}<=set(data):
        raise ValueError('Bug recording requires canonical payload and explicit sources')
    payload=data['payload']
    if not isinstance(payload,dict) or not isinstance(payload.get('sections'),dict) or 'evidence' in payload['sections']:
        raise ValueError('Native evidence is derived from observations, not supplied assertions')
    hashes=sources(root,data['sources'])
    if any(value is None for value in hashes.values()):raise ValueError('Bug source must exist')
    proof=status(root,data.get('change_id'),session)
    if proof['status']=='stale_evidence':raise ValueError('Bug evidence is stale; preserve the source and refresh explicitly')
    if data.get('change_id') is not None:
        intent=proof['intent']
        if (payload['sections'].get('summary')!=intent['objective']
                or payload['sections'].get('expected-result')!='\n'.join(intent['acceptance'])
                or not set(hashes)<=set(proof['scope'])):raise ValueError('Bug report does not match the observed regression intent/scope')
    notice=('Instantánea de observaciones nativas; el relato aportado no es evidencia de ejecución.' if resolve(root)=='es' else
            'Native observation snapshot; user-supplied narrative is not execution proof.')
    sections={**payload['sections'],'evidence':notice+'\n\n```json\n'+encoded(proof)+'\n```'}
    return dict(sources=hashes,payload={**payload,'sections':sections},bug_evidence=proof)
