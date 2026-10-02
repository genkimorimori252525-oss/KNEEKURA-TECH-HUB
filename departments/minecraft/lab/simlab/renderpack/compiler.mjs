import { createHash } from 'node:crypto';
import { lstat, mkdir, mkdtemp, readFile, realpath, rename, rm, writeFile } from 'node:fs/promises';
import { dirname, extname, isAbsolute, join, resolve, sep } from 'node:path';
import {
  COORDINATE_SYSTEM,
  MATERIALS_SCHEMA,
  RENDER_MESH_SCHEMA,
  RENDER_PACK_SCHEMA,
  SCHEMA_VERSION,
} from '../contracts/render-v1/constants.mjs';
import {
  assertMaterialsIR,
  assertRenderMeshIR,
  assertRenderPackManifest,
  computePackHash,
} from '../contracts/render-v1/validator.mjs';
import { loadRenderPack } from './loader.mjs';

export const STATIC_CAPTURE_SCHEMA = 'kneekura.static-render-capture';
export const COMPILER_NAME = 'kneekura-renderpack-compiler';
export const COMPILER_VERSION = '0.1.0';
const HASH_RE = /^sha256:[0-9a-f]{64}$/;
const STRIDE_FLOATS = 11;
const STRIDE_BYTES = STRIDE_FLOATS * 4;

export class RenderPackCompileError extends Error {
  constructor(message, path = '$') {
    super(`${path}: ${message}`);
    this.name = 'RenderPackCompileError';
    this.path = path;
  }
}

function fail(message, path) {
  throw new RenderPackCompileError(message, path);
}

function isObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v);
}

function reqObject(v, path) {
  if (!isObject(v)) fail('expected object', path);
  return v;
}

function reqString(v, path) {
  if (typeof v !== 'string' || v.length === 0) fail('expected non-empty string', path);
  return v;
}

function reqArray(v, path) {
  if (!Array.isArray(v)) fail('expected array', path);
  return v;
}

function reqInteger(v, path, min = 0) {
  if (!Number.isSafeInteger(v) || v < min) fail(`expected safe integer >= ${min}`, path);
  return v;
}

function reqFinite(v, path) {
  if (typeof v !== 'number' || !Number.isFinite(v)) fail('expected finite number', path);
  return v;
}

function reqHash(v, path) {
  if (!HASH_RE.test(reqString(v, path))) fail('expected sha256:<64 lowercase hex>', path);
  return v;
}

