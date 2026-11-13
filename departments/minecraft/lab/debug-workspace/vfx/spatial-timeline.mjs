// Spatial & Timeline Inspector v1 (PLAN §4.4, P3). Extends the existing exact X/Z schematic with
// Y elevation views, per-source provenance and server/client event correlation. Derived only:
// it never infers hidden positions, collisions or causality.
import { escapeXml, topDownSvg } from '../evidence/visual-geometry.mjs';
import {
  boundedList, contentRef, exactKeys, finite, identifier, integer, oneOf, require, same, uuid, vector,
} from './common.mjs';
import { EVENT_KINDS } from './cue-contract.mjs';

export const SOURCE_KINDS = Object.freeze({
  SERVER_ENTITY_STATE: { side: 'SERVER', owner: 'subject' },
  HITBOX: { side: 'SERVER', owner: 'subject' },
  CLIENT_RENDER_POSE: { side: 'CLIENT', owner: 'bone' },
  FX_EMITTER: { side: 'CLIENT', owner: 'fx' },
  BEAM_ENDPOINT: { side: 'SERVER', owner: 'fx' },
  FX_PARTICLE_FIELD: { side: 'CLIENT', owner: 'fx' },
});
export const SAMPLE_STATUS = Object.freeze(['OBSERVED', 'MISSING', 'STALE', 'NOT_EXPOSED']);
const SAMPLE_KEYS = ['sampleId', 'sourceKind', 'status', 'epistemic', 'subjectUuid', 'fxInstanceId', 'bone', 'modelHash',
  'boneLayoutHash', 'gameTime', 'serverTick', 'renderFrame', 'partialTick', 'position', 'velocity', 'yaw', 'pitch', 'aabb', 'binding', 'observationId'];
const BINDING_KEYS = ['runId', 'processEpoch', 'arenaId', 'arenaEpoch'];

function bounds(b) {
  exactKeys(b, ['min', 'max'], 'ARENA_BOUNDS'); vector(b.min, 3); vector(b.max, 3);
  require(b.min.every((v, i) => b.max[i] > v && b.max[i] - v <= 128), 'INVALID_ARENA_BOUNDS');
  require(b.min[1] >= -64 && b.max[1] <= 320, 'INVALID_ARENA_HEIGHT');
}
function binding(b) {
  exactKeys(b, BINDING_KEYS, 'INSPECTOR_BINDING');
  identifier(b.runId); identifier(b.arenaId); integer(b.processEpoch, 1, 2147483647); integer(b.arenaEpoch, 0, Number.MAX_SAFE_INTEGER);
}

