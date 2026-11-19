"""Explicit network/real-engine smoke on an authored fixture, never imported by tests."""
from pathlib import Path
import json
import subprocess
import tempfile
import toolkit


def main() -> None:
    pins = toolkit.load_pins()
    report = {'scope': 'AUTHORED_JAVA17_FIXTURE_AND_REA_CLI_ONLY', 'tools': {},
              'owner_pc': 'NOT_TESTED', 'native_rea_providers': 'NOT_TESTED',
              'arbitrary_game_equivalence': 'NOT_TESTED'}
    with tempfile.TemporaryDirectory(prefix='kneekura-re-smoke-') as temp:
        root = Path(temp)
        cache = root / 'cache'
        source = root / 'Example.java'
        source.write_text('public class Example {\n'
                          ' public static int score(int n) { return n * 3; }\n'
                          ' public static void main(String[] args) { System.out.println(score(7)); }\n'
                          '}\n', encoding='utf-8')
        classes = root / 'classes'
        classes.mkdir()
        subprocess.run(['javac', '--release', '17', '-d', str(classes), str(source)],
                       check=True, timeout=60)
        target = root / 'example.jar'
        subprocess.run(['jar', '--create', '--file', str(target), '-C', str(classes), '.'],
                       check=True, timeout=60)
        original_hash = toolkit.sha256(target.read_bytes())
        for name in ('cfr', 'vineflower'):
            installed = toolkit.install_jar(name, pins[name], cache)
            receipt = toolkit.decompile(name, pins[name], cache, target, name + '-smoke')
            assert receipt['status'] == 'COMPLETED', receipt
            sources = list((cache / 'runs' / (name + '-smoke') / 'sources').rglob('*.java'))
            rebuilt = root / (name + '-rebuilt')
            rebuilt.mkdir()
            subprocess.run(['javac', '--release', '17', '-d', str(rebuilt), *map(str, sources)],
                           check=True, timeout=60)
            result = subprocess.run(['java', '-cp', str(rebuilt), 'Example'],
                                    check=True, capture_output=True, text=True, timeout=30)
            assert result.stdout.strip() == '21', result.stdout
            assert toolkit.sha256(target.read_bytes()) == original_hash
            report['tools'][name] = {'version': pins[name]['version'],
                                     'tool_sha256': installed['sha256'],
                                     'checksum_basis': installed['checksum_basis'],
                                     'fixture': 'DECOMPILED_RECOMPILED_OUTPUT_21'}
        installed = toolkit.install_rea(pins['rea'], cache)
        assert toolkit.run_rea(pins['rea'], cache, ['--version']) == 0
        assert toolkit.run_rea(pins['rea'], cache, ['--help']) == 0
        report['tools']['rea'] = {'version': pins['rea']['version'],
                                  'lock_sha256': installed['lock_sha256'],
                                  'scope': 'PINNED_PACKAGE_INSTALL_VERSION_HELP_ONLY'}
    # Only authored-tool summary, no binaries, decompiled third-party source or machine paths.
    Path('re-smoke-summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
