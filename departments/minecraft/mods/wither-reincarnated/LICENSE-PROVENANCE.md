# Wither: Reincarnated — License and Provenance

## Reviewed artifact

- name: Wither: Reincarnated
- file: `witherreincarnated-1.20.1-1.0.5.jar`
- SHA-256: `00589726de7d82628d92761394a8a3e6b153c28942f50c9ae6ba7860b0fab80a`
- size: 12,807,443 bytes
- mod id: `witherreincarnated`
- version: 1.0.5
- Minecraft: `[1.20.1,1.21)`
- Forge/JavaFML: `[47,)`
- author metadata: `Alexander's Fun and Games`
- acquisition: user-supplied binary in the analysis conversation, 2026-10-08

## Declared license

`META-INF/mods.toml` declares:

**All Rights Reserved**

For this research pass that means:

- no redistribution of the supplied JAR;
- no committed decompiled source tree;
- no copied Java method bodies;
- no copied texture/model/sound assets;
- no inference that public download access grants a reuse license;
- technical ideas are recorded as derived behavior/architecture descriptions and
  must be reimplemented independently when adopted.

## Source state

No authoritative public source repository matching this exact v1.0.5 binary was
established during the investigation.

Therefore:

- source/binary equivalence is **UNESTABLISHED**;
- class and behavior findings cite the exact binary identity, not a Git commit;
- any future public source discovery must be verified independently against the
  artifact before it can replace this binary receipt.

## Permitted KNEEKURA retention

Git may retain:

- exact hash/size/version;
- package/class names;
- Mixin and tag names;
- configuration-key/default summaries;
- call/state relationships derived from inspection;
- independent engineering lessons;
- bounded numeric behavior facts necessary to describe the analyzed binary.

Git must not retain from this artifact:

- the JAR;
- a decompiled tree;
- full bytecode dumps;
- third-party textures/models/audio;
- large extracted resource packs.

The local/user-provided artifact remains external evidence, not a repository asset.

## Adoption rule

Any KNEEKURA implementation inspired by this analysis is categorized as
**concept reimplementation** unless a separate, explicit license review authorizes
concrete code reuse.

For the Bedrock Wither reconstruction specifically, Wither: Reincarnated is a
**REFERENCE** only. Its constants and encounter design do not establish Bedrock
behavior.
