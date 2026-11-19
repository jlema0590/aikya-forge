import {lstatSync} from 'node:fs';
import {join} from 'node:path';
import {canonicalPath} from './project.ts';

/** libuv otherwise checks cwd before PATH on Windows, including redirected CI. */
export function prepareToolSearch(root:string) {
 refuseProjectToolCache(root);
 process.env.NoDefaultCurrentDirectoryInExePath='1';
}

/** Pi prefers this cache over PATH; repository files never authorize executables. */
export function refuseProjectToolCache(root:string) {
 let current=canonicalPath(root);
 for(const part of ['.aikya','pi','agent','bin']) {
  current=join(current,part);
  try {
   const stat=lstatSync(current);
   if(stat.isSymbolicLink()||!stat.isDirectory())throw new Error('Unsafe project tool-cache ancestor');
   if(part==='bin')throw new Error('Project-local tool cache is not used by Forge; review it before starting');
  }catch(error) {
   if((error as NodeJS.ErrnoException).code==='ENOENT')return;
   throw error;
  }
 }
}
