# Vanilla debug infrastructure — exact 1.20.1 correction

Evidence: DebugPackets, Path and the three debug renderers in [the exact bytecode ledger](ANCHOR-BYTECODE-LEDGER-2026-10-03.json) and the complete scoped Foundation Map.

## Exact owners and version boundary

The actual owner is `net/minecraft/network/protocol/game/DebugPackets`.

This 1.20.1 class map contains **no** `PathfindingDebugPayload`, `GoalDebugPayload` or `BrainDebugPayload` owners. Earlier signature-based notes referring to those typed payload classes were cross-version vocabulary and must not be used as 1.20.1 hook evidence.

The actual 1.20.1 data owners include:

- `GoalSelectorDebugRenderer$DebugGoal`;
- `BrainDebugRenderer$BrainDump`;
- `ClientboundCustomPayloadPacket` with the older channel/buffer transport;
- Path's optional debug node arrays.

Use exact bytecode/API locators for this generation. A modern typed custom-payload record is not a backport-compatible class merely because its concept is useful.

## Dormant senders

The inspected bodies show:

- `sendPathFindingPacket(Level, Mob, Path, float)`: immediate return;
- `sendEntityBrain(LivingEntity)`: immediate return;
- `sendGoalSelector(Level, Mob, GoalSelector)`: side check followed by return, with no goal payload emission.

The existence of names, serializers, synthetic helper methods and renderers does not prove production transport is active. PathFinder's inspected body also does not populate Path debug arrays with `setDebug()`.

## Renderer and authority boundaries

PathfindingRenderer, GoalSelectorDebugRenderer and BrainDebugRenderer are client presentation. Open/closed/cost/type display is useful vocabulary but does not supply server evidence by itself.

LAB must retain exact server source observations and immutable identity before deriving a local client overlay or packet. Overlay OFF adds no hidden drawing loop; raw Cardinal evidence must not silently include a derived overlay. No particles, entities or blocks are spawned to draw diagnostic lines.

Re-enabling a Vanilla debug sender through a MOD is a separate instrumentation adapter, with its own exact source/loader identity and observer-effect measurement. Existing Moonlight research is a precedent, not proof its current source matches this ANCHOR or supplies LAB evidence semantics.

## Proven hook surface

Read-only selected-subject snapshots can use the verified Goal/Brain/Path/control APIs. A deep path recorder must observe the original search before evaluator cleanup. Exact Goal/Behavior lifecycle calls and Sensor/candidate population require separately armed original-invocation hooks; never rerun them for the debugger.

Loaded-hook, client overlay and representative native acceptance remain pending. No static debug discovery is labelled a runtime PASS.
