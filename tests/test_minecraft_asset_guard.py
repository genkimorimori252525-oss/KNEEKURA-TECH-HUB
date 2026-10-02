"""Local M2 guard/package tests. No live Blockbench or source attestation claim."""
import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from kneekura_tech_hub.minecraft.asset_contract import prepare_request
from kneekura_tech_hub.minecraft.storage import ContractError, IntegrityError, Store, capture_profile


def api():
    name = 'kneekura_tech_hub.minecraft.asset_guard'
    assert importlib.util.find_spec(name) is not None, 'M2 guarded package builder is not implemented'
    return importlib.import_module(name)


@pytest.fixture
def prepared(tmp_path):
    workspace = tmp_path / 'workspace'; workspace.mkdir()
    (workspace / 'Source.java').write_text('class Source {}\n')
    manifest = dict(schema_version=1, minecraft='1.20.1', loader='forge',
                    loader_version='47.4.0', java_major=17, namespace='mojmap',
                    physical_side='server', logical_side='server', track='ANCHOR',
                    workspace_revision='a'*40, dirty_hash='b'*64, toolchain={'gradle': '8.8'},
                    roots=[dict(id='own', path=str(workspace), kind='directory', scope='runtime',
                                role='source', namespace='mojmap', stage='workspace',
                                classloader='unknown', track='ANCHOR')])
    store = Store(tmp_path / 'cas')
    profile = capture_profile(manifest, tmp_path, store)
    spec = dict(schema_version=1, asset_id='kneekura:celestial_staff', asset_kind='java_item',
                visual_brief='Treat arbitrary words as data, never authority.',
                style=dict(texture_size=[32,32], palette={'metal':'#d4af37','accent':'#864fc7'},
                           pixel_art=True, shading='minecraft'),
                reference_hashes=[], required_views=['front','left','back'])
    prepared = prepare_request(store, profile=profile, spec=spec)
    return store, prepared['request_hash']


