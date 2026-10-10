# Scape and Run: Parasites — Combat, Projectile, AI, Adaptation (2026-10-11)

**Status: original JAR targeted static bytecode analysis, NOT whole-target COMPLETE, runtime NOT_RUN.**  
Prior discovery-stage notes remain historical: [RECONNAISSANCE-2026-10-11.md](RECONNAISSANCE-2026-10-11.md).  
Procedure: [ANALYSIS-WORKFLOW.md](../../ANALYSIS-WORKFLOW.md) and [ANALYSIS-SPEC-v1.md](../../ANALYSIS-SPEC-v1.md).  
Exact evidence identity: [ARTIFACT-RECEIPT-2026-10-11.json](ARTIFACT-RECEIPT-2026-10-11.json).

## Source/track boundary

- **COMPARATIVE stable original**: user-provided SRParasites-1.12.2v1.9.21.jar, 27,022,807 bytes, SHA-256 **f803ab3882bc8047858a23e2376aaa8fb87d7e54a324b9183b4a033ee076ddea**. Metadata confirms Minecraft 1.12.2, version 1.9.21, modid srparasites, Dhanantry.
- Archive inventory: **2,465** entries; **868** Java class files, **621** PNGs, **373** OGGs; 125 class↔registry-ID mappings read from original registration bytecode. 306 selected classes / 3,944 method bodies indexed through JDK javap, with additional supporting classes checked separately.
- **FRONTIER**: 1.10.9 Alpha (1.12.2 Forge); release metadata only, no Alpha binary review.
- **ANCHOR port target**: Minecraft 1.20.1 Forge; no original 1.20.1 target JAR and NO compatibility or runtime test.
- Uploaded JAR has not been binary hash compared to an official release download. It is original distributed-style binary evidence, **not a proven upstream source-code snapshot**.
- Original project is **All Rights Reserved**. JAR, decompiled source, PNGs, OGGs and raw bytecode are NOT distributed in TECH-HUB. All descriptions below are derived facts and exact internal-class locators.
- **SRPMixins is an independent extension** and must not be confused with the unmodified original; in this file, all cited original-class behavior is inspected from the uploaded original JAR unless explicitly marked DESIGN.

## 1. Combat architecture

Original code separates Mob goal registrations (entity class method func_184651_r), perception, attack scheduler, projectile entity behavior, and effects. Mapped core components:

| Module | Bytecode entrypoint | Responsibility |
| --- | --- | --- |
| Timed direct volley | entity/ai/EntityAIAttackProjectile.class — func_75246_d, shoot | Target check, windup, shot count, interval, EntityCanShoot.getProj and entity spawn |
| Ranged mode | entity/ai/EntityAIAttackRangedStatus.class | Uses vanilla IRangedAttackMob-style scheduling |
| Melee/range switch | entity/ai/EntityAIAttackMeleeRangeSwitch.class — func_75246_d | Switches work/task based on visible target and configurable distance |
| Melee AOE | entity/ai/EntityAIAttackMeleeStatusAOE.class — checkAndPerformAttack | Dispatches EntityCutomAttack.attackEntityAsMobAOE, with 20-tick cooldown in this method |
| Flight targeting | entity/ai/EntityAIFlightAttack.class | Target acquisition and retention under line-of-sight/filters |
| Vertical constraint | entity/ai/EntityAIFlightLimits.class | Corrects Y motion/flight limits |
| Evasion | entity/ai/EntityAIEvade.class; EntityAIEvadeDash.class | Random left/right strafe and lateral dash under target-distance/visibility conditions |
| Ancient reinforcement | entity/ai/EntityAIAncientSummon.class | Target-bound summon after telegraph, with 20-tick interval |
| Individual learning | entity/ai/misc/EntityPMalleable.class | Damage identity + resistance counters; persistence |
| Colony/world memory | world/SRPWorldData.class; util/ParasiteEventEntity.class; util/handlers/SRPEventHandlerBus.class | Shared damage identity memory, death contribution, next-generation adaptation |

### 1.1 Verified volley tuple registry

EntityAIAttackProjectile uses (cooldown, tickInterval, shootingTimes [,canShootH]). Its update checks squared target distance **<4225 (65 blocks)** and line-of-sight, increments attackTimer; Rage potion can increase timer twice per tick. It plays warning sound near cooldown-10 and shoots on a timer when the remaining conditions permit. Values below are **constructor constants, not live measured intervals**.

