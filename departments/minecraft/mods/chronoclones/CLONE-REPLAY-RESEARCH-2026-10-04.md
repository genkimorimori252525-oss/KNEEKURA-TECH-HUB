# Chronoclones clone replay research — 2026-10-04

## 1. Research question

Recover the useful engineering ideas behind Chronoclones' clones for KNEEKURA without changing
game code: how player behavior is represented, scheduled, replayed, persisted, bounded, multiplied,
and exposed to normal Minecraft interaction semantics.

This is a **targeted subsystem study**, not a whole-MOD completion claim.

## 2. Evidence labels

- **AUTHOR_CLAIM** — behavior explicitly described by the author/project/release notes.
- **DIRECT_METADATA** — exact distribution/version metadata observed on the release page.
- **INFERENCE** — engineering conclusion derived from several reported behaviors; useful but not a
  class-level fact.
- **UNKNOWN** — not established without source, bytecode, or a bounded runtime observation.

A project page saying clones "mimic real players" is strong behavioral evidence, but it does not by
itself prove that the Forge implementation subclasses/uses `FakePlayer`.

## 3. Track pins

### ANCHOR

DIRECT_METADATA:

- Minecraft 1.20.1
- Forge
- Chronoclones 1.1
- CurseForge project `1625743`
- file `8986915`
- `chronoclones-1.20.1-forge-1.1.0.jar`
- 2026-09-27
- client + server
- MIT advertised by the project page

### FRONTIER

DIRECT_METADATA:

- Minecraft 26.2
- NeoForge
- Chronoclones 1.1
- file `8986919`
- `chronoclones-26.2-neoforge-1.1.0.jar`
- 2026-09-27

The matching release number and changelog do not prove identical compiled implementation between
tracks.

## 4. Player-visible feature map

| Surface | Evidence-backed behavior | Basis | Engineering interpretation |
|---|---|---|---|
| Recording | Chrono Recorder starts/stops a recording | AUTHOR_CLAIM | There is a bounded routine-capture lifecycle |
| Playback origin | Chrono Anchor plays a recording | AUTHOR_CLAIM | Playback is owned/hosted by an anchor-like controller |
| Preview | Chrono Goggles preview nearby recordings | AUTHOR_CLAIM | Routine geometry/state has a client-visible representation |
| Movement | Physical movement is recorded/replayed | AUTHOR_CLAIM | Routine contains temporal pose/motion information or equivalent commands |
| Blocks | Break/place and generic block interaction | AUTHOR_CLAIM | Replay has discrete world-action events beyond motion |
| Inventories | Move items; crafting; villager trade; enchanting/anvil | AUTHOR_CLAIM | Replay crosses menu/container and transaction semantics |
| Entities | Attack/kill, shear/feed and other mob interaction | AUTHOR_CLAIM | Replay invokes entity/player interaction semantics |
| Multiplicity | Splitter adds clones | AUTHOR_CLAIM | One routine can have multiple concurrent executors |
| Speed | Accelerator makes playback faster; 1.1 stacks to 3 / 4x speed | AUTHOR_CLAIM | Routine clock/scheduler can be time-scaled |
| Rotation | 1.0 added keybinds for rotating recordings | AUTHOR_CLAIM | Recorded coordinates/actions are transformable relative to placement |
| Redstone | 0.9 added anchor start/stop and comparator status | AUTHOR_CLAIM | Playback controller exposes external lifecycle/status control |
| Persistence | 1.1 clones resume where they left off after reload | AUTHOR_CLAIM | Runtime execution progress is persistent |
| Inventory persistence | 1.1 fixed held item/ammo loss on save/unload/edit | AUTHOR_CLAIM | Clone inventory/equipment is persistent runtime state |
| Tool semantics | 1.1 fixed durability loss and Exact rules for used tools | AUTHOR_CLAIM | Replayed use mutates real item state and has matching policy |
| XP semantics | 1.1 fixed Silk Touch XP and large clone XP display | AUTHOR_CLAIM | Clone execution carries XP-related state/effects |
| Spatial sandbox | `maxRadius`; 1.1 fixed actions outside it | AUTHOR_CLAIM | Actions are constrained by anchor-relative spatial policy |
| Action budget | `maxActionsPerTick`, `maxActionTicks`, `maxActions` | AUTHOR_CLAIM | Scheduler has explicit throughput and duration limits |
| Recording budget | `maxRecordingTicks` | AUTHOR_CLAIM | Capture is bounded independently of action count |
| PvP policy | `allowPvp`; 1.1 fixed PvP-off damage | AUTHOR_CLAIM | Replayed player-like actions pass through an explicit safety policy |
| Privacy | `gogglesShowOthers`; 1.1 fixed leaking other routines | AUTHOR_CLAIM | Routine visibility has ownership/privacy filtering |
| Concurrent conflicts | author warns multiple clones can cause odd behavior/rejections on same target | AUTHOR_CLAIM | Replay is not guaranteed to produce identical outcomes when world preconditions race |

