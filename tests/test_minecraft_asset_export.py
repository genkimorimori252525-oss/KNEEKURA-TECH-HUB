"""Strict captured-asset materialization; fixture evidence is never game acceptance."""
import base64
from copy import deepcopy
import importlib
import json
from pathlib import Path
import struct
import zlib

import pytest

from test_minecraft_asset_session import prepared
from kneekura_tech_hub.minecraft.asset_contract import provider_pin
from kneekura_tech_hub.minecraft.asset_guard import ITEM_DISPLAY
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest


def png(width=32,height=32):
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    raw=(b'\x00'+bytes([212,175,55,255])*width)*height
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')


def api():
    return importlib.import_module('kneekura_tech_hub.minecraft.asset_export')


@pytest.fixture
def capture(prepared):
    store,request,_,plan=prepared
    texture=png()
    faces=('north','south','east','west','up','down')
    model={'format_version':'1.9.0','texture_size':[32,32],'textures':{'0':'celestial_staff'},
           'elements':[{'name':c['name'],'from':c['from'],'to':c['to'],
                       'faces':{f:{'uv':[n/2 for n in c['uv']],'texture':'#0'} for f in faces}}
                      for c in plan['cubes']]}
    native={'meta':{'model_format':'java_block','format_version':'5.0','box_uv':False},
            'java_block_version':'1.9.0','resolution':{'width':32,'height':32},
            'elements':[{'type':'cube','uuid':f'cube-{i}','name':c['name'],'from':c['from'],'to':c['to'],
                         'faces':{f:{'uv':list(c['uv']),'texture':0} for f in faces}}
                        for i,c in enumerate(plan['cubes'])],
            'groups':[], 'outliner':[f'cube-{i}' for i in range(len(plan['cubes']))],
            'textures':[{'id':'0','name':'celestial_staff','width':32,'height':32,
                         'source':'data:image/png;base64,'+base64.b64encode(texture).decode()}]}
    model['display']=deepcopy(ITEM_DISPLAY)
    native['display']=deepcopy(ITEM_DISPLAY)
    artifacts=[]
    for kind,data in [('model',canonical(model)),('native',canonical(native)),('texture',texture),
                      ('view',png()),('view',png()),('view',png())]:
        item={'kind':kind,'content_hash':store.put(data),'size_bytes':len(data),
              'mime':'application/json' if kind in ('model','native') else 'image/png'}
        if kind=='view': item['view']=['front','left','back'][len(artifacts)-3]
        artifacts.append(item)
    inspection=store.put_json({'schema_version':1,'record_type':'asset_editor_inspection',
                               'request_hash':request,'project_uuid':'fixture-project','result':{}})
    receipt={'schema_version':1,'record_type':'asset_session_capture','request_hash':request,
             'plan_hash':store.put_json(plan),'provider':provider_pin(),'guard_protocol':1,
             'loaded_revision':'UNATTESTED','project_uuid':'fixture-project',
             'inspection_hash':inspection,'artifacts':artifacts,
             'verification':{'structural':'NOT_RUN','visual':'NOT_RUN','runtime':'NOT_RUN'},'outcome':'NOT_RUN'}
    return store,store.put_json(receipt),receipt


def test_materializes_only_derived_paths_and_preserves_native_bytes(capture,tmp_path):
    store,h,receipt=capture
    parent=tmp_path/'exports';parent.mkdir()
    out=api().materialize_asset(store,h,parent=parent)
    assert out['verification']=={'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'}
    assert out['outcome']=='NOT_RUN' and out['loaded_revision']=='UNATTESTED'
    dest=Path(out['directory'])
    files={str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()}
    assert files=={'source/kneekura/celestial_staff.bbmodel','assets/kneekura/models/item/celestial_staff.json',
                   'assets/kneekura/textures/item/celestial_staff.png','manifest.json'}
    exported=json.loads((dest/'assets/kneekura/models/item/celestial_staff.json').read_bytes())
    assert exported['textures']=={'0':'kneekura:item/celestial_staff'}
    assert (dest/'source/kneekura/celestial_staff.bbmodel').read_bytes()==store.read(receipt['artifacts'][1]['content_hash'])
    assert store.json(out['manifest_hash'])==json.loads((dest/'manifest.json').read_bytes())
    for item in out['files']:
        assert digest((dest/item['path']).read_bytes())==item['content_hash']
    with pytest.raises(ContractError,match='exist|overwrite'):
        api().materialize_asset(store,h,parent=parent)


@pytest.mark.parametrize('fault',['future_version','wrong_texture_ref','wrong_uv','wrong_geometry','native_texture',
                                   'native_version','png_crc','png_size','duplicate_artifact','missing_view','wrong_request'])
