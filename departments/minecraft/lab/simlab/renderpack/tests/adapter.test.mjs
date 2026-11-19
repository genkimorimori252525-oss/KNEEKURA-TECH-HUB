import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { compileDumpModelToRenderPack } from '../dumpmodels-adapter.mjs';
import { loadRenderPack } from '../loader.mjs';
import { createCompileTextureResolver, TextureResolveError } from '../texture-resolver.mjs';

const H = (c) => `sha256:${c.repeat(64)}`;

async function symlinkOrSkip(t, target, linkPath) {
  try {
    await symlink(target, linkPath);
    return true;
  } catch (error) {
    if (process.platform === 'win32' &&
        (error?.code === 'EPERM' || error?.code === 'EACCES')) {
      t.skip(
        'Windows runner cannot create symbolic links; symlink escape check is not executable in this environment'
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

async function setupModAssets() {
  const root = await mkdtemp(join(tmpdir(), 'kneekura-mod-assets-'));
  for (const [name, bytes] of [['body', [1, 2]], ['hair', [3, 4]], ['glow', [5, 6]]]) {
    const dir = join(root, 'test', 'textures');
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, `${name}.png`), Buffer.from(bytes));
  }
  return root;
}

function dumpFixture() {
  return {
    type: 'test:multi-group',
    renderGroupsVersion: 1,
    skeleton: {
      schema: 'kneekura.capture-skeleton',
      schemaVersion: 1,
      source: 'runtimeBonePaletteSlotMap',
      authority: 'measuredSlotMap',
      bones: [
        {
          slot: 0,
          name: 'root',
          parentSlot: null,
          parentSlotAuthority: 'UNKNOWN',
          bindMatrix: null,
          bindMatrixAuthority: 'UNKNOWN',
          inverseBindMatrix: null,
          inverseBindMatrixAuthority: 'UNKNOWN',
        },
        {
          slot: 1,
          name: 'hair',
          parentSlot: null,
          parentSlotAuthority: 'UNKNOWN',
          bindMatrix: null,
          bindMatrixAuthority: 'UNKNOWN',
          inverseBindMatrix: null,
          inverseBindMatrixAuthority: 'UNKNOWN',
        },
      ],
    },
    renderGroups: {
      idle: [
        {
          groupId: 'entityCutout(body)',
          order: 0,
          quads: 3,
          vertexCount: 9,
          texture: 'test:textures/body.png',
          sourceRenderType: 'entityCutout(body)',
          material: {
            alphaMode: 'UNKNOWN',
            blend: { enabled: 'UNKNOWN', equation: 'UNKNOWN', srcFactor: 'UNKNOWN', dstFactor: 'UNKNOWN' },
            cullMode: 'back',
            depth: { testFunction: '<=', write: 'UNKNOWN' },
            emissive: 'UNKNOWN',
            fullbright: 'UNKNOWN',
            fogMode: 'UNKNOWN',
            sampler: { status: 'UNKNOWN' },
            vertexTint: 'UNKNOWN',
            lightmap: true,
            overlay: false,
            captureStatus: 'partial-measured',
            capture: {
              method: 'RenderType.CompositeState field observation',
              transparencyShard: { name: 'no_transparency' },
            },
          },
          vertices: [...triangle(0), ...triangle(2), ...triangle(4)],
        },
        {
          groupId: 'entityTranslucent(hair)',
          order: 1,
          quads: 1,
          vertexCount: 3,
          texture: 'test:textures/hair.png',
          sourceRenderType: 'entityTranslucent(hair)',
          vertices: triangle(10),
        },
        {
          groupId: 'eyes(glow)',
          order: 2,
          quads: 1,
          vertexCount: 3,
          texture: 'test:textures/glow.png',
          sourceRenderType: 'eyes(glow)',
          vertices: triangle(20),
        },
      ],
    },
  };
}

test('dumpmodels adapter carries every captured RenderType group into a self-contained pack', async () => {
  const modAssets = await setupModAssets();
  const outputRoot = await mkdtemp(join(tmpdir(), 'kneekura-adapter-output-'));
  try {
    const textureResolver = createCompileTextureResolver({ modAssets });
    const result = await compileDumpModelToRenderPack({
      dump: dumpFixture(),
      outputRoot,
      textureResolver,
      source: {
        adapter: 'tlmsim-dumpmodels-v1',
        classification: 'runtimeVertexSnapshot',
        modVersion: 'fixture',
        modJarHash: H('a'),
        modelResourceHash: H('b'),
      },
     });
    assert.equal(result.selectedPose, 'idle');
    assert.deepEqual(result.mesh.drawGroups.map((g) => g.groupId), [
      'entityCutout(body)', 'entityTranslucent(hair)', 'eyes(glow)',
    ]);
    assert.deepEqual(result.mesh.drawGroups.map((g) => g.order), [0, 1, 2]);
    assert.equal(result.materials.materials.length, 3);
    const bodyMaterial = result.materials.materials[0];
    assert.equal(bodyMaterial.cullMode, 'back');
    assert.equal(bodyMaterial.depth.testFunction, '<=');
    assert.equal(bodyMaterial.depth.write, 'UNKNOWN');
    assert.equal(bodyMaterial.lightmap, true);
    assert.equal(bodyMaterial.overlay, false);
    assert.equal(bodyMaterial.fogMode, 'UNKNOWN');
    assert.equal(bodyMaterial.alphaMode, 'UNKNOWN');
    assert.equal(bodyMaterial.blend.enabled, 'UNKNOWN');
    assert.equal(bodyMaterial.captureStatus, 'partial-measured');
    assert.equal(bodyMaterial.replay.status, 'UNKNOWN');
    assert.equal(bodyMaterial.capture.transparencyShard.name, 'no_transparency');
    assert.equal(result.manifest.source.classification, 'runtimeVertexSnapshot');
    assert.equal(result.mesh.source.classification, 'runtimeVertexSnapshot');
    assert.deepEqual(result.mesh.bones.map((b) => [b.slot, b.name]), [[0, 'root'], [1, 'hair']]);
    assert.equal(result.mesh.bones[1].parentSlot, null);
    assert.equal(result.mesh.bones[1].parentSlotAuthority, 'UNKNOWN');
    assert.equal(result.mesh.bones[1].bindMatrix, null);
    assert.equal(result.mesh.bones[1].bindMatrixAuthority, 'UNKNOWN');

    await rm(modAssets, { recursive: true, force: true });
    const loaded = await loadRenderPack(result.packDir);
    assert.equal(loaded.mesh.drawGroups.length, 3);
    for (const material of loaded.materials.materials) {
      assert.match(material.baseTexture, /^textures\/[0-9a-f]{64}\.png$/);
    }
  } finally {
    await rm(modAssets, { recursive: true, force: true });
    await rm(outputRoot, { recursive: true, force: true });
  }
});

test('compile-time resolver rejects resource path traversal', async () => {
  const modAssets = await setupModAssets();
  try {
    const resolveTexture = createCompileTextureResolver({ modAssets });
    assert.throws(() => resolveTexture('test:../secret.png'), TextureResolveError);
  } finally {
    await rm(modAssets, { recursive: true, force: true });
  }
});

test('compile-time resolver rejects parent-directory symlink escape from modAssets', async (t) => {
  const modAssets = await mkdtemp(join(tmpdir(), 'kneekura-mod-root-'));
  const external = await mkdtemp(join(tmpdir(), 'kneekura-mod-external-'));
  try {
    await mkdir(join(external, 'test', 'textures'), { recursive: true });
    await writeFile(join(external, 'test', 'textures', 'escape.png'), Buffer.from([1, 2, 3]));
    if (!(await symlinkOrSkip(t, join(external, 'test'), join(modAssets, 'test')))) {
      return;
    }
    const resolveTexture = createCompileTextureResolver({ modAssets });
    assert.throws(
      () => resolveTexture('test:textures/escape.png'),
      /resolves outside its configured root/,
    );
  } finally {
    await rm(modAssets, { recursive: true, force: true });
    await rm(external, { recursive: true, force: true });
  }
});

test('YSM resolver fails closed when more than one pack exists instead of choosing the first', async () => {
  const modAssets = await setupModAssets();
  const custom = await mkdtemp(join(tmpdir(), 'kneekura-ysm-custom-'));
  try {
    for (const name of ['pack-a', 'pack-b']) {
      const dir = join(custom, name);
      await mkdir(join(dir, 'textures'), { recursive: true });
      await writeFile(join(dir, 'ysm.json'), '{}');
      await writeFile(join(dir, 'textures', 'texture2.png'), Buffer.from([7, 8, 9]));
    }
    const ambiguous = createCompileTextureResolver({ modAssets, ysmCustomDir: custom });
    assert.throws(() => ambiguous('ysm:textures/texture2.png'), /multiple YSM packs found/);

    const explicit = createCompileTextureResolver({
      modAssets,
      ysmCustomDir: custom,
      ysmPackDir: join(custom, 'pack-b'),
    });
    const resolved = explicit('ysm:textures/texture2.png');
    assert.deepEqual([...resolved.bytes], [7, 8, 9]);
  } finally {
    await rm(modAssets, { recursive: true, force: true });
    await rm(custom, { recursive: true, force: true });
  }
});

test('material probe calibrates standard shards without classifying RenderType or shader names', async () => {
  const source = await readFile(
    'bridge/tlm-forge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/client/SimRenderTypeMaterialProbe.java',
    'utf8',
  );

  // RenderType text and shard names may be retained as provenance only; never branch on them.
  assert.doesNotMatch(
    source,
    /String\.valueOf\(type\)[\s\S]{0,240}\.(?:contains|startsWith|endsWith|matches|equals)\(/,
  );
  assert.doesNotMatch(
    source,
    /shardName\([^)]*\)[\s\S]{0,240}(?:contains|startsWith|endsWith|matches|equals|switch)/,
  );

  // Standard semantics come from public canonical RenderType factories + shard object identity.
  for (const factory of [
    'entitySolid',
    'entityCutout',
    'entityCutoutNoCull',
    'entityCutoutNoCullZOffset',
    'entitySmoothCutout',
    'entityTranslucent',
    'entityTranslucentCull',
    'entityTranslucentEmissive',
    'eyes',
  ]) {
    assert.ok(source.includes('RenderType.' + factory + '('), 'missing canonical factory ' + factory);
  }
  assert.match(source, /actual == c\.noTransparency/);
  assert.match(source, /actual == c\.translucentTransparency/);
  assert.match(source, /actual == c\.additiveTransparency/);
  assert.match(source, /actual == profile\.shader\(\)/);
  assert.match(source, /new BlendState\(true, "add", "srcAlpha", "oneMinusSrcAlpha"/);
  assert.match(source, /new BlendState\(true, "add", "one", "one"/);
  assert.match(
    source,
    /translucentEmissive, "blend", 0\.1F, true, true, "rgbaFade", emissiveReplay\)/,
    '1.20.1 translucent-emissive must remain emissive + fullbright',
  );
  assert.match(
    source,
    /eyes,\s*"blend", null, true, true, "rgbaFade", null\)/,
    '1.20.1 eyes profile must remain emissive + fullbright',
  );

  // Field meaning is calibrated with constructor inputs rather than reflected field names.
  assert.match(source, /new RenderStateShard\.WriteMaskStateShard\(false, true\)/);
  assert.match(source, /new RenderStateShard\.WriteMaskStateShard\(true, false\)/);
  assert.match(source, /new RenderStateShard\.TextureStateShard\(CALIBRATION_TEXTURE, true, false\)/);
  assert.match(source, /new RenderStateShard\.TextureStateShard\(CALIBRATION_TEXTURE, false, true\)/);

  // Unknown/custom paths still start fail-closed.
  assert.match(source, /addProperty\("alphaMode",\s*"UNKNOWN"\)/);
  assert.match(source, /blend\.addProperty\("enabled",\s*"UNKNOWN"\)/);
  assert.match(source, /depth\.addProperty\("write",\s*"UNKNOWN"\)/);
  assert.match(source, /sampler\.addProperty\("status",\s*"UNKNOWN"\)/);
  assert.match(source, /out\.addProperty\("fogMode",\s*"UNKNOWN"\)/);
  assert.match(source, /out\.addProperty\("fogMode", profile\.fogMode\(\)\)/);
  assert.match(source, /out\.add\("replay", replayJson\(profile\.replay\(\)\)\)/);
  assert.match(source, /"dualDirectionalDiffuse", 0\.6F, 0\.4F, 1\.0F/);
  assert.match(source, /"modelViewInverseViewRotationShape"/);
  assert.match(source, /"modelViewLength"/);
  assert.match(source, /"sample0TimesVertexTimesShaderColor"/);
  assert.match(source, /"rgbMixByOverlayAlpha"/);
  assert.match(source, /"multiplyRgba"/);
  assert.match(source, /"minecraft:eyes_1_20_1", eyes,[\s\S]{0,160}"rgbaFade", null\)/);
  assert.match(source, /"colorMixPreserveAlpha"/);
  assert.match(source, /"rgbaFade"/);
});