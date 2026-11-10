import {createHash} from 'node:crypto';
import {readFileSync,lstatSync} from 'node:fs';
import {join} from 'node:path';
import {loadSkills,parseSkillBlock,type Skill,type ExtensionAPI} from '@earendil-works/pi-coding-agent';
import type {Context} from '@earendil-works/pi-ai';
import {hostOperation} from './host.ts';
import {registerSkillAdministration} from './skill-administration.ts';
export type SelectedSkill={name:string;description:string;file:string;base:string;source_hash:string;file_hash:string;body_hash:string};
const hash=(value:string|Buffer)=>createHash('sha256').update(value).digest('hex');

export async function approvedSkills(root:string,python?:string):Promise<{metadata:SelectedSkill[];skills:Skill[]}> {
  const value=await hostOperation(root,'skills.resolve',{},python),metadata=value.skills as SelectedSkill[];
  if(!Array.isArray(metadata)||metadata.length>20)throw new Error('Invalid selected-skill catalog');
  for(const entry of metadata) {
    if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.name)||entry.name.startsWith('aikya-')
      ||entry.file!=='.aikya/pi/skills/packages/'+entry.source_hash+'/'+entry.name+'/files/SKILL.md')throw new Error('Foreign selected skill');
    const file=join(root,entry.file),stat=lstatSync(file);
    if(stat.isSymbolicLink()||!stat.isFile()||stat.size>10000||hash(readFileSync(file))!==entry.file_hash)throw new Error('Selected skill integrity changed');
  }
  const loaded=loadSkills({cwd:root,agentDir:join(root,'.aikya/pi/agent'),skillPaths:metadata.map(s=>join(root,s.file)),includeDefaults:false});
  if(loaded.skills.length!==metadata.length||loaded.diagnostics.length)throw new Error('Selected skill compatibility requires review');
  for(const entry of loaded.skills) {
    if(!metadata.some(s=>s.name===entry.name&&join(root,s.file)===entry.filePath))throw new Error('Unknown loaded skill');
    entry.disableModelInvocation=true;
  }
  return {metadata,skills:loaded.skills};
}

export function verifySkillMessages(root:string,skills:SelectedSkill[],messages:Context["messages"]) {
  const active=new Set<string>();
  for(const message of messages) {
    if(message.role!=='user')continue;
    const text=typeof message.content==='string'?message.content:message.content.filter(p=>p.type==='text').map(p=>p.type==='text'?p.text:'').join('\n');
    if(!text.startsWith('<skill '))continue;
    const block=parseSkillBlock(text),entry=block&&skills.find(s=>s.name===block.name&&join(root,s.file)===block.location);
    if(!block||!entry)throw new Error('Unapproved skill expansion refused');
    const prefix='References are relative to '+join(root,entry.base)+'.\n\n';
    if(!block.content.startsWith(prefix)||hash(block.content.slice(prefix.length))!==entry.body_hash)throw new Error('Skill expansion differs from approved instructions');
    active.add(entry.name);
  }
  return active;
}

export async function verifyCurrentSkillMessages(root:string,skills:SelectedSkill[],messages:Context["messages"],python?:string) {
  const active=verifySkillMessages(root,skills,messages);
  if(skills.length) {
    const value=await hostOperation(root,'skills.resolve',{},python),current=value.skills as SelectedSkill[];
    if(!Array.isArray(current)||current.length!==skills.length||skills.some(old=>!current.some(now=>
      now.name===old.name&&now.file===old.file&&now.source_hash===old.source_hash&&now.file_hash===old.file_hash&&now.body_hash===old.body_hash)))
      throw new Error('Selected skill version changed; restart and invoke the reviewed version explicitly');
  }
  return active;
}

export function registerSelectedSkills(pi:ExtensionAPI,root:string,python:string|undefined,skills:SelectedSkill[],reviewer:boolean) {
  pi.on('input',async event=>{
    if(!event.text.startsWith('/skill:'))return;
    try {
      const name=event.text.slice(7).split(/\s/,1)[0],entry=skills.find(s=>s.name===name);
      if(reviewer||!entry)throw new Error('Unapproved skill');
      const current=await hostOperation(root,'skills.verify',{name},python);
      if(current.file!==entry.file||current.file_hash!==entry.file_hash||current.body_hash!==entry.body_hash)throw new Error('Changed skill');
    } catch {
      pi.sendMessage({customType:'aikya-skill-unavailable',content:'Selected skill unavailable or changed; review it before restarting.',display:true});
      return {action:'handled'};
    }
  });
  if(reviewer)return;
  registerSkillAdministration(pi,root,python);
}
