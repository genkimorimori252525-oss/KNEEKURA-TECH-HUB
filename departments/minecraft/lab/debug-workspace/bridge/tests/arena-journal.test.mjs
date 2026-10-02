import test from 'node:test';
import assert from 'node:assert/strict';
import {
  mkdtemp,
  rm,
  writeFile
} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {
  validateArenaContract,
  validateActionEnvelope,
  validateResetEvidence
} from '../arena-contract.mjs';
import {
  beginAction,
  recordActionOutcome,
  readActionOutcome
} from '../action-journal.mjs';
const arena={
  schemaVersion:1,
  arenaId:'a',
  arenaEpoch:1,
  arenaRevision:0,
  baselineHash:'a'.repeat(64),
  bounds:{
    min:[0,
    0,
    0],
    max:[16,
    16,
    16]
  },
  allowedMutationBounds:{
    min:[1,
    1,
    1],
    max:[15,
    15,
    15]
  },
  resetClasses:{
    blocks:'RESETTABLE',
    entities:'UNKNOWN'
  }
};
const identity={
  debugSessionId:'s',
  runId:'r',
  runSnapshotId:'ss',
  processEpoch:1,
  experimentId:'e',
  subjects:{
    subject:'00000000-0000-0000-0000-000000000001'
  }
};
const action=()=>({
  schemaVersion:1,
  ...Object.fromEntries(Object.entries(identity).filter(([k])=>k!=='subjects')),
  arenaId:'a',
  arenaEpoch:1,
  expectedArenaRevision:0,
  actionId:'a1',
  idempotencyKey:'id1',
  type:'set_block',
  args:{
    position:[2,
    2,
    2],
    block:'minecraft:stone'
  }
});
test('Arena is bounded integer half-open and reset classes explicit',
() => {
  assert.equal(validateArenaContract(arena).arenaId,
  'a');
  for(const a of [{
    ...arena,
    bounds:{
      min:[0,
      0,
      0],
      max:[65,
      16,
      16]
    }
  },
  {
    ...arena,
    bounds:{
      min:[0,
      -65,
      0],
      max:[16,
      0,
      16]
    }
  },
  {
    ...arena,
    resetClasses:{
      passwords:'RESETTABLE'
    }
  },
  {
    ...arena,
    allowedMutationBounds:{
      min:[0,
      0,
      0],
      max:[17,
      16,
      16]
    }
  }])
  assert.throws(()=>validateArenaContract(a));
});
test('typed exact actions require current identity revision subjects and bounds',
() => {
  assert.equal(validateActionEnvelope(action(),
  arena,
  identity).backend,
  'UNAVAILABLE');
  for(const a of [{
    ...action(),
    processEpoch:2
  },
  {
    ...action(),
    expectedArenaRevision:1
  },
  {
    ...action(),
    args:{
      position:[15,
      2,
      2],
      block:'minecraft:stone'
    }
  },
  {
    ...action(),
    args:{
      position:[2.5,
      2,
      2],
      block:'minecraft:stone'
    }
  },
  {
    ...action(),
    type:'command',
    args:{
      text:'kill @e'
    }
  }])
  assert.throws(()=>validateActionEnvelope(a,
  arena,
  identity));
  for(const [type,
  args] of [['wait_ticks',
  {
    ticks:1200
  }],
  ['teleport_subject',
  {
    subject_id:'subject',
    position:[2,
    2,
    2],
    rotation:[180,
    90]
  }],
  ['use_item',
  {
    subject_id:'subject',
    hand:'off_hand',
    ticks:20
  }]])
  assert.equal(validateActionEnvelope({
    ...action(),
    type,
    args
  },
  arena,
  identity).scope,
  'CONTRACT_ONLY');
  assert.throws(()=>validateActionEnvelope({
    ...action(),
    type:'use_item',
    args:{
      subject_id:'missing',
      hand:'off_hand',
      ticks:21
    }
  },
  arena,
  identity));
});
test('reset reports cannot prove runtime and baseline/unknown state stay unresolved',
() => {
  const e={
    schemaVersion:1,
    debugSessionId:'s',
    runId:'r',
    runSnapshotId:'ss',
    processEpoch:1,
    arenaId:'a',
    beforeEpoch:1,
    afterEpoch:2,
    beforeRevision:0,
    afterRevision:1,
    expectedBaselineHash:arena.baselineHash,
    measuredBaselineHash:arena.baselineHash,
    resetClasses:['blocks'],
    remainingClasses:['entities'],
    evidenceHashes:['b'.repeat(64)]
  };
  assert.equal(validateResetEvidence(e,
  arena,
  identity).classification,
  'INCONCLUSIVE');
  assert.equal(validateResetEvidence({
    ...e,
    measuredBaselineHash:'c'.repeat(64)
  },
  arena,
  identity).classification,
  'ARENA_NOT_CLEAN');
  assert.equal(validateResetEvidence({
    ...e,
    remainingClasses:[],
    resetClasses:['blocks',
    'entities']
  },
  {
    ...arena,
    resetClasses:{
      blocks:'RESETTABLE',
      entities:'RESETTABLE'
    }
  },
  identity).scope,
  'CONTRACT_ONLY');
});
async function fixture(t) {
  const runDir=await mkdtemp(path.join(os.tmpdir(),
  'lab-journal-'));
  t.after(()=>rm(runDir,
  {
    recursive:true,
    force:true
  }));
  return {
    runDir,
    arena,
    identity,
    action:action()
  };
}
test('journal duplicate requests are non-dispatchable and differing payload conflicts',
async t => {
  const f=await fixture(t),
  a=await beginAction(f),
  b=await beginAction(f);
  assert.equal(a.status,
  'REQUESTED');
  assert.equal(a.dispatchAllowed,
  false);
  assert.equal(b.alreadyRecorded,
  true);
  await assert.rejects(beginAction({
    ...f,
    action:{
      ...f.action,
      args:{
        position:[3,
        3,
        3],
        block:'minecraft:stone'
      }
    }
  }),
  /IDEMPOTENCY_CONFLICT/);
});
test('accepted/applied nonterminal recovery is UNKNOWN and terminal transitions immutable',
async t => {
  const f=await fixture(t);
  await beginAction(f);
  const p={
    ...f,
    idempotencyKey:f.action.idempotencyKey
  };
  await recordActionOutcome({
    ...p,
    outcome:{
      status:'ACCEPTED',
      evidenceHashes:[]
    }
  });
  assert.equal((await readActionOutcome(p)).status,
  'OUTCOME_UNKNOWN');
  await recordActionOutcome({
    ...p,
    outcome:{
      status:'APPLIED',
      evidenceHashes:['a'.repeat(64)]
    }
  });
  assert.equal((await readActionOutcome(p)).status,
  'OUTCOME_UNKNOWN');
  await recordActionOutcome({
    ...p,
    outcome:{
      status:'VERIFIED',
      evidenceHashes:['b'.repeat(64)]
    }
  });
  const got=await readActionOutcome(p);
  assert.equal(got.status,
  'VERIFIED');
  assert.equal(got.runtimeAttestation,
  'NOT_ESTABLISHED');
  await assert.rejects(recordActionOutcome({
    ...p,
    outcome:{
      status:'APPLIED',
      evidenceHashes:['b'.repeat(64)]
    }
  }),
  /TRANSITION/);
});
test('concurrent duplicate reservation cannot duplicate acceptance',
async t => {
  const f=await fixture(t);
  const a=await Promise.allSettled([beginAction(f),
  beginAction(f)]);
  assert.ok(a.some(x=>x.status==='fulfilled'));
  const p={
    ...f,
    idempotencyKey:f.action.idempotencyKey
  };
  const records=await Promise.allSettled([recordActionOutcome({
    ...p,
    outcome:{
      status:'ACCEPTED',
      evidenceHashes:[]
    }
  }),
  recordActionOutcome({
    ...p,
    outcome:{
      status:'ACCEPTED',
      evidenceHashes:[]
    }
  })]);
  assert.equal(records.filter(x=>x.status==='fulfilled').length,
  1);
});
test('never-seen journal lookup is read-only and distinguishable',
async t => {
  const f=await fixture(t);
  const got=await readActionOutcome({
    ...f,
    idempotencyKey:'not-seen'
  });
  assert.equal(got.status,
  'NEVER_SEEN');
});
test('torn and missing receipts preserve UNKNOWN',
async t => {
  const f=await fixture(t);
  const first=await beginAction(f);
  const p={
    ...f,
    idempotencyKey:f.action.idempotencyKey
  };
  await writeFile(path.join(first.directory,
  'receipt-000000.json'),
  '{broken');
  assert.equal((await readActionOutcome(p)).status,
  'OUTCOME_UNKNOWN');
  await assert.rejects(recordActionOutcome({
    ...p,
    outcome:{
      status:'ACCEPTED',
      evidenceHashes:[]
    }
  }));
});
test('reset epochs may not overflow safe integers',
() => {
  const a={
    ...arena,
    arenaEpoch:Number.MAX_SAFE_INTEGER
  };
  const e={
    schemaVersion:1,
    debugSessionId:'s',
    runId:'r',
    runSnapshotId:'ss',
    processEpoch:1,
    arenaId:'a',
    beforeEpoch:a.arenaEpoch,
    afterEpoch:a.arenaEpoch+1,
    beforeRevision:0,
    afterRevision:1,
    expectedBaselineHash:a.baselineHash,
    measuredBaselineHash:a.baselineHash,
    resetClasses:['blocks'],
    remainingClasses:['entities'],
    evidenceHashes:['b'.repeat(64)]
  };
  assert.throws(()=>validateResetEvidence(e,
  a,
  identity));
});

