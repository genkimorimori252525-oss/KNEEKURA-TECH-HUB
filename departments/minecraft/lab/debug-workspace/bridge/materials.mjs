import { constants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { exactKeys, hashId, integer } from './json.mjs';

async function resolveRegisteredFile(root, relativePath) {
  if (typeof root !== 'string' || !path.isAbsolute(root) ||
      await realpath(root) !== path.resolve(root)) {
    throw new TypeError('UNSAFE_ROOT');
  }
  if (typeof relativePath !== 'string' || !relativePath ||
      relativePath.includes('\\') || relativePath.includes(':') ||
      relativePath.includes('\0') || path.isAbsolute(relativePath) ||
      relativePath.split('/').some(component => !component || component === '.' || component === '..')) {
    throw new TypeError('UNSAFE_RELATIVE_PATH');
  }
  let fullPath = path.resolve(root);
  for (const component of relativePath.split('/')) {
    fullPath = path.join(fullPath, component);
    if ((await lstat(fullPath)).isSymbolicLink()) throw new TypeError('SYMLINK_REJECTED');
  }
  if (await realpath(fullPath) !== fullPath) throw new TypeError('PATH_ESCAPE');
  if (!(await lstat(fullPath)).isFile()) throw new TypeError('NOT_REGULAR_FILE');
  return fullPath;
}

export async function readRegisteredFile({
  root, relativePath, expectedSha256, maxBytes, retainBytes = true,
}) {
  integer(maxBytes, 1, 64 * 1024 * 1024, 'FILE_LIMIT');
  if (expectedSha256 != null) hashId(expectedSha256);
  const fullPath = await resolveRegisteredFile(root, relativePath);
  const handle = await open(fullPath, constants.O_RDONLY | (constants.O_NOFOLLOW ?? 0) | (constants.O_NONBLOCK ?? 0));
  try {
    const before = await handle.stat({ bigint: true });
    if (!before.isFile()) throw new TypeError('NOT_REGULAR_FILE');
    if (before.size > BigInt(maxBytes)) throw new TypeError('FILE_SIZE_LIMIT');
    const digest = createHash('sha256');
    const chunks = [];
    let size = 0;
    const buffer = Buffer.alloc(65536);
    while (true) {
      const { bytesRead } = await handle.read(buffer, 0, buffer.length, null);
      if (!bytesRead) break;
      size += bytesRead;
      if (size > maxBytes) throw new TypeError('FILE_SIZE_LIMIT');
      const bytes = buffer.subarray(0, bytesRead);
      digest.update(bytes);
      if (retainBytes) chunks.push(Buffer.from(bytes));
    }
    const after = await handle.stat({ bigint: true });
    const named = await lstat(fullPath, { bigint: true });
    if (named.isSymbolicLink() || before.ino !== after.ino || before.dev !== after.dev ||
        before.size !== after.size || before.mtimeNs !== after.mtimeNs ||
        named.ino !== after.ino || named.dev !== after.dev || await realpath(fullPath) !== fullPath) {
      throw new Error('FILE_CHANGED_DURING_READ');
    }
    const hash = digest.digest('hex');
    if (expectedSha256 != null && hash !== expectedSha256) throw new Error('MATERIAL_HASH_MISMATCH');
    return {
      relativePath, sizeBytes: size, sha256: hash,
      ...(retainBytes ? { bytes: Buffer.concat(chunks) } : {}),
    };
  } finally {
    await handle.close();
  }
}

export async function verifyBridgeMaterials(registration, binding) {
  exactKeys(registration.materials, ['buildArtifact', 'configArtifact', 'resourceArtifact'], 'MATERIALS');
  const fields = {
    buildArtifact: ['build_artifact_hash', 64 * 1024 * 1024],
    configArtifact: ['config_hash', 1024 * 1024],
    resourceArtifact: ['resource_hash', 16 * 1024 * 1024],
  };
  const inventory = {};
  for (const [key, [field, maxBytes]] of Object.entries(fields)) {
    exactKeys(registration.materials[key], ['relativePath'], 'MATERIAL');
    inventory[key] = await readRegisteredFile({
      root: registration.trustedRoot,
      relativePath: registration.materials[key].relativePath,
      expectedSha256: binding.target[field], maxBytes, retainBytes: false,
    });
  }
  return inventory;
}
