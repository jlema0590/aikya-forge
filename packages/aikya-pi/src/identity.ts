import {lstatSync,readFileSync} from 'node:fs';

/** Read bounded first-party package identity, never client or project settings. */
export function runtimeVersion(path:string|URL=new URL('../package.json',import.meta.url)):string {
  const stat=lstatSync(path);
  if(!stat.isFile()||stat.isSymbolicLink()||stat.size>65536)throw new Error('Invalid Aikya runtime package');
  const data:unknown=JSON.parse(readFileSync(path,'utf8'));
  if(!data||typeof data!=='object'||Array.isArray(data))throw new Error('Invalid Aikya runtime package');
  const {name,version}=data as Record<string,unknown>;
  if(name!=='@aikya/pi-runtime'||typeof version!=='string'||!/^(0|8)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-(alpha|beta|rc)\.(0|[1-9][0-9]*))?$/.test(version))
    throw new Error('Unsupported Aikya runtime identity');
  return version;
}
