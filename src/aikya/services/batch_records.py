"""Signed batch reservations, including orphan attempts before the pending pointer."""
import os
import re
from aikya.core.checkpoints import identity,safe_file
from aikya.review import authentication
from aikya.review.contracts import read_record,identifier,hash_id

PENDING='.aikya/pi/batches/pending.json'
OPERATIONS='.aikya/pi/batches/operations/'
RESERVATIONS='.aikya/pi/batches/reservations/'


def signed(root,path):
    value=authentication.verify(root,read_record(root,path,65536))
    fields={'schema','project','status','session','change_id','candidate','intent_hash','workflow_revision','language','nonce','files'}
    if (not isinstance(value,dict) or set(value) not in (fields,fields|{'result'}) or value['schema']!=1
            or value['project']!=identity(root) or value['status'] not in ('pending','written')
            or not isinstance(value['nonce'],str) or not re.fullmatch('[a-f0-9]{32}',value['nonce'])
            or value['language'] not in ('en','es') or not isinstance(value['files'],list) or not 1<=len(value['files'])<=20):
        raise ValueError('Invalid source batch reservation')
    identifier(value['session']);identifier(value['change_id']);hash_id(value['candidate']);hash_id(value['intent_hash'])
    if value['workflow_revision'] is not None:hash_id(value['workflow_revision'])
    seen=set()
    for item in value['files']:
        if (not isinstance(item,dict) or set(item)!={'path','before','after','action'}
                or item['action'] not in ('patch','replace','create','delete')):raise ValueError('Invalid reserved source operation')
        safe_file(root,item['path'])
        if item['path'] in seen or item['before']==item['after']:raise ValueError('Duplicate or empty reserved operation')
        seen.add(item['path'])
        for key in ('before','after'):
            if item[key] is not None:hash_id(item[key])
    return value


def guard(root):
    if safe_file(root,PENDING).exists():raise ValueError('Pending source batch requires reconciliation without replay')
    folder=safe_file(root,RESERVATIONS+'.probe').parent
    if not folder.exists():return
    with os.scandir(folder) as entries:
        for count,entry in enumerate(entries):
            if count>=200 or entry.is_symlink() or not entry.is_file() or not re.fullmatch(r'[a-f0-9]{32}\.json',entry.name):
                raise ValueError('Unsafe or oversized batch history')
            signed(root,RESERVATIONS+entry.name)
            raise ValueError('Uncertain source reservation requires manual reconciliation')