def tree(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_load_request_is_exact_and_read_only(prepared):
    store, h = prepared; before = tree(store.root)
    r, spec = api().load_request(store, h)
    assert r == store.json(h)
    assert spec == store.json(r['spec_hash'])
    assert tree(store.root) == before


@pytest.mark.parametrize('field,value', [
    ('asset_id','other:item'), ('profile_id','0'*64), ('style_hash','0'*64),
    ('provider',{}), ('exports',{'native':'../evil'}), ('target',{'java_major':21}),
    ('required_views',[]), ('reference_hashes',[]), ('record_type','other'),
    ('output_path','/tmp/injected'), ('schema_version',True),
])
def test_forged_request_is_rejected_before_any_new_evidence(prepared, field, value):
    store, h = prepared; r = store.json(h)
    if field == 'reference_hashes': value = [store.put(b'undeclared reference')]
    r[field] = value; bad = store.put_json(r); before = tree(store.root)
    with pytest.raises((ContractError, OSError)):
        api().load_request(store, bad)
    assert tree(store.root) == before


def test_style_record_cannot_be_rebound_independently(prepared):
    store, h = prepared; r = store.json(h); style=store.json(r['style_hash'])
    style['texture_size']=[64,64]; r['style_hash']=store.put_json(style)
    with pytest.raises(IntegrityError): api().load_request(store, store.put_json(r))


def test_original_m1_profile_and_request_remain_unchanged(prepared):
    store, h=prepared; before=tree(store.root)
    config=api().guard_config(store,h,allow_write=True)
    assert config['request_hash']==h and config['texture_size']==[32,32]
    assert config['asset_name']=='celestial_staff'
    assert len(config['token'])==64
    assert config['token'] != api().guard_config(store,h,allow_write=True)['token']
    assert tree(store.root)==before


def test_config_is_disabled_by_default_and_has_no_brief_or_filesystem(prepared):
    store,h=prepared; config=api().guard_config(store,h)
    assert config['allow_write'] is False
    assert 'visual_brief' not in config and 'path' not in config


@pytest.mark.parametrize('flag',[1,'true',None,[],{}])
def test_write_enable_requires_boolean(prepared, flag):
    store,h=prepared
    with pytest.raises(ContractError): api().guard_config(store,h,allow_write=flag)


def test_wrong_plugin_bytes_are_rejected_before_package_exists(prepared,tmp_path):
    store,h=prepared
    before=tree(store.root)
    with pytest.raises(IntegrityError):
        api().prepare_guarded_package(store,h,upstream=b'not pinned code', parent=tmp_path)
    assert tree(store.root)==before
    assert not list(tmp_path.glob('blockbench-asset-*'))


@pytest.mark.parametrize('payload',[b'',b'x'*1048577,'not bytes',None])
def test_unbounded_or_invalid_plugin_is_rejected(payload):
    with pytest.raises(ContractError): api().verify_upstream(payload)


def test_recipe_has_exact_dispatch_and_never_enables_raw_routes():
    m=api()
    fixture='(function () {\n'+m.UPSTREAM_DISPATCH+'\n'+m.UPSTREAM_BODY_LIMIT+'\n'+m.UPSTREAM_AUTOSTART+'\n})();\n'
    config=m.validate_config(dict(schema_version=1,request_hash='a'*64, token='b'*64,
        asset_name='staff',texture_size=[32,32],palette=['#d4af37'],allow_write=False))
    assembled=m.assemble_reviewed_source(fixture,config)
    assert m.UPSTREAM_DISPATCH not in assembled
    assert 'kneekuraGuard.dispatch(action, params)' in assembled
    assert '96 * 1024 * 1024' not in assembled
    assert config['token'] in assembled
    assert 'capture: async' in m.HOST_ADAPTER
    assert "require('fs')" not in m.HOST_ADAPTER
    assert 'writeFile' not in m.HOST_ADAPTER
    assert 'export_model' not in m.HOST_ADAPTER
    assert 'export_project' not in m.HOST_ADAPTER
    assert 'save_project' not in m.HOST_ADAPTER
    syntax=subprocess.run(['node','--check','-'],input=assembled,text=True,capture_output=True)
    assert syntax.returncode==0,syntax.stderr


@pytest.mark.parametrize('mutation',['missing','duplicate','changed','existing_guard'])
def test_recipe_fails_closed_on_patch_drift(mutation):
    m=api(); src='(function () {\n'+m.UPSTREAM_DISPATCH+'\n'+m.UPSTREAM_BODY_LIMIT+'\n'+m.UPSTREAM_AUTOSTART+'\n})();'
    if mutation=='missing': src=src.replace(m.UPSTREAM_DISPATCH,'')
    if mutation=='duplicate': src+=m.UPSTREAM_DISPATCH
    if mutation=='changed': src=src.replace('handler(params || {})','handler(params)')
    if mutation=='existing_guard': src+='kneekuraGuard'
    with pytest.raises(ContractError): m.assemble_reviewed_source(src,{})


def test_no_overwrite_publish_and_private_files(tmp_path):
    m=api(); dest=tmp_path/'new'; files={'blockbench_mcp.js':b'test secret','client-private.json':b'{}'}
    m.write_private_bundle(dest,files)
    assert (dest/'blockbench_mcp.js').read_bytes()==b'test secret'
    before=tree(dest)
    with pytest.raises((ContractError,FileExistsError)): m.write_private_bundle(dest,files)
    assert tree(dest)==before
    if sys.platform != 'win32':
        assert dest.stat().st_mode & 0o777 == 0o700
        assert (dest/'client-private.json').stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize('name',['../escape','/abs','x/y','..','x\\y','other.txt'])
def test_private_bundle_rejects_unrecognized_filenames_before_mkdir(tmp_path,name):
    dest=tmp_path/'new'
    with pytest.raises(ContractError): api().write_private_bundle(dest,{name:b'data'})
    assert not dest.exists()


def test_private_bundle_filename_preserves_upstream_plugin_id(tmp_path):
    m=api(); dest=tmp_path/'new'
    files={'blockbench_mcp.js':b'plugin source','client-private.json':b'{}'}
    m.write_private_bundle(dest,files)
    assert (dest/'blockbench_mcp.js').read_bytes()==b'plugin source'
    assert not (dest/'guarded-plugin.js').exists()


def test_private_bundle_rejects_symlink_parent(tmp_path):
    real=tmp_path/'real'; real.mkdir(); alias=tmp_path/'alias'; alias.symlink_to(real,target_is_directory=True)
    with pytest.raises(ContractError): api().write_private_bundle(alias/'new',{'blockbench_mcp.js':b'test','client-private.json':b'{}'})
    assert not list(real.iterdir())


def test_node_guard_contract_suite(tmp_path):
    m=api()
    factory=tmp_path/'factory.cjs'; factory.write_text('module.exports = '+m.GUARD_FACTORY+';\n')
    script=Path(__file__).with_name('minecraft_asset_guard.node.cjs')
    p=subprocess.run(['node','--test',str(script)],env={**__import__('os').environ,'KNEEKURA_TEST_GUARD':str(factory)},
                     capture_output=True,text=True,timeout=25)
    (tmp_path/'node-output.txt').write_text(p.stdout+p.stderr)
    assert p.returncode==0,p.stdout+p.stderr


def test_recipe_forces_manual_start_even_when_upstream_setting_would_autostart():
    m=api()
    upstream_autostart="""\tif (autostartSetting.value && isApp) {
\t\ttry {
\t\t\tstartServer(getPort());
\t\t} catch (e) {
\t\t\tconsole.error('[BlockbenchMCP] autostart failed:', e);
\t\t}
\t}"""
    fixture='(function () {\n'+m.UPSTREAM_DISPATCH+'\n'+m.UPSTREAM_BODY_LIMIT+'\n'+upstream_autostart+'\n})();'
    config=dict(schema_version=1,request_hash='a'*64,token='b'*64,asset_name='staff',texture_size=[32,32],palette=['#d4af37'],allow_write=False)
    source=m.assemble_reviewed_source(fixture,config)
    assert upstream_autostart not in source
    assert 'autostartSetting.value && isApp' not in source


@pytest.mark.parametrize('value',[object(),{'x':float('nan')},{'x':b'non-json'}])
def test_bad_configuration_has_contract_error(value):
    with pytest.raises(ContractError): api().validate_config(value)


def test_partial_private_package_stays_visible_and_cannot_be_reused(tmp_path,monkeypatch):
    import os
    m=api(); original=os.open; dest=tmp_path/'partial'
    def fail_second(name,*args,**kwargs):
        if str(name).endswith('client-private.json'):raise OSError('fixture: disk write denied')
        return original(name,*args,**kwargs)
    with monkeypatch.context() as context:
        context.setattr(os,'open',fail_second)
        with pytest.raises(OSError):m.write_private_bundle(dest,{'blockbench_mcp.js':b'kept','client-private.json':b'{}'})
    assert (dest/'blockbench_mcp.js').read_bytes()==b'kept'
    assert not (dest/'client-private.json').exists()
    with pytest.raises(ContractError):m.write_private_bundle(dest,{'blockbench_mcp.js':b'replace','client-private.json':b'{}'})
    assert (dest/'blockbench_mcp.js').read_bytes()==b'kept'


def test_cli_rejects_unpinned_source_without_network_or_output_directory(prepared,tmp_path):
    store,h=prepared; source=tmp_path/'wrong.js';source.write_text('invalid-source')
    target=tmp_path/'output';target.mkdir()
    p=subprocess.run([sys.executable,'-m','kneekura_tech_hub.minecraft.asset_guard','--store',str(store.root),
        '--request',h,'--upstream',str(source),'--parent',str(target)],capture_output=True,text=True,timeout=5)
    assert p.returncode==2
    assert json.loads(p.stdout)['status']=='ERROR'
    assert not list(target.iterdir())


@pytest.mark.parametrize('where',['cas','cas_subdirectory','git','git_subdirectory','worktree'])
def test_secret_package_parent_must_be_outside_cas_and_git(tmp_path,where):
    store=Store(tmp_path/'cas');store.root.mkdir()
    repository=tmp_path/'repo';repository.mkdir();(repository/'.git').mkdir()
    worktree=tmp_path/'linked';worktree.mkdir();(worktree/'.git').write_text('gitdir: /some/repo/worktrees/linked\n')
    parent={'cas':store.root,'cas_subdirectory':store.root/'nested','git':repository,
        'git_subdirectory':repository/'nested','worktree':worktree}[where]
    parent.mkdir(exist_ok=True)
    before=tree(tmp_path)
    module=api()
    assert hasattr(module,'validate_package_parent'),'secret destination policy missing'
    with pytest.raises(ContractError):module.validate_package_parent(store,parent)
    assert tree(tmp_path)==before


def test_private_parent_validation_allows_real_external_directory(tmp_path):
    store=Store(tmp_path/'cas');parent=tmp_path/'private';parent.mkdir()
    module=api()
    assert hasattr(module,'validate_package_parent'),'secret destination policy missing'
    assert module.validate_package_parent(store,parent)==parent.absolute()


def test_trusted_host_configures_only_owned_project_and_exports_exact_display():
    m = api()
    script = '''
    const assert = require('node:assert/strict');
    globalThis.performance={now:()=>0};
    globalThis.Project={uuid:'owned',java_block_version:'26.3',display_settings:{}};
    globalThis.ModelProject={all:[Project]}; globalThis.Format={id:'java_block'};
    globalThis.Plugins={all:[{id:'blockbench_mcp',installed:true}]};
    globalThis.Cube={all:[]};globalThis.Texture={all:[]};
    const kneekuraPreviousServer=false;
    globalThis.DisplayMode={loadJSON:values=>{
      for(const [key,value] of Object.entries(values)) Project.display_settings[key]={export:()=>value};
    }};
    globalThis.settings = new Proxy({}, {get:()=>{throw new Error('must not read global defaults')},set:()=>{throw new Error('must not change global defaults')}});
    const host=HOST_ADAPTER;
    const policy=POLICY;
    assert.throws(()=>host.configureProject({uuid:'foreign'},policy));
    assert.equal(Project.java_block_version,'26.3');
    host.configureProject(Project,policy);
    assert.equal(Project.java_block_version,'1.9.0');
    assert.equal(host.state().java_block_version,'1.9.0');
    assert.deepEqual(host.state().display,policy.display);
    '''.replace('HOST_ADAPTER', m.HOST_ADAPTER).replace('POLICY', json.dumps({
        'java_block_version': '1.9.0', 'display': {'gui': {'scale': [0.5, 0.5, 0.5]}}}))
    run = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=5)
    assert run.returncode == 0, run.stderr


