"""Synthetic class files only: no compiler, JVM, or binary fixtures required."""
import hashlib
import io
import struct
import unittest
import zipfile
from unittest.mock import patch

import native_java_metadata_ysm_265 as metadata


def class_bytes(name, superclass=None, methods=(), fields=(), interfaces=()):
    pool = []
    def utf(text):
        raw = text.encode()
        pool.append(b'\x01' + struct.pack('>H', len(raw)) + raw)
        return len(pool)
    def cls(text):
        idx = utf(text)
        pool.append(b'\x07' + struct.pack('>H', idx))
        return len(pool)
    owner = cls(name)
    parent = cls(superclass) if superclass else 0
    interface_indices = [cls(name) for name in interfaces]
    def members(items):
        result = struct.pack('>H', len(items))
        for access, member, descriptor in items:
            result += struct.pack('>HHHH', access, utf(member), utf(descriptor), 0)
        return result
    field_data = members(fields)
    method_data = members(methods)
    return (struct.pack('>IHHH', 0xcafebabe, 0, 65, len(pool) + 1)
            + b''.join(pool) + struct.pack('>HHHH', 1, owner, parent, len(interface_indices))
            + b''.join(struct.pack('>H', idx) for idx in interface_indices)
            + field_data + method_data + b'\x00\x00')


def archive(entries, jmod=False):
    out = io.BytesIO()
    if jmod:
        out.write(b'JM\x01\x00')
    with zipfile.ZipFile(out, 'w') as z:
        for name, raw in entries.items():
            z.writestr(zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), raw)
    return out.getvalue()


