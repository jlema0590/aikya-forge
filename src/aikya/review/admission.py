"""Admit an independent observed review; never derive consent from model prose."""
import hashlib
import time
import uuid
from aikya.code_index.policy import project_root, read_source
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.routing.pi_usage import _load as load_usage
from aikya.storage import atomic_write
from aikya.documentation.language import resolve
from . import authentication
from .contracts import dossier, identifier, digest, encoded, read_record
from .candidates import load_candidate, is_current
from .receipts import _read
from .publication import history, report_body, publish_report


def _evidence(root, change_id):
    return digest(_read(root,change_id))


def request_review(root, change_id, reviewer_session, *, approved=False):
    if approved is not True: raise ValueError('Host approval required for reviewer execution')
    from .controller import assess_candidate
    root=project_root(root); identifier(reviewer_session)
    candidate=load_candidate(root,change_id)
    if reviewer_session==candidate['session_id']: raise ValueError('Author cannot admit its own review')
    if not candidate['policy'].get('definitions') or assess_candidate(root,change_id)['status']!='review_required':
        raise ValueError('Fresh execution-bound checks required before independent review')
    authentication.key(root,create=True)
    own=dossier(change_id); folder=safe_file(root,own+'/.lock').parent
    with locked(folder):
        if not is_current(root,candidate): raise ValueError('Candidate changed before review')
        if sum(p['event']['decision']=='changes_requested' for p in history(root,own))>1:
            raise ValueError('Correction allowance exhausted; explicit escalation required')
        now=int(time.time()); nonce=uuid.uuid4().hex
        payload=dict(schema=1,project=candidate['project'],change_id=change_id,candidate=candidate['id'],
            author_session=candidate['session_id'],reviewer_session=reviewer_session,scope=candidate['scope'],
            evidence_hash=_evidence(root,change_id),nonce=nonce,issued_at=now,expires_at=now+900,docs_language=resolve(root))
        ticket=authentication.seal(root,payload)
        atomic_write(safe_file(root,own+'/reviews/'+nonce+'/request.json'),encoded(ticket)+'\n')
        return ticket


def _event(root, candidate, ticket, event):
    if not isinstance(event,dict) or set(event)!={'call_id','decision','findings'}: raise ValueError('Invalid reviewer result')
    identifier(event['call_id'])
    if event['decision'] not in ('accept','changes_requested','escalate') or not isinstance(event['findings'],list) or len(event['findings'])>20:
        raise ValueError('Invalid review decision')
    call=load_usage(root)['events'].get(event['call_id'])
    if not call or call['state']!='recorded' or not call['usage'] or sum(call['usage'].values())<=0:
        raise ValueError('Unobserved reviewer execution')
    context=call['context']
    if (context['session']!=ticket['reviewer_session'] or context['role']!='reviewer' or context['phase']!='review'
            or context.get('candidate')!=candidate['id'] or context.get('change_id')!=candidate['change_id']):
        raise ValueError('Reviewer is not bound to this candidate')
    for finding in event['findings']:
        if (not isinstance(finding,dict) or set(finding)!={'path','line','severity','summary'}
                or finding['path'] not in candidate['files'] or type(finding['line']) is not int or not 1<=finding['line']<=1000000
                or finding['severity'] not in ('low','medium','high','critical') or not isinstance(finding['summary'],str)
                or not 1<=len(finding['summary'])<=500 or '\x00' in finding['summary']): raise ValueError('Invalid review finding')
    if event['decision']=='accept' and any(f['severity'] in ('high','critical') for f in event['findings']):
        raise ValueError('Blocking findings cannot be accepted')
    return event


def admit_review(root, change_id, ticket, event):
    root=project_root(root); request=authentication.verify(root,ticket)
    own=dossier(change_id); candidate=load_candidate(root,change_id)
    if (request.get('change_id')!=change_id or request.get('project')!=candidate['project']
            or request.get('candidate')!=candidate['id'] or request.get('author_session')!=candidate['session_id']
            or not isinstance(request.get('nonce'),str)): raise ValueError('Foreign reviewer ticket')
    nonce=identifier(request['nonce']); archive=own+'/reviews/'+nonce+'/review.json'
    original=read_record(root,own+'/reviews/'+nonce+'/request.json',65536)
    if original!=ticket: raise ValueError('Changed reviewer request')
    with locked(safe_file(root,own+'/.lock').parent):
        if not is_current(root,candidate) or request['evidence_hash']!=_evidence(root,change_id): raise ValueError('Stale review evidence')
        _event(root,candidate,request,event)
        previous=safe_file(root,archive)
        if previous.exists():
            receipt=read_record(root,archive,65536); payload=authentication.verify(root,receipt)
            if payload['event']!=event or payload['ticket']!=ticket: raise ValueError('Conflicting review replay')
        else:
            if not request['issued_at']<=time.time()<=request['expires_at']: raise ValueError('Review request expired')
            records=history(root,own)
            if any(p['event']['call_id']==event['call_id'] for p in records): raise ValueError('Reviewer call already admitted')
            effective='escalate' if event['decision']=='changes_requested' and any(p['event']['decision']=='changes_requested' for p in records) else event['decision']
            payload=dict(schema=1,generated_by='aikya-admitted-review',ticket=ticket,event=event,
                         admitted_at=int(time.time()),evidence_hash=request['evidence_hash'],effective_decision=effective)
            body=report_body(candidate,request,{**event,'decision':effective})
            payload['report_hash']=hashlib.sha256(body.encode()).hexdigest()
            receipt=authentication.seal(root,payload)
            prepared=safe_file(root,own+'/reviews/'+nonce+'/prepared.json')
            if prepared.exists():
                receipt=read_record(root,prepared.relative_to(root).as_posix(),65536)
                payload=authentication.verify(root,receipt)
                if payload['event']!=event or payload['ticket']!=ticket: raise ValueError('Conflicting prepared review')
                body=report_body(candidate,request,{**event,'decision':payload['effective_decision']})
            else: atomic_write(prepared,encoded(receipt)+'\n')
            publish_report(root,own,body)
        report_hash=hashlib.sha256(read_source(root,own+'/review.md',65536)).hexdigest()
        if report_hash!=payload['report_hash'] or not is_current(root,candidate): raise ValueError('Review publication changed candidate or report')
        if not previous.exists(): atomic_write(previous,encoded(receipt)+'\n')
        atomic_write(safe_file(root,own+'/review.json'),encoded(receipt)+'\n')
        return receipt


def admitted_decision(root, change_id, candidate):
    own=dossier(change_id)
    if not safe_file(root,own+'/review.json').exists(): return None
    try:
        receipt=read_record(root,own+'/review.json',65536); payload=authentication.verify(root,receipt)
        request=authentication.verify(root,payload['ticket'])
        archive=read_record(root,own+'/reviews/'+identifier(request['nonce'])+'/review.json',65536)
        if archive!=receipt or request['project']!=candidate['project']:
            raise ValueError('Foreign review projection')
        if request['candidate']!=candidate['id']: return None
        if payload['evidence_hash']!=_evidence(root,change_id): raise ValueError('Changed process evidence')
        if hashlib.sha256(read_source(root,own+'/review.md',65536)).hexdigest()!=payload['report_hash']:
            raise ValueError('Changed review report')
        _event(root,candidate,request,payload['event'])
        return payload.get('effective_decision',payload['event']['decision'])
    except (ValueError,OSError,KeyError,TypeError): return 'unverified'
