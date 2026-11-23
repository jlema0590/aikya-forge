import {lstatSync} from 'node:fs';
import {join} from 'node:path';
import {canonicalPath} from './project.ts';

/** Inspect metadata only; never import personal credentials or linked auth bytes. */
export function assertCredentialLocation(root:string) {
  let path=canonicalPath(root);
  for(const part of ['.aikya','pi','agent','auth.json']) {
    path=join(path,part);
    try {
      const stat=lstatSync(path);
      if(stat.isSymbolicLink()||(part==='auth.json'?(!stat.isFile()||stat.nlink!==1||stat.size>1048576):!stat.isDirectory()))
        throw new Error('Unsafe project credential location');
    }catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
  }
}
