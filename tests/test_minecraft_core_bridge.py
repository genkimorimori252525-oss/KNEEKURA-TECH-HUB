import importlib
import pytest
from test_minecraft_index import class_profile
from kneekura_tech_hub.minecraft.index import prepare_index
from kneekura_tech_hub.minecraft.storage import ContractError


def mod():
    try: return importlib.import_module('kneekura_tech_hub.minecraft.core_bridge')
    except ImportError: pytest.fail('Existing-core bridge is not implemented')


def test_core_call_preserves_exact_selection_and_keeps_research_separate(class_profile):
    store,p,_=class_profile; idx=prepare_index(p,store)['index_snapshot_id']; calls=[]
    result={'candidate_claim_ids':['cl:exact'],'claims':[{'id':'cl:exact','maturity':'VALIDATED'}], 'claim_explanations':[{'claim':{'id':'cl:exact'},'evidence_chains':[{'source_snapshot':{'id':'ss:exact'}}]}], 'ambiguous':True}
    def explain(repo,entity_id,*,context):
        calls.append((repo,entity_id,context)); return result
    out=mod().context(store,idx,'attack',entity_id='ke:hurt',repository=object(),explain=explain)
    assert calls[0][1]=='ke:hurt'
    assert calls[0][2]['minecraft_version']=='1.20.1' and calls[0][2]['loader']=='forge'
    assert out['research']['results'] and out['governed']['status']=='OK'
    assert store.json(out['governed']['artifact_hash'])==result
    assert out['canonical_writes']==0


def test_backend_failure_does_not_hide_raw_source(class_profile):
    store,p,_=class_profile; idx=prepare_index(p,store)['index_snapshot_id']
    def fail(*a,**kw): raise OSError('database unavailable')
    out=mod().context(store,idx,'attack',entity_id='ke:hurt',repository=object(),explain=fail)
    assert out['status']=='PARTIAL' and out['research']['results']
    assert out['governed']['status']=='UNAVAILABLE'


def test_caller_cannot_override_environment(class_profile):
    store,p,_=class_profile; idx=prepare_index(p,store)['index_snapshot_id']
    with pytest.raises(ContractError,match='conflict'):
        mod().context(store,idx,'attack',entity_id='ke:hurt',extra_context={'minecraft_version':'1.21'})


def test_staging_bundle_preserves_single_snapshot_per_observation_and_creator(class_profile):
    store,p,_=class_profile; idx=prepare_index(p,store)['index_snapshot_id']
    out=mod().stage_bundle(store,idx,[d['document_id'] for d in p['documents']],summary='Observed attack signature',actor={'actor_type':'ai','actor_id':'jolly'},captured_at='2026-09-28T00:00:00Z')
    b=store.json(out['bundle_hash']); records={r['id']:r for r in b['records']}
    assert not any(r['record_type'] in ('claim','knowledge_entity') for r in b['records'])
    for obs in [r for r in b['records'] if r['record_type']=='staged_observation']:
        evidence=[records[x] for x in obs['evidence_candidate_ids']]
        assert len({e['source_snapshot_id'] for e in evidence})==1
        assert obs['status']=='NEW' and obs['created_by']['actor_type']=='ai'
        assert all(store.read(e['locator']['content_hash']) for e in evidence)
    assert out['canonical_writes']==0 and out['ingestion']=='REQUIRES_EXISTING_CORE_REVIEW'


def test_staging_cannot_reference_unavailable_or_invented_documents(class_profile):
    store,p,_=class_profile; idx=prepare_index(p,store)['index_snapshot_id']
    with pytest.raises(ContractError): mod().stage_bundle(store,idx,['madeup'],summary='x',actor={'actor_type':'ai'})
    d=p['documents'][0]; store.blob_path(d['content_hash']).unlink()
    with pytest.raises(OSError): mod().stage_bundle(store,idx,[d['document_id']],summary='x',actor={'actor_type':'ai'})
