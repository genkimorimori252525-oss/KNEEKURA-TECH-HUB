# Runtime network companion

KNEEKURA-LAB は Forge 1.20.1 `SimpleChannel` の runtime send / receive を、
arena JSONL とは別の `.net.jsonl` companion に記録する。

## Why separate

arena trace の writer は server JVM、clientbound packet の receive は client JVM。

両者を無理に 1 本の JSONL へ書くと、別processが同じfileを同時に触ることになる。
pose / palette と同じく **process-local companion** として分離する。

## Enablement

通常プレイでは `tlm.sim.scenario` が無いため writer は完全に停止する。

client 側でも network receive を記録したい場合は、client JVM にも同じ SimLab property を渡す。

推奨:

```text
-Dtlm.sim.scenario=tank
-Dtlm.sim.run=20260827-netdiag
-Dtlm.sim.out=<shared-or-known-output-root>
```

`tlm.sim.run` を server/client の両方へ渡すと、main trace と network companion を hard identity で照合できる。

## Output

既定:

```text
<gamedir>/simlab-out/
  <scenario>/
    _network/
      <run>/
        client-<pid>-<stamp>.net.jsonl
        dedicated_server-<pid>-<stamp>.net.jsonl
```

`-Dtlm.sim.net.out=...` があれば network companion だけ別rootへ出せる。

## Format v1

先頭行:

```json
{"v":1,"ch":"net_meta","scenario":"tank","run":"20260827-netdiag","bound":true,"physicalSide":"CLIENT","pid":"1234","startedGameTime":1000}
```

event:

```json
{"v":1,"ch":"net","seq":1,"stage":"send","physicalSide":"DEDICATED_SERVER","gameTime":1012,"thread":"Server thread","channel":"touhou_little_maid:reimu_net","packet":"com.example.ReimuSpellCardMolangPacket","packetSimple":"ReimuSpellCardMolangPacket","direction":"PLAY_TO_CLIENT","payload":{"x":0.0,"y":65.0,"z":0.0,"molangExpression":"(v.wuqi = 1)"}}
```

receive:

```json
{"v":1,"ch":"net","seq":4,"stage":"receive","physicalSide":"CLIENT","gameTime":1013,"thread":"Render thread","packet":"com.example.ReimuSpellCardMolangPacket","packetSimple":"ReimuSpellCardMolangPacket","direction":"PLAY_TO_CLIENT","payload":{"x":0.0,"y":65.0,"z":0.0,"molangExpression":"(v.wuqi = 1)"}}
```

receive 側で channel が取れない場合は無理に推測せず省略する。
packet class + direction は静的network graphの registration と照合できる。

### payload snapshot

packet が public instance field を持つ場合は、観測時点の安全な浅い snapshot を `payload` に付ける。

対象は最大24 field、型は String / boolean / number / char / enum / UUID のみ。String は2048文字で打ち切る。
private field、static field、array、collection、未知object、nested objectは読まない。methodも1つも呼ばない。

たとえば `ReimuSpellCardMolangPacket.molangExpression` は public String なので send/receive の両方へ残る。
これにより後段は packetが運んだMolang式を推測ではなくpayload evidenceとして扱える。

## Semantic rows

同じ companion には、network境界の後で起きた診断上のmilestoneを `ch:"net_semantic"` として追加できる。
`seq` は send/receive と共有するので、1process内の順序がそのまま残る。

handler実行:

```json
{"v":1,"ch":"net_semantic","seq":5,"kind":"reimu_spellcard_handler","physicalSide":"CLIENT","gameTime":1013,"thread":"Render thread","payload":{"x":0.0,"y":65.0,"z":0.0,"molangExpression":"(v.wuqi = 1)"}}
```

YSM command dispatch:

```json
{"v":1,"ch":"net_semantic","seq":6,"kind":"ysm_molang_command_dispatched","physicalSide":"CLIENT","gameTime":1015,"thread":"Render thread","payload":{"molangExpression":"(v.wuqi = 1)","command":"ysmclient molang execute (v.wuqi = 1)"}}
```

semantic payloadも packet payload と同じ scalar-only sanitizer を通す。
`kind` は観測点の意味であり、send/receive の `stage` と混ぜない。

重要: `ysm_molang_command_dispatched` は client の `sendCommand()` 呼び出しが例外なく戻った証拠。
YSM内部で最終的に変数が評価・適用されたことまでを意味しない。

### Pre-dispatch diagnostic anchor

正式M6検証のため、SimLab時だけ `sendCommand()` の直前に次の内部semanticを置く:

```json
{"v":1,"ch":"net_semantic","kind":"ysm_molang_command_pre_dispatch","payload":{"molangExpression":"(v.wuqi = 1)","command":"ysmclient molang execute (v.wuqi = 1)"}}
```

これは「今から `sendCommand` へ入る」の証拠だけで、成功ではない。KNEEKURA-LABはこの行が
durableに書かれた直後、対象Reimuのexact scalar stateをbeforeとして採る。

### M6 state rows

actual M3 handler contextがあり、pre-dispatch exact state、M5 `handledByClient=true`、
post-M5 exact stateを同一entity/candidateで結べた場合だけ正式M6を出す。

状態がcommandによって実際に変わったと確認できた場合:

```json
{"v":1,"ch":"net_semantic","kind":"ysm_molang_state_applied","payload":{"variable":"wuqi","before":0.0,"after":1.0,"handledByClient":true,"exactVariableIdentity":true,"evidenceLevel":"E2_ACTUAL_PRE_POST_TRANSITION"}}
```

post-stateは一致したが、pre-state不在・同値・candidate identity不一致などでcommandによる変化を
証明できない場合は弱い行だけを残す:

```json
{"v":1,"ch":"net_semantic","kind":"ysm_state_correlated","payload":{"variable":"wuqi","observedValue":1.0,"evidenceLevel":"E2_CORRELATED_POSTSTATE"}}
```

`ysm_state_correlated` はM6ではない。M5からM6を推測補完しない。

## Identity

main arena trace の `meta.run` と companion の `net_meta.run` を比較する。

- 同一run: 強い一致
- companion run = `unbound`: 自動採用しない
- scenario不一致: reject
- gameTime overlapなし: reject

`unbound` は client JVM に `tlm.sim.run` が渡っていない場合に発生する。
typeや時刻が近いだけで別runへ吸着させないための保守的な設計。

## Failure policy

network trace は観測機能であり、ゲーム本体より弱い。

- writer open失敗 → ログを1回出して停止
- write失敗 → companionだけ停止
- exceptionをpacket処理へ投げ返さない
- eventごとにflushし、クラッシュ直前のsend/receiveを残す

## Reader

`simlab/network-companion.mjs` が v1 の構造を検証する。

```bash
npm test
```

で malformed stage / sequence / meta を回帰検証する。
