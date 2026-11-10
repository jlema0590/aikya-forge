import { createHmac, randomBytes, randomUUID } from "node:crypto";
import { realpathSync } from "node:fs";
import { callBridge } from "./bridge.ts";

export type WriteIntent = {path: string; content: string};
type Preview = WriteIntent & {before: string | null; after: string; intent_hash: string; bytes: number; workflow_revision: string | null};
export type BatchIntent={change_id:string;operations:({path:string;content:string}|{path:string;edits:{old:string;new:string}[]}|{path:string;delete:true})[]};
type BatchPreview={candidate:string;files:Record<string,unknown>[];intent_hash:string;source_revision:string;workflow_revision:string|null};
export class WriteAuthority {
  #key = randomBytes(32);
  #project: string;
  #session: string;
  #python?: string;
  constructor(root: string, session: string, python?: string) {
    this.#project = realpathSync(root); this.#session = session; this.#python = python;
  }

  #grant(checked:{intent_hash:string;workflow_revision:string|null},source:string|null,operation:'file.write'|'file.batch') {
    const now=Math.floor(Date.now()/1000);
    const raw=Buffer.from(JSON.stringify({schema:1,project:this.#project,session:this.#session,operation,
      intent_hash:checked.intent_hash,source_revision:source,workflow_revision:checked.workflow_revision,
      issued_at:now,expires_at:now+120,nonce:randomUUID().replaceAll('-','')})).toString('base64url');
    return raw+'.'+createHmac('sha256',this.#key).update(raw).digest('hex');
  }

  async batch(intent:BatchIntent,confirm:(preview:BatchPreview)=>Promise<boolean>,signal?:AbortSignal):Promise<Record<string,unknown>> {
    if(signal?.aborted)return {status:'declined'};
    const approved=structuredClone(intent);
    const checked=await callBridge(this.#project,'batch-preview',{python:this.#python,signal,arguments:{intent:approved,session:this.#session}}) as BatchPreview;
    if(signal?.aborted||await confirm(structuredClone(checked))!==true||signal?.aborted)return {status:'declined'};
    const grant=this.#grant(checked,checked.source_revision,'file.batch');
    return await callBridge(this.#project,'batch',{python:this.#python,signal,hostKey:this.#key.toString('hex'),
      arguments:{session:this.#session,intent:approved,grant}}) as Record<string,unknown>;
  }

  async write(intent: WriteIntent, confirm: (preview: Preview) => Promise<boolean>,signal?:AbortSignal): Promise<Record<string, unknown>> {
    if(signal?.aborted)return {status:'declined'};
    const checked = await callBridge(this.#project, "write-preview", {python: this.#python, signal, arguments: {intent,session: this.#session}}) as Preview;
    // Bind copies before displaying approval; the dialog cannot change the authorized bytes.
    const approvedIntent = {path: intent.path, content: intent.content};
    if (signal?.aborted || await confirm({...checked, ...approvedIntent}) !== true || signal?.aborted) return {status: "declined", path: intent.path};
    const grant=this.#grant(checked,checked.before,'file.write');
    return await callBridge(this.#project, "write", {python: this.#python, signal, hostKey: this.#key.toString("hex"),
      arguments: {session: this.#session, intent: approvedIntent, grant}}) as Record<string, unknown>;
  }
}
