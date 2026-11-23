"""Trusted Pi host budget ledger; local token activity is not account quota."""
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from aikya.core.state import locked
from aikya.review.contracts import identifier, encoded, read_record, hash_id
from aikya.storage import atomic_write

PATH = '.aikya/pi/usage.json'
COUNTS = {'input', 'output', 'cacheRead', 'cacheWrite'}
CONTEXT = {'session', 'role', 'phase', 'provider', 'model'}
PHASES = {'explore', 'plan', 'implement', 'validate', 'security', 'review'}


def _counts(value):
    if value is not None and (not isinstance(value, dict) or set(value) != COUNTS
            or any(type(v) is not int or not 0 <= v <= 10_000_000_000 for v in value.values())):
        raise ValueError('Incomplete or invalid observed usage')
    return value


def _context(value):
    if (not isinstance(value, dict) or set(value) not in (CONTEXT, CONTEXT | {'candidate', 'change_id'})
            or any(not isinstance(v, str) or not 1 <= len(v) <= 160 or any(ord(c) < 32 for c in v) for v in value.values())
            or value['phase'] not in PHASES): raise ValueError('Invalid usage provenance')
    identifier(value['session'])
    if value['role']=='reviewer':
        hash_id(value.get('candidate')); identifier(value.get('change_id'))
        if value['phase']!='review': raise ValueError('Reviewer requires review phase')
    return value


def _load(root):
    data = read_record(root, PATH, 1_048_576)
    if (not isinstance(data, dict) or set(data) != {'schema', 'generated_by', 'project', 'limits', 'events'}
            or type(data['schema']) is not int or data['schema'] != 1 or data['generated_by'] != 'aikya-pi-usage'
            or data['project'] != str(root) or not isinstance(data['limits'], dict)
            or set(data['limits']) != {'tokens', 'calls'} or not isinstance(data['events'], dict)
            or len(data['events']) > 1000): raise ValueError('Custom or incompatible Pi usage state')
    _limits(**data['limits'])
    for ident, event in data['events'].items():
        identifier(ident)
        if (not isinstance(event, dict) or set(event) != {'context', 'state', 'usage'}
                or event['state'] not in ('pending', 'recorded', 'unknown')): raise ValueError('Invalid usage event')
        _context(event['context']); _counts(event['usage'])
        if (event['state'] == 'recorded') != (event['usage'] is not None): raise ValueError('Inconsistent usage event')
    return data


def _limits(tokens, calls):
    if type(tokens) is not int or not 1 <= tokens <= 1_000_000_000 or type(calls) is not int or not 1 <= calls <= 1000:
        raise ValueError('Explicit token and call limits required')


def _report(data):
    events = data['events']; total = sum(sum(e['usage'].values()) for e in events.values() if e['usage'] is not None)
    uncertain = [ident for ident, e in events.items() if e['state'] != 'recorded']
    state = ('unknown_usage' if uncertain else 'exhausted' if total >= data['limits']['tokens']
             or len(events) >= data['limits']['calls'] else 'available')
    groups={}
    for event in events.values():
        context=event['context']; group_id=tuple(context[k] for k in ('role','phase','provider','model'))
        if group_id not in groups:
            if len(groups)>=15: continue
            groups[group_id]=dict(zip(('role','phase','provider','model'),group_id),calls=0,recorded_tokens=0,usage_complete=True)
        group=groups[group_id]; group['calls']+=1
        group['recorded_tokens']+=sum(event['usage'].values()) if event['usage'] else 0
        group['usage_complete'] &= event['state']=='recorded'
    return dict(status=state, recorded_tokens=total, calls=len(events), limits=data['limits'], groups=list(groups.values()),
                grouped_calls=sum(g['calls'] for g in groups.values()),
                remaining_tokens=max(0, data['limits']['tokens'] - total), uncertain_calls=uncertain,
                note='Local recorded token activity, not provider quota or billing')


def status(root):
    root = project_root(root); target = safe_file(root, PATH)
    if not target.exists(): return dict(status='unconfigured', recorded_tokens=None, calls=0)
    with locked(target.parent): return _report(_load(root))


def configure(root, *, tokens, calls, approved=False):
    if approved is not True: raise ValueError('Host approval required to configure budget')
    _limits(tokens, calls); root = project_root(root); target = safe_file(root, PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    with locked(target.parent):
        if target.exists():
            data = _load(root)
            if data['limits'] != dict(tokens=tokens, calls=calls): raise ValueError('Budget exists; preserve accounting')
        else:
            data = dict(schema=1, generated_by='aikya-pi-usage', project=str(root), limits=dict(tokens=tokens, calls=calls), events={})
            atomic_write(target, encoded(data) + '\n', mode=0o600)
        return _report(data)


def admit(root, call_id, context):
    root = project_root(root); identifier(call_id); _context(context); target = safe_file(root, PATH)
    if not target.exists(): raise ValueError('Configure a project budget before inference')
    with locked(target.parent):
        data = _load(root)
        if call_id in data['events'] or _report(data)['status'] != 'available':
            raise ValueError('Budget exhausted, uncertain usage or replay; no inference admitted')
        data['events'][call_id] = dict(context=dict(context), state='pending', usage=None)
        atomic_write(target, encoded(data) + '\n', mode=0o600)
        return dict(call_id=call_id, status='reserved')


def adjust(root, *, tokens, calls, approved=False):
    if approved is not True: raise ValueError('Explicit host approval required for budget adjustment')
    _limits(tokens,calls); root=project_root(root); target=safe_file(root,PATH)
    if not target.exists(): raise ValueError('Configure the budget before adjusting it')
    with locked(target.parent):
        data=_load(root); data['limits']=dict(tokens=tokens,calls=calls)
        atomic_write(target,encoded(data)+'\n',mode=0o600)
        return _report(data)


def record(root, call_id, counts, *, approved_reconciliation=False):
    root = project_root(root); identifier(call_id); _counts(counts); target = safe_file(root, PATH)
    if not target.exists(): raise ValueError('Absent usage ledger')
    with locked(target.parent):
        data = _load(root); event = data['events'].get(call_id)
        if not event: raise ValueError('Unadmitted usage result')
        if event['state'] != 'pending':
            if event['usage'] == counts: return _report(data)
            if event['state'] != 'unknown' or approved_reconciliation is not True:
                raise ValueError('Conflicting usage result; explicit reconciliation required')
        event.update(state='recorded' if counts is not None else 'unknown', usage=counts)
        atomic_write(target, encoded(data) + '\n', mode=0o600)
        return _report(data)
