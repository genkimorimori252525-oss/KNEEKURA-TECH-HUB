// AI Review & Repair (PLAN §4.5, P5). An AI may change only schema-listed FX parameters of one cue,
// with expected old values, asset hash and generation pinned. Model edits are delegated to the
// existing Blockbench guard. The evidence packet keeps independent verdict columns and refuses to
// promote synthetic or unexecuted evidence to PASS.
import { FX_PARAMETER_SCHEMA, createCue, validateCue, validateFxParameter } from './cue-contract.mjs';
import { buildReplayIndex, validateFrameSequence } from './frame-sequence.mjs';
import {
  VERDICTS, boundedList, byteLimit, contentRef, exactKeys, hashId, identifier, integer, oneOf, require, same, sealed, verifySeal,
} from './common.mjs';

export const REPAIR_KIND = 'kneekura_vfx_repair_proposal';
const FINDING_EPISTEMIC = ['VISUAL_INFERRED', 'DIRECT_OBSERVED', 'SAMPLED_OBSERVED'];
export const VERDICT_COLUMNS = Object.freeze(['structure', 'visual', 'gameplay', 'performance', 'human_preference']);

export function validateRepairProposal(input) {
  const p = structuredClone(input);
  exactKeys(p, ['proposalId', 'schemaVersion', 'kind', 'targetCueId', 'runtimeAssetHash', 'generation', 'scope', 'changes', 'finding'], 'REPAIR_PROPOSAL');
  verifySeal(p, 'proposalId', 'REPAIR_PROPOSAL_INTEGRITY');
  require(p.schemaVersion === 1 && p.kind === REPAIR_KIND, 'INVALID_REPAIR_KIND');
  hashId(p.targetCueId); contentRef(p.runtimeAssetHash); integer(p.generation, 1, 1000000, 'REPAIR_GENERATION');
  boundedList(p.scope, Object.keys(FX_PARAMETER_SCHEMA).length); require(p.scope.length > 0, 'REPAIR_SCOPE_REQUIRED');
  for (const name of p.scope) {
    // Anything that is not an FX parameter (bones, geometry, textures, scripts) is out of this lane.
    if (['model', 'bone', 'texture', 'geometry', 'animation', 'uv'].includes(name)) throw new TypeError('MODEL_EDIT_DELEGATED_TO_BLOCKBENCH_GUARD');
    require(Object.hasOwn(FX_PARAMETER_SCHEMA, name), 'FX_PARAMETER_NOT_ALLOWED');
  }
  require(new Set(p.scope).size === p.scope.length, 'DUPLICATE_REPAIR_SCOPE');
  boundedList(p.changes, p.scope.length); require(p.changes.length > 0, 'REPAIR_CHANGES_REQUIRED');
  const touched = new Set();
  for (const c of p.changes) {
    exactKeys(c, ['param', 'expectedOld', 'next'], 'REPAIR_CHANGE');
    require(p.scope.includes(c.param), 'CHANGE_OUTSIDE_SCOPE'); require(!touched.has(c.param), 'DUPLICATE_REPAIR_CHANGE'); touched.add(c.param);
    if (c.expectedOld !== null) validateFxParameter(c.param, c.expectedOld);
    validateFxParameter(c.param, c.next);
    require(!same(c.expectedOld, c.next), 'NO_OP_REPAIR_CHANGE');
  }
  exactKeys(p.finding, ['summary', 'epistemic', 'evidenceRefs'], 'REPAIR_FINDING');
  require(typeof p.finding.summary === 'string' && p.finding.summary.trim().length > 0 && p.finding.summary.length <= 1024, 'REPAIR_FINDING_SUMMARY');
  oneOf(p.finding.epistemic, FINDING_EPISTEMIC, 'INVALID_FINDING_EPISTEMIC');
  boundedList(p.finding.evidenceRefs, 32); require(p.finding.evidenceRefs.length > 0, 'FINDING_EVIDENCE_REQUIRED');
  p.finding.evidenceRefs.forEach(identifier);
  byteLimit(p, 16 * 1024, 'REPAIR_PROPOSAL_TOO_LARGE');
  return p;
}

export function createRepairProposal(body) {
  return validateRepairProposal(sealed({ schemaVersion: 1, kind: REPAIR_KIND, ...body }, 'proposalId'));
}

/**
 * Apply a proposal to exactly the cue it names. Every precondition is re-checked against the live cue;
 * the result is a new sealed cue (generation + 1) whose non-target fields are proven unchanged.
 */
export function applyRepair(cueInput, proposalInput) {
  const cue = validateCue(cueInput);
  const p = validateRepairProposal(proposalInput);
  require(p.targetCueId === cue.cueId, 'REPAIR_TARGET_MISMATCH');
  require(p.runtimeAssetHash === cue.runtimeAssetHash, 'REPAIR_ASSET_CHANGED');
  require(p.generation === cue.generation, 'STALE_REPAIR_GENERATION');
  const params = structuredClone(cue.params);
  for (const c of p.changes) {
    const current = Object.hasOwn(params, c.param) ? params[c.param] : null;
    require(same(current, c.expectedOld), 'REPAIR_EXPECTED_OLD_MISMATCH');
    params[c.param] = structuredClone(c.next);
  }
  const { cueId, ...body } = cue;
  const next = createCue({ ...body, params, generation: cue.generation + 1 });
  // Non-target invariance: only `params[scope]`, `generation` and the seal may differ.
  const strip = c => { const { cueId: _id, generation: _g, params: pr, ...rest } = c;
    return { rest, params: Object.fromEntries(Object.entries(pr).filter(([k]) => !p.changes.some(ch => ch.param === k))) }; };
  require(same(strip(cue), strip(next)), 'NON_TARGET_FIELD_CHANGED');
  return { before: cue, after: next, proposalId: p.proposalId,
    diff: p.changes.map(c => ({ param: c.param, before: c.expectedOld, after: c.next })) };
}

