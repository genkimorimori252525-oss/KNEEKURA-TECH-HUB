# JAR provenance

## Exact artifact

`JujutsuCraft-ver50.1-forge-1.20.1.jar`

- SHA-256: `094247a33bf9c4a741a17fee9ecd1eb5879c97f107ae784af81cfc0f1eee26c9`
- SHA-1: `6c5dd6c74c45351b1029c204cc1d147fc459de4d`
- bytes: 16,398,540
- entries: 6,377
- classes: 3,493
- class major: 61 / Java 17

CurseForge lists the same file name as File ID **7985964**, uploaded 2026-04-26 for Minecraft 1.20.1 Forge.

## Embedded identity

`META-INF/mods.toml`:

- `modId="jujutsucraft"`
- `displayName="Jujutsu Craft"`
- `version="50"`
- `loaderVersion="[47,)"`
- Minecraft exactly `[1.20.1]`
- authors: `orca, MCreator`
- license: `All Rights Reserved`

The release filename/public page says **50.1**, but embedded metadata remains **50**. Exact hash/File ID control identity.

## Dependencies

The packaged metadata declares GeckoLib and PlayerAnimator both as mandatory entries and as duplicate optional entries. This raw contradiction is preserved; effective FML resolution was not runtime-tested.

## Transformation boundary

`mixins.jujutsucraft.json` exists, but its mixin/client lists are empty. No Access Transformer or coremod transformer was found. Presence of a mixin config alone is not evidence of active transformation.

## Source boundary

No `.java` entries are packaged. Public web/GitHub search did not locate an official Orca source repository. Static findings therefore use classfile disassembly/resource inspection as ORIGINAL_BINARY evidence.

Raw JAR and decompiled trees are not committed to Tech Hub.
