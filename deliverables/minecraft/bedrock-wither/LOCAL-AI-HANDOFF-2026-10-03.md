> **Source-completion checkpoint:** The later PR81 generation now contains ordinary phase 1 ascent/reposition/volleys, phase 2 firing/alternate charges/recovery, safe transient reloads, eligible-player targeting, actual skull impact/liquid/reflection fixes, both source-defined armor passes, and death/flicker/star-lifetime handling. Build and60 required GameTests pass locally. Read `STATUS.md` and the exact-head verification on [PR81](https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/81) for the current result; the original 18-test narrative and PR75 references below are a preserved historical snapshot.

> **Current completion amendment, 2026-10-03:** The user has chosen to finish the code without empirical Bedrock/Tank measurements. Do not use this historical handoff's measurement-gated statements as instructions to stop. Read current `STATUS.md`, `ADOPTION.md` and [SOURCE-COMPLETION-PLAN-2026-10-03.md](../../../departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCE-COMPLETION-PLAN-2026-10-03.md) first. Source-backed implementation must include ordinary AI reachability, not merely manually callable controller boundaries. Uncertain historical/adaptation values remain explicitly labelled and do not establish empirical parity. The historical health-interval arithmetic was also corrected from `/3` to `/6` after reading `SMMUL.W` in the actual native body.

# Bedrock Wither Reconstruction — Local AI Handoff

Date: 2026-10-03  
Project: KNEEKURA TECH HUB  
Deliverable: `minecraft/bedrock-wither`  
Target: Minecraft Java Edition 1.20.1 / Forge 47.2.x / Java 17  
Working branch: `jolly/bedrock-wither-reconstruction-2026-10-02`  
Draft PR: https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/pull/75

This document is a **context handoff**, not an implementation order.

Its purpose is to make the project understandable to a local coding AI without turning the handoff into a checklist of commands. The authoritative current product status remains:

- `deliverables/minecraft/bedrock-wither/STATUS.md`
- `deliverables/minecraft/bedrock-wither/ADOPTION.md`
- `deliverables/minecraft/bedrock-wither/evidence/`

At the time this handoff was drafted, the branch head before the handoff-document commit was:

`b732fde21ba0413752acba89b31b6ca7c3244922`

The latest retained **runtime-accepted source generation** is:

`da3ee83a14e3d110ffb34a0b442186a06e1cecae`

Dedicated Forge workflow run:

`37001222165`

Result:

**18 / 18 required Forge GameTests passed.**

The distinction between "branch head" and "last accepted runtime generation" is intentional. Later documentation or experimental commits must not automatically be interpreted as runtime-accepted behavior.

---

# 1. What this project is

The project is an attempt to reproduce the **observable current Bedrock Edition Wither** inside Minecraft Java Edition 1.20.1 as closely as evidence allows.

This is not intended to be:

- a "harder Java Wither";
- a BEStyleWither clone;
- a collection of guessed Bedrock-like buffs;
- a rewrite of Java `WitherBoss` with a few Mixins;
- a claim that Bedrock's closed native implementation has been recovered exactly.

The core idea is **behavioral reconstruction**.

The Wither is treated as an independent boss whose behavior is reconstructed from:

1. Mojang/Microsoft exposed Bedrock data;
2. current Bedrock Dedicated Server structure;
3. direct/current Bedrock runtime observations;
4. technical Bedrock documentation;
5. version-labelled historical reverse engineering;
6. community reports;
7. Java implementations only as engineering reference.

The Java vanilla Wither remains available as a comparison/control.

The product entity is independent:

`kneekura_bedrock_wither:bedrock_wither`

The implementation intentionally does not use Java `WitherBoss` as its behavioral superclass.

---

# 2. Why this lives inside TECH HUB without turning TECH HUB into a Wither repository

The repository has a permanent research/product boundary.

Research belongs under:

`departments/minecraft/`

The actual KNEEKURA product belongs under:

`deliverables/minecraft/bedrock-wither/`

Important product layout:

```
deliverables/minecraft/bedrock-wither/
├─ README.md
├─ STATUS.md
├─ ADOPTION.md
├─ LOCAL-AI-HANDOFF-2026-10-03.md
├─ mod/                         # actual Forge MOD source
├─ evidence/                    # retained build/GameTest evidence
└─ history/
   ├─ DECISIONS.md
   ├─ TIMELINE.md
   └─ failure-repair/
```

The Wither work is intentionally a **consumer of TECH HUB knowledge**, not the identity of TECH HUB itself.

Reusable knowledge discovered while reconstructing the boss is extracted back into the Minecraft technical department rather than buried inside the product.

A major reusable note is:

`departments/minecraft/techniques/boss-combat-state-machines.md`

---

# 3. Project owner's key constraint: Bedrock first

A central project decision came directly from the project owner.