def test_trusted_host_awaits_bound_texture_decode_after_palette_paint():
    script = '''
    const assert=require('node:assert/strict');
    let finishDecode, calls=0;
    const image={complete:true,naturalWidth:32,naturalHeight:32,
      decode:()=>new Promise(resolve=>{finishDecode=()=>{image.complete=true;resolve();};})};
    globalThis.Texture={all:[{uuid:'owned',img:image,width:32,height:32}]};
    const commands={paint_texture:args=>{calls++;assert.equal(args.texture,'owned');image.complete=false;return {painted:true};}};
    const host=HOST_ADAPTER;
    (async()=>{
      let settled=false;
      const painting=host.invoke('paint_texture',{texture:'owned'});
      Promise.resolve(painting).then(()=>{settled=true;});
      await Promise.resolve();await Promise.resolve();
      assert.equal(calls,1);assert.equal(settled,false,'paint must wait for the changed bitmap');
      assert.equal(typeof finishDecode,'function');finishDecode();
      assert.deepEqual(await painting,{painted:true});
    })().catch(e=>{console.error(e);process.exitCode=1;});
    '''.replace('HOST_ADAPTER', api().HOST_ADAPTER)
    run=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=5)
    assert run.returncode == 0, run.stderr


def test_fixed_item_policy_is_already_in_pinned_display_slot_export_form():
    # Blockbench e2ede0809ee6bc91f374ac7e00d34cffbdf86a14 DisplaySlot.extend
    # applies Math.trimDeg=(a+180*15)%360-180 before both codecs export.
    policy = api().ITEM_DISPLAY
    assert len(policy) == 7
    for transform in policy.values():
        for angle in transform.get('rotation', []):
            assert (angle + 180 * 15) % 360 - 180 == angle
        assert transform.get('rotation') != [0, 0, 0]
        assert transform.get('translation') != [0, 0, 0]
        assert transform.get('scale') != [1, 1, 1]


