"""Explicit virtual Unix CONFIGDIR receiver, never Forge setup or filesystem I/O.

Only absolute, normalized printable-ASCII paths are admitted. The synthetic
base is supplied by the caller; `config` comes from pinned FMLPaths.<clinit>.
Populated absolutePath says nothing about the subsequent directory operations.
No native instruction address participates in dispatch. UTF borrows are private
copies, tracked independently of immutable object identities and JNI handles.
"""
import copy
import json
from dataclasses import asdict, dataclass
from native_forge_runtime_fixture_ysm_265 import ForgeRuntimeCPU, FML_SHA

FML_PATHS = 'net/minecraftforge/fml/loading/FMLPaths'
PATH = 'java/nio/file/Path'
STRING = 'java/lang/String'
PROVIDER = 'virtual-unix-ascii-v1'
JAVA_SHA = 'f8d258a856a691c81ad9dd16964635bbc8a8fdd7f40edec37dcf3d904feb7ae1'
PINS = {
    FML_PATHS: (FML_SHA, 'c8fc0d33845a5aa3c285115f320cf23dc016fe0cdab183dd2cd3e8d8257675c5'),
    PATH: (JAVA_SHA, 'a742da0be8612380a06ebd1b770f2554567fd0cf34e90398b5fc5797604c5e66'),
    'sun/nio/fs/UnixPath': (JAVA_SHA, '4e57d0fa4fb8c02f66fba4fba40accf34a8f4fc3ea2139b8ccf9fddd8144a3bf'),
    'sun/nio/fs/UnixFileSystem': (JAVA_SHA, 'eb767a22dd28cb33aa66ed503015b4cc686ed5d65463dde61885f2875507fb8a')}
REF_BASE = 0x7f0000000000
MAX_REFS = 1024
MAX_CALLS = 4096
# JNI slots whose RSI parameter is an object/class reference. Unused registers
# are not arguments: ExceptionCheck/Clear, GetVersion, etc. must pass through,
# even when the ABI leaves a live or deleted path handle in RSI.
REFERENCE_RSI_SLOTS = frozenset(
    range(7, 15)) | frozenset(range(20, 26)) | frozenset(range(27, 163)) | frozenset(
    range(164, 167)) | frozenset(range(168, 172)) | frozenset((173, 174)) | frozenset(
    range(183, 219)) | frozenset(range(220, 228)) | frozenset(range(230, 234))


def require(condition, message):
    if not condition: raise ValueError(message)


def configuration(state, game_path, provider):
    require(type(state) is str and state in ('class-initialized-only', 'absolute-field-populated'), 'Unsupported FMLPaths state')
    require(provider == PROVIDER and type(provider) is str, 'Unsupported virtual provider')
    if state == 'class-initialized-only':
        require(game_path is None, 'Null absolutePath state cannot take a game path')
        config_path = None
    else:
        require(type(game_path) is str and 1 <= len(game_path) <= 2048 and game_path.startswith('/') and
                all(32 <= ord(c) <= 126 for c in game_path), 'Require bounded absolute ASCII virtual game path')
        require(game_path == '/' or all(c and c not in ('.', '..') for c in game_path[1:].split('/')),
                'Require already normalized virtual path')
        config_path = game_path.rstrip('/') + '/config'
    return {'state': state, 'game_path': game_path, 'provider': provider, 'config_path': config_path,
            'synthetic_declared_state': True, 'filesystem_operations_executed': False,
            'forge_setup_success_claimed': False,
            'provenance': {k: {'artifact_sha256': v[0], 'class_sha256': v[1]} for k, v in PINS.items()}}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


@dataclass(frozen=True)
class PathDeclaration:
    # Independent original input anchor. It is never reconstructed from mutable
    # live config/object records after configuration has been established.
    config_json: str


@dataclass(frozen=True)
class ObjectIdentity:
    identity: str
    java_type: str
    value: str
    provider: str


def objects(config):
    result = [ObjectIdentity('configdir-enum', FML_PATHS, 'CONFIGDIR', '')]
    if config['config_path'] is not None:
        result += [ObjectIdentity('config-path', PATH, config['config_path'], PROVIDER),
                   ObjectIdentity('config-string', STRING, config['config_path'], '')]
    return {x.identity: asdict(x) for x in result}


def initial(config, extension):
    return {'config': copy.deepcopy(config), 'declaration': canonical(config), 'legacy_extension': extension,
            'objects': objects(config), 'refs': {}, 'borrows': {}, 'calls': []}


