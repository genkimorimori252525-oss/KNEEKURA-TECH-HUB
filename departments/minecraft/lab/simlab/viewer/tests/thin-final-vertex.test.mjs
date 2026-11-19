import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import {
  FINAL_VERTEX_STRIDE_BYTES,
  ThinFinalVertexReplayError,
  applyDirectionalVertexLighting,
  buildFinalVertexReplayPlan,
  shadeFinalVertexSample,
  validateFinalVertexBuffer,
} from '../thin-final-vertex.js';

const H = (c) => `sha256:${c.repeat(64)}`;
const ID = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
const ID3 = [1,0,0, 0,1,0, 0,0,1];

function replayMaterial() {
  return {
    alphaMode: 'mask', alphaCutoff: 0.1,
    blend: { enabled: false, equation: 'UNKNOWN', srcFactor: 'UNKNOWN', dstFactor: 'UNKNOWN' },
    cullMode: 'back', depth: { testFunction: '<=', write: true },
    emissive: false, fullbright: false, fogMode: 'colorMixPreserveAlpha',
    sampler: { status: 'measured', bilinear: false, mipmap: false },
    vertexTint: 'vertexColor', lightmap: true, overlay: true,
    replay: {
      status: 'measured',
      vertexLighting: { mode: 'dualDirectionalDiffuse', power: 0.6, ambient: 0.4, clampMax: 1 },
      fogDistance: 'modelViewInverseViewRotationShape',
      textureCombine: 'sample0TimesVertexTimesShaderColor',
      alphaDiscardSource: 'sampler0Alpha',
      overlayCombine: 'rgbMixByOverlayAlpha',
      lightmapCombine: 'multiplyRgba',
    },
  };
}

function fixture() {
  const packHash=H('a'), layoutHash=H('b');
  const pack = {
    manifest: { modelId:'test:reimu', packHash, layoutHash },
    mesh: { drawGroups:[{ groupId:'body', materialId:'body', order:0 }] },
    materials: { materials:[{ materialId:'body', baseTexture:'textures/body.png', sourceTextureResourceId:'test:textures/body.png' }] },
  };
  const material = replayMaterial();
  const frame = {
    modelId:'test:reimu', packHash, layoutHash,
    source:{type:'runtimeFinalVertex',authority:'authoritative',fidelityTier:0,auxiliarySamplerInputs:'resolved-per-vertex-rgba'},
    modelToWorldMatrix:[...ID], modelNormalToWorldMatrix:[...ID3],
    globalShaderState:{
      matrixConvention:'JOML_COLUMN_MAJOR_COLUMN_VECTOR', modelViewMatrix:[...ID], projectionMatrix:[...ID], inverseViewRotationMatrix:[...ID3],
      directionalLights:[[0,0,1],[0,0,-1]], shaderColor:[1,1,1,1],
      fog:{curve:'smoothstep',start:0,end:96,color:[0.5,0.6,0.7,1],shape:'sphere',distanceSpace:'modelView'},
    },
    deformation:{type:'finalVertices',format:'KNEEKURA_FINAL_VERTEX_V2',strideFloats:24,vertexCount:4,groups:[{groupId:'body',order:0,vertexStart:0,vertexCount:4,primitiveMode:'QUADS'}]},
    drawOrder:['body'],
    drawStates:{body:{visible:true,textureResourceId:'test:textures/body.png',material}},
  };
  return {frame,pack,material};
}

function buffer(vertexCount=4) {
  const values=[];
  for(let i=0;i<vertexCount;i++) values.push(i,0,0, 0,0, 0,0,1, 1,1,1,1, 0,0, 240,240, 1,0,0,0.25, 0.8,0.9,1,1);
  const bytes=new Uint8Array(values.length*4); const view=new DataView(bytes.buffer);
  values.forEach((v,i)=>view.setFloat32(i*4,v,true));
  return bytes;
}

test('final-vertex replay plan uses only pack Sampler0 plus captured generic attributes', () => {
  const {frame,pack}=fixture();
  const plan=buildFinalVertexReplayPlan(frame,pack);
  assert.equal(plan.strideBytes, FINAL_VERTEX_STRIDE_BYTES);
  assert.deepEqual(plan.modelNormalToWorldMatrix, ID3);
  assert.equal(plan.groups[0].sampler0.texture,'textures/body.png');
  assert.deepEqual(plan.groups[0].primitive.indices,[0,1,2,2,3,0]);
  assert.match(plan.groups[0].shader.vertex,/aOverlayColor/);
  assert.match(plan.groups[0].shader.vertex,/uModelNormalToWorld \* aNormal/);
  assert.match(plan.groups[0].shader.fragment,/uSampler0/);
  assert.doesNotMatch(plan.groups[0].shader.vertex + plan.groups[0].shader.fragment,/Sampler[12]/);
});

test('Thin Viewer module contains no source-specific semantic reconstruction', async () => {
  const source=await readFile(new URL('../thin-final-vertex.js',import.meta.url),'utf8');
  assert.doesNotMatch(source,/\b(?:ysm|molang|hurt|biome|weather)\b/i);
  assert.doesNotMatch(source,/Sampler[12]/);
});

test('buffer validation accepts V2 resolved colors and rejects out-of-range auxiliary evidence', () => {
  const {frame}=fixture(); const bytes=buffer();
  assert.equal(validateFinalVertexBuffer(frame,bytes),true);
  new DataView(bytes.buffer).setFloat32(16*4,1.5,true);
  assert.throws(()=>validateFinalVertexBuffer(frame,bytes),ThinFinalVertexReplayError);
});

test('generic fragment replay preserves operation order and sample-alpha discard', () => {
  const {material}=fixture();
  const result=shadeFinalVertexSample({material,sampler0:[0.8,0.5,0.25,0.5],vertexColor:[0.5,1,1,1],overlayColor:[1,0,0,0.25],lightmapColor:[0.5,1,1,1],shaderColor:[1,0.5,1,1],fogDistance:0,fog:{start:0,end:10,color:[0,0,0,1]}});
  assert.equal(result.discarded,false);
  assert.deepEqual(result.color.map(x=>Number(x.toFixed(6))),[0.425,0.0625,0.0625,0.5]);
  const discarded=shadeFinalVertexSample({material,sampler0:[1,1,1,0.05],vertexColor:[1,1,1,1],overlayColor:[0,0,0,1],lightmapColor:[1,1,1,1],shaderColor:[1,1,1,1],fogDistance:0,fog:{start:0,end:10,color:[0,0,0,1]}});
  assert.equal(discarded.discarded,true);
});

test('dual directional replay uses measured 0.6/0.4 lighting constants', () => {
  const {material}=fixture(); const lighting=material.replay.vertexLighting;
  assert.deepEqual(applyDirectionalVertexLighting([0.8,0.5,0.25,1],[0,0,1],[[0,0,1],[0,0,-1]],lighting),[0.8,0.5,0.25,1]);
  assert.deepEqual(applyDirectionalVertexLighting([1,0.5,0.25,1],[1,0,0],[[0,0,1],[0,0,-1]],lighting),[0.4,0.2,0.1,1]);
});

test('unmeasured replay semantics and unproven primitive paths fail closed', () => {
  const {frame,pack}=fixture();
  frame.drawStates.body.material.replay={status:'UNKNOWN'};
  assert.throws(()=>buildFinalVertexReplayPlan(frame,pack),/not measured/);
  const x=fixture(); x.frame.deformation.groups[0].primitiveMode='LINES';
  assert.throws(()=>buildFinalVertexReplayPlan(x.frame,x.pack),/separately proven raster path/);
});
