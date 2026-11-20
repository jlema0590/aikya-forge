"""Deterministic native skill withdrawal; previews never grant confirmation."""
import argparse
import json
from pathlib import Path
import sys
from aikya.services import skill_removal,skill_management


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('status','uninstall','remove','restore','recover'))
    parser.add_argument('--target',type=Path,default=Path.cwd())
    parser.add_argument('--scope',choices=('project','local','global'),default='project')
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument('--name',action='append');selection.add_argument('--all',action='store_true')
    parser.add_argument('--operation',help='Completed withdrawal operation to restore')
    parser.add_argument('--yes',action='store_true',help='Explicitly confirm the reviewed local operation')
    args=parser.parse_args(argv);scope='project' if args.scope=='local' else args.scope
    try:
        if args.action=='status':
            if args.name or args.all or args.operation or args.yes:raise ValueError('Status is read-only and takes no selection')
            result=skill_management.status(args.target,scope)
        elif args.action=='recover':
            if args.name or args.all or args.operation:raise ValueError('Recovery uses the pending owned operation')
            preview=skill_removal.recovery_preview(args.target,scope)
            result=skill_removal.recover(args.target,preview['plan'],approved=True) if args.yes else dict(status='preview',**preview)
        else:
            if not args.name and not args.all:raise ValueError('Select --name explicitly or --all')
            preview=skill_removal.preview(args.target,scope,names='all' if args.all else args.name,
                action='remove' if args.action in ('uninstall','remove') else 'restore',operation_id=args.operation)
            if preview['plan'] is None:result=dict(status='no_op',**preview['review'])
            else:result=skill_removal.apply(args.target,preview['plan'],approved=True) if args.yes else dict(status='preview',**preview)
        print(json.dumps(result));return 0
    except (ValueError,OSError,TypeError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
