"""Subprocess tests: real public CLI routes, not calls to private helpers."""
import json
from pathlib import Path

from test_minecraft_cli import run_cli
from test_minecraft_workspace import project, export_data
from test_minecraft_execution import local


def test_cli_passive_discovery_and_resolved_import(project, tmp_path):
    cache=tmp_path/'cas'
    p,out=run_cli(cache,'profile','discover','--workspace',str(project))
    assert p.returncode==0,p.stderr
    assert out['manifest']['dependency_resolution']=='UNKNOWN'
    data=export_data(project); data['output_roots']=[]
    export=tmp_path/'export.json'; export.write_text(json.dumps(data))
    p,out=run_cli(cache,'profile','import','--workspace',str(project),'--resolved',str(export))
    assert p.returncode==0,p.stderr
    index=out['index_snapshot_id']; assert index
    p,out=run_cli(cache,'search','--index',index,'--query','class Mob')
    assert out['results']


def test_cli_mapping_import_lookup_and_original_bytes(tmp_path):
    cache=tmp_path/'cas'; path=tmp_path/'names.tiny'
    text='tiny\t2\t0\tintermediary\tmojmap\nc\ta/A\tb/B\n\tm\t()V\ta\tattack\n'
    path.write_text(text)
    p,out=run_cli(cache,'mapping','import','--path',str(path),'--format','tiny')
    assert p.returncode==0,p.stderr
    table=out['mapping_hash']; raw=out['text_hash']
    p,out=run_cli(cache,'mapping','lookup','--mapping',table,'--from-namespace','intermediary','--to-namespace','mojmap','--owner','a/A','--member','a','--descriptor','()V')
    assert p.returncode==0,p.stderr
    assert out['results'][0]['name']=='attack'
    p,out=run_cli(cache,'artifact','read','--hash',raw,'--size','20')
    assert out['results'][0]['text']==text[:20] and out['next_cursor']
    p,more=run_cli(cache,'artifact','read','--hash',raw,'--size','20','--cursor',out['next_cursor'])
    assert more['results'][0]['text']==text[20:40]


def test_cli_interventions_and_core_staging_keep_provenance(project,tmp_path):
    cache=tmp_path/'cas'; data=export_data(project); data['output_roots']=[]
    (project/'src/main/resources/demo.accesswidener').write_text('accessWidener v2 named\naccessible class example/Mob\n')
    export=tmp_path/'export.json'; export.write_text(json.dumps(data))
    p,out=run_cli(cache,'profile','import','--workspace',str(project),'--resolved',str(export))
    assert p.returncode==0,p.stderr
    idx=out['index_snapshot_id']
    p,out=run_cli(cache,'interventions','--index',idx,'--owner','example/Mob')
    assert p.returncode==0,p.stderr
    assert out['results']
    p,search=run_cli(cache,'search','--index',idx,'--query','class Mob')
    doc=search['results'][0]['document_id']
    stage_args=('knowledge','stage','--index',idx,'--document',doc,'--summary','Observed declaration','--actor-id','jolly')
    p,out=run_cli(cache,*stage_args)
    assert p.returncode != 0 and 'license' in str(out).lower()
    # This file is a test-owned fixture; no real upstream license is inferred.
    from kneekura_tech_hub.minecraft.storage import Store
    from kneekura_tech_hub.minecraft.index import _load
    store=Store(cache)
    snapshot=_load(store,idx)
    licenses=tmp_path/'reviewed-licenses.json'
    licenses.write_text(json.dumps({root['id']:{'state':'KNOWN','declared_expression':'MIT'}
                                    for root in snapshot['profile']['roots']}))
    p,out=run_cli(cache,*stage_args,'--source-licenses',str(licenses))
    assert p.returncode==0,p.stderr
    assert out['canonical_writes']==0 and out['bundle_hash']
    from kneekura_tech_hub.bundle import preflight_bundle
    preflight_bundle(store.json(out['bundle_hash']))
    p,out=run_cli(cache,'context','--index',idx,'--query','Mob','--entity','ke:mob')
    assert p.returncode==0,p.stderr
    assert out['research']['results'] and out['governed']['status']=='UNAVAILABLE'


def test_cli_registered_validation_executes_once(local,tmp_path):
    store,registry,root=local
    path=tmp_path/'registry.json'; path.write_text(json.dumps(registry))
    p,out=run_cli(store.root,'validate','run','--registry',str(path),'--kind','compile','--request-id','cli-1')
    assert p.returncode==0,p.stderr
    assert out['outcome']=='PASS' and out['receipt_hash']
    p,again=run_cli(store.root,'validate','run','--registry',str(path),'--kind','compile','--request-id','cli-1')
    assert again['receipt_hash']==out['receipt_hash']
    assert (root/'build/calls').read_text().count('called')==1


def test_cli_world_and_capabilities_do_not_claim_installed_forge(local,tmp_path):
    store,reg,root=local; template=root/'templates/empty'; template.mkdir(parents=True)
    reg['world_templates']=[str(template)]
    path=tmp_path/'reg.json'; path.write_text(json.dumps(reg))
    p,out=run_cli(store.root,'world','prepare','--registry',str(path),'--template',str(template),'--request-id','world-cli')
    assert p.returncode==0,p.stderr
    assert Path(out['world']).is_dir()
    p,out=run_cli(store.root,'capabilities')
    assert p.returncode==0,p.stderr
    assert out['runtime_status']=='NOT_PROBED' and out['ci_used'] is False


def test_duplicate_keys_cannot_override_explicit_execution_authorization(local,tmp_path):
    store,reg,root=local; pth=tmp_path/'reg.json'
    pth.write_text('{"allow_gradle":false,"allow_gradle":true}')
    p,out=run_cli(store.root,'validate','run','--registry',str(pth),'--kind','compile','--request-id','unsafe')
    assert p.returncode!=0 and out is not None and 'duplicate' in str(out).lower()
    assert not (root/'build/calls').exists()

def test_all_operation_envelopes_have_the_declared_common_fields(tmp_path):
    p,out=run_cli(tmp_path/'cas','capabilities')
    assert p.returncode==0
    assert {'schema_version','request_id','profile_id','profile_hash','index_snapshot_id',
            'status','results','evidence','coverage','warnings','next_cursor'} <= set(out)


def test_cli_explicit_client_world_layout_uses_run_saves(local,tmp_path):
    store,reg,root=local
    template=root/'templates/client'; template.mkdir(parents=True)
    (template/'level.dat').write_bytes(b'fixture-world')
    reg['world_templates']=[str(template)]
    path=tmp_path/'reg.json'; path.write_text(json.dumps(reg))
    p,out=run_cli(store.root,'world','prepare','--registry',str(path),'--template',str(template),
                  '--request-id','client-world-cli','--world-name','proof-world','--layout','client')
    assert p.returncode==0,p.stderr
    assert out['world_layout']=='client'
    assert Path(out['world'])==Path(out['directory'])/'saves/proof-world'
    assert (Path(out['world'])/'level.dat').read_bytes()==b'fixture-world'
    assert (Path(out['directory'])/'.kneekura-run.json').is_file()
