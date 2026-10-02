import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createHash
} from 'node:crypto';
import {
  mkdtemp,
  writeFile,
  readFile,
  mkdir,
  symlink,
  rm
} from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {
  validateTechHubBinding,
  readBridgeInputs,
  registerBridgeRequest,
  loadBridgeRegistration
} from '../registration.mjs';
import {
  readRegisteredFile
} from '../materials.mjs';
import {
  prepareBridgeContext
} from '../../core.mjs';
import {
  access
} from 'node:fs/promises';
const hash = b => createHash('sha256').update(b).digest('hex');
async function fixture(t) {
  const root=await mkdtemp(path.join(os.tmpdir(),
  'lab-reg-'));
  t.after(()=>rm(root,
  {
    recursive:true,
    force:true
  }));
  const material={
    buildArtifact:'build',
    configArtifact:'config',
    resourceArtifact:'resources'
  };
  for(const [key,
  value] of Object.entries(material)) await writeFile(path.join(root,
  key),
  value);
  const target={
    profile_id:'a'.repeat(64),
    index_snapshot_id:'b'.repeat(64),
    build_artifact_hash:hash('build'),
    source_revision:'c'.repeat(40),
    dirty_hash:'d'.repeat(64),
    config_hash:hash('config'),
    resource_hash:hash('resources')
  };
  const assertions='[{"assertion_id":"x","expected":1.0,"kind":"structured","operator":"equals","field":"health","subject_id":"s"}]';
  const req={
    schema_version:1,
    experiment_id:'exp',
    generation:1,
    target,
    arena:{
      arena_id:'arena',
      preset:'normal',
      baseline_hash:'e'.repeat(64),
      bounds:{
        min:[0,
        0,
        0],
        max:[16,
        16,
        16]
      }
    },
    subjects:[{
      subject_id:'s',
      uuid:'00000000-0000-0000-0000-000000000001',
      entity_type:'minecraft:pig'
    }],
    initial_state:[],
    actions:[],
    observation_scopes:[{
      kind:'ENTITY_UUID',
      subject_id:'s',
      lanes:['SERVER_ENTITY_STATE'],
      level:'L1'
    }],
    visual_rig:{
      mode:'none'
    },
    budgets:{
      time_budget_ms:1000,
      max_actions:0,
      max_captures:0
    },
    assertions:JSON.parse(assertions)
  };
  // Deliberately retain Python float formatting and non-ASCII exact bytes.
  const request=JSON.stringify(req).replace('"expected":1,',
  '"expected":1.0,');
  const binding={
    schema_version:1,
    experiment_id:'exp',
    generation:1,
    request_hash:hash(request),
    target,
    arena_id:'arena',
    arena_baseline_hash:'e'.repeat(64),
    assertions_hash:hash(assertions)
  };
  await writeFile(path.join(root,
  'request.json'),
  request);
  await writeFile(path.join(root,
  'binding.json'),
  JSON.stringify(binding));
  await writeFile(path.join(root,
  'assertions.json'),
  assertions);
  const registration={
    schemaVersion:1,
    trustedRoot:root,
    requestFile:'request.json',
    bindingFile:'binding.json',
    assertionsFile:'assertions.json',
    materials:Object.fromEntries(Object.keys(material).map(k=>[k,
    {
      relativePath:k
    }]))
  };
  return {
    root,
    registration,
    binding,
    request,
    assertions,
    runtimeRoot:path.join(root,
    'runtime')
  };
}
test('exact raw request/assertions identity and disk-only material proof',
async t => {
  const f=await fixture(t);
  const got=await readBridgeInputs(f.registration);
  assert.equal(got.binding.request_hash,
  hash(f.request));
  assert.equal(got.binding.assertions_hash,
  hash(f.assertions));
  assert.equal(got.runtimeAttestation,
  'NOT_ESTABLISHED');
  assert.equal(got.materialInventory.buildArtifact.sha256,
  f.binding.target.build_artifact_hash);
  assert.notEqual(hash(JSON.stringify(JSON.parse(f.request))),
  f.binding.request_hash);
});
test('binding strict fields and bounded identifiers',
async t => {
  const f=await fixture(t);
  assert.deepEqual(validateTechHubBinding(f.binding),
  f.binding);
  for(const b of [{
    ...f.binding,
    executable:'bad'
  },
  {
    ...f.binding,
    generation:true
  },
  {
    ...f.binding,
    request_hash:'x'
  },
  {
    ...f.binding,
    target:{
      ...f.binding.target,
      command:'bad'
    }
  }])
  assert.throws(()=>validateTechHubBinding(b));
});
test('request assertion and binding drift fail closed',
async t => {
  const f=await fixture(t);
  await writeFile(path.join(f.root,
  'request.json'),
  f.request+' ');
  await assert.rejects(readBridgeInputs(f.registration),
  /REQUEST_HASH/);
});
test('duplicate JSON keys malformed UTF8 and unsafe numbers rejected',
async t => {
  const f=await fixture(t);
  for(const value of ['{"a":1,"a":2}',
  Buffer.from([0xc3,
  0x28]),
  '{"a":1e999}',
  '{"a":9007199254740992}']) {
    await writeFile(path.join(f.root,
    'binding.json'),
    value);
    await assert.rejects(readBridgeInputs(f.registration));
  }
});
test('assertion payload cannot differ while request hash still matches',
async t => {
  const f=await fixture(t);
  await writeFile(path.join(f.root,
  'assertions.json'),
  '[]');
  f.binding.assertions_hash=hash('[]');
  await writeFile(path.join(f.root,
  'binding.json'),
  JSON.stringify(f.binding));
  await assert.rejects(readBridgeInputs(f.registration),
  /ASSERTIONS/);
});
test('materials reject mutation missing file traversal symlink and oversize',
async t => {
  const f=await fixture(t);
  await writeFile(path.join(f.root,
  'buildArtifact'),
  'changed');
  await assert.rejects(readBridgeInputs(f.registration),
  /MATERIAL_HASH/);
  for(const name of ['../escape',
  '/absolute',
  'missing'])await assert.rejects(readRegisteredFile({
    root:f.root,
    relativePath:name,
    expectedSha256:'a'.repeat(64),
    maxBytes:4
  }));
  await symlink(path.join(f.root,
  'configArtifact'),
  path.join(f.root,
  'link'));
  await assert.rejects(readRegisteredFile({
    root:f.root,
    relativePath:'link',
    expectedSha256:hash('config'),
    maxBytes:10
  }),
  /SYMLINK/);
  await assert.rejects(readRegisteredFile({
    root:f.root,
    relativePath:'configArtifact',
    expectedSha256:hash('config'),
    maxBytes:2
  }),
  /SIZE/);
});
test('registration immutable idempotent and load revalidates artifact bytes',
async t => {
  const f=await fixture(t);
  const a=await registerBridgeRequest(f);
  const b=await registerBridgeRequest(f);
  assert.equal(a.registrationHash,
  b.registrationHash);
  const loaded=await loadBridgeRegistration({
    runtimeRoot:f.runtimeRoot,
    requestHash:f.binding.request_hash
  });
  assert.deepEqual(loaded.binding,
  f.binding);
  await writeFile(path.join(f.root,
  'configArtifact'),
  'changed');
  await assert.rejects(loadBridgeRegistration({
    runtimeRoot:f.runtimeRoot,
    requestHash:f.binding.request_hash
  }),
  /MATERIAL_HASH/);
});
test('concurrent reservation never overwrites and incomplete registration rejects',
async t => {
  const f=await fixture(t);
  const results=await Promise.allSettled([registerBridgeRequest(f),
  registerBridgeRequest(f)]);
  assert.ok(results.some(x=>x.status==='fulfilled'));
  const a=await loadBridgeRegistration({
    runtimeRoot:f.runtimeRoot,
    requestHash:f.binding.request_hash
  });
  assert.equal(a.binding.request_hash,
  f.binding.request_hash);
  await rm(path.join(a.directory,
  'registration.json'));
  await assert.rejects(loadBridgeRegistration({
    runtimeRoot:f.runtimeRoot,
    requestHash:f.binding.request_hash
  }),
  /REGISTRATION_INCOMPLETE/);
});
test('registration rejects missing exact request fields even with matching digest',
async t => {
  const f=await fixture(t);
  const request=JSON.parse(f.request);
  delete request.actions;
  const bytes=JSON.stringify(request);
  f.binding.request_hash=hash(bytes);
  await writeFile(path.join(f.root,
  'request.json'),
  bytes);
  await writeFile(path.join(f.root,
  'binding.json'),
  JSON.stringify(f.binding));
  await assert.rejects(readBridgeInputs(f.registration),
  /REQUEST.*FIELDS/);
});
test('loading an absent registry is read-only',
async t => {
  const f=await fixture(t);
  await assert.rejects(loadBridgeRegistration({
    runtimeRoot:f.runtimeRoot,
    requestHash:f.binding.request_hash
  }));
  await assert.rejects(access(f.runtimeRoot));
});
test('snapshot preparation requires exact clean source and current disk material',
async t => {
  const f=await fixture(t);
  await registerBridgeRequest(f);
  const source={
    available:true,
    commit:f.binding.target.source_revision,
    dirty:false
  };
  const got=await prepareBridgeContext(f.runtimeRoot,
  source,
  f.binding.request_hash);
  assert.equal(got.binding.request_hash,
  f.binding.request_hash);
  await assert.rejects(prepareBridgeContext(f.runtimeRoot,
  {
    ...source,
    dirty:true
  },
  f.binding.request_hash),
  /DIRTY_SOURCE/);
  await assert.rejects(prepareBridgeContext(f.runtimeRoot,
  {
    ...source,
    commit:'f'.repeat(40)
  },
  f.binding.request_hash),
  /SOURCE_REVISION/);
  await writeFile(path.join(f.root,
  'resourceArtifact'),
  'changed');
  await assert.rejects(prepareBridgeContext(f.runtimeRoot,
  source,
  f.binding.request_hash),
  /MATERIAL_HASH/);
});