function sha256(bytes) {
  return `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
}

function canonicalize(value) {
  if (Array.isArray(value)) return value.map(canonicalize);
  if (!isObject(value)) return value;
  const out = {};
  for (const key of Object.keys(value).sort()) out[key] = canonicalize(value[key]);
  return out;
}

function canonicalHash(value) {
  return sha256(Buffer.from(JSON.stringify(canonicalize(value)), 'utf8'));
}

export function assertRelativePath(path, at = '$') {
  reqString(path, at);
  if (isAbsolute(path) || /^[A-Za-z]:[\\/]/.test(path)) fail('absolute path is forbidden', at);
  const normalized = path.replaceAll('\\', '/');
  const parts = normalized.split('/');
  if (parts.includes('..')) fail('path traversal is forbidden', at);
  if (parts.includes('')) fail('empty path segment is forbidden', at);
  if (parts.includes('.')) fail('dot path segment is forbidden', at);
  return normalized;
}

function resolveInside(root, relativePath, at) {
  const clean = assertRelativePath(relativePath, at);
  const absRoot = resolve(root);
  const abs = resolve(absRoot, clean);
  if (abs !== absRoot && !abs.startsWith(absRoot + sep)) fail('path escapes root', at);
  return abs;
}

function safeModelDirectory(modelId) {
  return modelId.replace(/[^A-Za-z0-9._-]+/g, '_').replace(/^_+|_+$/g, '') || 'model';
}

function normalizeTextureExtension(sourcePath) {
  const ext = extname(sourcePath).toLowerCase();
  return /^\.[a-z0-9]{1,8}$/.test(ext) ? ext : '.bin';
}

function defaultUnknownMaterial(materialId, texturePath, sourceRenderType, sourceTextureResourceId = null) {
  return {
    materialId,
    baseTexture: texturePath,
    normalTexture: null,
    emissiveTexture: null,
    alphaMode: 'UNKNOWN',
    blend: {
      enabled: 'UNKNOWN',
      equation: 'UNKNOWN',
      srcFactor: 'UNKNOWN',
      dstFactor: 'UNKNOWN',
    },
    cullMode: 'UNKNOWN',
    depth: {
      testFunction: 'UNKNOWN',
      write: 'UNKNOWN',
    },
    emissive: 'UNKNOWN',
    fullbright: 'UNKNOWN',
    fogMode: 'UNKNOWN',
    sampler: { status: 'UNKNOWN' },
    vertexTint: 'UNKNOWN',
    lightmap: 'UNKNOWN',
    overlay: 'UNKNOWN',
    replay: { status: 'UNKNOWN' },
    sourceRenderType,
    sourceTextureResourceId,
    captureStatus: 'provenance-only',
  };
}

function validateMatrixOrUnknown(value, authority, path) {
  if (value === null) {
    if (authority !== 'UNKNOWN') fail("null matrix requires authority 'UNKNOWN'", `${path}Authority`);
    return;
  }
  const a = reqArray(value, path);
  if (a.length !== 16) fail('expected 16 values', path);
  a.forEach((x, i) => reqFinite(x, `${path}[${i}]`));
}

function validateCapture(capture) {
  reqObject(capture, '$');
  if (capture.schema !== STATIC_CAPTURE_SCHEMA) fail(`expected ${STATIC_CAPTURE_SCHEMA}`, '$.schema');
  if (capture.schemaVersion !== SCHEMA_VERSION) fail(`expected schemaVersion ${SCHEMA_VERSION}`, '$.schemaVersion');
  reqString(capture.modelId, '$.modelId');
  if (capture.coordinateSystem !== COORDINATE_SYSTEM) fail(`expected ${COORDINATE_SYSTEM}`, '$.coordinateSystem');
  if (capture.vertexStrideFloats !== STRIDE_FLOATS) fail(`expected SimVertexRecorder stride ${STRIDE_FLOATS}`, '$.vertexStrideFloats');
  if (capture.topology !== 'expandedTriangles') fail("expected topology 'expandedTriangles'", '$.topology');

  const source = reqObject(capture.source, '$.source');
  reqString(source.adapter, '$.source.adapter');
  reqString(source.classification, '$.source.classification');
  reqString(source.modVersion, '$.source.modVersion');
  reqHash(source.modJarHash, '$.source.modJarHash');
  reqHash(source.modelResourceHash, '$.source.modelResourceHash');

  const bones = reqArray(capture.bones ?? [], '$.bones');
  bones.forEach((b, i) => {
    const p = `$.bones[${i}]`;
    reqObject(b, p);
    if (b.slot !== i) fail('bone slot must equal array index', `${p}.slot`);
    reqString(b.name, `${p}.name`);
    if (b.parentSlot !== null) {
      reqInteger(b.parentSlot, `${p}.parentSlot`, 0);
      if (b.parentSlot >= i) fail('parentSlot must reference an earlier stable slot', `${p}.parentSlot`);
    }
    validateMatrixOrUnknown(b.bindMatrix, b.bindMatrixAuthority, `${p}.bindMatrix`);
    validateMatrixOrUnknown(b.inverseBindMatrix, b.inverseBindMatrixAuthority, `${p}.inverseBindMatrix`);
  });

  const groups = reqArray(capture.groups, '$.groups');
  if (groups.length === 0) fail('at least one draw group is required', '$.groups');
  const ids = new Set();
  const orders = new Set();
  groups.forEach((g, i) => {
    const p = `$.groups[${i}]`;
    reqObject(g, p);
    const id = reqString(g.groupId, `${p}.groupId`);
    if (ids.has(id)) fail('duplicate groupId', `${p}.groupId`);
    ids.add(id);
    const order = reqInteger(g.order, `${p}.order`, 0);
    if (orders.has(order)) fail('duplicate draw order', `${p}.order`);
    orders.add(order);
    reqString(g.materialId, `${p}.materialId`);
    reqString(g.sourceRenderType, `${p}.sourceRenderType`);
    const vertices = reqArray(g.vertices, `${p}.vertices`);
    if (vertices.length === 0 || vertices.length % STRIDE_FLOATS !== 0) {
      fail(`vertices length must be a non-zero multiple of ${STRIDE_FLOATS}`, `${p}.vertices`);
    }
    vertices.forEach((x, n) => reqFinite(x, `${p}.vertices[${n}]`));
    const vertexCount = vertices.length / STRIDE_FLOATS;
    const indices = g.indices == null ? null : reqArray(g.indices, `${p}.indices`);
    if (indices) {
      if (indices.length === 0 || indices.length % 3 !== 0) fail('indices must contain triangles', `${p}.indices`);
      indices.forEach((x, n) => {
        reqInteger(x, `${p}.indices[${n}]`, 0);
        if (x >= vertexCount) fail(`index ${x} exceeds group vertexCount ${vertexCount}`, `${p}.indices[${n}]`);
      });
    } else if (vertexCount % 3 !== 0) {
      fail('expandedTriangles without explicit indices requires vertexCount divisible by 3', p);
    }
    if (g.texture !== null && g.texture !== undefined) {
      const t = reqObject(g.texture, `${p}.texture`);
      assertRelativePath(t.sourcePath, `${p}.texture.sourcePath`);
    }
  });
  return capture;
}

async function copyTexture(captureRoot, tempPackDir, texture, textureCache, at) {
  if (!texture) return null;
  const sourcePath = assertRelativePath(texture.sourcePath, `${at}.sourcePath`);
  const sourceAbs = resolveInside(captureRoot, sourcePath, `${at}.sourcePath`);
  let bytes;
  try {
    const rootReal = await realpath(captureRoot);
    const sourceInfo = await lstat(sourceAbs);
    if (sourceInfo.isSymbolicLink()) fail('symbolic-link texture sources are forbidden', `${at}.sourcePath`);
    const sourceReal = await realpath(sourceAbs);
    if (sourceReal !== rootReal && !sourceReal.startsWith(rootReal + sep)) {
      fail('texture source resolves outside capture root', `${at}.sourcePath`);
    }
    bytes = await readFile(sourceReal);
  } catch (error) {
    if (error instanceof RenderPackCompileError) throw error;
    fail(`failed to read texture '${sourcePath}': ${error.message}`, at);
  }
  const digest = sha256(bytes);
  const previous = textureCache.get(digest);
  if (previous) return previous;
  const ext = normalizeTextureExtension(sourcePath);
  const rel = `textures/${digest.slice('sha256:'.length)}${ext}`;
  await mkdir(dirname(resolveInside(tempPackDir, rel, `${at}.output`)), { recursive: true });
  await writeFile(resolveInside(tempPackDir, rel, `${at}.output`), bytes);
  textureCache.set(digest, rel);
  return rel;
}

function encodeMesh(groups) {
  let vertexCount = 0;
  let indexCount = 0;
  for (const g of groups) {
    vertexCount += g.vertices.length / STRIDE_FLOATS;
    indexCount += g.indices ? g.indices.length : g.vertices.length / STRIDE_FLOATS;
  }
  const vertexBytes = vertexCount * STRIDE_BYTES;
  const indexOffset = (vertexBytes + 3) & ~3;
  const totalBytes = indexOffset + indexCount * 4;
  const out = Buffer.alloc(totalBytes);
  let vertexBase = 0;
  let vertexFloatOffset = 0;
  let indexElementOffset = 0;
  const drawGroups = [];

  for (const g of groups) {
    for (const value of g.vertices) {
      out.writeFloatLE(value, vertexFloatOffset * 4);
      vertexFloatOffset++;
    }
    const localVertexCount = g.vertices.length / STRIDE_FLOATS;
    const localIndices = g.indices ?? Array.from({ length: localVertexCount }, (_, i) => i);
    for (let i = 0; i < localIndices.length; i++) {
      out.writeUInt32LE(vertexBase + localIndices[i], indexOffset + (indexElementOffset + i) * 4);
    }
    drawGroups.push({
      groupId: g.groupId,
      indexStart: indexElementOffset,
      indexCount: localIndices.length,
      materialId: g.materialId,
      order: g.order,
      sourceRenderType: g.sourceRenderType,
      sourceVertexStart: vertexBase,
      sourceVertexCount: localVertexCount,
    });
    vertexBase += localVertexCount;
    indexElementOffset += localIndices.length;
  }
  return { buffer: out, vertexCount, indexCount, indexOffset, drawGroups };
}

async function writeJson(path, value) {
  const bytes = Buffer.from(JSON.stringify(value, null, 2) + '\n', 'utf8');
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, bytes);
  return bytes;
}

export async function compileRenderPack({ capture, captureRoot, outputRoot }) {
  validateCapture(capture);
  reqString(captureRoot, '$compile.captureRoot');
  reqString(outputRoot, '$compile.outputRoot');
  const orderedGroups = [...capture.groups].sort((a, b) => a.order - b.order);
  const textureCache = new Map();
  const resolvedOutputRoot = resolve(outputRoot);
  await mkdir(resolvedOutputRoot, { recursive: true });
  const tempParent = await mkdtemp(join(resolvedOutputRoot, '.kneekura-renderpack-'));
  const tempPackDir = join(tempParent, 'pack');
  await mkdir(tempPackDir, { recursive: true });

  try {
    const compiledGroups = [];
    const materials = [];
    const materialIds = new Set();
    for (let i = 0; i < orderedGroups.length; i++) {
      const g = orderedGroups[i];
      const texturePath = await copyTexture(captureRoot, tempPackDir, g.texture, textureCache, `$.groups[${i}].texture`);
      compiledGroups.push({ ...g, texturePath });
      if (materialIds.has(g.materialId)) fail('materialId must be unique per captured draw group in PR-A', `$.groups[${i}].materialId`);
      materialIds.add(g.materialId);
      const explicit = g.material ?? null;
      if (explicit) {
        materials.push({
          ...defaultUnknownMaterial(
            g.materialId,
            texturePath,
            g.sourceRenderType,
            g.texture?.sourceResourceId ?? null,
          ),
          ...structuredClone(explicit),
          materialId: g.materialId,
          baseTexture: texturePath,
          sourceRenderType: g.sourceRenderType,
          sourceTextureResourceId: g.texture?.sourceResourceId ?? null,
        });
      } else {
        materials.push(defaultUnknownMaterial(
          g.materialId,
          texturePath,
          g.sourceRenderType,
          g.texture?.sourceResourceId ?? null,
        ));
      }
    }

    const encoded = encodeMesh(compiledGroups);
    const meshBinPath = join(tempPackDir, 'mesh', 'mesh.bin');
    await mkdir(dirname(meshBinPath), { recursive: true });
    await writeFile(meshBinPath, encoded.buffer);
    const meshSha = sha256(encoded.buffer);

    const bones = (capture.bones ?? []).map((b) => structuredClone(b));
    const layoutIdentity = {
      modelId: capture.modelId,
      coordinateSystem: capture.coordinateSystem,
      vertexStrideFloats: STRIDE_FLOATS,
      topology: capture.topology,
      meshSha256: meshSha,
      vertexCount: encoded.vertexCount,
      indexCount: encoded.indexCount,
      bones,
      drawGroups: encoded.drawGroups.map((g) => ({
        groupId: g.groupId,
        indexStart: g.indexStart,
        indexCount: g.indexCount,
        materialId: g.materialId,
        order: g.order,
        sourceRenderType: g.sourceRenderType,
      })),
    };
    const layoutHash = canonicalHash(layoutIdentity);

    const mesh = {
      schema: RENDER_MESH_SCHEMA,
      schemaVersion: SCHEMA_VERSION,
      modelId: capture.modelId,
      layoutHash,
      topology: 'triangles',
      vertexCount: encoded.vertexCount,
      buffers: [{ id: 'mesh', path: 'mesh/mesh.bin', byteLength: encoded.buffer.length, sha256: meshSha }],
      attributes: {
        position: { buffer: 'mesh', componentType: 'float32', byteOffset: 0, byteStride: STRIDE_BYTES, components: 3 },
        uv0: { buffer: 'mesh', componentType: 'float32', byteOffset: 12, byteStride: STRIDE_BYTES, components: 2 },
        normal: { buffer: 'mesh', componentType: 'float32', byteOffset: 20, byteStride: STRIDE_BYTES, components: 3 },
        color0: { buffer: 'mesh', componentType: 'float32', byteOffset: 32, byteStride: STRIDE_BYTES, components: 3 },
        joints: { availability: 'UNKNOWN', reason: 'SimVertexRecorder does not expose source skin joints' },
        weights: { availability: 'UNKNOWN', reason: 'SimVertexRecorder does not expose source skin weights' },
      },
      indexAccessor: {
        buffer: 'mesh',
        componentType: 'uint32',
        byteOffset: encoded.indexOffset,
        count: encoded.indexCount,
      },
      bones,
      drawGroups: encoded.drawGroups,
      source: {
        classification: capture.source.classification,
        adapter: capture.source.adapter,
      },
    };

    const groupsDoc = {
      schema: 'kneekura.drawgroups',
      schemaVersion: SCHEMA_VERSION,
      modelId: capture.modelId,
      layoutHash,
      groups: encoded.drawGroups.map((g, i) => ({
        ...g,
        baseTexture: compiledGroups[i].texturePath,
      })),
    };

    const skeletonDoc = {
      schema: 'kneekura.skeleton',
      schemaVersion: SCHEMA_VERSION,
      modelId: capture.modelId,
      layoutHash,
      bones,
    };

    const materialsDoc = {
      schema: MATERIALS_SCHEMA,
      schemaVersion: SCHEMA_VERSION,
      materials,
    };
    assertRenderMeshIR(mesh);
    assertMaterialsIR(materialsDoc);

    const fileBytes = new Map();
    fileBytes.set('mesh/mesh.bin', encoded.buffer);
    fileBytes.set('mesh/mesh.json', await writeJson(join(tempPackDir, 'mesh', 'mesh.json'), mesh));
    fileBytes.set('mesh/groups.json', await writeJson(join(tempPackDir, 'mesh', 'groups.json'), groupsDoc));
    fileBytes.set('mesh/skeleton.json', await writeJson(join(tempPackDir, 'mesh', 'skeleton.json'), skeletonDoc));
    fileBytes.set('materials/materials.json', await writeJson(join(tempPackDir, 'materials', 'materials.json'), materialsDoc));
    for (const rel of textureCache.values()) {
      fileBytes.set(rel, await readFile(resolveInside(tempPackDir, rel, '$.textureOutput')));
    }

    const manifest = {
      schema: RENDER_PACK_SCHEMA,
      schemaVersion: SCHEMA_VERSION,
      modelId: capture.modelId,
      packHash: 'sha256:' + '0'.repeat(64),
      layoutHash,
      compiler: { name: COMPILER_NAME, version: COMPILER_VERSION },
      source: {
        adapter: capture.source.adapter,
        classification: capture.source.classification,
        modVersion: capture.source.modVersion,
        modJarHash: capture.source.modJarHash,
        modelResourceHash: capture.source.modelResourceHash,
      },
      coordinateSystem: capture.coordinateSystem,
      files: [...fileBytes.entries()]
        .map(([path, bytes]) => ({ path, sha256: sha256(bytes) }))
        .sort((a, b) => a.path.localeCompare(b.path)),
    };
    manifest.packHash = computePackHash(manifest);
    assertRenderPackManifest(manifest);
    await writeJson(join(tempPackDir, 'manifest.json'), manifest);

    const modelDir = join(resolvedOutputRoot, safeModelDirectory(capture.modelId));
    await mkdir(modelDir, { recursive: true });
    const finalDir = join(modelDir, manifest.packHash.slice('sha256:'.length));
    try {
      await rename(tempPackDir, finalDir);
    } catch (error) {
      if (error?.code !== 'EEXIST' && error?.code !== 'ENOTEMPTY') throw error;
      await rm(tempPackDir, { recursive: true, force: true });
      try {
        const existing = await loadRenderPack(finalDir);
        if (existing.manifest.packHash !== manifest.packHash) {
          fail('existing deterministic pack directory has a different manifest identity', '$compile.outputRoot');
        }
      } catch (verifyError) {
        if (verifyError instanceof RenderPackCompileError) throw verifyError;
        fail(`existing deterministic pack is invalid: ${verifyError.message}`, '$compile.outputRoot');
      }
    }
    return { packDir: finalDir, manifest, mesh, materials: materialsDoc };
  } finally {
    await rm(tempParent, { recursive: true, force: true });
  }
}