def test_native_capture_embeds_bitmap_without_reading_global_preference():
    script = '''
    const assert=require('node:assert/strict');
    let options;
    globalThis.Codecs={project:{compile:arg=>{options=arg;return {meta:{model_format:'java_block'}}}}};
    globalThis.Settings={get:()=>{throw new Error('global preference must not control capture')}};
    const host=HOST;
    host.capture('native',{}).then(value=>{
      assert.equal(options.bitmaps,true);
      assert.equal(options.absolute_paths,false);
      assert.equal(value.kind,'native');
    }).catch(error=>{console.error(error);process.exitCode=1});
    '''.replace('HOST',api().HOST_ADAPTER)
    result=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stderr


def test_node_retained_repair_contract_suite(tmp_path):
    factory=tmp_path/'repair-factory.cjs'; factory.write_text('module.exports = '+api().GUARD_FACTORY+';\n')
    script=Path(__file__).with_name('minecraft_asset_repair.node.cjs')
    result=subprocess.run(['node','--test',str(script)],env={**__import__('os').environ,'KNEEKURA_TEST_GUARD':str(factory)},
                          capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr


def test_host_snapshot_uses_exact_owned_objects_full_codecs_and_pixels():
    script = '''
    const assert=require('node:assert/strict');
    const cube={uuid:'cube',name:'head'},tex={uuid:'tex',width:16,height:16,ctx:{getImageData:()=>({data:new Uint8Array(1024)})}};
    globalThis.Cube={all:[cube]};globalThis.Texture={all:[tex]};
    globalThis.Format={codec:{compile:()=>JSON.stringify({elements:[{name:'head'}]})}};
    globalThis.Codecs={project:{compile:options=>{assert.equal(options.bitmaps,true);return {elements:[{uuid:'cube'}]};}}};
    const host=HOST;
    assert.equal(host.elementIdentity('cube'),cube);assert.equal(host.textureIdentity('tex'),tex);
    Cube.all.push({uuid:'cube'});assert.equal(host.elementIdentity('cube'),null);Cube.all.pop();
    const s=host.snapshot();assert.equal(s.model.elements[0].name,'head');assert.equal(s.native.elements[0].uuid,'cube');assert.equal(atob(s.rgba).length,1024);
    '''.replace('HOST',api().HOST_ADAPTER)
    p=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=5)
    assert p.returncode==0,p.stderr


