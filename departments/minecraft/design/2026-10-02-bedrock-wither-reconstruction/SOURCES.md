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

### Mojang bedrock-samples — client Wither entity

URL:
https://github.com/Mojang/bedrock-samples/blob/main/resource_pack/entity/wither.entity.json

Use: client/render state reconnaissance only. It is not server AI authority.

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
