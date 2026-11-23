"""Read-only Forge release planning; retries never replace published assets."""
import argparse
import json
import os
from pathlib import Path
import sys
import github_tag

REPOSITORY='jlema0590/aikya-forge'
ENTRIES={'install.sh','install.ps1','SHA256SUMS','terminal-bootstrap.json','release.json'}


def stable_release(value,tag):
    if (not isinstance(value,dict) or value.get('tag_name')!=tag
            or value.get('draft') is not False or value.get('prerelease') is not False
            or not isinstance(value.get('published_at'),str) or not value['published_at']):
        raise ValueError('Existing release must be published, stable and match VERSION; review it without overwriting')
    assets=value.get('assets')
    if not isinstance(assets,list) or any(not isinstance(item,dict) or not isinstance(item.get('name'),str) for item in assets):
        raise ValueError('Invalid published release asset inventory')
    names=[item['name'] for item in assets]
    if len(names)!=len(set(names)) or not ENTRIES<=set(names):
        raise ValueError('Published release is missing unique native installation entries; no assets will be replaced')


def plan(*,repository,event,ref,sha,version,publish=False,lookup=None):
    if not all(isinstance(v,str) for v in (repository,event,ref,sha,version)) or type(publish) is not bool:
        raise ValueError('Invalid release context types')
    tag='v'+version;github_tag.check_args(repository,tag,sha)
    if event not in ('push','workflow_dispatch'):raise ValueError('Only main pushes and explicit manual runs are release events')
    requested=event=='push' or publish
    result=dict(mode='prepare',version=version,tag=tag,source_commit=sha.lower(),reason='Manual artifact preparation; no publication')
    if not requested:return result
    if repository!=REPOSITORY or ref!='refs/heads/main':raise ValueError('Publication requires main in the official Forge repository')
    if lookup is None:raise ValueError('Remote release lookup is required before publication')
    release=lookup('releases/tags/'+tag,True)
    tagged=github_tag.resolve_commit(repository,tag,'',getter=lookup)
    if release is None:
        if tagged not in (None,sha.lower()):raise ValueError('Existing version tag points to another commit; never move it')
        return {**result,'mode':'publish','reason':'New stable version; all release checks remain required'}
    stable_release(release,tag)
    if tagged is None:raise ValueError('Published release has no matching version tag')
    result.update(source_commit=tagged)
    if event=='push' and tagged!=sha.lower():
        return {**result,'mode':'skip','reason':'VERSION is already published; include a new version and changelog for new releases'}
    latest=lookup('releases/latest',False)
    stable_release(latest,tag)
    return {**result,'mode':'pages','reason':'Recover latest stable Pages from original published assets; do not rebuild or replace the release'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2]);args=parser.parse_args(argv)
    try:
        def lookup(path,missing):
            token=os.environ.get('GH_TOKEN')
            if not token:raise ValueError('A read-only GitHub token is required for publication planning')
            return github_tag._get_json(os.environ.get('GITHUB_REPOSITORY',''),path,token,allow_not_found=missing)
        result=plan(repository=os.environ.get('GITHUB_REPOSITORY',''),event=os.environ.get('GITHUB_EVENT_NAME',''),
            ref=os.environ.get('GITHUB_REF',''),sha=os.environ.get('GITHUB_SHA',''),version=(args.source/'VERSION').read_text().strip(),
            publish=os.environ.get('FORGE_PUBLISH','false')=='true',lookup=lookup)
        if os.environ.get('GITHUB_OUTPUT'):
            with Path(os.environ['GITHUB_OUTPUT']).open('a',encoding='utf8') as output:
                for name in ('mode','version','tag','source_commit'):output.write(name+'='+result[name]+'\n')
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a',encoding='utf8') as summary:
                summary.write('Forge '+result['tag']+': **'+result['mode']+'**\n\n'+result['reason']+'\n')
        print(json.dumps(result));return 0
    except (ValueError,OSError) as error:print('ERROR: '+str(error),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
