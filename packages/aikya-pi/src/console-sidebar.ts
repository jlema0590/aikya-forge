import {truncateToWidth,replaceControlCharacters} from '@earendil-works/pi-tui';
import {workspaceLabel,type WorkspaceIdentity} from './workspace.ts';
import {renderProviderPanel,attributionComplete,type ProviderPanelSnapshot} from './provider-panel.ts';
export type SidebarSnapshot=ProviderPanelSnapshot&{phase:string;state:string;model:string|null;workspace?:WorkspaceIdentity};
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
  const {budget}=snapshot,groups=budget.groups??[],complete=attributionComplete(budget);
  const total=budget.recorded_tokens;
  const rows=[...intro(snapshot),
    'Aikya local budget',total===null?'Recorded tokens: unknown':'Recorded tokens: '+total+(budget.status==='unknown_usage'?' + unknown':''),
    total!==null&&budget.limits?.tokens?percent(total/budget.limits.tokens*100)+' local budget'+(budget.status==='unknown_usage'?' (known only)':''):'Local budget: unconfigured',
    'Calls: '+budget.calls+(budget.limits?' / '+budget.limits.calls:''),'State: '+safe(budget.status),''];
  for(const provider of ['anthropic','openai-codex'] as const)rows.push(...renderProviderPanel(provider,snapshot,now),'');
  rows.push(complete?'Role token totals':'Role token totals · partial');
  for(const role of ['author','reviewer']) {
    const amount=groups.filter(g=>g.role===role).reduce((n,g)=>n+g.recorded_tokens,0);
    rows.push(role+': '+(total===null?'unknown':amount)+(complete&&total!==null&&total>0?' · '+percent(amount/total*100):''));
  }
  rows.push('','[Settings] [Flow] [Stop]');
  return rows.map(line=>truncateToWidth(line,Math.max(1,width),'…'));
}
