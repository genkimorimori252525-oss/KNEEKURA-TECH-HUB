"""Synthetic ELF metadata tests; no ELF instructions are executed."""
import struct
import unittest
from types import SimpleNamespace
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_PROT_READ
from native_jvm_artifact_view_ysm_265 import BASE, JvmArtifactView


def elf(dynamic=(), local=()):
    b = bytearray(0x2000)
    b[:16] = b'\x7fELF\x02\x01\x01' + bytes(9)
    struct.pack_into('<HHIQQQIHHHHHH', b, 16, 3, 62, 1, 0, 64, 0x1000, 0, 64, 56, 2, 64, 6, 0)
    struct.pack_into('<IIQQQQQQ', b, 64, 1, 5, 0, 0, 0, 0x1800, 0x1800, 0x1000)
    struct.pack_into('<IIQQQQQQ', b, 120, 1, 6, 0x1800, 0x3000, 0, 0x800, 0x1000, 0x1000)
    names = bytearray(b'\0')
    for index, rows, off, kind in ((3, dynamic, 0x400, 11), (4, local, 0x800, 2)):
        for i, (name, info, other, section, value, size) in enumerate(rows):
            n = len(names); names.extend(name.encode() + b'\0')
            struct.pack_into('<IBBHQQ', b, off + i * 24, n, info, other, section, value, size)
        struct.pack_into('<IIQQQQIIQQ', b, 0x1000 + index * 64, 0, kind, 0, 0, off, len(rows)*24, 5, 0, 8, 24)
    struct.pack_into('<IIQQQQIIQQ', b, 0x1040, 0, 1, 6, 0x200, 0x200, 0x100, 0, 0, 16, 0)
    struct.pack_into('<IIQQQQIIQQ', b, 0x1080, 0, 1, 3, 0x3000, 0x1800, 0x800, 0, 0, 8, 0)
    struct.pack_into('<IIQQQQIIQQ', b, 0x1140, 0, 3, 2, 0xc00, 0xc00, len(names), 0, 0, 1, 0)
    b[0xc00:0xc00+len(names)] = names
    return bytes(b)


def view(data):
    cpu = SimpleNamespace(uc=Uc(UC_ARCH_X86, UC_MODE_64))
    return JvmArtifactView(cpu, data), cpu


