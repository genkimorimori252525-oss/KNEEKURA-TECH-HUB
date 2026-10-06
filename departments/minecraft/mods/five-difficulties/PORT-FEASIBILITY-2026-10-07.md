# 五つの難題MOD+ X1 → Minecraft 1.20.1 Forge — Port Feasibility

Date: 2026-10-07

Status: **TECHNICALLY FEASIBLE — RECONSTRUCTION REQUIRED, NOT A BINARY PORT**

Implementation is deliberately **not started** by this document.

## 1. Fidelity target

Target behavior/art direction is the previously analyzed:

- 五つの難題MOD+ `ver2.90.1.X1-1.7.10`
- internal MOD version observed as `2.90-1.7.10`
- Minecraft 1.7.10
- X1 is a later bug-fix/behavior/render modified build around the original 2.90.1 line.

Public X1 thread:
- https://forum.civa.jp/viewtopic.php?t=25
- identifies X1 as adding bug fixes, invulnerability removal, damage-speed changes and rendering changes;
- states Forge 10.13.4.1614-1.7.10 / multiplayer support.

The port should treat **X1 itself** as the gameplay/visual oracle, not silently normalize back to stock 2.90.1.

### Previously recovered local static structure

The earlier X1 analysis recovered:
- `sources/java/`: 266 Java files;
- 276 compiled classes;
- a reusable architecture broadly shaped as:
  `ShotData / LaserData → THShotLib → SpellCard`;
- 35 registered spell-card entries plus one dormant implementation;
- many player items and special entities reuse the same shot/laser substrate;
- input/state changes alter topology, attack verb, charge behavior or focus behavior rather than only damage numbers;
- example: red Homing Amulet normal state uses a wide multi-shot pattern while Shift/focus uses a narrower, stronger pattern;
- Sakuya time stop is implemented through a clock/entity mechanism that repeatedly restores stored entity position/rotation/motion/tick-like state.

Before implementation, the exact supplied X1 archive must be repinned with SHA-256 and source↔binary receipts under the normal TECH-HUB workflow.

## 2. Conclusion

### Can its look be kept extremely close on 1.20.1?

**Yes.**

There is no fundamental renderer/API limitation preventing reproduction of:
- original PNG item icons;
- colored outlined orb bullets;
- shot sizes and palettes;
- laser width/color/length;
- spell-card geometry and sequencing;
- Master Spark silhouette;
- fairy/character textures and old Minecraft-style models;
- world-space weapon/effect entities;
- Shift/focus pattern changes;
- legacy-like UI/sound hooks.

What cannot be retained is the old **implementation API**.

Minecraft/Forge changed too much between 1.7.10 and 1.20.1 for the old classes to be recompiled with small edits. The correct engineering model is:

`preserve assets + formulas + tick semantics + visual contract`

while replacing:

`1.7.10 Forge/Minecraft integration code`.

This is a reconstruction/backport, not source copy/paste.

## 3. Fidelity matrix

| Surface | Visual/behavior fidelity potential | Port difficulty | Strategy |
| --- | --- | --- | --- |
| PNG item icons | extremely high | low | reuse exact allowed asset bytes; generated/item JSON |
| bullet textures/palette | extremely high | low-medium | same PNG/sprite UVs; modern translucent/full-bright renderer |
| bullet size/orientation | extremely high | medium | recreate legacy quad/billboard geometry |
| ShotData constants | extremely high | medium | translate constants/data model, not MC API calls |
| spell-card pattern geometry | extremely high | medium | preserve exact formulas and 20 TPS timeline |
| Shift/focus branches | extremely high | low-medium | server-authoritative use/sneak state or validated key packet |
| standard projectiles | high | medium | dedicated 1.20.1 shot runtime |
| lasers | high | high | custom renderer + collision service |
| Master Spark | high | high | dedicated beam/effect entity + custom RenderType |
| particle effects | high | medium | custom ParticleType/Particle or direct render layer |
| dynamic/3D item rendering | high | high | BEWLR / baked-model extension |
| fairy/character textures | extremely high | medium | preserve UV assets; rebuild model layer |
| fairy/character AI | high behaviorally | high | rewrite EntityAIBase-era logic as Goal/MoveControl/etc. |
| spell sounds | high when rights/assets available | low-medium | SoundEvent/sounds.json |
| multiplayer sync | high behaviorally | high | explicit modern packets + SynchedEntityData |
| time stop | high player-facing, not implementation-identical | very high | snapshot/restore service; whitelist tracked state |
| exact old bugs/races | intentionally low | undesirable | preserve only bugs proven to be part of expected gameplay |
| pixel-identical whole frame | not guaranteed | — | newer lighting/render pipeline prevents honest promise |