The owner has personally played **BEStyleWither** and does **not** consider it especially close to the real Bedrock Wither.

Therefore BEStyleWither is not treated as a gameplay specification.

Its role is limited to questions such as:

- how another Java developer isolated a charge attack;
- how Mixins were used;
- which compatibility problems appeared;
- what failure/repair history can be learned from;
- what implementation approaches are convenient in Java.

Its timers, spawn counts, health logic, phase ordering and constants are **not accepted merely because the code exists**.

The project is intentionally willing to write a more complex Java implementation if that is required to match Bedrock more faithfully.

---

# 4. Evidence hierarchy used by the project

The practical hierarchy is:

## Highest-value current evidence

### Mojang/Microsoft exposed Bedrock definitions

These describe public Bedrock components, goals, projectiles, rendering, models and Molang.

They are primary evidence for anything they explicitly expose.

However, they are **not assumed to describe the entire runtime**.

The Wither is one of the entities for which Mojang documents unique/native behavior beyond ordinary component JSON.

## Current BDS structural evidence

Generated Bedrock Dedicated Server headers are used to understand:

- native class boundaries;
- field names;
- state decomposition;
- native method boundaries;
- enum identities;
- ECS systems;
- return types.

This evidence can prove that a state or function exists without proving the hidden function body or exact constant.

Current mapped structural anchor used by this project:

**BDS 1.26.51.1**

via current LeviLamina generated headers.

## Current runtime observation / technical behavior documentation

This is especially important where native hardcoded behavior overrides exposed JSON.

Examples already discovered:

- public Wither JSON exposes movement `0.25`;
- runtime/native evidence supports effective speed `0.6`.

Similarly:

- public JSON exposes health `600`;
- runtime/native behavior yields difficulty-specific `300 / 450 / 600`.

## Historical Bedrock native reverse engineering

Historical decompiled/generated Bedrock code is useful when the same conceptual field or method still exists in current BDS.

It is used to answer questions such as:

- what a current field probably represented;
- how two current fields may have interacted historically;
- what scenario deserves modern measurement.

It does **not** automatically supply current constants.

## Community reports

Reddit, forums and videos are discovery material.

They are particularly useful for:

- rare bugs;
- phase transition anomalies;
- tunneling/charge behavior;
- lag caused by mass terrain destruction;
- reflection experiments;
- practical reproduction scenarios.

A popular Reddit comment is not promoted to implementation truth just because many users agree with it.

## Java implementations

Java vanilla and third-party mods are adaptation references.

They answer:

- what Java API primitive is available;
- what can be reused safely;
- where loader compatibility problems occur.

They do not define Bedrock gameplay.

---

# 5. Important primary and specialist sources

## 5.1 Microsoft Creator — current Vanilla Wither definition

https://learn.microsoft.com/en-us/minecraft/creator/reference/source/vanillabehaviorpack_snippets/entities/wither?view=minecraft-bedrock-stable

Important exposed information includes:

- health/max health base 600;
- movement 0.25 at the exposed component layer;
- `can_fly`;
- `minecraft:behavior.wither_target_highest_damage`;
- `minecraft:behavior.wither_random_attack_pos_goal`;
- nearest attackable target distance 70;
- collision box 1×3;
- boss HUD configuration;
- damage sensor;
- breathable/fire/freezing behavior.

This page is necessary, but **not sufficient by itself**, because native runtime overrides exist.

## 5.2 Microsoft Creator — unique entity behaviors

https://learn.microsoft.com/en-us/minecraft/creator/documents/uniqueentitybehaviors?view=minecraft-bedrock-stable

This is conceptually important because the project repeatedly encountered behavior that does not live completely in the public entity JSON.

## 5.3 Microsoft Creator — Wither-specific goals

Highest damage:

https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_wither_target_highest_damage?view=minecraft-bedrock-stable

Random attack position:

https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_wither_random_attack_pos_goal?view=minecraft-bedrock-stable

These are useful for confirming that Bedrock has dedicated Wither AI concepts rather than merely generic nearest-target/random-stroll behavior.

---

# 6. Mojang bedrock-samples — primary source repository

Repository:

https://github.com/Mojang/bedrock-samples

Pinned revision used by this reconstruction:

`46ba6ea985fb5a92d79a9419198f10dda14c199d`

Important files include:

## Server behavior

`behavior_pack/entities/wither.json`

`behavior_pack/entities/wither_skull.json`

`behavior_pack/entities/wither_skull_dangerous.json`

The skull definitions exposed several important differences:

- normal skull launch power 1.2;
- dangerous skull launch power 0.6;
- inertia 1.0;
- dangerous `reflect_on_hurt=true`;
- dangerous `max_resistance=4.0` in Bedrock explosion semantics;
- projectile collision box 0.15×0.15;
- Wither-effect durations by difficulty;
- explosion power 1.

The Java implementation translates engine semantics where necessary rather than assuming the same raw numeric value has the same meaning in both engines.

