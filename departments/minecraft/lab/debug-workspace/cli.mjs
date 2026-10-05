#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {decisionBurstFromArgs} from './decision-burst-cli.mjs';
import {terrainQueryFromArgs} from './terrain-query-cli.mjs';
import {queryDecisionDrilldown} from './evidence/decision-drilldown.mjs';
import {buildRetainedDecisionPresentation} from './evidence/decision-presentation.mjs';
import {writeDecisionPresentationArtifact} from './evidence/decision-view.mjs';
import {readTankContext,readTankJsonFile,prepareTankResourceFile} from './tank-cli.mjs';
import {
  doctor,
  launchDebugRun,
  readCurrent,
  readStartupTimeline,
  stopCurrent,
  writeG1Acceptance
} from './core.mjs';
import { evidenceRuntimeFromCurrent } from './evidence/runtime.mjs';
import { watchOwnerTriggerCaptures } from './bridge/owner-trigger-source.mjs';
import {
  clearTargetControl,
  readTargetControl,
  setTargetControl
} from './evidence/target-control.mjs';
import { finalizeEvidenceRun } from './evidence/finalize.mjs';
import {
  G2_CORE_REQUIRED_LANES,
  planG2CaptureWindow,
  waitForG2Evidence,
  writeG2Acceptance
} from './evidence/g2-acceptance.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');

function argValue(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
}

async function loadConfig() {
  const explicit = argValue('--config') || process.env.KNEEKURA_DEBUG_CONFIG;
  const file = explicit
    ? (path.isAbsolute(explicit) ? explicit : path.resolve(ROOT, explicit))
    : path.join(HERE, 'config.local.json');
  try {
    const text = await readFile(file, 'utf8');
    return { file, config: JSON.parse(text) };
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      throw new Error(
        'debug config not found: ' + file + '\n' +
        'Copy debug-workspace/profiles/reimu-mod.example.json to ' +
        'debug-workspace/config.local.json and set workspaceDir to the local reimu-mod checkout.'
      );
    }
    throw error;
  }
}

function print(value) {
  process.stdout.write(JSON.stringify(value, null, 2) + '\n');
}

