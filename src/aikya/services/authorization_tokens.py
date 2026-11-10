"""Ephemeral host grants shared by single-file and scoped batch effects."""
import base64
import hashlib
import hmac
import math
import re
import time
import uuid
from aikya.code_index.policy import project_root
from aikya.review.contracts import identifier,encoded,parse


def key(value):
    if not isinstance(value,bytes) or len(value)!=32:raise ValueError('Trusted host key required')


def source(checked):return checked['source_revision'] if 'source_revision' in checked else checked['before']


def issue(root,session,checked,authority,operation,*,now=None,ttl=120):
    key(authority);identifier(session)
    if operation not in ('file.write','file.batch'):raise ValueError('Unknown granted operation')
    if type(ttl) is not int or not 1<=ttl<=300:raise ValueError('Invalid grant lifetime')
    when=int(time.time()) if now is None else now
    payload=dict(schema=1,project=str(project_root(root)),session=session,operation=operation,
        intent_hash=checked['intent_hash'],source_revision=source(checked),workflow_revision=checked['workflow_revision'],
        issued_at=when,expires_at=when+ttl,nonce=uuid.uuid4().hex)
    raw=base64.urlsafe_b64encode(encoded(payload).encode()).rstrip(b'=')
    return raw.decode()+'.'+hmac.new(authority,raw,hashlib.sha256).hexdigest()


def verify(root,session,checked,token,authority,operation,now):
    key(authority);identifier(session)
    if not isinstance(token,str) or len(token)>4000 or not re.fullmatch(r'[A-Za-z0-9_-]+\.[a-f0-9]{64}',token):
        raise ValueError('Invalid host grant')
    raw,signature=token.split('.')
    if not hmac.compare_digest(hmac.new(authority,raw.encode(),hashlib.sha256).hexdigest(),signature):
        raise ValueError('Host grant signature mismatch')
    data=parse(base64.b64decode(raw+'='*(-len(raw)%4),altchars=b'-_',validate=True))
    fields={'schema','project','session','operation','intent_hash','source_revision','workflow_revision','issued_at','expires_at','nonce'}
    if (not isinstance(data,dict) or set(data)!=fields or type(data['schema']) is not int or data['schema']!=1
            or data['project']!=str(project_root(root)) or data['session']!=session or data['operation']!=operation
            or not isinstance(data['nonce'],str) or not re.fullmatch('[a-f0-9]{32}',data['nonce'])):
        raise ValueError('Foreign host grant')
    for field in ('issued_at','expires_at'):
        if type(data[field]) not in (int,float) or not math.isfinite(data[field]):raise ValueError('Invalid grant clock')
    if not data['issued_at']<=now<=data['expires_at'] or not 0<data['expires_at']-data['issued_at']<=300:
        raise ValueError('Expired host grant')
    if any(data[field]!=value for field,value in (('intent_hash',checked['intent_hash']),
            ('source_revision',source(checked)),('workflow_revision',checked['workflow_revision']))):
        raise ValueError('Approved content or source changed')
    return data
