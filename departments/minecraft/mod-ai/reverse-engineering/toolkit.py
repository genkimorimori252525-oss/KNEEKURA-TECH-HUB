"""Opt-in tool shelf. Import/help/catalog never probe or start analysis tools.

Standard-library only. No connection to the Hub's normal startup, task routing,
Core imports, package installation, agent skills or MCP configuration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_INPUT = 256 * 1024 * 1024
BLOCKED_REA = {'setup', 'mcp', 'upgrade', 'uninstall'}


class ToolkitError(RuntimeError):
    """An explicit operation failed; never silently repair or fall back."""


def load_pins() -> dict:
    return json.loads((HERE / 'tools.json').read_text(encoding='utf-8'))['tools']


def no_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part, 'is_junction', lambda: False)():
            raise ToolkitError(f'Symlink/junction path is not accepted: {part}')


def read_file(path: Path, limit: int = MAX_INPUT) -> bytes:
    no_links(path)
    if not path.is_file():
        raise ToolkitError(f'File not found: {path}')
    with path.open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ToolkitError(f'File exceeds {limit} byte limit: {path}')
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_bytes(data: bytes, pin: dict) -> str:
    observed = sha256(data)
    if pin.get('sha256'):
        good = observed == pin['sha256']
    elif pin.get('md5'):
        # Legacy official CFR release only publishes MD5 on its download page.
        # Record SHA-256 as observed identity; do not call this a SHA-256 pin.
        good = hashlib.md5(data, usedforsecurity=False).hexdigest() == pin['md5']
    else:
        raise ToolkitError('No trusted artifact checksum configured')
    if not good:
        raise ToolkitError('Tool checksum mismatch; no execution or automatic replacement')
    return observed


def fetch_bytes(url: str) -> bytes:
    if not url.startswith('https://'):
        raise ToolkitError('HTTPS download required')
    request = urllib.request.Request(url, headers={'User-Agent': 'Kneekura-Optional-RE/1'})
    with urllib.request.urlopen(request, timeout=60) as response:
        if not response.geturl().startswith('https://'):
            raise ToolkitError('Non-HTTPS redirect refused')
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ToolkitError('Download size limit exceeded')
    return data


def installed_jar(name: str, pin: dict, cache: Path) -> Path:
    path = cache / name / pin['filename']
    if not path.exists() and not path.is_symlink():
        raise ToolkitError(f'{name} is not installed; explicitly run: toolkit.py install {name}')
    verify_bytes(read_file(path, MAX_DOWNLOAD), pin)
    return path


def install_jar(name: str, pin: dict, cache: Path) -> dict:
    path = cache / name / pin['filename']
    no_links(path)
    reused = path.exists()
    if reused:
        installed_jar(name, pin, cache)
    else:
        data = fetch_bytes(pin['url'])
        verify_bytes(data, pin)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation: concurrent installers never replace another file.
        with path.open('xb') as stream:
            stream.write(data)
    return {'tool': name, 'version': pin['version'], 'path': str(path),
            'sha256': sha256(read_file(path, MAX_DOWNLOAD)), 'reused': reused,
            'checksum_basis': 'pinned-sha256' if pin.get('sha256') else 'published-md5'}


def node_supported(version: str) -> bool:
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', version.strip())
    if not match:
        return False
    major, minor, patch = map(int, match.groups())
    return major >= 26 or (major == 22 and minor >= 19) or (major == 24 and minor >= 11)


def checked_node(node: str) -> str:
    result = subprocess.run([node, '--version'], capture_output=True, text=True,
                            timeout=15, check=True, shell=False)
    if not node_supported(result.stdout):
        raise ToolkitError('REA requires Node ^22.19.0 || ^24.11.0 || >=26.0.0')
    return node


def rea_entry(pin: dict, cache: Path) -> Path:
    root = cache / 'rea' / 'node_modules' / 'rea-agents'
    meta = json.loads(read_file(root / 'package.json', MAX_DOWNLOAD).decode('utf-8'))
    if meta.get('name') != 'rea-agents' or meta.get('version') != pin['version']:
        raise ToolkitError('Installed REA package identity differs from tools.json')
    entry = root / pin.get('entry', 'scripts/rea.mjs')
    read_file(entry, MAX_DOWNLOAD)
    return entry


def install_rea(pin: dict, cache: Path, node: str = 'node') -> dict:
    root = cache / 'rea'
    no_links(root)
    meta = root / 'node_modules' / 'rea-agents' / 'package.json'
    if meta.exists():
        return {'tool': 'rea', 'version': pin['version'],
                'entry': str(rea_entry(pin, cache)), 'reused': True}
    checked_node(node)
    npm = shutil.which('npm')
    if not npm:
        raise ToolkitError('npm unavailable; install the supported Node/npm runtime explicitly')
    npm_path = Path(npm).resolve()
    # Avoid cmd.exe/shell interpolation, including Windows paths with spaces.
    if npm_path.suffix.lower() in {'.cmd', '.bat'}:
        npm_path = npm_path.parent / 'node_modules' / 'npm' / 'bin' / 'npm-cli.js'
    if not npm_path.is_file():
        raise ToolkitError('Cannot locate npm-cli.js; no shell fallback is performed')
    package = {'name': 'kneekura-local-re-tools', 'private': True,
               'version': '1.0.0', 'dependencies': {'rea-agents': pin['version']}}
    root.mkdir(parents=True, exist_ok=True)
    package_path = root / 'package.json'
    if package_path.exists():
        if json.loads(read_file(package_path).decode('utf-8')) != package:
            raise ToolkitError('Existing local npm prefix has a different package definition')
    else:
        package_path.write_text(json.dumps(package, indent=2) + '\n', encoding='utf-8')
    operation = 'ci' if (root / 'package-lock.json').exists() else 'install'
    argv = [node, str(npm_path), operation, '--prefix', str(root), '--ignore-scripts',
            '--no-audit', '--no-fund', '--cache', str(cache / 'npm-cache')]
    subprocess.run(argv, cwd=root, check=True, timeout=600, shell=False)
    return {'tool': 'rea', 'version': pin['version'], 'entry': str(rea_entry(pin, cache)),
            'reused': False, 'lock_sha256': sha256(read_file(root / 'package-lock.json')),
            'mcp_registered': False, 'providers_installed': False}


def run_rea(pin: dict, cache: Path, args: list[str], node: str = 'node') -> int:
    if not args or args[0] in BLOCKED_REA:
        raise ToolkitError('Use an explicit investigation command; setup/MCP/upgrade/uninstall are outside this shelf')
    entry = rea_entry(pin, cache)  # Never use npx or auto-install a missing tool.
    checked_node(node)
    return subprocess.run([node, str(entry), *args], timeout=600, shell=False).returncode


def provider_config(pin: dict, cache: Path, java: str, root_ids: list[str]) -> dict:
    jar = installed_jar('vineflower', pin, cache)
    return {'allow_execute': True, 'java': java, 'jar': str(jar),
            'jar_sha256': sha256(read_file(jar, MAX_DOWNLOAD)), 'version': pin['version'],
            'memory_mib': 1024, 'threads': 2, 'timeout_seconds': 300,
            'classpath_root_ids': root_ids}


def decompile(name: str, pin: dict, cache: Path, target: Path, run_name: str,
              *, java: str = 'java', libraries: list[Path] | None = None,
              timeout: int = 300) -> dict:
    if name not in {'cfr', 'vineflower'}:
        raise ToolkitError('Choose one Java decompiler explicitly')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', run_name):
        raise ToolkitError('Run name must be 1–80 letters/digits/underscore/hyphen')
    if target.suffix.lower() not in {'.jar', '.class'}:
        raise ToolkitError('Java comparison accepts .jar or .class only, not APK/EXE')
    if not 1 <= timeout <= 1800:
        raise ToolkitError('Timeout must be 1–1800 seconds')
    jar = installed_jar(name, pin, cache)
    tool_data = read_file(jar, MAX_DOWNLOAD)
    target_data = read_file(target)
    library_data = [(lib, read_file(lib)) for lib in libraries or []]
    if sum(len(data) for _, data in library_data) + len(target_data) > 512 * 1024 * 1024:
        raise ToolkitError('Combined input/classpath size limit exceeded')
    work = cache / 'runs' / run_name
    no_links(work)
    try:
        work.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ToolkitError('Run already exists; choose a new name, never overwrite evidence') from exc
    source = work / ('input' + target.suffix.lower())
    source.write_bytes(target_data)
    tool_copy = work / 'tool.jar'
    tool_copy.write_bytes(tool_data)
    libs = []
    for i, (_, data) in enumerate(library_data):
        path = work / f'library-{i}.jar'
        path.write_bytes(data)
        libs.append(str(path))
    output = work / 'sources'
    argv = [java, '-Xmx1024m', '-jar', str(tool_copy)]
    if name == 'cfr':
        argv += [str(source), '--outputdir', str(output), '--clobber', 'false']
        if libs:
            argv += ['--extraclasspath', os.pathsep.join(libs)]
    else:
        argv += ['--folder', '--thread-count=2', '--remove-synthetic=0', '--remove-bridge=0',
                 *['--add-external=' + path for path in libs], str(source), str(output)]
    receipt = {'schema_version': 1, 'tool': name, 'version': pin['version'],
               'tool_sha256': sha256(tool_data), 'input_sha256': sha256(target_data),
               'libraries': [{'order': i, 'sha256': sha256(data)}
                             for i, (_, data) in enumerate(library_data)],
               'argv': argv, 'status': 'ERROR', 'exit_code': None,
               'source_equivalence': 'NOT_VERIFIED', 'runtime_verification': 'NOT_RUN',
               'coverage': 'NOT_VERIFIED', 'outputs': [], 'run_directory': str(work)}
    try:
        with (work / 'tool.log').open('wb') as log:
            result = subprocess.run(argv, cwd=work, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=timeout, shell=False)
        receipt['exit_code'] = result.returncode
        files = sorted(output.rglob('*.java'))
        if result.returncode == 0 and files:
            receipt['outputs'] = [{'path': str(p.relative_to(output)),
                                   'sha256': sha256(read_file(p))} for p in files]
            receipt['status'] = 'COMPLETED'
        else:
            receipt['reason'] = 'NONZERO_EXIT_OR_NO_JAVA_OUTPUT'
    except subprocess.TimeoutExpired:
        receipt['reason'] = 'TIMEOUT'
    except (OSError, ToolkitError) as exc:
        receipt['reason'] = str(exc)
    (work / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # The selection catalogue is loaded only for an explicit choose request.
    # Regular help/catalog/CLI/Hub imports never touch the router or its inputs.
    if argv[:1] == ['choose']:
        import importlib.util
        spec = importlib.util.spec_from_file_location('kneekura_opt_in_selector', HERE / 'selector.py')
        if spec is None or spec.loader is None:
            raise ToolkitError('Optional selection router is missing')
        selector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(selector)
        return selector.main(['choose', *argv[1:]])
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog='Optional read-only plan: toolkit.py choose --input FILE --goal auto')
    parser.add_argument('--cache', type=Path, default=HERE / '.local')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('catalog', help='Static catalog only; never check installed tools')
    install = sub.add_parser('install', help='Explicitly install ONE local tool')
    install.add_argument('tool', choices=['cfr', 'vineflower', 'rea'])
    install.add_argument('--node', default='node')
    dec = sub.add_parser('decompile', help='Explicit isolated Java comparison')
    dec.add_argument('tool', choices=['cfr', 'vineflower'])
    dec.add_argument('input', type=Path)
    dec.add_argument('--run', required=True)
    dec.add_argument('--java', default='java')
    dec.add_argument('--library', type=Path, action='append', default=[])
    dec.add_argument('--timeout', type=int, default=300)
    config = sub.add_parser('provider-config', help='JSON for the EXISTING Vineflower CAS provider')
    config.add_argument('--java', default='java')
    config.add_argument('--classpath-root-id', action='append', default=[])
    rea = sub.add_parser('rea', help='Explicit local REA CLI; no setup or global MCP registration')
    rea.add_argument('--node', default='node')
    rea.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        pins = load_pins()
        if args.command == 'catalog':
            print(json.dumps(pins, indent=2))
            return 0
        cache = args.cache.absolute()
        no_links(cache)
        if args.command == 'install':
            result = (install_rea(pins['rea'], cache, args.node) if args.tool == 'rea'
                      else install_jar(args.tool, pins[args.tool], cache))
        elif args.command == 'decompile':
            result = decompile(args.tool, pins[args.tool], cache, args.input.absolute(),
                               args.run, java=args.java, libraries=args.library, timeout=args.timeout)
        elif args.command == 'provider-config':
            result = provider_config(pins['vineflower'], cache, args.java, args.classpath_root_id)
        else:
            forward = args.args[1:] if args.args[:1] == ['--'] else args.args
            return run_rea(pins['rea'], cache, forward, args.node)
        print(json.dumps(result, indent=2))
        return 2 if result.get('status') == 'ERROR' else 0
    except (ToolkitError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
