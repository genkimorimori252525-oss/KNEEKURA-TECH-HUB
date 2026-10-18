"""Own-byte classfiles with test-only pin substitution; no JVM or target execution."""
import copy
import hashlib
import io
import struct
import unittest
from unittest.mock import patch
import native_forge_runtime_fixture_ysm_265 as forge
from native_java_metadata_ysm_265 import JavaMetadata
from native_jni_fixture_ysm_265 import JniGuardedCPU, TRAPS
from native_guarded_checkpoint_ysm_265 import capture, restore
from native_unicorn_guarded_ysm_265 import ModelHalt, SP
from test_native_java_metadata_ysm_265 import archive, class_bytes
RET = 0x100000

class ForgeRuntimeTests(unittest.TestCase):
    def setUp(self):
        classes = {forge.ENV: class_bytes(forge.ENV, fields=[(9, 'production', 'Z'), (9, 'dist', forge.DESC)]),
                   forge.DIST: class_bytes(forge.DIST, fields=[(16409, 'CLIENT', forge.DESC), (16409, 'DEDICATED_SERVER', forge.DESC)])}
        for name in forge.PINS:
            if name not in classes: classes[name] = class_bytes(name)
        data = archive({k+'.class': v for k, v in classes.items()})
        digest = hashlib.sha256(data).hexdigest()
        self.pins = patch.dict(forge.PINS, {k: (digest, hashlib.sha256(v).hexdigest()) for k, v in classes.items()}, clear=True)
        self.pins.start(); self.addCleanup(self.pins.stop)
        self.metadata = JavaMetadata.from_buffers(dependency_buffers={'forge-own-byte': (data, digest)})
    def cpu(self, profile='forgeclient', configured=True):
        c = forge.ForgeRuntimeCPU(io.StringIO(), 'heap', limit=1)
        c.add_image(RET, b'\x90'*16); c.protect_image(); c.configure_jni(); c.configure_java_metadata(self.metadata)
        if configured: c.configure_forge_runtime(profile, initialized=True, production_property_present=False)
        return c
    def fresh(self, cls=forge.ForgeRuntimeCPU):
        c = cls(io.StringIO(), 'heap', limit=1); c.add_image(RET, b'\x90'*16); c.protect_image(); return c
    def string(self, c, value):
        a = c.reserve_fixture(len(value)+1); c.write_private(a, value.encode()+b'\0'); return a
    def call(self, c, slot, *args):
        c.stop = None; c.pc = TRAPS+(8+slot)*16; c.reg('RSP', SP); c.write_private(SP, struct.pack('<Q', RET)); c.reg('RDI', c.jni_state['env'])
        for r, v in zip(('RSI', 'RDX', 'RCX'), args): c.reg(r, v)
        c.model('jni-import'); return c.reg('RAX')
    def field(self, c, owner, name, desc):
        cls = self.call(c, 6, self.string(c, owner))
        field = self.call(c, 144, cls, self.string(c, name), self.string(c, desc))
        return cls, field
    def enum(self, c, owner=forge.ENV, name='dist'):
        return self.call(c, 145, *self.field(c, owner, name, forge.DESC))
    def test_profiles_fresh_typed_refs_identity_and_metadata_unchanged(self):
        for profile, expected in forge.PROFILES.items():
            c = self.cpu(profile); cls, field = self.field(c, forge.ENV, 'production', 'Z')
            before = copy.deepcopy(c.jni_state); self.assertEqual(self.call(c, 146, cls, field), 1)
            self.assertEqual(before, c.jni_state)
            a, b = self.enum(c), self.enum(c, forge.DIST, expected)
            self.assertNotEqual(a, b); self.assertEqual(self.call(c, 24, a, b), 1)
            other = self.enum(c, forge.DIST, 'CLIENT' if expected != 'CLIENT' else 'DEDICATED_SERVER')
            self.assertEqual(self.call(c, 24, a, other), 0)
            self.assertEqual(self.call(c, 24, 0, 0), 1); self.assertEqual(self.call(c, 24, a, 0), 0)
            self.assertNotIn(str(a), c.jni_state['classes'])
    def test_enum_deletion_pending_exception_and_no_aliases(self):
        c = self.cpu(); a = self.enum(c); b = self.enum(c)
        c.jni_state['pending_exception'] = {'class': 'java/lang/RuntimeException', 'message': 'test'}
        self.call(c, 23, a); self.assertFalse(c.forge_runtime['refs'][str(a)]['active'])
        with self.assertRaisesRegex(ModelHalt, 'DELETED'): self.call(c, 23, a)
        with self.assertRaisesRegex(ModelHalt, 'PENDING_EXCEPTION'): self.call(c, 24, b, b)
        self.call(c, 17)
        for slot, args in ((24, (a, b)), (24, (123, b)), (21, (b,)), (33, (b, 0, 0))):
            with self.assertRaises(ModelHalt): self.call(c, slot, *args)
        self.assertEqual(self.call(c, 24, b, b), 1)
    def test_field_proofs_and_alive_owner_required(self):
        changes = [lambda f: f.update(static=False), lambda f: f.update(descriptor='I'),
                   lambda f: f.update(name='missing'), lambda f: f.update(declaring_class=forge.DIST),
                   lambda f: f.update(class_sha256='0'*64), lambda f: f['source'].update(sha256='0'*64)]
        for change in changes:
            c = self.cpu(); cls, field = self.field(c, forge.ENV, 'production', 'Z'); change(c.jni_state['fields'][str(field)])
            before = copy.deepcopy(c.forge_runtime)
            with self.assertRaises(ModelHalt): self.call(c, 146, cls, field)
            self.assertEqual(before, c.forge_runtime)
        c = self.cpu(); cls, field = self.field(c, forge.ENV, 'production', 'Z'); self.call(c, 23, cls)
        with self.assertRaises(ModelHalt): self.call(c, 146, cls, field)
        c = self.cpu(); cls, field = self.field(c, forge.ENV, 'production', 'Z')
        other = self.call(c, 6, self.string(c, forge.DIST))
        with self.assertRaises(ModelHalt): self.call(c, 146, other, field)
        c.jni_state['pending_exception'] = {'class': 'java/lang/RuntimeException', 'message': 'test'}
        with self.assertRaisesRegex(ModelHalt, 'PENDING_EXCEPTION'): self.call(c, 146, cls, field)
    def test_configuration_pins_unknown_reads_and_budgets(self):
        c = self.cpu(configured=False); cls, field = self.field(c, forge.ENV, 'production', 'Z')
        with self.assertRaisesRegex(ModelHalt, 'SCENARIO_REQUIRED'): self.call(c, 146, cls, field)
        for profile, initialized, prop in (('userdev', True, False), ('forgeclient', False, False), ('forgeclient', True, 1)):
            with self.assertRaises(ValueError): c.configure_forge_runtime(profile, initialized=initialized, production_property_present=prop)
        c.configure_forge_runtime('forgeclient', initialized=True, production_property_present=True)
        self.assertEqual(self.call(c, 146, cls, field), 1)
        with self.assertRaises(ValueError): c.configure_forge_runtime('forgeserver', initialized=True, production_property_present=True)
        with self.assertRaises(ModelHalt): self.call(c, 145, cls, field)
        with patch.object(forge, 'MAX_CALLS', 0):
            with self.assertRaises(ModelHalt): self.call(c, 146, cls, field)
        with patch.object(forge, 'MAX_REFS', 0):
            cls, field = self.field(c, forge.ENV, 'dist', forge.DESC)
            with self.assertRaises(ModelHalt): self.call(c, 145, cls, field)
        c = self.cpu(configured=False); c.java_metadata = None
        with self.assertRaises(ValueError): c.configure_forge_runtime('forgeclient', initialized=True, production_property_present=False)
    def test_checkpoint_replay_provenance_and_backend(self):
        c = self.cpu(); a = self.enum(c); b = self.enum(c); self.call(c, 24, a, b); self.call(c, 23, a)
        c.stop = {'reason': 'TEST'}; state = capture(c)
        d = self.fresh(); restore(d, state); d.configure_java_metadata(self.metadata)
        self.assertEqual(d.forge_runtime, c.forge_runtime); self.assertEqual(d.jni_state, c.jni_state)
        self.assertEqual(self.call(d, 24, b, b), 1)
        with self.assertRaises(ValueError):
            d.configure_forge_runtime('forgeserver', initialized=True, production_property_present=False)
        with self.assertRaisesRegex(ValueError, 'Forge runtime-state backend'): restore(self.fresh(JniGuardedCPU), state)
        changes = [lambda t: t['config'].update(production=False),
                   lambda t: t['config'].update(production=1),
                   lambda t: t['refs'].update({str(b): []}),
                   lambda t: t['refs'][str(b)].update(active=1), lambda t: t['config'].update(profile='forgeserver'),
                   lambda t: t['config']['provenance'][forge.ENV].update(artifact_sha256='0'*64),
                   lambda t: t['refs'][str(b)].update(type='java/lang/Object'),
                   lambda t: t['refs'][str(a)].update(active=True), lambda t: t['calls'][0].update(result=b),
                   lambda t: t['calls'][2].update(result=0), lambda t: t['calls'].append(copy.deepcopy(t['calls'][-1]))]
        for change in changes:
            bad = copy.deepcopy(state); change(bad['sparse']['forge_runtime'])
            with self.assertRaises(ValueError): restore(self.fresh(), bad)
if __name__ == '__main__': unittest.main()
