# QB-MOD / “Madoka Magica MOD” — Initial whole-target analysis (2026-10-07)

## Executive finding

The supplied QB-MOD 1.6.4.082 is unusually useful as a legacy research target because the distribution ZIP contains 156 MCP Java sources and 156 compiled classes. Its required Garnet-MOD 1.6.4.082 also contains 37 Java sources and 37 classes. Primary behavior can therefore be recovered from shipped source instead of guessed from guides or decompilation.

Architecture is layered rather than monolithic:

1. Garnet framework: tameable/owner-aware entities, companion modes, targeting/follow AI, generic projectiles, guns/reload/full-auto, servants/summoners and renderer bases.
2. Madomagi common layer: inventory/GUI, form state, Soul Gem corruption, range-banded combat goals, common targeting and form rendering.
3. Character specializations: Madoka/Homura/Sayaka/Mami/Kyouko/Kirika/Yuri override stats, attacks and special-form AI.
4. Witch/boss specializations: Walpurgisnacht, Kriemhild, Homulilly, Charlotte, Oktavia and others.
5. Presentation: per-form models/textures, projectile renderers, scaled bosses and posture-driven rendering.

The reusable output should therefore be cataloged by subsystem, not stored as one “Madoka combat template.”

## 1. Magical-girl state machine

EntityMahoShojo stores synchronized form and Soul Gem state:

- 0 normal
- 1 transformed magical girl
- 2 Rebellion
- 3 Ultimate Form
- separate posture bit for renderer weapon pose
- integer Soul Gem corruption

Primary locator: QB SHA 52b1ba0774e098795dcf1ed9a489c66414ea725235978171f48a10db7287ba4e + MCP/puellamagi/mods/entity/passive/EntityMahoShojo.java:267-296,511-627.

Forms alter more than visuals: attributes, protection, AI, companion mode, fire immunity, healing frequency, inventory access and model/texture can all change.

Important nuance: setSoulGemDamage(int) adds to current corruption rather than assigning it. A modern rewrite should split addCorruption, cleanseCorruption and setCorruptionAbsolute. The persisted legacy key is misspelled SoulJem; migration should handle it explicitly if old-save compatibility is ever desired.

## 2. Companion contract / control

Garnet supplies the owner/mode skeleton. EntityGarnetTameable synchronizes enabled state, mode and owner name and cycles Standby → Satellite (if enabled) → Free → Follow.

Locator: Garnet SHA 5f778c8949dcce95dcd56dacd9242f117bc17f03879bab48cb667ba2a3c82778 + MCP/garnet/mods/entity/passive/EntityGarnetTameable.java:72-107,116-140,176-292.

QB-MOD composes narrative form with tactical mode:
- Standby/Satellite suppress combat transformation paths.
- Rebellion forces Free.
- Ultimate Form forces Follow.

ANCHOR rewrite should use UUID ownership rather than username strings and modern synchronized entity data.

## 3. Soul Gem loop

The corruption system is a complete feedback loop:

1. combat/actions add corruption;
2. red warning particles begin at >=52 and intensify at >=58;
3. Grief Seeds consume durability to cleanse;
4. at >=64 the magical girl changes into a character-specific witch, or disappears on Peaceful.

Locator: EntityMahoShojo.java:165-211,375-391,429-509,611-627.

The conversion searches for enough spawn room and removes surrounding blocks shell-by-shell. Bedrock, Mami barrier and Kyouko shield are exempt. This is a strong example of narrative state transition changing world topology.

For ANCHOR, preserve the concept but move terrain preparation into a bounded block-edit job. Do not run an open-ended synchronous clearance loop.

## 4. Range-banded character combat

The common layer exposes shortRangeAttack, middleRangeAttack and longRangeAttack. Shared goal classes select the appropriate band; characters implement distinct attack vocabularies.

