# Ages of Dominion RTS architecture research — 2026-10-04

## 1. Question

What reusable technology does Ages of Dominion contribute to KNEEKURA's Minecraft RTS, unit AI,
worker automation and village-defense work?

This is a source-backed targeted study of the exact upstream revision
`c1e71a021ba88a053a378292c6011cb89828fd36`. It is not a whole-target COMPLETE claim.

Evidence language:

- **DIRECT_OBSERVATION**: visible in the pinned source/diff.
- **AUTHOR_CLAIM**: stated by upstream release/project material.
- **INFERENCE**: engineering lesson derived from source behavior.
- **UNKNOWN**: not established by this pass.

Upstream source root:
https://github.com/NssIs/Ages-of-Dominion-ModJam-2026/tree/c1e71a021ba88a053a378292c6011cb89828fd36

## 2. High-level architecture

The main server tick in `ForgottenRealmsRTS` orchestrates worker orders, economy production,
invasions, defense and world maintenance. That means expensive or strategic logic does not have to
live inside every entity's own AI tick.

The implementation separates four kinds of state:

| State | Owner | Persistence |
|---|---|---|
| realm/economy/civilization/campaign | player | synced persistent attachments |
| placed buildings / active construction | world level | owner-keyed SavedData |
| worker specialist job | worker entity | synced fields + entity save data |
| tactical move/attack/hold and short response caches | runtime director | deliberately transient |

This separation is one of the strongest reusable patterns in the project.

## 3. Worker intelligence: replace Villager Brain with explicit RTS state

**DIRECT_OBSERVATION.** `RtsVillagerEntity` defines a work-state enum covering idle, wood
gather/return, mine travel/work/return, farm travel/work/return, build travel/build and repair
travel/repair. It serializes assignment IDs, carried resources, worksite targets and role flags.

More importantly, its server AI step intentionally does not run ordinary free-roaming Villager
Brain behavior. It only guards the currently assigned navigation. The source comment states that
the town director supplies routes and vanilla job-site/wander memories would pull the worker away
from the RTS ring.

Locators:

- `RtsVillagerEntity.java#L79` — WorkState
- `RtsVillagerEntity.java#L363-L367` — RTS-specific server AI boundary
- `RtsVillagerEntity.java#L388-L487` — persistent worker state

**Technique:** for tightly directed RTS workers, do not fight a general autonomous Brain on every
tick. Keep the entity as a physical Minecraft actor, but put strategic/job choice in a central
controller and represent the job as an explicit state machine.

This is directly relevant to KNEEKURA's preference for formation/group intelligence over 22 fully
independent high-level thinkers.

## 4. Command precedence: player intent is a hard strategic commitment

`RtsUnitOrders` keeps three explicit runtime modes:

- MOVE
- ATTACK
- HOLD

These orders are stored by unit UUID and deliberately remain session/runtime state. They are not
restored after world reload, because stale entity references should not become strategic truth.

`RtsDefenseDirector` then enforces the priority:

1. re-apply explicit player order;
2. otherwise leave a specialist worker's job alone;
3. otherwise honor a temporary defense response;
4. otherwise return the unit to its deterministic Town Hall patrol point.

The director explicitly refuses to "correct" a bad player command. HOLD may therefore be a
deliberate strategic mistake rather than something autonomous defense silently overrides.

Locators:

- `RtsUnitOrders.java#L108-L198`
- `RtsDefenseDirector.java#L44-L99`

**Technique:** define an authority/priority table before adding behavior. A strategy system becomes
predictable when autonomous controllers cannot casually steal units from player or job orders.

## 5. Hybrid AI: external strategy + vanilla tactical executors

Combat units do not contain a large strategy Brain.

- the soldier keeps a normal `MeleeAttackGoal`;
- archer/crossbow units keep normal ranged attack Goals;
- strategic target/destination comes from `RtsUnitOrders` or `RtsDefenseDirector`.

Enemies use normal target Goals, but `RtsEnemyEntity.customServerAiStep` reasserts a siege
destination after vanilla target processing when a building target exists.

