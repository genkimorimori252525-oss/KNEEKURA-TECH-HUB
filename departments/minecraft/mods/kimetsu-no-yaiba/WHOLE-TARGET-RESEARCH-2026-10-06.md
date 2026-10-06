# Kimetsu no Yaiba ver3 — Whole-Target Technical Research — 2026-10-06

## 1. Evidence basis

Primary implementation evidence:

`KimetsunoYaiba-ver3-forge-1.20.1.jar`

SHA-256:
`b4af6e8a9d5926c5fea212a5e237e61f1e8095a5be23eca9b8294258a3b466b6`

No official source repository/revision was pinned.

Therefore bytecode/resource locators use:

```text
Class
method
bytecode offset / constant / invoked method
```

rather than source line numbers.

Evidence labels:

- **DIRECT_OBSERVATION** — uploaded JAR / exact public release page
- **AUTHOR_CLAIM** — Orca_san_ release/project text
- **INFERENCE** — engineering interpretation
- **UNKNOWN** — not established

## 2. Loader / patch surface

`mods.toml`:

- MCreator-generated
- JavaFML [47,)
- MC 1.20.1
- version 3

Manifest:
- `MixinConfigs: mixins.kimetsunoyaiba.json`

Mixin config:
- required
- Java 17
- no actual mixin/client mixin class entries

Therefore this JAR has a nominal Mixin configuration but does not use Mixins as its main mutation
surface.

### Access Transformer

The important invasive surface is Access Transformer access to:

- `MultiNoiseBiomeSource.parameters`
- `ChunkGenerator.biomeSource`
- `ChunkGenerator.featuresPerStep`
- generation-settings getter/fields
- `NoiseBasedChunkGenerator.settings`
- `SurfaceRules.SequenceRuleSource`

These are used by runtime biome/surface injection.

## 3. Dependency reality vs metadata

Public project description says 1.20.1 requires:

- PlayerAnimator
- GeckoLib

JAR metadata marks them non-mandatory.

Bytecode contains:

- GeckoLib references in >100 classes
- direct PlayerAnimator API references in `SetupAnimationsProcedure`

**DIRECT_OBSERVATION:** metadata does not express the same dependency requirement as the public
description/bytecode.

**Compatibility lesson:** dependency declarations should match hard-link class loading. Optional
integration should be classloader-isolated behind presence checks.

## 4. MCreator as generated architecture

There are ~720 top-level Procedure classes.

Major families:

- 136 Breathing-form procedures
- 83 Blood Demon Art procedures
- 117 AI procedures
- 18 player breathing selectors
- 14 player demon-art selectors
- 56 swing/item procedures
- 49 effect procedures
- 33 spawn-rule procedures
- 8 animation procedures

The implementation is therefore not primarily object-oriented polymorphism.

It is a large procedure graph tied together with persistent data keys.

## 5. NPC AI: vanilla locomotion, custom combat planner

Representative hostile entity:
`AkazaEntity.m_8099_()` — vanilla `registerGoals` in obfuscated bytecode.

It installs:

- RestrictSunGoal
- custom MeleeAttackGoal
- HurtByTargetGoal
- many `NearestAttackableTargetGoal` instances, one per concrete hostile target class

Then the entity's per-tick path calls `AIakazaProcedure`.

Pattern:

```text
Vanilla:
  acquire target
  navigate
  basic melee

Procedure:
  counters
  target/distance state
  choose technique mode
  execute technique script
```

This hybrid is conceptually sound: avoid rewriting navigation just to add anime attacks.

## 6. Explicit target-class matrix

Compiled inventory found:

- ~1,521 anonymous `NearestAttackableTargetGoal` subclasses
- ~100 MeleeAttackGoal subclasses
- ~45 HurtByTargetGoal subclasses

Many Slayer/demon classes register dozens of concrete target classes independently.

The JAR also contains entity tags such as:

- `demon`
- `twelve_kizuki`
- `tag_hashira`
- `kamaboko`

but the AI target layer does not primarily exploit a common faction predicate.

**Reusable lesson:** faction semantics should usually be represented as one predicate/tag/relation
service, not duplicated into a class target matrix.

