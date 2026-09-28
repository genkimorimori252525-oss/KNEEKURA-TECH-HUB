"""Read-only Forge workspace discovery and import of explicit Gradle resolution.

Discovery is never a substitute for dependency resolution. The companion init
script runs only on an explicit, trusted Gradle invocation; this module merely
checks its export against current inputs before handing it to capture_profile.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path

from .storage import ContractError, IntegrityError, canonical, digest, key_for, valid_hash, NAMESPACES

EXPORT_FORMAT = 'kneekura.forge-inputs.v1'
_IGNORED = {'.git', '.gradle', '.kneekura-cache', '.kneekura-runs', '.superpowers', '.idea', 'build',
            'out', 'run', 'runs', 'saves', 'node_modules', '__pycache__'}
_CONFIG_NAMES = {'gradle.properties', 'gradlew', 'gradlew.bat', 'gradle.lockfile',
                 'gradle-wrapper.properties', 'gradle-wrapper.jar', 'libs.versions.toml'}


def _workspace(path: Path | str) -> Path:
    original = Path(path)
    if original.is_symlink() or not original.is_dir():
        raise ContractError('Registered workspace must be an existing nonsymlink directory')
    return original.resolve()


def _inputs(root: Path, *, config_only: bool = False) -> list[Path]:
    files = []
    def onerror(exc):
        raise ContractError(f'Cannot fingerprint workspace: {exc}')
    for directory, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        for name in dirs[:]:
            path = Path(directory) / name
            if name in _IGNORED:
                dirs.remove(name)
            elif path.is_symlink():
                raise ContractError('Symlink workspace input is not fingerprintable')
        for name in names:
            p = Path(directory) / name
            rel = p.relative_to(root).as_posix()
            config = (name in _CONFIG_NAMES or name.endswith(('.gradle', '.gradle.kts'))
                      or rel.startswith(('buildSrc/', 'build-logic/')))
            if config or (not config_only and (rel.startswith('src/') or '/src/' in rel)):
                if p.is_symlink():
                    raise ContractError('Symlink workspace input is not fingerprintable')
                files.append(p)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def file_hash(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def _fingerprint(root: Path, config_only: bool) -> str:
    # This wire format is also implemented by the Gradle init script. It does not
    # depend on JSON serializer ordering, platform separators or mtimes.
    h = hashlib.sha256()
    for path in _inputs(root, config_only=config_only):
        h.update(path.relative_to(root).as_posix().encode('utf-8'))
        h.update(b'\x00'); h.update(file_hash(path).encode('ascii')); h.update(b'\n')
    return h.hexdigest()


def workspace_fingerprint(root: Path | str) -> str:
    return _fingerprint(_workspace(root), False)


def configuration_fingerprint(root: Path | str) -> str:
    return _fingerprint(_workspace(root), True)


def _properties(path: Path) -> dict[str, str]:
    if not path.is_file(): return {}
    result = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith(('#', '!')) and '=' in line:
            k, v = line.split('=', 1); result[k.strip()] = v.strip()
    return result


def _revision(root: Path) -> str | None:
    if not shutil.which('git'): return None
    try:
        env = {k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
        r = subprocess.run(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'],
                           stdin=subprocess.DEVNULL, capture_output=True, timeout=5, env=env)
        rev = r.stdout.decode('ascii', errors='replace').strip()
        return rev if r.returncode == 0 and re.fullmatch('[a-f0-9]{40,64}', rev) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _root(id: str, path: Path, role: str, *, scope='runtime', namespace='mojmap',
          stage='workspace', track='ANCHOR') -> dict:
    return {'id':id, 'path':str(path), 'kind':('directory' if path.is_dir() else
            'jar' if path.suffix.lower() in {'.jar','.zip'} else 'file'),
            'scope':scope, 'role':role, 'namespace':namespace, 'stage':stage,
            'classloader':'unknown', 'track':track}


def discover_workspace(root: Path | str, *, track: str = 'ANCHOR',
                       physical_side: str = 'server') -> dict:
    """Return declared inputs only. No Gradle evaluation or network access."""
    root = _workspace(root)
    if track not in {'ANCHOR','FRONTIER','COMPARATIVE'}:
        raise ContractError('Unknown research track')
    if physical_side not in {'client','server'}: raise ContractError('Explicit physical side required')
    props = _properties(root/'gradle.properties')
    build = '\n'.join(p.read_text(encoding='utf-8') for p in (root/'build.gradle',root/'build.gradle.kts') if p.is_file())
    java = re.search(r'JavaLanguageVersion\.of\(\s*(\d+)\s*\)', build)
    minecraft = props.get('minecraft_version') or props.get('versionMc')
    forge = props.get('forge_version') or props.get('versionForge')
    literal = re.search(r'net\.minecraftforge:forge:([0-9.]+)-([0-9.]+)', build)
    if literal:
        minecraft = minecraft or literal[1]; forge = forge or literal[2]
    roots = []
    for role, relative in [('source','src/main/java'), ('source','src/main/kotlin'),
                           ('resources','src/main/resources'), ('source','build/generated/sources'),
                           ('binary','build/classes/java/main'), ('resources','build/resources/main')]:
        path = root/relative
        if path.exists():
            roots.append(_root(f'workspace:{relative}', path, role, track=track,
                               stage='compiled' if relative.startswith('build/') else 'workspace'))
    for p in _inputs(root, config_only=True):
        roots.append(_root('configuration:'+p.relative_to(root).as_posix(), p,
                           'configuration', scope='buildscript', namespace='unknown', track=track))
    source = workspace_fingerprint(root)
    return {'schema_version':1, 'minecraft':minecraft, 'loader':'forge', 'loader_version':forge,
            'java_major':int(java[1]) if java else None, 'namespace':'mojmap',
            'namespace_aliases':{'official':'mojmap','named':'mojmap'}, 'track':track,
            'physical_side':physical_side, 'logical_side':'server', 'workspace':str(root),
            'workspace_revision':_revision(root), 'dirty_hash':source,
            'source_generation':source, 'configuration_fingerprint':configuration_fingerprint(root),
            'toolchain':None, 'roots':roots, 'dependency_resolution':'UNKNOWN',
            'unresolved_dependencies':[{'scope':'runtime','reason':'No Gradle resolved-input export supplied'}],
            'binary_generation':{'status':'UNVERIFIED','reason':'No build receipt ties classes to these sources'}}


def _local(root: Path, value: str) -> Path:
    if not isinstance(value, str) or not value: raise ContractError('Missing workspace path')
    path = Path(value)
    if not path.is_absolute(): path = root/path
    if not path.resolve().is_relative_to(root) or path.is_symlink():
        raise ContractError('Exported project input escapes workspace')
    return path


def import_resolved(export: dict, root: Path | str, *, track: str = 'ANCHOR',
                    physical_side: str = 'server') -> dict:
    """Validate actual Gradle export; reading it never reruns a build."""
    root = _workspace(root)
    if not isinstance(export, dict) or export.get('format') != EXPORT_FORMAT or type(export.get('schema_version')) is not int or export['schema_version'] != 1:
        raise ContractError('Unsupported Gradle resolved-input export')
    if Path(export.get('workspace','')).resolve() != root:
        raise ContractError('Gradle export belongs to a different workspace')
    if export.get('configuration_fingerprint') != configuration_fingerprint(root):
        raise IntegrityError('Gradle export configuration is stale; explicitly export again')
    valid_hash(export.get('source_fingerprint'))
    if track == 'ANCHOR' and (export.get('minecraft') != '1.20.1' or export.get('loader') != 'forge'):
        raise ContractError('ANCHOR requires actual Forge 1.20.1 inputs')
    for field in ('minecraft','loader_version'):
        if not isinstance(export.get(field),str) or not re.fullmatch(r'\d+(?:\.\d+)+', export[field]):
            raise ContractError(f'Exact resolved {field} required')
    if export.get('namespace') not in NAMESPACES - {'unknown'}:
        raise ContractError('Resolved development namespace required; Parchment is annotation only')
    base = discover_workspace(root, track=track, physical_side=physical_side)
    roots = [r for r in base['roots'] if r['role'] == 'configuration']
    for field,role,stage in [('source_roots','source','workspace'),('resource_roots','resources','workspace'),
                             ('output_roots','binary','compiled')]:
        paths = export.get(field,[])
        if not isinstance(paths,list): raise ContractError('Exported roots must be lists')
        for i, rel in enumerate(paths):
            path = _local(root, rel)
            # Absent output directories are retained in coverage, not manufactured.
            item = _root(f'{field}:{i}', path, role, namespace=export['namespace'],stage=stage,track=track)
            if not path.exists(): item['kind'] = 'directory'
            roots.append(item)
    artifacts = export.get('artifacts')
    unresolved = export.get('unresolved')
    if not isinstance(artifacts,list) or not isinstance(unresolved,list):
        raise ContractError('Explicit artifacts and unresolved dependency arrays required')
    for i,a in enumerate(artifacts):
        if not isinstance(a,dict): raise ContractError('Malformed resolved artifact')
        path = Path(a.get('path',''))
        if not path.is_absolute() or path.is_symlink(): raise ContractError('Artifact must be an absolute nonsymlink path')
        expected = valid_hash(a.get('sha256'))
        if path.exists() and (not path.is_file() or file_hash(path) != expected):
            raise IntegrityError(f'Resolved artifact changed: {a.get("coordinate", path.name)}')
        namespace = a.get('namespace','unknown')
        if namespace not in NAMESPACES: raise ContractError('Unknown artifact namespace')
        scope = a.get('scope')
        if scope not in {'compile','runtime','client','server','buildscript'}:
            raise ContractError('Unknown artifact scope')
        item = _root(f'dependency:{i}', path, 'source' if a.get('classifier') == 'sources' else 'dependency',
                     scope=scope, namespace=namespace, stage=a.get('stage','resolved_userdev'),track=track)
        item.update(coordinate=a.get('coordinate'), resolved_sha256=expected)
        roots.append(item)
    base.update({k:export.get(k) for k in ('minecraft','loader','loader_version','namespace','java_major',
                                          'toolchain','gradle_version','forgegradle_version','mappings')})
    base.update(roots=roots, dependency_resolution='GRADLE_RESOLVED_NOT_LAUNCHED',
                resolution_export_hash=key_for(export), unresolved_dependencies=unresolved,
                export_source_generation=export['source_fingerprint'])
    if export['source_fingerprint'] != base['source_generation']:
        base['binary_generation']['reason'] = 'Workspace sources changed after export; classes are not current evidence'
    return base


def export_plan(root: Path | str, registry: dict, output: Path | str) -> dict:
    root = _workspace(root)
    if registry.get('allow_gradle') is not True or Path(registry.get('workspace','')).resolve() != root:
        raise ContractError('Explicitly registered trusted workspace and allow_gradle=true required')
    script = Path(__file__).with_name('resources')/'kneekura-inputs.init.gradle'
    wrapper = root/('gradlew.bat' if os.name == 'nt' else 'gradlew')
    return {'schema_version':1, 'status':'OK', 'outcome':'NOT_RUN', 'kind':'prepare',
            'workspace':str(root), 'argv':[str(wrapper),'--no-daemon','--console=plain','-I',str(script),
             'kneekuraExportInputs', '-PkneekuraNamespace=mojmap', '-PkneekuraExport='+str(Path(output).resolve())],
            'delegated_to':'registered_existing_runner', 'effects':['Gradle configuration and dependency resolution'],
            'note':'Not executed. Review the trusted workspace and run explicitly.'}
