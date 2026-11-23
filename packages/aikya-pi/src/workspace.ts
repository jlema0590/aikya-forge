import {execFile} from 'node:child_process';
import {basename,resolve,dirname,delimiter,isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {replaceControlCharacters} from '@earendil-works/pi-tui';

export type WorkspaceIdentity={project:string;user:string|null;branch:string|null};
export const workspaceLabel=(value:string)=>replaceControlCharacters(value).replace(/[\r\n\t]/g,' ').trim().slice(0,180);

/** Local user.name only; never shell, remote, email, model input or repaint I/O. */
export function readGitUser(root:string):Promise<string|null> {
  const names=['PATH','HOME','USERPROFILE','XDG_CONFIG_HOME','SYSTEMROOT','WINDIR','TEMP','TMP','TMPDIR','LANG','LC_ALL'];
  const env=Object.fromEntries(Object.entries(process.env).filter(([key])=>names.includes(key.toUpperCase())));
  const pathKey=Object.keys(env).find(key=>key.toUpperCase()==='PATH')??'PATH';
  env[pathKey]=(env[pathKey]??'').split(delimiter).filter(isAbsolute).join(delimiter);
  if(!env[pathKey])return Promise.resolve(null);
  env.NoDefaultCurrentDirectoryInExePath='1';
  return new Promise(resolveUser=>{
    execFile('git',['--no-optional-locks','-C',resolve(root),'config','--get','user.name'],
      {cwd:dirname(fileURLToPath(import.meta.url)),env,timeout:1500,maxBuffer:4096,windowsHide:true},(error,stdout)=>{
        resolveUser(error?null:workspaceLabel(stdout)||null);
      });
  });
}

/** Branch reads come from Pi's existing observed cache, including detached HEAD. */
export function projectIdentity(root:string,user:string|null,branch:()=>string|null):WorkspaceIdentity {
  return {project:basename(resolve(root))||resolve(root),user,get branch(){return branch();}};
}
