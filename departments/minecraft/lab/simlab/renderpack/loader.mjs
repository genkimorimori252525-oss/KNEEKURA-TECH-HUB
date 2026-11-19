import { createHash } from 'node:crypto';
import { lstat, readFile, realpath } from 'node:fs/promises';
import { isAbsolute, resolve, sep } from 'node:path';
import {
  assertMaterialsIR,
  assertRenderMeshIR,
  assertRenderPackManifest,
} from '../contracts/render-v1/validator.mjs';

export class RenderPackLoadError extends Error {
  constructor(message) {
    super(message);
    this.name = 'RenderPackLoadError';
  }
}

function sha256(bytes) {
  return `sha256:${createHash('sha256').update(bytes).digest('hex')}`;
}

function inside(root, relative) {
  if (typeof relative !== 'string' || relative.length === 0) throw new RenderPackLoadError('invalid pack-relative path');
  if (isAbsolute(relative) || /^[A-Za-z]:[\\/]/.test(relative)) throw new RenderPackLoadError(`absolute pack path forbidden: ${relative}`);
  const clean = relative.replaceAll('\\', '/');
  const parts = clean.split('/');
  if (parts.includes('..') || parts.includes('.') || parts.includes('')) throw new RenderPackLoadError(`unsafe pack path: ${relative}`);
  const absRoot = resolve(root);
  const abs = resolve(absRoot, clean);
  if (abs !== absRoot && !abs.startsWith(absRoot + sep)) throw new RenderPackLoadError(`pack path escapes root: ${relative}`);
  return abs;
}

async function readRegularInside(root, relative) {
  const path = inside(root, relative);
  const info = await lstat(path);
  if (info.isSymbolicLink()) throw new RenderPackLoadError(`symbolic links are forbidden in Render Packs: ${relative}`);
  const rootReal = await realpath(root);
  const fileReal = await realpath(path);
  if (fileReal !== rootReal && !fileReal.startsWith(rootReal + sep)) {
    throw new RenderPackLoadError(`pack file resolves outside root: ${relative}`);
  }
  return readFile(fileReal);
}

async function json(root, relative) {
  return JSON.parse((await readRegularInside(root, relative)).toString('utf8'));
}

export async function loadRenderPack(packDir) {
  const root = await realpath(resolve(packDir));
  const manifest = await json(root, 'manifest.json');
  assertRenderPackManifest(manifest);

  const listed = new Map();
  for (const file of manifest.files) {
    if (listed.has(file.path)) throw new RenderPackLoadError(`duplicate manifest file: ${file.path}`);
    const bytes = await readRegularInside(root, file.path);
    const actual = sha256(bytes);
    if (actual !== file.sha256) throw new RenderPackLoadError(`hash mismatch for ${file.path}: expected ${file.sha256}, got ${actual}`);
    listed.set(file.path, bytes);
  }

  for (const required of ['mesh/mesh.json', 'mesh/mesh.bin', 'mesh/groups.json', 'mesh/skeleton.json', 'materials/materials.json']) {
    if (!listed.has(required)) throw new RenderPackLoadError(`manifest missing required pack file: ${required}`);
  }

  const mesh = JSON.parse(listed.get('mesh/mesh.json').toString('utf8'));
  const materials = JSON.parse(listed.get('materials/materials.json').toString('utf8'));
  const groups = JSON.parse(listed.get('mesh/groups.json').toString('utf8'));
  const skeleton = JSON.parse(listed.get('mesh/skeleton.json').toString('utf8'));
  assertRenderMeshIR(mesh);
  assertMaterialsIR(materials);

  if (mesh.modelId !== manifest.modelId || groups.modelId !== manifest.modelId || skeleton.modelId !== manifest.modelId) {
    throw new RenderPackLoadError('modelId mismatch inside Render Pack');
  }
  if (mesh.layoutHash !== manifest.layoutHash || groups.layoutHash !== manifest.layoutHash || skeleton.layoutHash !== manifest.layoutHash) {
    throw new RenderPackLoadError('layoutHash mismatch inside Render Pack');
  }
  const materialIds = new Set(materials.materials.map((m) => m.materialId));
  for (const group of mesh.drawGroups) {
    if (!materialIds.has(group.materialId)) throw new RenderPackLoadError(`draw group ${group.groupId} references missing material ${group.materialId}`);
  }
  for (const material of materials.materials) {
    for (const key of ['baseTexture', 'normalTexture', 'emissiveTexture']) {
      const rel = material[key];
      if (rel != null && !listed.has(rel)) throw new RenderPackLoadError(`material ${material.materialId} references unlisted texture ${rel}`);
    }
  }

  return { root, manifest, mesh, materials, groups, skeleton, meshBytes: listed.get('mesh/mesh.bin') };
}