**Performance state:** risk only. No runtime benchmark proves a measurable target-scan bottleneck.

## 7. Persistent NBT is the combat blackboard

A constant-pool scan across the mod shows how widespread the shared keys are.

Number of class files containing selected keys:

| Key | Classes |
|---|---:|
| `cnt1` | 324 |
| `breathes` | 246 |
| `Damage` | 231 |
| `Range` | 221 |
| `cnt2` | 221 |
| `cnt3` | 175 |
| `projectile_type` | 145 |
| `ANIMATION_1` | 141 |
| `ANIMATION_2` | 141 |
| `effect` | 106 |
| `cnt_x` | 94 |
| `mode` | 87 |
| `cnt_target` | 60 |
| `friend_num` | 49 |
| `OWNER_UUID` | 21 |

This is effectively a dynamic shared struct.

Benefits:

- generated procedures can communicate without type plumbing
- helper entities can inherit attack context cheaply

Risks:

- stale values if a new technique forgets to overwrite a field
- name collisions
- save persistence of transient state
- difficult reasoning/testing
- numeric/double protocol instead of enums/types

## 8. Shared player/NPC technique executor

Player selectors and NPC AI call the same concrete form Procedure.

Examples:

### Stone

`PlayerBreathStoneProcedure.execute`

- 1601 -> Iwa1
- 1602 -> Iwa2
- 1603 -> Iwa3
- 1604 -> Iwa4
- 1605 -> Iwa5

`AIHimejimaProcedure` uses the same five calls.

### Water

`PlayerBreathWaterProcedure`

- 601..610 -> Water forms
- 611 -> Nagi

This is the most reusable architectural choice in the target:

> selection policy is separate from attack execution.

## 9. Stone Breathing / Himejima — ver3 case study

Public ver3 notes: Stone Breathing added.

### NPC selection

`AIHimejimaProcedure.execute`

Static behavior:

- calls `ActiveHashiraProcedure`
- dispatches current mode 1601..1605
- increments attack timer
- after roughly 60 ticks resets attack counters
- calculates distance
- selects random form 1601..1605
- writes `breathes` and `mode`
- calls `DirectionProcedure`

### Current distance-filter no-op

Bytecode offsets ~467..506 perform comparisons against:

- distance 8
- form 1603
- form 1602
- form 1604

but every path converges without changing the random result.

This is a useful reverse-engineering finding: the presence of condition bytecode does not prove an
actual behavior branch.

## 10. Stone forms use detached weapon actors

`BreathesIwa1Procedure` and the other Iwa forms:

- update `cnt1/cnt2/cnt3`
- drive animation state
- move/rotate actor
- play particles/sounds
- spawn `HIMEJIMA_WEAPONS`
- call `SetRangedAmmoProcedure`
- assign form animation name
- copy red-blade state
- invoke common attack/block-destruction helpers

The weapon helper has its own entity lifecycle.

`HimejimaWeaponsOnEntityTickUpdateProcedure`:

- resolves `OWNER_UUID`
- reads owner `breathes`
- chooses form1/form2/form3/form4/form5 visuals/state
- removes helper when its form/owner state expires

`AIHimejimaWeaponProcedure`:

- resolves owner UUID
- validates `NameRanged_ranged == owner.NameRanged`
- performs repeated owner-centered OUTLINE raycasts
- keeps short local counters/random yaw/pitch adjustments
- discards itself when no longer valid

**Technique:** use a detached helper actor for the visible chain/weapon while leaving damage
authority with the owner/shared attack kernel.

## 11. Attack provenance copying

`SetRangedAmmoProcedure` transfers context into helper actors.

Observed keys include:

- `NameRanged`
- `NameRanged_ranged`
- `friend_num`
- `Player`
- `PlayerName`
- `breath`
- `demon_art`
- `skill`
- `COOLDOWN_TICKS`
- `OWNER_UUID`

This allows later damage code to reconstruct who owns a detached attack object.

Conceptually useful contract:

```text
AttackActor {
  owner
  faction/friend context
  selected technique
  cooldown/skill context
}
```

The current implementation stores it in NBT strings/numbers.

## 12. DoDamage2 — common combat kernel