function sample(s, inspection) {
  exactKeys(s, SAMPLE_KEYS, 'SPATIAL_SAMPLE');
  identifier(s.sampleId);
  require(Object.hasOwn(SOURCE_KINDS, s.sourceKind), 'INVALID_SOURCE_KIND');
  const kind = SOURCE_KINDS[s.sourceKind];
  oneOf(s.status, SAMPLE_STATUS, 'INVALID_SAMPLE_STATUS');
  oneOf(s.epistemic, ['DIRECT_OBSERVED', 'SAMPLED_OBSERVED', 'DERIVED', 'NOT_EXPOSED'], 'INVALID_SAMPLE_EPISTEMIC');
  require((s.status === 'NOT_EXPOSED') === (s.epistemic === 'NOT_EXPOSED'), 'NOT_EXPOSED_MISMATCH');
  binding(s.binding);
  // Mixing runs/epochs in one view is the failure P3 must reject.
  require(same(s.binding, inspection.binding), 'MIXED_RUN_OR_EPOCH');
  integer(s.gameTime, 0, Number.MAX_SAFE_INTEGER);
  require(s.gameTime >= inspection.window.start && s.gameTime <= inspection.window.end, 'SAMPLE_OUTSIDE_WINDOW');
  if (kind.side === 'SERVER') {
    integer(s.serverTick, 0, Number.MAX_SAFE_INTEGER);
    require(s.renderFrame === null && s.partialTick === null, 'SERVER_SAMPLE_HAS_RENDER_CLOCK');
  } else {
    require(s.serverTick === null, 'CLIENT_SAMPLE_HAS_SERVER_TICK');
    integer(s.renderFrame, 0, Number.MAX_SAFE_INTEGER); finite(s.partialTick, 0, 1);
  }
  if (kind.owner === 'subject' || kind.owner === 'bone') { uuid(s.subjectUuid); require(inspection.subjects.includes(s.subjectUuid), 'UNREGISTERED_SUBJECT'); }
  else require(s.subjectUuid === null, 'FX_SAMPLE_HAS_SUBJECT');
  if (kind.owner === 'fx') identifier(s.fxInstanceId); else require(s.fxInstanceId === null, 'UNEXPECTED_FX_INSTANCE');
  if (kind.owner === 'bone') { identifier(s.bone); contentRef(s.modelHash); contentRef(s.boneLayoutHash); }
  else require(s.bone === null && s.modelHash === null && s.boneLayoutHash === null, 'UNEXPECTED_BONE_FIELDS');
  if (s.sourceKind === 'FX_PARTICLE_FIELD') require(s.status === 'NOT_EXPOSED', 'PARTICLE_POSITIONS_NOT_EXPOSED_IN_V1');
  const observed = s.status === 'OBSERVED' || s.status === 'STALE';
  if (!observed) require(['position', 'velocity', 'yaw', 'pitch', 'aabb', 'observationId'].every(k => s[k] === null), 'UNOBSERVED_SAMPLE_HAS_VALUES');
  else {
    identifier(s.observationId); vector(s.position, 3);
    if (s.sourceKind === 'SERVER_ENTITY_STATE') {
      vector(s.velocity, 3, 100); finite(s.yaw, -360000, 360000); finite(s.pitch, -90, 90); vector(s.aabb, 6);
      require(s.aabb.slice(0, 3).every((v, i) => v <= s.aabb[i + 3]), 'INVALID_SUBJECT_AABB');
    } else if (s.sourceKind === 'HITBOX') {
      require(s.velocity === null && s.yaw === null && s.pitch === null, 'HITBOX_HAS_MOTION');
      vector(s.aabb, 6); require(s.aabb.slice(0, 3).every((v, i) => v <= s.aabb[i + 3]), 'INVALID_HITBOX_AABB');
    } else require(s.velocity === null && s.yaw === null && s.pitch === null && s.aabb === null, 'POINT_SAMPLE_HAS_EXTRA_FIELDS');
  }
}

function event(e, inspection) {
  exactKeys(e, ['eventId', 'kind', 'side', 'attackInstanceId', 'gameTime', 'renderFrame', 'observationId'], 'TIMELINE_EVENT');
  identifier(e.eventId); oneOf(e.kind, EVENT_KINDS, 'INVALID_EVENT_KIND'); oneOf(e.side, ['SERVER', 'CLIENT'], 'INVALID_EVENT_SIDE');
  identifier(e.attackInstanceId); identifier(e.observationId); integer(e.gameTime, 0, Number.MAX_SAFE_INTEGER);
  require(e.gameTime >= inspection.window.start && e.gameTime <= inspection.window.end, 'EVENT_OUTSIDE_WINDOW');
  if (e.side === 'SERVER') require(e.renderFrame === null, 'SERVER_EVENT_HAS_RENDER_FRAME');
  else integer(e.renderFrame, 0, Number.MAX_SAFE_INTEGER);
}

function blockSamples(b, inspection) {
  if (b === null) return;
  exactKeys(b, ['roi', 'blocks'], 'BLOCK_SAMPLES'); bounds(b.roi);
  const a = inspection.arenaBounds;
  require(b.roi.min.every((v, i) => v >= a.min[i]) && b.roi.max.every((v, i) => v <= a.max[i]), 'BLOCK_ROI_OUTSIDE_ARENA');
  const volume = b.roi.max.reduce((p, v, i) => p * (v - b.roi.min[i]), 1);
  require(volume <= 4096, 'BLOCK_ROI_TOO_LARGE');
  boundedList(b.blocks, 4096);
  const seen = new Set();
  for (const block of b.blocks) {
    exactKeys(block, ['pos', 'state'], 'BLOCK_SAMPLE');
    vector(block.pos, 3); block.pos.forEach(v => integer(v, -30000000, 30000000));
    require(block.pos.every((v, i) => v >= b.roi.min[i] && v < b.roi.max[i]), 'BLOCK_OUTSIDE_ROI');
    require(typeof block.state === 'string' && /^[a-z0-9_.-]+:[a-z0-9_./-]+(\[[a-z0-9_=,]*\])?$/.test(block.state), 'INVALID_BLOCK_STATE');
    const key = block.pos.join(','); require(!seen.has(key), 'DUPLICATE_BLOCK_SAMPLE'); seen.add(key);
  }
}

