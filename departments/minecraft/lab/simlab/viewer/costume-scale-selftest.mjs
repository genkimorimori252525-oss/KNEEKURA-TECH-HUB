#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const YSM_JS = path.join(HERE, 'ysm.js');
const source = fs.readFileSync(YSM_JS, 'utf8');
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(source, sandbox, { filename: YSM_JS });

const Y = sandbox.YSM;
let failures = 0;
let checks = 0;

function fail(message) {
  failures++;
  console.error('SELFTEST FAIL: ' + message);
}

function check(condition, message) {
  checks++;
  if (!condition) fail(message);
}

function checkNear(actual, expected, message) {
  checks++;
  if (actual.length !== expected.length) {
    fail(`${message}: 長さが違う (${actual.length} != ${expected.length})`);
    return;
  }
  for (let i = 0; i < actual.length; i++) {
    if (Math.abs(actual[i] - expected[i]) > 1e-6) {
      fail(`${message}: index ${i} が違う (${actual[i]} != ${expected[i]})`);
      return;
    }
  }
}

function bone(name) {
  return { name, r: [0, 0, 0], t: [0, 0, 0], parent: -1 };
}

function scaleOf(matrix) {
  return Math.hypot(matrix[0], matrix[1], matrix[2]);
}

check(Y && typeof Y.collectCostumeBones === 'function', 'YSM.collectCostumeBones が公開されていない');
check(Y && typeof Y.poseBones === 'function', 'YSM.poseBones が公開されていない');
check(!source.includes('\u0008'), 'ysm.js に U+0008 (誤った \\b) が混入している');

if (Y) {
  const costumeVars = [
    'shangyi', 'qunzi', 'shoutao', 'wazi', 'xiezi',
    'weijin', 'kouzhao', 'maozi', 'naian',
  ];
  const excludedVars = ['yan', 'yantong', 'zui', 'bianzi', 'qianfa', 'jian'];
  const bones = {};
  for (const name of costumeVars) bones['costume_' + name] = { scale: `1-v.roaming.${name}` };
  for (const name of excludedVars) bones['excluded_' + name] = { scale: `1-v.roaming.${name}` };
  bones.nested_keyframe = { scale: { '0.0': [1, 1, 1], '1.0': ['v.roaming.qunzi', 1, 1] } };
  bones.similar_prefix = { scale: 'vXroamingXshangyi' };
  bones.longer_identifier = { scale: 'v.roaming.shangyi_alt' };
  bones.fixed_scale = { scale: [1, 1, 1] };

  const actual = [...Y.collectCostumeBones({ test: { bones } })].sort();
  const expected = [...costumeVars.map((name) => 'costume_' + name), 'nested_keyframe'].sort();
  check(JSON.stringify(actual) === JSON.stringify(expected),
    `衣装ボーンの抽出結果が違う: ${JSON.stringify(actual)}`);

  const dress = bone('dress');
  const pinned = new Set(['dress']);
  const baseHidden = new Map([['dress', { s: [0, 0, 0] }]]);
  const revealAndMove = new Map([['dress', { r: [0, 0, 30], p: [16, 0, 0], s: [1, 1, 1] }]]);
  const moveOnly = new Map([['dress', { r: [0, 0, 30], p: [16, 0, 0] }]]);
  const protectedHidden = Y.poseBones([dress], [
    baseHidden,
    { map: revealAndMove, weight: 1, scaleWeight: 1 },
  ], { pinScale: pinned });
  const expectedHidden = Y.poseBones([dress], [
    baseHidden,
    { map: moveOnly, weight: 1, scaleWeight: 1 },
  ], { pinScale: pinned });
  checkNear(protectedHidden, expectedHidden,
    '衣装 scale を止めてもアクションの rotation/position は維持されるべき');
  check(scaleOf(protectedHidden) < 1e-6,
    '待機下地が隠した衣装をアクション scale が再表示している');

  const baseVisible = new Map([['dress', { s: [1, 1, 1] }]]);
  const hideAction = new Map([['dress', { s: [0, 0, 0] }]]);
  const protectedVisible = Y.poseBones([dress], [
    baseVisible,
    { map: hideAction, weight: 1, scaleWeight: 1 },
  ], { pinScale: pinned });
  check(Math.abs(scaleOf(protectedVisible) - 1) < 1e-6,
    '待機下地が表示した衣装をアクション scale が消している');

  const weapon = bone('weapon');
  const unprotected = Y.poseBones([weapon], [
    new Map([['weapon', { s: [1, 1, 1] }]]),
    { map: new Map([['weapon', { s: [0, 0, 0] }]]), weight: 1, scaleWeight: 1 },
  ], { pinScale: pinned });
  check(scaleOf(unprotected) < 1e-6,
    '衣装以外のボーンまでアクション scale が止められている');
}

if (failures > 0) {
  console.error(`costume scale selftest FAILED (${failures} failures / ${checks} checks)`);
  process.exit(1);
}
console.log(`costume scale selftest OK (${checks} checks)`);
