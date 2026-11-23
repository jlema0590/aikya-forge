import {Container,replaceControlCharacters,type TUI} from '@earendil-works/pi-tui';
import type {ExtensionAPI,ExtensionCommandContext,ExtensionContext,ModelRuntime} from '@earendil-works/pi-coding-agent';
import {ConsolePreferences,type ConsoleSettings} from './console-preferences.ts';
import {applyAppearance} from './console-appearance.ts';
import {renderSidebar,renderCompactSidebar} from './console-sidebar.ts';
import {ForgeWorkbench} from './console-layout.ts';
import {configureProvider} from './provider-settings.ts';
import type {registerLocalCommands} from './local-commands.ts';
import type {TaskHandler} from './task-run.ts';
import {hostOperation} from './host.ts';

export function registerConsole(pi:ExtensionAPI,root:string,python:string|undefined,local:ReturnType<typeof registerLocalCommands>,
  phase:()=>string,runtime:ModelRuntime|undefined,task:TaskHandler|undefined,controlled=false) {
  const store=new ConsolePreferences(root);let settings=store.load().value;
  let context:ExtensionContext|undefined,tui:TUI|undefined,workbench:ForgeWorkbench|undefined,timer:ReturnType<typeof setInterval>|undefined;
  let running=false;
  const request=()=>tui?.requestRender();
  const snapshot=()=>({...local.viewUsage(),workspace:local.viewWorkspace(),phase:phase(),state:running?'running':'idle',
    model:controlled&&context?.model?context.model.provider+'/'+context.model.id:null,context:controlled?context?.getContextUsage():undefined});
  const repaint=()=>{const value=store.load();if(!value.diagnostic)settings=value.value;request();};
  local.onUsageChanged(request);
  pi.on('session_start',(_e,ctx)=>{
    context=ctx;settings=store.load().value;
    if(ctx.mode!=='tui')return;
    if(store.load().diagnostic)ctx.ui.notify(store.load().diagnostic!,'warning');
    applyAppearance(ctx.ui,settings);
    clearInterval(timer);timer=setInterval(request,1000).unref();
  });
  pi.on('agent_start',(_e,ctx)=>{running=true;context=ctx;request();});
  pi.on('agent_end',(_e,ctx)=>{running=false;context=ctx;request();});
  pi.on('session_shutdown',()=>{
    clearInterval(timer);timer=undefined;
    if(tui&&workbench) {
      const index=tui.children.indexOf(workbench);
      if(index>=0)tui.children.splice(index,1,...workbench.originalChildren());
    }
    workbench=undefined;tui=undefined;
  });
  const open=async(ctx:ExtensionContext,initialPage?:string)=>{
      if(ctx.mode!=='tui') {pi.sendMessage({customType:'aikya-settings',display:true,content:JSON.stringify({status:'interactive_terminal_required'})});return;}
      settings=store.load().value;
      const save=(next:ConsoleSettings)=>{
        const previous=ctx.ui.theme;
        try {applyAppearance(ctx.ui,next);store.save(next);settings=next;request();}
        catch(error){ctx.ui.setTheme(previous);throw error;}
      };
      for(;;) {
        const page=initialPage??await ctx.ui.select('Forge settings',['Providers','Appearance','Sidebar','Flow','Close']);
        initialPage=undefined;
        if(!page||page==='Close')break;
        if(page==='Providers') {
          if(!runtime)ctx.ui.notify('Local provider catalog unavailable','warning');
          else await configureProvider(ctx,runtime,settings,save);
        }else if(page==='Appearance') {
          const item=await ctx.ui.select('Appearance',['Theme','Accent color','Text color','Muted color','Background color','Text style','Font family and size','Reset colors']);
          if(item==='Theme') {
            const theme=await ctx.ui.select('Theme',['aikya','dark','light']);
            if(theme==='aikya'||theme==='dark'||theme==='light')save({...settings,theme});
          }else if(item==='Text style') {
            const style=await ctx.ui.select('Text style',['normal','bold','italic']);
            if(style==='normal'||style==='bold'||style==='italic')save({...settings,textStyle:style});
          }else if(item==='Font family and size')ctx.ui.notify('Font family and size are controlled by your terminal application. Forge preserves those settings.','info');
          else if(item==='Reset colors')save({...settings,colors:{}});
          else {
            const color=({'Accent color':'accent','Text color':'text','Muted color':'muted','Background color':'background'} as const)[item as 'Accent color'];
            if(color) {
              const value=await ctx.ui.input(item!,'#RRGGBB');if(value===undefined)continue;
              if(!/^#[a-fA-F0-9]{6}$/.test(value)){ctx.ui.notify('Use a six-digit HEX color, for example #4D9DE0','warning');continue;}
              save({...settings,colors:{...settings.colors,[color]:value}});
            }
          }
        }else if(page==='Sidebar') {
          const value=await ctx.ui.select('Right sidebar',['Show','Hide']);if(value)save({...settings,sidebar:value==='Show'});
        }else if(page==='Flow') {
          const value=await ctx.ui.select('Flow controls',['Inspect current flow','Stop current flow','Cancel current response','Refresh usage']);
          if(value==='Refresh usage'){await local.refreshUsage();request();}
          else if(value==='Cancel current response') {ctx.abort();running=false;request();}
          else if(value==='Stop current flow'&&task)await task({action:'stop-run'},ctx);
          else if(value==='Inspect current flow') {
            const state=await hostOperation(root,'task.status',{session_id:ctx.sessionManager.getSessionId()},python);
            const summary=replaceControlCharacters(JSON.stringify({status:state.status,phase:state.phase,run_id:state.run_id,state:state.state}));
            await ctx.ui.confirm('Current flow',summary);
          }
        }
      }
      repaint();
  };
  let opened=false;
  const show=async(ctx:ExtensionContext,initial?:string)=>{
    if(opened)return;opened=true;
    try {await open(ctx,initial);}finally {opened=false;}
  };
  pi.registerCommand('aikya-settings',{description:'Configure providers, palette, text style, sidebar and native flow controls locally',
    handler:async(args,ctx)=>{
      if(args.trim())throw new Error('Open /aikya-settings without arguments; credentials never belong in commands');
      await show(ctx);
    }});
  pi.registerShortcut('f2',{description:'Open Forge settings',handler:ctx=>show(ctx)});
  return {mount:(target:TUI)=>{
    tui=target;if(workbench&&target.children.includes(workbench))return;
    const body=new Container();body.children=[...target.children];
    workbench=new ForgeWorkbench(body,width=>renderSidebar(snapshot(),width).map(line=>context?.ui.theme.fg('muted',line)??line),()=>settings.sidebar,
      ()=>({...settings,theme:context?.ui.theme.name==='aikya'?'aikya':context?.ui.theme.appearance??settings.theme}),action=>{
        if(!context)return;const ctx=context;
        void (action==='stop'&&task?task({action:'stop-run'},ctx):show(ctx,action==='flow'?'Flow':undefined))
          .catch(()=>ctx.ui.notify('Control did not confirm completion; inspect flow status','warning'));
      },width=>renderCompactSidebar(snapshot(),width).map(line=>context?.ui.theme.fg('muted',line)??line));
    target.children.splice(0,target.children.length,workbench);
  }};
}