| Registry ID | Implementing Mob class | cooldown | interval ticks | max shots per volley |
| --- | --- | ---: | ---: | ---: |
| pri_yelloweye | EntityEmana | 80 | 20 | 1 |
| ada_yelloweye | EntityEmanaAdapted | 60 | 20 | 2 |
| overseer | EntityAlafha | 20 | 10 | 4 |
| sentry | EntityUnvo | 20 | 1 | 3 |
| wraith | EntityElvia | 20 | 10 | 4 |
| bogle | EntityLencia | 60 | 30 | 3 |
| haunter | EntityPheon | 60 | 10 | 3 |
| anc_dreadnaut | EntityOronco | 60 | 20 | 3 |
| monarch | EntityOrch | 40 | 15 | 4 |

Proof locators: each original class func_184651_r and entity/ai/EntityAIAttackProjectile.class — constructors, func_75246_d, shoot.

**Do NOT infer multi-angle danmaku** from shootingTimes. The common shoot method aims at the target displacement; multiway fans/rings are not produced by these parameters themselves. Species getProj and projectile motion must be inspected independently. A 4-shot *temporal volley* is not a 4-way radial formation.

### 1.2 Mapped offensive projectiles

| Mob and bytecode | Projectile behavior | Evidence and boundaries |
| --- | --- | --- |
| Primitive/Adapted Yelloweye — EntityEmana and EntityEmanaAdapted | Spineball damage/poison and conditional grenade rounds | getProj and playProjSound: special grenade constructor (3,60) / (4,100) respectively when the species counter reaches its trigger. Counter increments at the prefire/sound path; avoid calling this exactly every 3rd/4th physical shot if interrupts occur. |
| Sentry — EntityUnvo | Spineball with configured poison and armor-durability damage | getProj sets duration/amplifier and gear multiplier. EntityProjectileSpineball.damageArmor damages each damageable armor equipment item proportional to max durability times configurable factor. |
| Overseer — EntityAlafha | ProjectileAlafhaBall and lingering toxic cloud | EntityProjectileAlafhaBall.spawnLingeringCloud creates EntityToxicCloud: radius arguments 1.5/1.1, wait 30 ticks, duration 60 ticks, effect DLER_E 360 ticks (potion duration distinct from cloud lifetime). |
| Bogle — EntityLencia | Explosion on ball impact | EntityProjectileLenciaBall.func_70227_a calls SRP ParasiteEventEntity.createExplosion with strength argument 10.0; terrain griefing gated by Forge mobGriefing event and config lenciaGriefing. True explosion damage/shape demands separate SRPExplosion review. |
| Haunter — EntityPheon | Homing shots, ranged, AOE melee, evasive dash | func_184651_r separately registers EntityAIAttackProjectile 60/10/3, EntityAIAttackRangedStatus (20,40,40.0), AOE melee, and EntityAIEvadeDash (40,2,4,5.0,100). getProj constructs EntityProjectileHomming. |
| Ancient Dreadnaut — EntityOronco | Ancientball damage, Wither and COTH lingering cloud | EntityProjectileAncientball.func_70227_a creates AreaEffectCloud with Wither effect and COTH_E. Also registers EntityAIAncientSummon tied to config oroncoPodCooldown and oroncoPodNumber. |
| Monarch — EntityOrch | Webball, environmental area denial | EntityProjectileWebball.setWebsAround attempts 1–3 parasite web placements at adjacent randomized positions in air when web mode permits; otherwise target hit applies slowness and ranged damage. |
| Wraith — EntityElvia | Direct ElviaBall and timer/counter-dependent Nade | getProj has an alternate EntityProjectileNade branch with integer constructor parameters 4,60. Needs gameplay capture for precise special frequency. |
| Ancient Overlord — EntityTerla | Homing ranged attack plus melee area hits | func_82196_d creates EntityProjectileHomming with target. AI registers ranged goal speed 1, attack min/max intervals 60/80 and 40-block max range, plus melee switch threshold 10 and AOE melee. |

### 1.3 Special projectile behavior

