import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const index=fs.readFileSync(path.join(HERE,'index.html'),'utf8');
const store=fs.readFileSync(path.join(HERE,'store.js'),'utf8');

test('motion trace Viewer is OFF by default and requires explicit Mob selection',()=>{
  assert.match(index,/id="trail"[^>]*value="0"/);
  assert.match(index,/id="trailV"[^>]*>0t</);
  assert.match(index,/id="traceSubject"/);
  assert.match(index,/trail:0,traceSubject:''/);
  assert.match(index,/function selectedTraceEntity\(\)/);
});

test('selected Mob trace reads retained samples rather than forward-filled at(t)',()=>{
  assert.match(store,/samples:\s*\(startTick, endTick, limit\)/);
  assert.match(store,/SIMLAB_POS_RETAINED_POINT/);
  const uses=(index.match(/typeof tr\.samples==='function'/g)||[]).length;
  assert.ok(uses>=2,'F3 and plan/elevation must both consume retained samples');
  assert.match(index,/tr\.samples\(Math\.max\(t0,tr\.t0\),Math\.min\(T\.tick,tr\.t1\),4096\)/);
});

test('Mob and projectile traces have non-color visual distinction',()=>{
  assert.match(index,/setLineDash\(\[10,6\]\)/);
  assert.match(index,/lineWidth=2\.5/);
  assert.match(index,/arc\(q\.x,q\.y,2\.6/);
  assert.match(index,/if\(e\.role!=='projectile'\) continue/);
});