The meaningful target is **perceptual and gameplay fidelity**, not bit-identical 1.7.10 frames.

## 4. 1.7.10 → 1.20.1 platform map

### Registration

Legacy:
- GameRegistry/EntityRegistry/global numeric IDs;
- old preInit/init lifecycle.

1.20.1:
- `DeferredRegister`;
- `RegistryObject`;
- registered `EntityType`, `Item`, `Block`, `SoundEvent`, `ParticleType`.

The registry rewrite does not require visual changes.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/concepts/registries/

### Dynamic entity data

Legacy DataWatcher/state IDs must become:
- `SynchedEntityData`;
- `EntityDataAccessor`;
- explicit spawn data only when needed.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/networking/entities/

### Packets

Any legacy packet/FML channel logic should become:
- `SimpleChannel`;
- explicit encode/decode;
- explicit server/client direction;
- main-thread enqueue;
- validation of held item/state/target/range.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/networking/simpleimpl/

### Input / Shift behavior

Two categories should remain separate.

If old behavior is literally crouch/focus:
- use server-known player crouch/shift state where possible.

If a distinct client key is required:
- `KeyMapping`;
- optionally `KeyModifier.SHIFT`;
- send only action intent to server.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/misc/keymappings/

### Item/block assets

Flat legacy icons can generally retain their PNG appearance with:
- registry/resource name normalization;
- `item/generated`-style JSON;
- original texture dimensions where valid.

Dynamic item renderers that used old `IItemRenderer`/GL code must be rewritten through:
- baked-model extensions; or
- `BlockEntityWithoutLevelRenderer` where dynamic transforms are required.

Official references:
https://docs.minecraftforge.net/en/1.20.1/resources/client/models/
https://docs.minecraftforge.net/en/1.20.1/items/bewlr/

### Particles

Modern Forge still supports:
- custom particle data;
- server/client synchronization;
- translucent/lit/custom render types.

This is sufficient to reproduce the old glowing orb language without adopting a modern VFX art direction.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/gameeffects/particles/

### Sounds

The old readme documents optional named OGG hooks such as:
- `masterspark.ogg`;
- `spellcard.ogg`;
- `sukima.ogg`;
- `down.ogg`.

The same event contract can be retained through `SoundEvent` + `sounds.json`.

The legacy readme also says these sound files were not supplied by the author and users were expected to provide/create permitted files. A port should preserve the hooks without assuming redistribution rights for third-party sound files.

Official reference:
https://docs.minecraftforge.net/en/1.20.1/gameeffects/sounds/

## 5. Danmaku core: why this MOD is unusually portable

The strongest reason this project is feasible is the recovered separation:

`ShotData / LaserData`
→ shot parameters / visual type

`THShotLib`
→ geometry / emission helpers

`SpellCard`
→ temporal sequence

This is exactly the kind of separation needed to change Minecraft versions without changing the pattern.

The port should create a modern equivalent such as:

- `LegacyShotSpec`
- `LegacyLaserSpec`
- `LegacyShotMath`
- `LegacySpellCard`
- `LegacyPatternRuntime`

Legacy constants should be translated literally first:
- angle;
- speed;
- acceleration;
- gravity;
- homing;
- delay;
- color;
- shot type;
- scale;
- bounce;
- lifetime;
- number of bullets;
- per-tick phase changes.

Do **not** “improve” the bullet geometry before parity.

## 6. Fidelity-first bullet backend

### Phase A — physical compatibility backend

First implementation should favor auditability over optimization:

- one shot state per legacy projectile;
- entity-like server update semantics;
- one modern renderer reproducing old sprite/quad visuals;
- exact legacy 20 TPS sequencing;
- exact collision and lifetime policy as far as recovered.

Advantages:
- easiest comparison with X1;
- easier debugging of one bullet;
- easier replay of spell-card timelines;
- avoids hiding differences behind batching.

Disadvantage:
- large patterns may be expensive.

### Phase B — virtual/batched backend only after parity

After X1 patterns pass golden tests, high-density attacks can optionally use the modern technique already recovered from Youkai's Homecoming:
- server-managed simplified/virtual bullets;
- client bullet cache;
- batch synchronization;
- render queues;
- mover/ticker pattern logic.

The same `LegacyShotSpec` should feed either backend.

Required invariant:
`ENTITY backend result ≈ VIRTUAL backend result`
for trajectory, timing, collision, damage and presentation within declared tolerance.

