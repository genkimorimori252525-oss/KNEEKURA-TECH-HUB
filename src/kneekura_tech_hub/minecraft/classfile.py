"""Read JVM identities and declaration annotations without loading a MOD class.

This is a bounded classfile reader, not a bytecode transformer or interpreter.
Code instructions remain the responsibility of the installed JDK javap provider.
"""
from __future__ import annotations

import struct
from .storage import ContractError


class Reader:
    def __init__(self, data: bytes):
        self.data, self.position = data, 0

    def take(self, size: int) -> bytes:
        if size < 0 or self.position + size > len(self.data):
            raise ContractError('Truncated classfile')
        result = self.data[self.position:self.position + size]
        self.position += size
        return result

    def u1(self): return self.take(1)[0]
    def u2(self): return struct.unpack('>H', self.take(2))[0]
    def u4(self): return struct.unpack('>I', self.take(4))[0]


def read_class(data: bytes) -> dict:
    if len(data) > 32 * 1024 * 1024: raise ContractError('Classfile exceeds size budget')
    r = Reader(data)
    if r.u4() != 0xCAFEBABE: raise ContractError('Not a JVM classfile')
    minor, major = r.u2(), r.u2()
    count = r.u2(); cp = [None] * count; i = 1
    while i < count:
        tag = r.u1()
        if tag == 1:
            # JVM modified UTF-8 encodes null specially and permits UTF-16 surrogate units.
            text = r.take(r.u2()).replace(b'\xc0\x80', b'\x00').decode('utf-8', 'surrogatepass')
            cp[i] = ('utf', text.encode('utf-16', 'surrogatepass').decode('utf-16', 'surrogatepass'))
        elif tag in (3, 4): cp[i] = ('number', struct.unpack('>i' if tag == 3 else '>f', r.take(4))[0])
        elif tag in (5, 6):
            cp[i] = ('number', struct.unpack('>q' if tag == 5 else '>d', r.take(8))[0]); i += 1
        elif tag in (7, 8, 16, 19, 20): cp[i] = (tag, r.u2())
        elif tag in (9, 10, 11, 12, 17, 18): cp[i] = (tag, r.u2(), r.u2())
        elif tag == 15: cp[i] = (tag, r.u1(), r.u2())
        else: raise ContractError(f'Unknown constant pool tag {tag}')
        i += 1

    def entry(n):
        if not 0 < n < len(cp) or cp[n] is None: raise ContractError('Bad constant pool reference')
        return cp[n]

    def text(n):
        value = entry(n)
        if value[0] != 'utf': raise ContractError('Expected UTF-8 constant')
        return value[1]

    def class_name(n):
        value = entry(n)
        if value[0] != 7: raise ContractError('Expected class constant')
        return text(value[1])

    def element(a, depth=0):
        if depth > 16: raise ContractError('Annotation nesting exceeds budget')
        tag = chr(a.u1())
        if tag == 's': return text(a.u2())
        if tag in 'BCDFIJSZ':
            value = entry(a.u2())
            if value[0] != 'number': raise ContractError('Expected numeric annotation constant')
            return bool(value[1]) if tag == 'Z' else value[1]
        if tag == 'e': return {'enum_type': text(a.u2()), 'enum_value': text(a.u2())}
        if tag == 'c': return {'class': text(a.u2())}
        if tag == '@': return annotation(a, depth + 1)
        if tag == '[': return [element(a, depth + 1) for _ in range(a.u2())]
        raise ContractError(f'Unsupported annotation element {tag}')

    def annotation(a, depth=0):
        desc = text(a.u2()); result = {}
        for _ in range(a.u2()):
            name = text(a.u2())
            if name in result: raise ContractError('Duplicate annotation element')
            result[name] = element(a, depth + 1)
        return {'descriptor': desc, 'elements': result}

    def attributes(a):
        annotations = []
        for _ in range(a.u2()):
            name = text(a.u2()); body = Reader(a.take(a.u4()))
            if name in ('RuntimeVisibleAnnotations', 'RuntimeInvisibleAnnotations'):
                annotations.extend(annotation(body) for _ in range(body.u2()))
                if body.position != len(body.data): raise ContractError('Trailing annotation bytes')
        return annotations

    flags, owner, parent = r.u2(), class_name(r.u2()), r.u2()
    interfaces = [class_name(r.u2()) for _ in range(r.u2())]
    fields, methods = [], []
    for destination in (fields, methods):
        for _ in range(r.u2()):
            access, name, descriptor = r.u2(), text(r.u2()), text(r.u2())
            destination.append({'name': name, 'descriptor': descriptor, 'access': access,
                                'annotations': attributes(r)})
    annotations = attributes(r)
    if r.position != len(data): raise ContractError('Trailing classfile bytes')

    # CONSTANT_Class entries form a bounded structural/reference candidate set.
    # They include declaration types and owners referenced from bytecode without
    # requiring javap. Array class constants use descriptors and are excluded
    # here rather than being misreported as internal owners.
    class_references = sorted({
        text(value[1])
        for value in cp[1:]
        if value is not None and value[0] == 7
        and not text(value[1]).startswith('[')
    })

    return {'owner': owner, 'superclass': class_name(parent) if parent else None,
            'interfaces': interfaces, 'major': major, 'minor': minor, 'access': flags,
            'fields': fields, 'methods': methods, 'annotations': annotations,
            'class_references': class_references}
