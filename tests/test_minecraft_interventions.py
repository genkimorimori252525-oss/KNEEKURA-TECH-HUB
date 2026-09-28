import importlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from kneekura_tech_hub.minecraft.storage import Store, capture_profile, ContractError
from kneekura_tech_hub.minecraft.index import prepare_index
from test_minecraft_storage import manifest


def mod():
    try:
        return importlib.import_module('kneekura_tech_hub.minecraft.interventions')
    except ImportError:
        pytest.fail('Intervention inspection is not implemented')


@pytest.fixture
def inventory(tmp_path):
    src = tmp_path / 'src'; src.mkdir()
    (src / 'fabric.mod.json').write_text(json.dumps({'schemaVersion': 1, 'id': 'demo', 'entrypoints': {'main': ['demo.Init']}, 'mixins': ['demo.mixins.json'], 'accessWidener': 'demo.accesswidener'}))
    (src / 'demo.mixins.json').write_text(json.dumps({'package': 'demo.mixins', 'mixins': ['AttackMixin'], 'client': ['RenderMixin'], 'plugin': 'demo.Plugin', 'refmap': 'demo.refmap.json'}))
    (src / 'demo.accesswidener').write_text('accessWidener v2 intermediary\naccessible method demo/Entity method_1 (I)V\nmutable field demo/Entity field_1 I\n')
    (src / 'META-INF').mkdir()
    (src / 'META-INF/accesstransformer.cfg').write_text('public-f demo.Entity hurt(I)V\npublic demo.Entity field_2 # reason\n')
    store = Store(tmp_path / 'store'); p = capture_profile(manifest(), tmp_path, store)
    idx = prepare_index(p, store)['index_snapshot_id']
    return store, idx, tmp_path


def test_metadata_aw_at_and_conditionals(inventory):
    store, idx, _ = inventory
    out = mod().inspect_interventions(store, idx)
    assert out['status'] == 'PARTIAL'
    rows = out['results']
    aw = next(r for r in rows if r['kind'] == 'access_widener' and r['target']['member'] == 'method_1')
    assert aw['namespace'] == 'intermediary' and aw['target']['descriptor'] == '(I)V'
    at = next(r for r in rows if r['kind'] == 'access_transformer' and r['target'].get('member') == 'hurt')
    assert at['target']['owner'] == 'demo/Entity' and at['target']['descriptor'] == '(I)V'
    mx = next(r for r in rows if r['kind'] == 'mixin_config' and r['mixin'] == 'demo/mixins/RenderMixin')
    assert mx['side'] == 'client' and mx['plugin'] == 'demo.Plugin'
    assert mx['applicability'] == 'CONDITIONAL_NOT_EXECUTED'
    assert all(r.get('evidence') for r in rows)
    assert any('refmap' in str(x) for x in out['coverage']['unresolved'])
    assert out['canonical_writes'] == 0


def test_exact_owner_filter_does_not_claim_no_dynamic_injections(inventory):
    out = mod().inspect_interventions(*inventory[:2], owner='demo/Entity', member='hurt', descriptor='(I)V')
    assert len(out['results']) == 1
    assert out['coverage']['complete'] is False
    assert out['compatibility_verdict'] == 'NOT_DETERMINED'


def test_bad_metadata_is_partial_not_fatal(inventory):
    store, _, root = inventory
    (root / 'src/bad.mixins.json').write_text('{')
    idx = prepare_index(capture_profile(manifest(), root, store), store)['index_snapshot_id']
    out = mod().inspect_interventions(store, idx)
    assert out['results'] and any('bad.mixins.json' in str(x) for x in out['coverage']['unresolved'])


def test_pagination_and_wrong_cursor(inventory):
    store, idx, _ = inventory
    first = mod().inspect_interventions(store, idx, limit=2)
    second = mod().inspect_interventions(store, idx, limit=2, cursor=first['next_cursor'])
    assert len(first['results']) == 2 and first['results'] != second['results']
    assert mod().inspect_interventions(store, idx, owner='other', cursor=first['next_cursor'])['status'] == 'STALE'


def test_real_classfile_annotations(tmp_path):
    java = shutil.which('javac'); assert java, 'javac required'
    src = tmp_path / 'src'; src.mkdir()
    fixtures = {
        'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; import java.lang.annotation.*; @Retention(RetentionPolicy.CLASS) public @interface Mixin { Class<?>[] value() default {}; String[] targets() default {}; }',
        'org/spongepowered/asm/mixin/injection/At.java': 'package org.spongepowered.asm.mixin.injection; public @interface At { String value(); String target() default ""; int ordinal() default -1; }',
        'org/spongepowered/asm/mixin/injection/Inject.java': 'package org.spongepowered.asm.mixin.injection; import java.lang.annotation.*; @Retention(RetentionPolicy.CLASS) public @interface Inject { String[] method(); At at(); int require() default -1; }',
        'demo/Entity.java': 'package demo; public class Entity { public void hurt(int x) {} }',
        'demo/AttackMixin.java': 'package demo; import org.spongepowered.asm.mixin.*; import org.spongepowered.asm.mixin.injection.*; @Mixin(Entity.class) public class AttackMixin { @Inject(method={"hurt(I)V"}, at=@At(value="HEAD"), require=1) private void onHurt() {} }',
    }
    for p, content in fixtures.items():
        f=src/p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(content)
    classes = tmp_path/'classes'
    subprocess.run([java,'--release','17','-d',str(classes), *map(str,src.rglob('*.java'))],check=True,capture_output=True)
    m=manifest(); m['roots'].append(dict(m['roots'][0],id='classes',path='classes',role='binary',stage='compiled'))
    store=Store(tmp_path/'store'); idx=prepare_index(capture_profile(m,tmp_path,store),store)['index_snapshot_id']
    out=mod().inspect_interventions(store,idx,owner='demo/Entity',member='hurt',descriptor='(I)V')
    row=next(r for r in out['results'] if r['kind']=='mixin_injection')
    assert row['source_member']=='onHurt' and row['injection']['at']['elements']['value']=='HEAD'
    assert row['injection']['require']==1
    assert row['evidence']['path']=='demo/AttackMixin.class'
    graph=mod().relations(store,idx,owner='demo/AttackMixin',depth=1)
    assert any(e['relation']=='extends' and e['target']['owner']=='java/lang/Object' for e in graph['results'])
    assert any(e['relation']=='injects' and e['target']['owner']=='demo/Entity' for e in graph['results'])


def test_malformed_class_never_disappears_silently(inventory):
    store,_,root=inventory; (root/'src/bad.class').write_bytes(b'\xca\xfe\xba\xbe')
    idx=prepare_index(capture_profile(manifest(),root,store),store)['index_snapshot_id']
    out=mod().inspect_interventions(store,idx)
    assert any('bad.class' in str(x) for x in out['coverage']['unresolved'])
