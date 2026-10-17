"""Source-contract tests. Fake tool runs do not prove real decompiler behavior."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / 'toolkit.py'
    if not path.is_file():
        raise AssertionError('Missing opt-in toolkit implementation')
    spec = importlib.util.spec_from_file_location('optional_re_toolkit', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.tool = load()
        self.tmp = tempfile.TemporaryDirectory(prefix='re toolkit test ')
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name) / 'cache'
        self.jar_bytes = b'trusted-test-tool-not-a-real-decompiler'
        self.pin = {'version': 'fixture', 'url': 'https://example.invalid/tool.jar',
                    'sha256': hashlib.sha256(self.jar_bytes).hexdigest(),
                    'filename': 'fixture.jar'}

    def install_fixture(self, name='cfr'):
        path = self.cache / name / 'fixture.jar'
        path.parent.mkdir(parents=True)
        path.write_bytes(self.jar_bytes)
        return path

    def target(self):
        path = Path(self.tmp.name) / 'original input.class'
        path.write_bytes(b'fixture-bytecode')
        return path

    def test_import_does_not_execute_or_download(self):
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')), \
             mock.patch('urllib.request.urlopen', side_effect=AssertionError('network')):
            load()
        self.assertFalse(self.cache.exists())

    def test_help_does_not_read_pins_or_probe_tools(self):
        with mock.patch.object(self.tool, 'load_pins', side_effect=AssertionError('pins')), \
             mock.patch('subprocess.run', side_effect=AssertionError('spawn')), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.tool.main([]), 0)

    def test_catalog_does_not_inspect_installations(self):
        output = io.StringIO()
        with mock.patch.object(self.tool, 'installed_jar', side_effect=AssertionError('probe')), \
             mock.patch('subprocess.run', side_effect=AssertionError('spawn')), \
             mock.patch('urllib.request.urlopen', side_effect=AssertionError('network')), \
             contextlib.redirect_stdout(output):
            self.assertEqual(self.tool.main(['--cache', str(self.cache), 'catalog']), 0)
        self.assertIn('vineflower', output.getvalue())
        self.assertFalse(self.cache.exists())

    def test_install_only_selected_jar(self):
        with mock.patch.object(self.tool, 'fetch_bytes', return_value=self.jar_bytes) as get:
            result = self.tool.install_jar('cfr', self.pin, self.cache)
        self.assertEqual(Path(result['path']).read_bytes(), self.jar_bytes)
        self.assertEqual(get.call_args.args[0], self.pin['url'])
        self.assertFalse((self.cache / 'vineflower').exists())
        self.assertFalse((self.cache / 'rea').exists())

    def test_existing_verified_jar_avoids_network(self):
        self.install_fixture()
        with mock.patch.object(self.tool, 'fetch_bytes', side_effect=AssertionError('network')):
            self.assertTrue(self.tool.install_jar('cfr', self.pin, self.cache)['reused'])

    def test_corrupt_download_is_not_installed(self):
        with mock.patch.object(self.tool, 'fetch_bytes', return_value=b'bad'):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.install_jar('cfr', self.pin, self.cache)
        self.assertFalse((self.cache / 'cfr' / 'fixture.jar').exists())

    def test_corrupt_installed_jar_is_not_repaired_or_executed(self):
        self.install_fixture().write_bytes(b'corrupt')
        with mock.patch.object(self.tool, 'fetch_bytes', side_effect=AssertionError('network')):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.install_jar('cfr', self.pin, self.cache)

    def test_md5_published_checksum_is_supported_without_claiming_sha256_pin(self):
        pin = {**self.pin, 'sha256': None,
               'md5': hashlib.md5(self.jar_bytes, usedforsecurity=False).hexdigest()}
        self.assertEqual(self.tool.verify_bytes(self.jar_bytes, pin),
                         hashlib.sha256(self.jar_bytes).hexdigest())
        with self.assertRaises(self.tool.ToolkitError):
            self.tool.verify_bytes(b'wrong', pin)

    def test_missing_tool_does_not_install_or_create_run(self):
        with mock.patch.object(self.tool, 'fetch_bytes', side_effect=AssertionError('network')):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.decompile('cfr', self.pin, self.cache, self.target(), 'job')
        self.assertFalse((self.cache / 'runs').exists())

    def fake_java(self, argv, **kwargs):
        if '--outputdir' in argv:
            output = Path(argv[argv.index('--outputdir') + 1])
        else:
            output = Path(argv[-1])
        output.mkdir(parents=True, exist_ok=True)
        (output / 'Example.java').write_text('class Example {}', encoding='utf-8')
        return subprocess.CompletedProcess(argv, 0)

    def test_cfr_argv_snapshot_and_receipt(self):
        self.install_fixture()
        original = self.target()
        lib = Path(self.tmp.name) / 'library with space.jar'
        lib.write_bytes(b'library')
        with mock.patch('subprocess.run', side_effect=self.fake_java) as run:
            receipt = self.tool.decompile('cfr', self.pin, self.cache, original,
                                          'cfr-job', libraries=[lib])
        argv = run.call_args.args[0]
        self.assertIn('--outputdir', argv)
        self.assertIn('--extraclasspath', argv)
        self.assertNotIn(str(original), argv)  # immutable copied input is analyzed
        self.assertFalse(run.call_args.kwargs.get('shell', False))
        self.assertEqual(original.read_bytes(), b'fixture-bytecode')
        self.assertEqual(receipt['status'], 'COMPLETED')
        self.assertEqual(receipt['runtime_verification'], 'NOT_RUN')
        self.assertEqual(receipt['source_equivalence'], 'NOT_VERIFIED')
        self.assertEqual(receipt['coverage'], 'NOT_VERIFIED')
        self.assertEqual(receipt['input_sha256'], hashlib.sha256(b'fixture-bytecode').hexdigest())
        self.assertEqual(len(receipt['libraries']), 1)
        self.assertTrue((self.cache / 'runs/cfr-job/receipt.json').is_file())

    def test_vineflower_uses_existing_adapter_flags(self):
        self.install_fixture('vineflower')
        with mock.patch('subprocess.run', side_effect=self.fake_java) as run:
            self.tool.decompile('vineflower', self.pin, self.cache, self.target(), 'vf-job')
        argv = run.call_args.args[0]
        for flag in ('--folder', '--thread-count=2', '--remove-synthetic=0', '--remove-bridge=0'):
            self.assertIn(flag, argv)

    def test_existing_run_is_preserved(self):
        self.install_fixture()
        run_dir = self.cache / 'runs/job'
        run_dir.mkdir(parents=True)
        marker = run_dir / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaises(self.tool.ToolkitError):
            self.tool.decompile('cfr', self.pin, self.cache, self.target(), 'job')
        self.assertEqual(marker.read_text(), 'keep')

    def test_path_traversal_run_name_rejected(self):
        with self.assertRaises(self.tool.ToolkitError):
            self.tool.decompile('cfr', self.pin, self.cache, self.target(), '../escape')

    def test_nonzero_exit_records_error(self):
        self.install_fixture()
        with mock.patch('subprocess.run', return_value=subprocess.CompletedProcess([], 7)):
            result = self.tool.decompile('cfr', self.pin, self.cache, self.target(), 'failed')
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['exit_code'], 7)

    def test_empty_output_not_success(self):
        self.install_fixture()
        with mock.patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)):
            result = self.tool.decompile('cfr', self.pin, self.cache, self.target(), 'empty')
        self.assertEqual(result['status'], 'ERROR')

    def test_timeout_receipt_not_success(self):
        self.install_fixture()
        with mock.patch('subprocess.run', side_effect=subprocess.TimeoutExpired(['java'], 1)):
            result = self.tool.decompile('cfr', self.pin, self.cache, self.target(), 'timeout')
        self.assertEqual(result['status'], 'ERROR')
        self.assertEqual(result['reason'], 'TIMEOUT')

    def test_symlink_tool_rejected(self):
        jar = self.install_fixture()
        real = jar.with_suffix('.real')
        jar.rename(real)
        try:
            jar.symlink_to(real)
        except OSError:
            self.skipTest('Host does not support symlinks')
        with self.assertRaises(self.tool.ToolkitError):
            self.tool.installed_jar('cfr', self.pin, self.cache)

    def test_provider_config_compatible_without_executing(self):
        jar = self.install_fixture('vineflower')
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')):
            result = self.tool.provider_config(self.pin, self.cache, 'java', ['deps:0'])
        self.assertEqual(result['jar'], str(jar))
        self.assertEqual(result['jar_sha256'], self.pin['sha256'])
        self.assertEqual(result['classpath_root_ids'], ['deps:0'])
        self.assertTrue(result['allow_execute'])

    def test_rea_setup_mcp_upgrade_uninstall_are_not_implicit_integrations(self):
        for command in ('setup', 'mcp', 'upgrade', 'uninstall'):
            with self.subTest(command=command), self.assertRaises(self.tool.ToolkitError):
                self.tool.run_rea({'version': '6.5.0'}, self.cache, [command])
        self.assertFalse(self.cache.exists())

    def test_rea_missing_install_never_runs_npx(self):
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.run_rea({'version': '6.5.0'}, self.cache, ['--version'])

    def test_node_version_gate_matches_pinned_upstream_range(self):
        for version in ('22.19.0', '22.20.0', '24.11.0', '26.0.0', '27.0.0'):
            self.assertTrue(self.tool.node_supported(version), version)
        for version in ('20.19.0', '22.18.0', '23.0.0', '24.10.0', '25.0.0'):
            self.assertFalse(self.tool.node_supported(version), version)


    def rea_fixture(self, version='6.5.0'):
        root = self.cache / 'rea/node_modules/rea-agents'
        root.mkdir(parents=True, exist_ok=True)
        (root / 'package.json').write_text(json.dumps({'name': 'rea-agents', 'version': version}))
        entry = root / 'scripts/rea.mjs'
        entry.parent.mkdir(exist_ok=True)
        entry.write_text('// authored fixture, not REA')
        return entry

    def test_rea_pinned_entry_runs_without_shell_or_npx(self):
        entry = self.rea_fixture()
        def run(argv, **kwargs):
            if argv[-1] == '--version' and len(argv) == 2:
                return subprocess.CompletedProcess(argv, 0, stdout='v24.11.0\n')
            return subprocess.CompletedProcess(argv, 3)
        with mock.patch('subprocess.run', side_effect=run) as spawn:
            result = self.tool.run_rea({'version': '6.5.0'}, self.cache, ['--help'])
        self.assertEqual(result, 3)
        self.assertEqual(spawn.call_args.args[0], ['node', str(entry), '--help'])
        self.assertIs(spawn.call_args.kwargs['shell'], False)
        self.assertEqual(spawn.call_count, 2)

    def test_wrong_rea_version_never_starts_node(self):
        self.rea_fixture('0.0.0')
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.run_rea({'version': '6.5.0'}, self.cache, ['--help'])

    def test_existing_rea_install_avoids_npm_and_network(self):
        self.rea_fixture()
        with mock.patch('subprocess.run', side_effect=AssertionError('spawn')):
            result = self.tool.install_rea({'version': '6.5.0'}, self.cache)
        self.assertTrue(result['reused'])

    def test_explicit_rea_install_is_local_and_disables_lifecycle_scripts(self):
        npm = Path(self.tmp.name) / 'npm-cli.js'
        npm.write_text('// npm fixture')
        def run(argv, **kwargs):
            if argv == ['node', '--version']:
                return subprocess.CompletedProcess(argv, 0, stdout='v24.11.0\n')
            self.rea_fixture()
            (self.cache / 'rea/package-lock.json').write_text('{}')
            return subprocess.CompletedProcess(argv, 0)
        with mock.patch('shutil.which', return_value=str(npm)), \
             mock.patch('subprocess.run', side_effect=run) as spawn:
            result = self.tool.install_rea({'version': '6.5.0'}, self.cache)
        argv = spawn.call_args.args[0]
        self.assertEqual(argv[0], 'node')
        self.assertEqual(argv[2], 'install')
        self.assertTrue(Path(argv[1]).samefile(npm))
        for flag in ('--prefix', '--ignore-scripts', '--no-audit', '--no-fund'):
            self.assertIn(flag, argv)
        self.assertNotIn('--global', argv)
        self.assertFalse(result['mcp_registered'])
        self.assertFalse(result['providers_installed'])
        self.assertEqual(json.loads((self.cache / 'rea/package.json').read_text())['dependencies'],
                         {'rea-agents': '6.5.0'})

    def test_windows_npm_cmd_is_mapped_to_js_not_shell(self):
        npm_cmd = Path(self.tmp.name) / 'Node with spaces/npm.cmd'
        npm_js = npm_cmd.parent / 'node_modules/npm/bin/npm-cli.js'
        npm_js.parent.mkdir(parents=True)
        npm_cmd.write_text('@echo off')
        npm_js.write_text('// npm fixture')
        def run(argv, **kwargs):
            if argv == ['node', '--version']:
                return subprocess.CompletedProcess(argv, 0, stdout='v24.11.0\n')
            self.rea_fixture()
            (self.cache / 'rea/package-lock.json').write_text('{}')
            return subprocess.CompletedProcess(argv, 0)
        with mock.patch('shutil.which', return_value=str(npm_cmd)), \
             mock.patch('subprocess.run', side_effect=run) as spawn:
            self.tool.install_rea({'version': '6.5.0'}, self.cache)
        self.assertEqual(spawn.call_args.args[0][0], 'node')
        self.assertTrue(Path(spawn.call_args.args[0][1]).samefile(npm_js))
        self.assertIs(spawn.call_args.kwargs['shell'], False)

    def test_other_local_npm_project_is_not_overwritten(self):
        root = self.cache / 'rea'
        root.mkdir(parents=True)
        marker = root / 'package.json'
        marker.write_text('{"name":"another-project"}')
        npm = Path(self.tmp.name) / 'npm-cli.js'
        npm.write_text('// fixture')
        with mock.patch.object(self.tool, 'checked_node', return_value='node'), \
             mock.patch('shutil.which', return_value=str(npm)), \
             mock.patch('subprocess.run', side_effect=AssertionError('spawn')):
            with self.assertRaises(self.tool.ToolkitError):
                self.tool.install_rea({'version': '6.5.0'}, self.cache)
        self.assertEqual(marker.read_text(), '{"name":"another-project"}')

if __name__ == '__main__':
    unittest.main()