def member(jni, handle, collection, owner, name, descriptor, static):
    require(type(handle) is int, 'Invalid member handle')
    item = jni[collection].get(str(handle))
    require(type(item) is dict and item.get('requested_class') == owner and item.get('declaring_class') == owner and
            item.get('name') == name and item.get('descriptor') == descriptor and item.get('static') is static,
            'Unsupported exact member contract')
    archive, digest = PINS[owner]
    source = item.get('source', {})
    require(item.get('class_sha256') == digest and source.get('sha256') == archive and
            jni['class_proofs'].get(owner) == {'sha256': digest, 'source': source} and
            jni['java_sources'].get(source.get('id')) == {k: v for k, v in source.items() if k != 'id'},
            'Path member provenance mismatch')
    return item


def live(t, handle, kind=None):
    require(type(handle) is int, 'Invalid reference type')
    ref = t['refs'].get(str(handle))
    require(ref is not None and ref['active'], 'Unknown or deleted path reference')
    # Checkpoint dictionaries are serialized snapshots; receiver values themselves
    # are frozen typed identities, never mutable JNI handle records.
    obj = ObjectIdentity(**t['objects'][ref['identity']])
    require(kind is None or obj.java_type == kind, 'Wrong receiver type')
    return ref, obj


def new_ref(t, identity, scope='local'):
    require(len(t['refs']) < MAX_REFS, 'Path reference budget')
    handle = REF_BASE + 16 * len(t['refs'])
    t['refs'][str(handle)] = {'identity': identity, 'scope': scope, 'active': True}
    return handle


def transition(t, jni, index, a, b, *, pointer=None, replay=False):
    """Pure bounded JNI state transition, shared by execution and checkpoint replay."""
    require(all(type(x) is int for x in (index, a, b)), 'Invalid JNI path argument')
    if index == 145:
        require(jni['classes'].get(str(a)) == FML_PATHS and (replay or a not in jni['deleted_local_refs']),
                'Invalid CONFIGDIR jclass')
        member(jni, b, 'fields', FML_PATHS, 'CONFIGDIR', 'L'+FML_PATHS+';', True)
        return new_ref(t, 'configdir-enum')
    if index == 95:
        live(t, a, FML_PATHS)
        member(jni, b, 'fields', FML_PATHS, 'absolutePath', 'L'+PATH+';', False)
        return 0 if t['config']['config_path'] is None else new_ref(t, 'config-path')
    if index in (34, 35, 36):
        ref, _ = live(t, a, PATH)
        item = jni['methods'].get(str(b), {})
        name = item.get('name')
        require(name in ('normalize', 'toString'), 'Unsupported Path method')
        member(jni, b, 'methods', PATH, name, '()L'+(PATH if name == 'normalize' else STRING)+';', False)
        return new_ref(t, ref['identity'] if name == 'normalize' else 'config-string')
    if index in (21, 25):
        if a == 0: return 0
        ref, _ = live(t, a)
        return new_ref(t, ref['identity'], 'global' if index == 21 else 'local')
    if index in (22, 23):
        if a:
            ref, _ = live(t, a)
            require(ref['scope'] == ('global' if index == 22 else 'local'), 'Wrong reference deletion scope')
            ref['active'] = False
        return 0  # JNI void return register is unspecified.
    if index == 24:
        left = live(t, a)[0]['identity'] if a else None
        right = live(t, b)[0]['identity'] if b else None
        return int(left == right)
    if index in (168, 169, 170):
        ref, obj = live(t, a, STRING)
        data = obj.value.encode('ascii')  # Domain excludes NUL; these are exact modified-UTF8 bytes.
        if index == 168: return len(data)
        if index == 169:
            require(type(pointer) is int and pointer > 0 and str(pointer) not in t['borrows'], 'Invalid UTF borrow pointer')
            t['borrows'][str(pointer)] = {'identity': ref['identity'], 'active': True, 'length': len(data)}
            return pointer
        borrow = t['borrows'].get(str(b))
        require(borrow is not None and borrow['active'] and borrow['identity'] == ref['identity'], 'Invalid UTF release')
        borrow['active'] = False
        return 0
    raise ValueError('Unsupported path operation')