/** Before/after must be the same setup apart from the repaired cue, or the comparison is INCONCLUSIVE. */
export function compareSetups(beforeSeqInput, afterSeqInput) {
  const before = validateFrameSequence(beforeSeqInput);
  const after = validateFrameSequence(afterSeqInput);
  const differences = [];
  const check = (label, a, b) => { if (!same(a, b)) differences.push(label); };
  check('origin', before.origin, after.origin);
  check('subjects', before.subjects, after.subjects);
  check('effectId', before.fx.effectId, after.fx.effectId);
  check('runtimeAssetHash', before.fx.runtimeAssetHash, after.fx.runtimeAssetHash);
  check('cameraId', before.cameraId, after.cameraId);
  check('camera', before.frames[0].camera, after.frames[0].camera);
  check('arena', [before.identity.arenaId, before.identity.baselineHash], [after.identity.arenaId, after.identity.baselineHash]);
  check('budget', before.budget, after.budget);
  return { status: differences.length ? 'INCONCLUSIVE' : 'SAME_SETUP', differences };
}

function verdictCell(cell, column, context) {
  exactKeys(cell, ['verdict', 'evidenceRefs', 'note'], 'VERDICT_CELL');
  oneOf(cell.verdict, VERDICTS, 'INVALID_VERDICT');
  boundedList(cell.evidenceRefs, 32); cell.evidenceRefs.forEach(identifier);
  require(cell.note === null || (typeof cell.note === 'string' && cell.note.length <= 512), 'INVALID_VERDICT_NOTE');
  if (cell.verdict === 'PASS' || cell.verdict === 'FAIL') require(cell.evidenceRefs.length > 0, 'VERDICT_WITHOUT_EVIDENCE');
  if (cell.verdict === 'PASS') {
    // Synthetic fixtures and unexecuted runs can never certify runtime columns (A13).
    if (['visual', 'gameplay', 'performance'].includes(column)) require(context.realClient, 'SYNTHETIC_EVIDENCE_CANNOT_PASS_RUNTIME');
    if (column === 'visual') require(context.sameSetup && context.restored, 'VISUAL_PASS_REQUIRES_SAME_SETUP_AND_RESTORATION');
    if (column === 'human_preference') require(context.humanDecision === 'APPROVED', 'HUMAN_PREFERENCE_NOT_APPROVED');
  }
}

/**
 * P5 Evidence Packet: one finding, one bounded repair, before/after replay, independent verdict columns.
 * `complete` is true only when every column is PASS on real-client evidence; there is no combined score.
 */
export function buildEvidencePacket({ repair, beforeSequence, afterSequence, verdicts, humanDecision = 'NOT_REQUESTED' }) {
  const before = validateFrameSequence(beforeSequence);
  const after = validateFrameSequence(afterSequence);
  oneOf(humanDecision, ['NOT_REQUESTED', 'PENDING', 'APPROVED', 'REJECTED', 'NOT_REVIEWED'], 'INVALID_HUMAN_DECISION');
  require(before.fx.cueIds.includes(repair.before.cueId) && after.fx.cueIds.includes(repair.after.cueId), 'SEQUENCE_NOT_BOUND_TO_REPAIR');
  const beforeCue = validateCue(repair.before); const afterCue = validateCue(repair.after);
  hashId(repair.proposalId); boundedList(repair.diff, Object.keys(FX_PARAMETER_SCHEMA).length);
  require(afterCue.generation === beforeCue.generation + 1 && repair.diff.length > 0 &&
    repair.diff.every(d => same(afterCue.params[d.param], d.after) && same(beforeCue.params[d.param] ?? null, d.before)), 'REPAIR_RECORD_INCONSISTENT');
  const setup = compareSetups(before, after);
  const context = { realClient: before.origin === 'REAL_CLIENT' && after.origin === 'REAL_CLIENT', sameSetup: setup.status === 'SAME_SETUP',
    restored: before.restoration === 'RESTORED' && after.restoration === 'RESTORED', humanDecision };
  exactKeys(verdicts, VERDICT_COLUMNS, 'VERDICT_COLUMNS');
  for (const column of VERDICT_COLUMNS) verdictCell(verdicts[column], column, context);
  // An unanswered human review is NOT_REVIEWED, never silently PASS (A28/A41).
  if (humanDecision === 'PENDING' || humanDecision === 'NOT_REVIEWED') require(verdicts.human_preference.verdict !== 'PASS', 'HUMAN_PREFERENCE_NOT_APPROVED');
  const body = {
    schemaVersion: 1, kind: 'kneekura_vfx_evidence_packet', derived: true,
    origin: context.realClient ? 'REAL_CLIENT' : 'SYNTHETIC_OR_MIXED',
    repair: { proposalId: repair.proposalId, beforeCueId: repair.before.cueId, afterCueId: repair.after.cueId, diff: structuredClone(repair.diff) },
    sequences: { before: before.sequenceId, after: after.sequenceId },
    replay: { before: summary(buildReplayIndex(before)), after: summary(buildReplayIndex(after)) },
    setup, humanDecision, verdicts: structuredClone(verdicts),
    complete: VERDICT_COLUMNS.every(c => verdicts[c].verdict === 'PASS') && context.realClient,
  };
  return sealed(body, 'packetId');
}
const summary = i => ({ status: i.status, frameCount: i.frameCount, presentCount: i.presentCount, flaggedFrames: i.flaggedFrames });