## Client / visual definition

`resource_pack/entity/wither.entity.json`

`resource_pack/models/entity/wither_boss.geo.json`

`resource_pack/models/entity/wither_boss_armor.geo.json`

`resource_pack/animations/wither_boss.animation.json`

`resource_pack/render_controllers/wither_boss.render_controllers.json`

`resource_pack/render_controllers/wither_boss_armor.render_controllers.json`

These are the preferred source for:

- three-head geometry;
- body/tail animation;
- base scale;
- spawn swelling;
- shield/armor geometry;
- Molang-driven visibility.

Notably, current armor visibility is based on:

`query.is_shield_powered`

The product intentionally models Bedrock's `AirAttack`-style state separately from the structural native `Phase` field.

---

# 7. Current BDS structural source

## LeviLamina

https://github.com/LiteLDev/LeviLamina

Current structural revision studied:

`1bab1522cdfd697d241e77fe60f19b9db2a20a5a`

The relevant generated header set corresponds to BDS 1.26.51.x / server 26.51.1.

Especially useful files:

`src/mc/world/actor/boss/WitherBoss.h`

`src/mc/world/actor/ai/goal/target/WitherTargetHighestDamage.h`

`src/mc/world/actor/ai/goal/WitherRandomAttackPosGoal.h`

`src/mc/entity/components/WitherBossPreAIStepResult.h`

`src/mc/entity/components_json_legacy/ProjectileComponent.h`

Wither death ECS files:

`src/mc/entity/systems/WitherBossPreAIStepSystem.h`

`src/mc/entity/systems/death/ServerWitherBossTickDeathSystemImpl.h`

`src/mc/entity/systems/death/ClientWitherBossTickDeathSystemImpl.h`

`src/mc/entity/utilities/death/WitherBossDeathWrapper.h`

The generated current Wither structure exposes many useful field names:

- `mPhase`
- `mShieldHealth`
- `MAX_SHIELD_HEALTH`
- `mWantsToExplode`
- `mCharging`
- `mChargeDirection`
- `mChargeFrames`
- `mPreparingCharge`
- `mProjectileCounter`
- `mTimeTillNextShot`
- `mFireRate`
- `mSecondVolley`
- `mMainHeadAttackCountdown`
- `mNumSkeletons`
- `mMaxSkeletons`
- `mHealthIntervals`
- `mLastHealthValue`
- `mFramesTillMove`
- `mWantsMove`
- `mIsPathing`
- three head rotation/update arrays.

The current native attack-type enum exposes:

- Charge
- HurtExplosion
- Projectile

This is why the product does not model all terrain destruction as one generic "Wither break blocks" function.

The current `WitherTargetHighestDamage` header exposes a helper returning `Player*`, which is a major reason priority-1 threat targeting is currently modeled as a Player-oriented highest-damage path rather than generic LivingEntity priority.

---

# 8. Bedrock runtime data / BDS identity sources

BDS package identity:

https://github.com/LiteLDev/bds

Runtime-data project:

https://github.com/LiteLDev/bedrock-runtime-data

These are useful when correlating generated headers to actual BDS releases.

At the time of this investigation, the internal structure work was pinned around 1.26.51.1. A newer BDS package may exist before generated headers have caught up; "newest downloadable BDS" and "newest structurally mapped BDS" are not automatically the same thing.

---

# 9. Historical Bedrock reverse engineering

Repository:

https://github.com/PeratX/source

Pinned historical revision:

`ea30a251dd8fd16a7bd2e568209797a9c7be970f`

Important historical files:

`Minecraft/Entity/WitherBoss.c`

`Minecraft/Entity/WitherSkull.c`

`Minecraft/Goal/WitherRandomAttackPosGoal.c`

`unmapped/WitherTargetHighestDamage.c`

This source is **not current-authoritative**.

Its value comes from relationships that still line up with current BDS structures.

Examples where it proved useful:

- highest-damage Player tracking;
- first-phase/second-phase state relationships;
- charge direction/frame separation;
- hurt-reaction timer;
- destruction range 1 versus charge range 2;
- center-head projectile counter;
- old spawn-frame handling;
- owner heal-on-kill for Wither skulls;
- movement runtime override;
- old death/swell fields.

Historical constants are kept version-labelled instead of silently becoming modern Bedrock constants.

