import {openSync,closeSync,fstatSync,readFileSync,lstatSync,existsSync,constants,writeFileSync,renameSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {canonicalPath,projectDirectory} from './project.ts';
import type {ConsoleTheme} from './brand.ts';

export type ConsoleSettings={theme:ConsoleTheme;textStyle:'normal'|'bold'|'italic';sidebar:boolean;
  colors:Partial<Record<'accent'|'text'|'muted'|'background',string>>;provider?:{id:string;model:string}};
const defaults=():ConsoleSettings=>({theme:'aikya',textStyle:'normal',sidebar:true,colors:{}});
const object=(v:unknown):v is Record<string,unknown>=>Boolean(v)&&typeof v==='object'&&!Array.isArray(v);
export function validateSettings(input:unknown):ConsoleSettings {
  if(!object(input)||Object.keys(input).some(k=>!['theme','textStyle','sidebar','colors','provider'].includes(k))
    ||!['inherit','aikya','dark','light'].includes(String(input.theme))||!['normal','bold','italic'].includes(String(input.textStyle))
    ||typeof input.sidebar!=='boolean'||!object(input.colors))throw new Error('Invalid console settings');
  for(const [key,value] of Object.entries(input.colors))if(!['accent','text','muted','background'].includes(key)
    ||typeof value!=='string'||!/^#[a-fA-F0-9]{6}$/.test(value))throw new Error('Use a six-digit HEX color');
  if(input.provider!==undefined&&(!object(input.provider)||Object.keys(input.provider).sort().join(',')!=='id,model'
    ||typeof input.provider.id!=='string'||!/^[A-Za-z0-9_-]{1,80}$/.test(input.provider.id)
    ||typeof input.provider.model!=='string'||!/^[^\x00-\x20\x7f-\x9f]{1,160}$/u.test(input.provider.model)))throw new Error('Invalid provider selection');
  return structuredClone(input) as ConsoleSettings;
}

/** Non-secret, project-owned preferences. Credentials belong to ModelRuntime. */
export class ConsolePreferences {
  #root:string;
  constructor(root:string){this.#root=canonicalPath(root);}
  #path() {
    let path=this.#root;
    for(const part of ['.aikya','pi','console.json']) {
      path=join(path,part);
      try {if(lstatSync(path).isSymbolicLink())throw new Error('Linked console settings');}
      catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
    }
    return path;
  }
  #read() {
    const fd=openSync(this.#path(),constants.O_RDONLY|(constants.O_NOFOLLOW??0));
    try {
      const stat=fstatSync(fd);if(!stat.isFile()||stat.size>16384)throw new Error('Invalid settings file');
      const raw=readFileSync(fd);if(raw.length>16384)throw new Error('Oversized settings');
      return new TextDecoder('utf-8',{fatal:true}).decode(raw);
    }finally {closeSync(fd);}
  }
  load():{value:ConsoleSettings;diagnostic?:string} {
    try {
      const doc=JSON.parse(this.#read());
      if(!object(doc)||Object.keys(doc).sort().join(',')!=='generated_by,project,schema,settings'
        ||doc.schema!==1||doc.generated_by!=='aikya-console'||doc.project!==this.#root)throw new Error('Foreign settings');
      return {value:validateSettings(doc.settings)};
    }catch(error){
      const missing=(error as NodeJS.ErrnoException).code==='ENOENT',value=defaults();
      if(missing&&existsSync(join(this.#root,'.aikya/pi/theme.json')))value.theme='inherit';
      return {value,...(missing?{}:{diagnostic:'Console settings unavailable; custom bytes preserved'})};
    }
  }
  save(input:unknown) {
    const settings=validateSettings(input);
    if(this.load().diagnostic)throw new Error('Custom console settings are preserved');
    const folder=projectDirectory(this.#root,['.aikya','pi']),path=this.#path(),temp=join(folder,'.aikya-durable-console-'+randomUUID());
    let before:string|undefined;try {before=this.#read();}catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
    try {
      writeFileSync(temp,JSON.stringify({schema:1,generated_by:'aikya-console',project:this.#root,settings})+'\n',{flag:'wx',mode:0o600});
      let current:string|undefined;try {current=this.#read();}catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
      if(current!==before)throw new Error('Console settings changed during save');
      renameSync(temp,this.#path());
    }finally {rmSync(temp,{force:true});}
  }
}
