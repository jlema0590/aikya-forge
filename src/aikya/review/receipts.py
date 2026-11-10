"""Hash-linked process receipts submitted by the trusted local host executor."""
import hashlib
from aikya.code_index.policy import project_root, read_source
from aikya.core.checkpoints import identity, safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from .contracts import dossier, identifier, digest, encoded, parse, hash_id, read_record
from .candidates import load_candidate, is_current, validate

MAX_RECEIPTS = 200


def _validate_payload(root, change_id, payload):
    keys = {'id', 'candidate', 'session_id', 'kind', 'check', 'argv_hash', 'exit_code',
            'executed', 'skipped', 'evidence', 'evidence_hash'}
    extra = {'definition_hash', 'execution_status', 'failed'}
    if not isinstance(payload, dict) or set(payload) not in (keys, keys | extra) or payload['kind'] != 'process':
        raise ValueError('Invalid process receipt')
    identifier(payload['id']); identifier(payload['session_id']); identifier(payload['check'])
    hash_id(payload['candidate']); hash_id(payload['evidence_hash'])
    hash_id(payload['argv_hash'])
    observed = extra.issubset(payload)
    if ((payload['exit_code'] is not None or not observed) and
            (type(payload['exit_code']) is not int or not -2147483648 <= payload['exit_code'] <= 4294967295)):
        raise ValueError('Invalid process result')
    for key in ('executed', 'skipped'):
        if payload[key] is None and observed: continue
        if type(payload[key]) is not int or not 0 <= payload[key] <= 1_000_000:
            raise ValueError('Invalid process count')
    own = dossier(change_id)
    if not isinstance(payload['evidence'], str) or not payload['evidence'].startswith(own + '/checks/'):
        raise ValueError('Foreign execution evidence')
    historical = read_record(root, own + '/candidates/' + payload['candidate'] + '.json')
    validate(root, historical)
    if historical['change_id'] != change_id or historical['id'] != payload['candidate'] or historical['session_id'] != payload['session_id']:
        raise ValueError('Receipt candidate binding mismatch')
    if payload['check'] not in historical['policy']['checks']:
        raise ValueError('Unknown check in receipt')
    bound = historical['policy'].get('definitions', {}).get(payload['check'])
    if bound and not observed:
        raise ValueError('Execution-bound check requires executor evidence')
    if observed:
        from .execution_evidence import execution_metadata
        meta = execution_metadata(root, historical, payload['evidence'])
        counts = meta['counts']
        expected = dict(definition_hash=meta['definition_hash'], execution_status=meta['status'],
                        exit_code=meta['exit_code'], argv_hash=meta['argv_hash'],
                        executed=counts['executed'] if counts else None,
                        skipped=counts['skipped'] if counts else None, failed=counts['failed'] if counts else None)
        if any(payload[k] != v for k, v in expected.items()):
            raise ValueError('Receipt differs from execution evidence')
    try:
        evidence = read_source(root, payload['evidence'], 65_536)
    except OSError as exc:
        raise ValueError('Missing execution evidence') from exc
    if not evidence or hashlib.sha256(evidence).hexdigest() != payload['evidence_hash']:
        raise ValueError('Receipt evidence changed')


def _read(root, change_id):
    path = dossier(change_id) + '/receipts.jsonl'
    target = safe_file(root, path)
    if not target.exists():
        return []
    lines = read_source(root, path, 2_000_000).splitlines()
    header = dict(schema=1, generated_by='aikya-rdd-receipts', project=identity(root), change_id=change_id)
    if not lines or parse(lines[0]) != header or len(lines) > MAX_RECEIPTS + 1:
        raise ValueError('Invalid or custom receipt journal')
    records, previous, ids = [], None, set()
    for line in lines[1:]:
        row = parse(line)
        if not isinstance(row, dict) or set(row) != {'previous', 'payload', 'hash'}:
            raise ValueError('Invalid receipt envelope')
        if row['previous'] != previous or digest({k: row[k] for k in ('previous', 'payload')}) != row['hash']:
            raise ValueError('Broken receipt chain')
        payload = row['payload']
        _validate_payload(root, change_id, payload)
        if payload['id'] in ids:
            raise ValueError('Duplicate receipt identity')
        ids.add(payload['id'])
        records.append(row); previous = row['hash']
    return records


