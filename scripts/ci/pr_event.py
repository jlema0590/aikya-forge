"""Bind source acceptance to an eligible PR lifecycle event and target."""
import argparse
import json
import os
from pathlib import Path
import sys


def route(event):
    if not isinstance(event,dict) or event.get('action') not in ('opened','synchronize','reopened'):
        raise ValueError('Supported PR event required')
    number=event.get('number');pull=event.get('pull_request');changes=event.get('changes',{})
    if type(number) is not int or number<=0 or not isinstance(pull,dict) or not isinstance(changes,dict):
        raise ValueError('Invalid PR event metadata')
    base=pull.get('base',{}).get('ref') if isinstance(pull.get('base'),dict) else None
    if base not in ('develop','main'):raise ValueError('Supported PR target required')
    return dict(analyze=True,context='Forge PR acceptance | '+base,
                group='forge-pr-'+str(number)+'-analysis')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--event',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        with args.event.open('rb') as stream:raw=stream.read(2_000_001)
        if len(raw)>2_000_000:raise ValueError('PR event exceeds its metadata bound')
        result=route(json.loads(raw))
        if os.environ.get('GITHUB_OUTPUT'):
            with Path(os.environ['GITHUB_OUTPUT']).open('a',encoding='utf8') as stream:
                stream.write('analyze='+str(result['analyze']).lower()+'\ncontext='+result['context']+'\n')
        print(json.dumps(result));return 0
    except (ValueError,OSError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
