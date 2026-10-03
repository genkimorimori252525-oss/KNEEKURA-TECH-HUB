import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {motionOverlayLaunchEnvironment} from '../../motion-overlay-launch.mjs';

test('native renderer forwards actual Cardinal quiescence before acquiring a drawing buffer',async()=>{
  const source=await readFile(new URL('../../forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugMotionOverlay.java',import.meta.url),'utf8');
  assert.ok(/camera\.z,KneekuraDebugCardinalCapture\.quiescent\(\)\)/.test(source),'Renderer must forward actual raw-capture quiescence');
  assert.ok(source.indexOf('KneekuraDebugCardinalCapture.quiescent()')<source.indexOf('buffers.getBuffer(RenderType.lines())'));
});
import {validateConfig} from '../../core.mjs';
test('native Motion overlay is explicit/default OFF and inherited environment cannot arm it',()=>{
 const base={schemaVersion:1,workspaceId:'test',workspaceDir:'workspace',launch:{command:'gradlew.bat',args:['runClient']}};
 const config=validateConfig(base,process.cwd()).config;
 assert.equal(config.motionOverlay,false);
 assert.deepEqual(motionOverlayLaunchEnvironment(config),{KNEEKURA_DEBUG_MOTION_OVERLAY:'0'});
 assert.deepEqual(motionOverlayLaunchEnvironment({...config,motionOverlay:true}),{KNEEKURA_DEBUG_MOTION_OVERLAY:'1'});
 assert.equal(validateConfig({...base,motionOverlay:'true'},process.cwd()).ok,false);
});
