"""Fail-closed aggregate of the current PR's actual reusable workflow results."""
import argparse
import json
import os
from pathlib import Path
import sys

REQUIRED=('route','contracts','python','runtime','installers','native','publication')


def evaluate(results,base):
    if base not in ('develop','main') or not isinstance(results,dict) or set(results)!=set(REQUIRED):
        raise ValueError('Complete known PR stage results and a supported base are required')
    checks=[];issues=[]
    for name in REQUIRED:
        value=results[name]
        if not isinstance(value,dict) or not isinstance(value.get('result'),str):
            raise ValueError('Malformed PR stage result')
        status=value['result']
        if status not in ('success','failure','cancelled','skipped','abandoned'):status='invalid'
        if status!='success':issues.append(name+': '+status)
        checks.append(dict(stage=name,result=status,required=True))
    if results['route']['result']=='success':
        routed=results['route'].get('outputs')
        if not isinstance(routed,dict) or routed.get('analyze')!='true' or routed.get('context')!='Forge PR acceptance | '+base:
            raise ValueError('Required acceptance must be bound to actual analysis for this target')
    publication_ready=False;publication_status='unavailable'
    if results['publication']['result']=='success':
        output=results['publication'].get('outputs')
        if not isinstance(output,dict) or (output.get('status'),output.get('ready')) not in (('ready','true'),('blocked','false')):
            raise ValueError('Truthful publication readiness metadata is required')
        publication_status=output['status'];publication_ready=output['ready']=='true'
    return dict(status='failed' if issues else 'passed',base=base,checks=checks,issues=issues,
                publication_status=publication_status,publication_ready=publication_ready,publishes=False)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--base',required=True,choices=('develop','main'))
    args=parser.parse_args(argv)
    try:
        raw=os.environ.get('AIKYA_PR_NEEDS','')
        if len(raw.encode())>65536:raise ValueError('PR stage results exceed the metadata bound')
        result=evaluate(json.loads(raw),args.base)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            rows=['# Forge PR acceptance','',f"Result: **{result['status']}**; target: `{args.base}`.",'',
                  '| Stage | Result | Required |','| --- | --- | --- |']
            rows.extend('| '+c['stage']+' | '+c['result']+' | '+('yes' if c['required'] else 'no')+' |' for c in result['checks'])
            rows.extend(['','Publication readiness: **'+result['publication_status']+'**.',
                         'Technically validated code may integrate. Publication requires current reviewed real-provider evidence.',
                         'A passing PR analysis does not merge or publish a release.',''])
            with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a',encoding='utf8') as stream:stream.write('\n'.join(rows))
        print(json.dumps(result));return 0 if result['status']=='passed' else 1
    except (ValueError,OSError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
