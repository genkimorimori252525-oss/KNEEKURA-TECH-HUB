"""Declared Forge release-launch values, never real class initialization.

Pinned Forge 1.20.1-47.4.0 FMLEnvironment computes production from its launch
handler or presence of the production system-property key. Release client/server
handlers both declare production=true. This explicit initialized-state scenario
is synthetic input, not evidence about an installed JVM. Enum locals are typed
side-table references, never jclass aliases. All other object operations stop.
"""
import copy
from native_jni_fixture_ysm_265 import JniGuardedCPU

ENV = 'net/minecraftforge/fml/loading/FMLEnvironment'
DIST = 'net/minecraftforge/api/distmarker/Dist'
DESC = 'L'+DIST+';'
FML_SHA = 'd17c218af5c62fa4928019614aa8a5075279f8545efe21325baf46b80f4a5ac9'
DIST_SHA = '39d9a3d9277c1402b8e7b97f917ce278241cf1796312aec85b87f19a376dd99a'
PINS = {
    ENV: (FML_SHA, '2f2fb82b18a0c15be7200cef816f49a9e31ae9f89d6a2b1a1c3f84cf5bc03a75'),
    DIST: (DIST_SHA, '232942ceea0aefeb8ab48436f914847a1acc0222af1a39fabc2d6a57f1ac36e4'),
    'net/minecraftforge/fml/loading/targets/CommonClientLaunchHandler':
        (FML_SHA, '5c0f65787747a5080936560a333a5ad689b3b8fa9e4b09c1bc5e63ef3c85a2b8'),
    'net/minecraftforge/fml/loading/targets/CommonServerLaunchHandler':
        (FML_SHA, 'd1eae8da34de37ad8ca7a87e489a8fbed510f72bcd1f2acb0b4366895da06522')}
PROFILES = {'forgeclient': 'CLIENT', 'forgeserver': 'DEDICATED_SERVER'}
REF_BASE = 0x7e0000000000
MAX_REFS = 1024
MAX_CALLS = 4096


def configuration(profile, initialized, property_present):
    if type(profile) is not str or profile not in PROFILES or initialized is not True or type(property_present) is not bool:
        raise ValueError('Unsupported declared Forge runtime configuration')
    return {'profile': profile, 'initialized': True, 'production_property_present': property_present,
            'production': True, 'dist': PROFILES[profile], 'synthetic_declared_state': True,
            'class_initialization_executed': False,
            'provenance': {k: {'artifact_sha256': v[0], 'class_sha256': v[1]} for k, v in PINS.items()}}