This allows major performance improvement without redesigning the old look.

## 7. Rendering strategy for the original look

The old aesthetic should be preserved intentionally.

### Bullet sprites

Prefer:
- the original sprite/texture;
- nearest/appropriate legacy-like sampling;
- old palette unchanged;
- crossed quads or camera-facing quads matching the legacy geometry;
- full-bright where the old renderer behaved as full-bright;
- no bloom added by default;
- no forced modern particles/trails.

The bright outlined circular bullets visible in preserved gameplay are simple enough that a modern renderer can reproduce them closely.

### Laser

Reconstruct from `LaserData`:
- origin;
- direction;
- start/end length;
- width;
- color;
- opacity;
- lifetime;
- collision interval.

Rendering and collision should be separate.

The renderer should recreate the legacy beam mesh, while server logic owns hit tests.

### Master Spark

Do not turn it into a generic particle beam.

Use a dedicated `MasterSparkState`:
- charge/start;
- beam axis;
- width/scale envelope;
- active ticks;
- block/entity interaction;
- fade/end.

Renderer then reproduces the old broad beam shape from the same authoritative state.

### Old models

When original Java model geometry is available:
- extract cube dimensions, pivots, UV coordinates and scale;
- rebuild as 1.20.1 ModelPart/LayerDefinition or an equivalent custom mesh;
- preserve texture files.

Blockbench can be used as an authoring/inspection intermediary, but should not redesign silhouettes automatically.

## 8. Spell-card fidelity

Earlier analysis identified 35 registered spell cards plus a dormant implementation.

For every card, freeze:
- total duration;
- phase boundaries;
- shot events per tick;
- angle formulas;
- radial/spiral/fan topology;
- retarget timing;
- bullet transformation/deletion rules;
- color/type;
- sound declaration timing;
- collision/damage policy.

Recommended machine-readable oracle:

`tick → [shot spec + spawn transform + target rule]`.

A 1.20.1 implementation should generate the same timeline before any visual polish.

## 9. Shift / state-sensitive items

Earlier analysis found multiple semantic families:
- FOCUS;
- TOPOLOGY SWITCH;
- VERB SWITCH;
- CONTINUOUS CHARGE;
- THRESHOLD LADDER;
- EMBODIED CHARGE;
- CONTEXT ACTION;
- PERSISTENT MODE.

These should remain explicit.

Example:
the red Homing Amulet changes from a wide multi-shot normal pattern to a tighter stronger focused pattern while Shift/focus is active.

Do not reduce these items to:
`if shift: damage += N`.

The legacy pattern topology itself must change.

## 10. Time stop — hardest fidelity subsystem

The old clock/time-stop implementation snapshots and repeatedly restores entity state.

This is much harder to copy directly because:
- entity internals changed;
- field names/visibility changed;
- client interpolation changed;
- modern entities have more state;
- modded entities may use custom movement/AI;
- network correction may fight direct rewinds.

A 1.20.1 implementation should reconstruct the **observable contract**:

On freeze admission:
- capture eligible entity transform and motion state;
- optionally capture selected animation/tick state if necessary.

During freeze:
- suppress/restore movement according to legacy observation;
- define explicit whitelist/blacklist for players/projectiles/items/mobs;
- keep server authoritative;
- sync visuals deliberately.

On release:
- restore or resume velocity/tick state according to the X1 oracle.

Do not promise internal equivalence with 1.7.10 fields. Target observable equivalence.

## 11. AI / mobs

Old `EntityAIBase`-era code cannot be retained directly.

Rewrite into:
- Goal;
- targetSelector;
- MoveControl;
- Navigation;
- modern attributes;
- SynchedEntityData.

However:
- spawn conditions;
- target priorities;
- cooldowns;
- range;
- shot selection;
- retreat/approach distances;
- spell-card triggers;
can be copied as behavior values.

Visual character skins/models can stay almost unchanged even if AI internals are new.

## 12. World/block interactions

Items such as:
- Master Spark;
- special swords/tools;
- time stop;
- gap/sukima-style effects;
- block-destroying attacks

must be ported through explicit 1.20.1 block-state APIs.

For fidelity and server safety:
- preserve the same *selection geometry*;
- route bulk edits through a bounded service;
- preserve protected-block policy;
- avoid unbounded synchronous loops.

The visible destruction pattern can remain the same even when the scheduling changes internally.

## 13. Golden X1 oracle

Before optimization, run X1 in a controlled 1.7.10 environment and capture reference evidence.

For representative items/spell cards record:

