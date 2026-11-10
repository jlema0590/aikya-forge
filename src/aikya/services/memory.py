"""Bounded read-only projection of Aikya's existing reviewed project notes."""
import json
import re
from aikya.code_index.policy import project_root, load_policy
from aikya.core.checkpoints import safe_file
from aikya.memory.knowledge import inspect_notes


def _inspect(root):
    return inspect_notes(root, limit=200, max_input_bytes=1_048_576)


def status(root):
    root=project_root(root)
    present=safe_file(root,'aikya/docs/memory/MEMORY.md').parent.is_dir()
    notes=_inspect(root)
    return dict(status='partial' if notes.diagnostics or notes.omitted_count else 'available' if present else 'not_initialized',
                index_enabled=load_policy(root).enabled, reviewed_notes=sum(n['eligible_for_recall'] for n in notes.notes),
                stale_notes=sum(n['source_status'] != 'current' or n['expired'] for n in notes.notes),
                omitted=notes.omitted_count, diagnostics=notes.diagnostics)


def search(root, query, max_chars=2000):
    root=project_root(root)
    if not isinstance(query,str) or len(query)>1000 or type(max_chars) is not int or not 512<=max_chars<=6000:
        raise ValueError('Explicit bounded memory query required')
    inspection=_inspect(root); words=set(re.findall(r'\w+',query.casefold()))
    matches=[]
    for note in inspection.notes:
        if not note['eligible_for_recall']: continue
        score=len(words & set(re.findall(r'\w+',(note['text']+' '+note['source']).casefold())))
        if score: matches.append((-score,note['id'],note))
    result=dict(notes=[], omitted=inspection.omitted_count, diagnostics=inspection.diagnostics)
    for _,_,note in sorted(matches)[:5]:
        entry={k:note[k] for k in ('id','kind','source','text')}
        result['notes'].append(entry)
        while len(json.dumps(result,ensure_ascii=True))>max_chars and entry['text']:
            entry['text']=entry['text'][:-1]
        if len(json.dumps(result,ensure_ascii=True))>max_chars or not entry['text']:
            result['notes'].pop(); break
    result['omitted']+=max(0,len(matches)-len(result['notes']))
    # Omission counter growth must also fit the complete response budget.
    while len(json.dumps(result,ensure_ascii=True))>max_chars and result['notes']:
        result['notes'].pop(); result['omitted']+=1
    return result
