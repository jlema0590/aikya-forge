"""Reconcile durable observations; never execute or infer uncertain outcomes."""
import os
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from .contracts import dossier,identifier,read_record
from .candidates import load_candidate,is_current
from .receipts import load_receipts,record_execution
from .execution_evidence import execution_metadata


def plan_reconciliation(root,change_id):
    root=project_root(root);candidate=load_candidate(root,change_id);own=dossier(change_id)
    receipts=load_receipts(root,change_id);admitted={row['payload']['id'] for row in receipts}
    result=dict(candidate=candidate['id'],current=is_current(root,candidate),attempts=[])
    folder=safe_file(root,own+'/checks/.probe').parent
    if not folder.exists():return result
    with os.scandir(folder) as entries:
        for i,entry in enumerate(entries):
            if i>=200 or entry.is_symlink():raise ValueError('Unsafe or oversized execution inventory')
            if not entry.is_dir():continue
            identifier(entry.name);relative=own+'/checks/'+entry.name+'/execution.json'
            try:
                raw=read_record(root,relative,65536)
                if isinstance(raw,dict) and raw.get('status')=='pending':action='manual_reconciliation'
                else:
                    execution_metadata(root,candidate,relative)
                    action='already_attached' if entry.name in admitted else 'attach_observation' if result['current'] else 'historical_only'
            except (ValueError,OSError):action='manual_reconciliation'
            result['attempts'].append(dict(run_id=entry.name,action=action,evidence=relative))
    result['attempts'].sort(key=lambda item:item['run_id'])
    return result


def recover_execution(root,change_id,run_id,*,approved=False):
    if approved is not True:raise ValueError('Host approval required for reconciliation')
    root=project_root(root);identifier(run_id)
    plan=plan_reconciliation(root,change_id)
    attempt=next((item for item in plan['attempts'] if item['run_id']==run_id),None)
    if not plan['current'] or not attempt or attempt['action'] not in ('attach_observation','already_attached'):
        raise ValueError('Uncertain execution cannot be replayed or promoted')
    candidate=load_candidate(root,change_id)
    return record_execution(root,candidate,attempt['evidence'])
