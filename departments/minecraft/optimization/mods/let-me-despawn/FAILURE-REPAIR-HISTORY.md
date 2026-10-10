# Let Me Despawn — bounded selected reports, NO proven 1.5.0 repair

Track: target Forge 1.20.1 **1.5.0 source unacquired**; COMPARATIVE 1.18 Forge `1.0.3`, 1.21 NeoForge/Fabric source `1.4.4`. Selected public issue window: #66 and other gear despawn reports. No directly verified 1.5.0 issue→repair diff.

## LMD-66 — Endermen with blocks persist in tall forest

[Issue #66](https://github.com/frikinjay/let-me-despawn/issues/66), opened 2026-02-23, user exact **`letmedespawn-1.20.x-forge-1.5.0.jar`**, Forge MC1.20.1, DynamicTrees 1.4.9 / BiomesOPlenty, Endermen carry blocks and stop despawning. **Report only**: could be NBT/persistence rule/Enderman block holding vs item pickup, distance constraints or chunk loading. No static source for 1.5.0 or validated reproduction. Reporter follow-up refers to fix in much newer `1.26.9.1`; **this does not prove fix in 1.5.0**.

## Older/non-anchor cases

[Issue #45](https://github.com/frikinjay/let-me-despawn/issues/45) MC 1.20.1 **Fabric** reported lost held items on despawn; avoid copying to Forge 1.5.0 as confirmed cause. [Issue #57](https://github.com/frikinjay/let-me-despawn/issues/57) other dimension/NETHER unloading symptom; root and version compatibility not fully audited.

**No supported exact-code repair diff in this bounded window**. Need 1.5.0 original code or user release JAR, Mixin target descriptors, RemovalReason handling, source/asset rights; until then no reuse confidence or performance benchmark.