import { execFileSync, spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { once } from 'node:events';

test('nonregular FIFO material fails before a blocking open', { skip: process.platform !== 'linux' }, async t => {
  const f = await fixture(t);
  execFileSync('mkfifo', [path.join(f.root, 'pipe')]);
  const moduleUrl = pathToFileURL(path.resolve('debug-workspace/bridge/materials.mjs')).href;
  const source = `import {readRegisteredFile} from ${JSON.stringify(moduleUrl)};
    try { await readRegisteredFile({root:${JSON.stringify(f.root)},relativePath:'pipe',maxBytes:16});
      process.exitCode=2; } catch(error) { process.stdout.write(error.message); }`;
  const child = spawn(process.execPath, ['--input-type=module', '-e', source]);
  let output = '';
  child.stdout.on('data', bytes => { output += bytes; });
  const exited = once(child, 'exit');
  let timer;
  const result = await Promise.race([
    exited.then(() => 'exited'),
    new Promise(resolve => { timer = setTimeout(() => resolve('blocked'), 600); }),
  ]);
  clearTimeout(timer);
  if (result === 'blocked') {
    child.kill('SIGKILL');
    await exited;
  }
  assert.equal(result, 'exited');
  assert.match(output, /NOT_REGULAR_FILE/);
});

test('source revision is a scalar string without regex coercion', async t => {
  const f = await fixture(t);
  for (const revision of [[f.binding.target.source_revision], {}, 123, null, true]) {
    assert.throws(() => validateTechHubBinding({
      ...f.binding, target: { ...f.binding.target, source_revision: revision },
    }), /REVISION/);
  }
});
