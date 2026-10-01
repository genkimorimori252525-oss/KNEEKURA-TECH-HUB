"""Independent bounded asset-repair contracts. Fixtures are not live acceptance."""
import base64
from copy import deepcopy
import importlib
import struct
import zlib

import pytest

from test_minecraft_asset_session import prepared
from test_minecraft_asset_export import capture, png
from kneekura_tech_hub.minecraft.storage import ContractError, canonical, digest


def api():
    return importlib.import_module('kneekura_tech_hub.minecraft.asset_mutation')


def b64(raw):
    return base64.b64encode(raw).decode('ascii')


@pytest.fixture
def sealed(capture):
    store, _, receipt = capture
    native = store.json(receipt['artifacts'][1]['content_hash'])
    native['textures'][0]['uuid'] = 'texture-owned'
    raw = canonical(native)
    receipt['artifacts'][1].update(content_hash=store.put(raw), size_bytes=len(raw))
    snapshot = dict(schema_version=1, request_hash=receipt['request_hash'],
                    project_uuid=receipt['project_uuid'], generation=0,
                    parts=[dict(part_id=e['name'], native_uuid=e['uuid']) for e in native['elements']],
                    texture=dict(texture_id='atlas', native_uuid='texture-owned', width=32, height=32,
                                 rgba=b64(bytes([212,175,55,255])*32*32)),
                    native=native, model=store.json(receipt['artifacts'][0]['content_hash']))
    receipt.update(schema_version=2, generation=0, snapshot_hash=store.put_json(snapshot),
                   parent_receipt_hash=None, mutation_hash=None)
    h = store.put_json(receipt)
    return store, h, receipt, snapshot


def edit(receipt, operation='part_edit'):
    common = dict(schema_version=1, request_hash=receipt['request_hash'],
                  project_uuid=receipt['project_uuid'], expected_generation=receipt['generation'],
                  expected_snapshot_hash=receipt['snapshot_hash'], operation=operation)
    if operation == 'part_edit':
        common.update(target=dict(part_id='head', property='to', axis=1), expected=20, value=19)
    elif operation == 'uv_edit':
        common.update(target=dict(part_id='head', face='north', texture_id='atlas'),
                      expected=[4,0,12,8], value=[24,24,28,28])
    elif operation == 'texture_edit':
        common.update(target=dict(texture_id='atlas', rect=[24,24,32,32]),
                      expected=digest(bytes([212,175,55,255])*8*8), value='#864fc7')
    else:
        common.update(target=dict(slot='gui', property='translation', axis=1), expected=-4, value=-3)
    return common


def rgba_png(raw, width=32, height=32, filter_type=0, rgb=False):
    channels=3 if rgb else 4
    pixels=bytes(v for i,v in enumerate(raw) if not rgb or i%4!=3)
    stride=width*channels; scan=bytearray(); prior=bytes(stride)
    for y in range(height):
        row=pixels[y*stride:(y+1)*stride]; scan.append(filter_type)
        for i,v in enumerate(row):
            a=row[i-channels] if i>=channels else 0; b=prior[i]; c=prior[i-channels] if i>=channels else 0
            p=a+b-c; distances=[abs(p-a),abs(p-b),abs(p-c)]
            prediction=[0,a,b,(a+b)//2,[a,b,c][distances.index(min(distances))]][filter_type]
            scan.append((v-prediction)&255)
        prior=row
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,2 if rgb else 6,0,0,0))+chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b'')


@pytest.mark.parametrize('operation',['part_edit','uv_edit','texture_edit','display_edit'])
def test_four_distinct_mutations_derive_only_the_selected_delta(sealed, operation):
    store,h,receipt,before=sealed
    mutation=api().validate_mutation(store,h,edit(receipt,operation))
    assert mutation['base_receipt_hash']==h and mutation['allowed_delta']
    assert mutation['resulting_generation']==1
    after=api().expected_snapshot(before,mutation)
    if operation=='texture_edit':
        after['native']['textures'][0]['source']='data:image/png;base64,'+b64(rgba_png(base64.b64decode(after['texture']['rgba'])))
    assert api().verify_delta(before,after,mutation)['structural']=='PASS'
    assert before==sealed[3] and after['generation']==1


