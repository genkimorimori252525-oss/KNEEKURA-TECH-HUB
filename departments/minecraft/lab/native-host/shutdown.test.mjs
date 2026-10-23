import test from 'node:test';
import assert from 'node:assert/strict';
import {validateTerminalAck} from './shutdown.mjs';
const current={debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,cleanup:{status:'VERIFIED_EXIT'}};
const ack={v:1,debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,clean:true,status:'CLEAN_EVIDENCE_SHUTDOWN',worldStopped:true,writerDroppedTotal:0,remainingQueue:0,finalWriterSeq:2,ackedAt:new Date().toISOString()};
test('accept actual retained clean ACK only after independent owned exit proof',()=>assert.equal(validateTerminalAck(current,ack).clean,true));
for(const [key,value] of [['v',2],['debugSessionId','other'],['runId','other'],['runSnapshotId','other'],['processEpoch',2],['clean',false],['status','UNKNOWN'],['worldStopped',false],['writerDroppedTotal',1],['remainingQueue',1],['finalWriterSeq',0],['ackedAt','invalid']])test('reject ACK '+key,()=>assert.throws(()=>validateTerminalAck(current,{...ack,[key]:value})));
test('ACK cannot substitute for process ownership or verified exit',()=>{for(const status of ['UNKNOWN','INSPECTION_UNKNOWN','OWNERSHIP_CHANGED'])assert.throws(()=>validateTerminalAck({...current,cleanup:{status}},ack));});
