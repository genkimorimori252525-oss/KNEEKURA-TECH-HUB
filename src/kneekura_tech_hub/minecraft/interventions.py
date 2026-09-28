"""Inspectable intervention candidates and bounded, provenance-carrying relations.

Static declarations are candidates, NOT proof that a plugin selected an injection,
that a refmap resolved, that transformations ran, or that two mods are compatible.
"""
from __future__ import annotations

import json
import re
from pathlib import PurePosixPath

from . import index
from .classfile import read_class
from .storage import ContractError, Store, canonical, key_for


def _array(value): return value if isinstance(value, list) else [value]


def _target(value):
    if not isinstance(value, str) or not value: raise ContractError('Empty target selector')
    owner = None
    if value.startswith('L') and ';' in value:
        owner, value = value[1:].split(';', 1)
    pos = value.find('(')
    return dict(owner=owner, member=value if pos < 0 else value[:pos],
                descriptor=None if pos < 0 else value[pos:])


def _resource_name(name):
    if not isinstance(name, str): raise ContractError('Resource path must be a string')
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ContractError('Unsafe metadata resource reference')
    return str(p)


def _scan(store, identifier, *, scope=None, namespace=None, track=None):
    index._validate_filters(scope, namespace, track)
    snap = index._load(store, identifier); p = snap['profile']; rows = []; edges = []; unresolved = []
    docs = [d for d in p['documents'] if index._selected(d, p, scope, namespace, track)]
    available = {(d['root_id'], d['path']) for d in docs}

    def emit(d, kind, **kwargs):
        row = dict(kind=kind, root_id=d['root_id'], namespace=d['namespace'], scope=d['scope'],
                   stage=d['stage'], track=d['track'], applicability='STATIC_CANDIDATE',
                   evidence=index.locator(identifier, d))
        row.update(kwargs); rows.append(row)

    def edge(d, relation, source, target, **kwargs):
        edges.append(dict(relation=relation, source=source, target=target,
                          root_id=d['root_id'], namespace=d['namespace'], scope=d['scope'],
                          stage=d['stage'], track=d['track'], evidence=index.locator(identifier, d), **kwargs))

    for d in docs:
        path = d['path']
        try:
            if d['media'] == 'class':
                c = read_class(store.read(d['content_hash']))
                for relation, names in [('extends', [c['superclass']]), ('implements', c['interfaces'])]:
                    for name in names:
                        if name: edge(d, relation, {'owner': c['owner']}, {'owner': name})
                mixins = [a for a in c['annotations'] if a['descriptor'] == 'Lorg/spongepowered/asm/mixin/Mixin;']
                for mixin in mixins:
                    a = mixin['elements']; targets = []
                    for v in _array(a.get('value', [])):
                        desc = v.get('class') if isinstance(v, dict) else None
                        if isinstance(desc, str) and desc.startswith('L') and desc.endswith(';'): targets.append(desc[1:-1])
                    targets.extend(x.replace('.', '/') for x in _array(a.get('targets', [])) if isinstance(x, str))
                    for m in c['methods']:
                        for ann in m['annotations']:
                            injection = ann['descriptor'].split('/')[-1].rstrip(';')
                            if injection not in {'Inject','Redirect','ModifyArg','ModifyArgs','ModifyVariable','ModifyConstant','Overwrite','WrapOperation','WrapWithCondition','ModifyExpressionValue','ModifyReceiver','WrapMethod'}: continue
                            selectors = ann['elements'].get('method', [m['name'] + m['descriptor']] if injection == 'Overwrite' else [])
                            if not selectors: unresolved.append({'path': path, 'reason': 'Dynamic or unrecognised Mixin selector'})
                            for sel in _array(selectors):
                                target = _target(sel)
                                for owner in ([target['owner']] if target['owner'] else targets):
                                    final = dict(target, owner=owner)
                                    emit(d, 'mixin_injection', mixin=c['owner'], source_member=m['name'],
                                         source_descriptor=m['descriptor'], injector=injection, target=final,
                                         injection=ann['elements'], applicability='CONDITIONAL_NOT_EXECUTED')
                                    edge(d, 'injects', {'owner': c['owner'], 'member': m['name'], 'descriptor': m['descriptor']}, final,
                                         applicability='CONDITIONAL_NOT_EXECUTED')
                prepared = snap['bytecode'].get(d['document_id'], {})
                # javap's reference preview is explicitly a partial static relation set.
                for m in prepared.get('members', []):
                    for ref in m.get('references', []):
                        if isinstance(ref, dict) and ref.get('owner'):
                            edge(d, 'references', {'owner': c['owner'], 'member': m['name'], 'descriptor': m['descriptor']}, ref)
            elif path.endswith('.mixins.json') or path == 'fabric.mod.json':
                obj = json.loads(store.read(d['content_hash']))
                if not isinstance(obj, dict): raise ContractError('Metadata must be an object')
                if path == 'fabric.mod.json':
                    for phase, values in obj.get('entrypoints', {}).items():
                        for value in _array(values): emit(d, 'entrypoint', phase=phase, declaration=value)
                    resources = obj.get('mixins', []) + ([obj['accessWidener']] if 'accessWidener' in obj else [])
                    for resource in resources:
                        name = _resource_name(resource.get('config') if isinstance(resource, dict) else resource)
                        emit(d, 'metadata_reference', resource=name)
                        if (d['root_id'], name) not in available: unresolved.append({'path': path, 'reason': 'Missing resource ' + name})
                    for nested in obj.get('jars', []):
                        name = _resource_name(nested['file']); emit(d, 'nested_jar', resource=name)
                        unresolved.append({'path': path, 'reason': 'Nested JAR must be captured as its own classpath root: ' + name})
                else:
                    for side in ('mixins', 'client', 'server'):
                        for name in obj.get(side, []):
                            full = '.'.join(x for x in (obj.get('package', ''), name) if x).replace('.', '/')
                            emit(d, 'mixin_config', mixin=full, side='common' if side == 'mixins' else side,
                                 plugin=obj.get('plugin'), refmap=obj.get('refmap'), applicability='CONDITIONAL_NOT_EXECUTED')
                    if obj.get('plugin'): unresolved.append({'path': path, 'reason': 'Mixin plugin selection not executed'})
                    if obj.get('refmap'):
                        name = _resource_name(obj['refmap'])
                        unresolved.append({'path': path, 'reason': 'refmap resolution requires exact runtime context: ' + name})
            elif path.endswith('.accesswidener'):
                lines = store.read(d['content_hash']).decode().splitlines()
                records = [(i, s.split('#')[0].strip().split()) for i, s in enumerate(lines, 1) if s.split('#')[0].strip()]
                if not records or len(records[0][1]) != 3 or records[0][1][:2] not in (['accessWidener','v1'],['accessWidener','v2']):
                    raise ContractError('Invalid access widener header')
                ns = records[0][1][2]
                for line, v in records[1:]:
                    if len(v) not in (3,5) or v[1] not in ('class','field','method'): raise ContractError('Invalid access widener record')
                    emit(d, 'access_widener', namespace=ns, access=v[0], line=line,
                         target={'owner': v[2], 'member': v[3] if len(v)>3 else None, 'descriptor': v[4] if len(v)>4 else None})
            elif path == 'META-INF/accesstransformer.cfg':
                for line, s in enumerate(store.read(d['content_hash']).decode().splitlines(), 1):
                    v=s.split('#')[0].split()
                    if not v: continue
                    if len(v) not in (2,3): raise ContractError('Invalid access transformer record')
                    target = _target(v[2]) if len(v)==3 else dict(member=None,descriptor=None)
                    target['owner'] = v[1].replace('.', '/')
                    emit(d, 'access_transformer', access=v[0], target=target, line=line)
        except (OSError, ValueError, KeyError, TypeError, IndexError, UnicodeError) as exc:
            unresolved.append({'path': path, 'root_id': d['root_id'], 'reason': str(exc)})
    # Discovery cannot exclude arbitrary transformers, reflection or conditionally generated code.
    unresolved.append({'reason': 'Dynamic transformations/reflection, runtime refmaps and load order not executed'})
    return snap, rows, edges, unresolved