## 5. Recovered architecture

### 5.1 The useful mental model: timeline + actions, not Mob AI

**INFERENCE.** The public contract exposes four independent limits:
`maxRecordingTicks`, `maxActions`, `maxActionsPerTick`, and `maxActionTicks`.
That shape is much more consistent with a routine timeline plus scheduled discrete actions than with
ordinary pathfinding/Goal selection.

A robust transferable representation would therefore separate:

1. **continuous/tick state** — position, orientation, locomotion/pose or equivalent;
2. **discrete actions** — use/break/place/attack/menu transaction/etc.;
3. **runtime cursor** — current routine tick/action index;
4. **in-flight action state** — long-running action progress;
5. **executor-owned state** — inventory/equipment/ammo/XP and policy state.

This is a design recovery, not an assertion of Chronoclones' exact serialized classes.

### 5.2 Long actions require a state machine independent of routine length

AUTHOR_CLAIM: 1.1 fixed "long actions never finishing in short routines."

**INFERENCE.** A replay engine should not treat an action as a fire-and-forget event solely keyed to
the routine's current tick. Actions such as breaking, menu operations, or other multi-tick work need
a lifecycle such as:

`READY -> STARTED -> RUNNING -> COMPLETED / FAILED / TIMED_OUT`

with the routine clock and action lifecycle coordinated but not conflated. `maxActionTicks` is a
natural watchdog boundary.

### 5.3 Player-semantic execution is the core trick

AUTHOR_CLAIM: the project explicitly warns that clones **mimic real players**, and the supported
surface includes villagers, crafting, anvils/enchanting, blocks and mob interactions.

**INFERENCE.** The reusable idea is to funnel replay through a **player-semantic interaction
facade** instead of writing clone-specific logic for every target. On Forge 1.20.1,
`FakePlayer` is an obvious candidate mechanism, but **Chronoclones' actual use of FakePlayer is
UNKNOWN** until the 1.20.1 bytecode/source is inspected.

For KNEEKURA, preserve that distinction:

- technique: player-context action execution;
- possible Forge implementation: `FakePlayer` or another player-like actor;
- Chronoclones class identity: unknown.

### 5.4 Anchor-relative routines make recordings portable

AUTHOR_CLAIM: recordings play from an Anchor, have a max distance from that Anchor, can be nudged
(the 0.9 preview fix references nudging), and can be rotated (1.0 release note).

**INFERENCE.** Store routine geometry in a local coordinate frame and apply an Anchor transform at
execution/preview time. Discrete target positions/directions must use the same transform as movement.
This is substantially more reusable than storing only absolute world coordinates.

A KNEEKURA implementation should version the transform contract explicitly:
origin, rotation, optional mirror policy, and the transformation of block faces/look vectors.

### 5.5 Persistence must serialize execution state, not only the routine

AUTHOR_CLAIM: 1.1 adds resume-after-reload and fixes held-item/ammo loss on
save/unload/edit.

**INFERENCE.** Persist at least these conceptual domains independently:

