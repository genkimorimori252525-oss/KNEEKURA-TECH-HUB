import importlib
from copy import deepcopy
import pytest
from test_minecraft_storage import manifest
from kneekura_tech_hub.bundle import BundleValidationError, ingest_bundle, preflight_bundle
from kneekura_tech_hub.minecraft.index import prepare_index
from kneekura_tech_hub.minecraft.storage import ContractError, Store, capture_profile
from kneekura_tech_hub.repository import MemoryRepository
from kneekura_tech_hub.service import CurationEngine
from kneekura_tech_hub.validator import validate_record


@pytest.fixture
def core_profile(tmp_path):
    # This is a Core contract test, not a classfile/provider integration test.
    # Keep it runnable without javac so schema mismatches cannot silently skip.
    (tmp_path/'src').mkdir()
    (tmp_path/'src/Example.java').write_text('class Example { int attack(int x) { return x + 1; } }')
    (tmp_path/'resources').mkdir()
    (tmp_path/'resources/example.json').write_text('{"attack": 1}')
    m=manifest()
    m['roots'].append(dict(m['roots'][0], id='resources', path='resources', role='resource'))
    store=Store(tmp_path/'cache')
    return store, capture_profile(m,tmp_path,store), tmp_path


def fixture_licenses(profile):
    return {root['id']: {'state':'KNOWN','declared_expression':'MIT',
                       'handling_policy':'Locally authored unit-test fixture'}
            for root in profile['roots']}


def mod():
    try: return importlib.import_module('kneekura_tech_hub.minecraft.core_bridge')
    except ImportError: pytest.fail('Existing-core bridge is not implemented')