Detailed project notes:

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/HISTORICAL-BEDROCK-REVERSE-NOTES.md`

---

# 10. Bedrock technical documentation

## Bedrock Wiki — Wither Boss

https://bedrockwiki.com/books/mobs/page/wither-boss/revisions/692/changes

This has been particularly useful as a current gameplay-observation source.

Important reported behavior includes:

- Easy/Normal/Hard health 300/450/600;
- two combat stages;
- passive dangerous skull behavior;
- 3 normal + 1 dangerous firing cycle;
- approximately seven-second gap between cycles;
- firing speed changes with damage;
- phase-1 hurt reaction:
  - 20-tick delay;
  - 4×6×4 terrain destruction;
  - dangerous skull;
- half-health phase transition;
- three Wither Skeletons;
- phase-2 projectile immunity;
- charge attack;
- roughly 20-tick charge duration;
- 6×8×6 block destruction each active charge tick.

This is a strong technical observation source, but it is still community-maintained and explicitly work-in-progress.

The project keeps measured/corroborated values separate from weaker descriptions.

## Bedrock entity/NBT field references

A useful detailed Wither NBT reference is mirrored here:

https://wiki.ronlab.site/content/minecraftwiki_en_all_maxi_2025-11/Bedrock_Edition_level_format/Entity_format

A machine-readable schema carrying the same Wither fields is also visible in:

https://app.unpkg.com/mcbe-leveldb@1.21.0/files/nbtSchemas.ts

Especially useful field semantics:

- `AirAttack`
- `dyingFrames`
- `firerate`
- `Invul`
- `lastHealthInterval`
- `Phase`
- `ShieldHealth`
- `SpawningFrames`
- `swellAmount`
- `oldSwellAmount`
- `overlayAlpha`

Important current interpretation used by the product:

### AirAttack

- 1 = first/aerial phase and shield hidden;
- 0 = second phase and powered shield visible.

### Phase

Phase exists structurally, but the NBT reference explicitly distinguishes it from the state that directly controls visible shield behavior.

### lastHealthInterval

Described as the greatest multiple of 75 below the lowest health the Wither has reached; healing does not increase it.

This is why the current product no longer treats the old historical `maxHealth / 3` interval formula as a current runtime rule.

### SpawningFrames / dyingFrames

These reinforce separate spawn and death controllers rather than a single generic invulnerability timer.

---

# 11. Minecraft Wiki / general current behavior references

Main Wither article:

https://minecraft.wiki/w/Wither

Bedrock entity-format reference:

https://minecraft.wiki/w/Bedrock_Edition_level_format/Entity_format

These are useful for current gameplay descriptions, difficulty values and version history.

When these pages conflict with Bedrock-specific code structure or direct current evidence, the disagreement is retained instead of silently choosing whichever value is more convenient.

---

# 12. Java 1.20.1 adaptation references

## Java Wither mappings

https://mappings.dev/1.20.1/net/minecraft/world/entity/boss/wither/WitherBoss.html

Useful for understanding the Java boss implementation and deciding what **not** to inherit.

Java `WitherBoss` contains Java-specific private timers, head scheduling and terrain-destruction behavior. This was a major reason for using a standalone Monster-based entity.

## Forge 1.20.1 documentation

https://docs.minecraftforge.net/en/1.20.1/

Useful for loader/API integration, not for Bedrock gameplay facts.

---

# 13. BEStyleWither — prior art only

Repository:

https://github.com/MORIMORI0317/BEStyleWither

Reviewed 1.20-era track:

branch `1.20`

commit:

`ab98547f3e8e0dac83a814d5133a113d4bfd9e40`

Later/frontier track reviewed:

`e658d45ea3d2b6b6b16d6a02ee6b736ce9c411d2`

Detailed review inside TECH HUB:

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/PRIOR-ART-BESTYLEWITHER.md`

Its strongest value to this project has been:

- charge attack decomposition;
- transition-state implementation ideas;
- projectile adaptation ideas;
- compatibility failure history.

Its gameplay constants are deliberately non-authoritative.

One especially important lesson came from BEStyleWither Issue #4:

https://github.com/MORIMORI0317/BEStyleWither/issues/4

A delayed death implementation kept the Wither semantically alive while playing a custom death sequence, breaking kill-state/advancement compatibility.

That failure helped establish the KNEEKURA rule:

**semantic death and visual death are separate concerns.**

The KNEEKURA boss enters semantic death normally and layers Bedrock-style death ticking/visual state around it.

---

# 14. Reddit / community observations worth keeping nearby

Reddit is not a specification source here. These links are useful because they expose current edge cases that are easy to miss in clean documentation.

## Phase-2 downward tunneling and severe block/item lag

August 30, 2026:

https://www.reddit.com/r/Minecraft/comments/1w2ijls/the_bedrock_wither_has_to_be_broken/

The report describes normal first phase followed by second-phase deep burrowing, very large terrain destruction and extreme client lag from the resulting environment.

This is useful for reproducing practical stress scenarios around charge/destruction and item drops.

## Half-health drilling behavior

September 28, 2026:

https://www.reddit.com/r/minecraftbedrock/comments/1wsezmj/is_the_wither_supposed_to_do_that/

The thread shows disagreement over whether extended downward drilling is intended behavior or a persistent bug.

That disagreement is important. The project should not automatically reproduce such behavior as a core rule without version-bound evidence.

