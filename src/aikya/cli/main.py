#!/usr/bin/env python3
"""Aikya terminal entry and backward-compatible project support commands."""
from __future__ import annotations
import json
import sys
from pathlib import Path
# Dry-run and report-only must not leave bytecode in a project-local Aikya runtime.
sys.dont_write_bytecode = True
import aikya.installation.facade as installer
from aikya.installation.requirements import check, markdown


def resolved_answers(args, target:Path) -> Path:
    if args.answers:
        path=args.answers.expanduser().resolve()
    else:
        candidates=[target/'.aikya/answers.json',target/'.harness/project-profile.json']
        path=next((p for p in candidates if p.is_file()),candidates[0])
    if not path.is_file():
        raise ValueError(f'No technical profile was found at {path}; use /aikya-init for new projects, /aikya-analyze for existing repositories, or provide --answers.')
    return path


def _main(argv=None):
    selected=sys.argv[1:] if argv is None else list(argv)
    from aikya.cli.dispatch import dispatch
    handled,result=dispatch(selected)
    if handled:return result
    from aikya.cli.arguments import support_parser
    parser=support_parser();args=parser.parse_args(selected)
    target=args.target.expanduser().resolve()
    if args.agent_loop or args.command in ('feature','bugfix','implement'):
        from aikya.cli.loop_command import execute
        return execute(args,target,parser)
    lifecycle=None
    if args.command in ('init','analyze'):
        from aikya.middleware.lifecycle import Lifecycle
        lifecycle=Lifecycle(target,args.session,'aikya-'+args.command,preview=args.dry_run or args.report_only or (args.command=='analyze' and not args.approved),methodology=args.methodology,focus=args.focus)
    if args.command=='analyze':
        from aikya.cli.analysis import execute
        return execute(args,target,lifecycle)
    if args.command in ('probe','status'):
        from aikya.cli.queries import query
        return query(args,target)
    try:
        source=resolved_answers(args,target)
        raw=json.loads(source.read_text(encoding='utf8'))
        decisions=raw.get('decisions',raw)
        if args.command=='init' and decisions.get('mode')=='existing':
            message='/aikya-init is only for new projects; use /aikya-analyze'
            print('ERROR: '+message,file=sys.stderr)
            lifecycle.event('explore','blocked',reason=message);lifecycle.finish('blocked',message);return 2
        if args.command=='init' and args.methodology is None and decisions.get('methodology') is None:
            lifecycle.done('explore','Answers parsed; methodology selection is absent')
            lifecycle.event('plan','waiting',reason='Choose ODD or SDD before creating project files')
            print(json.dumps({'status':'NEEDS_METHODOLOGY','writes':False,'methodology_options':['odd','sdd'],'recommended_methodology':'odd'}))
            return 4
        profile=installer.validated({**decisions,**({'methodology':args.methodology} if args.methodology else {})},target)
    except (ValueError,OSError,UnicodeError,TypeError) as exc:
        print('ERROR parsing answers:',exc,file=sys.stderr)
        if lifecycle:lifecycle.event('explore','failed',reason=str(exc));lifecycle.finish('failed',str(exc))
        return 2
    if args.command=='init' and profile['mode']!='new':
        print('ERROR: /aikya-init is only for new projects. Use /aikya-analyze for existing repositories; nothing was written.',file=sys.stderr)
        return 2
    if args.command=='answers' and profile['mode']=='existing':
        print('NOTICE: legacy declarative profile; use /aikya-analyze for automatic existing-repository discovery.',file=sys.stderr)
        # Compatibility shim: existing profiles remain valid but no user IaC, CI or Docker files change.
        detected=installer.detect_project(target)
        try:
            actions=installer.install(target,profile,detected,dry_run=args.dry_run,adopt_existing=True,docs_lang=args.docs_lang)
        except (ValueError,OSError,UnicodeError) as exc:
            print('ERROR during adoption:',exc,file=sys.stderr)
            return 2
        print(json.dumps({'mode':'existing','dry_run':args.dry_run,'actions':actions},
                         ensure_ascii=False,indent=2))
        return 0
    report=check(profile,target)
    print('\n=== AIKYA TOOLCHAIN REQUIREMENTS ===')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.command=='requirements':
        return 4 if args.strict and not report['ready'] else 0
    if args.strict and not report['ready']:
        print('REQUIREMENTS PENDING: request developer approval before updating SDKs.',file=sys.stderr)
        if lifecycle:
            lifecycle.done('explore','Toolchain availability inspected')
            lifecycle.event('plan','blocked',reason='Strict toolchain requirements are incomplete')
            lifecycle.finish('blocked','Strict toolchain requirements are incomplete')
        return 4
    # run through current process (same interpreter), never auto-install SDKs.
    flags=['--target',str(target),'--answers',str(source),'--external',args.external]
    if args.methodology:flags+=['--methodology',args.methodology]
    if args.dry_run: flags.append('--dry-run')
    if args.display_name: flags+=['--display-name',args.display_name]
    if args.docs_lang: flags+=['--docs-lang',args.docs_lang]
    if (target/'.aikya/bootstrap.json').exists() or (target/'.aikya/answers.json').exists(): flags.append('--allow-bootstrap')
    if lifecycle:
        lifecycle.done('explore','New-project answers and toolchain availability inspected')
        lifecycle.done('plan','Explicit methodology and installation scope confirmed')
        if not args.dry_run:lifecycle.event('implement','running','Creating approved Aikya harness files')
    result=installer.main(flags)
    if lifecycle:
        if result==0:
            if args.dry_run:lifecycle.done('validate','Installer preflight completed without writes',True);lifecycle.finish('completed')
            else:lifecycle.done('implement','Installer returned successfully');lifecycle.verify_install()
        else:lifecycle.event('implement' if not args.dry_run else 'validate','failed',reason='Installer returned exit '+str(result));lifecycle.finish('failed','Installer failed')
    if result==0 and not args.dry_run:
        from aikya.documentation.layout import append_section
        try:
            locale = __import__('aikya.documentation.language',fromlist=['*']).resolve(target, args.docs_lang)
            append_section(target, 'overview.md', 'Toolchain diagnostics' if locale == 'en' else 'Diagnóstico de herramientas', markdown(report, locale))
        except ValueError as exc:
            print('NOTICE: customized overview preserved: '+str(exc), file=sys.stderr)
        print('\nAikya installed. Resolve outstanding SDK requirements before running project generators.')
    return result

def main(argv=None):
    selected=sys.argv[1:] if argv is None else list(argv)
    if '--summary' in selected:
        from aikya.cli.summary import run_compact
        return run_compact(_main,[x for x in selected if x!='--summary'])
    return _main(selected)

if __name__=='__main__':sys.exit(main())
