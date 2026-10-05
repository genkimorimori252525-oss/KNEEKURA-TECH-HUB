import path from 'node:path';
import {readRegisteredFile} from './bridge/materials.mjs';
import {decodeJson} from './bridge/json.mjs';
import {readFinalizedSources} from './bridge/result-export-source.mjs';
import {exportFinalizedExperiment} from './bridge/result-export.mjs';
import {buildExperimentDigest} from './evidence/experiment-digest.mjs';
import {requireTankObservations} from './evidence/tank-contract.mjs';
import {canonicalVisualSource} from './evidence/visual-compiler.mjs';
import {readRawVisualImage} from './evidence/visual-capture.mjs';

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
  const captures=source.rows.filter(r=>r.row.arenaEpoch===arenaEpoch&&r.row.lane==='VISUAL_CAPTURE'&&r.row.payload?.subjects?.includes(subjectUuid));
  if(captures.length>16)throw new RangeError('EXPERIMENT_CAPTURE_REFERENCE_LIMIT');
  const captureLinks=[];
  for(const entry of captures){
    const visual=await canonicalVisualSource({store:source.store,sourceObservationId:entry.row.observationId});
    for(const frame of visual.manifest.frames){
      if(source.inventory.has(frame.imagePath))await source.retained(frame.imagePath,16*1024*1024);
      // Legacy inventory seals the canonical manifest containing the exact raw image hash.
      try {await readRawVisualImage(runDir,frame);}catch(error){if(error.code==='ENOENT')continue;throw error;}
      captureLinks.push({sourceObservationId:entry.row.observationId,captureTick:frame.serverGameTime,view:frame.view,imageHash:frame.imageHash,
        imagePath:frame.imagePath,status:'VERIFIED_SEALED_CAPTURE_REFERENCE',relationship:'SAME_TICK_CONTEXT_NOT_EVENT_CAUSE'});
    }
  }
  const digest=buildExperimentDigest({request:source.request,identity,window,
    actionReceipts:exported.result.execution.action_receipts,
    observations:source.rows.map(r=>r.row).filter(r=>r.arenaEpoch===arenaEpoch),
    limits:{...context,receiptBlobs:exported.blobs,sourceBinding:{verifiedCanonical:true,verifiedRequestBinding:true,canonicalFileHash:source.canonicalFile.sha256,
      finalizationHash:source.finalFile.sha256,requestHash:source.requestHash,assertionsHash:source.binding.assertions_hash,
      contextHash:contextRelative?source.inventory.get(contextRelative).sha256:null},health:source.finalization.counts,
      cleanup:exported.result.execution.cleanup,captureLinks}});
  // Keep the existing evaluator's conservative statuses; no new implicit assertion engine.
  for(const a of digest.registeredAssertions)a.status=exported.result.assertions.find(r=>r.assertion_id===a.assertion_id)?.status??'INCONCLUSIVE';
  return {digest,source,exported,requestBytes,assertionsBytes};
}
