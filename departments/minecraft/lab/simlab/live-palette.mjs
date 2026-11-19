import net from 'node:net';

export const LIVE_PALETTE_MAGIC = 0x544c504c; // TLPL
export const LIVE_PALETTE_VERSION = 1;
export const LIVE_PALETTE_STRIDE = 12;
export const LIVE_PALETTE_MAX_BODY = 16 * 1024 * 1024;
const MAX_BONES = 4096;
const MAX_STRING_BYTES = 1024 * 1024;
const DEFAULT_HISTORY = 3;
const DEFAULT_IDENTITIES = 32;
const UTF8 = new TextDecoder('utf-8', { fatal: true });

function fail(message) {
  throw new Error(message);
}

function uuidAt(buf, offset) {
  const hex = buf.subarray(offset, offset + 16).toString('hex');
  if (hex === '00000000000000000000000000000000') fail('zero UUID');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

function hashString(hash, value) {
  const bytes = Buffer.from(value, 'utf8');
  let h = hash;
  for (const byte of bytes) {
    h ^= BigInt(byte);
    h = BigInt.asUintN(64, h * 0x100000001b3n);
  }
  h ^= 0xffn;
  return BigInt.asUintN(64, h * 0x100000001b3n);
}

export function livePaletteLayoutHash(modelId, modelTexture, geometryType, boneNames) {
  let hash = 0xcbf29ce484222325n;
  for (const value of [modelId, modelTexture, geometryType, ...boneNames]) {
    hash = hashString(hash, String(value ?? ''));
  }
  return hash;
}

/** Java SimPaletteLiveProtocol v1 の body を厳格に読む。Buffer 外参照と余剰 byte を許さない。 */
export function decodeLivePaletteFrame(body) {
  if (!Buffer.isBuffer(body) || body.length === 0 || body.length > LIVE_PALETTE_MAX_BODY) {
    fail('invalid body length');
  }
  let p = 0;
  const need = (n) => { if (n < 0 || p + n > body.length) fail(`truncated frame at ${p} + ${n}`); };
  const i32 = () => { need(4); const v = body.readInt32BE(p); p += 4; return v; };
  const u16 = () => { need(2); const v = body.readUInt16BE(p); p += 2; return v; };
  const i64 = () => { need(8); const v = body.readBigInt64BE(p); p += 8; return v; };
  const u64 = () => { need(8); const v = body.readBigUInt64BE(p); p += 8; return v; };
  const f32 = () => { need(4); const v = body.readFloatBE(p); p += 4; return v; };
  const string = () => {
    const length = i32();
    if (length < 0 || length > MAX_STRING_BYTES) fail(`invalid string length ${length}`);
    need(length);
    let value;
    try { value = UTF8.decode(body.subarray(p, p + length)); }
    catch { fail('invalid UTF-8 string'); }
    p += length;
    return value;
  };

  if (i32() !== LIVE_PALETTE_MAGIC) fail('magic mismatch');
  const version = u16();
  const stride = u16();
  if (version !== LIVE_PALETTE_VERSION || stride !== LIVE_PALETTE_STRIDE) {
    fail(`unsupported format version=${version} stride=${stride}`);
  }
  const sequence = i64();
  const gameTime = i64();
  const partialTick = f32();
  const entityId = i32();
  need(16);
  const uuid = uuidAt(body, p);
  p += 16;
  const wireLayoutHash = u64();
  const entityType = string();
  const modelId = string();
  const modelTexture = string();
  const geometryType = string();
  if (!/^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(entityType)) fail('invalid entity type identity');
  if (!modelId || !geometryType) fail('missing model identity');

  const boneCount = i32();
  if (boneCount < 1 || boneCount > MAX_BONES) fail(`invalid bone count ${boneCount}`);
  const boneNames = new Array(boneCount);
  for (let i = 0; i < boneCount; i++) {
    const name = string();
    // 同名 bone は YSM 側で許され得る。slot 順と組にすれば identity は一意なので拒否しない。
    if (!name) fail(`invalid bone identity at slot ${i}`);
    boneNames[i] = name;
  }
  const floats = i32();
  if (floats !== boneCount * LIVE_PALETTE_STRIDE) {
    fail(`palette length ${floats} != ${boneCount * LIVE_PALETTE_STRIDE}`);
  }
  const paletteBytesLength = floats * Float32Array.BYTES_PER_ELEMENT;
  need(paletteBytesLength);
  const palette = Buffer.from(body.subarray(p, p + paletteBytesLength));
  p += paletteBytesLength;
  if (p !== body.length) fail(`trailing bytes ${body.length - p}`);

  const layoutHash = livePaletteLayoutHash(modelId, modelTexture, geometryType, boneNames);
  if (layoutHash !== wireLayoutHash) fail('layout hash mismatch');
  return {
    version, stride, sequence, gameTime, partialTick, entityId, uuid, entityType,
    modelId, modelTexture, geometryType, layoutHash, boneCount, boneNames, palette,
  };
}

function publicFrame(frame) {
  return {
    sequence: frame.sequence.toString(),
    gameTime: frame.gameTime.toString(),
    partialTick: frame.partialTick,
    entityId: frame.entityId,
    uuid: frame.uuid,
    entityType: frame.entityType,
    modelId: frame.modelId,
    modelTexture: frame.modelTexture,
    geometryType: frame.geometryType,
    layoutHash: frame.layoutHash.toString(16).padStart(16, '0'),
    boneCount: frame.boneCount,
    boneNames: frame.boneNames,
    stride: frame.stride,
    paletteEndian: 'be-f32',
    palette: frame.palette.toString('base64'),
    receivedAt: frame.receivedAt,
  };
}

function validUuid(value) {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value || '');
}

