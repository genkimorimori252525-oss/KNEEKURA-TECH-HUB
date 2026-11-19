import assert from 'node:assert/strict';
import test from 'node:test';
import {
  findHeadlessBrowser,
  renderHeadlessFinalVertexBuffers,
} from '../headless-final-vertex.mjs';

const ID4 = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
const ID3 = [1,0,0, 0,1,0, 0,0,1];
const H = (c) => 'sha256:' + c.repeat(64);

function runtimeMaterial() {
  return {
    alphaMode: 'opaque',
    alphaCutoff: null,
    blend: {
      enabled: false,
      equation: 'UNKNOWN',
      srcFactor: 'UNKNOWN',
      dstFactor: 'UNKNOWN',
    },
    cullMode: 'none',
    depth: { testFunction: '<=', write: true },
    overlay: false,
    lightmap: false,
    emissive: false,
    fullbright: false,
    fogMode: 'colorMixPreserveAlpha',
    sampler: { status: 'measured', bilinear: false, mipmap: false },
    replay: {
      status: 'measured',
      vertexLighting: {
        mode: 'none',
        power: 0,
        ambient: 1,
        clampMax: 1,
      },
      fogDistance: 'modelViewLength',
      textureCombine: 'sample0TimesVertexTimesShaderColor',
      alphaDiscardSource: 'none',
      overlayCombine: 'none',
      lightmapCombine: 'none',
    },
  };
}

function fixture() {
  const material = runtimeMaterial();
  const frame = {
    schema: 'kneekura.renderframe',
    schemaVersion: '1.0.0',
    runId: 'headless-smoke',
    entityUuid: '00000000-0000-0000-0000-000000000001',
    renderSequence: 1,
    gameTime: 1,
    partialTick: 0,
    modelId: 'test:headless',
    packHash: H('a'),
    layoutHash: H('b'),
    source: {
      type: 'runtimeFinalVertex',
      authority: 'authoritative',
      fidelityTier: 0,
      auxiliarySamplerInputs: 'resolved-per-vertex-rgba',
    },
    modelToWorldMatrix: [...ID4],
    modelNormalToWorldMatrix: [...ID3],
    globalShaderState: {
      matrixConvention: 'JOML_COLUMN_MAJOR_COLUMN_VECTOR',
      modelViewMatrix: [...ID4],
      projectionMatrix: [...ID4],
      inverseViewRotationMatrix: [...ID3],
      directionalLights: [[0,1,0],[0,-1,0]],
      shaderColor: [1,1,1,1],
      fog: {
        curve: 'smoothstep',
        start: 100,
        end: 200,
        color: [0,0,0,1],
        shape: 'sphere',
        distanceSpace: 'modelView',
      },
    },
    deformation: {
      type: 'finalVertices',
      bufferRef: 'frame.bin',
      vertexCount: 3,
      strideFloats: 24,
      format: 'KNEEKURA_FINAL_VERTEX_V2',
      groups: [{
        groupId: 'body',
        order: 0,
        vertexStart: 0,
        vertexCount: 3,
        primitiveMode: 'TRIANGLES',
      }],
    },
    visibility: {
      bones: [],
      bonesResolvedInFinalVertices: true,
      groups: [true],
    },
    drawOrder: ['body'],
    drawStates: {
      body: {
        visible: true,
        textureResourceId: 'test:textures/body.png',
        material,
        vertexColorInBuffer: true,
        overlayCoordinatesInBuffer: true,
        lightCoordinatesInBuffer: true,
        resolvedOverlayColorInBuffer: true,
        resolvedLightmapColorInBuffer: true,
      },
    },
  };
  const pack = {
    manifest: {
      modelId: 'test:headless',
      packHash: H('a'),
      layoutHash: H('b'),
    },
    mesh: {
      drawGroups: [{
        groupId: 'body',
        materialId: 'body',
      }],
    },
    materials: {
      materials: [{
        materialId: 'body',
        sourceTextureResourceId: 'test:textures/body.png',
        baseTexture: 'textures/body.png',
      }],
    },
  };

  const vertices = [
    [-0.75,-0.75,0, 0.5,0.5, 0,0,1, 1,0,0,1],
    [ 0.75,-0.75,0, 0.5,0.5, 0,0,1, 1,0,0,1],
    [ 0.00, 0.75,0, 0.5,0.5, 0,0,1, 1,0,0,1],
  ];
  const buffer = Buffer.alloc(3 * 24 * 4);
  const view = new DataView(buffer.buffer, buffer.byteOffset, buffer.byteLength);
  for (let vertex = 0; vertex < 3; vertex++) {
    const values = [
      ...vertices[vertex],
      0,0,0,0,
      1,1,1,1,
      1,1,1,1,
    ];
    assert.equal(values.length, 24);
    for (let component = 0; component < values.length; component++) {
      view.setFloat32((vertex * 24 + component) * 4, values[component], true);
    }
  }
  return { frame, pack, frameBytes: new Uint8Array(buffer) };
}

test('Windows/browser headless Thin Viewer renders deterministic framebuffer pixels', { timeout: 120000 }, async () => {
  const browserPath = await findHeadlessBrowser();
  console.log('KNEEKURA_HEADLESS_BROWSER=' + browserPath);
  const { frame, pack, frameBytes } = fixture();
  const width = 16;
  const height = 16;
  const backgroundRgba = new Uint8Array(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    backgroundRgba[i * 4 + 2] = 255;
    backgroundRgba[i * 4 + 3] = 255;
  }
  const depth = new Float32Array(width * height);
  depth.fill(1);
  const textureImages = new Map([[
    'textures/body.png',
    { width: 1, height: 1, rgba: Uint8Array.from([255,255,255,255]) },
  ]]);

  const selectedBackend = 'd3d11-warp-webgl';
  console.log('KNEEKURA_HEADLESS_SELECTED_BACKEND=' + selectedBackend);
  const render = await renderHeadlessFinalVertexBuffers({
    frame,
    pack,
    frameBytes,
    background: { width, height, rgba: backgroundRgba },
    depth: { width, height, values: depth },
    textureImages,
    framebuffer: { width, height, viewportWidth: width, viewportHeight: height },
    browserPath,
    angleBackend: selectedBackend,
    timeoutMs: 30000,
  });
  console.log('KNEEKURA_HEADLESS_GL_RENDERER=' + render.gl.renderer);

  assert.equal(render.width, width);
  assert.equal(render.height, height);
  assert.ok(render.gl.renderer.length > 0);
  const center = ((8 * width) + 8) * 4;
  assert.deepEqual([...render.rgba.slice(center, center + 4)], [255,0,0,255]);
  assert.deepEqual([...render.rgba.slice(0, 4)], [0,0,255,255]);
});