### Simulation
- tick;
- projectile count;
- x/y/z;
- vx/vy/vz;
- yaw/pitch;
- color/type;
- scale;
- target ID;
- life/phase.

### Visual
At fixed ticks:
- first-person screenshot;
- side view;
- top-down view;
- same FOV and known camera coordinates.

### Laser
- start/end;
- length;
- width;
- rotation;
- alpha/color;
- collision result.

### Input
- normal vs Shift;
- ground/air;
- stationary/moving;
- charge thresholds;
- item switch/cancel.

### Time stop
- before freeze;
- first frozen tick;
- mid-freeze;
- final frozen tick;
- first release tick.

### Multiplayer
- server counts;
- client counts;
- owner/target;
- packet ordering tolerance;
- late join/tracking start.

The 1.20.1 port is accepted by **behavioral delta**, not by “looks close to memory.”

## 14. Acceptance levels

### L0 — Asset identity
- same approved source textures/icons;
- same palette;
- no accidental filtering/path changes.

### L1 — Static render parity
- item hand/inventory appearance;
- bullet sprite silhouette;
- model UV/scale.

### L2 — Single-technique parity
- one shot;
- homing;
- bounce;
- laser;
- Shift branch.

### L3 — Spell-card parity
- same timeline and topology.

### L4 — Interaction parity
- collision/damage/block behavior;
- time stop;
- Master Spark;
- NPC use.

### L5 — Multiplayer parity
- dedicated server;
- tracking/sync;
- no client-authoritative combat.

### L6 — Optimization parity
Only now swap selected attacks to virtual/batched runtime.

## 15. What should *not* be modernized during the fidelity phase

Do not, by default:
- replace old sprites with high-resolution art;
- add bloom/shaders;
- smooth all movement;
- alter colors;
- add trails that were not present;
- convert every attack to particles;
- normalize quirky burst timing;
- redesign recipes/balance;
- replace old spell geometry with Youkai's Homecoming patterns.

Modern techniques may implement the old result, but they must not silently replace its art direction.

## 16. Main technical risks

### High

1. **Time stop**
   - broad interaction with arbitrary entities and client interpolation.

2. **Rendering**
   - old fixed-function GL state must be translated carefully;
   - alpha/depth/full-bright differences can visibly change orb/laser appearance.

3. **Mass danmaku performance**
   - physical Entity parity may be expensive;
   - optimization must wait until parity is measurable.

4. **Master Spark / destructive effects**
   - rendering, hitbox and block edits have separate fidelity contracts.

5. **Multiplayer**
   - X1 itself was a modified multiplayer/bug-fix build;
   - old race/timing assumptions should not be carried blindly.

### Medium

- mob AI;
- special item renderers;
- custom GUI;
- recipes;
- block/item state migration;
- entity persistence.

### Low

- most flat PNG assets;
- language names;
- simple items;
- straightforward crafting data;
- simple sounds/hooks.

## 17. Public-distribution rights boundary

Technical feasibility is separate from redistribution permission.

Available public records establish:
- the English mirror says modpacks were allowed under conditions such as no money-grinding, original link and author credit;
- a later addon thread says publication questions for custom spell-card/addon work should ultimately be asked of original author くろあんこ, while recalling that the readme welcomed such work;
- X1 author says X1 use follows the original rules and asks users to identify that they are using the modified version.

These records are **not enough to confidently infer permission to redistribute a full modified 1.20.1 port containing original code/assets**.

Before a public release:
- recover the exact X1/original readme terms;
- distinguish permission to create addons/modpacks from permission to redistribute modified original assets/code;
- obtain author permission if the surviving terms do not clearly grant it;
- separately respect Touhou Project derivative-work rules.

Private technical reconstruction/research and public distribution should be tracked as different milestones.

References:
- https://www.minecraftforum.net/forums/mapping-and-modding-java-edition/minecraft-mods/1287201-touhou-items-mod-version-2-90-1-june-4-2016-check
- https://forum.civa.jp/viewtopic.php?t=25
- https://openeye.openmods.info/mod/thkaguyamod/all

## 18. Decision

**GO for a 1.20.1 Forge fidelity port as a technical project.**

Recommended framing:

> Five Difficulties X1 Preservation Port

not:

> automatic upgrade of the original source.

The project should preserve:
1. visual assets;
2. shot/laser mathematics;
3. spell-card timelines;
4. input semantics;
5. item/mob behavior;
6. then optimize the backend.

The primary technical question is no longer “can 1.20.1 display this?”

It can.

The difficult question is:

**how rigorously do we measure X1 before replacing the old engine around it?**

The existing source-rich X1 distribution makes that a tractable engineering problem.