class ForgePathCPU(ForgeRuntimeCPU):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.forge_paths = None
        self._path_declaration = None
        self._legacy_path_restore = False

    def verify_path_metadata(self):
        require(self.java_metadata is not None and self.jni_state is not None, 'Path metadata required')
        for name, (archive, digest) in PINS.items():
            info = self.java_metadata.class_info(name)
            require(info is not None and info['class_sha256'] == digest and info['source']['sha256'] == archive and
                    self.jni_state['java_sources'].get(info['source']['id']) ==
                    {k: v for k, v in info['source'].items() if k != 'id'}, 'Path metadata provenance mismatch')
        if self.forge_paths is not None:
            require(self._path_declaration is not None and
                    self.forge_paths.get('declaration') == self._path_declaration.config_json and
                    canonical(self.forge_paths['config']) == self._path_declaration.config_json and
                    self.forge_paths['objects'] == objects(self.forge_paths['config']),
                    'Changed original path declaration or objects')
            require(self.forge_paths['config'] == configuration(self.forge_paths['config'].get('state'),
                    self.forge_paths['config'].get('game_path'), self.forge_paths['config'].get('provider')), 'Changed path config')

    def configure_forge_paths(self, state, *, game_path=None, provider, allow_legacy_extension=False):
        config = configuration(state, game_path, provider)
        self.verify_path_metadata()
        if self.forge_paths is not None:
            require(self.forge_paths['config'] == config, 'FMLPaths state cannot change after declaration')
            return
        require(self._path_declaration is None, 'Previously declared path state cannot be replaced')
        require(not self._legacy_path_restore or allow_legacy_extension is True,
                'Legacy pre-path checkpoint requires explicit path extension')
        self._path_declaration = PathDeclaration(canonical(config))
        self.forge_paths = initial(config, self._legacy_path_restore)
        self.emit('DECLARED_VIRTUAL_FMLPATHS', state, f'provider={provider}', f'legacy_extension={self._legacy_path_restore}',
                  'synthetic_input=true', 'filesystem_operations_executed=false', 'forge_setup_success_claimed=false')

    def configure_java_metadata(self, *args, **kwargs):
        super().configure_java_metadata(*args, **kwargs)
        if self.forge_paths is not None: self.verify_path_metadata()

    def model(self, kind):
        # The inherited one-byte REP-copy model can propagate ordinary unknown
        # bytes as opaque values. A released lease is invalid, not merely unknown.
        if kind == 'copy' and self.reg('RCX'):
            self.demand(self.released_borrow_hit(self.reg('RSI'), 1) is None,
                        'RELEASED_UTF_BORROW_READ', self.reg('RSI'), 1)
        entry = self.jni_gateways.get(self.pc) if kind == 'jni-import' else None
        if self.forge_paths is None or entry is None or entry[0] != 'env': return super().model(kind)
        _, index, name = entry
        a, b = self.reg('RSI'), self.reg('RDX')
        refs = self.forge_paths['refs']
        own = ((index in REFERENCE_RSI_SLOTS and str(a) in refs) or
               (index == 24 and str(b) in refs) or
               (index in (21, 22, 23, 24, 25) and a == 0 and (index != 24 or b == 0)))
        field = self.jni_state['fields'].get(str(b), {})
        path_static = index == 145 and (self.jni_state['classes'].get(str(a)) == FML_PATHS or field.get('requested_class') == FML_PATHS)
        if not own and not path_static: return super().model(kind)
        self.demand(index in (21, 22, 23, 24, 25, 34, 35, 36, 95, 145, 168, 169, 170), 'UNMODELED_PATH_JNI_CALL', index)
        sp, target = self.frame(False)
        self.validate_interface('env', self.reg('RDI'))
        self.demand(self.jni_state['pending_exception'] is None or index in (22, 23, 170), 'JNI_CALL_WITH_PENDING_EXCEPTION', index)
        self.demand(len(self.forge_paths['calls']) + len(self.jni_state['calls']) +
                    len((self.forge_runtime or {}).get('calls', [])) < MAX_CALLS, 'PATH_CALL_BUDGET')
        candidate = copy.deepcopy(self.forge_paths)
        try:
            self.verify_path_metadata()
            self.validate_path_state(self.forge_paths, self.jni_state)
            # Validate the operation before reserving memory or mutating any ledger.
            pointer = 1 if index == 169 else None
            if index == 169:
                _, obj = live(candidate, a, STRING)
                data = obj.value.encode('ascii') + b'\0'
                if b: require(self.private_allowed(b, 1), 'Invalid isCopy output pointer')
            transition(candidate, self.jni_state, index, a, b, pointer=pointer)
            candidate = copy.deepcopy(self.forge_paths)
            if index == 169:
                pointer = self.reserve_fixture(len(data))
                self.write_private(pointer, data)
                self.private_readonly.append([pointer, pointer + len(data)])
                if b: self.write_private(b, b'\1')
            result = transition(candidate, self.jni_state, index, a, b, pointer=pointer)
        except ValueError:
            self.demand(False, 'INVALID_VIRTUAL_PATH_OPERATION', index)
        candidate['calls'].append([index, a, b, result])
        self.forge_paths = candidate
        self.reg('RAX', result); self.reg('RSP', sp+8); self.reg('RIP', target)
        self.emit('DECLARED_VIRTUAL_PATH_CALL', name, f'result={result:x}', 'filesystem_operations_executed=false')

    def released_borrow_hit(self, address, size):
        if size <= 0: return None
        for key, borrow in (getattr(self, 'forge_paths', None) or {}).get('borrows', {}).items():
            ptr = int(key)
            if not borrow['active'] and address < ptr+borrow['length']+1 and ptr < address+size:
                return max(address, ptr)
        return None

    def unknown(self, address, size):
        # Released copies remain reserved, but must never be consumed again.
        hit = self.released_borrow_hit(address, size)
        return hit if hit is not None else super().unknown(address, size)

    def read_known(self, address, size):
        self.demand(self.released_borrow_hit(address, size) is None,
                    'RELEASED_UTF_BORROW_READ', address, size)
        return super().read_known(address, size)

    def validate_path_state(self, t, jni, *, memory=True):
        if t is None:
            require(self._path_declaration is None, 'Previously declared path state is missing')
            return
        require(type(t) is dict and set(t) == {'config', 'declaration', 'legacy_extension', 'objects', 'refs', 'borrows', 'calls'} and
                type(t['config']) is dict and type(t['legacy_extension']) is bool and type(t['calls']) is list and
                len(t['calls']) <= MAX_CALLS and jni is not None, 'Invalid path checkpoint schema')
        config = configuration(t['config'].get('state'), t['config'].get('game_path'), t['config'].get('provider'))
        require(t['config'] == config and type(t['declaration']) is str and
                t['declaration'] == canonical(config), 'Invalid path checkpoint declaration/configuration')
        require(self._path_declaration is None or t['declaration'] == self._path_declaration.config_json,
                'Changed original path declaration')
        require(type(t['refs']) is dict and type(t['borrows']) is dict and type(t['objects']) is dict,
                'Invalid path object/reference schema')
        require(len(t['calls']) + len(jni['calls']) <= MAX_CALLS, 'Invalid path checkpoint budget')
        for archive, _ in PINS.values():
            require(any(source.get('sha256') == archive for source in (jni['java_sources'] or {}).values()), 'Missing pinned path source')
        replay = initial(config, t['legacy_extension'])
        for call in t['calls']:
            require(type(call) is list and len(call) == 4 and all(type(x) is int for x in call), 'Invalid path call ledger')
            index, a, b, expected = call
            result = transition(replay, jni, index, a, b, pointer=expected if index == 169 else None, replay=True)
            require(result == expected, 'Invalid path call result')
            replay['calls'].append(call)
        # JSON booleans and numbers must not compare equal across distinct schema types.
        require(canonical(replay) == canonical(t), 'Invalid path reference/borrow replay')
        if memory:
            for key, borrow in t['borrows'].items():
                ptr = int(key)
                data = t['objects'][borrow['identity']]['value'].encode('ascii') + b'\0'
                require(any(a == ptr and n == len(data) for a, n in self.fixture_regions) and
                        [ptr, ptr+len(data)] in self.private_readonly and super().unknown(ptr, len(data)) is None and
                        bytes(self.uc.mem_read(ptr, len(data))) == data, 'Invalid UTF borrow storage')

    def capture_sparse(self):
        self.validate_path_state(self.forge_paths, self.jni_state)
        if self.forge_paths is not None: self.verify_path_metadata()
        result = super().capture_sparse()
        result['forge_paths'] = copy.deepcopy(self.forge_paths)
        return result

    def restore_sparse(self, state):
        t = copy.deepcopy(state.get('forge_paths'))
        self.validate_path_state(t, state.get('jni'))
        if self._path_declaration is not None:
            require(t is not None and self._path_declaration.config_json == t['declaration'],
                    'Changed FMLPaths declaration on restore')
        super().restore_sparse(state)
        self.forge_paths = t
        if t is not None and self._path_declaration is None:
            self._path_declaration = PathDeclaration(t['declaration'])
        self._legacy_path_restore = t is None
