/** Actual installed Pi SDK and local observer; no external provider transport. */
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {writeFileSync,readFileSync,renameSync,unlinkSync} from 'node:fs';
const [runtimeFolder,root,python,commandsFile]=process.argv.slice(2);
const moduleAt=name=>import(pathToFileURL(join(runtimeFolder,'src',name+'.ts')).href);
const {createReadOnlySession}=await moduleAt('runtime');
const {ThemePreferences}=await moduleAt('theme');
const {hostOperation}=await moduleAt('host');
const {RuntimeBudget}=await moduleAt('usage');
const runtime=await createReadOnlySession(root,{python});
let providerCalls=0;
runtime.session.agent.streamFunction=()=>{providerCalls++;throw new Error('No inference is authorized in native acceptance');};
const observations=[];
try {
  const names=runtime.session.extensionRunner.getRegisteredCommands().map(c=>c.name);
  for(const name of JSON.parse(readFileSync(commandsFile,'utf8')))assert.equal(names.filter(n=>n===name).length,1,name);
  for(const command of ['aikya-status','aikya-memory','aikya-tokens'])await runtime.session.prompt('/'+command);
  const html=join(root,'aikya/docs/memory/view/index.html');
  const waitFor=async(predicate,label)=>{
    const deadline=Date.now()+20000;
    while(Date.now()<deadline) {if(predicate()) {observations.push(label);return;}await new Promise(r=>setTimeout(r,200));}
    throw new Error('Observer did not publish '+label);
  };
  const file=join(root,'src','external.py'),renamed=join(root,'src','renamed.py');
  writeFileSync(file,'class ExternalAddedEvidence: pass\n');await waitFor(()=>readFileSync(html,'utf8').includes('ExternalAddedEvidence'),'external-create');
  writeFileSync(file,'class ExternalChangedEvidence: pass\n');await waitFor(()=>readFileSync(html,'utf8').includes('ExternalChangedEvidence'),'external-edit');
  renameSync(file,renamed);writeFileSync(renamed,'class ExternalRenamedEvidence: pass\n');await waitFor(()=>readFileSync(html,'utf8').includes('ExternalRenamedEvidence'),'external-rename');
  unlinkSync(renamed);await waitFor(()=>!readFileSync(html,'utf8').includes('ExternalRenamedEvidence'),'external-delete');
  const preference=new ThemePreferences(root);preference.save('light',['dark','light']);assert.equal(preference.load(['dark','light']).name,'light');
  const notes=await hostOperation(root,'memory.event',{session:'native-acceptance-query',event:'activity'},python);
  assert.ok(['observing','disabled'].includes(String(notes.status)));
  await hostOperation(root,'memory.event',{session:'native-acceptance-query',event:'end'},python);
  const accounting=await new RuntimeBudget(root,python).status();
  assert.notEqual(accounting.status,'available','The fixture must not silently configure a model budget');
  assert.equal(providerCalls,0);
} finally {await runtime.close();}
console.log(JSON.stringify({provider_calls:providerCalls,observations,theme:'light',runtime:'actual-installed-Pi',ui:'headless SDK; not visual terminal acceptance'}));