async function main() {
  const command = process.argv[2] || 'status';
  const { file, config } = await loadConfig();

  if(command==='tank-resource') {
    const required=name=>{const value=argValue(name);if(!value||value.startsWith('--'))throw new Error('MISSING_'+name);return value;};
    print(await prepareTankResourceFile({savedFile:required('--saved-recipe'),profileFile:required('--profile'),output:required('--output')}));return;
  }
  if(command==='tank-status'||command==='tank-preflight') {
    const required=name=>{const value=argValue(name);if(!value||value.startsWith('--'))throw new Error('MISSING_'+name);return value;};
    const current=await readCurrent(config,ROOT),runtime=evidenceRuntimeFromCurrent(current);await runtime.init();
    const observations=await runtime.store.readObservations();
    const context=await readTankContext({current,observations,arenaEpoch:Number(required('--arena-epoch')),
      expectedRecipeHash:argValue('--recipe-hash'),worldBinding:argValue('--world-binding')?await readTankJsonFile(required('--world-binding')):undefined,
      profile:command==='tank-preflight'?await readTankJsonFile(required('--profile')):undefined,
      timeBudget:command==='tank-preflight'?await readTankJsonFile(required('--time-budget')):undefined});
    print(command==='tank-status'?context.status:context.preflight);return;
  }

  if (command === 'doctor') {
    const result = await doctor(config, ROOT);
    print({ configFile: file, ...result });
    process.exitCode = result.ok ? 0 : 1;
    return;
  }

  if (command === 'start') {
    const result = await launchDebugRun(config, ROOT);
    print({ configFile: file, ...result });
    return;
  }

  if (command === 'status') {
    const result = await readCurrent(config, ROOT);
    print({ configFile: file, ...result });
    return;
  }

  if (command === 'target-status') {
    const current = await readCurrent(config, ROOT);
    const target = await readTargetControl(current);
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      live: current.live,
      target
    });
    return;
  }

  if (command === 'target') {
    const entityUuid = process.argv[3];
    if (!entityUuid || entityUuid.startsWith('--')) {
      throw new Error('target requires an entity UUID argument');
    }
    const current = await readCurrent(config, ROOT);
    if (current.live !== true) {
      throw new Error('cannot set target: debug runtime is not live');
    }
    const target = await setTargetControl(current, entityUuid, {
      decisionSnapshot: process.argv.includes('--decision-snapshot'),
      decisionBurst: decisionBurstFromArgs(process.argv.slice(4)),
      decisionTerrain: terrainQueryFromArgs(process.argv.slice(4)),
    });
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      target
    });
    return;
  }

  if (command === 'target-clear') {
    const current = await readCurrent(config, ROOT);
    if (current.live !== true) {
      throw new Error('cannot clear target: debug runtime is not live');
    }
    const target = await clearTargetControl(current);
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      target
    });
    return;
  }

  if(command === 'evidence-decision' || command === 'evidence-decision-view') {
    const subjectUuid=process.argv[3];
    const required=name=>{const value=argValue(name);if(value==null||!value.trim()||value.startsWith('--'))throw new Error('required decision option: '+name);return value;};
    const current=await readCurrent(config,ROOT);
    const runtime=evidenceRuntimeFromCurrent(current);
    // Retained canonical read only. Do not initialize, ingest or rewrite a finalized evidence run.
    const observations=await runtime.store.readObservations();
    const identity={debugSessionId:current.debugSessionId,runId:current.runId,runSnapshotId:current.runSnapshotId,
      processEpoch:current.processEpoch,arenaEpoch:Number(required('--arena-epoch')),targetRevision:Number(required('--revision'))};
    if(command === 'evidence-decision-view') {
      const result=buildRetainedDecisionPresentation({observations,subjectUuid,identity,
        request:{startTick:Number(required('--start-tick')),endTick:Number(required('--end-tick'))}});
      const output=argValue('--output');
      if(output!==null) {
        required('--output');
        // Create a separate derived artifact; never overwrite retained evidence or any existing file.
        const outputFile=await writeDecisionPresentationArtifact(result,output,current.runDir);
        print({schema:result.schema,identity:result.identity,outputFile,readOnlyRetainedEvidence:true});
      }else print(result);
      return;
    }
    const result=queryDecisionDrilldown({observations,subjectUuid,identity,
      request:{channel:required('--channel'),startTick:Number(required('--start-tick')),endTick:Number(required('--end-tick')),
        limit:Number(argValue('--limit')??64),maxNodes:Number(argValue('--max-nodes')??32)}});
    print(result);return;
  }

  if (command === 'evidence-trigger-watch') {
    const current = await readCurrent(config, ROOT);
    if (current.live !== true || !current.ownerControlIntent?.envelopeHash) throw new Error('LIVE_PREPARED_OWNER_REQUIRED');
    const runtime = evidenceRuntimeFromCurrent(current); await runtime.init();
    print(await watchOwnerTriggerCaptures(runtime, { envelopeHash: current.ownerControlIntent.envelopeHash }));
    return;
  }

  if (command === 'evidence-status') {
    const current = await readCurrent(config, ROOT);
    const runtime = evidenceRuntimeFromCurrent(current);
    await runtime.init();
    const result = await runtime.refresh();
    print({
      configFile: file,
      debugRuntime: {
        status: current.status,
        live: current.live,
        processEpoch: current.processEpoch,
        runtimePid: current.runtimePid ?? null
      },
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      ...result
    });
    return;
  }

  if (command === 'evidence-anomalies') {
    const current = await readCurrent(config, ROOT);
    const runtime = evidenceRuntimeFromCurrent(current);
    await runtime.init();
    const ingest = await runtime.ingestAvailable();
    const anomalies = await runtime.broker.anomalies();
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      ingest,
      anomalies
    });
    return;
  }

  if (command === 'evidence-entity') {
    const entityUuid = process.argv[3];
    if (!entityUuid || entityUuid.startsWith('--')) {
      throw new Error('evidence-entity requires an entity UUID argument');
    }
    const current = await readCurrent(config, ROOT);
    const runtime = evidenceRuntimeFromCurrent(current);
    await runtime.init();
    const ingest = await runtime.ingestAvailable();
    const entity = await runtime.broker.entityCurrent(entityUuid, {
      lanes: [
        'TARGET_TRACKED',
        'ENTITY_STATE',
        'SERVER_TARGET_TRACKED',
        'SERVER_ENTITY_STATE',
        'AI_TARGET',
        'BRAIN_MEMORY',
        'RUNNING_BEHAVIORS',
        'NAVIGATION',
        'TLM_STATE',
        'REIMU_STATE'
      ],
      coherenceMode: 'BOUNDED_SKEW',
      // TARGET_TRACKED is a stateful delta lane with a 100-tick keyframe.
      // ENTITY_STATE is sampled more frequently. Six seconds keeps the query
      // explicit about that forward-fill window instead of pretending the
      // two rows were observed in the same instant.
      maxSkewMs: 6000
    });
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      ingest,
      entity
    });
    process.exitCode = entity.ok ? 0 : 2;
    return;
  }

  if (command === 'evidence-gap') {
    const lane = process.argv[3];
    if (!lane || lane.startsWith('--')) {
      throw new Error('evidence-gap requires a lane argument');
    }
    const current = await readCurrent(config, ROOT);
    const runtime = evidenceRuntimeFromCurrent(current);
    await runtime.init();
    const ingest = await runtime.ingestAvailable();
    const gap = await runtime.broker.explainGap(lane);
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      ingest,
      gap
    });
    return;
  }

  if (command === 'evidence-capture') {
    const current = await readCurrent(config, ROOT);
    const runtime = evidenceRuntimeFromCurrent(current);
    await runtime.init();

    const preRollArg = argValue('--pre-roll-ms');
    const requestedPreRollMs =
      preRollArg == null ? 5000 : Number(preRollArg);
    if (!Number.isInteger(requestedPreRollMs) ||
        requestedPreRollMs < 0) {
      throw new Error('--pre-roll-ms must be an integer >= 0');
    }

    const entityUuid = argValue('--entity');
    const laneArg = argValue('--lanes');
    const lanes = laneArg
      ? laneArg.split(',').map((x) => x.trim()).filter(Boolean)
      : null;

    const capture = await runtime.capturePreRoll({
      requestedPreRollMs,
      entityUuid,
      lanes
    });
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      capture
    });
    process.exitCode =
      capture.manifest.coverage.truncated ? 2 : 0;
    return;
  }

  if (command === 'evidence-finalize') {
    const current = await readCurrent(config, ROOT);
    const cleanShutdown = current.evidenceShutdown?.clean === true;
    const result = await finalizeEvidenceRun(current, {
      cleanShutdown,
      shutdownMode: cleanShutdown
        ? 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
        : (current.status === 'STOPPED'
            ? 'FORCED_PROCESS_STOP'
            : 'UNACKNOWLEDGED_STOP')
    });
    print({
      configFile: file,
      debugSessionId: current.debugSessionId,
      runId: current.runId,
      finalization: result
    });
    process.exitCode =
      result.manifest.status === 'EVIDENCE_COMPLETE' ? 0 : 2;
    return;
  }

  if (command === 'g2-smoke') {
    const entityUuid = process.argv[3];
    if (!entityUuid || entityUuid.startsWith('--')) {
      throw new Error('g2-smoke requires an entity UUID argument');
    }

    const requireReimu = process.argv.includes('--require-reimu');
    const timeoutArg = argValue('--evidence-timeout-ms');
    const evidenceTimeoutMs =
      timeoutArg == null ? 15000 : Number(timeoutArg);
    if (!Number.isInteger(evidenceTimeoutMs) ||
        evidenceTimeoutMs < 1000) {
      throw new Error(
        '--evidence-timeout-ms must be an integer >= 1000'
      );
    }

    const d = await doctor(config, ROOT);
    if (!d.ok) {
      print({ configFile: file, stage: 'doctor', ...d });
      process.exitCode = 1;
      return;
    }

    let started = null;
    let timeline = null;
    let liveStatus = null;
    let target = null;
    let evidenceGate = null;
    let capture = null;
    let stopped = null;
    let finalization = null;
    let g1Acceptance = null;
    let g2Acceptance = null;
    let failure = null;

    try {
      started = await launchDebugRun(config, ROOT);
      timeline = await readStartupTimeline(config, ROOT);
      liveStatus = await readCurrent(config, ROOT);
      target = await setTargetControl(liveStatus, entityUuid);

      const runtime = evidenceRuntimeFromCurrent(liveStatus);
      await runtime.init();

      evidenceGate = await waitForG2Evidence({
        runtime,
        current: liveStatus,
        entityUuid: target.targetUuid,
        targetRevision: target.revision,
        requireReimu,
        timeoutMs: evidenceTimeoutMs
      });

      if (evidenceGate.ok) {
        const capturePlan = planG2CaptureWindow(
          evidenceGate,
          {
            minimumPreRollMs: 1000,
            maxPreRollMs: runtime.store.ring.maxAgeMs
          }
        );
        if (capturePlan.waitMs > 0) {
          await new Promise(
            (resolve) => setTimeout(resolve, capturePlan.waitMs)
          );
        }
        capture = await runtime.capturePreRoll({
          triggerAt: capturePlan.triggerAt,
          requestedPreRollMs: capturePlan.requestedPreRollMs,
          entityUuid: target.targetUuid,
          lanes: [
            ...G2_CORE_REQUIRED_LANES,
            ...(requireReimu ? ['REIMU_STATE'] : []),
            'BEHAVIOR_TRANSITION'
          ]
        });
      }
    } catch (error) {
      failure = {
        stage: 'live-observation',
        message: error.message
      };
    }

    try {
      stopped = await stopCurrent(config, ROOT);
    } catch (error) {
      failure = failure || {
        stage: 'stop',
        message: error.message
      };
    }

    if (stopped?.runDir) {
      try {
        const cleanShutdown =
          stopped.evidenceShutdown?.clean === true;
        finalization = await finalizeEvidenceRun(stopped, {
          cleanShutdown,
          shutdownMode: cleanShutdown
            ? 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
            : 'FORCED_PROCESS_STOP'
        });
      } catch (error) {
        failure = failure || {
          stage: 'finalization',
          message: error.message
        };
      }
    }

    if (started && timeline && liveStatus && stopped) {
      try {
        g1Acceptance = await writeG1Acceptance(
          config,
          ROOT,
          {
            started,
            timeline,
            status: liveStatus,
            stopped,
            finalization
          }
        );
      } catch (error) {
        failure = failure || {
          stage: 'g1-acceptance',
          message: error.message
        };
      }
    }

    if (started) {
      try {
        g2Acceptance = await writeG2Acceptance({
          started,
          timeline,
          liveStatus,
          target,
          evidenceGate,
          capture,
          stopped,
          finalization
        });
      } catch (error) {
        failure = failure || {
          stage: 'g2-acceptance',
          message: error.message
        };
      }
    }

    const ok =
      failure == null &&
      g1Acceptance?.manifest?.result === 'PASS' &&
      g2Acceptance?.manifest?.result === 'PASS';

    print({
      configFile: file,
      ok,
      failure,
      started,
      timeline,
      liveStatus,
      target,
      evidenceGate,
      capture,
      stopped,
      finalization,
      g1Acceptance,
      g2Acceptance
    });
    process.exitCode = ok ? 0 : 2;
    return;
  }

  if (command === 'smoke') {
    const d = await doctor(config, ROOT);
    if (!d.ok) {
      print({ configFile: file, stage: 'doctor', ...d });
      process.exitCode = 1;
      return;
    }

    let started = null;
    let timeline = null;
    let status = null;
    let stopped = null;
    let finalization = null;
    try {
      started = await launchDebugRun(config, ROOT);
      timeline = await readStartupTimeline(config, ROOT);
      status = await readCurrent(config, ROOT);
      stopped = await stopCurrent(config, ROOT);
      finalization = await finalizeEvidenceRun(stopped, {
        cleanShutdown: stopped.evidenceShutdown?.clean === true,
        shutdownMode: stopped.evidenceShutdown?.clean === true
          ? 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
          : 'FORCED_PROCESS_STOP'
      });

      const acceptance = await writeG1Acceptance(config, ROOT, {
        started,
        timeline,
        status,
        stopped,
        finalization
      });

      const ok = acceptance.manifest.result === 'PASS';

      print({
        configFile: file,
        ok,
        started,
        timeline,
        status,
        stopped,
        finalization,
        acceptance
      });
      process.exitCode = ok ? 0 : 2;
      return;
    } catch (error) {
      try {
        stopped = await stopCurrent(config, ROOT);
      } catch {
        stopped = null;
      }
      print({
        configFile: file,
        ok: false,
        stage: 'smoke',
        error: error.message,
        started,
        timeline,
        status,
        stopped
      });
      process.exitCode = 2;
      return;
    }
  }

  if (command === 'timeline') {
    const result = await readStartupTimeline(config, ROOT);
    print({ configFile: file, ...result });
    process.exitCode = result.ok ? 0 : 2;
    return;
  }

  if (command === 'stop') {
    const result = await stopCurrent(config, ROOT);
    let finalization = null;
    if (result.ok && result.runDir) {
      const cleanShutdown = result.evidenceShutdown?.clean === true;
      finalization = await finalizeEvidenceRun(result, {
        cleanShutdown,
        shutdownMode: cleanShutdown
          ? 'PROBE_FLUSH_ACK_THEN_PROCESS_STOP'
          : (result.status === 'STOPPED'
              ? 'FORCED_PROCESS_STOP'
              : 'UNACKNOWLEDGED_STOP')
      });
    }
    print({ configFile: file, ...result, finalization });
    process.exitCode = result.ok ? 0 : 2;
    return;
  }

  throw new Error('unknown command: ' + command + ' (expected doctor/start/status/timeline/smoke/g2-smoke/stop/target/target-clear/target-status/evidence-status/evidence-trigger-watch/evidence-anomalies/evidence-entity/evidence-decision/evidence-decision-view/evidence-gap/evidence-capture/evidence-finalize)');
}

main().catch((error) => {
  process.stderr.write('[kneekura-debug] ' + (error.stack || error.message || String(error)) + '\n');
  process.exitCode = 1;
});
