import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';

test('CLI leaves burst OFF and uses bounded explicit opt-in defaults',()=>{
  assert.equal(decisionBurstFromArgs([]),null);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst']),{ticks:100,maxEvents:256,maxBytes:262144,maxNodes:32,
    channels:['goal','brain','path','control','malus','sensor']});
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-ticks','10','--decision-channels','path,malus']).channels,['path','malus']);
});
test('CLI rejects unarmed, missing, repeated and out-of-bound burst options',()=>{
  for(const args of [['--decision-ticks','10'],['--decision-burst','--decision-ticks'],
    ['--decision-burst','--decision-ticks','201'],['--decision-burst','--decision-ticks','NaN'],
    ['--decision-burst','--decision-ticks','1','--decision-ticks','2'],
    ['--decision-burst','--decision-channels','goal,goal'],['--decision-burst','--decision-channels','unknown']]) {
    assert.throws(()=>decisionBurstFromArgs(args));
  }
});
