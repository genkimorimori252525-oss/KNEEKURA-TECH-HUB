import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import {decisionHookLaunchOptions} from '../../decision-hook-launch.mjs';
import {validateConfig} from '../../core.mjs';

test('deep hooks are OFF by default and inherited arming environment is overridden',()=>{
  const base={schemaVersion:1,workspaceId:'test',workspaceDir:'workspace',launch:{command:'gradlew.bat',args:['runClient']}};
  const config=validateConfig(base,process.cwd()).config;
  assert.equal(config.decisionHooks,false);
  const options=decisionHookLaunchOptions(config,process.cwd());
  assert.deepEqual(options.extraArgs,[]);
  assert.equal(options.env.KNEEKURA_DEBUG_DECISION_HOOKS,'0');
  assert.equal(options.env.KNEEKURA_DEBUG_DECISION_RESOURCES,'');
  assert.equal(validateConfig({...base,decisionHooks:'true'},process.cwd()).ok,false);
});
test('explicit deep hooks add only the LAB-owned init/resources for a Gradle debug launch',()=>{
  const base={schemaVersion:1,workspaceId:'test',workspaceDir:'workspace',decisionHooks:true,launch:{command:'gradlew.bat',args:['runClient']}};
  const config=validateConfig(base,process.cwd()).config;
  const options=decisionHookLaunchOptions(config,process.cwd());
  assert.equal(options.extraArgs[0],'--init-script');
  assert.equal(options.extraArgs[1],path.join(process.cwd(),'debug-workspace','forge-bridge','decision-hooks.init.gradle'));
  assert.equal(options.env.KNEEKURA_DEBUG_DECISION_HOOKS,'1');
  assert.equal(options.env.KNEEKURA_DEBUG_DECISION_RESOURCES,path.join(process.cwd(),'debug-workspace','forge-bridge','src','main','resources'));
  assert.throws(()=>decisionHookLaunchOptions({...config,launch:{command:'arbitrary-launcher'}},process.cwd()),/GRADLE_DEBUG_LAUNCH_REQUIRED/);
});
