import assert from 'node:assert/strict';
import {test} from 'node:test';
import {mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const identity=await import('../src/identity.ts').catch(()=>null);

test('the terminal reports the actual packaged private version instead of a source constant',()=>{
  assert.ok(identity,'Runtime package identity reader is absent');
  const root=mkdtempSync(join(tmpdir(),'aikya-runtime-version-')),path=join(root,'package.json');
  try {
    const raw='{"name":"@aikya/pi-runtime","version":"8.0.0-beta.1"}\n';writeFileSync(path,raw);
    assert.equal(identity.runtimeVersion(path),'8.0.0-beta.1');assert.equal(readFileSync(path,'utf8'),raw);
    for(const raw of ['{"name":"foreign","version":"8.0.0-beta.1"}','{"name":"@aikya/pi-runtime","version":"8.00.0-alpha.0"}','x'.repeat(65537)]) {
      writeFileSync(path,raw);assert.throws(()=>identity.runtimeVersion(path));assert.equal(readFileSync(path,'utf8'),raw);
    }
  } finally {rmSync(root,{recursive:true,force:true});}
});

 test('Forge zero-major runtime identity is readable by the actual terminal',()=>{
  assert.ok(identity);
  const root=mkdtempSync(join(tmpdir(),'aikya-forge-version-')),path=join(root,'package.json');
  try {
    writeFileSync(path,'{"name":"@aikya/pi-runtime","version":"0.1.0"}');
    assert.equal(identity.runtimeVersion(path),'0.1.0');
  } finally {rmSync(root,{recursive:true,force:true});}
});
