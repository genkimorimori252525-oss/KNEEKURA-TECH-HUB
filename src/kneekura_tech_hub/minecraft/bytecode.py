"""Explicit preparation using the installed JDK, never a custom decompiler.

The provider runs javap against exact classfile bytes, not against a resolved
classpath. This avoids accidentally inspecting the first same-named class.
The output is pre-transform unless the input root explicitly records otherwise.
"""
from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .storage import ContractError, IntegrityError, Store, atomic_write, canonical, digest, key_for

OPTIONS = ['-private', '-s', '-c', '-l', '-verbose']
LIMITATIONS = ['Static bytecode references are not a complete call graph: reflection, '
               'dynamic dispatch, event callbacks and conditional Mixin plugins are unresolved.',
               'Original/distributed classfiles do not prove post-Mixin loaded bytecode or runtime behavior.']


def provider_identity(executable: str) -> dict:
    found = shutil.which(executable)
    if not found:
        raise ContractError('javap is unavailable; specify the installed JDK executable')
    path = Path(found).resolve()
    components = {}
    for relative in ('release', 'lib/modules'):
        component = path.parent.parent / relative
        if component.is_file():
            with component.open('rb') as stream:
                components[relative] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'provider': 'jdk-javap-v1', 'executable': str(path),
            'executable_hash': digest(path.read_bytes()), 'options': OPTIONS,
            'jdk_components': components,
            'jdk_image_status': 'HASHED' if 'lib/modules' in components else 'UNKNOWN',
            'normalization': 'remove temporary classfile path and modification date'}


def _run(data: bytes, identity: dict, timeout: float, max_output_bytes: int) -> str:
    # Remove Java option injection from the environment of this tool invocation.
    env = {k: v for k, v in os.environ.items()
           if k not in {'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS', 'JDK_JAVA_OPTIONS', 'CLASSPATH'}}
    env['LC_ALL'] = 'C'
    with tempfile.TemporaryDirectory(prefix='kneekura-javap-') as folder:
        source = Path(folder) / 'Input.class'; source.write_bytes(data)
        output = Path(folder) / 'output.txt'
        with output.open('wb') as stream:
            process = subprocess.Popen([identity['executable'], *OPTIONS, str(source)],
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=stream, env=env)
            started = time.monotonic()
            try:
                while process.poll() is None:
                    if time.monotonic() - started > timeout or output.stat().st_size > max_output_bytes:
                        raise ContractError('javap time/output budget exceeded')
                    time.sleep(0.01)
            finally:
                if process.poll() is None:
                    process.kill()
                process.wait()
        if output.stat().st_size > max_output_bytes:
            raise ContractError('javap output budget exceeded')
        text = output.read_text(encoding='utf-8', errors='strict')
        if process.returncode:
            raise ContractError('javap rejected the classfile: ' + text[:400])
    # These two presentation lines are not bytecode; the input hash is retained.
    text = re.sub(r'^Classfile .*$', 'Classfile sha256:' + digest(data), text, flags=re.M)
    text = re.sub(r'^  Last modified .*\n', '', text, flags=re.M)
    return text


def parse_javap(text: str) -> dict:
    owner_match = re.search(r'^\s*this_class:\s+#[0-9]+\s+//\s+(\S+)', text, re.M)
    if not owner_match:
        raise ContractError('Unsupported javap output: no exact this_class identity')
    owner = owner_match.group(1)
    parent = re.search(r'^\s*super_class:\s+#[0-9]+\s+//\s+(\S+)', text, re.M)
    members = []; current = None; declaration = None; inside = False
    for number, line in enumerate(text.splitlines(), 1):
        if line == '{': inside = True; continue
        if line == '}': inside = False
        if not inside: continue
        if re.match(r'^  \S', line) and line.rstrip().endswith(';'):
            if current: current['line_end'] = number - 1
            declaration = (line.strip(), number); current = None
        signature = re.match(r'^    descriptor:\s+(\S+)', line)
        if signature and declaration:
            header, start = declaration; descriptor = signature.group(1)
            kind = 'method' if descriptor.startswith('(') else 'field'
            if header == 'static {};': name = '<clinit>'
            elif kind == 'method':
                name = header.split('(', 1)[0].split()[-1]
                if name.replace('.', '/') == owner: name = '<init>'
            else:
                name = header.rstrip(';').split(' = ', 1)[0].split()[-1]
            current = {'owner': owner, 'name': name, 'descriptor': descriptor, 'kind': kind,
                       'declaration': header, 'line_start': start, 'line_end': None, 'references': []}
            members.append(current); declaration = None
        if current:
            ref = re.search(r'^\s*\d+:\s+(invoke\w+|getfield|putfield|getstatic|putstatic).*//\s+(?:InterfaceMethod|Method|Field)\s+(\S+)', line)
            if ref:
                target, desc = ref.group(2).split(':', 1)
                if '.' in target: target_owner, name = target.rsplit('.', 1)
                else: target_owner, name = owner, target
                current['references'].append({'owner': target_owner, 'name': name.strip('"'),
                                              'descriptor': desc, 'opcode': ref.group(1),
                                              'disassembly_line': number, 'relation': 'static_reference'})
    if members: members[-1]['line_end'] = len(text.splitlines())
    return {'owner': owner, 'superclass': parent.group(1) if parent else None,
            'members': members, 'limitations': LIMITATIONS}


def prepare_class(store: Store, class_hash: str, identity: dict, *, timeout: float = 20,
                  max_output_bytes: int = 16 * 1024 * 1024) -> tuple[dict, bool]:
    cache_key = key_for({'class_hash': class_hash, 'provider': identity})
    cache_path = store.root / 'derived' / (cache_key + '.json')
    if cache_path.exists():
        receipt = json.loads(cache_path.read_bytes())
        if receipt.get('cache_key') != cache_key:
            raise IntegrityError('Derived cache identity mismatch')
        store.read(class_hash)
        text = store.read(receipt['text_hash']).decode('utf-8')
        if not text.startswith('Classfile sha256:' + class_hash + '\n'):
            raise IntegrityError('Derived output/input identity mismatch')
        # Reconstruct metadata from verified output, not from an unverified cache payload.
        return dict(parse_javap(text), text_hash=receipt['text_hash'], provider=identity), True
    data = store.read(class_hash)
    if not data.startswith(b'\xca\xfe\xba\xbe'):
        raise ContractError('Invalid classfile magic')
    text = _run(data, identity, timeout, max_output_bytes)
    parsed = parse_javap(text)
    text_hash = store.put(text.encode('utf-8'))
    atomic_write(cache_path, canonical({'cache_key': cache_key, 'text_hash': text_hash}))
    return dict(parsed, text_hash=text_hash, provider=identity), False
