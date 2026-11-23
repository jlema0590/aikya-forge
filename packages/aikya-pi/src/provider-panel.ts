import type {BudgetStatus,QuotaCache} from './usage.ts';

export type ProviderPanelSnapshot={budget:BudgetStatus;contextProvider?:string;
  context?:{tokens:number|null;contextWindow:number;percent:number|null};quotas:ReturnType<QuotaCache['view']>[]};
const percent=(value:number)=>Number(value.toFixed(1))+'%';

export function attributionComplete(budget:BudgetStatus) {
  return budget.recorded_tokens!==null&&budget.status!=='unknown_usage'&&budget.grouped_calls===budget.calls
    &&(budget.groups??[]).every(group=>group.usage_complete);
}

function tokens(provider:string,budget:BudgetStatus) {
  const groups=(budget.groups??[]).filter(group=>group.provider===provider),complete=attributionComplete(budget);
  if(!groups.length&&!complete)return 'unknown';
  const value=groups.reduce((sum,group)=>sum+group.recorded_tokens,0);
  return String(value)+(!complete?' + unknown':budget.recorded_tokens!>0?' · '+percent(value/budget.recorded_tokens!*100)+' project':'');
}

/** Context is session-specific; token totals are project-specific; quotas are sourced. */
export function renderProviderPanel(provider:'anthropic'|'openai-codex',snapshot:ProviderPanelSnapshot,now=Date.now()):string[] {
  const context=snapshot.context;
  const known=snapshot.contextProvider===provider&&context&&context.tokens!==null&&Number.isFinite(context.tokens)&&context.tokens>=0
    &&Number.isFinite(context.contextWindow)&&context.contextWindow>0&&context.percent!==null&&Number.isFinite(context.percent)&&context.percent>=0;
  const rows=[provider==='anthropic'?'Claude':'Codex',
    'Context: '+(known?percent(context!.percent!)+' (estimated)':'unavailable'),
    'Tokens: '+tokens(provider,snapshot.budget)];
  const view=snapshot.quotas.find(quota=>quota.snapshot?.provider===provider),quota=view?.snapshot;
  const stale=Boolean(quota&&(view?.stale||now<quota.fetchedAt||now-quota.fetchedAt>60000));
  for(const [label,seconds] of [['5h',18000],['7d',604800]] as const) {
    const windows=quota?.windows.filter(window=>window.seconds===seconds&&Number.isFinite(window.usedPercent)&&window.usedPercent>=0&&window.usedPercent<=100)??[];
    const window=windows.length===1?windows[0]:undefined;
    const expired=window?.resetAt!==null&&window?.resetAt!==undefined&&window.resetAt<=now;
    rows.push('Usage '+label+': '+(window?percent(window.usedPercent)+' used'+(stale||expired?' · stale':''):'unavailable'));
  }
  if(quota)rows.push('Source: headers · '+Math.max(0,Math.floor((now-quota.fetchedAt)/1000))+'s old'+(stale?' · stale':''));
  return rows;
}
