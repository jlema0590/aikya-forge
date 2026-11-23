"""Content snapshots including tests, configuration and new project files."""
import hashlib
import os
from pathlib import Path
import subprocess
from aikya.code_index.policy import excluded, project_root, read_source
from aikya.core.checkpoints import identity, safe_file
from aikya.core.state import locked
from aikya.storage import atomic_write
from .contracts import identifier, digest, hash_id, encoded, dossier, read_record, policy as checked_policy

MAX_FILES = 12_000
MAX_BYTES = 100_000_000


def _derived_index(raw):
    from aikya.documentation.layout import derived_index
    return derived_index(raw)


def _base(root):
    if not (root / '.git').exists():
        return None
    if (root / '.git').is_symlink():
        raise ValueError('Symlinked Git metadata')
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', 'rev-parse', '--verify', 'HEAD'],
                            cwd=root, env=env, capture_output=True, timeout=5)
    if result.returncode:
        refs = subprocess.run(['git', 'show-ref', '--head'], cwd=root, env=env, capture_output=True, timeout=5)
        if refs.returncode == 1 and not refs.stdout:
            return None  # Unborn repository, still bound to checkout identity.
        raise ValueError('Cannot establish Git base')
    value = result.stdout.decode('ascii').strip()
    if len(value) not in (40, 64) or any(c not in 'abcdef0123456789' for c in value):
        raise ValueError('Invalid Git base')
    return value


def _files(root, own_dossier):
    result, total, examined = {}, 0, 0
    def fail(error):
        raise ValueError('Incomplete candidate inventory') from error
    for folder, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        current = Path(folder)
        if current != root and (current / '.git').exists():
            raise ValueError('Nested repositories require a separate candidate')
        for name in sorted(dirs + names):
            examined += 1
            if examined > MAX_FILES * 10:
                raise ValueError('Candidate inventory limit exceeded')
            path = current / name
            relative = path.relative_to(root).as_posix()
            if excluded(relative) or relative == own_dossier or relative.startswith(own_dossier + '/'):
                if name in dirs:
                    dirs.remove(name)
                continue
            if path.is_symlink():
                raise ValueError('Symlinked candidate source')
            if name in dirs:
                continue
            raw = read_source(root, relative, 10_000_000)
            if relative=='aikya/docs/indice.md' and _derived_index(raw):
                continue
            total += len(raw)
            if len(result) >= MAX_FILES or total > MAX_BYTES:
                raise ValueError('Candidate content limit exceeded')
            result[relative] = hashlib.sha256(raw).hexdigest()
    return dict(sorted(result.items()))


def freeze_candidate(root, change_id, scope, *, session_id, policy=None, parent=None):
    root = project_root(root)
    own = dossier(change_id)
    identifier(session_id)
    if parent is not None:
        hash_id(parent)
    if (not isinstance(scope, list) or not 1 <= len(scope) <= 100
            or any(not isinstance(p, str) for p in scope) or len(set(scope)) != len(scope)):
        raise ValueError('Explicit unique change scope required')
    for relative in scope:
        safe_file(root, relative)
        if excluded(relative) or relative == own or relative.startswith(own + '/'):
            raise ValueError('Control or excluded path in change scope')
    payload = dict(schema=1, generated_by='aikya-rdd', project=identity(root), change_id=change_id,
                   session_id=session_id, scope=sorted(scope), policy=checked_policy(policy),
                   parent=parent, base=_base(root), files=_files(root, own))
    _validate_tdd(root,payload)
    if len(encoded(payload)) > 1_900_000:
        raise ValueError('Candidate metadata limit exceeded')
    return {**payload, 'id': digest(payload)}


def _validate_tdd(root,candidate):
    for field in ('tdd','baseline'):
        for path in candidate['policy'].get(field,{}).get('paths',[]):
            safe_file(root,path)
            if excluded(path) or path not in candidate['scope'] or path not in candidate['files']:
                raise ValueError('Lineage tests must be present in the explicit candidate scope')


