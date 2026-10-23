import assert from 'node:assert/strict';
/** A real retained ACK is acceptable only with separately verified process exit. */
export function validateTerminalAck(current,ack){
 assert.equal(current.cleanup?.status,'VERIFIED_EXIT','TANK_EXIT_UNVERIFIED');assert.equal(ack.v,1);
 for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])assert(current[key]!=null&&current[key]===ack[key],'TANK_ACK_IDENTITY_'+key);
 assert.equal(ack.clean,true);assert.equal(ack.status,'CLEAN_EVIDENCE_SHUTDOWN');assert.equal(ack.worldStopped,true);assert.equal(ack.writerDroppedTotal,0);assert.equal(ack.remainingQueue,0);assert(Number.isInteger(ack.finalWriterSeq)&&ack.finalWriterSeq>=1);assert(Number.isFinite(Date.parse(ack.ackedAt)),'TANK_ACK_TIMESTAMP');
 return structuredClone(ack);
}
