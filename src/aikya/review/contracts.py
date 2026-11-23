"""Shared RDD identifiers, canonical encoding and bounded local records."""
import hashlib
import json
import re
from aikya.code_index.policy import read_source
from aikya.core.checkpoints import safe_file


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value):
        raise ValueError('Invalid RDD identifier')
    return value


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def hash_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-f0-9]{64}', value):
        raise ValueError('Invalid content identity')
    return value


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def parse(raw):
    try:
        return json.loads(raw, object_pairs_hook=unique_fields)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Invalid RDD JSON') from exc


def dossier(change_id):
    return 'aikya/docs/validation/' + identifier(change_id)


def read_record(root, relative, limit=2_000_000):
    safe_file(root, relative)
    try:
        return parse(read_source(root, relative, limit))
    except OSError as exc:
        raise ValueError('Missing or unreadable RDD record') from exc


def policy(value=None):
    value = {'checks': ['tests'], 'review_required': True} if value is None else value
    allowed={'checks','review_required','definitions','tdd','baseline','check_types','intent_hash','native_observations','workflow_revision'}
    if not isinstance(value, dict) or (not {'checks','review_required'}.issubset(value) or set(value)-allowed):
        raise ValueError('Invalid review policy')
    checks = value['checks']
    if (not isinstance(checks, list) or not 1 <= len(checks) <= 20
            or any(not isinstance(c, str) for c in checks) or len(set(checks)) != len(checks)
            or type(value['review_required']) is not bool):
        raise ValueError('Invalid review policy')
    result = {'checks': [identifier(c) for c in checks], 'review_required': value['review_required']}
    if 'definitions' in value:
        definitions = value['definitions']
        if not isinstance(definitions, dict) or set(definitions) != set(checks):
            raise ValueError('Every check needs a frozen execution definition')
        result['definitions'] = {key: hash_id(item) for key, item in definitions.items()}
    if 'native_observations' in value:
        if value['native_observations'] is not True or 'definitions' not in result:raise ValueError('Native observations require execution definitions')
        result['native_observations']=True
    if 'intent_hash' in value:result['intent_hash']=hash_id(value['intent_hash'])
    if 'workflow_revision' in value:result['workflow_revision']=hash_id(value['workflow_revision'])
    if 'check_types' in value:
        kinds=value['check_types']
        if (not isinstance(kinds,dict) or set(kinds)!=set(checks) or 'definitions' not in result
                or any(k not in ('test','process') for k in kinds.values())):
            raise ValueError('Invalid check types')
        result['check_types']=dict(kinds)
    if 'tdd' in value and 'baseline' in value:raise ValueError('Choose Red/Green or a positive baseline')
    for field in ('tdd','baseline'):
        if field not in value:continue
        tdd=value[field]
        if (not isinstance(tdd,dict) or set(tdd)!={'check','paths'} or tdd['check'] not in checks
                or tdd['check'] not in result.get('definitions',{}) or not isinstance(tdd['paths'],list)
                or not 1<=len(tdd['paths'])<=20 or any(not isinstance(p,str) for p in tdd['paths'])
                or len(set(tdd['paths']))!=len(tdd['paths'])
                or result.get('check_types',{}).get(tdd['check'],'test')!='test'):
            raise ValueError('Invalid test lineage policy')
        result[field]=dict(check=tdd['check'],paths=sorted(tdd['paths']))
    return result