- immutable or versioned routine definition;
- current playback cursor/clock;
- in-flight action identity/progress;
- clone inventory/equipment/ammo;
- clone XP and other state needed by supported transactions;
- anchor/controller state, upgrades and fuel/charge;
- ownership and policy state.

This avoids the classic bug where the world reloads the routine but restarts/forgets the actor state.

### 5.6 Inventory is real mutable execution state

The release notes establish that clone tools lose durability, held items/ammo survive lifecycle
events, hoppers could previously fill **inactive clone inventories**, and Exact item rules had to be
fixed for used tools.

Transferable lessons:

- do not model equipment as render-only snapshots;
- separate **item identity matching** from mutable wear/durability;
- gate automation capabilities when an executor is inactive;
- save inventory changes transactionally with playback/controller state where practical;
- define what happens when required items are missing instead of silently diverging.

The exact Forge capability/container classes used by Chronoclones remain UNKNOWN.

### 5.7 Multi-clone replay is a concurrency problem

AUTHOR_CLAIM: the author warns that several clones interacting with the same thing can produce
rejections or strange results.

This is a valuable design clue. A recorded action is an **intent**, while successful replay depends
on current world preconditions. Two clones may both have a valid recorded intent but race for the
same inventory slot, block, villager trade, entity, or item.

KNEEKURA should therefore make failure semantics explicit:

- precondition check;
- attempt;
- outcome classification;
- retry/skip/abort policy;
- bounded retries;
- optional conflict key/lease for high-contention resources.

Do not promise bit-for-bit deterministic world outcomes from deterministic input routines.

### 5.8 Scheduler controls are also safety controls

The public config provides four independent bounds:

- `maxRecordingTicks`
- `maxActions`
- `maxActionsPerTick`
- `maxActionTicks`

and spatial `maxRadius`.

That is a strong reusable pattern: bound **input size, per-tick throughput, individual task duration,
and spatial authority** separately. The 1.1 fixes for out-of-radius actions and long actions show
why each boundary needs enforcement at the actual execution point, not only at recording/edit time.

### 5.9 Accelerator/Splitter should modify scheduling, not duplicate logic

AUTHOR_CLAIM: Accelerator increases replay speed; Splitter adds clones; 1.1 caps each upgrade type
at three and allows Accelerator to reach 4x.

**INFERENCE.** A clean architecture keeps the routine definition stable while deriving an execution
plan from controller upgrades:

- clock multiplier / number of logical steps eligible per world tick;
- executor multiplicity;
- shared controller policy/budgets.

This prevents "fast clone" and "extra clone" from becoming separate behavior implementations.

### 5.10 Client/server and ownership boundary

DIRECT_METADATA: the mod is required on client and server.

AUTHOR_CLAIM: goggles preview routines; `gogglesShowOthers` controls whether other players'
routines are visible; `allowPvp` gates clone attacks on players.

**INFERENCE.** There is necessarily a meaningful client/server synchronization boundary for
preview/UI and authoritative world execution, but packet names, trust model, and exact
server-authoritative fields are UNKNOWN. KNEEKURA should keep playback mutations server-owned and
treat preview/editor input as requests.

## 6. Release-history clues

### 0.9.0 beta

- redstone start/stop for Anchors;
- comparator output by status;
- fixed items disappearing from an empty Anchor;
- fixed wrong item acceptance in fuel/upgrade slots;
- fixed preview flicker while nudging;
- improved dedicated-server stability.

### 1.0

- keybinds for rotating recordings;
- berry-picking clone fix;
- refactor for multi-loader/version releases.

### 1.1

The 1.1 repair batch is particularly informative because it crosses subsystem boundaries:

- persistence/resume;
- inventory/ammo/durability;
- recording lifecycle;
- enchanting and item matching;
- PvP safety;
- action timeout/completion;
- spatial containment;
- low-charge scheduler behavior;
- logout lifecycle;
- routine privacy;
- inactive inventory automation;
- XP semantics.

This is evidence of a **stateful execution engine**, not merely a visual ghost replay.

## 7. Transferable technology map for KNEEKURA

Priority candidates recovered from this study:

