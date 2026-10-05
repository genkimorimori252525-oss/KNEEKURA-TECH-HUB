import path from 'node:path';
import {readRegisteredFile} from './bridge/materials.mjs';
import {decodeJson} from './bridge/json.mjs';
import {readFinalizedSources} from './bridge/result-export-source.mjs';
import {exportFinalizedExperiment} from './bridge/result-export.mjs';
import {buildExperimentDigest} from './evidence/experiment-digest.mjs';
import {requireTankObservations} from './evidence/tank-contract.mjs';

async function bytes(file,maxBytes){const full=path.resolve(file);return (await readRegisteredFile({root:path.dirname(full),relativePath:path.basename(full),maxBytes})).bytes;}
/** Reuses the existing sealed inventory, exact request bytes and journal verifier. */
export async function readExperimentDigest({runDir,requestFile,assertionsFile,subjectUuid,targetRevision,arenaEpoch,window,actionKeys=[],contextRelative=null}) {
  const requestBytes=await bytes(requestFile,128*1024),assertionsBytes=await bytes(assertionsFile,256*1024);
  const source=await readFinalizedSources({runDir,requestBytes,assertionsBytes});
  requireTankObservations(source.rows);
  const exported=await exportFinalizedExperiment({runDir,requestBytes,assertionsBytes,actionKeys});
  const context=contextRelative?decodeJson((await source.retained(contextRelative,256*1024)).bytes):{};
  const identity={debugSessionId:source.identity.debugSessionId,runId:source.identity.runId,runSnapshotId:source.identity.runSnapshotId,
    processEpoch:source.identity.processEpoch,arenaEpoch,targetRevision,subjectUuid};
  const digest=buildExperimentDigest({request:source.request,identity,window,
    actionReceipts:exported.result.execution.action_receipts,
    observations:source.rows.map(r=>r.row).filter(r=>r.arenaEpoch===arenaEpoch),
    limits:{...context,sourceBinding:{verifiedCanonical:true,canonicalFileHash:source.canonicalFile.sha256,
      finalizationHash:source.finalFile.sha256,requestHash:source.requestHash,assertionsHash:source.binding.assertions_hash,
      contextHash:contextRelative?source.inventory.get(contextRelative).sha256:null},health:source.finalization.counts,
      cleanup:exported.result.execution.cleanup}});
  // Keep the existing evaluator's conservative statuses; no new implicit assertion engine.
  for(const a of digest.registeredAssertions)a.status=exported.result.assertions.find(r=>r.assertion_id===a.assertion_id)?.status??'INCONCLUSIVE';
  return {digest,source,exported,requestBytes,assertionsBytes};
}
