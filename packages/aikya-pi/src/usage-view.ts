import { truncateToWidth } from "@earendil-works/pi-tui";
import type { BudgetStatus, QuotaSnapshot } from "./usage.ts";

function numeric(value: string | undefined) {
  if (value === undefined || !/^(?:\d+\.?\d*|\.\d+)$/.test(value.trim())) return null;
  const number=Number(value); return Number.isFinite(number) ? number : null;
}

/** Observe only named response fields; no account endpoints or credential import. */
export function quotaFromHeaders(provider:string,headers:Record<string,string>,now=Date.now()):QuotaSnapshot|null {
  const values=Object.fromEntries(Object.entries(headers).map(([name,value])=>[name.toLowerCase(),value]));
  const windows:QuotaSnapshot['windows']=[];
  const label=(seconds:number)=>seconds===18000?'5h':seconds===604800?'week':seconds+'s';
  if (provider==='anthropic') {
    for (const [key,seconds] of [['5h',18000],['7d',604800]] as const) {
      const used=numeric(values['anthropic-ratelimit-unified-'+key+'-utilization']);
      const reset=numeric(values['anthropic-ratelimit-unified-'+key+'-reset']);
      if (used!==null&&used>=0&&used<=1) windows.push({label:label(seconds),seconds,usedPercent:used*100,resetAt:reset===null||reset>8640000000000?null:reset*1000});
    }
  } else if (provider==='openai-codex') {
    for (const kind of ['primary','secondary']) {
      const used=numeric(values['x-codex-'+kind+'-used-percent']);
      const minutes=numeric(values['x-codex-'+kind+'-window-minutes']);
      const reset=numeric(values['x-codex-'+kind+'-reset-at']);
      if (used!==null&&used>=0&&used<=100&&minutes!==null&&minutes>0&&minutes<=525600) {
        const seconds=minutes*60;
        windows.push({label:label(seconds),seconds,usedPercent:used,resetAt:reset===null||reset>8640000000000?null:reset*1000});
      }
    }
  }
  return windows.length?{provider,fetchedAt:now,windows}:null;
}

type QuotaView={snapshot:QuotaSnapshot|null;stale:boolean};
export function renderUsage(status:BudgetStatus,quotas:QuotaView[]=[],width=100,now=Date.now()) {
  const unknown=status.status==='unknown_usage';
  const count=status.recorded_tokens===null?'unknown':String(status.recorded_tokens)+(unknown?' + unknown':'');
  const limit=status.limits?String(status.limits.tokens):'unconfigured';
  const lines=[`Local budget: ${count} recorded tokens / ${limit} · calls ${status.calls} · ${status.status}`];
  if (!quotas.length || quotas.every(q=>!q.snapshot)) lines.push('Provider quota: unavailable');
  for (const quota of quotas) {
    if (!quota.snapshot) continue;
    const snapshot=quota.snapshot;
    lines.push(`${snapshot.provider} quota · response headers · ${Math.max(0,Math.floor((now-snapshot.fetchedAt)/1000))}s old${quota.stale?' · stale':''}`);
    for (const window of snapshot.windows) {
      const reset=window.resetAt===null||!Number.isFinite(window.resetAt)||window.resetAt<0||window.resetAt>8640000000000000?'reset unknown':new Date(window.resetAt).toISOString();
      lines.push(`  ${window.label}: ${window.usedPercent}% used · ${reset}`);
    }
  }
  return lines.map(line=>truncateToWidth(line,Math.max(1,width),'…'));
}

export function renderFooter(phase:string,model:string|null,status:BudgetStatus,width=100) {
  const usage=status.recorded_tokens===null?'local budget '+status.status:
    String(status.recorded_tokens)+(status.status==='unknown_usage'?' + unknown':'')+' local tokens'+
    (status.limits?' / '+status.limits.tokens:'')+' · '+status.status;
  return truncateToWidth(phase+' · '+(model??'model disabled')+' · '+usage,Math.max(1,width),'…');
}
