# Get It Together, Drops! — bounded history, missing 1.20 Forge source

**Original release:** [Forge 1.20/1.20.1 v1.3 file 4578649](https://www.curseforge.com/minecraft/mc-mods/get-it-together-drops/files/4578649), released 2023-06-10.

**Source gap:** Official repo `1.19` branch pinned `5adec7a58162d9762feeb1348eb11ce349638ae6` is Minecraft **1.19.2**, Forge 43.1.47. Developer's [next NeoForge 1.20.2 commit `095d051...`](https://github.com/bl4ckscor3/GetItTogetherDrops/commit/095d051034bbd8560f1bc5794a5ab1517ac822b5) (2023-11-10) says 1.20 changes were not committed. We cannot report an inspected original 1.20 bug or repaired code. Existing source demonstrates the conceptual ItemEntity Mixin only.

### Scoped issue reviews: no direct 1.20.1 repair pair supported

- [#9](https://github.com/bl4ckscor3/GetItTogetherDrops/issues/9): feature request to allow radius <0.5, not a crash/repair.
- [#10](https://github.com/bl4ckscor3/GetItTogetherDrops/issues/10): Fabric 1.21.9 `NoSuchMethodError` unrelated loader/API; no 1.20.1 Forge inference.
- Generic reports about merging and removal/upgrade were discovery-only; no exact issue→repair source link reviewed.

**Legitimate negative:** `NO_SUPPORTED_REPAIR_IN_BOUNDED_WINDOW`, **not** “mod has no defects.” Whole history and distributed binary/JAR archive NOT_ACQUIRED. Performance/correctness NOT_RUN.
