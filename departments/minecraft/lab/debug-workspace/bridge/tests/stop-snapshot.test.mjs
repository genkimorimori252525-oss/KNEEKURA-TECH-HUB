import test from 'node:test';
import assert from 'node:assert/strict';
import {
  mkdtemp,
  rm,
  writeFile,
  readFile
} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {
  verifyProcessesExited
} from '../../process-stop.mjs';
import {
  buildRunSnapshot,
  writeG1Acceptance,
  stopCurrent
} from '../../core.mjs';
const record={
  pid:123,
  spawnedAtEpochMs:1000,
  launchCommand:'java'
};
function clock(inspect) {
  let now=0;
  return {
    inspect,
    now:()=>now,
    sleep:async ms=>{
      now+=ms;
    },
    timeoutMs:100,
    pollMs:10
  };
}
test('bounded verifier exit timeout inspection error and PID reuse',
async () => {
  assert.equal((await verifyProcessesExited([record],
  clock(async()=>({
    exists:false,
    pid:123
  })))).status,
  'VERIFIED_EXIT');
  const live={
    exists:true,
    pid:123,
    startedAtEpochMs:1000,
    commandLine:'java'
  };
  assert.equal((await verifyProcessesExited([record],
  clock(async()=>live))).status,
  'EXIT_TIMEOUT');
  assert.equal((await verifyProcessesExited([record],
  clock(async()=>({
    exists:false,
    pid:123,
    inspectionError:'denied'
  })))).status,
  'INSPECTION_UNKNOWN');
  assert.equal((await verifyProcessesExited([record],
  clock(async()=>({
    ...live,
    startedAtEpochMs:999999
  })))).status,
  'OWNERSHIP_CHANGED');
  let n=0;
  assert.equal((await verifyProcessesExited([record],
  clock(async()=>++n<3?live:{
    exists:false,
    pid:123
  }))).status,
  'VERIFIED_EXIT');
  await assert.rejects(verifyProcessesExited([record],
  {
    ...clock(async()=>live),
    timeoutMs:Infinity
  }));
});
test('hung inspector has a real bounded timeout',
async () => {
  const start=Date.now();
  const got=await verifyProcessesExited([record],
  {
    inspect:()=>new Promise(() => {
    }),
    timeoutMs:30,
    pollMs:5
  });
  assert.equal(got.status,
  'INSPECTION_UNKNOWN');
  assert.ok(Date.now()-start<1000);
});
const binding={
  schema_version:1,
  experiment_id:'e',
  generation:1,
  request_hash:'a'.repeat(64),
  target:{
    profile_id:'b'.repeat(64),
    index_snapshot_id:'c'.repeat(64),
    build_artifact_hash:'d'.repeat(64),
    source_revision:'e'.repeat(40),
    dirty_hash:'f'.repeat(64),
    config_hash:'0'.repeat(64),
    resource_hash:'1'.repeat(64)
  },
  arena_id:'a',
  arena_baseline_hash:'2'.repeat(64),
  assertions_hash:'3'.repeat(64)
};
test('snapshot adds initial binding only and never promotes disk proof',
() => {
  const base={
    schemaVersion:1,
    snapshotId:'s',
    source:{
      before:{
        dirty:false
      }
    }
  };
  assert.deepEqual(buildRunSnapshot(base),
  base);
  const context={
    binding,
    registrationHash:'4'.repeat(64),
    materialInventory:{
      buildArtifact:{
        sha256:'d'.repeat(64)
      }
    },
    runtimeAttestation:'NOT_ESTABLISHED'
  };
  const got=buildRunSnapshot(base,
  context);
  assert.deepEqual(got.techHub,
  binding);
  assert.equal(got.bridge.runtimeAttestation,
  'NOT_ESTABLISHED');
  assert.equal(got.bridge.execution,
  'BLOCKED');
  assert.equal(Object.hasOwn(base,
  'techHub'),
  false);
  assert.throws(()=>buildRunSnapshot({
    ...base,
    techHub:binding
  },
  context));
});
test('G1 stop proof requires verified exit, not ok alone',
async t => {
  const dir=await mkdtemp(path.join(os.tmpdir(),
  'lab-g1-'));
  t.after(()=>rm(dir,
  {
    recursive:true,
    force:true
  }));
  const config={
    schemaVersion:1,
    workspaceId:'x',
    workspaceDir:dir,
    launch:{
      command:'node',
      args:[]
    }
  };
  const r=await writeG1Acceptance(config,
  dir,
  {
    started:{
      status:'DEBUG_READY',
      runDir:dir
    },
    timeline:{
      complete:true
    },
    status:{
      live:true
    },
    stopped:{
      ok:true,
      cleanup:{
        status:'EXIT_TIMEOUT'
      }
    }
  });
  assert.equal(r.manifest.safeStopPassed,
  false);
  assert.equal(r.manifest.result,
  'FAIL');
});
test('stopCurrent does not overwrite still-live process as stopped',
async t => {
  const dir=await mkdtemp(path.join(os.tmpdir(),
  'lab-stop-'));
  t.after(()=>rm(dir,
  {
    recursive:true,
    force:true
  }));
  await writeFile(path.join(dir,
  'current.json'),
  JSON.stringify({
    status:'DEBUG_READY',
    debugSessionId:'s',
    runId:'r',
    runSnapshotId:'ss',
    processEpoch:1,
    pid:123,
    runtimePid:123,
    runtimeStartedAtEpochMs:1000,
    runtimeCommandHint:'java',
    spawnedAtEpochMs:1000,
    launchCommand:'java',
    runDir:dir
  }));
  const config={
    schemaVersion:1,
    workspaceId:'x',
    workspaceDir:dir,
    runtimeRoot:dir,
    launch:{
      command:'node',
      args:[]
    }
  };
  const ops={
    inspect:async()=>({
      exists:true,
      pid:123,
      startedAtEpochMs:1000,
      commandLine:'java'
    }),
    terminate:async () => {
    },
    timeoutMs:30,
    pollMs:5
  };
  const got=await stopCurrent(config,
  dir,
  {
    processOperations:ops
  });
  assert.equal(got.ok,
  false);
  assert.equal(got.status,
  'STOP_INCOMPLETE');
  assert.equal(got.cleanup.status,
  'EXIT_TIMEOUT');
  assert.equal(JSON.parse(await readFile(path.join(dir,
  'current.json'),
  'utf8')).status,
  'STOP_INCOMPLETE');
});
import {
  buildEvidenceCut
} from '../../evidence/broker.mjs';
import {
  finalizeEvidenceRun
} from '../../evidence/finalize.mjs';
test('unsupported atomic/coherence labels cannot claim a barrier',
() => {
  const row={
    kind:'observation',
    debugSessionId:'s',
    runId:'r',
    runSnapshotId:'ss',
    processEpoch:1,
    arenaEpoch:1,
    resourceEpoch:1,
    lane:'SERVER_TICK',
    observedAt:'2026-10-01T00:00:00Z',
    writerId:'w',
    writerSeq:1,
    gameTime:1
  };
  for(const mode of ['ATOMIC_SNAPSHOT',
  'invented'])assert.equal(buildEvidenceCut([row],
  {
    coherenceMode:mode
  })
  .reason,
  'UNSUPPORTED_COHERENCE_MODE');
  for(const mode of ['LATEST_PER_LANE',
  'BEST_EFFORT',
  'BOUNDED_SKEW',
  'SAME_TICK_WHERE_AVAILABLE'])assert.equal(buildEvidenceCut([row],
  {
    coherenceMode:mode
  })
  .ok,
  true);
});
test('finalization rejects unknown process liveness',
async t => {
  const dir=await mkdtemp(path.join(os.tmpdir(),
  'lab-final-'));
  t.after(()=>rm(dir,
  {
    recursive:true,
    force:true
  }));
  await assert.rejects(finalizeEvidenceRun({
    runDir:dir,
    debugSessionId:'s',
    runId:'r',
    processEpoch:1,
    live:null
  }),
  /unverified|live/);
});