Mapped examples:
- Madoka: Light Arrow patterns + dedicated Ultimate AI.
- Homura: Desert Eagle short, Type 89 full-auto mid, TNT pressure long; dedicated Rebellion/Ultimate AI.
- Sayaka: aggressive melee/cutlass + dedicated Rebellion/Ultimate AI and servant concept.
- Mami: musket combat + Tea Time AI + ribbon/barrier mechanics.
- Kyouko: spear, Rebellion AI, Rosso Fantasma servant/guard concept, shield block.
- Kirika: claw/slow-oriented combat.
- Yuri: gun kit with ambidextrous renderer.

The portable technique is distance band → posture/weapon → projectile or melee pattern → cooldown/action tick, with special forms able to replace the generic goal.

## 5. Walpurgisnacht — highest-value boss system

Walpurgisnacht is a world encounter controller embedded in a boss entity.

### Spawn/event gate

Registry is broad, but real spawn requires:
- canWalpurgisSpawn=true;
- world day modulo 8 equals 0;
- time >12000 and <23200;
- Y at/above the height map;
- normal spawn test succeeds.

On success the global gate flips false and an arrival message is broadcast.

Locators: EntityWalpurgisnacht.java:200-238 and mod_QB.java:756-758.

### Ambience

Every ~100 ticks it forces rain, thunder and overworld time 23200. This is effective theatre but invasive global state mutation. Modern design should use an encounter-scoped/reversible ambience controller.

### Damage throttle / retaliation

Incoming valid damage is capped to 1 and opens a 20-tick super-armor window. Some rejected living-attacker hits cause a small-fireball countershot. Its own Flame Lance/Prickle damage is ignored.

Locator: EntityWalpurgisnacht.java:88-149.

### Phase escalation

Default “Play” combat runs while a target exists. The aggressive Attack task only starts at HP <=30 from max 90.

Locator: EntityMajoAIWalpurgisnachtAttack.java:44-60.

The boss does not merely chase a target; it selects pseudo-random offset points around the target and flies toward them, creating a circling/repositioning feel. Flame Lance and Prickle have independent staggered timers.

### Terrain-to-TNT attack

The low-health task periodically starts below the target, performs a bounded connected-block traversal and replaces qualifying solid blocks with stationary primed TNT at fuse=100. Bedrock, Mami barrier and Kyouko shield are excluded.

Locator: EntityMajoAIWalpurgisnachtAttack.java:177-306.

This is a strong reusable boss technique, but it should be implemented through KNEEKURA's bounded block-edit contract.

### Anti-air pressure and likely bug

A target airborne/out of water for ~100 ticks is marked for forced downward acceleration. Landing causes an explosion; after another ~100 ticks without grounding a larger explosion occurs.

Both Walpurgis combat AIs then apply poison to theHost rather than theTarget. This looks like a target-variable bug candidate.

Locators:
- EntityMajoAIWalpurgisnachtAttack.java:115-145
- EntityMajoAIWalpurgisnachtPlay.java:94-124

### Legacy anti-cheese code: do not port literally

When hit by a creative/flying player, Walpurgisnacht directly clears invulnerability, flying, allowFlying and creative-mode capability flags.

Locator: EntityWalpurgisnacht.java:99-109.

Preserve only the design intent (“encounter cannot be trivially cheesed by flight/debug state”), not this implementation. A modern MOD must not silently rewrite player game mode/capabilities.

### Death staging

On death it broadcasts congratulations, deletes nearby EntityMob instances in a 200-block expanded AABB, emits fireworks and drops a Grief Seed.

Locator: EntityWalpurgisnacht.java:240-284,383-395.

The useful concept is encounter cleanup; modern cleanup should be scoped by encounter membership/tags so unrelated modded mobs are not deleted.

## 6. Other bosses already expose distinct reusable patterns

- Kriemhild Gretchen: 2000-HP giant absorber/healer; huge terminal explosion.
- Homulilly: teleport evasion + TNT combat.
- Homulilly Nutcracker: giant destructive movement + super-armor + servant interaction.
- Oktavia: movement speed zero while spawning Wheel hazards around the target.
- Charlotte: synchronized phase/model state and replacement/revival-like behavior.
- Candeloro: melee plus strong movement slow.

