# Bedrock Wither Reconstruction — Source Ledger

Retrieved/reviewed: 2026-10-02

This ledger separates official exposed behavior, maintained secondary observation and community reports. It is a reconnaissance source set, not proof that Bedrock native code has been recovered.

## Official / primary-facing documentation

### Microsoft — Vanilla Wither entity definition

URL:
https://learn.microsoft.com/en-us/minecraft/creator/reference/source/vanillabehaviorpack_snippets/entities/wither?view=minecraft-bedrock-stable

Observed exposed fields include:
- health/max 600
- movement 0.25
- can_fly
- `minecraft:behavior.wither_target_highest_damage`
- `minecraft:behavior.wither_random_attack_pos_goal`
- nearest attackable target max distance 70

Important limitation: this public JSON does not expose the complete player-visible boss behavior.

### Microsoft — Unique Entity Behaviors

URL:
https://learn.microsoft.com/en-us/minecraft/creator/documents/uniqueentitybehaviors?view=minecraft-bedrock-stable

Microsoft documents that some entities have behavior built into Minecraft code that is not apparent from JSON. The Wither is one of the documented unique-behavior examples, including special abilities such as flight, explosive skulls and Wither Skeleton summoning.

### Microsoft — special Wither goals

URLs:
https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_wither_target_highest_damage
https://learn.microsoft.com/en-us/minecraft/creator/reference/content/entityreference/examples/entitygoals/minecraftbehavior_wither_random_attack_pos_goal

Use: authoritative evidence that these dedicated Bedrock goals exist and that highest-damage targeting is intentional. Parameters not documented there remain unknown.

### Mojang bedrock-samples — current vanilla Wither definitions

Repository:
https://github.com/Mojang/bedrock-samples

Pinned revision reviewed:
`46ba6ea985fb5a92d79a9419198f10dda14c199d`

Server behavior:
`behavior_pack/entities/wither.json`

Directly exposed current contract includes:
- `minecraft:behavior.wither_target_highest_damage` priority 1;
- `minecraft:behavior.hurt_by_target` priority 2;
- `minecraft:behavior.nearest_attackable_target` priority 3, `must_see=true`, max distance 70;
- the non-player target filter excludes the `undead` and `inanimate` families;
- `minecraft:behavior.wither_random_attack_pos_goal` priority 3;
- boss HUD range 55 and sky darkening;
- health 600, movement 0.25, `can_fly`;
- collision box width 1 / height 3;
- `movement.basic.max_turn=180`;
- damage from the `undead` family is rejected by `minecraft:damage_sensor`;
- fire and freezing immunity;
- water breathing;
- public navigation is still declared as `navigation.walk`, reinforcing that exposed JSON is not the complete hidden flight implementation.

Projectile definitions:
- `behavior_pack/entities/wither_skull.json`
- `behavior_pack/entities/wither_skull_dangerous.json`

Current shared projectile contract:
- collision box 0.15 x 0.15;
- gravity 0;
- inertia 1.0 and liquid inertia 1.0;
- explosion power 1;
- Wither effect duration: Easy 0, Normal 200 ticks, Hard 800 ticks;
- uncertainty base 7.5, uncertainty multiplier 1.

Current normal skull:
- launch power 1.2.

Current dangerous skull:
- launch power 0.6;
- `is_dangerous=true`;
- `reflect_on_hurt=true`;
- explosion `max_resistance=4.0`.

These values are primary implementation inputs. Where Java APIs do not have identical semantics (for example the exact native reflection vector or Bedrock projectile uncertainty algorithm), the adaptation is labeled separately and remains a runtime-comparison target.

Client/render references at the same pinned revision:
- `resource_pack/entity/wither.entity.json`
- `resource_pack/animations/wither_boss.animation.json`

The client definition exposes three independently queried head rotations, invulnerability-driven skin/armor state, spawn swelling/scaling and body animation. These are visual-authority inputs, not server AI authority.



### Current BDS structural surface — LeviLamina generated headers

Current inspected main:
`LiteLDev/LeviLamina@1bab1522cdfd697d241e77fe60f19b9db2a20a5a`

Target dependency recorded by that revision:
- BDS package: `1.26.51`
- supported server: `26.51.1`

Relevant generated Bedrock header blobs:
- `WitherBoss.h`: `03cd288d06c8c053678a51891c014d0d910e94e5`
- `WitherTargetHighestDamage.h`: `1857b2a20df2b86f07e4d661a09e67ad709a5057`
- `WitherRandomAttackPosGoal.h`: `258cdeb206ac193336e8d90ba598a6695bd42ad1`
- `WitherBossPreAIStepResult.h`: `6d02f203c934b22240e1cf63598e3de8cce78524`

These blobs are unchanged from immediately previous main commit `32fcaa02...`.

Use:
- current hidden-implementation **structure evidence**: fields, native function boundaries, enum names, return types;
- not function-body or exact-timing evidence.

Detailed map:
[BDS-STRUCTURE-2026-10-02.md](BDS-STRUCTURE-2026-10-02.md)

Key findings now shaping product code:
- native attack destruction categories: Charge / HurtExplosion / Projectile;
- explicit native phase/shield/charge/projectile/skeleton/movement counters;
- three head rotation/update slots;
- pre-AI execution gate;
- highest-damage target helper returns `Player*`;
- special random-position goal derives from RandomStrollGoal and tracks pathing.

