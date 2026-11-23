"""Contributor-only review capture of exact public PyPI binary parser recipes."""
import argparse
import json
from pathlib import Path
from urllib.request import Request,urlopen
from aikya.installation.bootstrap.code_index import PINS
from aikya.installation.managed_inputs import TARGETS
from aikya.installation.managed_parsers import compatible


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('Existing parser recipe is preserved; capture to a new review file')
    metadata={}
    for name,version in PINS.items():
        url='https://pypi.org/pypi/'+name+'/'+version+'/json'
        with urlopen(Request(url,headers={'User-Agent':'aikya-forge-parser-review'}),timeout=30) as response:
            if response.status!=200 or response.geturl()!=url:raise ValueError('Unexpected public metadata response')
            raw=response.read(2000001)
        if len(raw)>2000000:raise ValueError('Oversized package metadata')
        value=json.loads(raw)
        if value['info']['version']!=version:raise ValueError('Package pin drift')
        metadata[name]=[item for item in value['urls'] if item['packagetype']=='bdist_wheel' and not item['yanked']]
    result=dict(schema=1,python='3.13',platforms={})
    for target in TARGETS:
        selected={}
        for name,items in metadata.items():
            matches=sorted((item for item in items if compatible(item['filename'],target)),key=lambda item:item['filename'])
            if not matches:continue
            item=matches[0];selected[name]=dict(file=item['filename'],url=item['url'],version=PINS[name],sha256=item['digests']['sha256'])
        result['platforms'][target]=selected if 'tree-sitter' in selected else {}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({target:sorted(entries) for target,entries in result['platforms'].items()},indent=2))


if __name__=='__main__':main()
