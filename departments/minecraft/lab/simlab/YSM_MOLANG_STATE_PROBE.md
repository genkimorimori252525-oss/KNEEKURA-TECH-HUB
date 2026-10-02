# YSM Molang state discovery probe

This document defines the discovery boundary immediately after M5.

Current transport evidence proves:

```text
M0 runtime Molang intent
M1 packet send carries Molang
M2 packet receive carries Molang
M3 Reimu client handler executed
M4 YSM command dispatched
M5 Forge client command consumed
```

M5 does **not** prove that YSM evaluated the expression or applied it to runtime state.

## Probe roles

- `SimYsmObjectWalker`: shared field-only traversal and completeness contract
- `SimYsmGraphScan`: shape/candidate discovery
- `SimYsmScalarProbe`: scalar snapshot and stable before/after diff

The scalar probe deliberately does not assign Molang meaning.

## Safety

Unknown YSM objects are inspected with `Field#get` only.

Allowed container operations are JDK `Map` / `Collection` iteration and `Array` access.
Unknown obfuscated methods are never invoked.

Captured scalar values are limited to:

- String
- boolean / char
- byte / short / int / long
- float / double
- `Map<String, scalar>` values

Primitive arrays remain opaque leaves. Large strings and map keys are clipped at 256 characters and
marked truncated; truncated identities are excluded from stable diff evidence.

## Shared budgets

The object walker is the single source of truth for:

- max depth: 6
- max visited nodes: 40000
- max traversed elements per container: 64

Every probe receives:

- `truncatedContainers`
- `depthBudgetExhausted`
- `visitBudgetExhausted`
- `complete()`

A negative result is conclusive only when `complete=true`.

## Runtime snapshot artifact

The client command:

```text
/tlmsim ysmprobe snapshot
/tlmsim ysmprobe snapshot wuqi-0-a
```

writes a discovery snapshot only when **both** `tlm.sim.scenario` and `tlm.sim.run` are
explicitly set. An unbound client run is rejected instead of being guessed.

Output:

```text
<tlm.sim.out or gamedir/simlab-out>/
  <scenario>/
    _ysmprobe/
      <run>/
        <stamp>-gt<gameTime>-<label>.ysmprobe.json
```

Each artifact contains:

- exact `scenario` and sanitized run identity
- one captured `gameTime` used by both filename and JSON metadata
- target entity id / UUID
- runtime root route (`renderer` first, capability fallback)
- runtime root class
- YSM/TouhouLittleMaid JAR SHA-256 evidence
- scan completeness/budget fields
- scalar records with path, type, value, field name or Map key
- truncation/comparability flags

The renderer-root lookup is shared with `dumpcubes`, so the two probes do not silently inspect
different YSM roots.

Writing this file is only E0 discovery. It never emits a network semantic milestone and never
claims M6.

## Controlled differential probing

The client command:

```text
/tlmsim ysmprobe toggle wuqi
/tlmsim ysmprobe stop
```

uses the same `YsmReimuNaianClientRunner.scheduleSpellCardMolang(...)` route already used by
`SimPoseDump`. It drives:

```text
v.wuqi = 0 -> wait 8 ticks -> snapshot A
v.wuqi = 1 -> wait 8 ticks -> snapshot B
v.wuqi = 0 -> wait 8 ticks -> snapshot C
v.wuqi = 1 -> wait 8 ticks -> snapshot D
```

Each A/B/C/D artifact is the exact snapshot retained in memory for analysis. The analyzer does not
rescan the runtime graph after writing the file.

The maid selected at probe start is pinned for the entire sequence. Every command target and every
A/B/C/D snapshot resolves the YSM root from that same entity, and the sequence summary stores its
entity id / UUID. A newly-nearest Reimu cannot silently replace the observation target mid-run.

The sequence summary is written beside the snapshots:

```text
toggle-<variable>-<stamp>.ysmprobe-sequence.json
```

The pure-JDK `SimYsmToggleAnalyzer` requires the same `stableIdentity` to exist in all four
snapshots and to numerically follow exactly `0,1,0,1`.

- E1: stable candidate follows the complete controlled toggle sequence
- E2: E1 plus exact variable identity, currently exact Map key
  `wuqi`, `v.wuqi`, `variable.wuqi`, or exact field name `wuqi`

Truncated keys/values are not comparable and cannot become E1/E2.

The controlled probe deliberately writes:

```json
"formalM6": false
```

because this direct scheduler discovery is not the same causal run as the real M0-M5 packet path.
It can identify the likely YSM state location, but it cannot by itself prove that a specific
packet/handler/command chain instance applied the state.

## One-command formal M6 acceptance

For a run that has both `tlm.sim.scenario` and `tlm.sim.run` set, keep the target Reimu rendered
and run this client command:

```text
/tlmsim ysmprobe accept wuqi
```

The acceptance flow is intentionally two-stage:

```text
client controlled probe
  0 -> 1 -> 0 -> 1
  -> unique E2 qualification for the exact runtime candidate
  -> send server command with the same Reimu UUID

server SimLab acceptance driver
  -> EntityMaid.sendSpellCardMolang(..., true)
  -> actual packet 0 -> 1 -> 0 -> 1
     spaced 12 ticks apart
  -> M3 handler trace IDs
  -> pre-dispatch state
  -> M5 handledByClient
  -> formal M6 verification
```