def load_receipts(root, change_id):
    root = project_root(root)
    folder = safe_file(root, dossier(change_id) + '/.lock').parent
    if not folder.exists():
        return []
    with locked(folder):
        return _read(root, change_id)


def record_process(root, candidate, *, receipt_id, check, argv, exit_code, evidence, executed, skipped=0):
    """Record observed host results, not an assertion that this API ran the command."""
    root = project_root(root)
    identifier(receipt_id); identifier(check)
    if check not in candidate['policy']['checks']:
        raise ValueError('Check is outside the frozen policy')
    if check in candidate['policy'].get('definitions', {}):
        raise ValueError('Use the approved executor for an execution-bound check')
    if (not isinstance(argv, list) or not 1 <= len(argv) <= 100
            or any(not isinstance(a, str) or not a or len(a) > 1000 for a in argv)
            or type(exit_code) is not int or not -2147483648 <= exit_code <= 4294967295
            or any(type(n) is not int or not 0 <= n <= 1_000_000 for n in (executed, skipped))):
        raise ValueError('Invalid process evidence')
    own = dossier(candidate['change_id'])
    if not isinstance(evidence, str) or not evidence.startswith(own + '/checks/'):
        raise ValueError('Evidence must belong to the review dossier')
    raw = read_source(root, evidence, 65_536)
    if not raw:
        raise ValueError('Nonempty execution evidence required')
    payload = dict(id=receipt_id, candidate=candidate['id'], session_id=candidate['session_id'], kind='process',
                   check=check, argv_hash=digest(argv), exit_code=exit_code, executed=executed, skipped=skipped,
                   evidence=evidence, evidence_hash=hashlib.sha256(raw).hexdigest())
    return _append(root, candidate, payload)


def record_execution(root, candidate, evidence):
    from .execution_evidence import execution_metadata
    meta = execution_metadata(root, candidate, evidence)
    counts = meta['counts']
    raw = read_source(root, evidence, 65_536)
    payload = dict(id=meta['run_id'], candidate=candidate['id'], session_id=candidate['session_id'],
                   kind='process', check=meta['check'], argv_hash=meta['argv_hash'], exit_code=meta['exit_code'],
                   executed=counts['executed'] if counts else None, skipped=counts['skipped'] if counts else None,
                   failed=counts['failed'] if counts else None, definition_hash=meta['definition_hash'],
                   execution_status=meta['status'], evidence=evidence, evidence_hash=hashlib.sha256(raw).hexdigest())
    return _append(project_root(root), candidate, payload)


def _append(root, candidate, payload):
    _validate_payload(root, candidate['change_id'], payload)
    own, receipt_id = dossier(candidate['change_id']), payload['id']
    path = safe_file(root, own + '/receipts.jsonl')
    with locked(path.parent):
        current = load_candidate(root, candidate['change_id'])
        if current != candidate or not is_current(root, candidate):
            raise ValueError('Unpersisted or stale candidate')
        rows = _read(root, candidate['change_id'])
        for row in rows:
            if row['payload']['id'] == receipt_id:
                if row['payload'] != payload:
                    raise ValueError('Conflicting duplicate receipt')
                return row
        if len(rows) >= MAX_RECEIPTS:
            raise ValueError('Receipt budget exhausted')
        body = dict(previous=rows[-1]['hash'] if rows else None, payload=payload)
        record = {**body, 'hash': digest(body)}
        header = dict(schema=1, generated_by='aikya-rdd-receipts', project=identity(root), change_id=candidate['change_id'])
        raw = '\n'.join(encoded(row) for row in [header, *rows, record]) + '\n'
        if len(raw.encode()) > 2_000_000:
            raise ValueError('Receipt journal budget exhausted')
        atomic_write(path, raw)
        return record