def test_invalid_capture_never_writes_export_or_new_cas(capture,tmp_path,fault):
    store,h,receipt=capture
    r=deepcopy(receipt)
    if fault in ('future_version','wrong_texture_ref','wrong_uv','wrong_geometry'):
        a=r['artifacts'][0];data=store.json(a['content_hash'])
        if fault=='future_version': data['format_version']='26.3'
        if fault=='wrong_texture_ref': data['elements'][0]['faces']['north']['texture']='#undeclared'
        if fault=='wrong_uv': data['elements'][0]['faces']['north']['uv']=[0,0,99,99]
        if fault=='wrong_geometry': data['elements'][0]['to']=[9,32,9]
        raw=canonical(data);a.update(content_hash=store.put(raw),size_bytes=len(raw))
    elif fault in ('native_texture','native_version'):
        a=r['artifacts'][1];data=store.json(a['content_hash'])
        if fault=='native_texture': data['textures'][0]['source']='data:image/png;base64,'+base64.b64encode(png(16,16)).decode()
        else: data['java_block_version']='26.3'
        raw=canonical(data);a.update(content_hash=store.put(raw),size_bytes=len(raw))
    elif fault in ('png_crc','png_size'):
        a=r['artifacts'][2];raw=png(16,16) if fault=='png_size' else png()[:-1]+b'X'
        a.update(content_hash=store.put(raw),size_bytes=len(raw))
    elif fault=='duplicate_artifact': r['artifacts'].append(r['artifacts'][0])
    elif fault=='missing_view': r['artifacts'].pop()
    else: r['request_hash']='0'*64
    h=store.put_json(r);before={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    parent=tmp_path/'exports';parent.mkdir()
    with pytest.raises((ContractError,OSError)):
        api().materialize_asset(store,h,parent=parent)
    assert list(parent.iterdir())==[]
    assert before=={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


def test_symlink_parent_is_refused(capture,tmp_path):
    store,h,_=capture
    real=tmp_path/'real';real.mkdir();link=tmp_path/'link';link.symlink_to(real,target_is_directory=True)
    with pytest.raises(ContractError): api().materialize_asset(store,h,parent=link)
    assert list(real.iterdir())==[]


@pytest.mark.parametrize('fault',['boolean_coordinate','nonfinite_coordinate','new_display_slot','oversize_display','mismatched_display','noncube_native','missing_display'])
def test_structural_negatives_remain_unverified(capture,tmp_path,fault):
    store,h,receipt=capture;r=deepcopy(receipt)
    model=store.json(r['artifacts'][0]['content_hash']);native=store.json(r['artifacts'][1]['content_hash'])
    if fault=='boolean_coordinate': model['elements'][0]['from'][1]=False
    elif fault=='nonfinite_coordinate': model['elements'][0]['from'][0]=float('inf')
    elif fault=='new_display_slot': model['display']=native['display']={'arbitrary':{}}
    elif fault=='oversize_display': model['display']=native['display']={'gui':{'scale':[99,99,99]}}
    elif fault=='mismatched_display': model['display']={'gui':{'scale':[1,1,1]}}
    elif fault=='missing_display': model.pop('display');native.pop('display')
    else: native['elements'][0]['type']='mesh'
    for a,data in zip(r['artifacts'],[model,native]):
        raw=json.dumps(data,allow_nan=True).encode();a.update(content_hash=store.put(raw),size_bytes=len(raw))
    h=store.put_json(r);parent=tmp_path/'exports';parent.mkdir()
    with pytest.raises(ContractError): api().materialize_asset(store,h,parent=parent)
    assert list(parent.iterdir())==[]


def test_explicit_export_cli_uses_the_same_boundaries(capture,tmp_path):
    import subprocess
    import sys
    store,h,_=capture;parent=tmp_path/'exports';parent.mkdir()
    result=subprocess.run([sys.executable,'-m','kneekura_tech_hub.minecraft.assets','--store',str(store.root),
                           'export','--receipt',h,'--parent',str(parent)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
    out=json.loads(result.stdout)
    assert out['verification']=={'structural':'PASS','visual':'NOT_RUN','runtime':'NOT_RUN'}
    assert Path(out['directory']).is_dir()


@pytest.mark.parametrize('field,value',[('gui_light','unknown'),('ambientocclusion','false'),('shade','false')])
def test_export_rejects_invalid_runtime_model_fields(capture,tmp_path,field,value):
    store,h,r=capture;r=deepcopy(r);model=store.json(r['artifacts'][0]['content_hash'])
    if field=='shade': model['elements'][0][field]=value
    else: model[field]=value
    raw=canonical(model);r['artifacts'][0].update(content_hash=store.put(raw),size_bytes=len(raw))
    h=store.put_json(r);parent=tmp_path/'out';parent.mkdir()
    with pytest.raises(ContractError): api().materialize_asset(store,h,parent=parent)
    assert list(parent.iterdir())==[]


@pytest.mark.parametrize('fault',['native_rotation','native_inflate','native_uv','native_face_texture','native_group',
                                  'native_outliner','model_boolean_uv','native_boolean_uv','malformed_meta'])
def test_native_source_and_runtime_model_must_be_structurally_equivalent(capture,tmp_path,fault):
    store,h,receipt=capture;r=deepcopy(receipt)
    model=store.json(r['artifacts'][0]['content_hash']);native=store.json(r['artifacts'][1]['content_hash'])
    source=native['elements'][0]
    if fault=='native_rotation': source['rotation']=[0,0,45]
    elif fault=='native_inflate': source['inflate']=5
    elif fault=='native_uv': source['faces']['north']['uv']=[10,10,12,12]
    elif fault=='native_face_texture': source['faces']['north']['texture']='external'
    elif fault=='native_group': native['groups']=[{'rotation':[45,0,0],'children':native['outliner']}]
    elif fault=='native_outliner': native['outliner']=[{'rotation':[45,0,0],'children':native['outliner']}]
    elif fault=='model_boolean_uv': model['elements'][0]['faces']['north']['uv'][0]=False
    elif fault=='native_boolean_uv': source['faces']['north']['uv'][0]=False
    else: native['meta']=[]
    for a,data in zip(r['artifacts'],[model,native]):
        raw=canonical(data);a.update(content_hash=store.put(raw),size_bytes=len(raw))
    h=store.put_json(r);parent=tmp_path/'out';parent.mkdir()
    with pytest.raises(ContractError): api().materialize_asset(store,h,parent=parent)
    assert list(parent.iterdir())==[]
