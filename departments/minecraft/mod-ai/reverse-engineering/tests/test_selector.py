"""Opt-in router contract; fixtures only, never claims about real obfuscators."""
import contextlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def selector():
    spec = importlib.util.spec_from_file_location('kneekura_local_selector', ROOT / 'selector.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.m = selector()
        self.temp = tempfile.TemporaryDirectory(prefix='optional route spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def jar(self, name='fixture.jar', classes=('a/Obf.class', 'b/Thing.class')):
        path = self.root / name
        with zipfile.ZipFile(path, 'w') as z:
            for cls in classes:
                z.writestr(cls, b'\xca\xfe\xba\xbe\x00\x00\x00\x3d')
            z.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
        return path

    def classfile(self, name='Obf.class', major=61):
        path = self.root / name
        path.write_bytes(b'\xca\xfe\xba\xbe\x00\x00' + major.to_bytes(2, 'big'))
        return path

    def apk(self):
        path = self.root / 'app.apk'
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('AndroidManifest.xml', b'fake-manifest')
            z.writestr('classes.dex', b'dex\n035\x00')
        return path

    def exe(self):
        path = self.root / 'program.exe'
        data = bytearray(68)
        data[:2] = b'MZ'
        data[60:64] = (64).to_bytes(4, 'little')
        data[64:68] = b'PE\x00\x00'
        path.write_bytes(data)
        return path

    def test_import_does_not_probe_or_touch_runtime(self):
        with mock.patch('subprocess.run', side_effect=AssertionError('started')), \
             mock.patch('zipfile.ZipFile', side_effect=AssertionError('file read')):
            selector()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_static_capabilities_no_files_or_probes(self):
        out = io.StringIO()
        with mock.patch('subprocess.run', side_effect=AssertionError('started')), \
             mock.patch('zipfile.ZipFile', side_effect=AssertionError('file read')), \
             contextlib.redirect_stdout(out):
            self.assertEqual(self.m.main(['capabilities']), 0)
        self.assertIn('ClassGraph v5', out.getvalue())
        self.assertIn('ADVISORY_NOT_WIRED', out.getvalue())
        self.assertIn('RISK_REQUIRES_ISOLATION', out.getvalue())

    def test_declared_jar_first_pass_is_structure_only(self):
        r = self.m.choose('jar')
        self.assertEqual(r['decision'], 'READY_FOR_EXPLICIT_INVOCATION')
        self.assertEqual(r['selected']['tool'], 'archive-index')
        self.assertEqual(r['evidence']['basis'], 'CALLER_DECLARED_UNVERIFIED')
        self.assertFalse(any(r['policy'].values()))
        self.assertEqual(r['selected']['integration'], 'BUILTIN_READ_ONLY')

    def test_source_chooses_single_vineflower(self):
        r = self.m.choose('jar', 'source', input_path='C:/some path/target.jar')
        self.assertEqual(r['selected']['tool'], 'vineflower')
        self.assertEqual(r['selected']['suggested_argv'][3], 'vineflower')
        self.assertEqual(len(r['next_if']), 1)
        self.assertEqual(r['next_if'][0]['tool'], 'cfr')
        self.assertNotIn('install', r['selected']['suggested_argv'])

    def test_poor_decompile_chooses_only_cfr(self):
        r = self.m.choose('jar', signal='poor-decompile')
        self.assertEqual(r['resolved_goal'], 'source')
        self.assertEqual(r['selected']['tool'], 'cfr')
        self.assertEqual(r['next_if'][0]['tool'], 'vineflower')

    def test_given_source_skips_tool_when_not_needed(self):
        r = self.m.choose('jar', goal='source', has_source=True)
        self.assertEqual(r['decision'], 'NO_TOOL')
        self.assertIsNone(r['selected'])

    def test_header_only_class_and_java_17_version(self):
        f = self.classfile()
        info = self.m.inspect(f)
        self.assertEqual(info['kind'], 'class')
        self.assertEqual(info['classfile_major'], 61)
        self.assertEqual(info['java_version'], 17)
        self.assertEqual(self.m.choose(info['kind'])['selected']['tool'], 'javap')

    def test_jar_listing_is_bounded_and_only_metadata(self):
        f = self.jar(classes=('b/B.class', 'a/A.class', 'c/C.class'))
        with mock.patch.object(zipfile.ZipFile, 'read', side_effect=AssertionError('decompress')), \
             mock.patch.object(zipfile.ZipFile, 'extract', side_effect=AssertionError('extract')):
            info = self.m.inspect(f, limit=2)
        self.assertEqual(info['kind'], 'jar')
        self.assertEqual(info['archive']['class_count'], 3)
        self.assertEqual(info['archive']['class_sample'], ['a/A.class', 'b/B.class'])
        self.assertTrue(info['archive']['sample_truncated'])
        self.assertFalse(info['executed'])

    def test_javap_on_jar_needs_named_class(self):
        r = self.m.choose('jar', 'bytecode', input_path='x.jar')
        self.assertEqual(r['decision'], 'NEEDS_DETAIL')
        self.assertIsNone(r['selected'])
        self.assertEqual(r['next_if'][0]['tool'], 'archive-index')
        specified = self.m.choose('jar', 'bytecode', input_path='x.jar', class_name='pkg.A$Inner')
        self.assertEqual(specified['selected']['tool'], 'javap')
        self.assertEqual(specified['selected']['suggested_argv'][-1], 'pkg.A$Inner')

    def test_instruction_metadata_not_call_graph(self):
        r = self.m.choose('jar', goal='calls')
        self.assertEqual(r['selected']['tool'], 'sootup')
        self.assertEqual(r['decision'], 'ADVISORY_ONLY')
        self.assertIsNone(r['selected']['suggested_argv'])

    def test_encrypted_strings_avoid_dynamic_exec(self):
        r = self.m.choose('class', signal='encrypted-strings')
        self.assertEqual(r['selected']['tool'], 'javap')
        self.assertIn('threadtear', [x['tool'] for x in r['alternatives']])

    def test_mapping_never_claims_original_names(self):
        r = self.m.choose('jar', signal='obfuscated-names')
        self.assertEqual(r['selected']['tool'], 'enigma')
        self.assertEqual(r['decision'], 'ADVISORY_ONLY')
        self.assertEqual([x['tool'] for x in r['next_if']], ['mapping-io', 'tiny-remapper'])

    def test_version_matching_needs_second_verified_jar(self):
        r = self.m.choose('jar', goal='versions')
        self.assertEqual(r['decision'], 'NEEDS_DETAIL')
        good = self.m.choose('jar', goal='versions', compared_kind='jar', compared_path='b.jar')
        self.assertEqual(good['selected']['tool'], 'matcher')
        self.assertEqual(good['decision'], 'ADVISORY_ONLY')
        bad = self.m.choose('jar', goal='versions', compared_kind='apk', compared_path='app.apk')
        self.assertEqual(bad['decision'], 'NEEDS_DETAIL')

    def test_android_vs_native_are_separate(self):
        self.assertEqual(self.m.choose(self.m.inspect(self.apk())['kind'])['selected']['tool'], 'jadx')
        self.assertEqual(self.m.choose(self.m.inspect(self.exe())['kind'])['selected']['tool'], 'rea')
        self.assertEqual(self.m.choose('apk', 'native')['decision'], 'STOP')
        self.assertEqual(self.m.choose('pe', 'source')['decision'], 'STOP')

    def test_unknown_or_ambiguous_never_selects_engine(self):
        for kind in ('unknown', 'ambiguous'):
            r = self.m.choose(kind)
            self.assertEqual(r['decision'], 'STOP')
            self.assertIsNone(r['selected'])

    def test_extension_content_mismatch_blocks(self):
        path = self.root / 'spoof.jar'
        path.write_bytes(b'MZ' + b'\0' * 100)
        with self.assertRaises(self.m.SelectionError):
            self.m.inspect(path)
        self.jar('spoof.apk')
        with self.assertRaises(self.m.SelectionError):
            self.m.inspect(self.root / 'spoof.apk')

    def test_symlink_refused(self):
        f = self.jar()
        alias = self.root / 'alias.jar'
        try:
            alias.symlink_to(f)
        except (OSError, NotImplementedError):
            self.skipTest('cannot create symlink on this OS')
        with self.assertRaises(self.m.SelectionError):
            self.m.inspect(alias)

    def test_size_limit_and_sample_limit_are_explicit(self):
        with self.assertRaises(self.m.SelectionError):
            self.m.inspect(self.jar(), limit=301)
        path = self.jar('big.jar')
        original_stat = Path.stat
        def exaggerated_stat(node, **kwargs):
            original = original_stat(node, **kwargs)
            if node == path:
                class LargeFile:
                    st_size = self.m.MAX_TARGET_BYTES + 1
                    st_mode = original.st_mode
                return LargeFile()
            return original
        with mock.patch.object(Path, 'stat', exaggerated_stat):
            with self.assertRaises(self.m.SelectionError):
                self.m.inspect(path)

    def test_invalid_class_name_never_becomes_argv(self):
        with self.assertRaises(self.m.SelectionError):
            self.m.choose('jar', 'bytecode', class_name='--help; rm -rf')

    def test_cli_plan_uses_file_evidence_without_writes_or_subprocesses(self):
        f = self.jar()
        out = io.StringIO()
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')), \
             contextlib.redirect_stdout(out):
            self.assertEqual(self.m.main(['choose', '--input', str(f), '--goal', 'auto']), 0)
        import json
        payload = json.loads(out.getvalue())
        self.assertEqual(payload['selected']['tool'], 'archive-index')
        self.assertEqual(payload['evidence']['input']['archive']['class_count'], 2)
        self.assertFalse(any(payload['policy'].values()))
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), [f.name])

    def test_declared_kind_is_unverified_no_disk(self):
        out = io.StringIO()
        with mock.patch.object(self.m, 'inspect', side_effect=AssertionError('I/O')), \
             contextlib.redirect_stdout(out):
            self.assertEqual(self.m.main(['choose', '--kind', 'jar', '--goal', 'structure']), 0)
        self.assertIn('CALLER_DECLARED_UNVERIFIED', out.getvalue())

    def test_bad_options_fail_closed_with_clear_exit_code(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(self.m.main(['choose', '--goal', 'source']), 2)
            self.assertEqual(self.m.main(['choose', '--kind', 'jar', '--input', 'a.jar']), 2)
            self.assertEqual(self.m.main(['choose', '--kind', 'jar', '--compare-to', 'b.jar']), 2)

    def test_not_wired_tools_are_never_suggested_as_executable(self):
        for goal in ('calls', 'mapping', 'versions', 'android'):
            kwargs = {'compared_kind': 'jar', 'compared_path': 'b.jar'} if goal == 'versions' else {}
            kind = 'apk' if goal == 'android' else 'jar'
            r = self.m.choose(kind, goal=goal, **kwargs)
            self.assertEqual(r['decision'], 'ADVISORY_ONLY')
            self.assertIsNone(r['selected']['suggested_argv'])


if __name__ == '__main__':
    unittest.main()
