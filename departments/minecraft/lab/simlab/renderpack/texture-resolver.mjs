import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

export class TextureResolveError extends Error {
  constructor(message) {
    super(message);
    this.name = 'TextureResolveError';
  }
}

function safeResourceId(id) {
  if (typeof id !== 'string' || id.length === 0) throw new TextureResolveError('texture id must be non-empty');
  const colon = id.indexOf(':');
  const namespace = colon < 0 ? 'minecraft' : id.slice(0, colon);
  const relative = colon < 0 ? id : id.slice(colon + 1);
  if (!/^[a-z0-9_.-]+$/.test(namespace)) throw new TextureResolveError(`invalid texture namespace: ${namespace}`);
  if (relative.startsWith('/') || /^[A-Za-z]:[\\/]/.test(relative)) throw new TextureResolveError('absolute texture resource path is forbidden');
  const parts = relative.replaceAll('\\', '/').split('/');
  if (parts.includes('..') || parts.includes('.') || parts.includes('')) throw new TextureResolveError('unsafe texture resource path');
  return { namespace, relative: parts.join('/') };
}

class Zip {
  constructor(file) {
    this.buf = fs.readFileSync(file);
    this.index = new Map();
    this.#readCentralDirectory();
  }

  #readCentralDirectory() {
    const b = this.buf;
    let eocd = -1;
    for (let i = b.length - 22; i >= Math.max(0, b.length - 66000); i--) {
      if (b.readUInt32LE(i) === 0x06054b50) {
        eocd = i;
        break;
      }
    }
    if (eocd < 0) throw new TextureResolveError('client jar zip EOCD not found');
    const count = b.readUInt16LE(eocd + 10);
    let p = b.readUInt32LE(eocd + 16);
    for (let i = 0; i < count; i++) {
      if (p + 46 > b.length || b.readUInt32LE(p) !== 0x02014b50) {
        throw new TextureResolveError('invalid client jar central directory');
      }
      const method = b.readUInt16LE(p + 10);
      const csize = b.readUInt32LE(p + 20);
      const size = b.readUInt32LE(p + 24);
      const nameLen = b.readUInt16LE(p + 28);
      const extraLen = b.readUInt16LE(p + 30);
      const commentLen = b.readUInt16LE(p + 32);
      const local = b.readUInt32LE(p + 42);
      const nameEnd = p + 46 + nameLen;
      if (nameEnd > b.length) throw new TextureResolveError('invalid client jar entry name');
      const name = b.toString('utf8', p + 46, nameEnd);
      this.index.set(name, { method, csize, size, local });
      p = nameEnd + extraLen + commentLen;
    }
  }

  read(name) {
    const e = this.index.get(name);
    if (!e) return null;
    const b = this.buf;
    if (e.local + 30 > b.length || b.readUInt32LE(e.local) !== 0x04034b50) return null;
    const nameLen = b.readUInt16LE(e.local + 26);
    const extraLen = b.readUInt16LE(e.local + 28);
    const start = e.local + 30 + nameLen + extraLen;
    const end = start + e.csize;
    if (start < 0 || end > b.length) throw new TextureResolveError('client jar entry exceeds archive bounds');
    const raw = b.subarray(start, end);
    let out;
    if (e.method === 0) out = Buffer.from(raw);
    else if (e.method === 8) out = zlib.inflateRawSync(raw);
    else throw new TextureResolveError(`unsupported client jar compression method ${e.method}`);
    if (out.length !== e.size) throw new TextureResolveError(`client jar entry size mismatch for ${name}`);
    return out;
  }
}

function findClientJar(minecraftDir, version = '1.20.1') {
  if (!minecraftDir) return null;
  const dir = path.join(minecraftDir, 'versions');
  if (!fs.existsSync(dir)) return null;
  const exact = path.join(dir, version, `${version}.jar`);
  if (fs.existsSync(exact)) return exact;
  for (const name of fs.readdirSync(dir).sort()) {
    if (!name.startsWith(version)) continue;
    const file = path.join(dir, name, `${name}.jar`);
    if (fs.existsSync(file)) return file;
  }
  return null;
}

