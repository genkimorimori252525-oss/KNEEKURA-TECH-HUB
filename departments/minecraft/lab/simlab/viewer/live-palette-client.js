'use strict';

window.SimLivePalette = (function () {
  const STRIDE = 12;
  const COMPS = 9;

  function hashString(hash, value) {
    const bytes = new TextEncoder().encode(String(value == null ? '' : value));
    let h = hash;
    for (const byte of bytes) {
      h ^= BigInt(byte);
      h = BigInt.asUintN(64, h * 0x100000001b3n);
    }
    h ^= 0xffn;
    return BigInt.asUintN(64, h * 0x100000001b3n);
  }

  function layoutHash(modelId, modelTexture, geometryType, boneNames) {
    let hash = 0xcbf29ce484222325n;
    for (const value of [modelId, modelTexture, geometryType, ...boneNames]) {
      hash = hashString(hash, value);
    }
    return hash.toString(16).padStart(16, '0');
  }

  /** serve.mjs の SSE JSON を検査し、recorded palette と同じ state9 へ畳む。 */
  function decode(payload, expectedUuid, expectedModelId) {
    if (!payload || payload.uuid !== expectedUuid) throw new Error('live palette UUID mismatch');
    if (expectedModelId && payload.modelId !== expectedModelId) {
      throw new Error('live palette model ID mismatch');
    }
    if (payload.stride !== STRIDE || payload.paletteEndian !== 'be-f32') {
      throw new Error('unsupported live palette layout');
    }
    const bones = payload.boneCount | 0;
    const names = payload.boneNames;
    if (bones < 1 || !Array.isArray(names) || names.length !== bones) {
      throw new Error('invalid live palette bone identity');
    }
    if (!payload.modelId || !payload.geometryType
        || layoutHash(payload.modelId, payload.modelTexture || '', payload.geometryType, names)
          !== payload.layoutHash) {
      throw new Error('live palette model/layout identity mismatch');
    }
    let binary;
    try { binary = atob(payload.palette || ''); }
    catch { throw new Error('invalid live palette base64'); }
    if (binary.length !== bones * STRIDE * 4) {
      throw new Error('invalid live palette byte length');
    }
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const view = new DataView(bytes.buffer);
    const state9 = new Float32Array(bones * COMPS);
    for (let bone = 0; bone < bones; bone++) {
      for (let comp = 0; comp < COMPS; comp++) {
        state9[bone * COMPS + comp] = view.getFloat32((bone * STRIDE + comp) * 4, false);
      }
    }
    return {
      sequence: String(payload.sequence), gameTime: String(payload.gameTime),
      partialTick: Number(payload.partialTick) || 0, receivedAt: Number(payload.receivedAt) || Date.now(),
      uuid: payload.uuid, modelId: payload.modelId, layoutHash: payload.layoutHash,
      boneNames: names.slice(), slotOf: new Map(names.map((name, slot) => [name, slot])), state9,
    };
  }

  return { decode, layoutHash, STRIDE, COMPS };
})();
