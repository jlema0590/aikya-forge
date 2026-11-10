"""Conservative, bounded test-result adapters; no tool execution or raw logging."""
import re
import xml.etree.ElementTree as ET
from .contracts import parse

MAX_REPORT = 1_048_576
MAX_CASES = 10_000


def _counts(outcomes):
    if len(outcomes) > MAX_CASES:
        raise ValueError('Test report case limit exceeded')
    return dict(executed=len(outcomes) - outcomes.count('skip'),
                failed=outcomes.count('fail'), skipped=outcomes.count('skip'))


def _tag(element):
    return element.tag.rsplit('}', 1)[-1]


def _counter(attributes, name, expected):
    if name not in attributes:
        return
    value = attributes[name]
    if not re.fullmatch(r'[0-9]{1,7}', value) or int(value) != expected:
        raise ValueError('Inconsistent report counter')


def _xml(text):
    if ('<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper()
            or '\x00' in text or text.count('<') > 50_000):
        raise ValueError('Unsafe or oversized XML structure')
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError('Incomplete XML report') from exc
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth > 64: raise ValueError('XML report depth limit exceeded')
        stack.extend((child, depth + 1) for child in node)
    return root


def _junit(text):
    root = _xml(text)
    if _tag(root) not in ('testsuite', 'testsuites'):
        raise ValueError('Expected JUnit report')
    outcomes, identities, by_case = [], set(), {}
    for case in root.iter():
        if _tag(case) != 'testcase':
            continue
        name = case.get('name')
        key = (case.get('classname', ''), name)
        if not name or key in identities:
            raise ValueError('Missing or ambiguous JUnit case identity')
        identities.add(key)
        children = {_tag(c) for c in case}
        outcome = ('skip' if 'skipped' in children or case.get('status') == 'notrun'
                   else 'fail' if children & {'failure', 'error'} else 'pass')
        outcomes.append(outcome); by_case[case] = outcome
    counts = _counts(outcomes)
    for suite in root.iter():
        if _tag(suite) not in ('testsuite', 'testsuites'): continue
        cases = [c for c in suite.iter() if c in by_case]
        _counter(suite.attrib, 'tests', len(cases))
        _counter(suite.attrib, 'skipped', sum(by_case[c] == 'skip' for c in cases))
        for field, tag in (('failures', 'failure'), ('errors', 'error')):
            _counter(suite.attrib, field, sum(any(_tag(child) == tag for child in c) for c in cases))
    return counts


def _tap(text):
    plan, outcomes, numbers, trailing_plan = None, [], set(), False
    for line in text.splitlines():
        if line.lower().startswith('bail out!'):
            raise ValueError('TAP run bailed out')
        if line.startswith('TAP version') and line != 'TAP version 13':
            raise ValueError('Unsupported TAP version')
        match = re.fullmatch(r'1\.\.([0-9]+)(?:\s+#.*)?', line)
        if match:
            if plan is not None or int(match[1]) > MAX_CASES:
                raise ValueError('Duplicate or oversized TAP plan')
            plan = int(match[1]); trailing_plan = bool(outcomes); continue
        match = re.match(r'^(not )?ok\b(?:\s+([0-9]+))?(.*)$', line)
        if not match:
            continue
        if trailing_plan: raise ValueError('TAP plan cannot be inside the test stream')
        number = int(match[2]) if match[2] else len(outcomes) + 1
        if number in numbers or number < 1:
            raise ValueError('Ambiguous TAP case identity')
        numbers.add(number)
        deferred = re.search(r'#\s*(SKIP|TODO)\b', match[3], re.IGNORECASE)
        outcomes.append('skip' if deferred else 'fail' if match[1] else 'pass')
    if plan is None or numbers != set(range(1, plan + 1)):
        raise ValueError('Incomplete TAP run')
    return _counts(outcomes)


def _trx(text):
    root = _xml(text)
    if _tag(root) != 'TestRun':
        raise ValueError('Expected TRX report')
    outcomes, identities = [], set()
    for case in root.iter():
        if _tag(case) != 'UnitTestResult':
            continue
        key = case.get('executionId') or case.get('testId')
        if not key or key in identities:
            raise ValueError('Missing or ambiguous TRX identity')
        identities.add(key)
        outcome = case.get('outcome')
        if outcome not in ('Passed', 'Failed', 'NotExecuted', 'Skipped', 'Error', 'Timeout', 'Aborted',
                           'Inconclusive', 'NotRunnable', 'PassedButRunAborted', 'Warning'):
            raise ValueError('Unknown TRX outcome')
        outcomes.append('pass' if outcome == 'Passed' else 'skip' if outcome in ('NotExecuted', 'Skipped') else 'fail')
    summaries = [e for e in root.iter() if _tag(e) == 'ResultSummary']
    counters = [e for e in root.iter() if _tag(e) == 'Counters']
    if len(summaries) != 1 or len(counters) != 1:
        raise ValueError('Missing TRX summary')
    result = _counts(outcomes)
    for field, expected in (('total', len(outcomes)), ('executed', result['executed']),
                            ('passed', outcomes.count('pass')), ('failed', result['failed']), ('notExecuted', result['skipped'])):
        _counter(counters[0].attrib, field, expected)
    if summaries[0].get('outcome') not in ('Completed', 'Passed') and not result['failed']:
        raise ValueError('Unexplained TRX run failure')
    return result


def _go(text):
    cases, running, packages, closed = {}, set(), set(), {}
    for line in text.splitlines():
        event = parse(line)
        if not isinstance(event, dict):
            raise ValueError('Invalid Go event')
        action, package, case = event.get('Action'), event.get('Package'), event.get('Test')
        if not isinstance(package, str) or not package or len(package) > 1000:
            raise ValueError('Go package identity required')
        packages.add(package)
        if action not in ('start', 'run', 'pause', 'cont', 'pass', 'fail', 'skip', 'bench', 'output'):
            raise ValueError('Unsupported Go event')
        if case is not None and (not isinstance(case, str) or not case or len(case) > 1000):
            raise ValueError('Invalid Go test identity')
        if package in closed and action != 'output':
            raise ValueError('Go events after package completion')
        if case:
            key = (package, case)
            if action == 'run': running.add(key)
            if action in ('pass', 'fail', 'skip'):
                if key in cases:
                    raise ValueError('Repeated Go test result')
                cases[key] = {'pass': 'pass', 'fail': 'fail', 'skip': 'skip'}[action]
        elif action in ('pass', 'fail', 'skip'):
            closed[package] = action
    if not packages or packages != set(closed) or not running.issubset(cases):
        raise ValueError('Incomplete Go report')
    result = _counts(list(cases.values()))
    if 'fail' in closed.values(): result['failed'] = max(1, result['failed'])
    return result


def parse_report(kind, raw):
    parsers = {'junit': _junit, 'tap': _tap, 'trx': _trx, 'go-json': _go}
    if kind not in parsers or not isinstance(raw, bytes) or len(raw) > MAX_REPORT:
        raise ValueError('Unknown or oversized runner report')
    try:
        return parsers[kind](raw.decode('utf-8-sig'))
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('Invalid runner report encoding or depth') from exc