## Wither reaching bedrock through phase-2 destruction

April 13, 2026:

https://www.reddit.com/r/Minecraft/comments/1skc28g/whyd_he_blast_all_the_way_to_bedrock/

Useful as a modern anecdotal example of downward charge/tunneling and possible phase-transition failure.

## Large chunk-scale destruction near half health

September 26, 2026:

https://www.reddit.com/r/Minecraft/comments/1wqum13/bedrock_since_when_can_the_wither_destroy_entire/

Useful for stress/performance scenarios and for distinguishing intended 6×8×6-per-tick charge destruction from pathological repeated downward movement.

## Dangerous/blue skull redirection experiments

March 15, 2026:

https://www.reddit.com/r/BedrockRedstone/comments/1ruly4a/new_wither_tech/

Useful because the discussion focuses on redirectable blue skull behavior and practical manipulation.

The current BDS ProjectileComponent structure independently exposes:

- `mReflect`
- `mReflectImmunityTicks`
- `mLastReflectActor`
- `_tryReflectOnHurt(...)`

so community reflection experiments are especially relevant for designing direct Bedrock tests.

## General current Bedrock Wither mobility/difficulty discussion

February 6, 2026:

https://www.reddit.com/r/MinecraftBedrockers/comments/1qxkmfp/bedrock_difficulty_vs_java_difficulty_in_general/

Useful as a community description of how Bedrock Wither mobility, charge behavior and long Wither effect differ from the Java fight.

Again, this is scenario/discovery evidence rather than a numeric specification.

---

# 15. Current product architecture

The product currently contains these main implementation units:

```
BedrockWitherEntity
BedrockWitherState
BedrockWitherStateMachine
BedrockWitherRuntimeState

BedrockWitherSpawnController
BedrockWitherPhaseController
BedrockWitherVolleyController
BedrockWitherSideHeadController
BedrockWitherHeadTrackingController
BedrockWitherSpecialMovementController
BedrockWitherDashController
BedrockWitherHurtReactionController
BedrockWitherDestructionController
BedrockWitherAttackController

BedrockWitherThreatLedger
BedrockHighestDamageTargetGoal

BedrockWitherSkullEntity
BedrockWitherBlockRules

BedrockWitherDeathController

BedrockWitherModel
BedrockWitherRenderer
BedrockWitherArmorLayer
```

There is deliberately no single monolithic "Wither AI" class.

The decomposition mirrors the fact that current BDS itself exposes separate phase, charge, firing, side-head, movement, block destruction, spawn and death state.

---

# 16. Current implementation progress

The following summary reflects the current product `STATUS.md`, not old conversation state.

## Independent boss identity

Implemented.

The Bedrock-style boss is a standalone entity and does not globally replace Java `minecraft:wither`.

## Difficulty health

Implemented as:

- Easy: 300
- Normal: 450
- Hard: 600

This is a good example of native override behavior because public JSON exposes base 600, while runtime/native evidence resolves difficulty-specific values.

## Effective movement speed

Implemented as 0.6.

Public JSON exposes 0.25, but historical native hardcoded reload and current gameplay documentation support effective runtime 0.6.

This is one of the clearest examples that Behavior Pack JSON is not always the final runtime truth.

## Collision / search / boss surface

Implemented:

- collision box 1×3;
- follow/search range 70;
- max-turn adaptation 180;
- undead family;
- fire immunity;
- freezing immunity;
- water breathing;
- undead-source damage rejection;
- XP 50;
- boss HUD range 55;
- sky darkening.

## Targeting

Implemented Bedrock-oriented priority structure:

1. highest-damage Player path;
2. hurt-by-target;
3. nearest visible eligible target.

The broad threat ledger remains useful for diagnostics even though the dedicated highest-damage helper is Player-oriented.

## Spawn sequence

Modern target implemented as 220 ticks / approximately 11 seconds.

Important version history:

- historical Bedrock native code used 200;
- current reconstruction uses 220 because the project targets modern Bedrock behavior.

Spawn and combat tests are separated so spawn invulnerability cannot accidentally make later combat tests pass.

## Normal and dangerous Wither skulls

Custom projectile entity exists.

Implemented/captured behavior includes:

- normal launch power 1.2;
- dangerous launch power 0.6;
- inertia 1.0;
- dangerous reflection gate;
- explicit explosion lifecycle;
- Java-semantic translation for dangerous block resistance;
- explicit unbreakable exceptions;
- direct-impact damage:
  - Easy 5
  - Normal 8
  - Hard 12
- owner heal-on-kill = 5;
- Wither II:
  - Normal 200 ticks
  - Hard 800 ticks.

The exact dangerous-skull reflection vector and reflection-immunity timer remain unresolved.

## Main/center-head firing cycle

Implemented structural behavior:

- 3 normal skulls;
- then 1 dangerous skull;
- observed approximately 7-second inter-volley period.

