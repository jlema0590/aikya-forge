"""Run one explicitly approved, frozen check and retain only bounded metadata."""
import hashlib
import os
from aikya.code_index.policy import project_root, read_source
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from .candidates import load_candidate, is_current
from .contracts import identifier, dossier, digest, encoded, read_record
from .definitions import check_binding, prepare_definition
from .process import capture_process
from .reports import parse_report
from .receipts import record_execution


def _guard_incomplete(root, folder, check):
    if not folder.exists(): return
    with os.scandir(folder) as entries:
        for index, entry in enumerate(entries):
            if index >= 200: raise ValueError('Check attempt budget exhausted')
            if entry.is_symlink(): raise ValueError('Unsafe check attempt path')
            if not entry.is_dir(): continue
            relative = (folder / entry.name / 'execution.json').relative_to(root).as_posix()
            previous = read_record(root, relative, 65536)
            if not isinstance(previous, dict) or previous.get('generated_by') != 'aikya-check-executor':
                raise ValueError('Unknown check attempt requires reconciliation')
            if previous.get('status') == 'pending' and previous.get('check') == check:
                raise ValueError('Prior execution is uncertain; reconcile without launching another attempt')


def run_check(root, change_id, definition, *, session_id, run_id, approved=False, environment=None, cancel=lambda: False):
    if approved is not True:
        raise ValueError('Check execution requires explicit host approval')
    root = project_root(root); identifier(run_id); identifier(session_id)
    binding, cwd, env, executable = prepare_definition(root, definition, environment)
    own = dossier(change_id)
    evidence = own + '/checks/' + run_id + '/execution.json'
    target = safe_file(root, evidence)
    with locked(safe_file(root, own + '/.lock').parent):
        candidate = load_candidate(root, change_id)
        if (candidate['session_id'] != session_id or not is_current(root, candidate)
                or candidate['policy'].get('definitions', {}).get(definition['name']) != binding):
            raise ValueError('Session, candidate or approved definition changed')
        process=definition['report_format']=='process'
        if process!=(candidate['policy'].get('check_types',{}).get(definition['name'],'test')=='process'):
            raise ValueError('Execution type differs from frozen policy')
        _guard_incomplete(root, target.parent.parent, definition['name'])
        if target.parent.exists():
            raise ValueError('Run identity already exists; reconcile without re-executing')
        target.parent.mkdir(parents=True)
        metadata = dict(schema=1, generated_by='aikya-check-executor', project=candidate['project'],
            candidate=candidate['id'], session_id=session_id, run_id=run_id, check=definition['name'],
            definition_hash=binding, argv_hash=digest(definition['argv']), status='pending')
        atomic_write(target, encoded(metadata) + '\n')
    report = target.parent / 'report.xml'
    argv = [executable, *(a.replace('{report}', str(report)) for a in definition['argv'][1:])]
    env['AIKYA_TEST_REPORT'] = str(report)
    observed, stdout = capture_process(argv, cwd, env, definition['timeout_seconds'], definition['max_output_bytes'], cancel)
    metadata.update(observed, counts=None, report_sha256=None, report_format=definition['report_format'])
    try:
        if metadata['status'] == 'completed':
            raw = (read_source(root, report.relative_to(root).as_posix(), 1_048_576)
                   if definition['report_format'] in ('junit', 'trx') else stdout)
            metadata['report_sha256'] = hashlib.sha256(raw).hexdigest()
            if definition['report_format']!='process':metadata['counts'] = parse_report(definition['report_format'], raw)
            counts = metadata['counts']
            if metadata['exit_code'] != 0 or (counts and counts['failed']):
                metadata['status'] = 'failed'
            elif counts and (counts['executed'] == 0 or counts['skipped']):
                metadata['status'] = 'unverified'
    except (ValueError, OSError):
        metadata['status'] = 'failed' if metadata['exit_code'] not in (0, None) else 'invalid_report'
    finally:
        # Only the fresh owned report path is removed. Never follow a report link.
        if report.is_symlink() or report.is_file(): report.unlink()
    try:
        if check_binding(root, definition, environment) != binding:
            metadata['status'] = 'definition_changed'
    except (ValueError, OSError):
        metadata['status'] = 'definition_changed'
    if not is_current(root, candidate): metadata['status'] = 'candidate_changed'
    if candidate['policy'].get('native_observations'):
        from .observations import record as record_observation
        record_observation(root,candidate,metadata)
    atomic_write(target, encoded(metadata) + '\n')
    if metadata['status'] != 'candidate_changed': record_execution(root, candidate, evidence)
    return dict(status=metadata['status'], run_id=run_id, candidate=candidate['id'],
                evidence=evidence, counts=metadata['counts'])
