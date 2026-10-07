import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from '../../evidence/tests/visual-fixture.mjs';
import {preparedOwner} from './owner-action-fixture.mjs';
import {requestDeclaredCapture} from '../owner-action-adapter.mjs';
import {readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
const bundles=await import('../capture-bundle.mjs').catch(e=>{if(e.code==='ERR_MODULE_NOT_FOUND')return {};throw e;});
test('original capture slot inspection stays unknown without completion and never resubmits',async t=>{
 assert.equal(typeof bundles.captureBundle,'function');const f=await preparedOwner(t,{capture:true});
 const intent=await requestDeclaredCapture({...f.controlOptions,captureIndex:0}),file=path.join(f.runDir,'control/captures',intent.captureKey,'request.json'),before=await readFile(file);
 const result=await bundles.captureBundle({...f.controlOptions,captureIndex:0});assert.equal(result.status,'UNKNOWN');assert.equal(result.execution,'NOT_CONFIRMED');
 assert.deepEqual(await readFile(file),before);
});
test('bundle reader verifies four raw images, keeps their order and exposes integrity failure',async t=>{
 assert.equal(typeof bundles.bundleFromManifest,'function');const f=await fixture(t);
 const b=await bundles.bundleFromManifest({runDir:f.runDir,manifest:f.manifest});assert.equal(b.status,'COMPLETE');assert.equal(b.artifactRole,'REFERENCES_TO_RAW_AND_STRUCTURED_EVIDENCE');
 assert.deepEqual(b.views.map(v=>v.view),['north','east','south','west']);assert.equal(b.restoration,'RESTORED');
 const file=path.join(f.runDir,f.manifest.frames[0].imagePath);await writeFile(file,'corrupted fixture bytes');
 const broken=await bundles.bundleFromManifest({runDir:f.runDir,manifest:f.manifest});assert.equal(broken.status,'UNKNOWN');assert.equal(broken.views[0].verification,'UNKNOWN_INTEGRITY');
});
