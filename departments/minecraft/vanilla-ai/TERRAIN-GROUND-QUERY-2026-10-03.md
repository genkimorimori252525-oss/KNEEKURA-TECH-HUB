# Bounded observer ground query

This slice continues the approved regional malus drill-down. It queries static ground classification for one explicitly selected Mob, using the existing exact session/run/snapshot/process/Arena/selection identity. It does not rerun navigation, `canUse`, neighbor search or `Mob.getPathfindingMalus`.

## Control and evidence

`target <UUID> --terrain-radius 0..3 [--terrain-cells 1..49] [--terrain-millis 1..50]` requests one plane at the Mob's cached block position per selection revision. The default is OFF. Every ordinary selection/clear removes this request. Defaults are 49 cells and 10 ms; the deadline is checked between cells and cannot preempt one custom classifier invocation.

The producer uses `WalkNodeEvaluator.getBlockPathTypeStatic` against a bounded `BlockGetter`. `ServerChunkCache.getChunkNow` reads existing chunks without tickets, load/generation or blocking waits; the cached `LevelChunk.loaded` flag excludes its currently-loading shortcut. BlockEntity access is refused. Missing chunks, unsupported custom classifiers and unavailable cells remain unknown. This call can warm the chunk lookup cache/profiler and execute MOD block/fluid classification callbacks, so zero observer effect is not claimed.

Each available cell separates:

- static ground path type and its cached default type malus;
- the selected Mob's own cached `EnumMap` override, if present;
- effective malus: `NOT_EXPOSED`;
- actual PathFinder evaluation: `NOT_CAPTURED`.

Own overrides are not effective values: inheritance, custom overrides, selected evaluator rules and mount behavior can change the result. Previously retained `PATH_SEARCH_STATE` and `BASE_MALUS_RETURN` remain separate original-invocation evidence. A terrain query never proves that a path search evaluated a cell.

`AI_DECISION` carries `kneekura.terrain-ground-query/v1`, with actual server tick, UUID and Arena epoch. The consumer validates bounded coordinates, unique cells, status/truncation, timestamp and explicit semantics. It exposes observer state and `terrain_ground` retained drill-down, without creating candidate, evaluation or causal claims.

Example retained read:

```text
evidence-decision <UUID> --channel terrain_ground --revision <revision> --arena-epoch <epoch> --start-tick <tick> --end-tick <tick>
```

This reader does not initialize or reingest finalized evidence. Query identity and evidence IDs remain mandatory.

## Source correspondence

`TERRAIN-ANCHOR-BYTECODE-LEDGER-2026-10-03.json` records exact captured class and disassembly hashes for cached Entity position, nonblocking chunk lookup, loaded chunk state and `BlockGetter`. Foundation Map ID: `522cbb565d187f8e1e7b97140206f5ac11e8ca90719528bd661f875f184e34fd`. The existing AI ledger supplies the static ground classifier and `BlockPathTypes`/Mob cached fields. These are development-artifact proofs, not transformed resident-byte attestation.

## Validation boundary

Focused contracts cover default OFF, numeric bounds, reset/fences, deadline/cell truncation, missing cells, cached override preservation and refusal of invented effective/evaluated values. Compilation uses genuine hash-checked Forge dependencies. Native ground-query acceptance and total observer-effect measurement remain pending until a frozen-source run supplies retained evidence.
