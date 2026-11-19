import {sha256,stableJson,decodeJson} from '../bridge/json.mjs';
import {sameTankIdentity} from './tank-contract.mjs';

/** Exact existing export bytes and original canonical effect, never a declared tick alone. */
export function verifyExperimentAlignment({alignment,request,actionReceipts,receiptBlobs=[],observations,identity,window}) {
  const unknown={status:'UNVERIFIED',condition:null,evidenceRefs:[]};
  if(!alignment||!Number.isSafeInteger(alignment.anchorTick)||!Array.isArray(receiptBlobs)||receiptBlobs.length>128)return unknown;
  const receipt=actionReceipts.find(r=>r.status==='APPLIED'&&r.evidence_hash===alignment.actionReceiptHash);
  const action=[...(request.initial_state??[]),...(request.actions??[])].find(r=>r.action_id===receipt?.action_id);
  if(!receipt||!action)return unknown;
  const blobs=new Map();for(const b of receiptBlobs){if(!Buffer.isBuffer(b.bytes)||b.bytes.length>2*1024*1024||sha256(b.bytes)!==b.contentHash)throw new TypeError('ALIGNMENT_BLOB_HASH_OR_SIZE');blobs.set(b.contentHash,b.bytes);}
  const bytes=blobs.get(receipt.evidence_hash);if(!bytes)return unknown;
  const body=decodeJson(bytes,2*1024*1024);
  if(body.kind!=='lab_action_receipt_export'||body.actionId!==action.action_id||body.reportedStatus!=='APPLIED'
    ||['debugSessionId','runId','runSnapshotId','processEpoch'].some(k=>body.identity?.[k]!==identity[k])||!Array.isArray(body.effectEvidence)||body.effectEvidence.length>128)return unknown;
  for(const ref of body.effectEvidence){
    const effectBytes=blobs.get(ref.contentHash);if(!effectBytes)continue;
    const effect=decodeJson(effectBytes,2*1024*1024),original=observations.find(r=>r.observationId===ref.observationId);
    if(!original||effect.observationId!==original.observationId||!sameTankIdentity(original,identity)||!sameTankIdentity(effect,identity)
      ||original.lane!=='ACTION_APPLIED'||effect.lane!=='ACTION_APPLIED'||original.source?.side!=='SERVER'||effect.source?.side!=='SERVER'
      ||original.epistemicStatus!=='OBSERVED'||effect.epistemicStatus!=='OBSERVED'||original.completeness?.complete!==true||effect.completeness?.complete!==true
      ||original.gameTime!==alignment.anchorTick||effect.gameTime!==original.gameTime||original.payload?.actionId!==action.action_id
      ||original.payload?.postconditionMatched!==true||stableJson(effect.payload)!==stableJson(original.payload))continue;
    const {action_id,operation,...args}=action;
    return {status:'VERIFIED_RETAINED_ACTION_EFFECT',condition:{actionId:action_id,operation,args,
      windowStartOffset:window.startTick-original.gameTime,windowEndOffset:window.endTick-original.gameTime},
      anchorTick:original.gameTime,actionReceiptHash:receipt.evidence_hash,evidenceRefs:[original.observationId]};
  }
  return unknown;
}
