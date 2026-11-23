import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
const permissions = await import("../src/permissions.ts").catch(() => null);

test("host confirmation controls real isolated-service writes without leaking a grant", async () => {
  assert.ok(permissions, "Pi write authority is absent");
  const root = mkdtempSync(join(tmpdir(), "aikya-permissions-"));
  try {
    writeFileSync(join(root, "source.py"), "VALUE = 1\n");
    const authority = new permissions.WriteAuthority(root, "author", process.env.AIKYA_TEST_PYTHON);
    const intent = {path: "source.py", content: "VALUE = 2\n"};
    const denied = await authority.write(intent, async () => false);
    assert.equal(denied.status, "declined");
    assert.equal(readFileSync(join(root, "source.py"), "utf8"), "VALUE = 1\n");
    assert.equal(existsSync(join(root, ".aikya")), false);
    const accepted = await authority.write(intent, async (preview) => {
      assert.equal(preview.content, "VALUE = 2\n"); assert.equal(preview.path, "source.py"); return true;
    });
    assert.equal(accepted.status, "written");
    assert.equal(readFileSync(join(root, "source.py"), "utf8"), "VALUE = 2\n");
    assert.equal("grant" in accepted, false);
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test("source edited during the approval dialog is preserved", async () => {
  assert.ok(permissions);
  const root = mkdtempSync(join(tmpdir(), "aikya-confirm-drift-"));
  try {
    writeFileSync(join(root, "source.py"), "VALUE = 1\n");
    const authority = new permissions.WriteAuthority(root, "author", process.env.AIKYA_TEST_PYTHON);
    await assert.rejects(authority.write({path: "source.py", content: "VALUE = 2\n"}, async () => {
      writeFileSync(join(root, "source.py"), "USER_EDIT = 3\n"); return true;
    }));
    assert.equal(readFileSync(join(root, "source.py"), "utf8"), "USER_EDIT = 3\n");
  } finally { rmSync(root, {recursive: true, force: true}); }
});

test('cancellation during confirmation prevents the write even when the dialog returns approval',async()=>{
  assert.ok(permissions);
  const root=mkdtempSync(join(tmpdir(),'aikya-abort-confirmed-write-'));
  try {
    writeFileSync(join(root,'source.py'),'VALUE = 1\n');
    const authority=new permissions.WriteAuthority(root,'author',process.env.AIKYA_TEST_PYTHON),abort=new AbortController();
    const result=await authority.write({path:'source.py',content:'VALUE = 2\n'},async()=>{abort.abort();return true;},abort.signal);
    assert.equal(result.status,'declined');assert.equal(readFileSync(join(root,'source.py'),'utf8'),'VALUE = 1\n');
    assert.equal(existsSync(join(root,'.aikya/pi/authorizations')),false);
  } finally {rmSync(root,{recursive:true,force:true});}
});
