import {truncateToWidth,replaceControlCharacters} from '@earendil-works/pi-tui';
import type {BudgetStatus,QuotaCache} from './usage.ts';
import {workspaceLabel,type WorkspaceIdentity} from './workspace.ts';
export type SidebarSnapshot={phase:string;state:string;model:string|null;budget:BudgetStatus;
  workspace?:WorkspaceIdentity;context?:{tokens:number|null;contextWindow:number;percent:number|null};quotas:ReturnType<QuotaCache['view']>[]};
const safe=(v:string)=>replaceControlCharacters(v).slice(0,180);
const percent=(v:number)=>Number.isFinite(v)?Number(v.toFixed(1))+'%':'unknown';

function intro(snapshot:SidebarSnapshot) {
  const rows=['Flow',safe(snapshot.state)+' · '+safe(snapshot.phase),safe(snapshot.model??'Model disabled'),''];
  const workspace=snapshot.workspace;
  if(workspace)rows.push('Project & Git','Project: '+workspaceLabel(workspace.project),
    'Branch: '+workspaceLabel(workspace.branch??'unavailable'),'User: '+workspaceLabel(workspace.user??'not configured'),'');
  return rows;
}

export function renderCompactSidebar(snapshot:SidebarSnapshot,width:number):string[] {
  return intro(snapshot).filter(Boolean).map(row=>truncateToWidth(row,Math.max(1,width),'…'));
}

/** Account quota, context and local attribution always carry their own denominator. */
export function renderSidebar(snapshot:SidebarSnapshot,width=36,now=Date.now()):string[] {
  const {budget,context}=snapshot,groups=budget.groups??[];
  const complete=budget.status!=='unknown_usage'&&budget.recorded_tokens!==null
    &&budget.grouped_calls===budget.calls&&groups.every(g=>g.usage_complete);
  const total=budget.recorded_tokens;
  const rows=[...intro(snapshot),
    'Project token budget',total===null?'Recorded tokens: unknown':'Recorded tokens: '+total+(budget.status==='unknown_usage'?' + unknown':''),
    total!==null&&budget.limits?.tokens?percent(total/budget.limits.tokens*100)+' local budget'+(budget.status==='unknown_usage'?' (known only)':''):'Local budget: unconfigured',
    'Calls: '+budget.calls+(budget.limits?' / '+budget.limits.calls:''),'State: '+safe(budget.status),
    context?.percent!==null&&context?.percent!==undefined?percent(context.percent)+' context (estimated)':'Context: unavailable',
    '',complete?'Recorded token share':'Recorded token share · partial'];
  for(const [label,providers] of [['Claude',['anthropic']],['Codex',['openai-codex']]] as const) {
    const amount=groups.filter(g=>(providers as readonly string[]).includes(g.provider)).reduce((n,g)=>n+g.recorded_tokens,0);
    rows.push(label+': '+(total===null?'unknown':amount)+(complete&&total!==null&&total>0?' · '+percent(amount/total*100):' · share unavailable'));
  }
  for(const role of ['author','reviewer']) {
    const amount=groups.filter(g=>g.role===role).reduce((n,g)=>n+g.recorded_tokens,0);
    rows.push(role+': '+(total===null?'unknown':amount)+(complete&&total!==null&&total>0?' · '+percent(amount/total*100):''));
  }
  rows.push('');
  for(const [label,provider] of [['Claude','anthropic'],['Codex','openai-codex']]) {
    const view=snapshot.quotas.find(q=>q.snapshot?.provider===provider),q=view?.snapshot;
    if(!q){rows.push(label+' quota: unavailable');continue;}
    rows.push(label+' quota · response headers');
    for(const window of q.windows)rows.push(safe(window.label)+': '+percent(window.usedPercent)+' used');
    rows.push(Math.max(0,Math.floor((now-q.fetchedAt)/1000))+'s old'+(view.stale||now<q.fetchedAt||now-q.fetchedAt>60000?' · stale':''));
  }
  rows.push('','[Settings] [Flow] [Stop]');
  return rows.map(line=>truncateToWidth(line,Math.max(1,width),'…'));
}
