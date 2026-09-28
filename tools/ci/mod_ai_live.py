"""Exercise the real adapters against a disposable Forge MDK, not API stubs.

Called explicitly by the hosted workflow. No downloads, credentials, or public
endpoints here. Only the supplied runner-temporary MDK is edited/launched.
"""
from __future__ import annotations

import concurrent.futures
import gzip
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time
import uuid

from kneekura_tech_hub.minecraft import execution, index, runtime
from kneekura_tech_hub.minecraft.contracts import prepare_contract
from kneekura_tech_hub.minecraft.storage import Store, ContractError, capture_profile
from kneekura_tech_hub.minecraft.workspace import file_hash


def empty_structure() -> bytes:
    def name(text):
        b=text.encode(); return struct.pack('>H',len(b))+b
    def tag(kind,key,body): return bytes([kind])+name(key)+body
    def ints(values): return bytes([3])+struct.pack('>i',len(values))+b''.join(struct.pack('>i',v) for v in values)
    palette=tag(8,'Name',name('minecraft:stone'))+b'\0'
    block=tag(9,'pos',ints([0,0,0]))+tag(3,'state',struct.pack('>i',0))+b'\0'
    root=tag(3,'DataVersion',struct.pack('>i',3465))+tag(9,'size',ints([3,3,3]))
    root+=tag(9,'palette',bytes([10])+struct.pack('>i',1)+palette)
    root+=tag(9,'blocks',bytes([10])+struct.pack('>i',1)+block)
    root+=tag(9,'entities',bytes([10])+struct.pack('>i',0))+b'\0'
    return gzip.compress(tag(10,'',root),mtime=0)


def configure(root: Path, repo: Path):
    source=root/'src'; source.mkdir(exist_ok=False)
    java=source/'main/java/org/kneekura/probe'; java.mkdir(parents=True)
    shutil.copyfile(repo/'tools/ci/mod_ai_probe/ProbeMod.java',java/'ProbeMod.java')
    resources=source/'main/resources'; (resources/'META-INF').mkdir(parents=True)
    mods='''modLoader="javafml"
loaderVersion="[47,48)"
license="All Rights Reserved"
[[mods]]
modId="kneekura_probe"
version="1.0.0"
displayName="Disposable KNEEKURA integration probe"
[[dependencies.kneekura_probe]]
modId="forge"
mandatory=true
versionRange="[47,48)"
ordering="NONE"
side="BOTH"
[[dependencies.kneekura_probe]]
modId="minecraft"
mandatory=true
versionRange="[1.20.1]"
ordering="NONE"
side="BOTH"
'''
    (resources/'META-INF/mods.toml').write_text(mods)
    (resources/'pack.mcmeta').write_text(json.dumps({'pack':{'pack_format':15,'description':'Disposable CI probe'}}))
    structure=resources/'data/kneekura_probe/structures/empty.nbt'; structure.parent.mkdir(parents=True)
    structure.write_bytes(empty_structure())
    p=root/'gradle.properties'
    lines=p.read_text().splitlines()
    p.write_text('\n'.join('mod_id=kneekura_probe' if x.startswith('mod_id=') else
                          'org.gradle.jvmargs=-Xmx2G' if x.startswith('org.gradle.jvmargs=') else x
                          for x in lines)+'\norg.gradle.workers.max=2\n')
    (root/'gradlew').chmod(0o700)
    # A local disposable commit supplies a real revision, not a made-up hash.
    for cmd in (['git','init','-q'],['git','add','.'],
                ['git','-c','user.name=KNEEKURA CI','-c','user.email=ci@local.invalid',
                 'commit','-qm','Disposable Forge bridge acceptance fixture']):
        subprocess.run(cmd,cwd=root,check=True,timeout=30,stdout=subprocess.DEVNULL)



def prepare_probe_scenario(world: dict) -> dict:
    """Forge1.20.1 Main uses server.properties, not vanilla test-server defaults.

    These are fixture inputs, not a relaxation of the observer's runtime checks.
    Main expands/normalizes server.properties on startup, so the original bytes
    are retained as input evidence rather than claimed to be runtime-immutable.
    """
    directory=Path(world['directory']); target=Path(world['world'])
    if target.parent != directory or target.name != 'gametestserver':
        raise ValueError('Unexpected prepared fixture world')
    with (directory/'server.properties').open('x',encoding='utf-8') as f:
        f.write('level-seed=0\nlevel-name=gametestserver\nserver-ip=127.0.0.1\n'
                'server-port=0\nenable-rcon=false\nenable-query=false\n')
    # Forge's PrefixGameTestTemplate(false) changes the test ID as well as its template.
    return {'world_seed':0,'assertion_domain':'server_behavior','expected_tests':['bridge'],
            'expected_required':{'bridge':True},'purpose':'Bridge loop, not general MOD correctness'}