**Technique:** reuse vanilla locomotion/attack execution where it is good, while moving strategic
choice outside the entity. This is cheaper and more controllable than replacing every local action
with a custom planner.

## 6. Group movement: one order, individual paths — not formation planning

No formation-offset allocator was found in the pinned source.

The selected-unit request supplies a list of entity IDs plus one destination. After server
validation, `RtsUnitOrders.issueMove` gives each unit that same strategic destination, and each
unit obtains its own Minecraft Path.

So the current architecture is:

`selection -> one target -> N independent safe vanilla paths`

rather than:

`selection -> formation planner -> N role/slot destinations -> N paths`.

That distinction matters for KNEEKURA. Ages of Dominion provides a strong **command and safe-route
foundation**, but its group motion should not be mistaken for recovered formation intelligence.

## 7. Pathfinding wrapper: validate, cache and back off

`RtsUnitOrders.moveToSmart` wraps vanilla navigation rather than replacing A*.

Important details:

- current route is reused instead of recalculated every director pass;
- successful-route retry window: **40 ticks**;
- failed-route retry window: **100 ticks**;
- an invalid destination gets at most **four** nearby candidate path probes;
- if no safe reachable Path exists, navigation stops instead of falling back to raw coordinate
  movement;
- every remaining Path node is checked against current terrain;
- changed terrain can invalidate and stop a live worker route.

`RtsNavigationSafety` defines a two-block-high dry feet/head volume, solid dry support,
one-block vertical steps and guarded diagonal corners.

Locators:

- `RtsUnitOrders.java#L44-L98`
- `RtsUnitOrders.java#L223-L267`
- `RtsNavigationSafety.java`

**Technique:** the expensive part is often not "invent a new pathfinder" but controlling when the
existing pathfinder is asked to work. Cache a route, validate it cheaply, use a failure backoff, and
bound fallback searches.

This is especially useful for night waves and selected groups where dozens of identical
re-path requests can otherwise multiply server cost.

## 8. Defense director: bounded local reaction, not global retargeting

The director thinks once every **10 ticks**.

An allied unit hit by an RTS enemy can cause nearby combat units to respond, but:

- only attackers within the Town Hall threat region qualify;
- only combat units without explicit player orders are candidates;
- candidates are sorted by distance to the victim;
- at most **three** responders are assigned;
- response expires after **120 ticks**;
- outside response, units occupy deterministic ring positions derived from their UUID.

Locators:

- `RtsDefenseDirector.java#L20-L39`
- `RtsDefenseDirector.java#L101-L123`
- `RtsDefenseDirector.java#L130-L147`

**Technique:** bounded responder allocation turns "everyone saw combat" into a small local reaction.
It reduces dog-piling and gives a stable idle formation without a heavy planner.

## 9. Worker jobs are persistent FSMs with runtime reservations

### 9.1 Lumberjack

Wood work is more sophisticated than "find nearest log".

At assignment:

- clicked block is resolved to a legal worksite;
- natural-tree validation rejects building timbers;
- a bounded connected log component is captured;
- a stable worksite anchor is stored;
- one normal tree allows one worker; a large tree (>=12 captured logs) allows three;
- repeated assignment is treated idempotently.

During work:

- the exact reserved component is rechecked;
- a building completed during chopping immediately protects its footprint;
- worker swings and block-break progress are visible;
- carried wood is bounded at 16;
- the worker returns to the Town Hall, deposits into the economy, then resumes the same tree if
  appropriate;
- a designated idle lumberjack periodically looks for another tree;
- runtime route-stall tracking triggers recovery after 80 ticks stationary.

On reload, the runtime reservation can be rebuilt only from the persisted target + worksite if the
natural rooted component is still valid. It does not blindly reinterpret any new nearby log as the
old job.

Locators:

- `RtsWorkerOrders.java#L107-L194`
- `RtsWorkerOrders.java#L322-L562`
- `RtsWorkerOrders.java#L975-L1077`
- `RtsWorkerOrders.java#L1203-L1260`