@pytest.mark.parametrize('fault',['other_part','other_face','other_slot','native_flag','native_root','outliner','identity','pixel'])
def test_complete_unrelated_snapshot_invariance(sealed,fault):
    store,h,r,before=sealed;m=api().validate_mutation(store,h,edit(r));after=api().expected_snapshot(before,m)
    if fault=='other_part': after['native']['elements'][0]['from'][0]=6
    if fault=='other_face': after['native']['elements'][1]['faces']['south']['uv'][0]=5
    if fault=='other_slot': after['native']['display']['ground']['translation'][1]=3
    if fault=='native_flag': after['native']['elements'][1]['hidden']=True
    if fault=='native_root': after['native']['new_behavior']='foreign'
    if fault=='outliner': after['native']['outliner'].reverse()
    if fault=='identity': after['parts'][1]['native_uuid']='recreated'
    if fault=='pixel':
        pixels=bytearray(base64.b64decode(after['texture']['rgba']));pixels[0]=0;after['texture']['rgba']=b64(pixels)
    with pytest.raises(ContractError): api().verify_delta(before,after,m)


@pytest.mark.parametrize('fault',['request','project','generation','hash','old_value','extra','native_selector','bounds','nan','bool','no_op'])
def test_mutation_identity_and_value_rejections_are_read_only(sealed,fault):
    store,h,r,_=sealed;m=edit(r)
    if fault=='request': m['request_hash']='0'*64
    if fault=='project': m['project_uuid']='other'
    if fault=='generation': m['expected_generation']=1
    if fault=='hash': m['expected_snapshot_hash']='0'*64
    if fault=='old_value': m['expected']=21
    if fault=='extra': m['script']='arbitrary'
    if fault=='native_selector': m['target']['uuid']='cube-1'
    if fault=='bounds': m['value']=33
    if fault=='nan': m['value']=float('nan')
    if fault=='bool': m['value']=True
    if fault=='no_op': m['value']=m['expected']
    prior={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(ContractError): api().validate_mutation(store,h,m)
    assert prior=={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('operation,target,value',[
    ('part_edit',dict(part_id='missing',property='to',axis=1),19),
    ('part_edit',dict(part_id='head',property='origin',axis=1),19),
    ('part_edit',dict(part_id='head',property='to',axis=1),15),
    ('uv_edit',dict(part_id='head',face='north',texture_id='other'),[0,0,4,4]),
    ('uv_edit',dict(part_id='head',face='unknown',texture_id='atlas'),[0,0,4,4]),
    ('uv_edit',dict(part_id='head',face='north',texture_id='atlas'),[0,0,33,4]),
    ('uv_edit',dict(part_id='head',face='north',texture_id='atlas'),[0,0,0,4]),
    ('texture_edit',dict(texture_id='atlas',rect=[24,24,33,32]),'#864fc7'),
    ('texture_edit',dict(texture_id='atlas',rect=[24,24,32,32]),'#ffffff'),
    ('display_edit',dict(slot='head',property='translation',axis=1),2),
    ('display_edit',dict(slot='gui',property='scale',axis=1),0),
])
def test_specific_target_boundaries(sealed,operation,target,value):
    store,h,r,_=sealed;m=edit(r,operation);m.update(target=target,value=value)
    with pytest.raises(ContractError): api().validate_mutation(store,h,m)


@pytest.mark.parametrize('filter_type',range(5))
@pytest.mark.parametrize('rgb',[True,False])
def test_png_reconstructs_all_filters_and_rgb_rgba(filter_type,rgb):
    pixels=bytes([i%251 for i in range(32*32*4)])
    if rgb: pixels=bytes(255 if i%4==3 else x for i,x in enumerate(pixels))
    assert api().decode_png_rgba(rgba_png(pixels,filter_type=filter_type,rgb=rgb),[32,32])==pixels


@pytest.mark.parametrize('fault',['crc','size','trailing','truncated','decompression'])
def test_png_integrity_rejection(fault):
    raw=png()
    if fault=='crc':raw=raw[:-1]+b'X'
    if fault=='size':raw=png(16,16)
    if fault=='trailing':raw+=b'x'
    if fault=='truncated':raw=raw[:-12]
    if fault=='decompression':raw=raw.replace(b'IDAT',b'ADAT',1)
    with pytest.raises(ContractError):api().decode_png_rgba(raw,[32,32])


def test_region_edit_rejects_adjacent_pixel_even_with_consistent_new_png(sealed):
    store,h,r,before=sealed;m=api().validate_mutation(store,h,edit(r,'texture_edit'));after=api().expected_snapshot(before,m)
    pixels=bytearray(base64.b64decode(after['texture']['rgba']));pixels[(23+24*32)*4]=0
    after['texture']['rgba']=b64(pixels);after['native']['textures'][0]['source']='data:image/png;base64,'+b64(rgba_png(pixels))
    with pytest.raises(ContractError):api().verify_delta(before,after,m)


def test_legacy_capture_cannot_be_adopted_for_mutation(capture):
    store,h,r=capture
    with pytest.raises(ContractError):api().validate_mutation(store,h,{})


def frame(view='front',size=32):
    return dict(schema_version=1,view=view,projection='perspective',position=[8,16,-75],quaternion=[0,0,0,1],
                up=[0,1,0],target=[8,16,8],projection_matrix=[1]*16,camera_parameters=dict(near=1,far=30000,zoom=1,fov=45,aspect=1),
                viewport=[640,480],canvas=[640,480],output=[size,size],device_pixel_ratio=1,render_mode='edit',
                capture_method='fixed_preview_canvas_v1',render_settings=dict(shading=True))


def session_transport(monkeypatch, sealed, mode='ok', fresh=False):
    from kneekura_tech_hub.minecraft import asset_session as session
    store,h,r,before=sealed; current=deepcopy(before); operations=[]
    config=__import__('kneekura_tech_hub.minecraft.asset_guard',fromlist=['guard_config']).guard_config(store,r['request_hash'],allow_write=True)
    def command(registry,action,p):
        if action=='kneekura_asset_status':
            return dict(guard_protocol=1,state='READY' if fresh else 'OPEN',next_sequence=0 if fresh else 20,
                        project_uuid=None if fresh else r['project_uuid'],busy=False,request_hash=r['request_hash'],
                        loaded_revision='UNATTESTED',last_receipt=None if fresh else dict(completion='CONFIRMED',request_hash=r['request_hash'],project_uuid=r['project_uuid']))
        op=p['operation'];args=p['arguments'];operations.append(op)
        result={}; completion='CONFIRMED'
        if op=='snapshot':
            raw=canonical(current)
            result=dict(kind='snapshot',generation=current['generation'],snapshot_hash=digest(raw),encoding='utf8',content=raw.decode())
        elif op in ('part_edit','uv_edit','texture_edit','display_edit'):
            if mode=='drop': raise ContractError('uncertain transport')
            updated=api().expected_snapshot(current,args); current.clear();current.update(updated)
            if op=='texture_edit':current['native']['textures'][0]['source']='data:image/png;base64,'+b64(rgba_png(base64.b64decode(current['texture']['rgba'])))
            if mode=='unknown':completion='UNKNOWN'
            if mode=='other_field':current['native']['foreign']=True
        elif op=='capture':
            kind=args['kind']
            if mode=='capture_loss' and kind=='native':raise ContractError('capture dropped')
            if kind in ('model','native'):
                result=dict(kind=kind,mime='application/json',encoding='utf8',content=canonical(current[kind]).decode())
            elif kind=='texture':
                result=dict(kind=kind,mime='image/png',encoding='base64',content=current['native']['textures'][0]['source'].split(',')[1])
            else:
                result=dict(kind='view',mime='image/png',encoding='base64',view=args['view'],looking_at='fixture',model_right_on='image_left',note='fixture',content=b64(png()),frame=frame(args['view']),generation=current['generation'])
        return dict(seq=p['seq'],operation=op,completion=completion,project_uuid=r['project_uuid'],request_hash=r['request_hash'],
                    assertion_domain='asset_editor_operation',verification=dict(structural='NOT_RUN',visual='NOT_RUN',runtime='NOT_RUN'),result=result)
    monkeypatch.setattr(session,'_command',command)
    from test_minecraft_asset_session import registry
    return session,config,registry(8787),operations


def test_opt_in_session_seals_generation_zero_and_preserves_default_contract(sealed,monkeypatch):
    store,h,r,_=sealed;session,config,registry,ops=session_transport(monkeypatch,sealed,fresh=True)
    result=session.run_session(store,registry,config,store.json(r['plan_hash']),retain_generation=True)
    saved=store.json(result['receipt_hash']);assert saved['schema_version']==2 and saved['generation']==0
    assert saved['parent_receipt_hash'] is None and saved['mutation_hash'] is None
    assert ops.count('snapshot')==1
    api().load_snapshot(store,result['receipt_hash'])


@pytest.mark.parametrize('operation',['part_edit','uv_edit','texture_edit','display_edit'])
def test_one_shot_session_continuation_retains_confirmed_lineage(sealed,monkeypatch,operation):
    store,h,r,before=sealed;session,config,registry,ops=session_transport(monkeypatch,sealed)
    result=session.run_mutation(store,registry,config,h,edit(r,operation));saved=store.json(result['receipt_hash'])
    assert saved['schema_version']==2 and saved['generation']==1 and saved['parent_receipt_hash']==h
    mutation=store.json(saved['mutation_hash']);assert mutation['base_receipt_hash']==h
    assert ops.count(operation)==1 and result['verification']['runtime']=='NOT_RUN'
    _,after=api().load_snapshot(store,result['receipt_hash']);api().verify_delta(before,after,mutation)


@pytest.mark.parametrize('mode',['drop','unknown','other_field','capture_loss'])
def test_uncertain_or_invalid_continuation_never_retries_or_persists_receipt(sealed,monkeypatch,mode):
    store,h,r,_=sealed;session,config,registry,ops=session_transport(monkeypatch,sealed,mode)
    prior={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(ContractError):session.run_mutation(store,registry,config,h,edit(r))
    assert ops.count('part_edit')==1
    assert prior=={str(p):p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('operation',['part_edit','uv_edit','texture_edit','display_edit'])
def test_repaired_generation_exports_with_independent_chain_validation(sealed,monkeypatch,tmp_path,operation):
    from kneekura_tech_hub.minecraft.asset_export import materialize_asset
    store,h,r,_=sealed;session,config,registry,_=session_transport(monkeypatch,sealed)
    result=session.run_mutation(store,registry,config,h,edit(r,operation));dest=tmp_path/'exports';dest.mkdir()
    output=materialize_asset(store,result['receipt_hash'],parent=dest)
    assert output['verification']==dict(structural='PASS',visual='NOT_RUN',runtime='NOT_RUN')
    with pytest.raises(ContractError):materialize_asset(store,result['receipt_hash'],parent=dest)


@pytest.mark.parametrize('fault',['parent','mutation_hash','generation','allowlist','forged_delta'])
def test_forged_repair_lineage_never_exports(sealed,monkeypatch,tmp_path,fault):
    from kneekura_tech_hub.minecraft.asset_export import materialize_asset
    store,h,r,_=sealed;session,config,registry,_=session_transport(monkeypatch,sealed)
    result=session.run_mutation(store,registry,config,h,edit(r));later=store.json(result['receipt_hash'])
    if fault=='parent':later['parent_receipt_hash']=result['receipt_hash']
    if fault=='mutation_hash':later['mutation_hash']=h
    if fault=='generation':later['generation']=2
    if fault in ('allowlist','forged_delta'):
        m=store.json(later['mutation_hash'])
        if fault=='allowlist':m['allowed_delta'].append('native/*')
        else:m['value']=18
        later['mutation_hash']=store.put_json(m)
    dest=tmp_path/'exports';dest.mkdir()
    with pytest.raises(ContractError):materialize_asset(store,store.put_json(later),parent=dest)
    assert not list(dest.iterdir())


def test_unrelated_nested_boolean_cannot_become_number(sealed):
    store,h,r,before=sealed;m=api().validate_mutation(store,h,edit(r))
    before['native']['elements'][0]['locked']=True
    after=api().expected_snapshot(before,m);after['native']['elements'][0]['locked']=1
    with pytest.raises(ContractError):api().verify_delta(before,after,m)


def test_expected_uv_boolean_cannot_match_numeric_zero(sealed):
    store,h,r,_=sealed;m=edit(r,'uv_edit');m['expected'][1]=False
    with pytest.raises(ContractError):api().validate_mutation(store,h,m)


def test_bounded_cas_read_rejects_oversize_before_full_load_and_preserves_integrity(sealed,monkeypatch):
    from kneekura_tech_hub.minecraft.storage import IntegrityError
    store,_,_,_=sealed;key=store.put(b'x'*1025)
    monkeypatch.setattr(store,'read',lambda *a: (_ for _ in ()).throw(AssertionError('unbounded read')))
    with pytest.raises(ContractError):api().bounded_read(store,key,1024)
    assert api().bounded_read(store,key,1025)==b'x'*1025
    store.blob_path(key).write_bytes(b'y'*1025)
    with pytest.raises(IntegrityError):api().bounded_read(store,key,1025)


def test_nonregular_cas_blob_is_rejected_without_blocking(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path
    from kneekura_tech_hub.minecraft.storage import Store
    if not hasattr(os, 'mkfifo'):
        pytest.skip('POSIX FIFO regression')
    store = Store(tmp_path / 'cas'); key = '8' * 64
    path = store.blob_path(key); path.parent.mkdir(parents=True); os.mkfifo(path)
    child = '''from kneekura_tech_hub.minecraft.asset_mutation import bounded_read
from kneekura_tech_hub.minecraft.storage import Store, ContractError
import sys
try:
    bounded_read(Store(sys.argv[1]), sys.argv[2], 16)
except ContractError:
    raise SystemExit(0)
raise SystemExit(1)
'''
    try:
        result = subprocess.run([sys.executable, '-c', child, str(store.root), key],
            capture_output=True, text=True, timeout=2,
            env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1] / 'src')})
    except subprocess.TimeoutExpired:
        pytest.fail('bounded asset CAS read blocked on a FIFO')
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('replacement', ['regular', 'fifo'])
def test_bounded_read_rejects_replacement_between_stat_and_open(sealed, monkeypatch, replacement):
    import os
    store, _, _, _ = sealed; raw = b'owned'; key = store.put(raw); path = store.blob_path(key)
    real_open = os.open
    def swapped_open(target, flags, *args, **kwargs):
        # A nonblocking open is necessary even after a successful regular-file lstat.
        assert flags & os.O_NONBLOCK
        path.rename(path.with_suffix('.prior'))
        if replacement == 'fifo': os.mkfifo(path)
        else: path.write_bytes(raw)
        return real_open(target, flags, *args, **kwargs)
    monkeypatch.setattr(api().os, 'open', swapped_open)
    with pytest.raises(ContractError): api().bounded_read(store, key, 16)


def test_bounded_read_rejects_metadata_change_during_read(sealed, monkeypatch):
    import os
    store, _, _, _ = sealed; key = store.put(b'owned'); path = store.blob_path(key)
    real_fstat = os.fstat; calls = []
    def changed_fstat(fd):
        calls.append(fd)
        if len(calls) == 2:
            metadata = path.stat()
            os.utime(path, ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1_000_000))
        return real_fstat(fd)
    monkeypatch.setattr(api().os, 'fstat', changed_fstat)
    with pytest.raises(ContractError): api().bounded_read(store, key, 16)


def transparent_gold_png():
    raw = rgba_png(bytes([212,175,55,255]) * 32 * 32, rgb=True)
    data = struct.pack('>HHH', 212, 175, 55); kind = b'tRNS'
    chunk = struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    return raw[:33] + chunk + raw[33:]


def test_rgb_png_transparency_is_not_silently_decoded_as_opaque():
    with pytest.raises(ContractError, match='transparen|tRNS'):
        api().decode_png_rgba(transparent_gold_png(), [32,32])


def test_schema2_export_rejects_consistent_transparent_png_without_writes(sealed, tmp_path):
    from kneekura_tech_hub.minecraft.asset_export import materialize_asset
    store, _, receipt, snapshot = sealed; raw = transparent_gold_png()
    snapshot['native']['textures'][0]['source'] = 'data:image/png;base64,' + b64(raw)
    native = canonical(snapshot['native'])
    receipt['artifacts'][1].update(content_hash=store.put(native), size_bytes=len(native))
    receipt['artifacts'][2].update(content_hash=store.put(raw), size_bytes=len(raw))
    receipt['snapshot_hash'] = store.put_json(snapshot); key = store.put_json(receipt)
    destination = tmp_path / 'export'; destination.mkdir()
    prior = {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(ContractError): materialize_asset(store, key, parent=destination)
    assert not list(destination.iterdir())
    assert prior == {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('generation', [False, 0.0, True, 1.0, -1, 33])
@pytest.mark.parametrize('entrypoint', ['snapshot', 'export'])
def test_receipt_generation_requires_exact_bounded_integer(sealed, tmp_path, generation, entrypoint):
    from kneekura_tech_hub.minecraft.asset_export import materialize_asset
    store, _, receipt, _ = sealed; receipt['generation'] = generation; key = store.put_json(receipt)
    destination = tmp_path / 'export'; destination.mkdir()
    prior = {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(ContractError):
        if entrypoint == 'snapshot': api().load_snapshot(store, key)
        else: materialize_asset(store, key, parent=destination)
    assert not list(destination.iterdir())
    assert prior == {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('entrypoint', ['mutation', 'export'])
def test_schema2_validation_never_reopens_legacy_request_unbounded(sealed, monkeypatch, entrypoint):
    from kneekura_tech_hub.minecraft.asset_export import _validate_capture
    store, key, receipt, _ = sealed
    prior = {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    def unbounded_read(key): raise AssertionError('validation reopened an unbounded Store.read')
    monkeypatch.setattr(store, 'read', unbounded_read)
    if entrypoint == 'mutation':
        assert api().validate_mutation(store, key, edit(receipt))['resulting_generation'] == 1
    else:
        assert _validate_capture(store, key)[0]['generation'] == 0
    assert prior == {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('field', ['request_hash', 'plan_hash'])
def test_schema2_rejects_oversized_legacy_records_before_writes_or_commands(sealed, monkeypatch, field):
    store, key, receipt, _ = sealed
    session, config, registry, operations = session_transport(monkeypatch, sealed)
    # Sparse oversized backing bytes at a declared valid identity must never be loaded whole.
    with store.blob_path(receipt[field]).open('wb') as stream: stream.truncate(17 * 1024 * 1024)
    prior = {str(p): p.stat().st_size for p in store.root.rglob('*') if p.is_file()}
    def unbounded_read(key): raise AssertionError('validation reopened an unbounded Store.read')
    monkeypatch.setattr(store, 'read', unbounded_read)
    with pytest.raises(ContractError): session.run_mutation(store, registry, config, key, edit(receipt))
    assert operations == []
    assert prior == {str(p): p.stat().st_size for p in store.root.rglob('*') if p.is_file()}


@pytest.mark.parametrize('fresh', [False, True])
def test_generation_session_reads_are_bounded_before_persistence(sealed, monkeypatch, fresh):
    store, key, receipt, _ = sealed
    plan = store.json(receipt['plan_hash'])
    session, config, registry, operations = session_transport(monkeypatch, sealed, fresh=fresh)
    real_persist = session._persist_capture; real_read = store.read; persisting = False
    def guarded_read(key):
        assert persisting, 'unbounded read before capture persistence'
        return real_read(key)
    def persist(*args, **kwargs):
        nonlocal persisting
        persisting = True
        return real_persist(*args, **kwargs)
    monkeypatch.setattr(store, 'read', guarded_read)
    monkeypatch.setattr(session, '_persist_capture', persist)
    if fresh: result = session.run_session(store, registry, config, plan, retain_generation=True)
    else: result = session.run_mutation(store, registry, config, key, edit(receipt))
    assert result['generation'] == (0 if fresh else 1)
    assert api().load_snapshot(store, result['receipt_hash'])[0]['generation'] == result['generation']


def test_bounded_read_preserves_preloaded_bundle_protocol_and_checks_hash_and_size():
    from kneekura_tech_hub.minecraft.storage import IntegrityError
    class ReadOnlyBundle:
        def read(self, key): return b'owned'
    bundle = ReadOnlyBundle(); key = digest(b'owned')
    assert api().bounded_read(bundle, key, 5) == b'owned'
    with pytest.raises(ContractError): api().bounded_read(bundle, key, 4)
    with pytest.raises(IntegrityError): api().bounded_read(bundle, digest(b'other'), 5)


@pytest.mark.parametrize('protocol', [True, 1.0])
def test_mutation_status_protocol_requires_exact_integer_before_mutation(sealed, monkeypatch, protocol):
    store, key, receipt, _ = sealed
    session, config, registry, operations = session_transport(monkeypatch, sealed)
    command = session._command
    def wrong_protocol(registry, action, params):
        result = command(registry, action, params)
        if action == 'kneekura_asset_status': result['guard_protocol'] = protocol
        return result
    monkeypatch.setattr(session, '_command', wrong_protocol)
    prior = {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
    with pytest.raises(ContractError): session.run_mutation(store, registry, config, key, edit(receipt))
    assert operations == []
    assert prior == {str(p): p.read_bytes() for p in store.root.rglob('*') if p.is_file()}
