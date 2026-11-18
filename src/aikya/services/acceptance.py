"""Privacy-bounded local usage observations; never provider acceptance or publishing consent."""
import argparse
import hashlib
import json
from importlib.metadata import version,PackageNotFoundError
from pathlib import Path
import sys
from aikya.code_index.policy import project_root
from aikya.core.checkpoints import safe_file
from aikya.installation import managed_runtime
from aikya.review.contracts import digest,parse
from aikya.routing import pi_usage
from aikya.storage import write_new


def _runtime():
    try:
        current=managed_runtime.resolve()
        if Path(current['python']).resolve()!=Path(sys.executable).resolve():return None,None
        payload=managed_runtime._path(Path(current['root']),'terminal/versions/'+current['manifest_hash'])
        manifest_raw=managed_runtime._read(payload/'manifest.json',16000000)
        if hashlib.sha256(manifest_raw).hexdigest()!=current['manifest_hash']:return None,None
        manifest=parse(manifest_raw)
        raw=managed_runtime._read(payload/'provenance.json',8000000)
        if hashlib.sha256(raw).hexdigest()!=manifest['files']['provenance.json']['sha256']:return None,None
        value=parse(raw)
        return current['version'],digest(dict(core=value['core']['source']['files'],runtime=value['runtime']['files']))
    except (ValueError,OSError,KeyError,TypeError):return None,None


def _label(kind,value):return kind+'-'+hashlib.sha256(value.encode()).hexdigest()[:16]


def snapshot(root):
    root=project_root(root);usage=pi_usage.status(root);runtime,fingerprint=_runtime()
    try:package=version('aikya-harness')
    except PackageNotFoundError:package=None
    uncertain=usage.get('uncertain_calls',[]);groups=[]
    for value in usage.get('groups',[]):
        complete=value['usage_complete']
        groups.append(dict(role=value['role'] if value['role'] in ('author','reviewer','compaction') else 'other',
            phase=value['phase'],provider_id=_label('provider',value['provider']),model_id=_label('model',value['model']),
            calls=value['calls'],usage_complete=complete,recorded_tokens=value['recorded_tokens'] if complete else None,
            known_recorded_tokens=value['recorded_tokens']))
    return dict(schema=1,generated_by='aikya-provider-observation',package_version=package,runtime_version=runtime,
        runtime_fingerprint=fingerprint,status=usage['status'],recorded_tokens=usage.get('recorded_tokens') if not uncertain else None,
        known_recorded_tokens=usage.get('recorded_tokens'),calls=usage['calls'],uncertain_calls=len(uncertain),groups=groups,
        grouped_calls=usage.get('grouped_calls',0),groups_truncated=usage.get('grouped_calls',0)!=usage['calls'],
        provider_verified=False,quota_windows=None,quota_savings=None,
        note='Local host observations only; provider IDs are pseudonymized. No prompts, keys or project paths. External acceptance requires separate review.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('export',))
    parser.add_argument('--target',type=Path,default=Path.cwd());parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        root=project_root(args.target);relative=args.output.relative_to(root).as_posix() if args.output.is_absolute() else args.output.as_posix()
        if not relative.startswith('aikya/docs/validation/') or not relative.endswith('.json'):raise ValueError('Export inside project aikya/docs/validation/ as JSON')
        target=safe_file(root,relative)
        if target.exists():raise ValueError('Existing evidence export is preserved; choose a new filename')
        value=snapshot(root);target.parent.mkdir(parents=True,exist_ok=True);safe_file(root,relative)
        write_new(target,json.dumps(value,indent=2)+'\n',mode=0o600)
        print(json.dumps(dict(status='exported_observation',provider_verified=False,path=relative)));return 0
    except (ValueError,OSError,TypeError) as error:
        print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
