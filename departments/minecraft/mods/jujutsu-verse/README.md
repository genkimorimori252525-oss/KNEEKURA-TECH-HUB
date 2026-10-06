# Jujutsu Kaisen (Jujutsu Verse) — V8.1 / Minecraft 1.20.1 Forge

Status: **STATIC_ANALYSIS_COMPLETE — runtime NOT_RUN**

This target is kept separate from **Jujutsu Craft (Sorcery Fight)**. This record preserves Tehen's Jujutsu Verse implementation techniques, especially its visual-effect stack and Domain Expansion clash/cut-in system.

## ANCHOR

- Distribution: jujutsu_kaisen-8.1-forge-1.20.1.jar
- CurseForge project: Jujutsu Kaisen (Jujutsu Verse), Project ID 1269804
- CurseForge File ID: 8097357
- Public release: 2026-05-16
- Minecraft: 1.20.1
- Loader: Forge / javafml [47,)
- Java classfile: 61 / Java 17
- SHA-256: d0f2f4e427ae3db92432cfac186a7db137ab8960807ed13ebfa64c7971cb8217
- SHA-1: 84f8b095672d931c9ffed30bd7eb62354863311a
- Size: 28,285,565 bytes
- ZIP entries: 4,860
- Classes: 2,619
- Mod ID: jujutsu_kaisen
- Distribution version: 8.1
- Embedded mods.toml version: 7.0
- Public license: All Rights Reserved
- Embedded license field: Not specified
- Runtime: NOT_RUN

The exact uploaded binary hash is the canonical ANCHOR. Distribution version and embedded version are deliberately kept separate.

## Main findings

- Domain Expansion owns a dedicated DOMAINHP durability layer and clash lifecycle.
- Ordinary attack damage can damage Domain HP through Attackhit1Procedure -> DomainbattleProcedure.
- Active clashes also push/pull Domain HP every tick using Domain Expansion effect amplifiers.
- DomainCutinOverlay is a client-only presentation layer with 2-way diagonal and 3-way split cinematics.
- The cut-in uses depth-buffer masks, procedural line backgrounds and live 3D entity rendering.
- Domain sure-hit evaluation is amortized over a 20-tick expanding spherical shell with coarse interior sampling.
- VFX are separated into particles, custom world geometry, renderer layers/mixins, post-processing, GUI cinematics and FBO-backed surfaces.
- Black Flash is procedural geometry; beam/VFX systems reconstruct dense visuals client-side from compact synchronized entity state.
- RippleEffectManager projects a target entity into screen coordinates and uses that position as a post-process shader epicenter.
- CustomPortalBlockEntityRenderer renders a separate TextureTarget and projects it through world geometry.
- The technique-focused pass maps all 18 player kits and their named UI moves into per-technique VFX/trajectory evidence, preserving partial mappings instead of guessing.

## Whole-target scale

Class package counts:
- procedures: 1,196
- entity package: 509 classes
- client: 336
- item: 274
- network: 47
- potion: 56
- block: 37
- init: 37
- mixins: 16

Resource-file counts:
- textures: 1,145
- models: 239
- Geo models: 122
- GeckoLib animations: 121
- sounds: 63
- particle definitions: 50
- shader files: 8
- PlayerAnimator JSONs: 2
- advancements: 130
- damage types: 36
- worldgen: 33
- structures: 26

## Documents

- JAR-PROVENANCE.md
- SOURCE-INVENTORY.json
- FOUNDATION-MAP.md
- DOMAIN-CLASH-AND-CUTIN.md
- RENDERING-EFFECTS.md
- TECHNIQUE-EFFECT-PATTERNS.md
- TECHNIQUE-VFX-ATLAS.md
- TECHNIQUE-VFX-INVENTORY.json
- PLAYER-ANIMATION-ATLAS.md
- DOMAIN-VISUAL-ATLAS.md
- JUJUTSUCRAFT-COMPARISON.md
- TECHNICAL-KNOWLEDGE.md
- manifest.json

## Evidence boundary

This record is based on the exact user-supplied V8.1 JAR, class/resource inspection and targeted public release metadata. Raw copyrighted assets and decompiled source are not committed.