### Historical Bedrock reverse engineering

Version-unresolved decompiled/generator output is kept separate:
[HISTORICAL-BEDROCK-REVERSE-NOTES.md](HISTORICAL-BEDROCK-REVERSE-NOTES.md)

Use only to corroborate relationships that still have current structural counterparts or to design runtime measurements. Historical constants never override current Mojang definitions or current BDS structure.


## Maintained secondary / gameplay observation

### Bedrock Wiki — Wither boss behavior

URL:
https://bedrockwiki.com/books/mobs/page/wither-boss/revisions/692/changes

Useful reported observations:
- Easy/Normal/Hard health 300/450/600
- two-stage combat
- phase 1 burst described as 3 normal skulls plus 1 dangerous skull
- health-dependent firing speed
- phase-1 damage reaction with local block destruction and dangerous skull
- half-health transition
- Wither Skeleton summon
- phase-2 projectile immunity
- charge/dash
- reported 20-tick charge
- reported 6x8x6 destruction cuboid during charge

Status: high-value measurement hypothesis, but community-maintained and WIP. Numeric values require our own runtime verification before strict acceptance.

### Minecraft Wiki / current mirrors

Used to cross-check:
- difficulty-dependent Bedrock health
- half-health second phase
- explosion/skeleton behavior
- dash/terrain damage
- lack of ordinary passive regeneration in current Bedrock behavior
- death sequence/explosion

Because mirrors and version snapshots can disagree, exact values are retained as candidates unless corroborated by runtime evidence.

## Community reports

Reddit/forum/video reports are used only to discover edge cases, e.g.:
- downward tunneling during phase-2 dash
- severe block-item generation/performance symptoms
- platform/version-specific fight behavior

Status: CANDIDATE only. No Reddit report directly sets an implementation constant.

## Known disagreements to retain

1. **Wither Skeleton count**: current detailed sources commonly report 3, while some older/stale pages report other counts. Runtime measurement wins.
2. **Exact firing thresholds/cadence**: some mirrors report health thresholds; detailed Bedrock Wiki describes changing delays. We must measure instead of merging them.
3. **Phase-2 armor after healing**: some sources describe persistence quirks. Treat as a possible Bedrock bug/version behavior, not a base requirement.
4. **Block destruction exceptions**: Java/Forge and Bedrock block semantics differ. Exact Bedrock breakability needs scenario tests, not a direct Java tag assumption.

## Java ANCHOR references

### Java 1.20.1 WitherBoss mappings

URL:
https://mappings.dev/1.20.1/net/minecraft/world/entity/boss/wither/WitherBoss.html

Important implementation observation:
- Java `WitherBoss` extends `Monster`
- Java-specific head cooldown arrays, block-breaking timer and boss event are private
- `aiStep` and `customServerAiStep` own significant behavior
- ranged helper methods include private internals

Conclusion: use Java Wither as comparison/reference, not as the primary behavioral superclass.

### Forge 1.20.1 Wither model/renderer API

URLs:
https://mcstreetguy.github.io/ForgeJavaDocs/1.20.1-latest/net/minecraft/client/model/WitherBossModel.html
https://mappings.dev/1.20.1/net/minecraft/client/renderer/entity/WitherBossRenderer.html

The vanilla renderer/model generics are bound to `WitherBoss`; an independent `Monster` implementation therefore gets its own renderer/model adapter.

## Evidence next actions

Direct Bedrock runtime observation should measure:
- spawn sequence duration and invulnerability
- exact phase-1 movement/reposition rule
- exact 3+1 firing timing and health-dependent changes
- dangerous-skull spontaneous interval
- phase-1 hurt break box, timing and item-drop behavior
- exact 50% transition action ordering
- skeleton count by difficulty
- dash prep/duration/velocity/termination
- destruction box origin, dimensions, per-tick timing and exception blocks
- projectile immunity boundary
- healing/armor persistence quirks
- death sequence/explosion timing

Each scenario should record Bedrock version, difficulty, seed/world setup, target position, health, tick/video timing method and result confidence.


## Comparative implementation prior art

### BEStyleWither

Repository:
https://github.com/MORIMORI0317/BEStyleWither

Pinned review:
- COMPARATIVE-ANCHOR-LIKE: branch `1.20`, commit `ab98547f3e8e0dac83a814d5133a113d4bfd9e40`, declared support 1.20/1.20.1, Forge 46.0.13.
- FRONTIER: `main`, commit `e658d45ea3d2b6b6b16d6a02ee6b736ce9c411d2`, Minecraft 1.21.1.

Detailed engineering review:
[PRIOR-ART-BESTYLEWITHER.md](PRIOR-ART-BESTYLEWITHER.md)

Use: implementation-technique and failure-history reference only. Its constants and behavior are not accepted as Bedrock truth.


## Evidence priority for product implementation

For the Bedrock Wither deliverable, implementation decisions use this order:

1. pinned Mojang/Microsoft Bedrock definitions and documentation;
2. direct Bedrock runtime observation retained by KNEEKURA;
3. maintained Bedrock technical/gameplay documentation;
4. community reports as discovery/edge-case leads;
5. BEStyleWither and other Java implementations as engineering hints only.

A lower layer must not override a contradictory higher layer merely because its Java code is easier to reuse.