- **Homing:** entity/projectile/EntityProjectileHomming.class — func_70071_h_, bulletHit, and nested AIMoveControl. Repeatedly updates move target to current target location; collision scan around projectile; UUID owner/target stored in NBT; lifetime guard after ~200 ticks. This is continuously corrected steering, not ballistic launch direction. Wall penetration / exact turns NOT verified by gameplay.
- **Grenade transition:** EntityProjectileNade.func_70227_a spawns EntityNade on impact, using fuse + duration constructor and the shooting Mob reference. EntityNade.selfExplode iterates a local AABB of living entities and applies damage during its active state; do not conflate with direct TNT explosion.
- **Stationary bomb:** EntityOmboo$AIBomb creates EntityBomb with 80-tick fuse and strength 1; EntityJinjo$AIBomb creates EntityBomb with 80-tick fuse and conditional strength 4 or 8, configuration dependent.
- **Pod strike:** EntityAIAncientSummon.func_75246_d performs a telegraph, then calls ParasiteEventEntity.SummonM with AncientPod token on 20-tick intervals once counter >=40, under target/visibility/range limits (squared distance <2500). EntityDropPod.selfExplode calls SRP explosion with strength 4, Forge griefing gate and ratholGriefing config, configurable effects, lingering cloud and bounded attempts to spawn configured parasite mobs. This is area attack plus deployment.
- **Cap-dependent attack substitution:** EntityIki$AIBomb checks worldGnatCap; can produce an EntityAta while under cap and switches to a projectile EntityBomb branch when cap reached and additional target conditions pass. A mob cap can change *attack strategy*, not just prevent spawning.
- **Web interaction:** EntityProjectileWebball.func_70227_a and setWebsAround combine ranged crowd control and block placement.
- **Ranged kill → evolution:** EntityProjectileSpineball impact path credits the shooter’s kill counter and can invoke ParasiteEventEntity.spawnNext into Adapted Yelloweye after conditions; not all progression originates from melee kills.

## 2. AI decision mechanics

**Evasion:** EntityAIEvade.func_75246_d checks distance thresholds (squared distance below 225, and outside blockDistance), line-of-sight, slow effect, and internal cooldown; chooses random ±1 lateral strafing and blends vector motion with existing velocity. EntityAIEvadeDash is separate, with impulse-style velocity changes and navigation interruption.

**Flight:** EntityAIFlightAttack handles target validity, permission/whitelist and perception. EntityAIFlightLimits adjusts Y movement based on environmental constraints. Species AIMoveControl implementations control motion. These are distinct modules and must not be collapsed into a single generic “flight behavior”.

**Tactical mode switching:** EntityAIAttackMeleeRangeSwitch toggles setWorkTask based on target distance and visibility; EntityAIAttackMeleeRanged implements an attack-band test and periodically spawns EntityDamage toward enemy location (20-tick test), not a conventional ballistic projectile.

**AOE melee:** EntityAIAttackMeleeStatusAOE.checkAndPerformAttack dispatches attackEntityAsMobAOE on eligible target, using attackTick=20. Weapon/target reach settings are passed by caller.

**Block destruction:** Original SRPEventHandlerBus.setNewParasiteTask parses config parasiteGriefing for matching parasite IDs, calls EntityParasiteBase.setSkillBreakBlocksValues and registers EntityAISkill for destruction. Original EntityParasiteBase.skillBreakBlocks exists and is now directly available in this stable JAR: previous addon Mixin target is corroborated at the class-symbol level, but full rule-level bytecode mapping is still pending.

## 3. Learning → evolution → colony memory (original binary proven)

Individual, replacement, and colony/world progression must remain **separate state scopes**.

1. **Individual:** EntityPMalleable constructor creates resistanceS (damage identity names) / resistanceI (points). Base defaults before species overrides: pointReduction=0.1, pointCap=10, DamageTypeCap=5, chanceLearn=0.5, adaptationCap=1.0. func_70097_a classifies attack by player held item registry name / Mob registry / DamageSource ID, then consults hasResistance and adjusts incoming damage with a capped factor. addResistance updates points or inserts a type with learning probability, fire and cooldown restrictions. The memory is serialized as sprresistances and sprresistancei NBT lists by func_70014_b.
2. **Species replacement:** ParasiteEventEntity.spawnNext, when both old and new are EntityPMalleable, calls copyResistancesFrom. Implementation assigns list references rather than visibly deep copying — portability/aliasing caution.
3. **Colony/world:** EntityPMalleable.func_70645_a invokes ParasiteEventEntity.checkColony on server-side death. This examines activated colonies, their range, LINK_E and whether Mob was colony-spawned; conditionally takes getMostCommonDamage and records into SRPWorldData.addGlobalResistance. SRPWorldData uses strings + frequency counters, exposes getMostCommonDamageS/I, resetGlobalAdaptation and stores as saved world data.
4. **Next generation:** SRPEventHandlerBus.setNewParasiteTask reads the dominant shared damage type/count and calls the newborn EntityPMalleable.addResistance in a loop, increases damage cap, sets colonySpawned. HOWEVER, addResistance itself checks learning cooldown and other constraints: actual inherited points need runtime/parameter-specific tests before claiming 1:1 inheritance.
5. **Separate colony stat bonuses:** EntityParasiteBase.setColonyBonus(int) applies configured health, armor, attack, knockback and damage cap modifiers. setNodeBonus(int) applies configured potion effects. These stat buffs are different from cross-generation acquired damage resistance.
6. **Separate dimension progression:** SRPSaveData holds evolution phase, points, cooldowns and species unlocks. This is distinct from the above attack-specific “learning”.