def test_core_call_preserves_exact_selection_and_keeps_research_separate(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']; calls=[]
    result={'candidate_claim_ids':['cl:exact'],'claims':[{'id':'cl:exact','maturity':'VALIDATED'}], 'claim_explanations':[{'claim':{'id':'cl:exact'},'evidence_chains':[{'source_snapshot':{'id':'ss:exact'}}]}], 'ambiguous':True}
    def explain(repo,entity_id,*,context):
        calls.append((repo,entity_id,context)); return result
    out=mod().context(store,idx,'attack',entity_id='ke:hurt',repository=object(),explain=explain)
    assert calls[0][1]=='ke:hurt'
    assert calls[0][2]['minecraft_version']=='1.20.1' and calls[0][2]['loader']=='forge'
    assert out['research']['results'] and out['governed']['status']=='OK'
    assert store.json(out['governed']['artifact_hash'])==result
    assert out['canonical_writes']==0


def test_backend_failure_does_not_hide_raw_source(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    def fail(*a,**kw): raise OSError('database unavailable')
    out=mod().context(store,idx,'attack',entity_id='ke:hurt',repository=object(),explain=fail)
    assert out['status']=='PARTIAL' and out['research']['results']
    assert out['governed']['status']=='UNAVAILABLE'


def test_caller_cannot_override_environment(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    with pytest.raises(ContractError,match='conflict'):
        mod().context(store,idx,'attack',entity_id='ke:hurt',extra_context={'minecraft_version':'1.21'})


def test_staging_bundle_preserves_single_snapshot_per_observation_and_creator(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    out=mod().stage_bundle(store,idx,[d['document_id'] for d in p['documents']],summary='Observed attack signature',actor={'actor_type':'ai','actor_id':'jolly'},captured_at='2026-09-28T00:00:00Z',source_licenses=fixture_licenses(p))
    b=store.json(out['bundle_hash']); records={r['id']:r for r in b['records']}
    assert len(preflight_bundle(b))==out['records']
    assert len([r for r in b['records'] if r['record_type']=='source'])==2
    assert not any(r['record_type'] in ('claim','knowledge_entity') for r in b['records'])
    for obs in [r for r in b['records'] if r['record_type']=='staged_observation']:
        evidence=[records[x] for x in obs['evidence_candidate_ids']]
        assert len({e['source_snapshot_id'] for e in evidence})==1
        assert obs['status']=='NEW' and obs['created_by']['actor_type']=='ai'
        assert all(store.read(e['locator']['content_hash']) for e in evidence)
    assert out['canonical_writes']==0 and out['ingestion']=='REQUIRES_EXISTING_CORE_REVIEW'


def test_staging_cannot_reference_unavailable_or_invented_documents(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    with pytest.raises(ContractError): mod().stage_bundle(store,idx,['madeup'],summary='x',actor={'actor_type':'ai'})
    d=p['documents'][0]; store.blob_path(d['content_hash']).unlink()
    with pytest.raises(OSError): mod().stage_bundle(store,idx,[d['document_id']],summary='x',actor={'actor_type':'ai'})


def test_staging_requires_explicit_license_review_before_writing_bundle(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    before={path.relative_to(store.root):path.read_bytes() for path in store.root.rglob('*') if path.is_file()}
    with pytest.raises(ContractError,match='license'):
        mod().stage_bundle(store,idx,[p['documents'][0]['document_id']],summary='x',actor={'actor_type':'ai'})
    after={path.relative_to(store.root):path.read_bytes() for path in store.root.rglob('*') if path.is_file()}
    assert after==before


@pytest.mark.parametrize('license', [
    None, {}, {'state':'UNKNOWN'}, {'state':'REVIEW_REQUIRED'}, {'state':'CONFLICT'},
    {'state':'KNOWN'}, {'state':'KNOWN','declared_expression':''},
    {'state':'KNOWN','declared_expression':' '}, {'state':'KNOWN','declared_expression':False},
])
def test_staging_does_not_invent_license_authority(core_profile,license):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']; doc=p['documents'][0]
    with pytest.raises(ContractError,match='license'):
        mod().stage_bundle(store,idx,[doc['document_id']],summary='x',actor={'actor_type':'ai'},
                           source_licenses={doc['root_id']:license})


def test_staging_checks_all_selected_roots_for_licenses(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    licenses=fixture_licenses(p); licenses.pop('resources')
    with pytest.raises(ContractError,match='license'):
        mod().stage_bundle(store,idx,[d['document_id'] for d in p['documents']],summary='x',
                           actor={'actor_type':'ai'},source_licenses=licenses)


def test_staging_uses_core_schema_before_publishing_any_bundle(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    before={path.relative_to(store.root):path.read_bytes() for path in store.root.rglob('*') if path.is_file()}
    with pytest.raises(ContractError,match='Core'):
        mod().stage_bundle(store,idx,[p['documents'][0]['document_id']],summary='x',
                           actor={'actor_type':'ai','actor_id':{'invalid':'actor'}},
                           source_licenses=fixture_licenses(p))
    after={path.relative_to(store.root):path.read_bytes() for path in store.root.rglob('*') if path.is_file()}
    assert after==before


def test_valid_bundle_preserves_licenses_and_existing_human_review_gate(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    licenses=fixture_licenses(p); original=deepcopy(licenses)
    result=mod().stage_bundle(store,idx,[d['document_id'] for d in p['documents']],summary='Observed local fixture',
                              actor={'actor_type':'ai','actor_id':'test'},source_licenses=licenses)
    bundle=store.json(result['bundle_hash']); repository=MemoryRepository(); engine=CurationEngine(repository)
    assert licenses==original
    for source in (r for r in bundle['records'] if r['record_type']=='source'):
        assert source['license']==licenses[source['origin']['root_id']]
        assert source['acquisition']=={'level':'selected-files'}
    with pytest.raises(BundleValidationError,match='human'):
        ingest_bundle(engine,bundle,actor={'actor_type':'ai','actor_id':'test'})
    assert repository.list()==[]
    # A test-only human reviewer drives the existing service; the bridge never does.
    ingest_bundle(engine,bundle,actor={'actor_type':'human','actor_id':'fixture-reviewer'})
    assert len(repository.list('staged_observation'))==2
    assert not repository.list('claim') and not repository.list('knowledge_entity')


def test_core_context_uses_real_guidance_selection_and_provenance(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    staged=mod().stage_bundle(store,idx,[p['documents'][0]['document_id']],summary='Observed local fixture',
                              actor={'actor_type':'ai','actor_id':'test'},source_licenses=fixture_licenses(p))
    bundle=store.json(staged['bundle_hash']); repository=MemoryRepository()
    ingest_bundle(CurationEngine(repository),bundle,actor={'actor_type':'human','actor_id':'fixture-reviewer'})
    evidence=repository.list('evidence')[0]
    entity={'record_type':'knowledge_entity','id':'ke:fixture-attack','canonical_name':'Fixture attack',
            'aliases':[],'kinds':['test-fixture'],'abstraction_level':'L1','identity_state':'CANONICAL','relations':[]}
    exact={'minecraft_version':'1.20.1','loader':'forge','loader_version':'47.4.0',
           'namespace':'mojmap','physical_side':'server','track':'ANCHOR'}
    claim={'record_type':'claim','id':'cl:fixture-anchor','entity_id':entity['id'],
           'claim_type':'DIRECT_OBSERVATION','statement':'Local fixture has an attack declaration.',
           'maturity':'VALIDATED','applicability':exact,'evidence_ids':[evidence['id']],
           'created_by':{'actor_type':'ai','actor_id':'test'},'policy_version':'1.0.0'}
    other=deepcopy(claim); other.update(id='cl:fixture-frontier',applicability=dict(exact,minecraft_version='1.21'))
    candidate=deepcopy(claim); candidate.update(id='cl:fixture-candidate',maturity='CANDIDATE')
    # Historical read fixtures do not exercise or bypass real human promotion.
    for record in (entity,claim,other,candidate):
        validate_record(record); repository.put(record)
    before=repository.list()
    out=mod().context(store,idx,'attack',entity_id=entity['id'],repository=repository)
    assert out['governed']['status']=='OK'
    explanation=store.json(out['governed']['artifact_hash'])
    assert explanation['candidate_claim_ids']==[claim['id']]
    chain=explanation['claim_explanations'][0]['evidence_chains'][0]
    assert chain['evidence']==evidence
    assert chain['source_snapshot']==repository.get(evidence['source_snapshot_id'])
    assert chain['source']==repository.get(evidence['source_id'])
    assert out['canonical_writes']==0 and repository.list()==before


def test_repeated_staging_reuses_existing_core_records_without_writes(core_profile):
    store,p,_=core_profile; idx=prepare_index(p,store)['index_snapshot_id']
    kwargs={'summary':'Observed local fixture','actor':{'actor_type':'ai','actor_id':'test'},
            'source_licenses':fixture_licenses(p)}
    staged=mod().stage_bundle(store,idx,[p['documents'][0]['document_id']],captured_at='2026-09-28T00:00:00Z',**kwargs)
    repository=MemoryRepository()
    ingest_bundle(CurationEngine(repository),store.json(staged['bundle_hash']),
                  actor={'actor_type':'human','actor_id':'fixture-reviewer'})
    before=repository.list()
    again=mod().stage_bundle(store,idx,[p['documents'][0]['document_id']],captured_at='2026-09-30T00:00:00Z',
                             existing_repository=repository,**kwargs)
    assert again=={'status':'NOT_MODIFIED','canonical_writes':0,'bundle_hash':None}
    assert repository.list()==before