export function validateInspection(input) {
  const x = structuredClone(input);
  exactKeys(x, ['schemaVersion', 'kind', 'binding', 'dimension', 'arenaBounds', 'subjects', 'window', 'samples', 'events', 'blockSamples'], 'INSPECTION');
  require(x.schemaVersion === 1 && x.kind === 'kneekura_spatial_timeline_inspection', 'INVALID_INSPECTION_KIND');
  binding(x.binding);
  require(typeof x.dimension === 'string' && /^[a-z0-9_]+:[a-z0-9_./-]+$/.test(x.dimension), 'INVALID_DIMENSION');
  bounds(x.arenaBounds);
  boundedList(x.subjects, 16); require(x.subjects.length > 0, 'SUBJECTS_REQUIRED'); x.subjects.forEach(v => uuid(v));
  require(new Set(x.subjects).size === x.subjects.length, 'DUPLICATE_SUBJECT');
  exactKeys(x.window, ['start', 'end'], 'INSPECTION_WINDOW');
  integer(x.window.start, 0, Number.MAX_SAFE_INTEGER); integer(x.window.end, x.window.start, x.window.start + 1200, 'INSPECTION_WINDOW');
  boundedList(x.samples, 4096); boundedList(x.events, 512);
  const ids = new Set();
  for (const s of x.samples) { sample(s, x); require(!ids.has(s.sampleId), 'DUPLICATE_SAMPLE'); ids.add(s.sampleId); }
  const eventIds = new Set();
  for (const e of x.events) { event(e, x); require(!eventIds.has(e.eventId), 'DUPLICATE_EVENT'); eventIds.add(e.eventId); }
  blockSamples(x.blockSamples, x);
  return x;
}

export const subjectLabels = subjects => [...subjects].sort().map((u, i) => ({ label: String.fromCharCode(65 + i), uuid: u, uuidSuffix: u.slice(-6) }));

/** Per-gameTime rows with WORLD and ARENA_LOCAL coordinates and explicit UNKNOWN entries. */
export function buildInspectorModel(input) {
  const x = validateInspection(input);
  const origin = x.arenaBounds.min;
  const local = p => p && p.map((v, i) => v - origin[i]);
  const inside = p => p.every((v, i) => v >= x.arenaBounds.min[i] && v <= x.arenaBounds.max[i]);
  const times = [...new Set([...x.samples.map(s => s.gameTime), ...x.events.map(e => e.gameTime)])].sort((a, b) => a - b);
  const rows = times.map(gameTime => ({
    gameTime,
    samples: x.samples.filter(s => s.gameTime === gameTime).map(s => ({
      sampleId: s.sampleId, sourceKind: s.sourceKind, side: SOURCE_KINDS[s.sourceKind].side, status: s.status, epistemic: s.epistemic,
      subjectUuid: s.subjectUuid, fxInstanceId: s.fxInstanceId, bone: s.bone,
      world: s.position ? { x: s.position[0], y: s.position[1], z: s.position[2] } : 'UNKNOWN',
      arenaLocal: s.position ? Object.fromEntries(['x', 'y', 'z'].map((k, i) => [k, local(s.position)[i]])) : 'UNKNOWN',
      flags: [...(s.position && !inside(s.position) ? ['OUTSIDE_ARENA'] : []), ...(s.status === 'STALE' ? ['STALE_VALUE'] : [])],
      clock: { serverTick: s.serverTick, renderFrame: s.renderFrame, partialTick: s.partialTick },
    })),
    // Registered subjects that have no SERVER_ENTITY_STATE at this time are shown, not hidden.
    missingSubjects: x.subjects.filter(u => !x.samples.some(s => s.gameTime === gameTime && s.subjectUuid === u && s.sourceKind === 'SERVER_ENTITY_STATE' && s.status === 'OBSERVED')),
    events: x.events.filter(e => e.gameTime === gameTime).map(e => ({ ...e })),
  }));
  return { schemaVersion: 1, kind: 'kneekura_spatial_timeline_model', derived: true, binding: x.binding, dimension: x.dimension,
    arenaBounds: x.arenaBounds, coordinateFrames: { WORLD: 'Minecraft world blocks, +Y up', ARENA_LOCAL: `WORLD minus arena min ${JSON.stringify(origin)}` },
    labels: subjectLabels(x.subjects), rows, correlation: correlateEvents(x), blockSamples: x.blockSamples };
}

