import test from 'node:test';
import assert from 'node:assert/strict';
import {motionOverlayLaunchEnvironment} from '../../motion-overlay-launch.mjs';
import {validateConfig} from '../../core.mjs';
test('native Motion overlay is explicit/default OFF and inherited environment cannot arm it',()=>{
 const base={schemaVersion:1,workspaceId:'test',workspaceDir:'workspace',launch:{command:'gradlew.bat',args:['runClient']}};
 const config=validateConfig(base,process.cwd()).config;
 assert.equal(config.motionOverlay,false);
 assert.deepEqual(motionOverlayLaunchEnvironment(config),{KNEEKURA_DEBUG_MOTION_OVERLAY:'0'});
 assert.deepEqual(motionOverlayLaunchEnvironment({...config,motionOverlay:true}),{KNEEKURA_DEBUG_MOTION_OVERLAY:'1'});
 assert.equal(validateConfig({...base,motionOverlay:'true'},process.cwd()).ok,false);
});
