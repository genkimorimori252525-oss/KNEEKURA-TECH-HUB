import { createHash } from 'node:crypto';

export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

export function stableJson(value) {
  if (Array.isArray(value)) return '[' + value.map(stableJson).join(',') + ']';
  if (value && typeof value === 'object') {
    return '{' + Object.keys(value).sort().map(
      key => JSON.stringify(key) + ':' + stableJson(value[key]),
    ).join(',') + '}';
  }
  return JSON.stringify(value);
}

export function exactKeys(value, keys, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value) ||
      Object.keys(value).sort().join('\0') !== [...keys].sort().join('\0')) {
    throw new TypeError('INVALID_' + label + '_FIELDS');
  }
}

export function identifier(value) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value)) {
    throw new TypeError('INVALID_IDENTIFIER');
  }
  return value;
}

export function hashId(value) {
  if (typeof value !== 'string' || !/^[a-f0-9]{64}$/.test(value)) {
    throw new TypeError('INVALID_SHA256');
  }
  return value;
}

export function integer(value, min, max, label = 'INTEGER') {
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    throw new TypeError('INVALID_' + label);
  }
  return value;
}

/** Bounded JSON parser; JSON.parse alone silently accepts duplicate map keys. */
export function decodeJson(bytes, maxBytes = 1048576) {
  if (bytes.length > maxBytes) throw new TypeError('JSON_SIZE_LIMIT');
  const source = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
  let offset = 0;
  let tokens = 0;

  function whitespace() {
    while (/[\x20\x09\x0a\x0d]/.test(source[offset] ?? '!')) offset++;
  }

  function string() {
    const start = offset++;
    while (offset < source.length) {
      const character = source[offset++];
      if (character === '\\') {
        offset++;
        continue;
      }
      if (character === '"') {
        const result = JSON.parse(source.slice(start, offset));
        for (const character of result) {
          const codePoint = character.codePointAt(0);
          if (codePoint >= 0xd800 && codePoint <= 0xdfff) {
            throw new TypeError('INVALID_UNICODE');
          }
        }
        return result;
      }
    }
    throw new TypeError('INVALID_JSON_STRING');
  }

  function object(depth) {
    offset++;
    whitespace();
    const result = {};
    const seen = new Set();
    if (source[offset] === '}') {
      offset++;
      return result;
    }
    while (offset < source.length) {
      whitespace();
      if (source[offset] !== '"') throw new TypeError('INVALID_JSON_KEY');
      const key = string();
      if (seen.has(key)) throw new TypeError('DUPLICATE_JSON_KEY');
      seen.add(key);
      whitespace();
      if (source[offset++] !== ':') throw new TypeError('INVALID_JSON_COLON');
      const member = value(depth + 1);
      // __proto__ must remain data and cannot change the object's prototype.
      Object.defineProperty(result, key, {
        value: member, enumerable: true, writable: true, configurable: true,
      });
      whitespace();
      const delimiter = source[offset++];
      if (delimiter === '}') return result;
      if (delimiter !== ',') throw new TypeError('INVALID_JSON_OBJECT');
    }
    throw new TypeError('INVALID_JSON_OBJECT');
  }

  function array(depth) {
    offset++;
    whitespace();
    const result = [];
    if (source[offset] === ']') {
      offset++;
      return result;
    }
    while (offset < source.length) {
      result.push(value(depth + 1));
      whitespace();
      const delimiter = source[offset++];
      if (delimiter === ']') return result;
      if (delimiter !== ',') throw new TypeError('INVALID_JSON_ARRAY');
    }
    throw new TypeError('INVALID_JSON_ARRAY');
  }

  function value(depth) {
    if (depth > 64 || ++tokens > 100000) throw new TypeError('JSON_COMPLEXITY_LIMIT');
    whitespace();
    const character = source[offset];
    if (character === '"') return string();
    if (character === '{') return object(depth);
    if (character === '[') return array(depth);
    for (const [word, result] of [['true', true], ['false', false], ['null', null]]) {
      if (source.startsWith(word, offset)) {
        offset += word.length;
        return result;
      }
    }
    const match = source.slice(offset).match(/^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/);
    if (!match) throw new TypeError('INVALID_JSON_VALUE');
    offset += match[0].length;
    const number = Number(match[0]);
    if (!Number.isFinite(number) || Math.abs(number) > Number.MAX_SAFE_INTEGER) {
      throw new TypeError('UNSAFE_JSON_NUMBER');
    }
    return number;
  }

  const result = value(0);
  whitespace();
  if (offset !== source.length) throw new TypeError('INVALID_JSON_TRAILING');
  return result;
}

/** Preserve the existing RunSnapshot algorithm: recursively sort then JSON.stringify.
 * JSON.stringify still orders integer-like object keys numerically; do not replace this with stableJson. */
export function canonicalRunSnapshotBytes(value) {
  function sorted(item) {
    if (Array.isArray(item)) return item.map(sorted);
    if (item && typeof item === 'object') return Object.fromEntries(Object.keys(item).sort().map(key => [key, sorted(item[key])]));
    return item;
  }
  return Buffer.from(JSON.stringify(sorted(value)), 'utf8');
}
