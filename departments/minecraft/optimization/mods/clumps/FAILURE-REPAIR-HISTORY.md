# Clumps — version-separated failure and repair (bounded window)

**Scope:** Clumps 1.20/1.20.1 branch and Issues #124, #128, #133, #134, #138, #141, #144; only selected original issue/comment bodies and one actual repair patch read. No full issue/PR history and no user binary.

## C-124 — custom spawn egg XP map clobbered (older 1.20 Fabric)

[Issue #124](https://github.com/jaredlll08/Clumps/issues/124) user: custom SpawnEgg with `EntityTag:{id:experience_orb,Count:65538,Value:32767}` creates orb returning zero XP while direct `/summon` works. Report Minecraft **1.20 Fabric, Clumps 11.0.0.1**, **NOT user 12.0.0.4**.

**Verified source diff** [commit `ebb464852a132188a023cf0f5698e8a4216b9476`](https://github.com/jaredlll08/Clumps/commit/ebb464852a132188a023cf0f5698e8a4216b9476), parent `3b2b4ad169439b87c91f648b4415f688c7672619`: `MixinExperienceOrb.addAdditionalSaveData` checks `clumps$clumpedMap != null` before writing nested `clumpedMap` tag, so it does not force initialization with current zero `value` during serialization. After commit author [says fixed](https://github.com/jaredlll08/Clumps/issues/124#issuecomment-1611967103). This guard persists in pinned 1.20.1 source. No KNEEKURA actual runtime verification.

**Lesson:** lazy aggregate state construction must not mutate separate authoritative metadata during serialization/loading (and zero XP legitimate value should be handled properly).

## C-144 — event ownership causes known incompatibility on exact user-version

[Issue #144](https://github.com/jaredlll08/Clumps/issues/144) **MC 1.20.1 Forge 47.3.0, Clumps 12.0.0.4** plus Blood Magic 3.3.3-45: XP increasing and redirect-to-item handlers use Forge `PlayerXpEvent.PickupXp`, modify XP orb's `value`, but grouped `clumpedMap` determines later experience award independently. [Maintainer comment](https://github.com/jaredlll08/Clumps/issues/144#issuecomment-2208130840) says incompatible with any mod modifying `value` inside PickupXp and recommends Clumps Value/Repair events. **This is a confirmed source-contract incompatibility + maintainer admission**, NOT a code fix. No PR/commit fixing exact behavior identified. Do not describe closed issue as resolved.

## C-134 and C-128 — reports with contrary/no reproduction

- [#134](https://github.com/jaredlll08/Clumps/issues/134): Forge 12.0.0.3 with BetterMC4, user says Mending not working; maintainer recreates same behavior in a flat creative world and sees **Mending works**, requests isolated modpack proof; reporter found worked after client restart in fresh world. No supported root cause/repair.
- [#128](https://github.com/jaredlll08/Clumps/issues/128): Forge 12.0.0.3, XP Tome, one ticking crash user could not reproduce again; closed for inactivity, **no verified fix**.

## C-141 — false version attribution trap

[#141](https://github.com/jaredlll08/Clumps/issues/141) report of XP duplication sounds severe; follow-up comments explicitly identify **Minecraft 1.12.2 / Clumps 3.0.0** and developer advises 3.1.2. **Not** a known issue for owner's 1.20.1 / 12.0.0.4. Classified COMPARATIVE older, not ANCHOR.

History was scoped; no complete source-body acquisition, issue video/transcript, runtime tests or importer-grade CAS IDs. `PERFORMANCE_NOT_VERIFIED`.
