"""Render canonical append-only bug records in a bounded captured document snapshot."""
from pathlib import Path
import tempfile
from aikya.code_index.policy import read_source
from aikya.core.checkpoints import safe_file
from aikya.documentation import templates
from aikya.documentation.layout import generated
from aikya.review.contracts import encoded
from .documentation_inputs import sha

PATH='aikya/docs/bugs/bugs.md'


def document(root,payload,profile,language,pages):
    target=safe_file(root,PATH);before=read_source(root,PATH,12000).decode() if target.exists() else None
    if before is not None and not generated(before):raise ValueError('Customized bug register is preserved')
    if PATH in pages and (before is None or sha(before.encode())!=pages[PATH]):raise ValueError('Managed bug register changed outside this workflow')
    with tempfile.TemporaryDirectory(prefix='aikya-bug-preview-') as tmp:
        stage=Path(tmp);(stage/'.harness').mkdir();(stage/'.harness/project-profile.json').write_text(encoded(dict(decisions=profile)))
        (stage/'.aikya').mkdir();(stage/'.aikya/docs-policy.json').write_text(encoded(dict(schema_version=1,language=language)))
        if before is not None:
            old=stage/PATH;old.parent.mkdir(parents=True);old.write_text(before)
        templates.record(stage,templates.BUG,payload,approved=True)
        after=(stage/PATH).read_text()
    if len(after.encode())>12000:raise ValueError('Bug register needs reviewed archival before another native append')
    return dict(path=PATH,before=before,after=after,templates=[templates.BUG],evidence_hashes={})