`DoDamage2Procedure.execute(LevelAccessor, x, y, z, actor)`

is one of the most important classes in the JAR.

### Input protocol

Reads from actor persistent data:

- `Range`
- `Damage`
- `knockback`
- `target_type`
- `projectile_type`
- `swing`
- effect-related fields

### Owner resolution

If the actor is tagged `forge:ranged_ammo`, the Procedure resolves `OWNER_UUID`.

If it resolves to a LivingEntity, that owner becomes the meaningful damage source.

### Spatial query

Bytecode offsets ~290–361:

1. construct Vec3 attack center
2. construct zero-size AABB at center
3. inflate by `Range / 2`
4. `LevelAccessor.getEntitiesOfClass(Entity.class, box, predicate)`
5. stream/sort candidates by distance to attack center
6. iterate

### Per-target path

Calls:

- `LogicAttackProcedure` or `LogicAttack2Procedure`
- `EffectConfilmProcedure`
- `LogicGuardSuccessProcedure`
- custom `kimetsunoyaiba:kimetsu_damage_2`
- `PlayerAttackTimesProcedure`
- knockback vector helpers
- `EffectProcedure`

### Projectile interaction

If `projectile_type != 0` and a candidate is a moving Projectile not marked `strong`:

- set target projectile `flag_projectile=true`
- `projectile_type == 1` -> discard projectile server-side
- `projectile_type == 2` -> overwrite velocity with a 0.25-scaled computed vector

So sword/forms can encode:

- normal hit
- projectile cutting
- projectile deflection

through the same area-attack kernel.

## 13. Recommended attack-kernel abstraction

The invariant concept is excellent.

Instead of each attack rewriting target filtering/damage/knockback:

```text
AttackContext {
  center
  range
  damage
  knockback
  target policy
  guard policy
  projectile interaction
  effect
  owner
}
AttackKernel.apply(context)
```

The current target implements this as mutable persistent NBT.

KNEEKURA should preserve the kernel, not the untyped transport.

## 14. Projectile = mobile attack-volume emitter

Example:
`BulletSlashingMoonWhileBulletFlyingTickProcedure`

Every projectile tick:

- sets projectile `strong=true`
- writes owner attack Damage
- Range=3
- knockback=1
- calls DoDamage2 at projectile position
- expands Range to 4
- calls block destruction
- sets noGravity
- increments `life`
- discards after >18 ticks

The Damage expression includes a living-owner effect-amplifier term.

Therefore this projectile is not only:

> collide once with a target.

It is:

> carry an area-damage field through space for N ticks.

This is a useful technique for anime slash waves, but potentially expensive because it can run an
AABB query every projectile tick.

## 15. Helper-Mob attacks

Not every attack helper is an AbstractArrow.

The mod also uses PathfinderMob/helper entities such as:

- FlameDragon
- EnergyWave-like actors
- Himejima weapon actors
- string/web/weapon effects

Benefits:

- richer animation/model
- independent lifespan/state
- entity tracking
- path/movement logic if needed

Cost:

- normal Entity lifecycle/network/tick overhead

Contrast with Youkai Homecoming's virtual bullets: Kimetsu generally keeps attack actors as real
Minecraft entities.

## 16. Representative demon AI — Akaza

`AIakazaProcedure` combines:

- target state
- `cnt_x/cnt_target/cnt1/cnt2/cnt3`
- numeric `mode`
- `demon_art`
- distance/random decisions

and dispatches Akaza techniques such as:

- Ranshiki
- Kushiki
- Messhiki
- Manyou
- Shushiki
- Kishinyaeshin
- Ryusengunko
- Hiyuseisenrin
- Rashin

This is a scripted combat FSM.

It is highly expressive but hard to inspect because state is distributed over magic-number NBT.

## 17. Player input is server-executed intent

The SimpleChannel message family includes input messages for:

- change Breath/Blood Art
- Back Step
- Jump
- Special Attack
- Demon Slayer Mark

Representative:
`KeySpecialAttackMessage`

Payload:
- `type`
- `pressedms`

Server handler:

- obtains sender
- `enqueueWork`
- calls pressed/released Procedure

This is the correct security direction:

> client announces intent; server runs gameplay Procedure.