**Technique:** reserve the **work object**, not just a coordinate. The job identity should survive
changes to its current sub-target.

### 9.2 Mine / farm / construction / repair

Mine and farm work use explicit travel/work/return state transitions. Construction and repair
likewise bind a worker to a stable building/construction ID rather than a transient screen target.

The common pattern is:

`validate assignment -> clear incompatible tactical order -> persist role/job ID -> route ->
work cadence -> resource/progress mutation -> return/release -> restore route after reload`.

That pattern is portable even when the exact 26.1 APIs are not.

## 10. Construction: persistent progress, bounded work and no destructive overwrite

`RtsConstructionStore` records:

- stable ID and owner;
- structure ID;
- origin and rotation;
- total blocks;
- placed prefix;
- accumulated work progress;
- whether the build uses layered ordering.

Paid construction thinks every **5 ticks**. Each present builder contributes work, and at most
**four blocks** are placed in one think pass.

A world cell is checked again immediately before placement. If another process/player changed that
cell to an unexpected block, construction pauses instead of overwriting it.

Free/autonomous construction uses bottom-up Y layers at a slower cadence rather than palette-order
worker progress.

Locators:

- `RtsConstructionStore.java#L23-L59`
- `RtsConstructionOrders.java#L83-L198`
- `RtsConstructionOrders.java#L247-L340`
- `RtsConstructionOrders.java#L343-L414`

**Techniques:**

- save logical progress independently of worker routes;
- cap world mutations per scheduler pass;
- make build work resumable/idempotent by comparing expected world state;
- never treat an old empty cell as permission to overwrite a newly occupied cell.

## 11. Natural-tree recognition: semantics need topology, not only tags

Minecraft's log tag also matches timber used by structures. Ages of Dominion therefore adds
bounded semantic classification.

The v4.2 `NaturalTreeClassifier` requires a connected log component that:

- is rooted on natural ground (or a tightly controlled temporary support exception);
- has nearby leaves;
- remains inside explicit horizontal/vertical/log-count bounds;
- excludes protected building/foundation regions, block entities and fluids;
- caches accepted and rejected components for one scanner lifetime.

The classifier is shared by placement/tree handling and related client behavior.

Locator:
- `NaturalTreeClassifier.java#L133-L331`

**Technique:** tags answer "what material is this?" but not "what world object does this belong to?".
When automated workers may destroy blocks, classify the object using topology + environment +
ownership/protection boundaries.

## 12. Building placement: shared preview rule, server authority

`BuildingPlacement` deliberately shares geometry rules between client ghost and authoritative
server placement.

Notable rules:

- only base-layer columns require ground support; roof overhangs are not falsely rejected;
- support uses collision geometry rather than a coarse material flag;
- destination collision is checked against actual occupied structure cells;
- paths have explicitly different surface replacement rules;
- natural-tree replacement is an explicit allowance, not generic terrain destruction;
- path/wall expansion is bounded to **256 pieces**; oversized requests fail rather than silently
  placing a prefix.

Locator:
- `BuildingPlacement.java#L97-L217`
- `BuildingPlacement.java#L223-L286`

**Technique:** client and server should share the same pure validation contract, while the server
still reruns it. Preview truth and mutation authority are separate concerns.

## 13. Economy: physical labor plus low-frequency building production

The economy deliberately combines two models:

- opening wood is physically gathered by worker entities;
- completed economic buildings produce on a **40-tick** cycle;
- building level multiplies defined production;
- special moons modify the cycle (Golden 2x, Blue 0.5x);
- recovered relics add a persistent percentage bonus;
- stock is capped.

This is a useful hybrid between a purely simulated spreadsheet economy and expensive fully physical
production for every resource.

## 14. Night invasion / siege orchestration

The invasion manager evaluates once per 20 ticks.

Behavior includes:

