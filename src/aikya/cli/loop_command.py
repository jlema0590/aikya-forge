"""Explicit legacy loop execution remains separate from the native Pi terminal."""
import json
import sys


def execute(args,target,parser):
    if not args.agent_loop or args.command not in ('feature','bugfix','implement') or not args.loop_input or args.dry_run or args.report_only:
        parser.error('feature/bugfix/implement require --agent-loop and --loop-input; onboarding never starts a loop')
    from aikya.core.loop import run
    try:
        if args.loop_input.is_symlink() or not args.loop_input.is_file() or args.loop_input.stat().st_size>100_000:raise ValueError('Reviewed regular loop JSON required')
        raw=json.loads(args.loop_input.read_text())
        if not isinstance(raw,dict):raise ValueError('Reviewed loop input must be a JSON object')
        if raw.get('command')!='aikya-'+args.command:raise ValueError('Loop command does not match the requested command')
        result=run(target,raw,approved=args.approved,run_id=args.loop_run_id)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result['status']=='completed' else 4
    except (ValueError,OSError,TypeError,KeyError) as exc:
        print('ERROR: '+str(exc),file=sys.stderr);return 2
