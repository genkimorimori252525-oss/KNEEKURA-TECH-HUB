import assert from 'node:assert/strict';
import { parseNetworkCompanionText } from './network-companion.mjs';
import { evaluateM6Acceptance } from './m6-acceptance-check.mjs';

function row(seq, after, traceId, extra={}) {
  return JSON.stringify({
    v:1,
    ch:'net_semantic',
    seq,
    kind:'ysm_molang_state_applied',
    physicalSide:'CLIENT',
    gameTime:100+seq,
    thread:'Render thread',
    payload:{
      variable:'wuqi',
      before:after===0?1:0,
      after,
      expectedValue:after,
      observedValue:after,
      entityUuid:'11111111-2222-3333-4444-555555555555',
      controlledE2Qualified:true,
      packetHandlerOrigin:true,
      handledByClient:true,
      exactVariableIdentity:true,
      packetTraceIds:String(traceId),
      evidenceLevel:'E2_ACTUAL_PRE_POST_TRANSITION',
      ...extra
    }
  });
}

function fixture(rows) {
  return [
    JSON.stringify({
      v:1,ch:'net_meta',scenario:'ysm-compat',run:'run-accept',bound:true,
      physicalSide:'CLIENT',pid:'1',startedGameTime:100
    }),
    ...rows
  ].join('\n');
}

const ok=parseNetworkCompanionText(fixture([
  row(1,0,11), row(2,1,12), row(3,0,13), row(4,1,14)
]));
const pass=evaluateM6Acceptance(ok,'v.wuqi');
assert.equal(pass.pass,true);
assert.deepEqual(pass.observed,[0,1,0,1]);
assert.deepEqual(pass.packetTraceIds,['11','12','13','14']);

const weak=parseNetworkCompanionText(fixture([
  row(1,0,11),
  JSON.stringify({
    v:1,ch:'net_semantic',seq:2,kind:'ysm_state_correlated',
    physicalSide:'CLIENT',gameTime:102,thread:'Render thread',
    payload:{variable:'wuqi',after:1,controlledE2Qualified:false}
  }),
  row(3,0,13), row(4,1,14)
]));
assert.equal(evaluateM6Acceptance(weak,'wuqi').pass,false);

const unbound=parseNetworkCompanionText([
  JSON.stringify({
    v:1,ch:'net_meta',scenario:'ysm-compat',run:'unbound',bound:false,
    physicalSide:'CLIENT',pid:'1',startedGameTime:100
  }),
  row(1,0,11), row(2,1,12), row(3,0,13), row(4,1,14)
].join('\n'));
assert.equal(evaluateM6Acceptance(unbound,'wuqi').pass,false);

const serverSide=parseNetworkCompanionText([
  JSON.stringify({
    v:1,ch:'net_meta',scenario:'ysm-compat',run:'run-accept',bound:true,
    physicalSide:'DEDICATED_SERVER',pid:'1',startedGameTime:100
  }),
  row(1,0,11), row(2,1,12), row(3,0,13), row(4,1,14)
].join('\n'));
assert.equal(evaluateM6Acceptance(serverSide,'wuqi').pass,false);

const repeatedTrace=parseNetworkCompanionText(fixture([
  row(1,0,11), row(2,1,11), row(3,0,13), row(4,1,14)
]));
assert.equal(evaluateM6Acceptance(repeatedTrace,'wuqi').pass,false);

const wrong=parseNetworkCompanionText(fixture([
  row(1,0,11), row(2,1,12), row(3,1,13), row(4,0,14), row(5,1,15)
]));
assert.equal(evaluateM6Acceptance(wrong,'wuqi').pass,false);

console.log('m6-acceptance-selftest OK');
