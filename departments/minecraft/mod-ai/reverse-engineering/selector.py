"""Cold, deterministic selection for the *optional* reverse-engineering shelf.

No import-time I/O. Planning reads only a requested file header and (for JARs)
ZIP directory metadata; it never imports, installs, executes, or repairs a tool.
Advisory integrations are expressly NOT executable adapters.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import zipfile

MAX_TARGET_BYTES = 256 * 1024 * 1024
MAX_ZIP_ENTRIES = 100_000
MAX_PREVIEW_CLASSES = 300

# This catalogue is descriptive, not a package-manager manifest. Only the three
# named tools in tools.json are locally installable via the existing toolkit.
TOOLS = {
    'archive-index': ('BUILTIN_READ_ONLY', 'Python zipfile: names/counts only', None),
    'javap': ('JDK_EXPLICIT', 'JDK command; bytecode listing, not a call graph',
              'https://docs.oracle.com/en/java/javase/17/docs/specs/man/javap.html'),
    'vineflower': ('EXISTING_EXPLICIT', 'Pinned Java decompiler, existing MOD-AI CAS integration',
                   'https://github.com/Vineflower/vineflower'),
    'cfr': ('EXISTING_EXPLICIT', 'Pinned alternative Java decompiler; not an automatic second pass',
            'https://www.benf.org/other/cfr/'),
    'rea': ('EXISTING_EXPLICIT', 'CLI only; native analysis needs a separately configured provider',
            'https://github.com/morluto/rea'),
    'asm': ('ADVISORY_NOT_WIRED', 'Static classfile instruction visitors; build a scoped adapter first',
            'https://asm.ow2.io/'),
    'classgraph': ('ADVISORY_NOT_WIRED', 'Deep classpath relationships; JDK17 requires ClassGraph v5, not v6',
                  'https://github.com/classgraph/classgraph'),
    'sootup': ('ADVISORY_NOT_WIRED', 'Jimple, call graphs and data-flow; no existing adapter',
               'https://github.com/soot-oss/SootUp'),
    'enigma': ('ADVISORY_NOT_WIRED', 'Curated symbolic name mappings, not automatic name truth',
               'https://github.com/FabricMC/Enigma'),
    'matcher': ('ADVISORY_NOT_WIRED', 'Static matching of two Java JAR versions, not exact equivalence',
                'https://github.com/FabricMC/Matcher'),
    'mapping-io': ('ADVISORY_NOT_WIRED', 'Read/write mapping formats after mappings exist',
                   'https://github.com/FabricMC/mapping-io'),
    'tiny-remapper': ('ADVISORY_NOT_WIRED', 'Apply existing mappings to bytecode',
                      'https://github.com/FabricMC/tiny-remapper'),
    'recaf': ('ADVISORY_NOT_WIRED', 'Interactive investigation; Recaf 4 requires JDK22+ and JavaFX',
              'https://github.com/Col-E/Recaf'),
    'jadx': ('ADVISORY_NOT_WIRED', 'Android DEX/APK source analysis',
             'https://github.com/skylot/jadx'),
    'java-deobfuscator': ('RISK_REQUIRES_ISOLATION', 'Transformer-specific; some methods may execute untrusted code',
                          'https://github.com/java-deobfuscator/deobfuscator'),
    'threadtear': ('RISK_REQUIRES_ISOLATION', 'Some decryptors load/run target code; never automatic',
                   'https://github.com/loerting/threadtear'),
}

GOALS = ('auto', 'structure', 'source', 'bytecode', 'calls', 'strings',
         'mapping', 'versions', 'android', 'native')
SIGNALS = ('none', 'poor-decompile', 'obfuscated-names', 'encrypted-strings',
           'invokedynamic', 'changed-versions')
JAVA = {'jar', 'class'}
ANDROID = {'apk', 'dex'}
NATIVE = {'pe', 'elf', 'macho'}
EXTENSIONS = {'.jar': 'jar', '.class': 'class', '.apk': 'apk', '.dex': 'dex',
              '.exe': 'pe', '.dll': 'pe', '.so': 'elf'}
CLASS_NAME = re.compile(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*\Z', re.ASCII)


class SelectionError(ValueError):
    """Input cannot safely be classified or a proposed operation is invalid."""


def _no_links(path: Path) -> None:
    for node in (path, *path.parents):
        if node.is_symlink() or getattr(node, 'is_junction', lambda: False)():
            raise SelectionError(f'Symlink or junction refused: {node}')


def inspect(path: Path, *, limit: int = MAX_PREVIEW_CLASSES) -> dict:
    """Read only file headers and ZIP central-directory metadata; no decompression."""
    if not 0 <= limit <= MAX_PREVIEW_CLASSES:
        raise SelectionError('limit must be between 0 and 300')
    path = path.absolute()
    _no_links(path)
    if not path.is_file():
        raise SelectionError(f'Input is not a regular file: {path}')
    size = path.stat().st_size
    if size > MAX_TARGET_BYTES:
        raise SelectionError('Input exceeds 256 MiB inspection bound')
    with path.open('rb') as stream:
        head = stream.read(128)
    result = {'path': str(path), 'size_bytes': size, 'kind': 'unknown',
              'basis': 'FILE_MAGIC_AND_CONTAINER_METADATA', 'executed': False}
    if head.startswith(b'\xca\xfe\xba\xbe') and len(head) >= 8:
        major = int.from_bytes(head[6:8], 'big')
        # CAFEBABE also marks Mach-O fat binaries. Reject impossible JVM majors.
        if 45 <= major <= 200:
            result.update(kind='class', classfile_major=major, java_version=major - 44)
        else:
            result['kind'] = 'macho'
    elif head.startswith((b'PK\x03\x04', b'PK\x05\x06')):
        try:
            with zipfile.ZipFile(path) as archive:
                # Metadata only; no calls to archive.open(), read(), or extract().
                files = archive.infolist()
                if len(files) > MAX_ZIP_ENTRIES:
                    raise SelectionError('Archive exceeds 100,000 entry metadata bound')
                names = (entry.filename for entry in files if not entry.is_dir())
                classes = []
                class_count = dex_count = 0
                has_android_manifest = False
                for name in names:
                    if name == 'AndroidManifest.xml':
                        has_android_manifest = True
                    if re.fullmatch(r'classes\d*\.dex', name):
                        dex_count += 1
                    if name.endswith('.class'):
                        class_count += 1
                        if len(classes) < limit:
                            classes.append(name)
                if dex_count and class_count:
                    result['kind'] = 'ambiguous'
                elif dex_count or has_android_manifest:
                    result['kind'] = 'apk'
                elif class_count:
                    result['kind'] = 'jar'
                result['archive'] = {'entry_count': len(files), 'class_count': class_count,
                                     'dex_count': dex_count, 'class_sample': sorted(classes),
                                     'sample_truncated': class_count > len(classes)}
        except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
            raise SelectionError(f'Invalid archive directory: {exc}') from exc
    elif head.startswith(b'dex\n'):
        result['kind'] = 'dex'
    elif head.startswith(b'\x7fELF'):
        result['kind'] = 'elf'
    elif head[:4] in (b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe',
                      b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe',
                      b'\xca\xfe\xba\xbe'):
        result['kind'] = 'macho'
    elif head.startswith(b'MZ'):
        if len(head) >= 64:
            offset = int.from_bytes(head[0x3c:0x40], 'little')
            if 0 <= offset <= min(size - 4, 1024 * 1024):
                with path.open('rb') as stream:
                    stream.seek(offset)
                    if stream.read(4) == b'PE\0\0':
                        result['kind'] = 'pe'
    expected = EXTENSIONS.get(path.suffix.lower())
    if expected and result['kind'] != expected:
        raise SelectionError(f'Extension {path.suffix} claims {expected}, but content is {result["kind"]}')
    return result


def declared(kind: str) -> dict:
    return {'kind': kind, 'basis': 'CALLER_DECLARED_UNVERIFIED', 'executed': False}


def _candidate(key: str, *, reason: str) -> dict:
    state, capability, source = TOOLS[key]
    return {'tool': key, 'integration': state, 'capability': capability,
            'source': source, 'reason': reason, 'installed_checked': False}


def _command(tool: str, input_path: str | None, class_name: str | None) -> list[str] | None:
    target = input_path or '<INPUT.jar>'
    if tool == 'archive-index':
        return ['python', 'selector.py', 'inspect', '--input', target]
    if tool in ('vineflower', 'cfr'):
        return ['python', 'toolkit.py', 'decompile', tool, target, '--run', '<UNIQUE_RUN_NAME>']
    if tool == 'javap':
        if not class_name and target.lower().endswith('.jar'):
            return None
        if target.lower().endswith('.class'):
            return ['javap', '-c', '-p', target]
        if class_name:
            return ['javap', '-c', '-p', '-classpath', target, class_name]
    if tool == 'rea':
        return ['python', 'toolkit.py', 'rea', '--', '--help']  # help only, not auto-native analysis
    return None


def choose(kind: str, goal: str = 'auto', *, signal: str = 'none',
           input_path: str | None = None, compared_kind: str | None = None,
           compared_path: str | None = None, class_name: str | None = None,
           has_source: bool = False, evidence: dict | None = None) -> dict:
    if goal not in GOALS or signal not in SIGNALS:
        raise SelectionError('Unknown goal or signal')
    if class_name and not CLASS_NAME.fullmatch(class_name):
        raise SelectionError('Class name must be a dotted JVM identifier, not shell syntax')
    if kind not in (*JAVA, *ANDROID, *NATIVE, 'unknown', 'ambiguous'):
        raise SelectionError('Unsupported or unverified input kind')
    goal_requested = goal
    if goal == 'auto':
        if signal == 'poor-decompile':
            goal = 'source'
        elif signal == 'encrypted-strings':
            goal = 'strings'
        elif signal == 'obfuscated-names':
            goal = 'mapping'
        elif signal == 'changed-versions':
            goal = 'versions'
        elif signal == 'invokedynamic':
            goal = 'bytecode'
        else:
            goal = ('structure' if kind == 'jar' else
                    'bytecode' if kind == 'class' else
                    'android' if kind in ANDROID else
                    'native' if kind in NATIVE else 'auto')

    result = {'schema_version': 1, 'requested_goal': goal_requested,
              'resolved_goal': goal, 'signal': signal, 'kind': kind,
              'decision': 'STOP', 'selected': None, 'alternatives': [],
              'next_if': [], 'limitations': [],
              'evidence': evidence or {'basis': 'CALLER_DECLARED_UNVERIFIED'},
              'policy': {'tools_probed': False, 'installed_checked': False,
                         'tools_executed': False, 'network_called': False,
                         'installed': False, 'original_modified': False}}
    if kind in {'unknown', 'ambiguous'}:
        result['limitations'].append('Unknown/ambiguous binary: inspect format before selecting an engine')
        return result
    if has_source and goal in ('source', 'structure') and signal == 'none':
        result.update(decision='NO_TOOL', limitations=['Prefer available authoritative source; inspect binary only on evidence of mismatch'])
        return result

    if goal in ('structure', 'source', 'bytecode', 'calls', 'strings', 'mapping', 'versions') and kind not in JAVA:
        result['limitations'].append('Requested JVM workflow is not compatible with this input type')
        return result
    if goal == 'android' and kind not in ANDROID:
        result['limitations'].append('JADX is for Android/DEX, not ordinary Java JARs')
        return result
    if goal == 'native' and kind not in NATIVE:
        result['limitations'].append('Do not route JVM/Android bytecode into native REA analysis by default')
        return result

    tool, why = None, ''
    if goal == 'structure':
        if kind == 'class':
            tool, why = 'javap', 'Single CLASS: inspect signatures using JDK bytecode tools'
        else:
            tool, why = 'archive-index', 'Names and entry counts are enough for the first pass; no Java runtime needed'
            result['alternatives'].append({'tool': 'classgraph', 'why_not': 'Only escalate for hierarchy/annotations/classpath semantics; JDK17 use v5'})
    elif goal == 'source':
        tool = 'cfr' if signal == 'poor-decompile' else 'vineflower'
        why = 'Alternative only because prior decompilation was reported unclear' if tool == 'cfr' else 'Reuse existing MOD-AI Vineflower path; one decompiler is sufficient initially'
        result['next_if'].append({'condition': 'selected decompilation is incomplete or misleading',
                                  'tool': 'vineflower' if tool == 'cfr' else 'cfr',
                                  'policy': 'explicit separate run, preserve original receipt'})
    elif goal in ('bytecode', 'strings'):
        tool, why = 'javap', 'Read-only JVM opcode/constant listing before heavier bytecode adapters'
        if kind == 'jar' and not class_name:
            result.update(decision='NEEDS_DETAIL', limitations=['Specify --class-name for JAR opcode listing; do not dump every class'])
            result['next_if'].append({'condition': 'Need class names first', 'tool': 'archive-index',
                                      'command': _command('archive-index', input_path, None)})
            return result
        if goal == 'strings':
            result['alternatives'].append({'tool': 'threadtear', 'why_not': 'Some decryptors execute untrusted target code; require separate sandbox and approval'})
        else:
            result['next_if'].append({'condition': 'Opcode listing cannot resolve invokedynamic/control-flow',
                                      'tool': 'asm', 'policy': 'design/pin separate static adapter first'})
    elif goal == 'calls':
        tool, why = 'sootup', 'Call graph/data-flow require structured IR, not merely decompiled text'
        result['alternatives'].append({'tool': 'asm', 'why_not': 'Lower-level visitor; use only for narrowly scoped custom static passes'})
    elif goal == 'mapping':
        tool, why = 'enigma', 'Store human-reviewed obfuscated -> research names with source evidence'
        result['next_if'].append({'condition': 'Need to read/convert existing mapping file',
                                  'tool': 'mapping-io', 'policy': 'requires validated mapping input'})
        result['next_if'].append({'condition': 'Need to apply verified mappings to JAR',
                                  'tool': 'tiny-remapper', 'policy': 'explicit copy-only transformation'})
    elif goal == 'versions':
        if kind != 'jar' or compared_kind != 'jar' or not compared_path:
            result.update(decision='NEEDS_DETAIL', limitations=['Provide two verified Java JARs with --compare-to; Matcher does not infer identity from one JAR'])
            return result
        tool, why = 'matcher', 'Match two versions based on static similarity; preserve uncertain correspondences'
    elif goal == 'android':
        tool, why = 'jadx', 'Android DEX/APK source investigation should start in an Android-specific engine'
        result['alternatives'].append({'tool': 'rea', 'why_not': 'Native/provider analysis only for evidence it is needed; no implicit Ghidra/JADX setup'})
    elif goal == 'native':
        tool, why = 'rea', 'Native target: explicit REA CLI may coordinate an separately approved provider'
        result['limitations'].append('REA CLI present does not imply Ghidra/IDA/Hopper provider is installed; --help is not analysis')
    else:
        result['limitations'].append('No justified tool selection: supply a specific investigation goal')
        return result

    selected = _candidate(tool, reason=why)
    selected['suggested_argv'] = _command(tool, input_path, class_name)
    result['selected'] = selected
    result['decision'] = ('ADVISORY_ONLY' if selected['integration'] in ('ADVISORY_NOT_WIRED', 'RISK_REQUIRES_ISOLATION')
                          else 'READY_FOR_EXPLICIT_INVOCATION')
    if tool == 'archive-index':
        result['limitations'].append('ZIP names/counts are not bytecode semantics, call edges, or recovered source')
    if tool == 'javap':
        result['limitations'].append('JDK executable is not probed; command is advisory and must be invoked separately')
    if selected['integration'] == 'ADVISORY_NOT_WIRED':
        result['limitations'].append('No adapter/download/version pin exists in TECH HUB; never claim this recommendation is runnable')
    if tool in ('vineflower', 'cfr', 'rea'):
        result['limitations'].append('Suggested commands are NOT run; missing tools must be explicitly installed separately')
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    plan = sub.add_parser('choose', help='Emit explainable plan, never install/run/check any tool')
    plan.add_argument('--input', type=Path)
    plan.add_argument('--kind', choices=sorted((*JAVA, *ANDROID, *NATIVE, 'unknown')))
    plan.add_argument('--goal', choices=GOALS, default='auto')
    plan.add_argument('--signal', choices=SIGNALS, default='none')
    plan.add_argument('--compare-to', type=Path)
    plan.add_argument('--class-name')
    plan.add_argument('--has-source', action='store_true')
    scan = sub.add_parser('inspect', help='Print bounded Java archive names/magic; no decompression or execution')
    scan.add_argument('--input', type=Path, required=True)
    scan.add_argument('--limit', type=int, default=MAX_PREVIEW_CLASSES)
    sub.add_parser('capabilities', help='Static advisory catalogue only')
    args = parser.parse_args(argv)
    try:
        if args.command == 'capabilities':
            output = {key: {'integration': val[0], 'capability': val[1], 'source': val[2]}
                      for key, val in sorted(TOOLS.items())}
        elif args.command == 'inspect':
            output = inspect(args.input, limit=args.limit)
        else:
            if bool(args.input) == bool(args.kind):
                raise SelectionError('Provide exactly one of --input (verified) or --kind (declared)')
            if args.compare_to and not args.input:
                raise SelectionError('--compare-to requires a verified --input')
            meta = inspect(args.input) if args.input else declared(args.kind)
            other = inspect(args.compare_to) if args.compare_to else None
            output = choose(meta['kind'], args.goal, signal=args.signal,
                            input_path=str(args.input.absolute()) if args.input else None,
                            compared_kind=other['kind'] if other else None,
                            compared_path=str(args.compare_to.absolute()) if other else None,
                            class_name=args.class_name, has_source=args.has_source,
                            evidence={'input': meta, **({'comparison': other} if other else {})})
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (SelectionError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'SELECTION_ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
