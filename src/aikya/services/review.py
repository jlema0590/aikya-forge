"""Trusted-host RDD operations; never exposed as reviewer-authoring model tools."""
import hashlib
from aikya.code_index.policy import project_root,read_source
from aikya.review.candidates import load_candidate,is_current
from aikya.review.contracts import parse
from aikya.review.admission import request_review,admit_review
from aikya.review.controller import assess_candidate


def context(root,change_id):
    root=project_root(root);candidate=load_candidate(root,change_id)
    if not is_current(root,candidate) or len(candidate['scope'])>20:
        raise ValueError('Stale or oversized review scope requires explicit escalation')
    from aikya.review.document_transitions import review_scope
    documentation_scope=review_scope(root,candidate)
    files=[];remaining=6000
    for path in [*candidate['scope'],*documentation_scope]:
        expected=candidate['files'].get(path)
        if expected is None:
            files.append(dict(path=path,content=None,sha256=None));continue
        raw=read_source(root,path,remaining)
        if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Review source changed')
        remaining-=len(raw)
        files.append(dict(path=path,content=raw.decode('utf8'),sha256=expected))
    if not is_current(root,candidate):raise ValueError('Review context became stale')
    from aikya.review.receipts import load_receipts
    evidence={}
    for row in load_receipts(root,change_id):
        receipt=row['payload']
        if receipt['candidate']==candidate['id']:
            evidence[receipt['check']]={k:receipt.get(k) for k in ('execution_status','executed','failed','skipped','definition_hash')}
            if 'check_types' in candidate['policy']:
                evidence[receipt['check']]['check_type']=candidate['policy']['check_types'][receipt['check']]
    from .checks import bound_intent
    return dict(candidate=candidate['id'],change_id=change_id,scope=candidate['scope'],files=files,
                documentation_scope=documentation_scope,intent=bound_intent(root,candidate),
                checks=assess_candidate(root,change_id)['checks'],check_evidence=evidence)


def request(root,change_id,reviewer_session,approved=False):
    return request_review(root,change_id,reviewer_session,approved=approved)


def admit(root,change_id,ticket,call_id,response):
    if not isinstance(response,str) or len(response.encode('utf8'))>16000:raise ValueError('Oversized reviewer output')
    event=parse(response)
    if not isinstance(event,dict) or set(event)!={'decision','findings'}:raise ValueError('Malformed reviewer output')
    admit_review(root,change_id,ticket,dict(call_id=call_id,**event))
    return assess_candidate(root,change_id)