def probe_entity_request() -> tuple[str, dict]:
    """Bind this fixture's summon and observation to one exact UUID.

    A generated world can contain many natural pigs; a capped all-entity page
    cannot prove absence or count of the deliberately created test entity.
    The scoreboard mutation separately proves duplicate-request idempotency.
    """
    entity=uuid.UUID('e52e0073-5ce9-4c43-8bfd-5d70f071de2b')
    values=','.join(str(v) for v in struct.unpack('>iiii',entity.bytes))
    command='summon minecraft:pig 0 80 0 {NoAI:1b,NoGravity:1b,UUID:[I;'+values+']}'
    return command, {'limit':1,'dimension':'minecraft:overworld','entity_uuids':[str(entity)]}


def run(root: Path, evidence: Path, repo: Path):
    root=root.resolve(); evidence=evidence.resolve(); evidence.mkdir(parents=True,exist_ok=True)
    temp=Path(os.environ['RUNNER_TEMP']).resolve()
    if not root.is_relative_to(temp) or root==temp or not (root/'gradlew').is_file():
        raise RuntimeError('Only an explicitly supplied disposable RUNNER_TEMP MDK is accepted')
    configure(root,repo)
    store=Store(temp/'kneekura-live-cas')
    pig_command,pig_query=probe_entity_request()
    registry={'workspace':str(root),'allow_gradle':True,'wrapper_sha256':file_hash(root/'gradlew'),
        'allowed_kinds':['compile','export','gametest'], 'build_outputs':['build/classes/java/main'],
        'build_artifact':'build/classes/java/main','runtime_config_files':[],
        'world_templates':[str(root/'world-template')], 'remaining_launches':1,
        'launch_budget_id':'one-hosted-probe','timeout_seconds':600,'max_log_bytes':8*1024*1024,
        'command_registry':{
            'objective':'scoreboard objectives add kneekura dummy',
            'zero':'scoreboard players set probe kneekura 0',
            'increment':'scoreboard players add probe kneekura 1',
            'score':'scoreboard players get probe kneekura',
            'pig':pig_command,
            'finish':'setblock 0 80 1 minecraft:emerald_block'}}
    receipts=[]
    def record(label,result):
        receipts.append({'phase':label,'outcome':result.get('outcome'),'receipt_hash':result.get('receipt_hash')})
        if result.get('log_hash'):
            raw=store.read(result['log_hash']); (evidence/(label+'.txt')).write_bytes(raw)
            print(label,result.get('outcome'),flush=True)
            if result.get('outcome') not in ('PASS',): print(raw[-14000:].decode(errors='replace'),flush=True)
        (evidence/'receipts.json').write_text(json.dumps(receipts,indent=2))
    built=execution.execute(store,registry,kind='compile',request_id='probe-build'); record('build',built)
    assert built['outcome']=='PASS',built
    registry['build_receipt_hash']=built['receipt_hash']
    resolved=execution.execute(store,registry,kind='export',request_id='probe-export'); record('export',resolved)
    assert resolved['outcome']=='PASS',resolved
    manifest=store.json(resolved['outputs'][0]['manifest_hash'])
    manifest['physical_side']='server'
    profile=capture_profile(manifest,root,store)
    snapshot=index.prepare_index(profile,store)['index_snapshot_id']
    assert index.search(store,snapshot,'class ProbeMod')['results']
    (root/'world-template').mkdir()
    world=execution.prepare_world(store,registry,template=str(root/'world-template'),request_id='probe-world')
    scenario=prepare_probe_scenario(world)
    shutil.copyfile(Path(world['directory'])/'server.properties', evidence/'server-input.properties')
    contract=prepare_contract(store,registry,index_id=snapshot,world=world['world'],scenario=scenario)['contract']
    session_path=Path(world['directory'])/'session.json'
    live_errors=[]; summary={}; command_evidence=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future=pool.submit(execution.execute,store,registry,kind='gametest',request_id='probe-run',
                           world=world['world'],contract=contract,timeout=420)
        try:
            deadline=time.monotonic()+360
            endpoint=Path(world['directory'])/'endpoint.json'
            while not endpoint.exists():
                if future.done(): raise RuntimeError('Game process completed before observer became ready')
                if time.monotonic()>deadline: raise TimeoutError('No authenticated observer endpoint within budget')
                time.sleep(0.2)
            def observe(query=None):
                result=runtime.observe_live(store,str(session_path),query=query or {'limit':128})
                assert result['status']=='OK' and result['evidence_level']=='AUTHENTICATED_LIVE_OBSERVER',result
                return result
            initial=observe()
            (evidence/'handshake.json').write_text(json.dumps(store.json(initial['handshake_hash']),indent=2))
            def command(key,identifier):
                out=runtime.execute_registered_command(store,str(session_path),command_id=key,request_id=identifier)
                assert out['outcome']=='PASS' and out['assertion_domain']=='command_execution',out
                raw=store.json(out['artifact_hash'])
                command_evidence.append(raw)
                (evidence/'command-receipts.json').write_text(json.dumps(command_evidence,indent=2))
                return out,raw
            command('objective','objective-1')
            _,zero=command('zero','zero-1'); assert zero['command_result']==0
            first,_=command('increment','increment-once'); repeated,_=command('increment','increment-once')
            assert first['artifact_hash']==repeated['artifact_hash']
            _,score=command('score','read-score'); assert score['command_result']==1
            pig_first,_=command('pig','pig-once'); pig_repeat,_=command('pig','pig-once')
            assert pig_first['artifact_hash']==pig_repeat['artifact_hash']
            observation=observe(pig_query); data=store.json(observation['artifact_hash'])
            (evidence/'entity-observation.json').write_text(json.dumps(data,indent=2))
            pigs=[e for e in data['entities'] if e['type']=='minecraft:pig' and e['uuid']==pig_query['entity_uuids'][0]]
            assert len(pigs)==1 and not data['entities_truncated'],data
            s=runtime.load_session(session_path); url=json.loads(endpoint.read_text())['url']
            try: runtime.BridgeClient(url,'0'*64,contract).request('/v1/handshake')
            except ContractError: pass
            else: raise AssertionError('Wrong token accepted')
            command('finish','finish-1')
            summary={'handshake':'PASS','live_entity_observation':'PASS','pig_count':len(pigs),
                'duplicate_command_execution_count':score['command_result'],'successful_zero_result':'PASS',
                'wrong_token_rejected':True,'initial_handshake_hash':initial['handshake_hash'],
                'observation_hash':observation['artifact_hash'],'client_rendering':'NOT_RUN'}
        except Exception as exc:
            live_errors.append(type(exc).__name__+': '+str(exc))
        finally:
            # Even on host assertions failing, collect the bounded actual process result.
            result=future.result(timeout=460); record('gametest',result)
            for path in Path(world['directory']).glob('logs/*.log'):
                if path.stat().st_size<=8*1024*1024: shutil.copyfile(path,evidence/('game-'+path.name))
    summary.update(minecraft=manifest['minecraft'],forge=manifest['loader_version'],run_id=contract['run_id'],
        index_snapshot_id=snapshot,profile_id=profile['profile_id'],process_outcome=result['outcome'],
        errors=live_errors,assertion_scope='Disposable probe: transport, identity, idempotency and GameTest reporting')
    s=runtime.load_session(session_path)
    report=runtime.read_signed_report(s,Path(world['directory'])/'gametest-report.json')
    (evidence/'gametest-report.json').write_text(json.dumps(report,indent=2))  # No session token.
    summary['test_results']=report['tests']
    (evidence/'live-summary.json').write_text(json.dumps(summary,indent=2))
    assert not live_errors,live_errors
    assert result['outcome']=='PASS',result
    assert report['completed'] and report['executed_count']==2 and report['detected_count']==2,report
    actual={t['id']:t for t in report['tests']}
    assert actual['bridge']['status']=='PASS'
    assert actual['knownbad']['status']=='FAIL' and not actual['knownbad']['required']
    assert result['gametest']['unrelated_failures'][0]['id']=='knownbad'
    print('REAL_FORGE_LIVE_BRIDGE_AND_GAMETEST_PASS_WITH_PRESERVED_NEGATIVE_CONTROL',flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args(); run(a.workspace,a.evidence,Path(__file__).resolve().parents[2])
