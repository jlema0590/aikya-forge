"""Signed local run checkpoints; project token accounting remains in the existing ledger."""
import re
from aikya.core.checkpoints import identity,safe_file
from aikya.documentation.layout import write_document,stamp
from aikya.review import authentication
from aikya.review.contracts import read_record,encoded,identifier,dossier
from aikya.storage import atomic_write

BASE='.aikya/pi/task-runs/'
ACTIVE=BASE+'active.json'


def path(run_id):
    if not isinstance(run_id,str) or not re.fullmatch('[a-f0-9]{32}',run_id):raise ValueError('Invalid native task run identity')
    return BASE+run_id+'.json'


def load(root,run_id,session_id):
    value=authentication.verify(root,read_record(root,path(run_id),65536))
    fields={'schema','project','run_id','session_id','provider','model','change_id','candidate','base','policy_hash','selection',
            'limits','security','language','status','phase','calls_start','tokens_start','started_ns','updated_ns','deadline_ns',
            'corrections_used','events'}
    if (not isinstance(value,dict) or set(value)!=fields or value['schema']!=1 or value['project']!=identity(root)
            or value['run_id']!=run_id or value['session_id']!=session_id
            or value['status'] not in ('running','stopped','escalated','recorded')
            or value['phase'] not in ('explore','plan','implement','validate','security','review')
            or not isinstance(value['events'],list) or len(value['events'])>64):
        raise ValueError('Unknown or foreign native task run is preserved')
    identifier(session_id);identifier(value['change_id'])
    for key in ('calls_start','tokens_start','started_ns','updated_ns','deadline_ns','corrections_used'):
        if type(value[key]) is not int or value[key]<0:raise ValueError('Invalid task checkpoint counter')
    return value


def active(root):
    if not safe_file(root,ACTIVE).exists():return None
    value=authentication.verify(root,read_record(root,ACTIVE,16000))
    if not isinstance(value,dict) or set(value)!={'schema','project','run_id'} or value['schema']!=1 or value['project']!=identity(root):
        raise ValueError('Unknown task-run owner is preserved')
    path(value['run_id']);return value['run_id']


def save(root,value):
    if len(encoded(value))>60000:raise ValueError('Task-run checkpoint exceeds its bound')
    atomic_write(safe_file(root,path(value['run_id'])),encoded(authentication.seal(root,value))+'\n',mode=0o600)
    es=value['language']=='es'
    body=stamp(('# Ciclo de tarea nativo' if es else '# Native task cycle')+' — '+value['run_id']+'\n\n'
        +('Estado local registrado; no autoriza entrega ni acredita fases no ejecutadas.' if es else
          'Recorded local state; this does not authorize delivery or attest unexecuted phases.')+'\n\n```json\n'
        +encoded({k:value[k] for k in ('status','phase','change_id','selection','limits','security','corrections_used','events')})+'\n```')
    write_document(root,dossier(value['change_id'])+'/task-runs/'+value['run_id']+'.md',body,replace_generated=True)
