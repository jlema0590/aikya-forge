"""Validate executor metadata without treating repository JSON as host consent."""
from .contracts import dossier, identifier, hash_id, read_record

STATUSES = ('completed', 'failed', 'unverified', 'invalid_report', 'timed_out', 'cancelled',
            'output_limit', 'launch_failed', 'definition_changed', 'candidate_changed')


def execution_metadata(root, candidate, path):
    data = read_record(root, path, 65_536)
    keys = {'schema', 'generated_by', 'project', 'candidate', 'session_id', 'run_id', 'check',
            'definition_hash', 'argv_hash', 'status', 'exit_code', 'counts', 'started_ns',
            'finished_ns', 'duration_ns', 'stdout_bytes', 'stderr_bytes', 'stdout_sha256',
            'stderr_sha256', 'report_sha256', 'report_format'}
    if (not isinstance(data, dict) or set(data) != keys or type(data['schema']) is not int
            or data['schema'] != 1 or data['generated_by'] != 'aikya-check-executor'
            or data['project'] != candidate['project'] or data['candidate'] != candidate['id']
            or data['session_id'] != candidate['session_id'] or data['status'] not in STATUSES):
        raise ValueError('Invalid executor metadata')
    identifier(data['run_id']); identifier(data['check'])
    if path != dossier(candidate['change_id']) + '/checks/' + data['run_id'] + '/execution.json':
        raise ValueError('Execution evidence is not in its owned run directory')
    if candidate['policy'].get('definitions', {}).get(data['check']) != data['definition_hash']:
        raise ValueError('Execution definition differs from frozen policy')
    for field in ('definition_hash', 'argv_hash', 'stdout_sha256', 'stderr_sha256'):
        hash_id(data[field])
    if data['report_sha256'] is not None: hash_id(data['report_sha256'])
    if data['report_format'] not in ('junit', 'trx', 'tap', 'go-json','process'):
        raise ValueError('Unknown execution report format')
    process=data['report_format']=='process'
    if process!=(candidate['policy'].get('check_types',{}).get(data['check'],'test')=='process'):
        raise ValueError('Execution type differs from frozen policy')
    for field in ('started_ns', 'finished_ns', 'duration_ns', 'stdout_bytes', 'stderr_bytes'):
        if type(data[field]) is not int or data[field] < 0:
            raise ValueError('Invalid execution timing or size')
    if data['finished_ns'] < data['started_ns']:
        raise ValueError('Invalid execution timing')
    code, counts = data['exit_code'], data['counts']
    if process and counts is not None:raise ValueError('Process validators cannot report test counters')
    if code is not None and (type(code) is not int or not -2147483648 <= code <= 4294967295):
        raise ValueError('Invalid execution exit code')
    if counts is not None:
        if (not isinstance(counts, dict) or set(counts) != {'executed', 'failed', 'skipped'}
                or any(type(v) is not int or not 0 <= v <= 10000 for v in counts.values())):
            raise ValueError('Invalid execution counters')
    if data['status'] == 'completed' and (code != 0 or (not process and
            (not counts or counts['executed'] == 0 or counts['failed'] or counts['skipped']))):
        raise ValueError('Unverified execution cannot be completed')
    if candidate['policy'].get('native_observations'):
        from .observations import verify
        verify(root,candidate,data)
    return data
