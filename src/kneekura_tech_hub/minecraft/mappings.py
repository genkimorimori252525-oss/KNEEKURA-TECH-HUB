"""Scoped symbol lookup, not a replacement bytecode remapper.

Reads Tiny v2, TSRG 1/2 and Mojang's ProGuard mapping form. All members are
identified by owner + descriptor. Missing names and collisions remain visible.
Actual JAR transformations are delegated to the pinned external provider.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from .storage import ContractError, digest


def remap_descriptor(descriptor: str, names: dict[str, str | None]) -> str:
    if not isinstance(descriptor,str) or not descriptor:
        raise ContractError('A JVM descriptor is required')
    offset = 0
    def typ(allow_void=False):
        nonlocal offset
        if offset >= len(descriptor): raise ContractError('Truncated JVM descriptor')
        char = descriptor[offset]; offset += 1
        if char in 'BCDFIJSZ' or char == 'V' and allow_void: return char
        if char == '[': return '[' + typ(False)
        if char == 'L':
            end = descriptor.find(';',offset)
            if end < offset or end == offset: raise ContractError('Malformed object descriptor')
            owner = descriptor[offset:end]
            if any(c in owner for c in '.;[()\x00'):
                raise ContractError('Malformed internal class name')
            offset = end+1
            target = names.get(owner,owner)
            if not target: raise ContractError('Ambiguous/missing descriptor type mapping: '+owner)
            return 'L'+target+';'
        raise ContractError('Invalid JVM descriptor type: '+char)
    if descriptor.startswith('('):
        offset = 1; params = []
        while offset < len(descriptor) and descriptor[offset] != ')': params.append(typ())
        if offset >= len(descriptor): raise ContractError('Unclosed method descriptor')
        offset += 1
        result = '('+''.join(params)+')'+typ(True)
    else:
        result = typ(False)
    if offset != len(descriptor): raise ContractError('Trailing JVM descriptor data')
    return result


def _java_type(name: str) -> str:
    arrays = 0
    while name.endswith('[]'):
        arrays += 1; name = name[:-2]
    primitive = {'void':'V','boolean':'Z','byte':'B','short':'S','char':'C',
                 'int':'I','long':'J','float':'F','double':'D'}
    return '['*arrays + primitive.get(name,'L'+name.replace('.','/')+';')


@dataclass
class MappingTable:
    namespaces: list[str]
    classes: list[dict]
    mapping_hash: str
    format: str

    @classmethod
    def parse(cls, text: str, format: str, *, source_namespace: str | None = None,
              target_namespace: str | None = None) -> 'MappingTable':
        if not isinstance(text,str) or len(text.encode('utf-8')) > 64*1024*1024:
            raise ContractError('Mapping text exceeds supported input budget')
        lines = text.splitlines(); classes = []; current = None
        if not lines: raise ContractError('Empty mapping')
        if format == 'tiny':
            header = lines[0].split('\t')
            if header[:3] != ['tiny','2','0'] or len(header) < 5:
                raise ContractError('This lookup adapter supports Tiny v2; convert other forms with mapping-io')
            namespaces = header[3:]
            if any(line == '\tescaped-names' for line in lines[1:]):
                raise ContractError('Tiny escaped-names metadata is not supported by this lookup adapter; normalize explicitly')
            for n,raw in enumerate(lines[1:],2):
                fields = raw.split('\t')
                if not raw or raw.startswith('#'): continue
                if fields[0] == 'c':
                    if len(fields) != len(namespaces)+1: raise ContractError(f'Malformed class at line {n}')
                    current = {'names':dict(zip(namespaces,fields[1:])), 'members':[], 'line':n}
                    classes.append(current)
                elif len(fields) > 1 and fields[0] == '' and fields[1] in {'m','f'}:
                    if current is None or len(fields) != len(namespaces)+3:
                        raise ContractError(f'Malformed member at line {n}')
                    remap_descriptor(fields[2],{})
                    current['members'].append({'kind':'method' if fields[1]=='m' else 'field',
                        'descriptor':fields[2], 'names':dict(zip(namespaces,fields[3:])), 'line':n})
                # Comments, local variables and parameter annotations are not
                # separate executable symbols; raw mapping remains the evidence.
        elif format == 'tsrg':
            header = lines[0].split()
            if header[0] == 'tsrg2': namespaces = header[1:]; body = lines[1:]
            else:
                if not source_namespace or not target_namespace:
                    raise ContractError('TSRG1 requires explicit source and target namespaces')
                namespaces = [source_namespace,target_namespace]; body = lines
            for n,raw in enumerate(body,2 if header[0]=='tsrg2' else 1):
                if not raw.strip() or raw.lstrip().startswith('#') or raw.startswith('\t\t'): continue
                fields = raw.split()
                if not raw.startswith('\t'):
                    if len(fields) != len(namespaces): raise ContractError(f'Malformed TSRG class at {n}')
                    current = {'names':dict(zip(namespaces,fields)), 'members':[], 'line':n}; classes.append(current)
                else:
                    if current is None: raise ContractError('TSRG member without class')
                    desc = fields[1] if len(fields)==len(namespaces)+1 else None
                    if desc: remap_descriptor(desc,{})
                    members = [fields[0],*fields[2:]] if desc else fields
                    if len(members)!=len(namespaces): raise ContractError(f'Malformed TSRG member at {n}')
                    current['members'].append({'kind':'method' if desc and desc.startswith('(') else 'field',
                        'descriptor':desc,'names':dict(zip(namespaces,members)),'line':n})
        elif format == 'proguard':
            if not source_namespace or not target_namespace:
                raise ContractError('ProGuard requires explicit source/target namespace labels')
            namespaces = [source_namespace,target_namespace]
            for n,raw in enumerate(lines,1):
                if not raw.strip() or raw.lstrip().startswith('#'): continue
                if not raw[:1].isspace():
                    match = re.fullmatch(r'(.+) -> (.+):',raw)
                    if not match: raise ContractError(f'Malformed ProGuard class at {n}')
                    current = {'names':dict(zip(namespaces,[match[1].replace('.','/'),match[2].replace('.','/')])),
                               'members':[], 'line':n}; classes.append(current)
                else:
                    if current is None or ' -> ' not in raw: raise ContractError(f'Malformed ProGuard member at {n}')
                    decl,target = raw.strip().rsplit(' -> ',1)
                    decl = re.sub(r'^\d+:\d+:','',decl)
                    decl = re.sub(r':\d+(?::\d+)?$','',decl)
                    typ,name = decl.split(' ',1)
                    if '(' in name:
                        method,params = name.split('(',1)
                        if not params.endswith(')'): raise ContractError('Malformed ProGuard arguments')
                        desc = '('+''.join(_java_type(x.strip()) for x in params[:-1].split(',') if x.strip())+')'+_java_type(typ)
                        name = method; kind = 'method'
                    else: desc = _java_type(typ); kind = 'field'
                    remap_descriptor(desc,{})
                    current['members'].append({'kind':kind,'descriptor':desc,
                        'names':dict(zip(namespaces,[name,target])),'line':n})
        else: raise ContractError('Unsupported mapping format')
        if len(namespaces) < 2 or len(set(namespaces)) != len(namespaces):
            raise ContractError('Distinct mapping namespaces required')
        if 'parchment' in namespaces: raise ContractError('Parchment is annotation, not an executable namespace')
        return cls(namespaces,classes,digest(text.encode('utf-8')),format)

    def _class_map(self,source: str,target: str) -> dict:
        result = {}
        for c in self.classes:
            key = c['names'].get(source); value = c['names'].get(target)
            if not key: continue
            if key in result and result[key] != value: result[key] = None
            else: result[key] = value
        return result

    def resolve(self, source: str, target: str, owner: str, member: str | None = None,
                descriptor: str | None = None, *, aliases: dict | None = None) -> dict:
        aliases = aliases or {}
        source = aliases.get(source,source); target = aliases.get(target,target)
        if source not in self.namespaces or target not in self.namespaces:
            raise ContractError('Requested namespace is not declared by this mapping')
        if descriptor: remap_descriptor(descriptor,{})
        results = []; unresolved = []
        original = self.namespaces[0]
        for c in self.classes:
            if c['names'].get(source) != owner: continue
            to_owner = c['names'].get(target)
            if not to_owner:
                unresolved.append({'line':c['line'],'reason':'Missing target class name'}); continue
            if member is None:
                results.append({'owner':to_owner,'name':None,'descriptor':None,'kind':'class','line':c['line']})
                continue
            for m in c['members']:
                if m['names'].get(source) != member: continue
                try:
                    from_desc = remap_descriptor(m['descriptor'], self._class_map(original,source)) if m['descriptor'] else None
                    if descriptor is not None and from_desc != descriptor: continue
                    target_name = m['names'].get(target)
                    if not target_name: raise ContractError('Missing target member name')
                    to_desc = remap_descriptor(m['descriptor'], self._class_map(original,target)) if m['descriptor'] else None
                    results.append({'owner':to_owner,'name':target_name,'descriptor':to_desc,
                                    'kind':m['kind'],'line':m['line']})
                except ContractError as exc:
                    unresolved.append({'line':m['line'],'reason':str(exc)})
        return {'schema_version':1,'status':'AMBIGUOUS' if len(results)>1 else 'PARTIAL' if unresolved else
                'OK' if results else 'NOT_FOUND', 'results':results,'unresolved':unresolved,
                'mapping_hash':self.mapping_hash,'from_namespace':source,'to_namespace':target,
                'coverage':{'mapping_domain_only':True, 'format':self.format},
                'warnings':['Mapping lookup does not prove cross-version equivalence or runtime compatibility']}
