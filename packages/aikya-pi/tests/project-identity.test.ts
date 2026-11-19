import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {mkdtempSync,realpathSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {test} from 'node:test';
import {callBridge} from '../src/bridge.ts';

test('the Python service and SDK share one native project identity',async()=>{
  const root=mkdtempSync(join(tmpdir(),'aikya-identity-'));
  try {
    const python=process.env.AIKYA_TEST_PYTHON??'python3';
    const canonical=execFileSync(python,['-I','-B','-c','from pathlib import Path;import sys;print(Path(sys.argv[1]).resolve(strict=True))',root],{encoding:'utf8'}).trim();
    const observed={defaultMatchesPython:realpathSync(root)===canonical,nativeMatchesPython:realpathSync.native(root)===canonical};
    const result=await callBridge(root,'status',{python}).catch(()=>assert.fail('Synthetic project identity mismatch: '+JSON.stringify(observed)));
    assert.equal((result as {configured:boolean}).configured,false);
  } finally {rmSync(root,{recursive:true,force:true});}
});
