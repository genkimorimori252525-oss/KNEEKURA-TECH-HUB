import { constants } from 'node:fs';
import { mkdir, lstat, open, realpath } from 'node:fs/promises';
import path from 'node:path';
import { sha256, stableJson, hashId } from '../bridge/json.mjs';
import { readRegisteredFile } from '../bridge/materials.mjs';

export function derivedArtifact(bytes, { role, mediaType, extension, sourceObservationIds, rawSourceHashes, binding, details = {} }) {
  if (!Buffer.isBuffer(bytes) || bytes.length > 32 * 1024 * 1024) throw new TypeError('DERIVED_ARTIFACT_SIZE_LIMIT');
  if (!['png','svg','json','html'].includes(extension)) throw new TypeError('INVALID_ARTIFACT_EXTENSION');
  const hash = sha256(bytes);
  const body = { schemaVersion: 1, role, mediaType, derived: true, sha256: hash, bytes: bytes.length,
    path: `evidence/derived/visual/${hash}.${extension}`, sourceObservationIds: [...sourceObservationIds],
    rawSourceHashes: [...rawSourceHashes], binding: structuredClone(binding), details: structuredClone(details) };
  return { ref: { artifactId: sha256(stableJson(body)), ...body }, bytes };
}

/** Derived files share the existing run tree; they are not another evidence database. */
export async function persistDerivedArtifacts(store, artifacts) {
  await store.assertMutable();
  const root = store.runDir;
  if (!path.isAbsolute(root) || await realpath(root) !== path.resolve(root)) throw new TypeError('UNSAFE_RUN_DIR');
  let directory = root;
  for (const part of ['evidence','derived','visual']) {
    directory = path.join(directory, part);
    try { await mkdir(directory); } catch (error) { if (error.code !== 'EEXIST') throw error; }
    const stat = await lstat(directory);
    if (stat.isSymbolicLink()) throw new TypeError('SYMLINK_REJECTED');
    if (!stat.isDirectory()) throw new TypeError('NOT_DIRECTORY');
  }
  for (const {ref,bytes} of artifacts) {
    const {artifactId,...body} = ref; hashId(artifactId); hashId(ref.sha256);
    if (sha256(stableJson(body)) !== artifactId || sha256(bytes) !== ref.sha256 || bytes.length !== ref.bytes ||
        !new RegExp(`^evidence/derived/visual/${ref.sha256}\\.(png|svg|json|html)$`).test(ref.path))
      throw new TypeError('DERIVED_ARTIFACT_INTEGRITY');
    await store.assertMutable();
    let handle;
    try { handle = await open(path.join(root,ref.path), constants.O_CREAT | constants.O_EXCL | constants.O_WRONLY | (constants.O_NOFOLLOW ?? 0), 0o600); }
    catch (error) {
      if (error.code !== 'EEXIST') throw error;
      await readRegisteredFile({root,relativePath:ref.path,expectedSha256:ref.sha256,maxBytes:32*1024*1024});
      continue;
    }
    try { await handle.writeFile(bytes); await handle.sync(); } finally { await handle.close(); }
  }
  return artifacts.map(a => structuredClone(a.ref));
}
