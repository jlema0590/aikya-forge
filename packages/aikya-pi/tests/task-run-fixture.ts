import {ModelRuntime,type ExtensionUIContext} from '@earendil-works/pi-coding-agent';
import {createAssistantMessageEventStream,type AssistantMessage,type Context} from '@earendil-works/pi-ai';
import {join} from 'node:path';

/** Only the terminal and external provider transport are simulated; services and Pi execute. */
export function approvingUI(decision=(title:string)=>true):ExtensionUIContext {
  const theme={name:'dark',fg:(_color:string,text:string)=>text,bg:(_color:string,text:string)=>text,bold:(text:string)=>text};
  const noop=()=>{};
  return {theme:theme as never,select:async()=>undefined,confirm:async title=>decision(title),input:async()=>undefined,
    notify:noop,onTerminalInput:()=>noop,setStatus:noop,setWorkingMessage:noop,setWorkingVisible:noop,setWorkingIndicator:noop,
    setHiddenThinkingLabel:noop,setWidget:noop,setFooter:noop,setHeader:noop,setTitle:noop,
    custom:async<T>(factory:Parameters<ExtensionUIContext['custom']>[0])=>new Promise<T>((resolve,reject)=>{
      const tui={terminal:{rows:50},requestRender:noop};
      void Promise.resolve(factory(tui as never,theme as never,{} as never,value=>resolve(value as T))).then(component=>{
        const rows=component.render(120),title=rows[0]??'';
        if(rows.some(row=>row.includes('Enter: approve')||row.includes('End: bottom'))) {
          if(!decision(title))component.handleInput?.('\x1b');
          else {component.handleInput?.('\x1b[F');component.render(120);component.handleInput?.('\r');}
        }
      }).catch(reject);
    }),pasteToEditor:noop,setEditorText:noop,getEditorText:()=>'',editor:async()=>undefined,
    addAutocompleteProvider:noop,setEditorComponent:noop,getEditorComponent:()=>undefined,getAllThemes:()=>[{name:'dark',path:undefined},{name:'light',path:undefined}],
    getTheme:()=>theme as never,setTheme:()=>({success:true}),getToolsExpanded:()=>false,setToolsExpanded:noop};
}
export async function fixtureModels(root:string,answer:(request:number,context:Context)=>AssistantMessage['content'],onRequest=()=>{}) {
  const models=await ModelRuntime.create({authPath:join(root,'.aikya/pi/fixture-auth.json'),modelsPath:null,
    modelsStorePath:join(root,'.aikya/pi/fixture-models.json'),allowModelNetwork:false,refreshOnCreate:false});
  let calls=0;
  models.registerProvider('fixture',{api:'fixture',apiKey:'fixture-no-network',baseUrl:'http://invalid.local',
    models:[{id:'fixture',name:'Fixture',reasoning:false,input:['text'],cost:{input:0,output:0,cacheRead:0,cacheWrite:0},contextWindow:10000,maxTokens:500}],
    streamSimple:(_model,context)=>{
      onRequest();const content=answer(++calls,context),tool=content.some(item=>item.type==='toolCall'),stream=createAssistantMessageEventStream();
      const message:AssistantMessage={role:'assistant',content,api:'fixture',provider:'fixture',model:'fixture',
        usage:{input:7,output:3,cacheRead:0,cacheWrite:0,totalTokens:10,cost:{input:0,output:0,cacheRead:0,cacheWrite:0,total:0}},
        stopReason:tool?'toolUse':'stop',timestamp:Date.now()};
      stream.push({type:'done',reason:tool?'toolUse':'stop',message});return stream;
    }});
  return models;
}