The project deliberately does **not** claim that the exact current health-dependent ticks-per-shot have been fully reconstructed.

Current NBT-style `lastHealthInterval` uses monotonic 75-HP buckets.

## Side heads

Current product includes:

- side-head scheduler;
- independent side targets;
- passive dangerous-skull behavior;
- Normal/Hard targeted side-head behavior from Bedrock-native structure.

The historical/currently provisional attack-range value of 30 is not considered final runtime parity.

## Head tracking

Three independent head pitch values are server-authored and synchronized for rendering.

This is based on Mojang animation/query structure and current BDS three-head state.

## Phase transition

Implemented structure includes:

- half-health trigger;
- native-like phase 1 → 0;
- separate `AirAttack` state;
- one-shot transition latch;
- Easy: no skeletons;
- Normal/Hard: 3 Wither Skeletons;
- phase-2 projectile immunity;
- transition explosion isolated behind an evidence-labelled value.

Exact modern transition action ordering and current binary confirmation of explosion power are still open.

## Powered shield / armor

`AirAttack` is synchronized separately from structural `nativePhase`.

Current product semantics:

- first/aerial phase: AirAttack=true, powered shield hidden;
- second phase: AirAttack=false, powered shield visible.

Official Bedrock inflated armor geometry is implemented.

Because Bedrock armor texture assets are not redistributed, Java's bundled Wither armor texture is currently used as a temporary visual substitute.

Full Bedrock white/blue two-layer texture parity remains a visual/Tank concern.

## Phase-1 hurt reaction

Implemented:

- 20-tick non-resetting delay;
- 4×6×4 block candidate geometry;
- one dangerous skull.

The exact modern no-target/fallback dangerous-skull aim remains adaptation rather than proven Bedrock parity.

## Destruction geometry

Accepted and implemented from a strong cross-layer derivation:

Historical native calls:

- hurt destruction range=1;
- charge destruction range=2.

Combined with official 1×3 Wither collision box and inclusive block iteration:

- range 1 → 4×6×4;
- range 2 → 6×8×6.

Current Bedrock technical observation reports exactly the same cuboids.

## Phase-2 dash

Implemented execution structure includes:

- separate charge direction;
- charging state;
- charge frame counter;
- 20 active ticks;
- range-2 / 6×8×6 block destruction each active tick;
- 15 entity damage.

Still unresolved:

- exact current dash speed;
- preparation trigger/duration;
- collision termination nuances.

The controller therefore separates the accepted execution structure from measurement-gated speed/trigger information.

## Special phase-1 movement

A dedicated `BedrockWitherSpecialMovementController` boundary now exists.

It models the native-shaped relationship between:

- phase-1 aerial state;
- live target;
- `wantsMove`;
- pathing.

The implementation deliberately avoids inventing unresolved current destination radius, flight multiplier or cooldown constants.

## Death lifecycle

A dedicated `BedrockWitherDeathController` now exists.

The implementation preserves **semantic death immediately** while allowing a Bedrock-style extended death visual/removal sequence.

This follows both:

- current BDS dedicated Wither death ECS structure;
- the compatibility lesson learned from BEStyleWither Issue #4.

Current product also carries native-shaped visual/death state:

- death ticks;
- swell/old swell;
- overlay;
- related visual state.

The exact modern death duration, final explosion timing, XP timing and full swell/flicker equations are still not claimed as complete parity.

## Loot

Bedrock Wither Nether Star loot contract is present.

---

# 17. Current visual implementation

Official Bedrock geometry has been converted to Java model parts rather than inheriting the Java Wither model as authority.

Important Bedrock visual inputs already used:

- base scale 2;
- three heads;
- shoulder/rib/tail layout;
- body oscillation;
- independent head-X queries;
- shared target-Y rotation behavior;
- inflated armor geometry;
- powered-shield state.

The product does not redistribute Bedrock texture bytes.

Visual verification is still weaker than server/GameTest verification because full paired Tank acceptance has not yet occurred.

---

# 18. Current automated verification

The dedicated Forge workflow is:

`.github/workflows/bedrock-wither-build.yml`

It builds the standalone product and runs Forge GameTests.

The latest retained accepted generation:

`da3ee83a14e3d110ffb34a0b442186a06e1cecae`

Workflow:

https://github.com/genkimorimori252525-oss/KNEEKURA-TECH-HUB/actions/runs/37001222165

Result:

**18 / 18 required tests passed.**

Current retained GameTest evidence:

`deliverables/minecraft/bedrock-wither/evidence/gametest-2026-10-02.json`

The evidence currently covers, among other things:

