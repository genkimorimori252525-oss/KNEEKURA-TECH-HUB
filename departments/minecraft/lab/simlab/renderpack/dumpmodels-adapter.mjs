import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { extname, join, resolve } from 'node:path';
import { compileRenderPack } from './compiler.mjs';

export class DumpModelsAdapterError extends Error {
  constructor(message) {
    super(message);
    this.name = 'DumpModelsAdapterError';
  }
}

function reqObject(v, label) {
  if (v === null || typeof v !== 'object' || Array.isArray(v)) throw new DumpModelsAdapterError(`${label} must be an object`);
  return v;
}

function reqString(v, label) {
  if (typeof v !== 'string' || v.length === 0) throw new DumpModelsAdapterError(`${label} must be a non-empty string`);
  return v;
}

function safeExt(value) {
  const ext = String(value || '').toLowerCase();
  return /^\.[a-z0-9]{1,8}$/.test(ext) ? ext : '.bin';
}

function selectPose(dump, requestedPose) {
  const groups = reqObject(dump.renderGroups, 'dump.renderGroups');
  if (requestedPose) {
    if (!Array.isArray(groups[requestedPose])) throw new DumpModelsAdapterError(`requested pose '${requestedPose}' has no renderGroups`);
    return requestedPose;
  }
  if (Array.isArray(groups.idle)) return 'idle';
  const first = Object.keys(groups).find((name) => Array.isArray(groups[name]) && groups[name].length > 0);
  if (!first) throw new DumpModelsAdapterError('dump has no non-empty renderGroups pose');
  return first;
}

export async function compileDumpModelToRenderPack({
  dump,
  outputRoot,
  textureResolver,
  source,
  bones = null,
  pose = null,
}) {
  reqObject(dump, 'dump');
  if (dump.renderGroupsVersion !== 1) throw new DumpModelsAdapterError('dump.renderGroupsVersion must be 1');
  reqString(dump.type, 'dump.type');
  reqString(outputRoot, 'outputRoot');
  if (typeof textureResolver !== 'function') throw new DumpModelsAdapterError('textureResolver function is required');
  source = reqObject(source, 'source');
  for (const key of ['adapter', 'classification', 'modVersion', 'modJarHash', 'modelResourceHash']) reqString(source[key], `source.${key}`);
  if (bones === null) {
    bones = Array.isArray(dump.skeleton?.bones) ? structuredClone(dump.skeleton.bones) : [];
  }
  if (!Array.isArray(bones)) throw new DumpModelsAdapterError('bones must be an array when supplied');

  const selectedPose = selectPose(dump, pose);
  const poseGroups = dump.renderGroups[selectedPose];
  const resolvedOutputRoot = resolve(outputRoot);
  await mkdir(resolvedOutputRoot, { recursive: true });
  const tempParent = await mkdtemp(join(resolvedOutputRoot, '.kneekura-dump-adapter-'));
  const captureRoot = join(tempParent, 'capture');
  await mkdir(join(captureRoot, 'textures'), { recursive: true });

  try {
    const groups = [];
    for (let i = 0; i < poseGroups.length; i++) {
      const g = reqObject(poseGroups[i], `dump.renderGroups.${selectedPose}[${i}]`);
      const sourceRenderType = reqString(g.sourceRenderType, `group[${i}].sourceRenderType`);
      if (!Array.isArray(g.vertices) || g.vertices.length === 0) throw new DumpModelsAdapterError(`group[${i}].vertices must be non-empty`);
      let texture = null;
      if (g.texture != null) {
        const id = reqString(g.texture, `group[${i}].texture`);
        const resolved = await textureResolver(id);
        if (!resolved || !Buffer.isBuffer(resolved.bytes)) {
          throw new DumpModelsAdapterError(`textureResolver did not return Buffer bytes for ${id}`);
        }
        const ext = safeExt(resolved.extension || extname(id));
        const rel = `textures/group-${String(i).padStart(4, '0')}${ext}`;
        await writeFile(join(captureRoot, rel), resolved.bytes);
        texture = { sourcePath: rel, sourceResourceId: id };
      }
      const material = g.material == null
        ? null
        : structuredClone(reqObject(g.material, `group[${i}].material`));
      groups.push({
        groupId: reqString(g.groupId, `group[${i}].groupId`),
        order: Number.isSafeInteger(g.order) ? g.order : i,
        materialId: `material-${String(i).padStart(4, '0')}`,
        sourceRenderType,
        texture,
        material,
        vertices: g.vertices,
      });
    }

    const capture = {
      schema: 'kneekura.static-render-capture',
      schemaVersion: '1.0.0',
      modelId: dump.type,
      coordinateSystem: 'KNEEKURA_RH_Y_UP_BLOCK',
      vertexStrideFloats: 11,
      topology: 'expandedTriangles',
      source: {
        ...source,
        selectedPose,
        sourceDumpFormat: 'tlmsim.dumpmodels.renderGroups/v1',
        skeletonAuthority: bones.length > 0 ? 'adapter-provided' : 'UNKNOWN',
      },
      bones,
      groups,
    };
    const result = await compileRenderPack({ capture, captureRoot, outputRoot: resolvedOutputRoot });
    return { ...result, selectedPose };
  } finally {
    await rm(tempParent, { recursive: true, force: true });
  }
}