import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, rmSync, readFileSync, existsSync, symlinkSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { test } from "node:test";
const themes = await import("../src/theme.ts").catch(() => null);

test("installed palette preview validates references without writing or activating themes", () => {
  assert.ok(themes, "Theme configuration is absent");
  const root=mkdtempSync(join(tmpdir(), "aikya-theme-"));
  try {
    const source=join(root,"dark.json");
    writeFileSync(source,JSON.stringify({name:"dark",colors:{accent:"violet",text:"#ffffff"},vars:{violet:"okhsl(295 50% 67%)"}}));
    const preview=themes.previewTheme("dark",source);
    assert.match(preview.sample,/sample/);
    assert.equal(existsSync(join(root,".aikya")),false);
    writeFileSync(source,JSON.stringify({name:"dark",colors:{accent:"a",text:"#ffffff"},vars:{a:"b",b:"a"}}));
    assert.throws(()=>themes.previewTheme("dark",source));
    writeFileSync(source,Buffer.from([255])); assert.throws(()=>themes.previewTheme("dark",source));
  } finally {rmSync(root,{recursive:true,force:true});}
});

test("theme preference survives restart and preserves corrupt custom state", () => {
  assert.ok(themes);
  const root=mkdtempSync(join(tmpdir(),"aikya-theme-state-"));
  try {
    const prefs=new themes.ThemePreferences(root);
    assert.equal(prefs.load(["dark","light"]).name,"dark");
    assert.equal(existsSync(join(root,".aikya")),false);
    prefs.save("light",["dark","light"]);
    assert.equal(new themes.ThemePreferences(root).load(["dark","light"]).name,"light");
    const state=join(root,".aikya/pi/theme.json"); writeFileSync(state,"CUSTOM");
    assert.equal(prefs.load(["dark","light"]).name,"dark");
    assert.throws(()=>prefs.save("light",["dark","light"]));
    assert.equal(readFileSync(state,"utf8"),"CUSTOM");
  } finally {rmSync(root,{recursive:true,force:true});}
});

test("theme state symlink cannot redirect preference writes", () => {
  assert.ok(themes);
  const root=mkdtempSync(join(tmpdir(),"aikya-theme-link-"));
  try {
    const prefs=new themes.ThemePreferences(root); prefs.save("dark",["dark","light"]);
    const state=join(root,".aikya/pi/theme.json"), outside=join(root,"outside");
    rmSync(state); writeFileSync(outside,"USER"); symlinkSync(outside,state);
    assert.throws(()=>prefs.save("light",["dark","light"]));
    assert.equal(readFileSync(outside,"utf8"),"USER");
  } finally {rmSync(root,{recursive:true,force:true});}
});