def fixture(entries):
    raw = archive(entries)
    return metadata.JavaMetadata.from_buffers(jar=raw, expected_jar_sha256=hashlib.sha256(raw).hexdigest())


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.root = class_bytes('example/Root', methods=[(1, '<init>', '()V'),
            (1, 'run', '(I)Z'), (9, 'create', '()I'), (2, 'secret', '()V')],
            fields=[(1, 'count', 'I')])
        self.child = class_bytes('example/Child', 'example/Root')
        self.data = fixture({'example/Root.class': self.root, 'example/Child.class': self.child})

    def test_metadata_and_provenance(self):
        info = self.data.class_info('example/Root')
        self.assertEqual(info['fields'][0]['descriptor'], 'I')
        self.assertEqual(info['class_sha256'], hashlib.sha256(self.root).hexdigest())
        self.assertEqual(info['source']['archive_kind'], 'jar')
        info['methods'].clear()
        self.assertEqual(len(self.data.class_info('example/Root')['methods']), 4)

    def test_lookup_exact_inherited_static_and_constructor(self):
        result = self.data.lookup_method('example/Child', 'run', '(I)Z', False)
        self.assertEqual(result['declaring_class'], 'example/Root')
        self.assertIsNone(self.data.lookup_method('example/Child', 'run', '(J)Z'))
        self.assertIsNone(self.data.lookup_method('example/Child', 'run', '(I)Z', True))
        self.assertIsNotNone(self.data.lookup_method('example/Child', 'create', '()I', True))
        self.assertIsNone(self.data.lookup_method('example/Child', 'create', '()I'))
        self.assertIsNone(self.data.lookup_method('example/Child', '<init>', '()V'))
        self.assertIsNotNone(self.data.lookup_method('example/Root', '<init>', '()V'))
        self.assertIsNone(self.data.lookup_method('example/Child', 'secret', '()V'))

    def test_missing_is_never_fabricated(self):
        self.assertIsNone(self.data.class_info('missing/Thing'))
        self.assertIsNone(self.data.lookup_method('missing/Thing', 'run', '()V'))
        self.assertIsNone(metadata.JavaMetadata().class_info('java/io/File'))

    def test_java_base_jmod_and_shadow_prevention(self):
        raw = archive({'classes/java/io/File.class': class_bytes('java/io/File', methods=[(1, 'exists', '()Z')])}, True)
        data = metadata.JavaMetadata.from_buffers(java_base=raw)
        self.assertEqual(data.lookup_method('java/io/File', 'exists', '()Z')['source']['id'], 'java.base')
        spoof = fixture({'java/io/File.class': class_bytes('java/io/File')})
        self.assertIsNone(spoof.class_info('java/io/File'))
        with self.assertRaises(metadata.MetadataError):
            metadata.JavaMetadata.from_buffers(java_base=archive({}))

    def test_pinned_ysm_digest(self):
        with self.assertRaisesRegex(metadata.MetadataError, 'SHA-256'):
            metadata.JavaMetadata.from_buffers(jar=archive({}))

    def test_path_constructor_cannot_override_pin(self):
        with patch.object(metadata.Path, 'open', return_value=io.BytesIO(archive({}))):
            with self.assertRaisesRegex(metadata.MetadataError, 'SHA-256'):
                metadata.JavaMetadata(jar_path='synthetic.jar')

    def test_duplicate_archive_entries_rejected(self):
        import warnings
        out = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(out, 'w') as z:
                z.writestr('same', b'a')
                z.writestr('same', b'b')
        raw = out.getvalue()
        with self.assertRaisesRegex(metadata.MetadataError, 'duplicate'):
            metadata.JavaMetadata.from_buffers(jar=raw, expected_jar_sha256=hashlib.sha256(raw).hexdigest())

    def test_invalid_names_and_descriptors(self):
        for name in ('../File', '/File', 'a//b', 'a\\b', 'a.b', '[I', 'a/../b'):
            with self.subTest(name=name), self.assertRaises(metadata.MetadataError):
                self.data.class_info(name)
        for desc in ('I', '(', '()Q', '(V)V', '()Vextra', '(L;)V', '([' + '[' * 255 + 'I)V'):
            with self.subTest(desc=desc), self.assertRaises(metadata.MetadataError):
                self.data.lookup_method('example/Root', 'run', desc)

    def test_archive_and_class_budgets(self):
        with patch.object(metadata, 'MAX_ARCHIVE_ENTRIES', 1), self.assertRaises(metadata.MetadataError):
            fixture({'a': b'', 'b': b''})
        with patch.object(metadata, 'MAX_ARCHIVE_BYTES', 10), self.assertRaises(metadata.MetadataError):
            fixture({'a': b''})
        with patch.object(metadata, 'MAX_CLASS_BYTES', 5), self.assertRaises(metadata.MetadataError):
            self.data.class_info('example/Root')
        with self.assertRaises(metadata.MetadataError):
            fixture({'../bad': b''})

    def test_corrupt_and_wrong_identity_classes(self):
        for raw in (b'bad', class_bytes('different/Name'), self.root + b'extra',
                    self.root[:-2] + b'\x00\x01\x00\x01\xff\xff\xff\xff'):
            data = fixture({'example/Root.class': raw})
            with self.assertRaises(metadata.MetadataError):
                data.class_info('example/Root')

    def test_super_depth_cycle_and_missing(self):
        data = fixture({'a.class': class_bytes('a', 'b'), 'b.class': class_bytes('b', 'a')})
        with self.assertRaisesRegex(metadata.MetadataError, 'cyclic'):
            data.lookup_method('a', 'missing', '()V')
        with patch.object(metadata, 'MAX_SUPER_DEPTH', 1), self.assertRaisesRegex(metadata.MetadataError, 'depth'):
            self.data.lookup_method('example/Child', 'run', '(I)Z')
        data = fixture({'a.class': class_bytes('a', 'b')})
        self.assertIsNone(data.lookup_method('a', 'missing', '()V'))


