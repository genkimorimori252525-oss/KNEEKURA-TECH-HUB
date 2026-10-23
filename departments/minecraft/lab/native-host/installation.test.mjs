import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {verifyImportClosure} from './tank.mjs';
test('installation rejects omitted transitive dependency and paths escaping bundle',async t=>{const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-closure-test-'));t.after(()=>fs.rm(root,{recursive:true,force:true}));await fs.writeFile(path.join(root,'entry.mjs'),"export {x} from './library.mjs';\n");await assert.rejects(verifyImportClosure(root),/ENOENT/);await fs.writeFile(path.join(root,'library.mjs'),'export const x=1;\n');await verifyImportClosure(root);await fs.writeFile(path.join(root,'entry.mjs'),"export {x} from '../foreign.mjs';\n");await assert.rejects(verifyImportClosure(root),/IMPORT_ESCAPE/);});
