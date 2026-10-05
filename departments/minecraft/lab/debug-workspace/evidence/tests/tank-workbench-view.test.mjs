import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {buildCursorDecisionPacket} from '../cursor-decision.mjs';
import {buildTankMap} from '../tank-map.mjs';
import {packTankWorkbenchData,renderTankWorkbenchHtml,writeTankWorkbenchArtifact} from '../tank-workbench-view.mjs';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
const subjectUuid='00000000-0000-0000-0000-000000000001';
const status={schema:'kneekura.tank-status/v1',identity,geometry:{value:{x:0,y:64,z:0,width:16,height:8,depth:16},sourceObservationIds:[]},presentation:{reason:'NOT_CAPTURED'}};
const packet=buildCursorDecisionPacket({observations:[],identity,subjectUuid,window:{startTick:100,endTick:110},cursorTick:105});
const input={status,preflight:null,cursorPackets:[packet],map:buildTankMap({status,positions:[]}),experiment:null,comparison:null};
test('standalone workbench keeps shared data once, escapes script content and defaults layers OFF',()=>{
  const shared={...packet,cursorTick:106},data=packTankWorkbenchData({...input,cursorPackets:[packet,shared]});
  assert.equal(data.roots.cursorPackets.length,2);assert(data.nodes.length>0);
  const malicious=structuredClone(input);malicious.status.presentation.reason='</script><script>window.pwned=true</script>';
  const html=renderTankWorkbenchHtml(malicious);
  assert(html.includes('\\u003c/script>'));assert(!html.includes('</script><script>window.pwned=true'));
  assert(html.includes('Content-Security-Policy'));assert(!html.includes('innerHTML'));assert(!html.includes('fetch('));
  assert(!html.includes(' checked'));assert(html.includes('PLAN_XZ'));assert(html.includes('ELEVATION'));
});
test('workbench rejects oversized data, foreign context and too many cursors explicitly',()=>{
  assert.throws(()=>packTankWorkbenchData({...input,cursorPackets:Array(257).fill(packet)}),/CURSOR_LIMIT/);
  assert.throws(()=>packTankWorkbenchData({...input,status:{...status,large:'x'.repeat(262144)}}),/BYTE_BUDGET/);
  assert.throws(()=>packTankWorkbenchData({...input,cursorPackets:[{...packet,identity:{...identity,runId:'other'}}]}),/IDENTITY/);
  assert.throws(()=>packTankWorkbenchData({...input,cursorPackets:[packet,{...packet,identity:{...packet.identity,subjectUuid:'other'}}]}),/SUBJECT/);
  assert.throws(()=>packTankWorkbenchData({...input,cursorPackets:[packet,{...packet,identity:{...packet.identity,targetRevision:2}}]}),/SUBJECT/);
  assert.throws(()=>packTankWorkbenchData({...input,cursorPackets:[{...packet,dimension:'minecraft:the_nether'}]}),/DIMENSION/);
});
test('workbench output cannot append to retained run or overwrite existing output',async t=>{
  const root=await mkdtemp(path.join(os.tmpdir(),'tank-workbench-test-'));t.after(()=>rm(root,{recursive:true,force:true}));
  const runDir=path.join(root,'run');await mkdir(runDir);
  await assert.rejects(writeTankWorkbenchArtifact(input,path.join(runDir,'view.html'),runDir),/OUTSIDE/);
  const output=path.join(root,'view.html');await writeTankWorkbenchArtifact(input,output,runDir);
  const before=await readFile(output,'utf8');await assert.rejects(writeTankWorkbenchArtifact(input,output,runDir),{code:'EEXIST'});
  assert.equal(await readFile(output,'utf8'),before);
});