/**
 * Pair SERVER and CLIENT events of the same attack instance and kind. Client gameTime is the server-synced
 * level time, so the difference is an estimate; causality is never established here.
 */
export function correlateEvents(x) {
  const used = new Set();
  return x.events.filter(e => e.side === 'SERVER').map(server => {
    const client = x.events.find(c => c.side === 'CLIENT' && !used.has(c.eventId) && c.attackInstanceId === server.attackInstanceId && c.kind === server.kind);
    if (!client) return { serverEventId: server.eventId, kind: server.kind, attackInstanceId: server.attackInstanceId, status: 'UNPAIRED', causality: 'NOT_ESTABLISHED' };
    used.add(client.eventId);
    return { serverEventId: server.eventId, clientEventId: client.eventId, kind: server.kind, attackInstanceId: server.attackInstanceId,
      status: 'PAIRED_BY_ID', clientMinusServerGameTicks: client.gameTime - server.gameTime, clientRenderFrame: client.renderFrame,
      clockNote: 'CLIENT_GAME_TIME_IS_SERVER_SYNCED_ESTIMATE', causality: 'NOT_ESTABLISHED' };
  });
}

/** Facts in the exact shape the existing topDownSvg consumes, from SERVER_ENTITY_STATE only. */
export function topDownFacts(model, gameTime) {
  const row = model.rows.find(r => r.gameTime === gameTime);
  require(row, 'NO_ROW_AT_GAME_TIME');
  const subjects = row.samples.filter(s => s.sourceKind === 'SERVER_ENTITY_STATE' && s.status === 'OBSERVED');
  return { row, subjects };
}

const VIEW = { width: 560, height: 420, pad: 48 };

