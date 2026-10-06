# Kimetsu no Yaiba (Demon Slayer) — ver3 / Minecraft 1.20.1

## Scope

Whole-target technical analysis of the user-supplied:

`KimetsunoYaiba-ver3-forge-1.20.1.jar`

Primary interest:

- NPC combat AI and technique selection
- Breathing / Blood Demon Art execution architecture
- projectile and helper-entity attacks
- damage / guard / knockback kernel
- player input / progression / animation synchronization
- rendering / animation
- worldgen / dimensions / structures
- persistence / network state
- performance and compatibility boundaries
- 1.20.1 release repair history

No game implementation code is changed in KNEEKURA.

## ANCHOR

Uploaded artifact:

- file: `KimetsunoYaiba-ver3-forge-1.20.1.jar`
- SHA-256: `b4af6e8a9d5926c5fea212a5e237e61f1e8095a5be23eca9b8294258a3b466b6`
- mod id: `kimetsunoyaiba`
- internal version: `3`
- Minecraft: `1.20.1`
- Forge loader contract: `javafml [47,)`
- bytecode: Java 17 / class major 61
- generator: MCreator
- exact public release identity: filename/file metadata matches CurseForge file **7151280**
- public release date: 2025-10-26
- released-public-file SHA equality: **NOT_ESTABLISHED**
- official source repository: **NOT_FOUND / NOT_PINNED**

Because no official source revision is available, this uploaded JAR is the implementation authority.

## Public distribution / license boundary

CurseForge project:

- project: `471263`
- author: `Orca_san_`
- project license: **All Rights Reserved**
- public page explicitly prohibits reuse of internal textures/models

The JAR's `mods.toml` says `license="Not specified"`, but KNEEKURA follows the public project
license as the distribution/copy boundary.

This research stores architecture, bytecode locators and independently reconstructed concepts.
It does not copy upstream assets or decompiled source.

## Source tree / binary inventory

JAR:

- ZIP entries: **5,863**
- class files: **3,713**
- non-class resources: **2,068**
- top-level classes: **1,524**

Large package surfaces:

- `entity/`: **1,867 class files**
- `procedures/`: **860 class files** / ~720 top-level Procedure classes
- `item/`: **480**
- `client/`: **322**
- `block/`: **111**
- `init/`: **24**
- `potion/`: **24**
- `network/`: **14**
- `world/`: **6**

Gameplay entity implementations:

- top-level entity classes: **164**
- Monster: **94**
- PathfinderMob: **45**
- AbstractArrow: **17**
- TamableAnimal: **8**
- registered entity types: **165**

Other registries:

- items: **388**
- blocks: **59**
- effects: **19**
- particles: **26**
- sounds: **26**
- block entities: **13**

## Architectural summary

The mod is best understood as a **hybrid vanilla-AI + imperative Procedure combat runtime**.

```text
Entity
  |
  +-- vanilla GoalSelector / TargetSelector
  |      navigation / melee / target acquisition
  |
  +-- every-tick character AI Procedure
           |
           +-- numeric mode / counters in persistent NBT
           |
           +-- concrete Breathing / Blood Art Procedure
                    |
                    +-- animation
                    +-- movement
                    +-- particles / sound
                    +-- helper entity / projectile
                    +-- shared DoDamage2 attack kernel
```

The important finding is not that this is "MCreator code".

It is that the generated code converges on several reusable architecture patterns:

1. **numeric technique opcode namespaces**
2. **shared player/NPC concrete form implementations**
3. **one reusable attack-volume kernel**
4. **detached helper actors carrying owner/provenance**
5. **mobile projectile-as-AoE-emitter attacks**
6. **central animation opcode mapping + network synchronization**
7. **usage-count mastery progression**
8. **data + runtime-injected world generation**

## Research status

**TARGETED_WHOLE_TARGET_ARCHITECTURE_MAPPED**

Static JAR evidence is strong for:

- inventory
- AI/technique architecture
- attack kernel
- Stone Breathing
- representative Blood Demon Art
- projectile/helper entities
- animation/network/state
- worldgen/dimensions
- current compatibility/performance risks

Not claimed:

- runtime TPS/FPS benchmark
- every one of 700+ Procedure implementations manually described
- public-source equivalence
- exact CurseForge JAR SHA equality
- exhaustive old-version binary diff

## Documents

- [WHOLE-TARGET-RESEARCH-2026-10-06.md](WHOLE-TARGET-RESEARCH-2026-10-06.md)
- [COMBAT-TECHNIQUE-OPCODE-MAP.md](COMBAT-TECHNIQUE-OPCODE-MAP.md)
- [BREATHING-MARK-AWAKENING-DEEP-DIVE-2026-10-06.md](BREATHING-MARK-AWAKENING-DEEP-DIVE-2026-10-06.md)
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)
- [SOURCE-INVENTORY-2026-10-06.json](SOURCE-INVENTORY-2026-10-06.json)