These are MAPPED, not yet declared exhaustively analyzed attack-by-attack.

## 7. Rendering

The client proxy registers separate models/renderers for forms and bosses. RenderMahoShojo switches actual model instances by synchronized form, while EntityMahoShojo switches texture suffixes MS/Reb/UF. Posture drives aimedBow.

Locators:
- client/PuellaMagiClientProxy.java:75-121
- client/renderer/RenderMahoShojo.java:35-80
- entity/passive/EntityMahoShojo.java:52-67

HeightCorrection is a renderer pre-scale gate; it is not AI/navigation height logic.

Old RenderLiving/GL11 code requires rewrite on 1.20.1, but the state→presentation contract is portable.

## 8. GUI / networking / persistence risks

Garnet gun full-auto uses legacy Packet250CustomPayload. ANCHOR should use modern Forge payload/channel APIs with explicit direction and payload validation.

MadomagiGuiHandler stores a mutable shared ContainerMadomagi field, injected before openGui and returned server-side. This is a cross-player/reentrancy risk in a shared handler. Modern menus should resolve entity/server state independently for each open request.

Ownership is persisted by username; ANCHOR should use UUID.

Forms, inventory and corruption are persisted; save migration requires an explicit schema decision.

## 9. Static performance / safety probes

Runtime/LAB probes should focus on:
1. witch-conversion terrain clearing;
2. Walpurgis connected-block → TNT conversion;
3. Walpurgis collision block destruction;
4. Kriemhild absorb scans/large scale;
5. 200-block boss-death entity scan;
6. Rebellion/Ultimate projectile bursts;
7. large scaled boss rendering.

No performance PASS is claimed from static source.

## 10. Current facet status

| Facet | Status |
| --- | --- |
| legacy snapshot/hashes | EVIDENCE_BACKED |
| full source-tree acquisition | EVIDENCE_BACKED |
| source↔compiled-class correspondence | MAPPED — exhaustive path/SourceFile-name match + sampled javap; full semantic equivalence not claimed |
| bootstrap/registries/config | EVIDENCE_BACKED |
| ownership/modes/persistence | EVIDENCE_BACKED |
| magical-girl form/corruption machine | EVIDENCE_BACKED |
| character attack catalog | MAPPED |
| boss/witch catalog | MAPPED |
| Walpurgis encounter | EVIDENCE_BACKED |
| rendering/models/textures | MAPPED |
| GUI/networking | MAPPED |
| recipes/items/blocks | INVENTORIED |
| custom dimensions/structures | NOT_APPLICABLE in initial tree pass |
| mixins/coremods/transformers | NOT_APPLICABLE in initial tree pass |
| performance | NOT_ANALYZED |
| failure/repair history | NOT_ANALYZED / historical VCS unavailable |
| 1.20.1 ANCHOR reconstruction | NOT_ANALYZED |

## 11. Highest-value TECH-HUB techniques

Keep these independent instead of collapsing them into one template:

- owner/tameable NPC mode machine;
- narrative combat-form machine;
- corruption/resource meter with staged warning and terminal transformation;
- range-banded attack dispatcher;
- form-specific replacement AI goals;
- servant/summoner framework;
- generic projectile ownership/damage/explosion pipeline;
- gun reload/full-auto synchronization;
- boss super-armor/damage throttle + counterattack;
- offset-point flying boss movement;
- multi-timer projectile pressure;
- anti-air pressure;
- bounded terrain-to-hazard conversion attack;
- encounter ambience controller (rewrite);
- encounter-scoped death cleanup (rewrite);
- synchronized model/texture form switching;
- budgeted world-topology preparation for giant-form transformation.

This decomposition avoids making future KNEEKURA entities into reskins of one imported MOD architecture.