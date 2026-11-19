/** Explicit cross-repository source gate; does not launch Minecraft or a browser. */
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fixture } from './result-export-fixture.mjs';
import { request } from '../../evidence/tests/visual-fixture.mjs';
import { exportFinalizedExperiment } from '../result-export.mjs';
import { sha256, stableJson } from '../json.mjs';
const tech=process.env.KNEEKURA_TECH_HUB_SOURCE;
if(!tech||!path.isAbsolute(tech))throw new Error('KNEEKURA_TECH_HUB_SOURCE must point to the real TECH source checkout');
const temporary=await mkdtemp(path.join(os.tmpdir(),'lab-result-roundtrip-'));const cleanup=[];
const python=process.env.KNEEKURA_PYTHON??'python';
const script=String.raw`
import json,sys,re
from pathlib import Path
from kneekura_tech_hub.minecraft import storage,index,experiment_bridge
from kneekura_tech_hub.minecraft.asset_contract import decode_json
root=Path(sys.argv[1]); store=storage.Store(root/'cas')
if sys.argv[2]=='prepare':
    source=root/'source'; (source/'src').mkdir(parents=True)
    (source/'src/Example.java').write_text('class Example { int damage = 1; }\n')
    m={'schema_version':1,'minecraft':'1.20.1','loader':'forge','loader_version':'47.4.0','java_major':17,'namespace':'mojmap',
       'physical_side':'server','logical_side':'server','track':'ANCHOR','workspace_revision':'a'*40,'dirty_hash':'b'*64,
       'toolchain':{'gradle':'8.8','forgegradle':'6.0.24'},'roots':[{'id':'own','path':'src','kind':'directory','scope':'runtime',
       'role':'source','namespace':'mojmap','stage':'workspace','classloader':'unknown','track':'ANCHOR'}]}
    p=storage.capture_profile(m,source,store); idx=index.prepare_index(p,store)['index_snapshot_id']
    req=json.loads((root/'base-request.json').read_text());req['target'].update(profile_id=p['profile_id'],index_snapshot_id=idx,
      source_revision=p['manifest']['workspace_revision'],dirty_hash=p['manifest']['dirty_hash'],
      build_artifact_hash=store.put(b'source-fixture-build'),config_hash=store.put(b'source-fixture-config'),resource_hash=store.put(b'source-fixture-resource'))
    saved=experiment_bridge.prepare_experiment(store,req)
    (root/'request.json').write_bytes(storage.canonical(req));(root/'assertions.json').write_bytes(storage.canonical(req['assertions']))
    print(json.dumps({'prepared':saved['request_hash']}))
else:
    manifest=json.loads((root/'transport/manifest.json').read_text())
    assert manifest['contains_private_evidence'] is True
    for item in manifest['blobs']:
        h=item['content_hash'];assert re.fullmatch('[a-f0-9]{64}',h)
        raw=(root/'transport/blobs'/h).read_bytes();assert len(raw)==item['size_bytes'];assert store.put(raw)==h
    result=decode_json(store.read(manifest['result_hash']))
    imported=experiment_bridge.import_experiment_result(store,manifest['request_hash'],result)
    assert imported['runtime_attestation']=='NOT_ESTABLISHED'
    assert imported['reported_execution']=='COMPLETED' and imported['reported_cleanup']=='UNKNOWN'
    assert all(a['status']=='INCONCLUSIVE' for a in imported['reported_assertions'])
    resumed=experiment_bridge.resume_experiment(store,imported['result_hash'])
    assert resumed['can_replay'] is False and resumed['execution_authority']=='NONE'
    print(json.dumps({'imported':True,'evidenceCount':len(result['evidence']),'runtimeAttestation':imported['runtime_attestation'],
      'cleanup':imported['reported_cleanup'],'replay':resumed['can_replay']}))
`;
function run(mode){const result=spawnSync(python,['-c',script,temporary,mode],{encoding:'utf8',timeout:60000,maxBuffer:2*1024*1024,
 env:{...process.env,PYTHONDONTWRITEBYTECODE:'1',PYTHONPATH:path.join(tech,'src')}});
 if(result.error||result.status!==0)throw new Error('Cross-repository source gate failed: '+mode+'\n'+result.stderr,{cause:result.error});return JSON.parse(result.stdout.trim());}
try{
 await writeFile(path.join(temporary,'base-request.json'),stableJson(request()));run('prepare');
 const requestBytes=await readFile(path.join(temporary,'request.json'));const assertionsBytes=await readFile(path.join(temporary,'assertions.json'));
 const f=await fixture({after:fn=>cleanup.push(fn)},{requestValue:JSON.parse(requestBytes),requestBytesOverride:requestBytes,assertionsBytesOverride:assertionsBytes,
  visual:true,sparseProducer:true});
 const out=await exportFinalizedExperiment(f);await mkdir(path.join(temporary,'transport/blobs'),{recursive:true});
 for(const blob of out.blobs){assert.equal(sha256(blob.bytes),blob.contentHash);await writeFile(path.join(temporary,'transport/blobs',blob.contentHash),blob.bytes,{flag:'wx'});}
 await writeFile(path.join(temporary,'transport/manifest.json'),stableJson(out.manifest));
 console.log(JSON.stringify(run('import')));
}finally{for(const fn of cleanup)await fn();await rm(temporary,{recursive:true,force:true});}
