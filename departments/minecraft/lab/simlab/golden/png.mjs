import { deflateSync, inflateSync } from 'node:zlib';

const PNG_SIGNATURE = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
const MAX_PIXELS = 64 * 1024 * 1024;

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (const byte of buf) c = CRC_TABLE[(c ^ byte) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data = Buffer.alloc(0)) {
  const typeBuf = Buffer.from(type, 'ascii');
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
  return Buffer.concat([len, typeBuf, data, crc]);
}

function paeth(a, b, c) {
  const p = a + b - c;
  const pa = Math.abs(p - a);
  const pb = Math.abs(p - b);
  const pc = Math.abs(p - c);
  if (pa <= pb && pa <= pc) return a;
  if (pb <= pc) return b;
  return c;
}

function channelsForColorType(colorType) {
  if (colorType === 0) return 1;
  if (colorType === 2) return 3;
  if (colorType === 4) return 2;
  if (colorType === 6) return 4;
  throw new Error(`unsupported PNG colorType ${colorType}; supported: 0,2,4,6`);
}

export function decodePng(bytes) {
  const buf = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes);
  if (buf.length < 8 || !buf.subarray(0, 8).equals(PNG_SIGNATURE)) {
    throw new Error('invalid PNG signature');
  }

  let offset = 8;
  let width = null;
  let height = null;
  let bitDepth = null;
  let colorType = null;
  let compression = null;
  let filterMethod = null;
  let interlace = null;
  const idat = [];
  let sawIend = false;

  while (offset + 12 <= buf.length) {
    const length = buf.readUInt32BE(offset);
    const typeStart = offset + 4;
    const dataStart = typeStart + 4;
    const dataEnd = dataStart + length;
    const crcEnd = dataEnd + 4;
    if (crcEnd > buf.length) throw new Error('truncated PNG chunk');

    const typeBuf = buf.subarray(typeStart, dataStart);
    const type = typeBuf.toString('ascii');
    const data = buf.subarray(dataStart, dataEnd);
    const expectedCrc = buf.readUInt32BE(dataEnd);
    const actualCrc = crc32(Buffer.concat([typeBuf, data]));
    if (expectedCrc !== actualCrc) throw new Error(`PNG CRC mismatch in ${type}`);

    if (type === 'IHDR') {
      if (length !== 13) throw new Error('invalid IHDR length');
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      compression = data[10];
      filterMethod = data[11];
      interlace = data[12];
    } else if (type === 'IDAT') {
      idat.push(data);
    } else if (type === 'IEND') {
      sawIend = true;
      break;
    }
    offset = crcEnd;
  }

  if (!sawIend) throw new Error('PNG missing IEND');
  if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    throw new Error('PNG missing/invalid IHDR dimensions');
  }
  if (bitDepth !== 8) throw new Error(`unsupported PNG bitDepth ${bitDepth}; only 8-bit supported`);
  if (compression !== 0 || filterMethod !== 0 || interlace !== 0) {
    throw new Error('unsupported PNG compression/filter/interlace mode');
  }
  if (idat.length === 0) throw new Error('PNG missing IDAT');

  const pixels = width * height;
  if (!Number.isSafeInteger(pixels) || pixels > MAX_PIXELS) {
    throw new Error('PNG dimensions exceed safe pixel limit');
  }
  const channels = channelsForColorType(colorType);
  const bytesPerPixel = channels;
  const scanlineBytes = width * channels;
  const expectedRaw = height * (scanlineBytes + 1);
  if (!Number.isSafeInteger(expectedRaw)) throw new Error('PNG decompressed size is unsafe');
  const raw = inflateSync(Buffer.concat(idat), { maxOutputLength: expectedRaw });
  if (raw.length !== expectedRaw) {
    throw new Error(`unexpected PNG decompressed size ${raw.length}; expected ${expectedRaw}`);
  }

  const recon = Buffer.alloc(height * scanlineBytes);
  let src = 0;
  for (let y = 0; y < height; y++) {
    const filter = raw[src++];
    const rowStart = y * scanlineBytes;
    const prevStart = (y - 1) * scanlineBytes;
    for (let x = 0; x < scanlineBytes; x++) {
      const v = raw[src++];
      const left = x >= bytesPerPixel ? recon[rowStart + x - bytesPerPixel] : 0;
      const up = y > 0 ? recon[prevStart + x] : 0;
      const upLeft = y > 0 && x >= bytesPerPixel ? recon[prevStart + x - bytesPerPixel] : 0;
      let out;
      if (filter === 0) out = v;
      else if (filter === 1) out = (v + left) & 0xff;
      else if (filter === 2) out = (v + up) & 0xff;
      else if (filter === 3) out = (v + Math.floor((left + up) / 2)) & 0xff;
      else if (filter === 4) out = (v + paeth(left, up, upLeft)) & 0xff;
      else throw new Error(`unsupported PNG filter ${filter}`);
      recon[rowStart + x] = out;
    }
  }

  const rgba = new Uint8Array(width * height * 4);
  for (let i = 0, p = 0; i < width * height; i++) {
    if (colorType === 6) {
      rgba[p++] = recon[i * 4];
      rgba[p++] = recon[i * 4 + 1];
      rgba[p++] = recon[i * 4 + 2];
      rgba[p++] = recon[i * 4 + 3];
    } else if (colorType === 2) {
      rgba[p++] = recon[i * 3];
      rgba[p++] = recon[i * 3 + 1];
      rgba[p++] = recon[i * 3 + 2];
      rgba[p++] = 255;
    } else if (colorType === 0) {
      const g = recon[i];
      rgba[p++] = g; rgba[p++] = g; rgba[p++] = g; rgba[p++] = 255;
    } else if (colorType === 4) {
      const g = recon[i * 2];
      rgba[p++] = g; rgba[p++] = g; rgba[p++] = g; rgba[p++] = recon[i * 2 + 1];
    }
  }
  return { width, height, rgba };
}

export function encodePngRgba({ width, height, rgba, compressionLevel = 9 }) {
  if (!Number.isInteger(width) || width <= 0 || !Number.isInteger(height) || height <= 0) {
    throw new Error('width/height must be positive integers');
  }
  const src = rgba instanceof Uint8Array ? rgba : new Uint8Array(rgba);
  if (src.length !== width * height * 4) {
    throw new Error(`RGBA length ${src.length} does not match ${width}x${height}`);
  }

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8;
  ihdr[9] = 6;
  ihdr[10] = 0;
  ihdr[11] = 0;
  ihdr[12] = 0;

  const raw = Buffer.alloc(height * (1 + width * 4));
  let dst = 0;
  for (let y = 0; y < height; y++) {
    raw[dst++] = 0;
    const start = y * width * 4;
    Buffer.from(src.buffer, src.byteOffset + start, width * 4).copy(raw, dst);
    dst += width * 4;
  }

  return Buffer.concat([
    PNG_SIGNATURE,
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw, { level: compressionLevel })),
    chunk('IEND'),
  ]);
}