/** Side elevation: horizontal = world X (axis 'X') or world Z (axis 'Z'), vertical = world Y (up). */
export function elevationSvg(model, inspectionInput, gameTime, axis) {
  oneOf(axis, ['X', 'Z'], 'INVALID_ELEVATION_AXIS');
  const x = validateInspection(inspectionInput);
  require(same(x.binding, model.binding), 'MODEL_INSPECTION_BINDING_MISMATCH');
  const h = axis === 'X' ? 0 : 2;
  const b = x.arenaBounds;
  const scale = Math.min((VIEW.width - 2 * VIEW.pad) / (b.max[h] - b.min[h]), (VIEW.height - 2 * VIEW.pad) / (b.max[1] - b.min[1]));
  const px = v => VIEW.pad + (v - b.min[h]) * scale;
  const py = v => VIEW.height - VIEW.pad - (v - b.min[1]) * scale;
  const labels = new Map(model.labels.map(l => [l.uuid, l]));
  const samples = x.samples.filter(s => s.gameTime === gameTime);
  const parts = [];
  const unknown = [];
  for (const s of samples) {
    const tag = s.subjectUuid ? `${labels.get(s.subjectUuid).label}${s.bone ? '.' + s.bone : ''}` : s.fxInstanceId;
    if (s.status !== 'OBSERVED' && s.status !== 'STALE') { unknown.push(`${s.sourceKind} ${tag}: ${s.status}`); continue; }
    const [wx, wy, wz] = s.position; const hp = axis === 'X' ? wx : wz;
    const data = `data-sample="${escapeXml(s.sampleId)}" data-source-kind="${s.sourceKind}" data-world-x="${wx}" data-world-y="${wy}" data-world-z="${wz}"`;
    const stale = s.status === 'STALE' ? ' stroke-dasharray="3 2"' : '';
    if (s.aabb) parts.push(`<rect ${data} x="${px(s.aabb[h])}" y="${py(s.aabb[4])}" width="${(s.aabb[h + 3] - s.aabb[h]) * scale}" height="${(s.aabb[4] - s.aabb[1]) * scale}" fill="${s.sourceKind === 'HITBOX' ? '#ff6b6b22' : '#79b8ff22'}" stroke="${s.sourceKind === 'HITBOX' ? '#ff6b6b' : '#79b8ff'}"${stale}/>`);
    const color = { SERVER_ENTITY_STATE: '#ffffff', CLIENT_RENDER_POSE: '#c792ea', FX_EMITTER: '#7fdbff', BEAM_ENDPOINT: '#ffd166', HITBOX: '#ff6b6b' }[s.sourceKind];
    const cx = px(hp), cy = py(wy);
    parts.push(s.sourceKind === 'CLIENT_RENDER_POSE'
      ? `<path ${data} d="M${cx} ${cy - 5}L${cx + 5} ${cy}L${cx} ${cy + 5}L${cx - 5} ${cy}Z" fill="${color}"${stale}/>`
      : `<circle ${data} cx="${cx}" cy="${cy}" r="${s.sourceKind === 'FX_EMITTER' ? 4 : 3}" fill="${color}"${stale}/>`);
    // Nearby points (weapon bone vs its emitter) are common; stagger labels per source kind so they stay legible.
    const dy = { SERVER_ENTITY_STATE: -6, CLIENT_RENDER_POSE: -8, FX_EMITTER: 16, BEAM_ENDPOINT: 28, HITBOX: 40 }[s.sourceKind];
    parts.push(`<text x="${cx + 6}" y="${cy + dy}">${escapeXml(tag)}${s.status === 'STALE' ? ' (STALE)' : ''}</text>`);
  }
  for (const u of x.subjects) if (!samples.some(s => s.subjectUuid === u && s.sourceKind === 'SERVER_ENTITY_STATE' && s.status === 'OBSERVED'))
    unknown.push(`SERVER_ENTITY_STATE ${labels.get(u).label}: UNKNOWN`);
  const name = axis === 'X' ? 'X' : 'Z';
  const footer = unknown.slice(0, 12).map((t, i) => `<text x="20" y="${VIEW.height + 18 + i * 14}" fill="#ffb86c">UNKNOWN · ${escapeXml(t)}</text>`).join('');
  const height = VIEW.height + 24 + Math.min(unknown.length, 12) * 14;
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${VIEW.width}" height="${height}" viewBox="0 0 ${VIEW.width} ${height}"><rect width="${VIEW.width}" height="${height}" fill="#141921"/><g fill="#fff" font-family="sans-serif" font-size="12"><text x="20" y="20">Exact ${name}/Y elevation · gameTime ${gameTime} · +Y up · ${axis === 'X' ? 'EAST = +X' : 'SOUTH = +Z'}</text><rect x="${px(b.min[h])}" y="${py(b.max[1])}" width="${(b.max[h] - b.min[h]) * scale}" height="${(b.max[1] - b.min[1]) * scale}" fill="none" stroke="#8a94a8"/><text x="${px(b.min[h])}" y="${py(b.min[1]) + 16}">WORLD ${name}=${b.min[h]} Y=${b.min[1]} (ARENA_LOCAL 0,0)</text><text x="${px(b.max[h]) - 90}" y="${py(b.max[1]) - 6}">${name}=${b.max[h]} Y=${b.max[1]}</text>${parts.join('')}<text x="20" y="${VIEW.height - 10}">White: server entity · Violet: client bone pose · Cyan: FX emitter · Red: hitbox · dashed: STALE</text>${footer}</g></svg>`);
}

/** One sheet: existing exact X/Z schematic (reused, not reimplemented) plus X/Y and Z/Y elevations. */
export function spatialSheetSvg(model, inspectionInput, gameTime) {
  const { subjects } = topDownFacts(model, gameTime);
  const x = validateInspection(inspectionInput);
  const facts = { dimension: x.dimension, gameTime, arenaBounds: x.arenaBounds,
    subjects: subjects.map(s => { const src = x.samples.find(r => r.sampleId === s.sampleId);
      return { uuid: src.subjectUuid, position: src.position, velocity: src.velocity, yaw: src.yaw, pitch: src.pitch, bounds: src.aabb }; }) };
  const inner = svg => svg.toString('utf8').replace(/^<svg xmlns="http:\/\/www\.w3\.org\/2000\/svg"/, '<svg');
  const top = inner(topDownSvg(facts, model.labels));
  const sideX = inner(elevationSvg(model, x, gameTime, 'X'));
  const sideZ = inner(elevationSvg(model, x, gameTime, 'Z'));
  const place = (svg, dx) => svg.replace(/^<svg/, `<svg x="${dx}" y="0"`);
  return Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="1680" height="640" viewBox="0 0 1680 640"><rect width="1680" height="640" fill="#141921"/>${place(top, 0)}${place(sideX, 560)}${place(sideZ, 1120)}</svg>`);
}
