import assert from 'node:assert/strict';
import {test} from 'node:test';
import {stripTerminalSequences,visibleWidth} from '@earendil-works/pi-tui';
import {renderBrandHeader} from '../src/brand-header.ts';
const figlet=await import('../src/figlet.ts').catch(()=>null);

test('the real isolated Python renders Figlet once and the header selects a fitting font',async()=>{
  assert.ok(figlet,'Python FIGlet bridge is absent');
  const banner=await figlet.loadFigletBanner(process.env.AIKYA_TEST_PYTHON);
  assert.equal(banner.generator,'pyfiglet');
  const wide=renderBrandHeader(79,'0.2.0','Local preview',banner);
  assert.ok(wide.every(row=>visibleWidth(row)<=79));
  assert.ok(banner.variants[0].lines.every(row=>wide.map(stripTerminalSequences).includes(row)));
  const small=renderBrandHeader(10,'0.2.0','Local preview',banner);
  assert.ok(small.every(row=>visibleWidth(row)<=10));assert.ok(small.length<=3);
  assert.deepEqual(await figlet.loadFigletBanner(process.env.AIKYA_TEST_PYTHON),banner);
});

test('an unavailable interpreter preserves a bounded plain startup without leaking errors',async()=>{
  assert.ok(figlet);
  const value=await figlet.loadFigletBanner('/missing/private/interpreter');
  assert.equal(value.generator,'plain');
  assert.ok(renderBrandHeader(79,'0.2.0','Local preview',value).every(row=>!row.includes('/missing/')));
});
