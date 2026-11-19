import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { compileRenderPack, RenderPackCompileError } from '../compiler.mjs';
import { loadRenderPack, RenderPackLoadError } from '../loader.mjs';

const H = (c) => `sha256:${c.repeat(64)}`;
const ID = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];

async function symlinkOrSkip(t, target, linkPath) {
  try {
    await symlink(target, linkPath);
    return true;
  } catch (error) {
    if (process.platform === 'win32' &&
        (error?.code === 'EPERM' || error?.code === 'EACCES')) {
      t.skip(
        'Windows runner cannot create symbolic links; symlink security check is not executable in this environment'
      );
      return false;
    }
    throw error;
  }
}

function triangle(x) {
  return [
    x, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1,
    x + 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1,
    x, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1,
  ];
}

async function setupCapture() {
  const captureRoot = await mkdtemp(join(tmpdir(), 'kneekura-capture-'));
  const outputRoot = await mkdtemp(join(tmpdir(), 'kneekura-packs-'));
  await mkdir(join(captureRoot, 'textures'), { recursive: true });
  await writeFile(join(captureRoot, 'textures', 'body.png'), Buffer.from([1, 2, 3, 4]));
  await writeFile(join(captureRoot, 'textures', 'hair.png'), Buffer.from([5, 6, 7, 8]));
  await writeFile(join(captureRoot, 'textures', 'glow.png'), Buffer.from([9, 10, 11, 12]));
  const capture = {
    schema: 'kneekura.static-render-capture',
    schemaVersion: '1.0.0',
    modelId: 'test:multi-group',
    coordinateSystem: 'KNEEKURA_RH_Y_UP_BLOCK',
    vertexStrideFloats: 11,
    topology: 'expandedTriangles',
    source: {
      adapter: 'fixture',
      classification: 'runtimeVertexSnapshot',
      modVersion: 'test',
      modJarHash: H('a'),
      modelResourceHash: H('b'),
    },
    bones: [{
      slot: 0,
      name: 'root',
      parentSlot: null,
      bindMatrix: ID,
      inverseBindMatrix: ID,
    }],
    groups: [
      {
        groupId: 'body', order: 0, materialId: 'body', sourceRenderType: 'entityCutout(body)',
        texture: { sourcePath: 'textures/body.png', sourceResourceId: 'test:textures/body.png' },
        vertices: [...triangle(0), ...triangle(2), ...triangle(4)],
      },
      {
        groupId: 'hair', order: 1, materialId: 'hair', sourceRenderType: 'entityTranslucent(hair)',
        texture: { sourcePath: 'textures/hair.png', sourceResourceId: 'test:textures/hair.png' }, vertices: triangle(10),
      },
      {
        groupId: 'glow', order: 2, materialId: 'glow', sourceRenderType: 'eyes(glow)',
        texture: { sourcePath: 'textures/glow.png', sourceResourceId: 'test:textures/glow.png' }, vertices: triangle(20),
      },
    ],
  };
  return { captureRoot, outputRoot, capture };
}

async function cleanup(...paths) {
  await Promise.all(paths.map((p) => rm(p, { recursive: true, force: true })));
}

test('compiler preserves every draw group even when body is the largest group', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    const { mesh, materials } = await compileRenderPack({ capture, captureRoot, outputRoot });
    assert.deepEqual(mesh.drawGroups.map((g) => g.groupId), ['body', 'hair', 'glow']);
    assert.deepEqual(mesh.drawGroups.map((g) => g.order), [0, 1, 2]);
    assert.deepEqual(mesh.drawGroups.map((g) => g.sourceRenderType), [
      'entityCutout(body)', 'entityTranslucent(hair)', 'eyes(glow)',
    ]);
    assert.equal(mesh.drawGroups[0].indexCount, 9);
    assert.equal(mesh.drawGroups[1].indexCount, 3);
    assert.equal(mesh.drawGroups[2].indexCount, 3);
    assert.equal(materials.materials.length, 3);
    assert.deepEqual(materials.materials.map((m) => m.sourceTextureResourceId), [
      'test:textures/body.png', 'test:textures/hair.png', 'test:textures/glow.png',
    ]);
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('PR-A materials preserve unknown render state instead of guessing defaults', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    const { materials } = await compileRenderPack({ capture, captureRoot, outputRoot });
    for (const material of materials.materials) {
      assert.equal(material.alphaMode, 'UNKNOWN');
      assert.equal(material.blend.enabled, 'UNKNOWN');
      assert.equal(material.cullMode, 'UNKNOWN');
      assert.equal(material.depth.write, 'UNKNOWN');
      assert.equal(material.emissive, 'UNKNOWN');
      assert.equal(material.lightmap, 'UNKNOWN');
      assert.equal(material.overlay, 'UNKNOWN');
    }
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('textures are content-addressed and the compiled pack survives capture source deletion', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    const result = await compileRenderPack({ capture, captureRoot, outputRoot });
    const texturePaths = result.materials.materials.map((m) => m.baseTexture);
    assert.equal(new Set(texturePaths).size, 3);
    for (const p of texturePaths) assert.match(p, /^textures\/[0-9a-f]{64}\.png$/);
    await rm(captureRoot, { recursive: true, force: true });
    const loaded = await loadRenderPack(result.packDir);
    assert.deepEqual(loaded.mesh.drawGroups.map((g) => g.groupId), ['body', 'hair', 'glow']);
  } finally {
    await cleanup(outputRoot);
  }
});

