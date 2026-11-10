"""Build a private native v8 terminal; never publish or rewrite the stable VERSION."""
import argparse
import json
from pathlib import Path
from aikya.installation.managed_bundle import build


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parents[2])
    parser.add_argument('--assets',type=Path,help='Existing official Python/Node archives verified against pinned recipes')
    parser.add_argument('--fetch-components',action='store_true',help='Explicitly fetch pinned public components when --assets is absent')
    args=parser.parse_args()
    print(json.dumps(build(args.source,args.output,args.version,assets=args.assets,fetch_components=args.fetch_components),sort_keys=True))


if __name__=='__main__':main()