## 18. Player progression capability

`KimetsunoyaibaModVariables.PlayerVariables` stores:

- player_receiveDamage
- player_usedBreathingNum
- player_nichirincolor
- mode
- KILL_POINT_1
- KILL_POINT_2
- kill_hashira
- PlayerLevel
- playerBack
- NUM_SKILL

It serializes/deserializes NBT.

### Synchronization scope

`syncPlayerVariables(Entity)` uses:

`PacketDistributor.DIMENSION`

and sends a PlayerVariablesSyncMessage with entity ID.

So one player's variable snapshot is broadcast to the dimension, not only the owning client.

This may be intentional for remote rendering/state, but it is a broader network scope than strictly
private capability state.

## 19. Breathing mastery through use count

`PlayerAttackTimesProcedure` reads/increments:

`player_usedBreathingNum`

and grants/checks advancement milestones:

- breathing_20
- breathing_40
- breathing_60
- breathing_80
- breathing_100

It also interacts with:

- demon_slayer_mark
- transparent_world

This is a simple reusable progression structure:

```text
successful technique use
 -> mastery counter
 -> milestone advancement
 -> unlock advanced mechanics
```

## 20. Blood Art selection is item state

R key:

```text
key packet
 -> ChangeArt=true on player
 -> held Blood Art item tick
 -> consume flag
 -> change_flag on ItemStack
 -> cycle item select/select_name/select_cooltime
```

This allows different Blood Art items to own their own selection menu/state.

It also means selected technique is spread across:

- player persistent NBT
- held item NBT
- Procedure state

which complicates debugging.

## 21. GeckoLib entity animation

Many custom entities implement GeckoLib `GeoEntity`.

Representative entity state:

- synchronized ANIMATION string
- synchronized TEXTURE string
- movement animation controller
- Procedure animation controller
- local `animationprocedure`

This is the entity-side presentation stack.

## 22. PlayerAnimator pipeline

`SetupAnimationsProcedure` registers:

`kimetsunoyaiba:player_animation`

as a PlayerAnimator `ModifierLayer`, priority 1000.

`setAnimationClientside`:

- obtains the player layer
- resolves a named animation in PlayerAnimationRegistry
- creates a KeyframeAnimationPlayer
- applies it

The JAR contains **112 player animation JSON files**.

## 23. Animation opcode bridge

`PlayAnimationProcedure`:

- writes custom ANIMATION_1 from persistent `skill`
- writes ANIMATION_2 from `cnt5`
- if ANIMATION_1 != 0:
  - creates custom DamageSource `kimetsunoyaiba:start_animation`
  - calls `hurt(..., 1.0F)`

`PlayAnimationPlayerProcedure` subscribes to `LivingAttackEvent`.

When source is `start_animation`:

- read numeric animation attributes
- map them through a large opcode->animation-name chain
- apply locally
- send animation message to:
  - PLAYER
  - TRACKING_ENTITY

This is unusual.

**Reusable intent:** a central animation-event/opcode dispatcher.

**Do not preserve:** fake gameplay damage as the internal animation event bus.

Potential compatibility problems:

- damage-cancel hooks
- armor/effects/mod event listeners
- invulnerability logic
- combat trackers

can observe an animation-only event.

## 24. World generation architecture

The target combines:

1. datapack worldgen
2. runtime generator mutation

Static resources include:

- 75 biome modifiers
- 5 custom biomes
- 6 configured features
- 6 placed features
- 16 structures
- 16 structure sets
- 26 template pools
- 37 NBT structure templates

## 25. Runtime overworld biome injection

`KimetsunoyaibaModBiomes.onServerAboutToStart`:

- gets dimension stems/chunk generators
- detects `MultiNoiseBiomeSource`
- obtains climate parameter list
- injects parameter points for custom biomes including:
  - mt_sagiri
  - mt_yoko
  - mt_natagumo
- replaces ChunkGenerator biome source
- accesses NoiseBasedChunkGenerator settings
- obtains existing surface rule
- constructs additional rules
- creates a replacement NoiseGeneratorSettings
- writes a direct Holder back into the generator settings field

Access Transformer exists specifically to make this possible.