class ArtifactTests(unittest.TestCase):
    def test_mapping_preserves_unknown_writable_and_zero_fill(self):
        v, c = view(elf())
        self.assertIsNone(v.unknown(BASE+0x200, 8))
        self.assertEqual(v.unknown(BASE+0x3000, 8), BASE+0x3000)
        self.assertEqual(v.unknown(BASE+0x3800, 8), BASE+0x3800)
        self.assertTrue(v.unchanged(c))
        self.assertTrue(all(p == UC_PROT_READ for _, _, p in c.uc.mem_regions()))

    def test_overlapping_load_segments_rejected_before_mapping(self):
        for flags in (4,6):
            b=bytearray(elf());struct.pack_into('<IIQQQQQQ',b,120,1,flags,0x1000,0x1000,0,0x800,0x800,0x1000)
            cpu=SimpleNamespace(uc=Uc(UC_ARCH_X86,UC_MODE_64))
            with self.assertRaisesRegex(ValueError,'Overlapping'):JvmArtifactView(cpu,bytes(b))
            self.assertEqual(list(cpu.uc.mem_regions()),[])

    def test_local_function_is_not_exported(self):
        v, _ = view(elf(local=[('jni_GetEnv', 2, 0, 1, 0x200, 16)]))
        self.assertTrue(hasattr(v, 'local_function'), 'static symbol lookup is missing')
        self.assertEqual(v.local_function('jni_GetEnv'), dict(address=BASE+0x200, kind=2, size=16))
        with self.assertRaises(ValueError): v.symbol('jni_GetEnv')
        self.assertIsNone(v.dynamic_symbol_containing(BASE+0x200))

    def test_dynamic_containing_is_bounded_and_returns_name(self):
        v, _ = view(elf(dynamic=[('exported', 0x12, 0, 1, 0x200, 16)]))
        self.assertTrue(hasattr(v, 'dynamic_symbol_containing'), 'address lookup is missing')
        self.assertEqual(v.symbol('exported'), dict(address=BASE+0x200, kind=2, size=16))
        self.assertEqual(v.dynamic_symbol_containing(BASE+0x20f), dict(name='exported', name_address=BASE+0xc01, address=BASE+0x200, kind=2, size=16))
        self.assertIsNone(v.dynamic_symbol_containing(BASE+0x210))

    def test_visibility_binding_undefined_and_kind_filtered(self):
        rows = [('hidden',0x12,2,1,0x200,1), ('undefined',0x12,0,0,0,0), ('local',2,0,1,0x200,1), ('tls',0x16,0,2,0x3000,1)]
        v, _ = view(elf(dynamic=rows,local=[('global',0x12,0,1,0x200,1),('object',1,0,1,0x200,1)]))
        for name in ('hidden','undefined','local','tls'):
            with self.assertRaises(ValueError): v.symbol(name)
        for name in ('global','object'):
            with self.assertRaises(ValueError): v.local_function(name)

    def test_full_symbol_extent_must_fit(self):
        v, _ = view(elf(dynamic=[('bad',0x12,0,1,0x2ff,32)]))
        with self.assertRaises(ValueError): v.symbol('bad')

    def test_duplicate_identical_and_conflicting_records(self):
        row=('same',0x12,0,1,0x200,16)
        v, _=view(elf(dynamic=[row,row]))
        self.assertEqual(v.symbol('same')['address'],BASE+0x200)
        v, _=view(elf(dynamic=[row,('same',0x12,0,1,0x220,16)]))
        with self.assertRaises(ValueError):v.symbol('same')
        self.assertIsNone(v.dynamic_symbol_containing(BASE+0x200))

    def test_malformed_string_and_symbol_table_bounds(self):
        for offset, fmt, value in ((0x400,'I',0xffff),(0x10c0+40,'I',99),(0x10c0+56,'Q',23),(0x10c0+32,'Q',0x10000000)):
            b=bytearray(elf(dynamic=[('a',0x12,0,1,0x200,1)]));struct.pack_into('<'+fmt,b,offset,value)
            v,_=view(bytes(b))
            with self.assertRaises(ValueError):v.symbol('a')

    def test_cached_parse_and_result_not_mutable(self):
        v,_=view(elf(local=[('jni_GetEnv',2,0,1,0x200,1)]))
        self.assertTrue(hasattr(v,'local_function'), 'static symbol lookup is missing')
        result=v.local_function('jni_GetEnv');result['address']=0
        self.assertEqual(v.local_function('jni_GetEnv')['address'],BASE+0x200)
        self.assertIsNotNone(v._symbol_cache)

    def test_weak_protected_object_and_zero_size_export(self):
        v,_=view(elf(dynamic=[('object',0x21,3,2,0x3000,8),('zero',0x12,0,1,0x200,0)]))
        self.assertEqual(v.symbol('object'),dict(address=BASE+0x3000,kind=1,size=8))
        self.assertEqual(v.dynamic_symbol_containing(BASE+0x200)['name'],'zero')
        self.assertIsNone(v.dynamic_symbol_containing(BASE+0x201))

    def test_overlapping_export_aliases_are_ambiguous(self):
        v,_=view(elf(dynamic=[('a',0x12,0,1,0x200,16),('b',0x12,0,1,0x208,16)]))
        self.assertIsNone(v.dynamic_symbol_containing(BASE+0x209))
        self.assertEqual(v.dynamic_symbol_containing(BASE+0x201)['name'],'a')

    def test_local_conflicts_and_invalid_extent_fail_closed(self):
        for rows in ([('a',2,0,1,0x200,1),('a',2,0,1,0x220,1)], [('a',2,0,1,0x2ff,2)]):
            v,_=view(elf(local=rows))
            with self.assertRaises(ValueError):v.local_function('a')

    def test_unmapped_or_wrong_file_mapping_names_have_no_guest_address(self):
        for field,value in ((8,0),(16,0x3000),(16,0xc10)):
            b=bytearray(elf(dynamic=[('a',0x12,0,1,0x200,1)]))
            struct.pack_into('<Q',b,0x1140+field,value)
            v,_=view(bytes(b))
            self.assertNotIn('name_address',v.dynamic_symbol_containing(BASE+0x200))

    def test_cached_parse_identity(self):
        v,_=view(elf(local=[('a',2,0,1,0x200,1)]))
        v.local_function('a');cache=v._symbol_cache
        v.local_function('a')
        self.assertIs(cache,v._symbol_cache)

if __name__ == '__main__': unittest.main()
