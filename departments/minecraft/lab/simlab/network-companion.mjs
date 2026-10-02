import fs from 'node:fs/promises';

export async function readNetworkCompanion(file) {
  return parseNetworkCompanionText(await fs.readFile(file, 'utf8'), file);
}

export function parseNetworkCompanionText(text, source='<memory>') {
  const rows = [];
  let lineNo = 0;
  for (const raw of String(text).split(/\r?\n/)) {
    lineNo++;
    if (!raw.trim()) continue;
    let row;
    try { row = JSON.parse(raw); }
    catch (e) { throw new Error(`${source}:${lineNo}: invalid JSON: ${e.message}`); }
    if (!row || typeof row !== 'object' || Array.isArray(row)) {
      throw new Error(`${source}:${lineNo}: row must be an object`);
    }
    rows.push({row,lineNo});
  }

  if (!rows.length) throw new Error(`${source}: empty network companion`);
  const meta = rows[0].row;
  if (meta.ch !== 'net_meta') throw new Error(`${source}:${rows[0].lineNo}: first row must be ch=net_meta`);
  if (meta.v !== 1) throw new Error(`${source}:${rows[0].lineNo}: unsupported network companion v=${meta.v}`);
  if (typeof meta.scenario !== 'string' || !meta.scenario) throw new Error(`${source}: net_meta.scenario is required`);
  if (typeof meta.run !== 'string' || !meta.run) throw new Error(`${source}: net_meta.run is required`);
  if (typeof meta.physicalSide !== 'string' || !meta.physicalSide) throw new Error(`${source}: net_meta.physicalSide is required`);

  const events = [];
  const semantics = [];
  let prevSeq = 0;

  for (const {row,lineNo} of rows.slice(1)) {
    if (row.v !== 1) throw new Error(`${source}:${lineNo}: unsupported row v=${row.v}`);
    if (!Number.isInteger(row.seq) || row.seq <= prevSeq) {
      throw new Error(`${source}:${lineNo}: seq must be a strictly increasing integer`);
    }
    prevSeq = row.seq;
    if (!Number.isInteger(row.gameTime)) {
      throw new Error(`${source}:${lineNo}: gameTime must be an integer`);
    }
    validatePayload(row, source, lineNo);

    if (row.ch === 'net') {
      if (row.stage !== 'send' && row.stage !== 'receive') {
        throw new Error(`${source}:${lineNo}: stage must be send or receive`);
      }
      if (typeof row.packet !== 'string' || !row.packet) {
        throw new Error(`${source}:${lineNo}: packet class is required`);
      }
      if (row.direction !== undefined && typeof row.direction !== 'string') {
        throw new Error(`${source}:${lineNo}: direction must be a string when present`);
      }
      if (row.channel !== undefined && typeof row.channel !== 'string') {
        throw new Error(`${source}:${lineNo}: channel must be a string when present`);
      }
      events.push(row);
      continue;
    }

    if (row.ch === 'net_semantic') {
      if (typeof row.kind !== 'string' || !row.kind) {
        throw new Error(`${source}:${lineNo}: semantic kind is required`);
      }
      semantics.push(row);
      continue;
    }

    throw new Error(`${source}:${lineNo}: expected ch=net or ch=net_semantic`);
  }

  const timed = [...events, ...semantics];
  return {
    meta,
    events,
    semantics,
    sendCount: events.filter(e=>e.stage==='send').length,
    receiveCount: events.filter(e=>e.stage==='receive').length,
    semanticCount: semantics.length,
    minGameTime: timed.length ? Math.min(...timed.map(e=>e.gameTime)) : null,
    maxGameTime: timed.length ? Math.max(...timed.map(e=>e.gameTime)) : null
  };
}

function validatePayload(row, source, lineNo) {
  if (row.payload === undefined) return;
  if (!row.payload || typeof row.payload !== 'object' || Array.isArray(row.payload)) {
    throw new Error(`${source}:${lineNo}: payload must be an object when present`);
  }
  for (const [key,value] of Object.entries(row.payload)) {
    const scalar = typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean';
    if (!scalar) throw new Error(`${source}:${lineNo}: payload.${key} must be a scalar`);
  }
}
