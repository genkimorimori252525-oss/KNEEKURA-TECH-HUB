"""Comparable camera conditions never establish aesthetics or game acceptance."""
from copy import deepcopy
import importlib

import pytest

from test_minecraft_asset_session import prepared
from test_minecraft_asset_export import capture
from test_minecraft_asset_mutation import sealed, frame, edit, api as mutation_api
from kneekura_tech_hub.minecraft.storage import ContractError, canonical


def api():return importlib.import_module('kneekura_tech_hub.minecraft.asset_comparison')


@pytest.fixture
def pair(sealed):
    store,_,r,before=sealed
    for a in r['artifacts']:
        if a['kind']=='view':a.update(frame=frame(a['view']),generation=0)
    h=store.put_json(r);m=mutation_api().validate_mutation(store,h,edit(r));after=mutation_api().expected_snapshot(before,m)
    later=deepcopy(r);later.update(generation=1,snapshot_hash=store.put_json(after),parent_receipt_hash=h,mutation_hash=store.put_json(m))
    for a in later['artifacts']:
        if a['kind'] in ('native','model'):
            raw=canonical(after[a['kind']]);a.update(content_hash=store.put(raw),size_bytes=len(raw))
        if a['kind']=='view':a['generation']=1
    return store,h,store.put_json(later),later


def test_exact_frames_and_next_generation_are_comparable_without_quality_claim(pair):
    store,b,a,_=pair;result=api().compare_captures(store,b,a)
    assert result['comparability']=='COMPARABLE' and len(result['views'])==3
    assert all(v['comparability']=='COMPARABLE' for v in result['views'])
    assert result['verification']=={'structural':'NOT_RUN','visual':'NOT_RUN','runtime':'NOT_RUN'}
    assert 'score' not in result


@pytest.mark.parametrize('change',['position','projection','viewport','canvas','output','frame_missing','view_missing','view_generation','parent'])
def test_changed_or_missing_evidence_is_non_comparable(pair,change):
    store,b,_,later=pair;r=deepcopy(later);a=r['artifacts'][3]
    if change=='position':a['frame']['position'][0]+=1
    if change=='projection':
        a['frame']['projection']='orthographic';a['frame']['camera_parameters']={'near':1,'far':30000,'zoom':1,'left':-8,'right':8,'top':8,'bottom':-8}
    if change in ('viewport','canvas','output'):a['frame'][change][0]+=1
    if change=='frame_missing':a.pop('frame')
    if change=='view_missing':r['artifacts'].pop(3)
    if change=='view_generation':a['generation']=0
    if change=='parent':r['parent_receipt_hash']='0'*64
    result=api().compare_captures(store,b,store.put_json(r))
    assert result['comparability']=='NON_COMPARABLE'
    assert len(result['views'])==3


def test_legacy_view_labels_are_never_upgraded_to_comparable(capture):
    store,h,_=capture;r=api().compare_captures(store,h,h)
    assert r['comparability']=='NON_COMPARABLE' and 'MISSING_GENERATION_METADATA' in r['reasons']


@pytest.mark.parametrize('fault',['nonfinite','unknown','bool','bad_dimensions','camera'])
def test_frame_validation_is_strict(fault):
    f=frame()
    if fault=='nonfinite':f['position'][0]=float('nan')
    if fault=='unknown':f['url']='https://invalid.test'
    if fault=='bool':f['device_pixel_ratio']=True
    if fault=='bad_dimensions':f['viewport']=[0,480]
    if fault=='camera':f['camera_parameters']['far']=0
    with pytest.raises(ContractError):api().validate_frame(f,'front')


def test_comparison_request_validation_uses_bounded_reads(pair, monkeypatch):
    store, before, after, _ = pair
    def unbounded_read(key): raise AssertionError('comparison reopened an unbounded Store.read')
    monkeypatch.setattr(store, 'read', unbounded_read)
    assert api().compare_captures(store, before, after)['comparability'] == 'COMPARABLE'


@pytest.mark.parametrize('field,value', [('expected_generation', False), ('expected_generation', 0.0),
                                       ('resulting_generation', True), ('resulting_generation', 1.0)])
def test_comparison_mutation_generation_identity_requires_exact_integer(pair, field, value):
    store, before, _, later = pair
    mutation = store.json(later['mutation_hash']); mutation[field] = value
    later['mutation_hash'] = store.put_json(mutation)
    with pytest.raises(ContractError): api().compare_captures(store, before, store.put_json(later))
