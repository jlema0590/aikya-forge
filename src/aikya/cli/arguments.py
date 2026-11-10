"""Support-command options and explicit default-terminal argument recognition."""
import argparse
from pathlib import Path


def _default_terminal_arguments(arguments):
    values={'--target','--runtime-dir','--provider','--model'};flags={'--resume','--print-command'}
    index=0
    while index<len(arguments):
        item=arguments[index];name=item.split('=',1)[0]
        if name in values:index+=1 if '=' in item else 2
        elif item in flags:index+=1
        else:return False
    return True



def support_parser():
    parser=argparse.ArgumentParser(description='Aikya Forge project and runtime support commands',
        epilog='Run aikya without a subcommand to open the installed terminal; use aikya terminal --help for session and model options.')
    parser.add_argument('command',choices=['probe','requirements','init','answers','status','analyze','feature','bugfix','implement','memory','context','context-policy','review','terminal'])
    parser.add_argument('--target',type=Path,default=Path.cwd())
    parser.add_argument('--answers',type=Path)
    parser.add_argument('--summary',action='store_true',help='Compact response; retain blocking reasons and omission counts')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--strict',action='store_true',help='Fail with exit 4 if SDK requirements are incomplete')
    parser.add_argument('--external',choices=['skip','plan','install'],default='plan')
    parser.add_argument('--display-name')
    parser.add_argument('--scope',default='.')
    parser.add_argument('--focus',choices=['general','security','architecture','infrastructure','operations'],default='general')
    parser.add_argument('--docs-lang',choices=['en','es'],default=None,help='Aikya living documentation language')
    parser.add_argument('--methodology', choices=['odd', 'sdd', 'standard'], default=None)
    parser.add_argument('--session',default=__import__('os').environ.get('CLAUDE_SESSION_ID','local'))
    parser.add_argument('--execution-details',action='store_true')
    parser.add_argument('--refresh',action='store_true')
    parser.add_argument('--report-only',action='store_true')
    parser.add_argument('--approved',action='store_true',help='Explicit approval to create Aikya-owned files')
    parser.add_argument('--agent-loop',action='store_true',help='Explicit bounded execution for feature, bugfix or implement only')
    parser.add_argument('--loop-input',type=Path,help='Reviewed agent loop JSON, including scoped files, checks and budgets')
    parser.add_argument('--loop-run-id',help='Resume a durable loop without resetting limits')
    return parser