- entity dimensions/range/effective speed;
- difficulty health mapping;
- 220-tick spawn/invulnerability;
- undead-source rejection;
- three independent head target slots;
- skull type behavior;
- 5/8/12 skull impact mapping;
- block-resistance translation;
- 3+1 center-head projectile order;
- 75-point health bucket tracking;
- half-health transition;
- AirAttack/powered-shield state;
- phase-2 projectile immunity;
- hurt/charge destruction geometries;
- 20-tick hurt reaction;
- dangerous hurt-reaction skull;
- 20-tick dash execution;
- status-effect immunity;
- isolated GameTest batches;
- semantic death versus visual death;
- special movement gating;
- side-head behavior;
- synchronized three-head pitch.

This does **not** mean direct Bedrock parity has been proven. It means the current Java implementation is internally behaving according to the currently accepted reconstruction contract.

---

# 19. Important failure / repair history

The failure history is part of the technical value of this project.

Directory:

`deliverables/minecraft/bedrock-wither/history/failure-repair/`

## BWR-0001 — wildcard Optional compile failure

A Java generic capture issue in the threat ledger.

Lesson: preserve flexible subtype inputs and make widening explicit at the return boundary.

## BWR-0002 — JSON-only skull impact inference

The public skull JSON lacked an explicit impact-damage field, so the first implementation wrongly concluded that Bedrock skulls had no native direct-hit damage.

Historical native and current runtime evidence disproved that assumption.

Lesson:

**absence from Bedrock JSON is not proof of absence at runtime.**

## BWR-0003 — semantic method rename broke compile

A local refactor renamed the call site but not the declaration.

Lesson: evidence-status wording changes can still create ordinary code drift.

## BWR-0004 — zero spawn frames skipped spawn sequence

A native-shaped field existed but was left at zero while zero had real gameplay meaning.

Lesson: "unknown/uninitialized" must not silently become a valid runtime value.

## BWR-0005 — Java WitherSkull superclass mismatch

Java's owned Wither skull direct hit used 8 damage on Easy, while Bedrock requires 5/8/12.

Lesson: superclass reuse is valid only at a verified semantic boundary.

## BWR-0006 — volley GameTest AI interference

A controller-unit test allowed ambient server AI ticks to alter the state it was trying to test.

Lesson: synchronous controller tests need fully owned preconditions.

## BWR-0007 — health-bucket test assumed Hard-scale HP

A test used absolute health values that were invalid under lower difficulty max-health domains.

Lesson: difficulty-dependent boss tests should derive fixtures from the actual runtime domain.

These records are valuable context for a local AI because they show where "obvious" assumptions have already failed.

---

# 20. Important conceptual lessons already established

## Behavior Pack JSON is not always runtime truth

The Wither provides concrete examples:

- JSON movement 0.25 versus effective native/runtime 0.6;
- JSON health base 600 versus difficulty 300/450/600;
- JSON omission of skull direct-hit behavior despite native hit processing.

This has become a reusable TECH HUB technique:

**exposed component → native override → runtime observation**

## Structural evidence is different from body evidence

A current BDS header proving that `mChargeFrames` exists does not prove its value.

A current header proving `WitherAttackType::Charge/HurtExplosion/Projectile` exists is strong evidence that these are distinct native paths.

The project tries to preserve that difference.

## Historical reverse engineering is valuable but version-bound

Old native code has repeatedly predicted current structure correctly.

It has also contained constants that changed.

Historical code is therefore used as a relationship map, not a current constants table.

## Java reuse is adaptation, not authority

Sometimes Java happens to provide the right primitive.

Examples:

- EnergySwirl-style UV motion can reproduce the Bedrock white armor motion formula;
- Java Wither Skull APIs are convenient for ownership/effect integration.

But every reused method is checked for semantic leakage.

## Semantic and visual lifecycle are separate

Spawn, phase transition and death each have:

- gameplay state;
- visual state;
- timing state.

The project deliberately avoids collapsing them into one timer/boolean.

---

# 21. Current unresolved areas

The following remain open or only partially resolved.

They are not failures; they are the parts where the evidence is not yet strong enough for a final parity claim.

## Phase-1 special reposition/path generation

Known structurally:

- special Wither goal;
- phase-1 relationship;
- target relationship;
- wantsMove/pathing state;
- firing-delay relationship.

Still unresolved:

- exact modern destination radius;
- vertical distribution;
- speed multiplier;
- move interval;
- stop conditions.

## Exact health-dependent center-shot cadence

Known:

- 3+1 projectile identity cycle;
- firing accelerates as damage accumulates;
- inter-volley pause around seven seconds;
- `firerate` is separate from volley pause;
- `lastHealthInterval` tracks monotonic 75-point lowest-health buckets.

Still unresolved:

- exact current ticks-per-shot at each acceleration stage;
- exact relation between current `mSecondVolley`, `mDelayShot`, `mTimeTillNextShot` and visible firing rhythm.

## Passive dangerous-skull interval

The behavior exists and is represented.

Exact current interval still needs stronger direct measurement.

## Dangerous-skull reflection

Known:

