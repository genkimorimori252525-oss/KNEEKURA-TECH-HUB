# Bedrock Wither Reconstruction Implementation Plan

**Goal:** Minecraft Java 1.20.1 + Forge で、Bedrock Edition ウィザーの観測可能な戦闘挙動を独立Entityとして再現し、KNEEKURA Tankで差分検証できる状態にする。

**Design:** `departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/`

## Phase 0 — Evidence freeze

- [x] official exposed Wither JSON/unique behavior/special goal sourcesを記録する
- [x] Bedrock Wiki / Minecraft Wiki / community reportsを実装権威と分離する
- [x] Java 1.20.1 `WitherBoss` を継承ベースではなく比較対象とする
- [x] 未確定の数値を `TBD_MEASURE` として固定する
- [x] [Bedrock実機観測scenario v1](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/MEASUREMENT-SCENARIOS-v1.md)を作る（2026-10-03 PREPARED / NOT EXECUTED。実行manifestの固定・観測・受入は未実施）

## Phase 1 — Standalone Forge boss skeleton

Use the canonical product workspace at `deliverables/minecraft/bedrock-wither/mod/`. The root `deliverables/` boundary keeps product code separate from TECH HUB research/Python infrastructure; do not place distributable MOD code under `departments/` or `src/kneekura_tech_hub/`.

Initial classes:

```
BedrockWitherMod
ModEntities
BedrockWitherEntity
BedrockWitherState
BedrockWitherStateMachine
BedrockWitherThreatLedger
BedrockWitherFlightController
BedrockWitherAttackController
BedrockWitherDashController
BedrockWitherDestructionController
BedrockWitherRenderer
BedrockWitherModel
```

Tasks:
- [ ] entity registration and attributes
- [ ] boss event/bar
- [ ] synced state + NBT
- [ ] server/client separation
- [ ] basic flight controller
- [ ] debug read-only snapshot
- [ ] vanilla Wither remains untouched

## Phase 2 — Targeting and phase 1

- [ ] implement bounded highest-damage threat ledger
- [ ] implement target validity/search range
- [ ] independent side-head target sync/aim
- [ ] explicit normal/dangerous skull spawn path
- [ ] parameterized burst sequencer
- [ ] parameterized reposition/hover controller
- [ ] phase-1 hurt reaction hook
- [ ] no Java Wither passive behavior leakage

## Phase 3 — 50% transition and phase 2

- [ ] exactly-once transition latch
- [ ] transition action timeline
- [ ] difficulty-aware skeleton summon policy
- [ ] projectile immunity
- [ ] dash preparation/target vector
- [ ] bounded dash duration
- [ ] per-tick destruction controller
- [ ] collision/invalid-target termination

## Phase 4 — Bedrock measurement replacement

For each `TBD_MEASURE` constant:
- [ ] define Bedrock reference scenario
- [ ] capture direct evidence
- [ ] retain version/difficulty/setup
- [ ] calculate accepted value/range
- [ ] update source ledger and behavior contract
- [ ] add regression test before changing the implementation constant

Priority measurements:
1. phase-1 burst timing/order
2. health-dependent cadence
3. hurt-reaction destruction
4. 50% transition ordering/summon count
5. dash duration/speed/destruction geometry
6. spawn/death sequences

## Phase 5 — KNEEKURA Tank comparative verification

- [ ] register the MOD workspace in existing Minecraft MOD AI/Tank flow
- [ ] create isolated Wither arena fixture; do not reuse production worlds
- [ ] expose state snapshot through the bounded observer
- [ ] record position/velocity/state/projectile/destruction timelines
- [ ] paired vanilla-Java control
- [ ] paired Bedrock-reconstruction run
- [ ] compare against retained Bedrock reference measurements
- [ ] adversarial scenarios: target loss, projectile spam, unbreakable blocks, reload, lag/tick delay

## Phase 6 — Compatibility layer

Only after behavioral acceptance:
- [ ] optional recipe/spawn replacement mode
- [ ] config to keep vanilla Wither available
- [ ] mod interaction audit
- [ ] performance budget for per-tick destruction
- [ ] optional version-bound Bedrock quirks

## Stop conditions

Do not:
- claim exact Bedrock reproduction from Wiki text alone
- silently inherit Java `WitherBoss` attack/regen/block logic
- widen test tolerances after a failure without a scenario revision
- let dash destruction run without strict bounds
- replace `minecraft:wither` before the standalone boss is accepted
- emulate an apparent Bedrock bug by default without versioned evidence

## Immediate next executable slice

The next coding slice is Phase 1 + the minimum of Phase 2 needed to spawn and inspect the boss:

1. create dedicated Forge 1.20.1 MOD workspace;
2. register independent `bedrock_wither`;
3. implement state enum/state machine shell;
4. implement difficulty health + boss bar;
5. implement basic no-gravity flight;
6. implement threat ledger API;
7. expose debug snapshot;
8. compile + GameTest smoke;
9. connect to Tank only after the standalone build is clean.

No phase-accurate skull cadence or dash dimensions are hardcoded in this slice unless direct measurement is already available.