- first natural night is quiet;
- later wave size grows with day and is capped at 40;
- Blood/Blue/Golden moon variants change wave/economy behavior;
- RTS enemies prefer the nearest live non-Town-Hall building;
- if none remains, they siege the Town Hall;
- each attacker inside a small radius contributes structure/hall damage;
- defensive towers act automatically;
- daylight removes/purges invasion enemies;
- Town Hall integrity decides defeat; surviving through the final campaign day decides victory.

Locator:
- `RtsInvasion.java#L143-L274`
- `RtsInvasion.java#L276-L339`
- `RtsInvasion.java#L433-L464`

**Technique:** an RTS raid becomes much more legible when enemies target settlement assets as
first-class records, not only nearest living entities.

## 15. Client selection -> server intent -> authoritative resolution

The client owns interaction ergonomics:

- click selection;
- screen-space drag box;
- contextual worker/building interpretation;
- path breadcrumbs and HUD state.

The server owns game truth:

- it receives entity IDs / building IDs / target positions;
- rejects oversized unit lists (>64);
- de-duplicates IDs;
- resolves live entities again;
- checks allied type and settlement radius;
- checks RTS/civilization/campaign state;
- owner-scopes building/construction lookups;
- applies mutation only after those checks.

The network protocol at v4.2 is version **8**:

- **27** registered client-to-server payload types;
- **11** registered server-to-client payload types.

Locators:

- `ModPayloads.java#L186-L242`
- `ModPayloads.java#L816-L829`
- `ModPayloads.java#L973-L996`
- `ClientPayloadHandlers.java#L56-L79`

### Multiplayer warning

The public project currently says multiplayer is not supported. The current selected-unit
validator knows "allied RTS unit + proximity", but units do not carry a universal per-player owner
identity. Do not assume this is a complete hostile-client ownership boundary.

**Technique for KNEEKURA:** keep the same client-intent/server-resolution split, but require explicit
unit ownership/command authority before multiplayer.

## 16. Detached RTS camera over a real Minecraft player anchor

RTS mode forces the real player into a protected spectator-like state. Client camera control then
uses a fixed tactical pitch, zoom and X/Z panning; terrain-following keeps the anchor above local
terrain.

The camera terrain pass uses a cached 13x13 client heightmap window instead of a full Y scan every
tick. A MoveCamera payload lets the authoritative player anchor follow the selected X/Z chunk on
the server.

Locators:

- `RtsMode.java`
- `IsometricCameraController.java#L72-L268`
- `ModPayloads.java#L716-L726`

**Technique:** a detached RTS view can coexist with Minecraft's player-centric server model by
treating the real player as an invisible protected anchor, while keeping camera presentation
client-side.

## 17. Persistence architecture

Ages of Dominion separates persistence according to what the state belongs to.

### Player attachments

`RtsEconomy`, `RtsCivilization`, `RtsBattle` and `RtsMode` use NeoForge attachments for
persistent player state. Many fields are also auto-synced to the client so the HUD needs no
dedicated packet.

### Level SavedData

`RtsBuildingStore` and `RtsConstructionStore` store world geometry/state with stable numeric IDs
and an owner UUID. Lookups combine ID + owner.

### Entity persistence

`RtsVillagerEntity` owns its work state, carried resources, specialist assignments and saved
worksite coordinates.

### Deliberately transient state

Manual tactical orders and temporary defense response maps are not saved.

**Technique:** persistence should follow semantic lifetime. Saving every runtime decision is not
"more correct"; some strategic orders should intentionally decay on reload while durable jobs and
realm geometry recover.

## 18. Performance techniques recovered

The source includes several simple but high-value cost controls:

- coarse director cadences (5/10/20/40+ ticks depending on subsystem);
- route reuse and backoff;
- max four fallback path probes;
- max 64 selected IDs per command;
- max four construction blocks per paid think;
- bounded tree-component searches;
- cached protected structure footprints;
- cached 13x13 terrain height samples for camera following;
- bounded responder counts;
- wave cap 40;
- bounded linear construction 256 pieces.

The pattern is consistent: **bound fan-out before optimizing the inner operation**.

## 19. 1.20.1 Forge portability