- only dangerous skull is reflectable;
- current ProjectileComponent contains:
  - `mReflect`;
  - `mReflectImmunityTicks`;
  - `mLastReflectActor`;
  - `_tryReflectOnHurt(...)`.

Still unresolved:

- exact reflection vector reconstruction;
- exact immunity-tick value;
- repeated-reflector semantics.

## Phase transition

Known broadly:

- half health;
- second phase;
- shield/AirAttack change;
- skeleton summon;
- projectile immunity;
- explosion.

Still unresolved:

- exact modern tick ordering;
- exact current binary confirmation of explosion power.

## Dash

Known:

- execution state exists;
- direction and frame counters exist;
- ~20 active ticks;
- block destruction geometry;
- entity damage.

Still unresolved:

- exact preparation trigger;
- exact speed;
- exact collision/termination behavior.

## Per-attack block rules

Current BDS proves `canDestroy(Block, WitherAttackType)`.

This means Charge, HurtExplosion and Projectile may not share a perfectly identical block whitelist/blacklist.

The shared current product rules are conservative.

Exact modern per-attack differences remain open.

## Shield internals

The product has a useful AirAttack-driven visibility model.

Still unresolved:

- exact meaning of `ShieldHealth`;
- exact meaning/value of `MAX_SHIELD_HEALTH`;
- full relationship between shield health, flicker and armor render state.

## Death

Current BDS gives an unusually strong structural map.

Still unresolved:

- exact current total duration;
- exact explosion tick/power;
- exact XP spawn tick;
- full swell/flicker/overlay equations.

## Full visual/Tank parity

Server-side GameTests are much stronger than current visual acceptance.

The real Bedrock-versus-Java visual/trajectory comparison is still a future acceptance layer.

---

# 22. Current source-of-truth files inside the repository

A local AI can understand most of the project by reading these in this order conceptually, although this document does not prescribe a work sequence.

## Product status

`deliverables/minecraft/bedrock-wither/STATUS.md`

## Product adoption / what external research is actually allowed to influence

`deliverables/minecraft/bedrock-wither/ADOPTION.md`

## Product identity

`deliverables/minecraft/bedrock-wither/README.md`

## Design

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/DESIGN.md`

## Source ledger

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/SOURCES.md`

## Current BDS structure map

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/BDS-STRUCTURE-2026-10-02.md`

## Historical Bedrock reverse notes

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/HISTORICAL-BEDROCK-REVERSE-NOTES.md`

## BEStyle prior-art review

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/PRIOR-ART-BESTYLEWITHER.md`

## Acceptance

`departments/minecraft/design/2026-10-02-bedrock-wither-reconstruction/ACCEPTANCE.md`

## GameTest evidence

`deliverables/minecraft/bedrock-wither/evidence/gametest-2026-10-02.json`

## Failure/repair history

`deliverables/minecraft/bedrock-wither/history/failure-repair/`

## Reusable extracted technology

`departments/minecraft/techniques/boss-combat-state-machines.md`

---

# 23. How to interpret "complete"

This project has already moved well beyond a skeleton.

It has:

- a real independent Forge boss;
- current/native-oriented state decomposition;
- projectiles;
- phases;
- spawn;
- death boundary;
- model/rendering;
- shield state;
- side-head behavior;
- targeting;
- block destruction;
- dash execution;
- automated GameTests;
- retained evidence and failure history.

However, "18/18 tests pass" means:

> the Java implementation satisfies the current KNEEKURA reconstruction contract.

It does **not** mean:

> the reconstruction is already proven indistinguishable from current Bedrock.

The remaining gap is increasingly about **exact modern hidden constants and direct paired measurement**, not basic architecture.

That distinction is important.

---

# 24. Overall project state at handoff

The project is in a healthy state.

The architecture has stabilized around a Bedrock-first, evidence-layered standalone boss rather than a Java-Wither patch.

Several early assumptions have already been corrected through actual CI/GameTest failures, and those corrections materially improved the methodology.

The strongest current qualities are:

- research/product separation;
- Bedrock-first evidence discipline;
- native-structure awareness;
- no dependence on BEStyleWither for gameplay truth;
- explicit handling of uncertain values;
- high observability;
- repeatable Forge GameTests;
- retained repair history;
- careful separation of current evidence from historical reverse engineering.

The largest remaining uncertainties are concentrated in a relatively small number of hidden native timing/movement/visual details:

- special movement destination rules;
- accelerated shot cadence;
- passive dangerous-skull timing;
- reflection vector/immunity;
- dash trigger/speed;
- precise transition ordering;
- shield-health internals;
- exact death timing and visuals.

The current product is therefore best described as:

**a substantial Bedrock-native-oriented reconstruction with a strong tested core, not yet a final parity release.**

The project owner considers real Bedrock behavior the reference target. Java prior art is useful only insofar as it helps implement that target without contaminating it.