test('layoutHash and packHash are deterministic across capture directories', async () => {
  const a = await setupCapture();
  const b = await setupCapture();
  try {
    const ra = await compileRenderPack({ capture: a.capture, captureRoot: a.captureRoot, outputRoot: a.outputRoot });
    const rb = await compileRenderPack({ capture: b.capture, captureRoot: b.captureRoot, outputRoot: b.outputRoot });
    assert.equal(ra.manifest.layoutHash, rb.manifest.layoutHash);
    assert.equal(ra.manifest.packHash, rb.manifest.packHash);
  } finally {
    await cleanup(a.captureRoot, a.outputRoot, b.captureRoot, b.outputRoot);
  }
});

test('compiler rejects texture path traversal', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    capture.groups[0].texture.sourcePath = '../secret.png';
    await assert.rejects(
      compileRenderPack({ capture, captureRoot, outputRoot }),
      (error) => error instanceof RenderPackCompileError && /path traversal/.test(error.message),
    );
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('compiler rejects out-of-range topology indices instead of repairing them', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    capture.groups[1].indices = [0, 1, 99];
    await assert.rejects(
      compileRenderPack({ capture, captureRoot, outputRoot }),
      (error) => error instanceof RenderPackCompileError && /exceeds group vertexCount/.test(error.message),
    );
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('compiler rejects symbolic-link texture sources even when the lexical path is inside capture root', async (t) => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  const external = await mkdtemp(join(tmpdir(), 'kneekura-external-'));
  try {
    await writeFile(join(external, 'secret.png'), Buffer.from([99, 98, 97]));
    await rm(join(captureRoot, 'textures', 'hair.png'));
    if (!(await symlinkOrSkip(
      t,
      join(external, 'secret.png'),
      join(captureRoot, 'textures', 'hair.png')
    ))) {
      return;
    }
    await assert.rejects(
      compileRenderPack({ capture, captureRoot, outputRoot }),
      (error) => error instanceof RenderPackCompileError && /symbolic-link texture sources are forbidden/.test(error.message),
    );
  } finally {
    await cleanup(captureRoot, outputRoot, external);
  }
});

test('unknown bind matrices remain explicit null rather than identity guesses', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    capture.bones[0].bindMatrix = null;
    capture.bones[0].bindMatrixAuthority = 'UNKNOWN';
    capture.bones[0].inverseBindMatrix = null;
    capture.bones[0].inverseBindMatrixAuthority = 'UNKNOWN';
    const { mesh } = await compileRenderPack({ capture, captureRoot, outputRoot });
    assert.equal(mesh.bones[0].bindMatrix, null);
    assert.equal(mesh.bones[0].inverseBindMatrix, null);
    assert.equal(mesh.bones[0].bindMatrixAuthority, 'UNKNOWN');
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('loader fails closed when a packed file is corrupted', async () => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  try {
    const result = await compileRenderPack({ capture, captureRoot, outputRoot });
    const meshPath = join(result.packDir, 'mesh', 'mesh.bin');
    const bytes = await readFile(meshPath);
    bytes[0] ^= 0xff;
    await writeFile(meshPath, bytes);
    await assert.rejects(loadRenderPack(result.packDir), (error) => error instanceof RenderPackLoadError && /hash mismatch/.test(error.message));
  } finally {
    await cleanup(captureRoot, outputRoot);
  }
});

test('loader rejects symbolic links inside a compiled pack', async (t) => {
  const { captureRoot, outputRoot, capture } = await setupCapture();
  const external = await mkdtemp(join(tmpdir(), 'kneekura-pack-external-'));
  try {
    const result = await compileRenderPack({ capture, captureRoot, outputRoot });
    const meshPath = join(result.packDir, 'mesh', 'mesh.bin');
    await writeFile(join(external, 'mesh.bin'), await readFile(meshPath));
    await rm(meshPath);
    if (!(await symlinkOrSkip(t, join(external, 'mesh.bin'), meshPath))) {
      return;
    }
    await assert.rejects(
      loadRenderPack(result.packDir),
      (error) => error instanceof RenderPackLoadError && /symbolic links are forbidden/.test(error.message),
    );
  } finally {
    await cleanup(captureRoot, outputRoot, external);
  }
});