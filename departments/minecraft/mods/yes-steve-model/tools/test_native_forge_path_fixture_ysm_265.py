"""Authored classfiles and direct JNI model calls only; no guest instructions/JVM."""
import copy
import hashlib
import io
import struct
import unittest
from unittest.mock import patch
import native_forge_path_fixture_ysm_265 as paths
import native_forge_runtime_fixture_ysm_265 as forge
from native_java_metadata_ysm_265 import JavaMetadata
from native_jni_fixture_ysm_265 import JniGuardedCPU, TRAPS, VERSION
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_unicorn_guarded_ysm_265 import ModelHalt, SP
from test_native_java_metadata_ysm_265 import archive, class_bytes
RET = 0x100000


class ForgePathTests(unittest.TestCase):
    def setUp(self):
        classes = {
            paths.FML_PATHS: class_bytes(paths.FML_PATHS, fields=[
                (16409, 'CONFIGDIR', 'L'+paths.FML_PATHS+';'), (2, 'absolutePath', 'L'+paths.PATH+';')]),
            paths.PATH: class_bytes(paths.PATH, methods=[
                (1025, 'normalize', '()L'+paths.PATH+';'), (1025, 'toString', '()Ljava/lang/String;'),
                (1025, 'toAbsolutePath', '()L'+paths.PATH+';')]),
            forge.ENV: class_bytes(forge.ENV, fields=[(9, 'production', 'Z'), (9, 'dist', forge.DESC)]),
            forge.DIST: class_bytes(forge.DIST, fields=[(16409, 'CLIENT', forge.DESC)])}
        for name in {*paths.PINS, *forge.PINS}:
            classes.setdefault(name, class_bytes(name))
        data = archive({k+'.class': v for k, v in classes.items() if k.startswith('net/')})
        java = archive({'classes/'+k+'.class': v for k, v in classes.items() if not k.startswith('net/')}, jmod=True)
        digest = hashlib.sha256(data).hexdigest()
        for module in (paths, forge):
            pins = patch.dict(module.PINS, {k: (digest if k.startswith('net/') else hashlib.sha256(java).hexdigest(), hashlib.sha256(classes[k]).hexdigest()) for k in module.PINS}, clear=True)
            pins.start(); self.addCleanup(pins.stop)
        self.metadata = JavaMetadata.from_buffers(java_base=java, dependency_buffers={'own-byte': (data, digest)})

    def fresh(self, cls=paths.ForgePathCPU):
        c = cls(io.StringIO(), 'heap', limit=1)
        c.add_image(RET, b'\x90'*16); c.protect_image()
        return c

    def cpu(self, state='absolute-field-populated', configured=True):
        c = self.fresh(); c.configure_jni(); c.configure_java_metadata(self.metadata)
        if configured: c.configure_forge_paths(state, game_path='/fixture/ysm-game' if state == 'absolute-field-populated' else None, provider=paths.PROVIDER)
        return c

    def string(self, c, text):
        data = text.encode()+b'\0'; ptr = c.reserve_fixture(len(data)); c.write_private(ptr, data); return ptr

    def call(self, c, slot, *args):
        c.stop = None; c.pc = TRAPS+(8+slot)*16; c.reg('RSP', SP)
        c.write_private(SP, struct.pack('<Q', RET)); c.reg('RDI', c.jni_state['env'])
        for reg in ('RSI', 'RDX', 'RCX'): c.reg(reg, 0)
        for reg, value in zip(('RSI', 'RDX', 'RCX'), args): c.reg(reg, value)
        c.model('jni-import'); return c.reg('RAX')

    def member(self, c, owner, name, descriptor, slot):
        cls = self.call(c, 6, self.string(c, owner))
        return cls, self.call(c, slot, cls, self.string(c, name), self.string(c, descriptor))

    def enum(self, c):
        return self.call(c, 145, *self.member(c, paths.FML_PATHS, 'CONFIGDIR', 'L'+paths.FML_PATHS+';', 144))

    def path(self, c):
        enum = self.enum(c)
        _, field = self.member(c, paths.FML_PATHS, 'absolutePath', 'L'+paths.PATH+';', 94)
        return self.call(c, 95, enum, field)

    def method(self, c, ref, name, slot=35):
        _, method = self.member(c, paths.PATH, name, '()L'+(paths.STRING if name == 'toString' else paths.PATH)+';', 33)
        return self.call(c, slot, ref, method, 0)

    def test_state_independent_of_runtime_and_null_field(self):
        c = self.cpu(configured=False)
        c.configure_forge_runtime('forgeclient', initialized=True, production_property_present=False)
        with self.assertRaises(ModelHalt): self.enum(c)
        self.assertIsNone(c.forge_paths)
        c.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER)
        self.assertEqual(self.path(c), 0)
        with self.assertRaises(ValueError): c.configure_forge_paths('absolute-field-populated', game_path='/fixture/ysm-game', provider=paths.PROVIDER)
        c = self.cpu(); self.assertIsNone(c.forge_runtime); self.assertNotEqual(self.path(c), 0)
        self.assertFalse(c.forge_paths['config']['forge_setup_success_claimed'])

    def test_exact_identities_aliases_global_and_local_deletion(self):
        c = self.cpu(); p = self.path(c)
        self.assertEqual(self.call(c, 24, 0, 0), 1)
        self.assertEqual(self.call(c, 24, p, 0), 0)
        self.assertEqual(self.call(c, 21, 0), 0)
        self.assertEqual(self.call(c, 25, 0), 0)
        self.call(c, 22, 0); self.call(c, 23, 0)
        q = self.method(c, p, 'normalize'); self.assertNotEqual(p, q)
        self.assertEqual(self.call(c, 24, p, q), 1)
        g = self.call(c, 21, p); local = self.call(c, 25, g)
        self.call(c, 23, p); self.call(c, 23, q)
        self.assertEqual(self.call(c, 24, g, local), 1)
        with self.assertRaises(ModelHalt): self.call(c, 23, g)
        with self.assertRaises(ModelHalt): self.call(c, 22, local)
        self.call(c, 22, g)
        with self.assertRaises(ModelHalt): self.call(c, 21, g)
        with self.assertRaises(ModelHalt): self.method(c, p, 'normalize')
        self.assertEqual(self.call(c, 24, local, local), 1)
        self.assertEqual(len(c.forge_paths['objects']), 3)

    def test_string_modified_utf8_borrows_and_release(self):
        c = self.cpu(); p = self.path(c); s = self.method(c, p, 'toString')
        alias = self.method(c, p, 'toString'); self.assertEqual(self.call(c, 24, s, alias), 1)
        flag = c.reserve_fixture(1); c.write_private(flag, b'\0')
        ptr = self.call(c, 169, s, flag); ptr2 = self.call(c, 169, alias, 0)
        expected = b'/fixture/ysm-game/config'
        self.assertNotEqual(ptr, ptr2); self.assertEqual(c.read_known(flag, 1), b'\1')
        self.assertEqual(self.call(c, 168, s), len(expected)); self.assertEqual(c.read_known(ptr, len(expected)+1), expected+b'\0')
        self.call(c, 23, s); self.call(c, 170, alias, ptr)
        self.assertFalse(c.forge_paths['borrows'][str(ptr)]['active'])
        with self.assertRaises(ModelHalt): c.read_known(ptr, 1)
        self.assertEqual(c.read_known(ptr2, 1), b'/')
        with self.assertRaises(ModelHalt): self.call(c, 170, alias, ptr)
        with self.assertRaises(ModelHalt): self.call(c, 170, alias, ptr+1)
        self.call(c, 170, alias, ptr2)

    def test_wrong_receivers_methods_and_staticness_stop_without_mutation(self):
        c = self.cpu(); p = self.path(c); enum = self.enum(c)
        for slot, args in ((168, (p,)), (169, (enum, 0)), (21, (123,)), (24, (p, 123)), (95, (p, 0)), (31, (p,))):
            before = copy.deepcopy(c.forge_paths)
            with self.assertRaises(ModelHalt): self.call(c, slot, *args)
            self.assertEqual(before, c.forge_paths)
        with self.assertRaises(ModelHalt): self.method(c, p, 'toAbsolutePath')
        for change in (lambda x: x.update(static=True), lambda x: x.update(declaring_class=paths.FML_PATHS),
                       lambda x: x.update(descriptor='()I'), lambda x: x.update(class_sha256='0'*64)):
            c = self.cpu(); p = self.path(c)
            _, m = self.member(c, paths.PATH, 'normalize', '()L'+paths.PATH+';', 33)
            change(c.jni_state['methods'][str(m)])
            with self.assertRaises(ModelHalt): self.call(c, 35, p, m)

    def test_static_field_owner_deleted_class_wrong_field(self):
        for change in (lambda x: x.update(static=False), lambda x: x.update(name='GAMEDIR'),
                       lambda x: x.update(descriptor='Ljava/lang/Object;'), lambda x: x['source'].update(sha256='0'*64)):
            c = self.cpu(); cls, f = self.member(c, paths.FML_PATHS, 'CONFIGDIR', 'L'+paths.FML_PATHS+';', 144)
            change(c.jni_state['fields'][str(f)])
            with self.assertRaises(ModelHalt): self.call(c, 145, cls, f)
        c = self.cpu(); cls, f = self.member(c, paths.FML_PATHS, 'CONFIGDIR', 'L'+paths.FML_PATHS+';', 144)
        self.call(c, 23, cls)
        with self.assertRaises(ModelHalt): self.call(c, 145, cls, f)
        other = self.call(c, 6, self.string(c, paths.PATH))
        with self.assertRaises(ModelHalt): self.call(c, 145, other, f)
        enum = self.enum(c)
        with self.assertRaises(ModelHalt): self.call(c, 145, enum, f)

    def test_instance_field_and_class_receivers_reject(self):
        for change in (lambda x: x.update(static=True), lambda x: x.update(name='relativePath'),
                       lambda x: x.update(descriptor='Ljava/lang/String;'), lambda x: x.update(requested_class=paths.PATH)):
            c = self.cpu(); enum = self.enum(c)
            _, f = self.member(c, paths.FML_PATHS, 'absolutePath', 'L'+paths.PATH+';', 94)
            change(c.jni_state['fields'][str(f)])
            with self.assertRaises(ModelHalt): self.call(c, 95, enum, f)
        c = self.cpu(); cls, f = self.member(c, paths.FML_PATHS, 'absolutePath', 'L'+paths.PATH+';', 94)
        with self.assertRaises(ModelHalt): self.call(c, 95, cls, f)
        _, m = self.member(c, paths.PATH, 'normalize', '()L'+paths.PATH+';', 33)
        with self.assertRaises(ModelHalt): self.call(c, 35, cls, m)

    def test_metadata_integrity_and_budgets(self):
        c = self.cpu(configured=False)
        c.jni_state['java_sources']['java.base']['sha256'] = '0'*64
        with self.assertRaises(ValueError): c.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER)
        c = self.cpu(); p = self.path(c)
        with patch.object(paths, 'MAX_CALLS', 0):
            with self.assertRaises(ModelHalt): self.call(c, 21, p)
        with patch.object(paths, 'MAX_REFS', 0):
            with self.assertRaises(ModelHalt): self.call(c, 21, p)
        c = self.cpu(); p = self.path(c)
        c.forge_paths['objects']['config-path']['provider'] = 'host-unix'
        with self.assertRaises(ModelHalt): self.call(c, 21, p)

    def test_unsupported_path_provider_inputs(self):
        for path in ('relative', '', '/a/../b', '/a/./b', '/a//b', '//a', '/a/', '/é', '/a\0b', '/a\nb', '/'+('x'*2048)):
            with self.assertRaises(ValueError): paths.configuration('absolute-field-populated', path, paths.PROVIDER)
        for provider in ('unix', 'Windows', None):
            with self.assertRaises(ValueError): paths.configuration('absolute-field-populated', '/fixture/ysm-game', provider)
        with self.assertRaises(ValueError): paths.configuration('class-initialized-only', '/fixture/ysm-game', paths.PROVIDER)
        self.assertEqual(paths.configuration('absolute-field-populated', '/', paths.PROVIDER)['config_path'], '/config')
        c = self.cpu(configured=False); c.java_metadata = None
        with self.assertRaises(ValueError): c.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER)

    def test_pending_exception_deletion_and_release_only(self):
        c = self.cpu(); p = self.path(c); s = self.method(c, p, 'toString'); ptr = self.call(c, 169, s, 0)
        c.jni_state['pending_exception'] = {'class': 'java/lang/RuntimeException', 'message': 'own-byte'}
        with self.assertRaisesRegex(ModelHalt, 'PENDING_EXCEPTION'): self.call(c, 168, s)
        self.call(c, 170, s, ptr); self.call(c, 23, s)
        self.call(c, 17); self.assertIsNone(c.jni_state['pending_exception'])

    def test_receiver_free_calls_ignore_stale_live_and_deleted_registers(self):
        c = self.cpu(); live = self.path(c); deleted = self.call(c, 25, live)
        self.call(c, 23, deleted)
        # Deliberately supply stale values for all unused argument registers,
        # rather than depending on the test helper's zero-register defaults.
        for stale in (live, deleted):
            before = copy.deepcopy(c.forge_paths)
            self.assertEqual(self.call(c, 4, stale, stale, stale), VERSION)
            self.assertEqual(self.call(c, 228, stale, stale, stale), 0)
            self.call(c, 17, stale, stale, stale)
            c.jni_state['pending_exception'] = {'class': 'java/lang/RuntimeException', 'message': 'own-byte'}
            self.assertEqual(self.call(c, 228, stale, stale, stale), 1)
            with self.assertRaisesRegex(ModelHalt, 'PENDING_EXCEPTION'):
                self.call(c, 4, stale, stale, stale)
            self.call(c, 17, stale, stale, stale)
            self.assertIsNone(c.jni_state['pending_exception'])
            self.assertEqual(self.call(c, 228, stale, stale, stale), 0)
            self.assertEqual(c.forge_paths, before)
            # Actual unsupported receiver-taking operations still reject both.
            with self.assertRaisesRegex(ModelHalt, 'UNMODELED_PATH_JNI_CALL'):
                self.call(c, 31, stale, stale, stale)

    def test_released_borrow_copy_and_restored_lifetime(self):
        c = self.cpu(); p = self.path(c); s = self.method(c, p, 'toString')
        ptr = self.call(c, 169, s, 0); dest = c.reserve_fixture(1); c.write_private(dest, b'X')
        def copy_byte(cpu, source, count=1):
            cpu.stop = None; cpu.pc = RET; cpu.reg('RIP', RET)
            cpu.reg('RSI', source); cpu.reg('RDI', dest); cpu.reg('RCX', count); self.assertEqual(cpu.reg('DF'), 0)
            cpu.model('copy')
        copy_byte(c, ptr)
        self.assertEqual(c.read_known(dest, 1), b'/')
        self.call(c, 170, s, ptr)
        c.stop = {'reason': 'AUTHORED_TEST'}; state = capture(c)
        restored = self.fresh(); restore(restored, state); restored.configure_java_metadata(self.metadata)
        for cpu in (c, restored):
            before = (cpu.modeled_copies, cpu.opaque_copies, cpu.heap_writes, dict(cpu.opaque))
            with self.assertRaisesRegex(ModelHalt, 'RELEASED_UTF_BORROW_READ'):
                copy_byte(cpu, ptr)
            self.assertEqual(cpu.reg('RCX'), 1)
            self.assertEqual(cpu.read_known(dest, 1), b'/')
            self.assertEqual(before, (cpu.modeled_copies, cpu.opaque_copies, cpu.heap_writes, cpu.opaque))
            with self.assertRaisesRegex(ModelHalt, 'RELEASED_UTF_BORROW_READ'):
                cpu.read_known(ptr+len('/fixture/ysm-game/config'), 1)
            # C memcpy uses read_known rather than the opaque-copy seam.
            from native_memory_imports_ysm_265 import model as memory_model
            cpu.stop = None; cpu.reg('RDI', dest); cpu.reg('RSI', ptr); cpu.reg('RDX', 1)
            with self.assertRaisesRegex(ModelHalt, 'RELEASED_UTF_BORROW_READ'):
                memory_model(cpu, 'memcpy')
            copy_byte(cpu, ptr, count=0)  # No read occurs for an empty copy.
            self.assertEqual(cpu.reg('RCX'), 0)
            unknown = cpu.reserve_fixture(1)
            copy_byte(cpu, unknown)  # Ordinary unknown-source propagation remains supported.
            self.assertEqual(cpu.reg('RCX'), 0); self.assertEqual(cpu.opaque[dest], unknown)

    def test_checkpoint_pending_borrow_and_alias_roundtrip(self):
        c = self.cpu(); p = self.path(c); s = self.method(c, p, 'toString'); g = self.call(c, 21, s)
        ptr = self.call(c, 169, s, 0); self.call(c, 23, s)
        c.stop = {'reason': 'AUTHORED_TEST'}; state = capture(c)
        d = self.fresh(); restore(d, state); d.configure_java_metadata(self.metadata)
        self.assertEqual(d.forge_paths, c.forge_paths); self.assertEqual(d.attempted, 0)
        self.assertEqual(self.call(d, 168, g), len('/fixture/ysm-game/config'))
        self.call(d, 170, g, ptr); self.call(d, 22, g)
        d.stop = {'reason': 'AUTHORED_TEST'}; state2 = capture(d)
        e = self.fresh(); restore(e, state2); e.configure_java_metadata(self.metadata)
        self.assertEqual(e.forge_paths, d.forge_paths)
        for cls in (JniGuardedCPU, forge.ForgeRuntimeCPU):
            with self.assertRaisesRegex(ValueError, 'path-state backend'): restore(self.fresh(cls), state)

    def test_original_declaration_anchor_rejects_coordinated_tampering(self):
        from dataclasses import FrozenInstanceError
        c = self.cpu(); p = self.path(c)
        with self.assertRaises(FrozenInstanceError):
            c._path_declaration.config_json = '{}'
        c.stop = {'reason': 'AUTHORED_TEST'}; state = capture(c)
        changed = paths.configuration('absolute-field-populated', '/changed', paths.PROVIDER)
        c.forge_paths['config'] = copy.deepcopy(changed)
        c.forge_paths['objects'] = paths.objects(changed)
        with self.assertRaisesRegex(ValueError, 'original path declaration'):
            c.configure_forge_paths('absolute-field-populated', game_path='/changed', provider=paths.PROVIDER)
        with self.assertRaises(ModelHalt): self.call(c, 21, p)
        with self.assertRaises(ValueError): c.capture_sparse()
        # Replacing the serialized declaration too cannot overwrite a live anchor.
        c.forge_paths['declaration'] = paths.canonical(changed)
        with self.assertRaises(ValueError):
            c.configure_forge_paths('absolute-field-populated', game_path='/changed', provider=paths.PROVIDER)
        bad = copy.deepcopy(state)
        bad['sparse']['forge_paths']['config'] = copy.deepcopy(changed)
        bad['sparse']['forge_paths']['objects'] = paths.objects(changed)
        with self.assertRaisesRegex(ValueError, 'declaration/configuration'):
            restore(self.fresh(), bad)
        bad['sparse']['forge_paths']['declaration'] = paths.canonical(changed)
        # A coherently different snapshot must still reject against an existing
        # explicit declaration, even if its internal records are self-consistent.
        declared = self.cpu()
        with self.assertRaisesRegex(ValueError, 'original path declaration'):
            restore(declared, bad)
        restored = self.fresh(); restore(restored, state); restored.configure_java_metadata(self.metadata)
        restored.forge_paths['config'] = copy.deepcopy(changed)
        restored.forge_paths['objects'] = paths.objects(changed)
        with self.assertRaises(ValueError): restored.capture_sparse()
        restored.forge_paths = None
        with self.assertRaises(ValueError): restored.capture_sparse()
        with self.assertRaises(ValueError):
            restored.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER)

    def test_checkpoint_tampering_rejected(self):
        c = self.cpu(); p = self.path(c); s = self.method(c, p, 'toString'); ptr = self.call(c, 169, s, 0)
        c.stop = {'reason': 'AUTHORED_TEST'}; state = capture(c)
        changes = [lambda t: t['config'].update(provider='host-unix'),
                   lambda t: t['config'].update(game_path='/other'),
                   lambda t: t['config'].update(filesystem_operations_executed=0),
                   lambda t: t['config']['provenance'][paths.PATH].update(class_sha256='0'*64),
                   lambda t: t['objects']['config-path'].update(value='/wrong'),
                   lambda t: t['refs'][str(p)].update(active=False),
                   lambda t: t['refs'][str(p)].update(active=1),
                   lambda t: t['refs'][str(p)].update(identity='configdir-enum'),
                   lambda t: t['borrows'][str(ptr)].update(active=False),
                   lambda t: t['borrows'][str(ptr)].update(length=1),
                   lambda t: t['calls'][0].__setitem__(3, 123),
                   lambda t: t.update(legacy_extension=1),
                   lambda t: t['calls'].append([170, s, ptr+1, 0])]
        for change in changes:
            bad = copy.deepcopy(state); change(bad['sparse']['forge_paths'])
            with self.assertRaises(ValueError): restore(self.fresh(), bad)
        bad = copy.deepcopy(state); bad['fields']['private_readonly'] = []
        with self.assertRaises(ValueError): restore(self.fresh(), bad)

    def test_legacy_extension_explicit_and_default_stop_unchanged(self):
        c = self.cpu(configured=False); c.stop = {'reason': 'AUTHORED_TEST'}
        state = capture(c); state['sparse'].pop('forge_paths')
        d = self.fresh(); restore(d, state); d.configure_java_metadata(self.metadata)
        with self.assertRaises(ModelHalt): self.enum(d)
        with self.assertRaisesRegex(ValueError, 'explicit path extension'):
            d.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER)
        d.configure_forge_paths('class-initialized-only', provider=paths.PROVIDER, allow_legacy_extension=True)
        self.assertTrue(d.forge_paths['legacy_extension']); self.assertEqual(self.path(d), 0)
        with self.assertRaises(ValueError):
            d.configure_forge_paths('absolute-field-populated', game_path='/fixture/ysm-game', provider=paths.PROVIDER, allow_legacy_extension=True)


if __name__ == '__main__': unittest.main()
