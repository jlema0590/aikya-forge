"""Validate separately reviewed provider trials; this read-only gate never publishes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from aikya.core.checkpoints import safe_file
from aikya.installation import build_sources, managed_runtime, managed_versions, managed_wheel
from aikya.review.contracts import digest, hash_id, parse

CHECKS=('positive_budget','exhaustion','unknown_usage','cancellation','compaction',
        'resumption','independent_review','quota_provenance','comparative_trials')
DOSSIER='aikya/docs/validation/'


def runtime_fingerprint(source):
    source=Path(source).resolve(strict=True)
    core=build_sources.capture(source,files=managed_wheel.FILES,directories=('src',))
    runtime=build_sources.capture(source/'packages/aikya-pi',files=('package.json','package-lock.json'),directories=('src',))
    return digest(dict(core={n:hashlib.sha256(v).hexdigest() for n,v in core.items()},
                       runtime={n:hashlib.sha256(v).hexdigest() for n,v in runtime.items()}))


def record(root,relative):
    if not isinstance(relative,str) or not relative.startswith(DOSSIER) or not relative.endswith('.json'):
        raise ValueError('Acceptance evidence must be JSON inside the project validation dossier')
    try:
        raw=managed_runtime._read(safe_file(root,relative),1000000)
        value=parse(raw)
    except OSError as error:raise ValueError('Missing external acceptance evidence') from error
    if not isinstance(value,dict):raise ValueError('Acceptance evidence must be an object')
    return value,hashlib.sha256(raw).hexdigest()


def validate(source,report,version):
    managed_versions.parts(version)
    root=Path(source).resolve(strict=True);report=Path(report).absolute()
    if not report.is_relative_to(root):raise ValueError('External review must be inside the source dossier')
    value,review_hash=record(root,report.relative_to(root).as_posix())
    fingerprint=hash_id(runtime_fingerprint(root))
    if (value.get('schema')!=1 or value.get('version')!=version or value.get('runtime_fingerprint')!=fingerprint
            or value.get('review_status')!='accepted'):
        raise ValueError('External provider review is absent, pending or stale')
    for field in ('cache_conditions','review_note'):
        if not isinstance(value.get(field),str) or not 10<=len(value[field].strip())<=4000:
            raise ValueError('Explicit bounded external review notes and cache conditions required')
    if value.get('checks')!={name:'passed' for name in CHECKS}:raise ValueError('All external acceptance scenarios require review')
    count=value.get('repetitions');observations=value.get('observations')
    if type(count) is not int or not 3<=count<=10 or not isinstance(observations,list) or len(observations)!=count:
        raise ValueError('Three to ten distinct controlled observations required')
    hashes=set()
    for relative in observations:
        trial,identity=record(root,relative)
        if identity in hashes:raise ValueError('Duplicate observation content is not an independent trial')
        hashes.add(identity)
        if (trial.get('schema')!=1 or trial.get('generated_by')!='aikya-provider-observation'
                or trial.get('runtime_version')!=version or trial.get('runtime_fingerprint')!=fingerprint
                or trial.get('status')!='available' or trial.get('groups_truncated') is not False
                or type(trial.get('uncertain_calls')) is not int or trial['uncertain_calls']!=0
                or trial.get('provider_verified') is not False):
            raise ValueError('Only complete current local observations may support an external review')
        if any(type(trial.get(key)) is not int or trial[key]<=0 for key in ('recorded_tokens','calls')):
            raise ValueError('Known positive usage observations required; unknown usage cannot pass')
    return dict(status='reviewed_external_evidence',version=version,runtime_fingerprint=fingerprint,
                review_hash=review_hash,observation_count=count,publishes=False,
                note='Document validation only. A human must verify real provider provenance; local exports do not prove it.')


def readiness(source,report,version):
    try:
        validate(source,report,version)
        return dict(status='ready',ready=True,version=version,publishes=False)
    except (ValueError,OSError) as error:
        return dict(status='blocked',ready=False,version=version,publishes=False,
                    reason=' '.join(str(error).split())[:500])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--report',type=Path);parser.add_argument('--version');parser.add_argument('--fingerprint',action='store_true')
    parser.add_argument('--status',action='store_true',help='Report readiness only; does not authorize publication')
    args=parser.parse_args()
    if args.fingerprint:print(runtime_fingerprint(args.source));return
    if not args.report or not args.version:parser.error('--report and --version are required for validation')
    if not args.status:
        print(json.dumps(validate(args.source,args.report,args.version),sort_keys=True));return
    result=readiness(args.source,args.report,args.version)
    if os.environ.get('GITHUB_OUTPUT'):
        with Path(os.environ['GITHUB_OUTPUT']).open('a',encoding='utf8') as output:
            output.write('ready='+str(result['ready']).lower()+'\nstatus='+result['status']+'\n')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a',encoding='utf8') as summary:
            summary.write('## Publication readiness: **'+result['status']+'**\n\n'
                          'Technical integration is separate. Publication still requires current reviewed real-provider evidence.\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
