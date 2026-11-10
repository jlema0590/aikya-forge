"""Local RDD preview, status and explicitly approved frozen check execution."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from .candidates import freeze_candidate, store_candidate
from .controller import assess_candidate
from .contracts import read_record
from .executor import check_binding, run_check


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('snapshot', 'status', 'run'))
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--id', required=True)
    parser.add_argument('--session')
    parser.add_argument('--file', action='append', default=[])
    parser.add_argument('--parent')
    parser.add_argument('--check-definition', action='append', default=[])
    parser.add_argument('--run-id')
    parser.add_argument('--approved', action='store_true')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if args.action == 'status':
            if args.approved or args.file or args.parent or args.session or args.check_definition or args.run_id:
                parser.error('Status does not accept mutation or snapshot options')
            result = assess_candidate(root, args.id)
        elif args.action == 'run':
            if len(args.check_definition) != 1 or args.file or args.parent or not args.run_id:
                parser.error('Run requires one check definition and run ID, without snapshot options')
            definition = read_record(root, args.check_definition[0], 16000)
            result = run_check(root, args.id, definition, session_id=args.session,
                               run_id=args.run_id, approved=args.approved)
        else:
            if args.run_id or len(args.check_definition) > 20:
                parser.error('Invalid snapshot options')
            policy = None
            if args.check_definition:
                definitions = [read_record(root, path, 16000) for path in args.check_definition]
                bindings = {}
                for item in definitions:
                    binding = check_binding(root, item)
                    bindings[item['name']] = binding
                if len(bindings) != len(definitions):
                    raise ValueError('Duplicate check names')
                policy = dict(checks=list(bindings), definitions=bindings, review_required=True)
            candidate = freeze_candidate(root, args.id, args.file, session_id=args.session, parent=args.parent, policy=policy)
            if args.approved:
                store_candidate(root, candidate, approved=True)
            result = dict(candidate=candidate['id'], project=candidate['project'],
                          files=len(candidate['files']), scope=candidate['scope'],
                          parent=candidate['parent'], persisted=args.approved)
        print(json.dumps(result, ensure_ascii=True))
        return 0 if args.action != 'run' or result['status'] == 'completed' else 4
    except (ValueError, OSError, subprocess.SubprocessError):
        print('ERROR: RDD state unavailable, invalid or stale; no approval granted.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