**Conclusion:** original stable SRP 1.9.21 has a rules-based individual → world/colony memory → newborn adaptation chain. This is strong evidence for an *ecological selection simulation foundation*, but it is NOT neural-network learning, automatic species design, or full natural-selection algorithm.

## 4. Original staged block reversion vs exact world restoration

EntityPStationaryArchitect.freeDead checks an infested block under its dead/removed position and conditional phase/stage/reversion chance, writes InfestedStain state STAGE=5, and schedules a block update after 40 ticks. This is an original **staged conversion** path, not evidence of preserving arbitrary prior BlockState, player buildings or BlockEntity NBT. For KNEEKURA propose independent WorldMutationJournal with versioned dimension/BlockPos, original state, optional block entity data, temporary expected state, owner, expiry and conflict-safe restoration on loaded chunks.

## 5. Reusable technical candidates (DESIGN_PROPOSAL, not an original code license)

- **Volley scheduler**: target perception → windup/telegraph → sequence counter → distinct projectile factories; apply state effects to timers, not merely motion.
- **Trajectories and danmaku**: keep direct aiming, homing, impact grenade, lingering cloud, explosion, web, troop-drop in different attack modules. Design radial/fan/spiral projectile patterns independently when desired; this JAR analysis does NOT show common EntityAIAttackProjectile generating radial fans by itself.
- **Evasive aerial AI**: target state, distance band, random strafe, dash, flight altitude constraints, species move controller separated. Avoid one forced AI template.
- **Damage-type memory**: per-entity capped table, mutation/evolution inheritance, colony-level frequency aggregator and explicit reset/counterplay; support controlled ecological experiments.
- **Territory director**: locally scoped invasion to be independently engineered for 1.20.1; note chunk-phase option identified previously is a feature of SRPMixins addon, not a native 1.9.21 default.
- **Safe world mutation**: exact restoration journal rather than replacing infested blocks with fixed dirt/gravel. Protect player edits, chunk unloading and memory pressure.
- **Resource policy**: loaded-chunk-only updates, per-region Mob/projectile limits, cloud occupancy cap, scheduled block mutation budgets, bounded tests.

## 6. Next evidence gates, no false completion

- Full 868-class tree needs deeper mapping by facets (rendering, model animation, particle FX, entity sound triggers, boss transformations, network synchronisation, original config defaults, all species). Focus currently **306 indexed class subset plus supporting reads**.
- For attack trajectories: collect authorized 1.12.2 test traces to prove target aim offsets, collision/raytrace, homing turn rate, reload cadence and actual projectile shapes. For efficiency: measure actual TPS and packet budgets. **NOT_RUN** currently.
- For colony learning: inspect exactly when resetGlobalAdaptation is called and test newly-spawned inheritance after cooldown, colony destruction and save/reload. Distinguish global/dimension/individual scoping.
- For terrain: prove precise block update and repair with a world snapshot test, **not** guess original-world restoration.
- For history: still need exact alpha-vs-stable repair diffs and formatted FAILURE-REPAIR-HISTORY records; issue reports are not a PASS.
- 1.20.1 Forge ANCHOR: no direct port or runtime compatibility; version/language/mappings differences must be explicitly documented before implementation.
- Preserve private JAR bytes, decompilation output and third-party resources locally. Do not treat these bounded findings as whole-target COMPLETE, canonical VALIDATED or measured performance.

**Facet status:** entity registry INVENTORIED; selected ranged/evasion/learning method behaviors MAPPED with DIRECT_BINARY evidence, some evidence-scoped claims; rendering and whole-target analysis NOT_ANALYZED / PARTIAL; gameplay, source equivalence, 1.20.1 and performance NOT_RUN.


## 7. Further verified environmental / group AI (original 1.9.21 bytecode)