class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.raw = archive({'example/Root.class': class_bytes('example/Root',
            methods=[(9, 'create', '()I')])})
        self.pin = hashlib.sha256(self.raw).hexdigest()

    def data(self, **kwargs):
        return metadata.JavaMetadata.from_buffers(
            dependency_buffers={'commons-lang3': (self.raw, self.pin)}, **kwargs)

    def test_lookup_and_member_provenance(self):
        data = self.data()
        self.assertEqual(data.class_info('example/Root')['source']['id'], 'commons-lang3')
        member = data.lookup_method('example/Root', 'create', '()I', True)
        self.assertEqual(member['source']['sha256'], self.pin)
        self.assertEqual(member['source']['archive_kind'], 'jar')
        self.assertIsNone(data.lookup_method('example/Root', 'create', '()I'))
        self.assertIsNone(data.class_info('missing/Class'))

    def test_inherited_member_crosses_source_boundary(self):
        jar = archive({'example/Child.class': class_bytes('example/Child', 'example/Root')})
        data = self.data(jar=jar, expected_jar_sha256=hashlib.sha256(jar).hexdigest())
        self.assertEqual(data.lookup_method('example/Child', 'create', '()I', True)
                         ['source']['id'], 'commons-lang3')

    def test_dependency_hash_required_and_verified(self):
        for pin in (None, '', '0' * 64, self.pin.upper(), '../bad'):
            with self.subTest(pin=pin), self.assertRaises(metadata.MetadataError):
                metadata.JavaMetadata.from_buffers(dependency_buffers={'dep': (self.raw, pin)})

    def test_source_ids_and_shapes_fail_closed(self):
        for key in ('ysm', 'java.base', '', '../dep', '/dep', 'dep/name', 'a' * 65, 1):
            with self.subTest(key=key), self.assertRaises(metadata.MetadataError):
                metadata.JavaMetadata.from_buffers(dependency_buffers={key: (self.raw, self.pin)})
        for value in (self.raw, (self.raw,), (self.raw, self.pin, 1), None):
            with self.subTest(value=value), self.assertRaises(metadata.MetadataError):
                metadata.JavaMetadata.from_buffers(dependency_buffers={'dep': value})
        with self.assertRaises(metadata.MetadataError):
            metadata.JavaMetadata.from_buffers(dependency_buffers=[])

    def test_duplicate_classes_fail_without_order_guess(self):
        with self.assertRaisesRegex(metadata.MetadataError, 'ambiguous'):
            self.data(jar=self.raw, expected_jar_sha256=self.pin)
        with self.assertRaisesRegex(metadata.MetadataError, 'ambiguous'):
            metadata.JavaMetadata.from_buffers(dependency_buffers={
                'dep1': (self.raw, self.pin), 'dep2': (self.raw, self.pin)})

    def test_platform_shadowing_rejected(self):
        raw = archive({'java/io/File.class': class_bytes('java/io/File')})
        with self.assertRaisesRegex(metadata.MetadataError, 'platform'):
            metadata.JavaMetadata.from_buffers(dependency_buffers={'dep':
                (raw, hashlib.sha256(raw).hexdigest())})
        base = archive({'classes/example/Root.class': class_bytes('example/Root')}, True)
        with self.assertRaisesRegex(metadata.MetadataError, 'platform'):
            self.data(java_base=base)

    def test_dependency_budgets(self):
        empty = archive({})
        pair = (empty, hashlib.sha256(empty).hexdigest())
        with self.assertRaisesRegex(metadata.MetadataError, 'count'):
            metadata.JavaMetadata.from_buffers(dependency_buffers={str(i): pair for i in range(9)})
        with patch.object(metadata, 'MAX_DEPENDENCY_BYTES', len(empty) * 2 - 1):
            with self.assertRaisesRegex(metadata.MetadataError, 'byte budget'):
                metadata.JavaMetadata.from_buffers(dependency_buffers={'one': pair, 'two': pair})
        with patch.object(metadata, 'MAX_ARCHIVE_ENTRIES', 0):
            with self.assertRaisesRegex(metadata.MetadataError, 'entry budget'):
                self.data()

    def test_paths_read_only_and_validated_before_open(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'dep.jar'
            path.write_bytes(self.raw)
            data = metadata.JavaMetadata(dependency_paths={'dep': (path, self.pin)})
            self.assertEqual(data.class_info('example/Root')['source']['sha256'], self.pin)
            self.assertEqual(path.read_bytes(), self.raw)
            self.assertEqual(list(Path(tmp).iterdir()), [path])
        with patch.object(metadata.Path, 'open', side_effect=AssertionError('unexpected read')):
            with self.assertRaises(metadata.MetadataError):
                metadata.JavaMetadata(dependency_paths={'../bad': ('bad.jar', self.pin)})


class FieldTests(unittest.TestCase):
    def setUp(self):
        self.root = class_bytes('example/Root', fields=[
            (2, 'bits', 'J'), (9, 'count', 'I'), (1, 'value', 'Ljava/lang/Object;'),
            (1, 'array', '[[I'), (1, 'objects', '[Ljava/lang/String;')])
        self.data = fixture({'example/Root.class': self.root,
                             'example/Child.class': class_bytes('example/Child', 'example/Root')})

    def test_exact_fields_and_provenance(self):
        for name, descriptor, static in [('bits', 'J', False), ('count', 'I', True),
                ('value', 'Ljava/lang/Object;', False), ('array', '[[I', False),
                ('objects', '[Ljava/lang/String;', False)]:
            with self.subTest(name=name):
                result = self.data.lookup_field('example/Root', name, descriptor, static)
                self.assertEqual(result['declaring_class'], 'example/Root')
                self.assertEqual(result['descriptor'], descriptor)
                self.assertEqual(result['class_sha256'], hashlib.sha256(self.root).hexdigest())
                self.assertEqual(result['source']['id'], 'ysm')
        self.assertEqual(self.data.lookup_field('example/Root', 'bits', 'J')['access'], 2)

    def test_inherited_private_and_missing_fields(self):
        self.assertEqual(self.data.lookup_field('example/Child', 'bits', 'J')['declaring_class'], 'example/Root')
        self.assertIsNone(self.data.lookup_field('example/Root', 'bits', 'I'))
        self.assertIsNone(self.data.lookup_field('example/Root', 'bits', 'J', True))
        self.assertIsNone(self.data.lookup_field('example/Root', 'count', 'I'))
        self.assertIsNone(self.data.lookup_field('example/Root', 'missing', 'J'))
        self.assertIsNone(self.data.lookup_field('missing/Class', 'bits', 'J'))

    def test_invalid_field_inputs(self):
        for descriptor in ('', 'V', '[V', '()I', 'II', 'Iextra', 'L;',
                           'Ljava.lang.Object;', 'L../bad;', '[', '[' * 256 + 'I'):
            with self.subTest(descriptor=descriptor), self.assertRaises(metadata.MetadataError):
                self.data.lookup_field('example/Root', 'bits', descriptor)
        for name in ('', '<init>', 'a/b', 'a.b', 'a;', '[a', 'a\\b', 'a\x00b'):
            with self.subTest(name=name), self.assertRaises(metadata.MetadataError):
                self.data.lookup_field('example/Root', name, 'I')
        with self.assertRaises(metadata.MetadataError):
            self.data.lookup_field('example/Root', 'bits', 'J', 1)
        self.assertIsNone(self.data.lookup_field('example/Root', 'none', '[' * 255 + 'I'))

    def test_cycle_depth_and_unresolved_interfaces_fail_closed(self):
        data = fixture({'a.class': class_bytes('a', 'b'), 'b.class': class_bytes('b', 'a')})
        with self.assertRaisesRegex(metadata.MetadataError, 'cyclic'):
            data.lookup_field('a', 'missing', 'I')
        with patch.object(metadata, 'MAX_SUPER_DEPTH', 1), self.assertRaisesRegex(metadata.MetadataError, 'depth'):
            self.data.lookup_field('example/Child', 'bits', 'J')
        data = fixture({'example/Root.class': self.root,
            'example/Child.class': class_bytes('example/Child', 'example/Root',
                                                interfaces=['unresolved/Interface'])})
        self.assertIsNone(data.lookup_field('example/Child', 'bits', 'J'))


if __name__ == '__main__':
    unittest.main()
