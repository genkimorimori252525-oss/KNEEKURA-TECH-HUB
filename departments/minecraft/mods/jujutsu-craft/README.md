# Jujutsu Craft (Sorcery Fight) — ver50.1 / Minecraft 1.20.1 Forge

Status: **IN_PROGRESS — whole-target static analysis evidence-backed; runtime NOT_RUN**

## ANCHOR

- Distribution: `JujutsuCraft-ver50.1-forge-1.20.1.jar`
- CurseForge File ID: **7985964**
- Public release: **2026-04-26**
- Minecraft: **1.20.1**
- Loader: **Forge / javafml 47+**
- Java classfile: **61 / Java 17**
- SHA-256: `094247a33bf9c4a741a17fee9ecd1eb5879c97f107ae784af81cfc0f1eee26c9`
- SHA-1: `6c5dd6c74c45351b1029c204cc1d147fc459de4d`
- Size: 16,398,540 bytes
- ZIP entries: 6,377
- Classes: 3,493
- Embedded mod ID: `jujutsucraft`
- Embedded version: **50**
- Distribution version: **50.1**
- License: **All Rights Reserved**
- Public source: **NOT FOUND**
- Runtime: **NOT_RUN**

The external distribution is ver50.1 while `mods.toml` still reports version 50. Artifact hash + File ID are therefore the canonical ANCHOR identity.

## Main findings

- Combat is heavily **MCreator Procedure-driven**: 1,080 root procedure classes form the real behavior layer.
- Gojo's Limitless has both **spatial interception** and **damage-event cancellation**, with counters centralized in `AntiInfinityProcedure`.
- Blue / Red / Hollow Purple are implemented as **persistent moving field actors**, not ordinary vanilla projectile classes.
- Domain Expansion is a shared **domain state machine** with common lifecycle/battle procedures and character-specific active behavior.
- Mahoraga adaptation stores **per-damage-source progress in equipment NBT**, with separate Limitless-specific adaptation state.
- Sukuna's Malevolent Shrine is an ongoing server-side **area attack + block-destruction field**.
- Black Flash is a stochastic escalation embedded inside the generic `RangeAttackProcedure`, not just a standalone key skill.
- Player combat state is persisted in a synchronized capability containing curse power, selected techniques, Six Eyes/Sukuna flags, charge, experience/fame and more.
- Player animation sync and GeckoLib entity animation use separate transport/execution paths.
- The release line shows repeated repair pressure around multiplayer animation, Six Eyes, Mahoraga adaptation, performance/particles and Limitless.

## Whole-target scale

- 310 registered entity types
- 415 registered items
- 27 blocks
- 46 mob effects
- 43 particle types
- 28 sounds
- 310 client renderers
- 127 client model classes
- 151 animation JSONs
- 152 Geo model JSONs
- 430 entity textures
- 160 biome modifiers
- 200 advancements
- 16 structures / 16 structure sets / 31 template pools

## Documents

- [JAR provenance](JAR-PROVENANCE.md)
- [Source / artifact inventory](SOURCE-INVENTORY.json)
- [Gameplay feature map](GAMEPLAY-FEATURE-MAP.md)
- [Code map](CODE-MAP.md)
- [Technical knowledge](TECHNICAL-KNOWLEDGE.md)
- [Limitless and Gojo](LIMITLESS-AND-GOJO.md)
- [Domain system](DOMAIN-SYSTEM.md)
- [Mahoraga adaptation](MAHORAGA-ADAPTATION.md)
- [Sukuna combat](SUKUNA-COMBAT.md)
- [Animation / networking](ANIMATION-NETWORK.md)
- [Version portability](VERSION-PORTABILITY.md)
- [Failure / repair history](FAILURE-REPAIR-HISTORY.md)
- [Technique cards](TECHNIQUE-CARDS.json)
- [License provenance](LICENSE-PROVENANCE.md)
