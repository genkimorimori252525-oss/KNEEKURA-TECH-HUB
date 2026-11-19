import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

// Regression: production-built mapped-dev MODs carry SRG refmaps. Without ForgeGradle's dev remapping the
// injectors fail with InvalidInjectionException and consumers had to hand-edit the refmap inside the JAR.
const gradle=await fs.readFile(path.join(path.dirname(fileURLToPath(import.meta.url)),'host/build.gradle'),'utf8');
const client=gradle.slice(gradle.indexOf('client {'),gradle.indexOf('repositories {'));
test('client run remaps SRG refmaps like the ForgeGradle MDK, for every trial',()=>{
 assert.match(client,/property 'mixin\.env\.remapRefMap', 'true'/);
 assert.match(client,/property 'mixin\.env\.refMapRemappingFile', srgToMcpFile\.absolutePath/);
 assert.match(gradle,/def srgToMcpFile = file\('build\/createSrgToMcp\/output\.srg'\)/);
 assert.doesNotMatch(client.slice(0,client.indexOf('mixin.env.remapRefMap')),/if \(profile\)\s*\{[^}]*$/,'remapping must not be conditional on a profile field');
});
test('preparation produces the remapping file and launch fails closed without it',()=>{
 assert.match(gradle,/tasks\.register\('writeTankResolved'\) \{\s*dependsOn 'createSrgToMcp'/);
 const run=gradle.slice(gradle.indexOf("tasks.matching { it.name == 'runClient' }"));
 assert.match(run,/if \(!srgToMcpFile\.isFile\(\)\) throw new GradleException\('TANK_REFMAP_REMAPPING_FILE_MISSING/);
});