The server command root is deliberately separate from the client `/tlmsim` command:

```text
/tlmsimserver m6toggle <reimu-uuid> <variable>
/tlmsimserver m6stop
```

Normally you do not need to type it: `ysmprobe accept` sends it automatically only after the
controlled E2 qualification succeeds. The UUID is taken from the exact maid used for all four
controlled snapshots, so the actual packet phase cannot silently switch to another Reimu.

The server command is registered only when `tlm.sim.scenario` was explicitly supplied, and it is
executable only while `SimLab.ENABLED` is true. Normal play therefore has no acceptance command.

After the actual packet phase, check the client network companion directly:

```text
npm run check:m6 -- <client.net.jsonl> wuqi
```

The checker returns PASS only when one entity has four formal
`ysm_molang_state_applied` observations with:

- `after = 0,1,0,1` in order
- `controlledE2Qualified=true`
- `packetHandlerOrigin=true`
- `handledByClient=true`
- `exactVariableIdentity=true`
- a real `before != after` transition on every row
- four distinct non-empty `packetTraceIds`

`ysm_state_correlated`, M5-only evidence, a repeated trace ID, a missing transition, or an
incomplete sequence does not pass the acceptance check.

## Formal M6 on the actual packet chain

Controlled discovery locates likely state candidates, but formal M6 is produced only from the
actual Reimu runtime causal chain.

The live verifier requires this sequence:

```text
M3 reimu_spellcard_handler
  -> ysm_molang_command_pre_dispatch
       -> exact pre-dispatch YSM scalar snapshot
  -> M5 ysm_client_command_result handledByClient=true
       -> wait 2 ticks
       -> exact post-M5 YSM scalar snapshot
  -> same entity + same exact stable candidate
       before != after
       after == assigned numeric literal
  -> ysm_molang_state_applied   (formal M6)
```

`ysm_molang_command_pre_dispatch` is an internal diagnostic anchor emitted immediately before
`player.connection.sendCommand(...)`. It is **not** command success and is not counted as a
transport milestone.

The current formal verifier intentionally supports only simple one-segment numeric assignments such
as:

```text
v.wuqi = 0
variable.foo = 1.5
```

It fails closed for dotted variables such as `v.roaming.c`, computed right-hand sides, comparisons,
or malformed expressions. A merged command may contain several simple assignments; the final literal
assigned to each supported variable is the expected post-command value.

Before the actual-chain verifier may emit M6, the same run/entity/variable/stable candidate must
already have passed the controlled `0 -> 1 -> 0 -> 1` probe as a **unique E2 candidate**. That
qualification is kept in an in-process registry keyed by:

```text
run + client-level identity + entity UUID + variable + stableIdentity
```

If the controlled probe finds zero E2 candidates or more than one E2 candidate, nothing is qualified.
A client-level replacement (world reconnect/reload) changes the qualification scope, and a process
restart loses the in-memory registry entirely. Both fail closed until the controlled probe is
repeated in the current level.

For each supported variable:

- the candidate must already be controlled-E2-qualified for this run/entity
- the handler coordinates must resolve to one Reimu target within the same 1.5-block selector radius
- pre-dispatch state must have exactly one exact numeric identity candidate
- M5 must report `handledByClient=true`
- post-state must again have exactly one exact candidate matching the assigned literal
- pre/post candidates must have the same `stableIdentity`
- `before` and `after` must differ

If post-state matches but the pre-state is missing, already equal, or comes from a different stable
candidate, only `ysm_state_correlated` is emitted. That weak row is **not M6**.

Positive state evidence does not require a complete whole-graph scan: completeness controls negative
claims, not a directly observed unique positive scalar. An incomplete scan therefore remains marked
in the evidence, but no absence conclusion is drawn from it.

The pre-dispatch semantic also carries `packetHandlerOrigin`. Formal M6 requires it to be exactly
`true`. The Reimu packet handler uses a package-private packet-origin scheduler entrypoint; normal
controlled/direct scheduling is `false`. If packet-origin and direct work are merged into one queued
SPELL_CARD command, provenance is conservatively downgraded to `false`.

Each traced M3 handler also carries a positive `packetTraceId`. The queued pre-dispatch semantic
carries the exact comma-separated `packetTraceIds` that contributed to that command. Formal M6
requires every listed ID to resolve to exactly one non-expired M3 row whose complete expression is
present in the merged command. Missing, malformed, duplicate or stale IDs fail closed. Therefore an
older M3 with the same Molang text cannot be substituted merely because the expression matches.

Therefore the controlled `/tlmsim ysmprobe toggle` route cannot accidentally become formal M6:
it lacks both packet-handler provenance and the required M3 context.

## Artifact separation

Large discovery snapshots belong in the `_ysmprobe/<run>/` artifact directory described above.
Only a small, already-qualified milestone should be copied into the network semantic companion.

The runtime snapshot path does **not** claim M6. Controlled repeated mutation remains required.