1. **Routine IR** — versioned timeline + typed discrete actions.
2. **Anchor-local coordinate system** — rebase/rotate one routine without rerecording.
3. **Player-semantic actor facade** — execute vanilla interactions through a player-like context.
4. **Action adapter registry** — typed handlers for block/entity/menu/transaction actions.
5. **Serializable execution cursor** — resume from exact logical progress after reload.
6. **Serializable actor state** — inventory/equipment/ammo/XP separate from visual clone state.
7. **Long-action state machine** — explicit completion/failure/timeout.
8. **Four-dimensional budget** — recording length, total actions, per-tick actions, per-action time.
9. **Spatial authority sandbox** — validate target at action execution against anchor radius.
10. **Conflict-aware outcomes** — precondition + result + retry/skip/abort, not blind replay.
11. **Inactive capability gating** — external automation must not mutate a dormant executor.
12. **Upgrade-derived execution plan** — speed/multiplicity transform scheduling, not routine data.
13. **External lifecycle API** — redstone-like start/stop/status is a useful generic control seam.
14. **Ownership/privacy policy** — preview visibility and PvP need explicit owner-aware checks.
15. **Lifecycle hygiene** — logout/unload/edit/save are first-class transitions with cleanup/save hooks.

## 8. What this is *not*

Chronoclones should not be used as evidence for sophisticated autonomous decision AI:

- no public evidence here of Goal/Brain planning;
- no evidence of autonomous route planning beyond reproducing recorded player movement;
- no evidence of adaptive strategy selection.

Its value is different: it is a compact case study in **record -> serialize -> transform ->
schedule -> execute as a player-like actor -> persist -> repeat**.

That makes it especially useful as a deterministic baseline beside KNEEKURA's future Goal/Brain,
motion-trace and AI-observation work.

## 9. Exact unresolved questions

Source/bytecode inspection is required to answer these safely:

- Does ANCHOR use Forge `FakePlayer`, a custom Player subclass, a Mob, or another actor?
- Exact package/class graph and loader abstraction boundaries.
- Exact routine/action serialized schema and storage location.
- Whether movement is pose sampling, input replay, target interpolation, teleport correction, or a mix.
- How block breaking progress is represented.
- How menu/container actions identify slots and validate state.
- How target entities are identified across unload/reload.
- Exact inventory/XP persistence schema.
- Exact networking packets and ownership validation.
- Exact low-charge scheduling/fuel formula.
- Exact collision/path obstruction behavior when the world has changed.
- Exact retry/failure semantics.
- Threading model and performance scaling with many clones.
- Cross-loader implementation equivalence.

## 10. Acquisition/provenance boundary

The ANCHOR CurseForge release is precisely identified, but the JAR bytes were not acquired by the
available analysis runtime. Direct internet access from the container was unavailable, and the
public project pages do not expose a linked source repository.

Accordingly:

- raw/decompiled code is not committed;
- no class name is invented;
- no SHA-256 is invented;
- the release metadata and author behavior/changelog are retained as locators;
- class-level statements remain UNKNOWN.

## 11. Sources

Retrieved 2026-10-04 unless noted.

- CurseForge project: https://www.curseforge.com/minecraft/mc-mods/chronoclones
- ANCHOR 1.1 / Forge 1.20.1 file 8986915:
  https://www.curseforge.com/minecraft/mc-mods/chronoclones/files/8986915
- FRONTIER 1.1 / NeoForge 26.2 file 8986919:
  https://www.curseforge.com/minecraft/mc-mods/chronoclones/files/8986919
- Modrinth project/docs:
  https://modrinth.com/mod/chronoclones
- 0.9.0 beta release notes:
  https://modrinth.com/mod/chronoclones/version/0.9.0b
- 1.0 release notes:
  https://modrinth.com/mod/chronoclones/version/DmozM0j9
- CurseForge legacy issue surface:
  https://legacy.curseforge.com/minecraft/mc-mods/chronoclones/issues

No suitable Reddit thread with version-specific, reviewable technical claims was found in the
bounded search. That absence is recorded rather than replaced by unrelated community discussion.
