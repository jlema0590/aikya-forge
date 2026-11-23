"""CLI rendering/lifecycle of existing-project analysis over the canonical engine."""
import json
import sys


def execute(args,target,lifecycle):
    from aikya.discovery.analyze import execute
    try:
        result=execute(target,scope=args.scope,focus=args.focus,
                       approved=args.approved,refresh=args.refresh,
                       dry_run=args.dry_run,report_only=args.report_only,docs_lang=args.docs_lang,methodology=args.methodology,observer=lifecycle)
    except (ValueError,OSError,UnicodeError,TypeError) as exc:
        print('ERROR during analysis:',exc,file=sys.stderr)
        lifecycle.event('explore','failed',reason=str(exc));lifecycle.finish('failed',str(exc))
        return 2
    lifecycle.result(result,preview=args.dry_run or args.report_only)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='READY' else 4