function discoverYsmPack(ysmCustomDir) {
  if (!ysmCustomDir || !fs.existsSync(ysmCustomDir)) return null;
  const found = [];
  for (const name of fs.readdirSync(ysmCustomDir).sort()) {
    const dir = path.join(ysmCustomDir, name);
    try {
      if (fs.statSync(dir).isDirectory() && fs.existsSync(path.join(dir, 'ysm.json'))) found.push(dir);
    } catch {
      // Ignore unreadable candidates; the final resolution remains fail-closed.
    }
  }
  if (found.length === 0) return null;
  if (found.length > 1) {
    throw new TextureResolveError('multiple YSM packs found; pass ysmPackDir explicitly instead of guessing');
  }
  return found[0];
}

function readRegularInside(root, file, label) {
  const rootReal = fs.realpathSync(root);
  const st = fs.lstatSync(file);
  if (st.isSymbolicLink()) throw new TextureResolveError(`symbolic-link ${label} is forbidden: ${file}`);
  if (!st.isFile()) throw new TextureResolveError(`${label} is not a regular file: ${file}`);
  const fileReal = fs.realpathSync(file);
  if (fileReal !== rootReal && !fileReal.startsWith(rootReal + path.sep)) {
    throw new TextureResolveError(`${label} resolves outside its configured root: ${file}`);
  }
  return fs.readFileSync(fileReal);
}

export function createCompileTextureResolver({
  modAssets,
  minecraftDir = null,
  ysmPackDir = null,
  ysmCustomDir = minecraftDir ? path.join(minecraftDir, 'config', 'yes_steve_model', 'custom') : null,
  vanillaVersion = '1.20.1',
} = {}) {
  if (!modAssets || !path.isAbsolute(modAssets)) {
    throw new TextureResolveError('modAssets must be an explicit absolute path');
  }
  let clientZip;
  let clientTried = false;
  let resolvedYsmPack = ysmPackDir;

  function vanillaZip() {
    if (!clientTried) {
      clientTried = true;
      const jar = findClientJar(minecraftDir, vanillaVersion);
      clientZip = jar ? new Zip(jar) : null;
    }
    return clientZip;
  }

  return function resolveTexture(id) {
    const { namespace, relative } = safeResourceId(id);

    if (namespace === 'ysm') {
      if (!resolvedYsmPack) resolvedYsmPack = discoverYsmPack(ysmCustomDir);
      if (!resolvedYsmPack) throw new TextureResolveError(`YSM texture cannot be resolved without a YSM pack: ${id}`);
      const file = path.join(resolvedYsmPack, ...relative.split('/'));
      if (!fs.existsSync(file)) throw new TextureResolveError(`YSM texture not found: ${id}`);
      return { bytes: readRegularInside(resolvedYsmPack, file, 'YSM texture'), extension: path.extname(file) || '.bin', source: file };
    }

    if (namespace !== 'minecraft') {
      const direct = path.join(modAssets, namespace, ...relative.split('/'));
      if (fs.existsSync(direct)) {
        return { bytes: readRegularInside(modAssets, direct, 'mod texture'), extension: path.extname(direct) || '.bin', source: direct };
      }
      const packs = path.join(modAssets, namespace, 'tlm_custom_pack');
      if (fs.existsSync(packs)) {
        const matches = [];
        for (const pack of fs.readdirSync(packs).sort()) {
          const nested = path.join(packs, pack, 'assets', namespace, ...relative.split('/'));
          if (fs.existsSync(nested)) matches.push(nested);
        }
        if (matches.length > 1) {
          throw new TextureResolveError(`multiple mod textures match ${id}; refusing first-match guessing`);
        }
        if (matches.length === 1) {
          return { bytes: readRegularInside(modAssets, matches[0], 'nested mod texture'), extension: path.extname(matches[0]) || '.bin', source: matches[0] };
        }
      }
      throw new TextureResolveError(`mod texture not found: ${id}`);
    }

    const override = path.join(modAssets, 'minecraft', ...relative.split('/'));
    if (fs.existsSync(override)) {
      return { bytes: readRegularInside(modAssets, override, 'minecraft override texture'), extension: path.extname(override) || '.bin', source: override };
    }
    const zip = vanillaZip();
    if (!zip) throw new TextureResolveError(`Minecraft client jar unavailable for texture: ${id}`);
    const bytes = zip.read(`assets/minecraft/${relative}`);
    if (!bytes) throw new TextureResolveError(`Minecraft texture not found in client jar: ${id}`);
    return { bytes, extension: path.extname(relative) || '.bin', source: `client-jar:assets/minecraft/${relative}` };
  };
}