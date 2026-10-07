import test from 'node:test';
import assert from 'node:assert/strict';
import {spatialMapFromRoster,writeTankRosterSpatialMap} from '../tank-roster.mjs';
import * as fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';

const result=()=>({status:'PARTIAL',sampleIndex:0,evidenceHash:'a'.repeat(64),execution:'CANONICAL_STRUCTURED_EVIDENCE',roster:{
 serverTick:67,gameTime:123,min:[-16,224,0],max:[16,248,32],status:'PARTIAL',missingEntityNotAbsent:true,
 coverage:{allChunksLoaded:false,missingChunks:[[-1,1]],truncationReasons:['ENTITY_LIMIT']},
 entities:[{uuid:'00000000-0000-0000-0000-000000000001',entityType:'soutou_ghast:soutou_ghast',knownSubjectId:'<untrusted>',
 world:[-2,230,9.5],local:[14,6,9.5],aabbMin:[-4,230,7.5],aabbMax:[0,234,11.5],fullyContained:true}]
}});
test('retained map preserves source, positions, body, half-open bounds and partial gaps',()=>{
 const input=result(),before=structuredClone(input),m=spatialMapFromRoster(input);
 assert.deepEqual(input,before);assert.equal(m.artifactRole,'DERIVED_ARTIFACT');
 assert.equal(m.currentPositions,'UNKNOWN');assert.equal(m.sourceTick,67);assert.equal(m.sourceEvidenceHash,'a'.repeat(64));
 assert.match(m.html,/X\/Z/);assert.match(m.html,/X\/Y/);assert.match(m.html,/PARTIAL/);
 assert.match(m.html,/Missing residents are not absent/);assert.match(m.html,/ENTITY_LIMIT/);
 assert.match(m.html,/data-gap="-1,1"/);assert.match(m.html,/14, 6, 9.5/);assert.match(m.html,/-2, 230, 9.5/);
 assert.match(m.html,/data-aabb=/);assert.match(m.html,/&lt;untrusted&gt;/);assert.doesNotMatch(m.html,/<untrusted>/);
 assert.doesNotMatch(m.html,/<script|https?:\/\//);
});
test('no fabricated map for missing canonical evidence or contradictory completeness',()=>{
 for(const delta of [{status:'UNKNOWN'},{evidenceHash:null},{execution:'NOT_CONFIRMED'},{roster:null}])
  assert.throws(()=>spatialMapFromRoster({...result(),...delta}),/SPATIAL_MAP_VERIFIED_ROSTER_REQUIRED/);
 const r=result();r.roster.status='COMPLETE';assert.throws(()=>spatialMapFromRoster(r),/SPATIAL_MAP_VERIFIED_ROSTER_REQUIRED/);
});
test('derived writer rejects retained-run destinations before reading evidence',async()=>{
 await assert.rejects(writeTankRosterSpatialMap({runDir:process.cwd(),outputFile:process.cwd()+'/map.html'}),/SPATIAL_MAP_OUTSIDE_RUN_REQUIRED/);
});
test('unfinalized export rejects without initializing or ingesting the source run',async()=>{
 const parent=await fs.mkdtemp(path.join(os.tmpdir(),'tank-unfinalized-map-')),runDir=path.join(parent,'run');
 await fs.mkdir(path.join(runDir,'evidence/raw'),{recursive:true});
 await fs.writeFile(path.join(runDir,'evidence/raw/pending.jsonl'),'pending observation\n');
 const before=await fs.readdir(path.join(runDir,'evidence'),{recursive:true});
 await assert.rejects(writeTankRosterSpatialMap({runDir,outputFile:path.join(parent,'map.html')}),/SPATIAL_MAP_FINALIZED_RUN_REQUIRED/);
 assert.deepEqual(await fs.readdir(path.join(runDir,'evidence'),{recursive:true}),before);
 assert.equal(await fs.readFile(path.join(runDir,'evidence/raw/pending.jsonl'),'utf8'),'pending observation\n');
 await assert.rejects(fs.stat(path.join(parent,'map.html')),/ENOENT/);
});
