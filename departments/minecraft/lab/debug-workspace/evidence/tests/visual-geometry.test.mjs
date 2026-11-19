import test from 'node:test';
import assert from 'node:assert/strict';
import { project } from '../visual-geometry.mjs';
const camera=()=>({position:[0,2,10],quaternion:[0,0,0,1],viewport:[64,64],
 matrixConvention:'JOML_COLUMN_MAJOR_CAMERA_RELATIVE',
 viewMatrix:[1,0,0,0,0,1,0,0,0,0,1,0,2,0,0,1],
 projectionMatrix:[1,0,0,0,0,1,0,0,0,0,-1,-1,0,0,-.2,0]});
test('projection uses exact recorded camera-relative view matrix including translation',()=>{
 const p=project([0,2,0],camera());assert.ok(Math.abs(p.x-38.4)<1e-10);assert.equal(p.y,32);
});
test('projection refuses unknown convention and leaves points behind camera unresolved',()=>{
 const c=camera();c.matrixConvention='UNKNOWN';assert.throws(()=>project([0,2,0],c),/CONVENTION/);
 assert.equal(project([0,2,20],camera()),null);
});