def validate(root, candidate):
    keys = {'schema', 'generated_by', 'project', 'change_id', 'session_id', 'scope', 'policy', 'parent', 'base', 'files', 'id'}
    if (not isinstance(candidate, dict) or set(candidate) != keys or type(candidate['schema']) is not int
            or candidate['schema'] != 1 or candidate['generated_by'] != 'aikya-rdd'
            or candidate['project'] != identity(root)):
        raise ValueError('Invalid candidate or project mismatch')
    identifier(candidate['change_id']); identifier(candidate['session_id'])
    checked_policy(candidate['policy']); hash_id(candidate['id'])
    if candidate['parent'] is not None:
        hash_id(candidate['parent'])
    scope = candidate['scope']
    if (not isinstance(scope, list) or not 1 <= len(scope) <= 100
            or any(not isinstance(p, str) for p in scope) or len(set(scope)) != len(scope)):
        raise ValueError('Invalid persisted change scope')
    own = dossier(candidate['change_id'])
    for relative in scope:
        safe_file(root, relative)
        if excluded(relative) or relative == own or relative.startswith(own + '/'):
            raise ValueError('Invalid persisted change scope')
    base = candidate['base']
    if base is not None and (not isinstance(base, str) or len(base) not in (40, 64)
                             or any(c not in 'abcdef0123456789' for c in base)):
        raise ValueError('Invalid persisted Git base')
    if not isinstance(candidate['files'], dict) or len(candidate['files']) > MAX_FILES:
        raise ValueError('Invalid candidate inventory')
    for relative, value in candidate['files'].items():
        safe_file(root, relative); hash_id(value)
        if excluded(relative) or relative.startswith(own + '/'):
            raise ValueError('Invalid persisted inventory path')
    _validate_tdd(root,candidate)
    if digest({k: v for k, v in candidate.items() if k != 'id'}) != candidate['id']:
        raise ValueError('Candidate content identity mismatch')
    return candidate


def is_current(root, candidate):
    try:
        validate(root, candidate)
        fresh = freeze_candidate(root, candidate['change_id'], candidate['scope'],
                                 session_id=candidate['session_id'], policy=candidate['policy'], parent=candidate['parent'])
        return fresh['id'] == candidate['id']
    except (ValueError, OSError, subprocess.SubprocessError):
        return False


def load_candidate(root, change_id):
    root = project_root(root)
    value = read_record(root, dossier(change_id) + '/candidate.json')
    validate(root, value)
    if value['change_id'] != change_id:
        raise ValueError('Candidate dossier mismatch')
    historical = read_record(root, dossier(change_id) + '/candidates/' + value['id'] + '.json')
    if historical != value:
        raise ValueError('Current candidate disagrees with its immutable manifest')
    return value



def require_scope(previous,candidate,root=None):
    changed={p for p in previous['files'].keys()|candidate['files'].keys()
             if previous['files'].get(p)!=candidate['files'].get(p)}
    outside=changed-set(candidate['scope'])
    if outside:
        from .document_transitions import observed
        observed(root,previous,candidate,outside)


def store_candidate(root, candidate, *, approved=False):
    root = project_root(root)
    if approved is not True:
        raise ValueError('Candidate storage requires explicit host authorization')
    validate(root, candidate)
    relative = dossier(candidate['change_id'])
    pointer = safe_file(root, relative + '/candidate.json')
    safe_file(root, relative + '/.lock')
    pointer.parent.mkdir(parents=True, exist_ok=True)
    with locked(pointer.parent):
        if not is_current(root, candidate):
            raise ValueError('Candidate changed before persistence')
        previous = load_candidate(root, candidate['change_id']) if pointer.exists() else None
        if previous and previous['id'] != candidate['id'] and candidate['parent'] != previous['id']:
            raise ValueError('Successor must bind the current parent')
        if previous:
            require_scope(previous,candidate,root)
        if previous is None and candidate['parent'] is not None:
            raise ValueError('Missing parent candidate')
        history = safe_file(root, relative + '/candidates/' + candidate['id'] + '.json')
        if history.exists() and read_record(root, history.relative_to(root).as_posix()) != candidate:
            raise ValueError('Historical candidate is protected')
        atomic_write(history, encoded(candidate) + '\n')
        atomic_write(pointer, encoded(candidate) + '\n')
    return candidate