There is no native ANCHOR implementation. Reuse is therefore a conceptual/backport exercise.

### Mostly portable gameplay logic

These are strong direct candidates for reconstruction:

- command precedence table;
- MOVE / ATTACK / HOLD tactical order abstraction;
- route cache + safe-path validation + retry backoff;
- central worker FSM/director;
- stable worksite reservation;
- bounded local defense responses;
- persistent construction progress;
- server-side revalidation of client intent;
- building-first siege targeting;
- low-frequency scheduler cadences;
- client/server-shared pure placement rules.

### Rewrite boundaries for Forge 1.20.1

- Java 25 upstream -> Java 17 target.
- NeoForge 26.1 AttachmentType persistence/sync needs a Forge 1.20.1 equivalent design.
- Modern NeoForge payload registration/codecs need a Forge 1.20.1 packet layer.
- Modern entity `ValueInput/ValueOutput` persistence must be adapted to 1.20.1 entity save APIs.
- Identifier/registry and several event/camera APIs changed across the Minecraft/loader gap.
- detached camera hooks should be reconstructed against actual Forge 1.20.1 client events/mixins,
  not copied mechanically.
- structure/template and SavedData calls require version-specific review.

### Semantic risk

Do **not** backport the current single-player authority assumptions unchanged if KNEEKURA later
supports multiplayer. Add explicit owner/control identity to units and validate every command
against it.

## 20. What Ages of Dominion gives KNEEKURA

The most valuable recoveries are:

1. **Authority ladder** — explicit order > job > reaction > patrol.
2. **Central worker FSM** — physical villagers without autonomous Villager Brain interference.
3. **Vanilla executor / custom strategy split** — Goals attack; directors decide why/whom.
4. **Safe navigation wrapper** — validate/cache/backoff around vanilla Path.
5. **Stable work-object reservation** — tree component + anchor instead of constantly retargeting.
6. **Bounded responder allocation** — only a few nearby defenders react.
7. **Persistent construction transaction** — saved progress + world-state recheck.
8. **Settlement-asset siege AI** — buildings are strategic targets.
9. **Semantic world classifier** — topology/environment distinguish tree from timber structure.
10. **Client intent / server truth** — UI selects, server resolves and mutates.
11. **Lifetime-based persistence** — durable jobs/world records, transient tactical commands.
12. **RTS camera anchor pattern** — Minecraft player remains the server anchor for a detached view.
13. **Fan-out budgets everywhere** — cost is controlled structurally before micro-optimization.

## 21. Non-findings / boundaries

- No formation-slot or flocking planner was found.
- No evidence of one LLM/planner-like "unit brain" exists; the architecture is deliberately simpler.
- No runtime benchmark was performed.
- No ordinary test suite was present in the source tree.
- No exact released-JAR SHA/source-byte equivalence was established.
- Native 1.20.1 Forge code does not exist in the pinned upstream.
- Multiplayer correctness is not established.

## 22. Primary source locators

Pinned source:
https://github.com/NssIs/Ages-of-Dominion-ModJam-2026/tree/c1e71a021ba88a053a378292c6011cb89828fd36

Key files:

- `RtsVillagerEntity.java`
- `RtsUnitOrders.java`
- `RtsNavigationSafety.java`
- `RtsDefenseDirector.java`
- `RtsWorkerOrders.java`
- `RtsMineOrders.java`
- `RtsFarmOrders.java`
- `RtsConstructionOrders.java`
- `RtsConstructionStore.java`
- `RtsBuildingStore.java`
- `RtsInvasion.java`
- `BuildingPlacement.java`
- `NaturalTreeClassifier.java`
- `network/ModPayloads.java`
- `network/ClientPayloadHandlers.java`
- `client/build/BuildingSelectionController.java`
- `client/camera/IsometricCameraController.java`

Public distribution/release material:

- https://www.curseforge.com/minecraft/mc-mods/ages-of-dominion
- https://www.curseforge.com/minecraft/mc-mods/ages-of-dominion/files/8845160
