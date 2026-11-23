"""Bounded signed review history and conservative Markdown projection."""
import hashlib
import os
from aikya.core.checkpoints import safe_file
from aikya.documentation.layout import stamp, index_paths, write_document
from .authentication import verify
from .contracts import encoded, read_record


def history(root, own):
    folder=safe_file(root,own+'/reviews/.probe').parent
    if not folder.exists(): return []
    records=[]
    with os.scandir(folder) as entries:
        for i,entry in enumerate(entries):
            if i>=128 or entry.is_symlink(): raise ValueError('Review history limit or unsafe path')
            if not entry.is_dir(): raise ValueError('Unknown review history entry')
            relative=own+'/reviews/'+entry.name+'/review.json'
            if not safe_file(root,relative).exists(): continue
            record=read_record(root,relative,65536); value=verify(root,record)
            if value.get('schema')!=1 or value.get('generated_by')!='aikya-admitted-review': raise ValueError('Unknown review schema')
            records.append(value)
    return records


def report_body(candidate, request, event):
    from aikya.documentation.language import validate
    es=validate(request.get('docs_language','en'))=='es'
    return stamp(('# Revisión independiente' if es else '# Independent review')
                 +'\n\n'+('- Candidato: ' if es else '- Candidate: ')+candidate['id']
                 +('\n- Decisión: ' if es else '\n- Decision: ')+event['decision']
                 +('\n- Sesión del revisor: ' if es else '\n- Reviewer session: ')+request['reviewer_session']
                 +'\n\n```json\n'+encoded(event['findings'])+'\n```')


def publish_report(root, own, body):
    report=safe_file(root,own+'/review.md'); pointer=safe_file(root,own+'/review.json')
    expected=hashlib.sha256(body.encode()).hexdigest()
    if report.exists():
        actual=hashlib.sha256(report.read_bytes()).hexdigest()
        if actual!=expected:
            if not pointer.exists(): raise ValueError('Custom review report is preserved')
            previous=verify(root,read_record(root,own+'/review.json',65536))
            if previous['report_hash']!=actual: raise ValueError('Modified review report is preserved')
    index_paths(root)
    write_document(root,own+'/review.md',body,replace_generated=True)
    return expected
