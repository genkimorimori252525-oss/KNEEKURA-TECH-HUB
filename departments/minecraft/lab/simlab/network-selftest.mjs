import assert from 'node:assert/strict';
import { parseNetworkCompanionText } from './network-companion.mjs';

const valid = [
  JSON.stringify({v:1,ch:'net_meta',scenario:'tank',run:'run-42',bound:true,physicalSide:'CLIENT',pid:'1',startedGameTime:100}),
  JSON.stringify({v:1,ch:'net',seq:1,stage:'send',physicalSide:'DEDICATED_SERVER',gameTime:101,thread:'Server thread',channel:'touhou_little_maid:reimu_net',packet:'demo.ReimuPacket',packetSimple:'ReimuPacket',direction:'PLAY_TO_CLIENT',payload:{x:1.25,molangExpression:'(v.wuqi = 1)',enabled:true}}),
  JSON.stringify({v:1,ch:'net',seq:2,stage:'receive',physicalSide:'CLIENT',gameTime:102,thread:'Render thread',packet:'demo.ReimuPacket',packetSimple:'ReimuPacket',direction:'PLAY_TO_CLIENT',payload:{molangExpression:'(v.wuqi = 1)'}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:3,kind:'reimu_spellcard_handler',physicalSide:'CLIENT',gameTime:102,thread:'Render thread',payload:{x:1.25,molangExpression:'(v.wuqi = 1)',packetTraceId:17}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:4,kind:'ysm_molang_command_pre_dispatch',physicalSide:'CLIENT',gameTime:103,thread:'Render thread',payload:{molangExpression:'(v.wuqi = 1)',command:'ysmclient molang execute (v.wuqi = 1)',packetHandlerOrigin:true,packetTraceIds:'17'}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:5,kind:'ysm_molang_command_dispatched',physicalSide:'CLIENT',gameTime:104,thread:'Render thread',payload:{molangExpression:'(v.wuqi = 1)',command:'ysmclient molang execute (v.wuqi = 1)',packetHandlerOrigin:true}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:6,kind:'ysm_client_command_result',physicalSide:'CLIENT',gameTime:104,thread:'Render thread',payload:{molangExpression:'(v.wuqi = 1)',handledByClient:true}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:7,kind:'ysm_state_correlated',physicalSide:'CLIENT',gameTime:106,thread:'Render thread',payload:{variable:'wuqi',observedValue:1,controlledE2Qualified:false,evidenceLevel:'E2_ACTUAL_PRE_POST_TRANSITION_UNQUALIFIED'}}),
  JSON.stringify({v:1,ch:'net_semantic',seq:8,kind:'ysm_molang_state_applied',physicalSide:'CLIENT',gameTime:116,thread:'Render thread',payload:{variable:'wuqi',before:0,after:1,handledByClient:true,packetHandlerOrigin:true,packetTraceIds:'17',controlledE2Qualified:true,evidenceLevel:'E2_ACTUAL_PRE_POST_TRANSITION'}})
].join('\n');

const parsed = parseNetworkCompanionText(valid, 'valid.net.jsonl');
assert.equal(parsed.meta.run, 'run-42');
assert.equal(parsed.sendCount, 1);
assert.equal(parsed.receiveCount, 1);
assert.equal(parsed.semanticCount, 6);
assert.equal(parsed.minGameTime, 101);
assert.equal(parsed.maxGameTime, 116);
assert.equal(parsed.events[0].channel, 'touhou_little_maid:reimu_net');
assert.equal(parsed.events[0].payload.molangExpression, '(v.wuqi = 1)');
assert.equal(parsed.semantics[0].kind, 'reimu_spellcard_handler');
assert.equal(parsed.semantics[1].kind, 'ysm_molang_command_pre_dispatch');
assert.equal(parsed.semantics[0].payload.packetTraceId, 17);
assert.equal(parsed.semantics[1].payload.packetHandlerOrigin, true);
assert.equal(parsed.semantics[1].payload.packetTraceIds, '17');
assert.equal(parsed.semantics[5].kind, 'ysm_molang_state_applied');
assert.equal(parsed.semantics[5].payload.controlledE2Qualified, true);
assert.equal(parsed.semantics[5].payload.packetTraceIds, '17');
assert.equal(parsed.semantics[5].payload.before, 0);
assert.equal(parsed.semantics[5].payload.after, 1);

assert.throws(
  ()=>parseNetworkCompanionText(JSON.stringify({v:1,ch:'net',seq:1,stage:'send',packet:'x',gameTime:1})),
  /first row must be ch=net_meta/
);

assert.throws(
  ()=>parseNetworkCompanionText([
    JSON.stringify({v:1,ch:'net_meta',scenario:'x',run:'r',physicalSide:'CLIENT'}),
    JSON.stringify({v:1,ch:'net',seq:1,stage:'maybe',packet:'x',gameTime:1})
  ].join('\n')),
  /stage must be send or receive/
);

assert.throws(
  ()=>parseNetworkCompanionText([
    JSON.stringify({v:1,ch:'net_meta',scenario:'x',run:'r',physicalSide:'CLIENT'}),
    JSON.stringify({v:1,ch:'net',seq:2,stage:'send',packet:'x',gameTime:1}),
    JSON.stringify({v:1,ch:'net_semantic',seq:2,kind:'handler',gameTime:2})
  ].join('\n')),
  /strictly increasing/
);

assert.throws(
  ()=>parseNetworkCompanionText([
    JSON.stringify({v:1,ch:'net_meta',scenario:'x',run:'r',physicalSide:'CLIENT'}),
    JSON.stringify({v:1,ch:'net',seq:1,stage:'receive',packet:'x',gameTime:1,payload:{nested:{bad:true}}})
  ].join('\n')),
  /payload\.nested must be a scalar/
);

assert.throws(
  ()=>parseNetworkCompanionText([
    JSON.stringify({v:1,ch:'net_meta',scenario:'x',run:'r',physicalSide:'CLIENT'}),
    JSON.stringify({v:1,ch:'net_semantic',seq:1,gameTime:1,payload:{value:'x'}})
  ].join('\n')),
  /semantic kind is required/
);

console.log('network companion selftest OK');