import { assertCurrentAllowsLaunch } from '../../core.mjs';

test('empty process identity cannot prove exit', async () => {
  const result = await verifyProcessesExited([], { inspect: async () => ({ exists: false }) });
  assert.equal(result.status, 'INSPECTION_UNKNOWN');
});

test('missing recorded PIDs cannot produce verified safe stop', async t => {
  const directory = await mkdtemp(path.join(os.tmpdir(), 'lab-missing-pid-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  await writeFile(path.join(directory, 'current.json'), JSON.stringify({
    status: 'DEBUG_READY', debugSessionId: 's', runId: 'r', runSnapshotId: 'ss',
    processEpoch: 1, pid: null, runtimePid: null, runDir: directory,
  }));
  const config = {
    schemaVersion: 1, workspaceId: 'x', workspaceDir: directory, runtimeRoot: directory,
    launch: { command: 'node', args: [] },
  };
  const result = await stopCurrent(config, directory);
  assert.equal(result.ok, false);
  assert.equal(result.cleanup.status, 'INSPECTION_UNKNOWN');
  assert.notEqual(result.live, false);
});

test('lost or unknown ownership quarantines subsequent launch', () => {
  assert.throws(() => assertCurrentAllowsLaunch({
    live: false, current: { status: 'OWNERSHIP_LOST' }, processes: { anyObservedUnowned: true },
  }), /reconciliation|unverified/);
  assert.throws(() => assertCurrentAllowsLaunch({
    live: false, current: { status: 'OWNERSHIP_LOST' }, processes: { anyObservedUnowned: false },
  }), /reconciliation|unverified/);
  assert.doesNotThrow(() => assertCurrentAllowsLaunch({
    live: false, current: { status: 'STOPPED' }, processes: { anyObservedUnowned: false },
  }));
});