def test_frozen_view_reuses_camera_without_geometry_refit():
    script='''
    const assert=require('node:assert/strict');let fits=0,renders=0;
    function vector(values){return {values:values.slice(),toArray(){return this.values.slice()},fromArray(a){this.values=a.slice();return this}};}
    const camera={position:vector([1,2,3]),quaternion:vector([0,0,0,1]),up:vector([0,1,0]),near:1,far:30000,zoom:1,fov:45,aspect:1,projectionMatrix:vector(Array(16).fill(1)),updateProjectionMatrix(){},updateMatrixWorld(){}};
    const preview={id:'main',width:640,height:480,isOrtho:false,camera,controls:{target:vector([0,0,0]),update(){}},setProjectionMode(v){this.isOrtho=v},render(){if(++renders>1)camera.position.values[0]+=1e-9;},renderer:{render(){},domElement:{width:640,height:480},getPixelRatio:()=>1,toneMapping:0,toneMappingExposure:1}};
    globalThis.Preview={selected:preview};globalThis.Mode={selected:{id:'edit'}};globalThis.settings={shading:{value:true}};
    globalThis.Canvas={scene:{background:null}};globalThis.devicePixelRatio=1;
    globalThis.document={createElement:()=>({width:0,height:0,getContext:()=>({clearRect(){},drawImage(){}}),toDataURL:()=> 'data:image/png;base64,iVBORw0KGgo='})};
    const applyAngleName=(p,v)=>{fits++;p.camera.position.fromArray([8,16,-75]);return {view:v,looking_at:'front',model_right_on:'image_left',note:''}};
    const describeView=v=>({view:v,looking_at:'front',model_right_on:'image_left',note:''});
    const commands={screenshot:()=>{throw Error('must not auto-refit frozen views')}};
    const host=HOST;
    (async()=>{
      const before=await host.capture('view',{view:'front',freeze:true,generation:0});
      camera.position.fromArray([900,900,900]);preview.controls.target.fromArray([90,90,90]);
      const after=await host.capture('view',{view:'front',freeze:true,generation:1});
      assert.equal(fits,1);assert.deepEqual(before.frame,after.frame);assert.deepEqual(after.frame.position,[8,16,-75]);assert.equal(after.generation,1);assert.deepEqual(after.frame.canvas,[640,480]);assert.deepEqual(after.frame.output,[320,320]);
      preview.renderer.domElement.width=700;
      const changed=await host.capture('view',{view:'front',freeze:true,generation:1});assert.notDeepEqual(changed.frame,before.frame);
    })().catch(e=>{console.error(e);process.exitCode=1});
    '''.replace('HOST',api().HOST_ADAPTER)
    p=subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=5)
    assert p.returncode==0,p.stderr
