import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const base=new URL('../../forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/',import.meta.url);
test('real Forge adapter uses guarded exact UUID mutations and bounded measured reset',async()=>{
 const source=await readFile(new URL('KneekuraDebugForgeArenaBackend.java',base),'utf8');
 for(const api of ['isSameThread()', 'getEntity(', 'setBlock(', 'getBlockState(', 'teleportTo(', 'getBlockEntity(', 'isLoaded(', 'restoreBaseline()', 'getWorldData().getLevelName()']) assert.ok(source.includes(api),api);
 assert.ok(!source.includes('teleportToWithTicket')&&!source.includes('setChunkForced')&&!source.includes('performPrefixedCommand'));
 assert.ok(source.includes('instanceof Player')&&source.includes('POSTCONDITION_MISMATCH'));
});
test('runtime remains gated without external command transport',async()=>{
 const source=await readFile(new URL('KneekuraDebugArenaRuntime.java',base),'utf8');
 assert.ok(source.includes('installOwner')&&source.includes('uninstallOwner'));
 assert.ok(source.includes('LIVE_AUTHORIZATION_MISSING')&&source.includes('RUNTIME_ATTESTATION_NOT_ESTABLISHED'));
 assert.ok(!source.includes('System.getenv')&&!source.includes('readString')&&!source.includes('HttpServer'));
 const cli=await readFile(new URL('../../cli.mjs',import.meta.url),'utf8');
 assert.ok(!cli.includes('arena-action')&&!cli.includes('arena-install'));
});
test('Arena evidence has asynchronous durable acknowledgement on the existing writer',async()=>{
 const source=await readFile(new URL('KneekuraDebugEvidenceWriter.java',base),'utf8');
 assert.ok(source.includes('recordArenaObservedAsync')&&source.includes('CompletableFuture<String>'));
 const durability=await readFile(new URL('KneekuraDebugDurability.java',base),'utf8');
 assert.ok(source.includes('KneekuraDebugDurability.write')&&durability.includes('force(true)')&&source.includes('arenaEpoch'));
});