test('missing initial request and corrupted receipt hash remain non-dispatchable', async t => {
  const first = await fixture(t);
  const entry = await beginAction(first);
  const query = { ...first, idempotencyKey: first.action.idempotencyKey };
  await rm(path.join(entry.directory, 'request.json'));
  assert.equal((await readActionOutcome(query)).status, 'OUTCOME_UNKNOWN');

  const second = await fixture(t);
  const next = await beginAction(second);
  const badReceipt = { sequence: 0, status: 'VERIFIED', receiptHash: 'a'.repeat(64) };
  await writeFile(path.join(next.directory, 'receipt-000000.json'), JSON.stringify(badReceipt));
  const result = await readActionOutcome({ ...second, idempotencyKey: second.action.idempotencyKey });
  assert.equal(result.status, 'OUTCOME_UNKNOWN');
  assert.equal(result.dispatchAllowed, false);
});

test('Java backend canonical action sidecar preserves the Node payload digest', async () => {
  const { readFile } = await import('node:fs/promises');
  const { sha256, stableJson } = await import('../json.mjs');
  const runDir = await mkdtemp(path.join(os.tmpdir(), 'arena-java-'));
  try {
    const input = action();
    const result = await beginAction({runDir, arena, identity, action: input});
    const bytes = await readFile(path.join(result.directory, 'canonical-action.json'));
    const request = JSON.parse(await readFile(path.join(result.directory, 'request.json')));
    assert.equal(bytes.toString(), stableJson(input));
    assert.equal(sha256(bytes), request.payloadHash);
    assert.deepEqual(JSON.parse(bytes), input);
  } finally { await rm(runDir, {recursive:true, force:true}); }
});