**Compatibility risk:** another worldgen mod mutating the same generator internals can conflict in
order/assumptions.

For TECH-HUB, prefer documented Forge/data worldgen hooks where they can express the intended
result.

## 26. Mugen Castle dimension

`data/kimetsunoyaiba/dimension/mugen_castle_dimension.json`

Properties:

- one custom biome: mugen_biome
- noise generator
- min Y 0
- height 128
- sea level 0
- default block AIR
- default fluid AIR
- island-noise-derived density
- surface rules output AIR

This is effectively an empty/air-oriented world substrate for authored castle structures.

Large NBT/template assets then supply the meaningful architecture.

**Technique:** separate authored mega-structure space from natural terrain generation.

## 27. Enmu Dream dimension

`enmu_dream.json` is closer to an Overworld noise stack:

- min Y -64
- height 384
- overworld climate/cave noises
- custom biome
- stone default block
- declared default fluid snow_block
- bedrock + grass/gravel/dirt surface rules

`EnmuDreamDimension` also invokes a player-entry Procedure.

This is a combination of environmental worldgen + gameplay transition behavior.

## 28. Resource volume

The JAR contains substantial authored content:

- 787 textures
- 588 model files
- 112 player animation JSONs
- 90 advancements
- 87 loot tables
- 51 recipes

This matters because reverse engineering this mod only from Java would miss a large fraction of its
design.

## 29. Performance/maintenance findings

No runtime benchmark was performed.

### 29.1 Explicit target-goal explosion

1,521 NearestAttackableTargetGoal inner classes.

Potential costs:

- class count
- memory
- goal-selector work
- update burden for every new faction entity

Recommendation:
single faction predicate/tag Goal.

### 29.2 Per-tick Procedure planner

Representative NPCs run large imperative AI Procedure logic every entity tick.

Potential optimization:
split:

- cheap state/timer tick
- lower-frequency tactical think
- current action execution

### 29.3 DoDamage2 query + sort

Every attack-kernel invocation:

- spatial entity query
- complete distance sort

Some callers do this once per attack.
Mobile projectiles can do it every tick.

Potential optimization:

- skip sorting if target order does not matter
- spatial/candidate cache for projectile swarms
- explicit max-target/nearest-target logic

### 29.4 Helper Entity density

Visually rich attacks use real helper entities.

Potential optimization:
separate:

- server damage geometry
- compact synced attack state
- client visual effects

where interaction does not require full Entity identity.

### 29.5 Persistent NBT scratch blackboard

Transient counters/attack parameters are saved as persistent Entity data.

Potential costs/risks:

- serialization noise
- stale state
- implicit coupling
- difficult migration

Use typed runtime state where possible.

### 29.6 Math.random in combat selection

Some AI paths use `Math.random()` while others use Minecraft RandomSource.

For reproducible testing/replay, one actor/world-owned RNG source is preferable.

## 30. What should be reused

Strong concepts:

1. player/NPC share one concrete technique executor
2. technique selector separated from execution
3. common typed attack-volume kernel
4. attack actors inherit owner/faction context
5. projectile as mobile attack-volume emitter
6. detached weapon visual actor
7. central animation opcode -> asset dispatcher
8. server-authoritative input procedures
9. use-count progression milestones
10. empty-space dimension + authored mega-structures

## 31. What should not be copied blindly

- ARR source/assets
- persistent NBT as universal scratch memory
- thousands of explicit target-class Goals
- artificial damage as an animation event
- AT-based ChunkGenerator surgery unless absolutely necessary
- broad dimension-wide capability sync without state-use analysis
- metadata that marks hard dependencies optional
- no-op range branches from generated Procedure code

## 32. Static completeness boundary

This pass is a whole-target architecture map, not a claim that every individual technique has been
fully reconstructed.

High-confidence facets:

- binary identity/inventory
- AI architecture
- technique protocol
- Stone case study
- damage kernel
- helper/projectile architecture
- network/persistence
- animation
- worldgen
- release history

Future optional deep dives:

- every Breathing form trajectory/area
- every Blood Demon Art
- exact NPC per-character tactic table
- animation opcode full name table
- runtime performance profiling
- old ver1/ver2 binary structural diff