class ForgeRuntimeCPU(JniGuardedCPU):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.forge_runtime = None

    def verify_forge_metadata(self):
        if self.java_metadata is None or self.jni_state is None:
            raise ValueError('Forge runtime requires pinned Java metadata')
        for name, (archive, digest) in PINS.items():
            info = self.java_metadata.class_info(name)
            if (info is None or info['class_sha256'] != digest or
                    info['source']['sha256'] != archive or
                    self.jni_state['java_sources'].get(info['source']['id']) !=
                    {k: v for k, v in info['source'].items() if k != 'id'}):
                raise ValueError('Forge runtime artifact provenance mismatch')

    def configure_forge_runtime(self, profile, *, initialized, production_property_present):
        config = configuration(profile, initialized, production_property_present)
        self.verify_forge_metadata()
        if self.forge_runtime is not None:
            if self.forge_runtime['config'] != config:
                raise ValueError('Forge runtime configuration cannot change')
            return
        self.forge_runtime = {'config': config, 'refs': {}, 'calls': []}
        self.emit('DECLARED_FORGE_RUNTIME', f'profile={profile}', 'initialized_assumed=true',
                  f'production_property_present={production_property_present}',
                  'production=true', f'dist={PROFILES[profile]}',
                  'synthetic_input=true', 'host_java_execution=false')

    def configure_java_metadata(self, *args, **kwargs):
        super().configure_java_metadata(*args, **kwargs)
        if self.forge_runtime is not None:
            self.verify_forge_metadata()

    def field_value(self, state, cls, field, index, alive=True):
        if (type(cls) is not int or type(field) is not int or
                str(cls) not in state['classes'] or (alive and cls in state['deleted_local_refs'])):
            raise ValueError('Invalid Forge jclass')
        item = state['fields'].get(str(field))
        owner = state['classes'][str(cls)]
        if (type(item) is not dict or item.get('static') is not True or
                item.get('requested_class') != owner or item.get('declaring_class') != owner or
                owner not in (ENV, DIST)):
            raise ValueError('Invalid Forge static field proof')
        archive, digest = PINS[owner]
        source = item.get('source', {})
        if (item.get('class_sha256') != digest or source.get('sha256') != archive or
                state['class_proofs'].get(owner) != {'sha256': digest, 'source': source} or
                state['java_sources'].get(source.get('id')) != {k: v for k, v in source.items() if k != 'id'}):
            raise ValueError('Invalid Forge field provenance')
        name, descriptor = item.get('name'), item.get('descriptor')
        if index == 146 and owner == ENV and name == 'production' and descriptor == 'Z':
            return True
        if index == 145 and descriptor == DESC:
            if owner == ENV and name == 'dist': return self.forge_runtime['config']['dist']
            if owner == DIST and name in ('CLIENT', 'DEDICATED_SERVER'): return name
        raise ValueError('Unsupported Forge runtime field')

    def model(self, kind):
        entry = self.jni_gateways.get(self.pc) if kind == 'jni-import' else None
        if entry is None or entry[0] != 'env': return super().model(kind)
        _, index, name = entry
        refs = (self.forge_runtime or {}).get('refs', {})
        own_delete = index == 23 and str(self.reg('RSI')) in refs
        if index not in (145, 146, 24) and not own_delete: return super().model(kind)
        self.demand(self.forge_runtime is not None, 'FORGE_RUNTIME_SCENARIO_REQUIRED')
        s, t = self.jni_state, self.forge_runtime
        self.demand(s is not None and len(t['calls']) < MAX_CALLS and
                    len(t['calls'])+len(s['calls']) < MAX_CALLS, 'FORGE_RUNTIME_CALL_BUDGET')
        sp, target = self.frame(False)
        self.validate_interface('env', self.reg('RDI'))
        self.demand(s['pending_exception'] is None or own_delete, 'JNI_CALL_WITH_PENDING_EXCEPTION', index)
        try: self.verify_forge_metadata()
        except ValueError: self.demand(False, 'FORGE_RUNTIME_PROVENANCE_REQUIRED')
        a, b = self.reg('RSI'), self.reg('RDX')
        if index in (145, 146):
            try:
                value = self.field_value(s, a, b, index)
                item = s['fields'][str(b)]
                record = self.java_metadata.lookup_field(item['requested_class'], item['name'], item['descriptor'], True)
                self.demand(record is not None and all(record[k] == item[k] for k in
                    ('declaring_class', 'class_sha256', 'source')), 'FORGE_FIELD_METADATA_MISMATCH')
            except ValueError: self.demand(False, 'UNMODELED_FORGE_RUNTIME_FIELD')
            if index == 146: result = 1
            else:
                self.demand(len(refs) < MAX_REFS, 'FORGE_ENUM_REFERENCE_BUDGET')
                result = REF_BASE+16*len(refs)
                refs[str(result)] = {'type': DIST, 'constant': value, 'active': True}
            call = {'index': index, 'class': a, 'field': b, 'result': result}
        elif index == 24:
            self.demand(all(x == 0 or (str(x) in refs and refs[str(x)]['active']) for x in (a, b)),
                        'UNKNOWN_FORGE_ENUM_REFERENCE')
            result = int((a == b == 0) or (a != 0 and b != 0 and
                         refs[str(a)]['constant'] == refs[str(b)]['constant']))
            call = {'index': index, 'left': a, 'right': b, 'result': result}
        else:
            self.demand(refs[str(a)]['active'], 'DELETED_FORGE_ENUM_REFERENCE')
            refs[str(a)]['active'] = False
            result = self.reg('RAX')
            call = {'index': 23, 'ref': a}
        t['calls'].append(call)
        self.reg('RAX', result); self.reg('RSP', sp+8); self.reg('RIP', target)
        self.emit('DECLARED_FORGE_RUNTIME_CALL', name, f'result={result:x}',
                  'synthetic_input=true', 'java_initialization_executed=false', 'host_java_execution=false')

    def validate_forge_state(self, t, jni):
        if t is None: return
        if (type(t) is not dict or set(t) != {'config', 'refs', 'calls'} or type(t['config']) is not dict or
                type(t['refs']) is not dict or len(t['refs']) > MAX_REFS or type(t['calls']) is not list or
                len(t['calls']) > MAX_CALLS or jni is None or len(t['calls'])+len(jni['calls']) > MAX_CALLS):
            raise ValueError('Invalid Forge runtime checkpoint')
        c = t['config']
        if (any(type(c.get(k)) is not bool for k in ('initialized', 'production_property_present', 'production',
                'synthetic_declared_state', 'class_initialization_executed')) or
                c != configuration(c.get('profile'), c.get('initialized'), c.get('production_property_present'))):
            raise ValueError('Invalid Forge runtime provenance/configuration')
        if any(type(r) is not dict or set(r) != {'type', 'constant', 'active'} or
               type(r['active']) is not bool for r in t['refs'].values()):
            raise ValueError('Invalid Forge enum reference schema')
        replay = {}
        previous = self.forge_runtime
        self.forge_runtime = t
        try:
            for call in t['calls']:
                if type(call) is not dict or type(call.get('index')) is not int:
                    raise ValueError('Invalid Forge runtime call')
                index = call['index']
                if index in (145, 146):
                    if set(call) != {'index', 'class', 'field', 'result'} or type(call['result']) is not int:
                        raise ValueError('Invalid Forge field-read ledger')
                    value = self.field_value(jni, call['class'], call['field'], index, alive=False)
                    expected = 1 if index == 146 else REF_BASE+16*len(replay)
                    if call['result'] != expected: raise ValueError('Invalid Forge field result')
                    if index == 145: replay[str(expected)] = {'type': DIST, 'constant': value, 'active': True}
                elif index == 24:
                    if set(call) != {'index', 'left', 'right', 'result'} or any(type(call[k]) is not int for k in ('left', 'right', 'result')):
                        raise ValueError('Invalid Forge identity call')
                    a, b = call['left'], call['right']
                    if any(x != 0 and (str(x) not in replay or not replay[str(x)]['active']) for x in (a, b)):
                        raise ValueError('Invalid Forge identity reference')
                    expected = int((a == b == 0) or (a != 0 and b != 0 and replay[str(a)]['constant'] == replay[str(b)]['constant']))
                    if call['result'] != expected: raise ValueError('Invalid Forge identity result')
                elif index == 23:
                    if (set(call) != {'index', 'ref'} or type(call['ref']) is not int or
                            str(call['ref']) not in replay or not replay[str(call['ref'])]['active']):
                        raise ValueError('Invalid Forge deleted reference')
                    replay[str(call['ref'])]['active'] = False
                else: raise ValueError('Unknown Forge runtime ledger call')
            if replay != t['refs'] or any(type(r.get('active')) is not bool for r in t['refs'].values()):
                raise ValueError('Invalid Forge enum reference ledger')
        finally:
            self.forge_runtime = previous

    def capture_sparse(self):
        self.validate_forge_state(self.forge_runtime, self.jni_state)
        if self.forge_runtime is not None: self.verify_forge_metadata()
        s = super().capture_sparse(); s['forge_runtime'] = copy.deepcopy(self.forge_runtime)
        return s

    def restore_sparse(self, s):
        t = copy.deepcopy(s.get('forge_runtime'))
        self.validate_forge_state(t, s.get('jni'))
        if self.forge_runtime is not None and (t is None or self.forge_runtime['config'] != t['config']):
            raise ValueError('Changed Forge runtime configuration on restore')
        super().restore_sparse(s)
        self.forge_runtime = t