/**
 * loopback receiver と UUID/model 別の短い memory buffer。start/close を明示できるので
 * selftest は実 socket を使ってもプロセスやファイルを残さない。
 */
export function createLivePaletteHub(options = {}) {
  const host = options.host || '127.0.0.1';
  const port = options.port ?? 8778;
  const historyLimit = Math.max(1, options.historyLimit || DEFAULT_HISTORY);
  const identityLimit = Math.max(1, options.identityLimit || DEFAULT_IDENTITIES);
  const history = new Map();
  const latestByUuid = new Map();
  const subscribers = new Set();
  const sockets = new Set();
  const stats = {
    accepted: 0, rejected: 0, outOfOrder: 0, connections: 0, disconnects: 0, serverErrors: 0,
  };
  let server = null;
  let listening = null;
  let nextSourceId = 0;

  const status = () => ({
    listening: !!(server && server.listening), host, port: server?.address()?.port || port,
    sourceConnected: sockets.size > 0, sources: sockets.size,
    identities: history.size, ...stats,
  });
  const statusFor = (uuid, modelId = '') => {
    const latest = latestByUuid.get(String(uuid || '').toLowerCase()) || null;
    const matches = !!latest && (!modelId || latest.modelId === modelId);
    return {
      ...status(), uuid: uuid || null, expectedModelId: modelId || null,
      identity: latest ? { uuid: latest.uuid, modelId: latest.modelId,
        layoutHash: latest.layoutHash.toString(16).padStart(16, '0') } : null,
      identityMatches: matches,
      lastFrameAt: matches ? latest.receivedAt : null,
      ageMs: matches ? Math.max(0, Date.now() - latest.receivedAt) : null,
    };
  };
  const notify = (event) => {
    for (const sub of subscribers) {
      if (event.type === 'frame') {
        if (sub.uuid !== event.frame.uuid) continue;
        if (sub.modelId && sub.modelId !== event.frame.modelId) continue;
      }
      try { sub.callback(event); } catch { /* 一つの HTTP client に全体を止めさせない。 */ }
    }
  };
  const accept = (decoded, sourceId) => {
    const frame = { ...decoded, sourceId, receivedAt: Date.now() };
    const uuidKey = frame.uuid.toLowerCase();
    const previous = latestByUuid.get(uuidKey);
    if (previous && previous.sourceId === sourceId
        && frame.gameTime >= previous.gameTime && frame.sequence <= previous.sequence) {
      stats.outOfOrder++;
      return false;
    }
    const identityKey = `${uuidKey}\u0000${frame.modelId}\u0000${frame.layoutHash.toString(16)}`;
    const frames = history.get(identityKey) || [];
    frames.push(frame);
    if (frames.length > historyLimit) frames.splice(0, frames.length - historyLimit);
    history.delete(identityKey);
    history.set(identityKey, frames);
    while (history.size > identityLimit) history.delete(history.keys().next().value);
    latestByUuid.set(uuidKey, frame);
    stats.accepted++;
    notify({ type: 'frame', frame });
    return true;
  };

  const attach = (socket) => {
    // server 自体も loopback bind だが、accept 後にも確認して設定事故を fail closed にする。
    if (!socket.remoteAddress || !['127.0.0.1', '::1', '::ffff:127.0.0.1'].includes(socket.remoteAddress)) {
      stats.rejected++;
      socket.destroy();
      return;
    }
    sockets.add(socket);
    const sourceId = ++nextSourceId;
    stats.connections++;
    notify({ type: 'status' });
    let input = Buffer.alloc(0);
    socket.on('data', (chunk) => {
      if (input.length + chunk.length > LIVE_PALETTE_MAX_BODY + 4) {
        stats.rejected++;
        socket.destroy();
        return;
      }
      input = input.length ? Buffer.concat([input, chunk]) : chunk;
      while (input.length >= 4) {
        const length = input.readInt32BE(0);
        if (length < 1 || length > LIVE_PALETTE_MAX_BODY) {
          stats.rejected++;
          socket.destroy();
          return;
        }
        if (input.length < length + 4) return;
        const body = input.subarray(4, length + 4);
        input = input.subarray(length + 4);
        try { accept(decodeLivePaletteFrame(body), sourceId); }
        catch {
          stats.rejected++;
          socket.destroy();
          return;
        }
      }
    });
    socket.on('error', () => { /* close が状態を一度だけ更新する。 */ });
    socket.on('close', () => {
      if (!sockets.delete(socket)) return;
      stats.disconnects++;
      notify({ type: 'status' });
    });
  };

  const start = () => {
    if (listening) return listening;
    server = net.createServer(attach);
    // listen 後の server error に handler が無いと Node がプロセスごと終了する。
    // bind 失敗は下の once handler でも reject し、稼働後は status へ反映する。
    server.on('error', () => {
      stats.serverErrors++;
      notify({ type: 'status' });
    });
    listening = new Promise((resolve, reject) => {
      const onError = (error) => { server.off('listening', onListening); reject(error); };
      const onListening = () => { server.off('error', onError); resolve(server.address()); };
      server.once('error', onError);
      server.once('listening', onListening);
      server.listen({ host, port });
    });
    return listening;
  };
  const close = async () => {
    for (const socket of sockets) socket.destroy();
    sockets.clear();
    subscribers.clear();
    if (!server) return;
    await new Promise((resolve) => server.close(() => resolve()));
    server = null;
    listening = null;
  };
  const subscribe = ({ uuid, modelId = '' }, callback) => {
    const normalized = String(uuid || '').toLowerCase();
    if (!validUuid(normalized)) throw new Error('invalid palette subscription UUID');
    const sub = { uuid: normalized, modelId, callback };
    subscribers.add(sub);
    callback({ type: 'status' });
    for (const frames of history.values()) {
      for (const frame of frames) {
        if (frame.uuid !== normalized || (modelId && frame.modelId !== modelId)) continue;
        callback({ type: 'frame', frame });
      }
    }
    return () => subscribers.delete(sub);
  };

  return { start, close, subscribe, status, statusFor, publicFrame, validUuid };
}