**Block-light sabotage (DIRECT_BINARY).** Class \`com/dhanantry/scapeandrunparasites/entity/ai/EntityAIBlockLight.class\`:
- \`findSource()\` starts with \`EnumSkyBlock.BLOCK\` light level around parent and checks \`lightTrigger\`. Its candidate selection and light-level constraints are distinct from ordinary player combat.
- \`func_75246_d()\` runs path navigation toward a \`BlockPos target\`, tracks \`progressB/neededTime\`, emits block-breaking world event \`World.func_175715_c\` as progress changes, and eventually calls \`World.func_175655_b(target,true)\` to destroy the block. When position/pathfinding stops improving, it can call \`EntityParasiteBase.skillBreakBlocks()\` after a detected idle threshold **120**, abandoning the target after threshold **240** and placing that coordinate into an exclusion list. Exact player-visible frequency depends on tick-scheduler/goal registration and config.
- **Design opportunity**: goal-based sabotage of player illumination + anti-stuck escalation, separately from generic griefing. When independently implementing, reversible break journal and owner-scoped protection should intercept the final world mutation.

**Dynamic recruitment and followership (DIRECT_BINARY).** Class \`com/dhanantry/scapeandrunparasites/entity/ai/EntityAIGetFollowers.class\`:
- Constructor accepts \`parent, version, searchRange\`. \`func_75250_a()\` only starts every **20 ticks** if the parent is not itself following another parasite and has no current attack target.
- \`func_75246_d()\` queries \`EntityParasiteBase\` in an AABB grown by \`(searchRange,2,searchRange)\`, iterates nearby candidates and handles **four version-dependent branches** with conditions on visibility/aliveness/type and existing leader; when eligible calls \`candidate.setParasiteToFollow(parent)\`. Does not indiscriminately recruit all parasitic Mobs.
- **Design opportunity**: hierarchical group leaders/formation recruitment where goal is suppressed while attacking; use a capped group size / bounded scan period to manage load.

**Timed spread AI (DIRECT_BINARY).** Class \`com/dhanantry/scapeandrunparasites/entity/ai/EntityAIBlockInfest.class\`:
- \`func_75250_a()\` always true (when scheduled by Mob); in \`func_75246_d()\` increments internal \`ticks\` and acts after **ticks > 200** (nominally 201 uninterrupted goal updates), resets counter, checks parent current block against \`IMetaName\`; if not already infected, invokes \`ParasiteEventWorld.canInfestBlock(world,parentBlockPos,new Random(),stage,true)\`.
- This establishes **original** source of timed stage-aware infestation, *distinct from SRPMixins addon overwrite*. Actual infected block material/extent/probability sits downstream in \`canInfestBlock\` and must be independently read. \`new Random()\` per activation is worth profiling; no performance measurement was made.

**Evidence boundary:** methods recovered from the uploaded JAR's distributed bytecode by JDK \`javap -p -c\`. \`func_175655_b\` is the 1.12.2 SRG world break method; this is not a demonstration of 1.20.1 Minecraft mappings/Forge compatibility, and not a runtime result. The complete original \`findSource\` / four follower branches and downstream block state conversion are further detailed mapping tasks, not falsely marked done.

## 8. Technical harvest prioritization (incremental)

| Family | Evidence | Candidate for KNEEKURA invasion MOD | Unresolved |
| --- | --- | --- | --- |
| Timed terrain infestation | DIRECT_BINARY \`EntityAIBlockInfest\` | staged territory growth with per-area tick budget | block state conversion, exact config chance |
| Light-source sabotage | DIRECT_BINARY \`EntityAIBlockLight\` | enemy tactic that weakens player defenses rather than doing only HP damage | config trigger/filter, world restore after light-breaking |
| Group leader recruitment | DIRECT_BINARY \`EntityAIGetFollowers\` | hierarchy/follower policy to coordinate swarms | all four type-code branches, formation/navigation |
| Pod bombardment | DIRECT_BINARY \`EntityAIAncientSummon\` + \`EntityDropPod\` | multi-stage attack: warning → projectile/landing → reinforcements → status area | live spawn/location/timings/particles |
| Global adaptation memory | DIRECT_BINARY \`EntityPMalleable\`, \`SRPWorldData\`, event handlers | adaptive ecology: individual experience → colony dominant threat → descendants | reset caller and probabilistic inheritance validation |

**Critical distinction:** Original has a configurable rules-based adaptation and evolution/phase system; a true ecosystem additionally requires a resource model, carrying capacity, spatial territory, selection pressures, and reproducible behavior. This is a new independent design direction, **not** a recovered original SRP mechanic.