def inspect_interventions(store: Store, identifier: str, *, owner=None, member=None, descriptor=None,
                          scope=None, namespace=None, track=None, limit=20, cursor=None):
    index._positive(limit,1000)
    snap, rows, _, unresolved = _scan(store, identifier, scope=scope, namespace=namespace, track=track)
    request = dict(op='interventions',owner=owner,member=member,descriptor=descriptor,scope=scope,namespace=namespace,track=track)
    offset=index._offset(cursor,identifier,request)
    if offset is None: return index._envelope(snap,identifier,'STALE',[])
    for key, value in [('owner',owner),('member',member),('descriptor',descriptor)]:
        if value is not None: rows=[r for r in rows if r.get('target',{}).get(key)==value]
    page=rows[offset:offset+limit]
    while len(page)>1 and len(canonical(page))>48*1024: page.pop()
    end=offset+len(page)
    out=index._envelope(snap,identifier,'PARTIAL',page,
                        cursor=index._cursor(identifier,request,end) if end<len(rows) else None,
                        coverage=dict(complete=False,declared_candidates=len(rows),unresolved=unresolved),
                        evidence=[r['evidence'] for r in page])
    out.update(compatibility_verdict='NOT_DETERMINED',canonical_writes=0)
    return out


def relations(store: Store, identifier: str, *, owner: str, depth=1, scope=None, namespace=None,
              track=None, limit=50, cursor=None):
    index._positive(depth,3); index._positive(limit,1000)
    snap,_,edges,unresolved=_scan(store,identifier,scope=scope,namespace=namespace,track=track)
    if not isinstance(owner,str) or not owner: raise ContractError('Exact internal owner name required')
    request=dict(op='relations',owner=owner,depth=depth,scope=scope,namespace=namespace,track=track)
    offset=index._offset(cursor,identifier,request)
    if offset is None: return index._envelope(snap,identifier,'STALE',[])
    reached={owner}; selected={}
    for _ in range(depth):
        added=set()
        for e in edges:
            if e['source']['owner'] in reached or e['target']['owner'] in reached:
                selected[key_for(e)]=e; added.update((e['source']['owner'],e['target']['owner']))
        reached |= added
    rows=list(selected.values()); page=rows[offset:offset+limit]; end=offset+len(page)
    return index._envelope(snap,identifier,'PARTIAL',page,
                           coverage=dict(complete=False,depth=depth,unresolved=unresolved,edges=len(rows)),
                           cursor=index._cursor(identifier,request,end) if end<len(rows) else None,
                           evidence=[e['evidence'] for e in page],
                           warnings=['Target origins are not inferred: duplicate classloaders/origins remain unresolved. No dynamic call graph.'])
