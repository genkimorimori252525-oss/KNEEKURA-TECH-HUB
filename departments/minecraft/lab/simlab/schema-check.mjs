#!/usr/bin/env node
// =============================================================================
// schema-check.mjs — トレースの形が黙ってズレるのを止める (AGENT-04)
// =============================================================================
//
// 使い方:
//   node simlab/schema-check.mjs [検査するトレースのパス]   (既定 simlab/fixtures)
//
// **何から守るのか**: Java 側 (SimCh) が形を変えたのに解析側 (stats.mjs) が古い形を
// 読み続けると、**表の数字が静かに 0 になる**。0 は「そうだった」のか
// 「読めなかった」のか見分けが付かないので、気づくのが遅れる。
// ここで両方向を見張って、ズレたら即座に落とす。
//
// 3つ見る:
//   1. stats.mjs の CONSUMED に在って schema.json に無いフィールド
//      → 解析側が「宣言されていないもの」を読んでいる
//   2. トレースに在って schema.json に無いフィールド
//      → 実機が「宣言していないもの」を書いている
//   3. section-parse.golden.json と JS の parseSection が一致するか
//      → Java と JS の2実装が同じ答えを出すか (Java 側は SimChSchemaTest が見る)
//
// Java 側の見張りは src/test/.../SimChSchemaTest.java。**両方要る** ——
// Java だけだと JS の読み手がズレたときに気づけず、JS だけだと schema.json 自体が
// SimCh から離れたときに気づけない。
//
// 依存は Node 標準ライブラリのみ。

import fs from 'node:fs';
import path from 'node:path';
import { parseTrace, parseSection, CONSUMED } from './stats.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname).replace(/^\/([A-Za-z]:)/, '$1');
const SCHEMA = path.join(HERE, 'schema.json');
const GOLDEN = path.join(HERE, 'fixtures', 'section-parse.golden.json');
const CASES = path.join(HERE, 'fixtures', 'section-parse.cases.txt');

const argv = process.argv.slice(2);
// --coverage: 検査対象が『全 channel と全 optional を最低1回ずつ含む』ことも要求する。
// fixture 専用の指定。**これが無いと fixture は黙って痩せる** —— 実際 pos.agg は
// 既存 fixture に1件も無く、fixtures だけを見るゲートは修正前でも緑だった (2026-08-24 実測)。
const wantCoverage = argv.includes('--coverage');
const target = argv.find((a) => !a.startsWith('--')) || path.join(HERE, 'fixtures');
const problems = [];

// --- schema.json ---
if (!fs.existsSync(SCHEMA)) {
  console.error('FATAL: ' + SCHEMA + ' が無い。SimCh.schemaJson() の出力を保存すること');
  process.exit(1);
}
const schema = JSON.parse(fs.readFileSync(SCHEMA, 'utf8'));
const declared = new Map();   // ch -> Set(field)
for (const [ch, spec] of Object.entries(schema.channels || {})) {
  declared.set(ch, new Set([...(spec.required || []), ...(spec.optional || [])]));
}
// 全行が持つ共通フィールド。チャンネル毎に宣言しない
const COMMON = new Set(['t', 'ch']);

// --- 1. 解析側が宣言外を読んでいないか ---
for (const [ch, fields] of Object.entries(CONSUMED)) {
  const d = declared.get(ch);
  if (!d) {
    problems.push(`CONSUMED に居る ch="${ch}" が schema.json に無い`);
    continue;
  }
  for (const f of fields) {
    if (!d.has(f) && !COMMON.has(f)) {
      problems.push(`stats.mjs が読む ${ch}.${f} が schema.json で宣言されていない`);
    }
  }
}

// --- 2. トレースが宣言外を書いていないか ---
function walk(dir, out) {
  if (!fs.existsSync(dir)) return out;
  const st = fs.statSync(dir);
  if (st.isFile()) { if (dir.endsWith('.jsonl')) out.push(dir); return out; }
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    walk(path.join(dir, e.name), out);
  }
  return out;
}
const files = walk(target, []);
let scannedLines = 0;
const unknownSeen = new Set();
const seenPairs = new Set();   // --coverage 用: 実際に現れた ch.field
for (const f of files) {
  const { events } = parseTrace(fs.readFileSync(f, 'utf8'));
  for (const e of events) {
    scannedLines++;
    const d = declared.get(e.ch);
    if (!d) {
      const key = 'ch:' + e.ch;
      if (!unknownSeen.has(key)) {
        unknownSeen.add(key);
        problems.push(`トレースに未宣言のチャンネル ch="${e.ch}" がある (${path.basename(f)})`);
      }
      continue;
    }
    for (const k of Object.keys(e)) {
      if (COMMON.has(k)) continue;
      if (d.has(k)) { seenPairs.add(e.ch + '.' + k); continue; }
      const key = e.ch + '.' + k;
      if (unknownSeen.has(key)) continue;
      unknownSeen.add(key);
      problems.push(`トレースに未宣言のフィールド ${key} がある (${path.basename(f)})`);
    }
  }
}

// --- 3. Java と JS の parseSection が同じ答えを出すか ---
let goldenChecked = 0;
if (fs.existsSync(GOLDEN) && fs.existsSync(CASES)) {
  const golden = JSON.parse(fs.readFileSync(GOLDEN, 'utf8'));
  // Java 側と同じ区切り方。JS の split は末尾の空要素を残す（Java は limit=-1 で揃えてある）
  const cases = fs.readFileSync(CASES, 'utf8').split(/\r?\n---\r?\n/).map((c) => c.trim());
  if (cases.length !== golden.length) {
    problems.push(`golden のケース数 ${golden.length} と cases.txt の ${cases.length} が違う`);
  } else {
    for (let i = 0; i < cases.length; i++) {
      const mine = parseSection(cases[i]);
      const a = JSON.stringify(mine);
      const b = JSON.stringify(golden[i]);
      if (a !== b) {
        problems.push(`section-parse ケース${i}: JS と golden(Java) が食い違う\n    JS    : ${a}\n    golden: ${b}`);
      }
      goldenChecked++;
    }
  }
} else {
  problems.push('section-parse.golden.json / cases.txt が無い（SimChSchemaTest が期待値を出す）');
}

// --- 4. (--coverage) 検査対象が宣言を全部踏んでいるか ---
// **ゲートが空振りしないことの検査。** 宣言に在るのに fixture に1回も出ないフィールドは、
// そのフィールドについて何も検査されていないのと同じ。落として気づかせる。
if (wantCoverage) {
  const uncovered = [];
  for (const [ch, fields] of declared) {
    for (const f of fields) {
      if (!seenPairs.has(ch + '.' + f)) uncovered.push(ch + '.' + f);
    }
  }
  if (uncovered.length) {
    problems.push('--coverage: 検査対象に1回も現れないフィールドがある (そのぶんゲートは空振りする): '
      + uncovered.join(', '));
  }
}

// --- 結果 ---
if (problems.length) {
  console.error('スキーマのズレを検出:');
  for (const p of problems) console.error('  - ' + p);
  console.error('');
  console.error('直し方: **SimCh が形の真実源**。SimCh を直し、SimCh.schemaJson() の出力を');
  console.error('simlab/schema.json へ保存し、stats.mjs の CONSUMED を実態に合わせる。');
  process.exit(1);
}
console.log(`schema OK — トレース ${files.length} 本 / ${scannedLines} 行、`
  + `CONSUMED ${Object.keys(CONSUMED).length} ch、section-parse ${goldenChecked} ケース`
  + (wantCoverage ? `、coverage ${seenPairs.size} 組` : ''));
