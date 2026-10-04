# Native bounded ground-query acceptance

Frozen LAB: `ee273cccb191ea10ff375191511c8304ac711adf`; pinned MOD: `53a84d06578632b5d123e3c2bb631b611bf830d7`. Minecraft 1.20.1 / Forge 47.2.0 / Java 17, actual private tank copy. Deep decision hooks were OFF. This is native observer-query smoke acceptance, not effective malus, complete Mob behavior or total observer-effect acceptance.

Run: `run-20261003093726-9ab5570bec1e`; session: `sess-20261003093726-84d660ddd3f5`; snapshot: `snapshot-20261003093726-1bb75374eb5e`. Private raw/canonical observations and receipts remain outside Git under `native-r8` in the native data root.

| Case | Revision | Ground rows | Cells | Capture status |
| --- | --- | --- | --- | --- |
| Default OFF | 1 | 0 | 0 | NOT_CAPTURED |
| Snapshot only | 2 | 0 | 0 | NOT_CAPTURED |
| Zombie radius 1 | 3 | 1 | 9 | AVAILABLE |
| Zombie radius 3 | 4 | 1 | 49 | AVAILABLE |
| Zombie radius 3, two-cell limit | 5 | 1 | 2 | PARTIAL |
| Ghast static ground | 6 | 1 | 9 | AVAILABLE |
| Villager static ground | 7 | 1 | 9 | AVAILABLE |
| Ordinary selection resets query | 8 | 0 | 0 | NOT_CAPTURED |

All 78 acquired cells passed the strict terrain decoder. Their effective malus remained `NOT_EXPOSED`, and evaluated-by-PathFinder remained `NOT_CAPTURED`. Ghast's ground classification does not imply admission by its flight controller/evaluator. Each armed revision produced exactly one row; no original decision events appeared with deep hooks OFF.

The writer retained **510 records**, drop **0**, remaining queue **0**, clean ACK and verified process exit. Canonical finalization is **EVIDENCE_COMPLETE**. The original tank's **85 file hashes matched** after the trial; original save files were not edited. Retained native report SHA256: `940d3873659765e770f6693d44cf6de13e24579708adf0436e804c5fddea9578`.

The actual `evidence-decision --channel terrain_ground` CLI returned the radius-3 row at tick **40948**, Arena epoch **0**, revision **4**, with source ID **`obs:forge-runtime:43296:149`**. Reading the finalized store left both hashes unchanged:

- Canonical observations: `922c4a66721a53ff99754cab86fb6a6c8da9dc1261bf0edbd7f46d54f80d81ae`.
- Finalization: `be145baa5f681000e6c8e4e3ccb8f1428b1c3767370775a9436a07088cb1d07e`.

Producer capture costs for these five individual queries were **4.6318, 0.3481, 0.1132, 0.0784 and 0.1166 ms** respectively. This scope excludes encoding/writer/viewer and is not a controlled estimate of total observer effect. First-call and warmed-call costs are not interchangeable; the inter-cell deadline cannot preempt one classifier call.

For private startup IO only, 1,226 resource-pack files / 35,025,277 bytes were copied into a hash-checked C: cache through an explicit resource-directory Junction. The preceding K: pack was preserved. No world directory link, MOD source edit, owner gate change or gameplay behavior shortcut was introduced. Native startup still performed the original pack initialization.

## Source validation

Motion/Decision tests: **59 pass / 0 skip**. Portable Java/source contracts and genuine mapped Forge API tests, including terrain request and field tests, passed. All bridge/Mixin sources compiled against exact hash-checked dependencies. Linux source checks (push and PR) plus repository pytest all succeeded at the frozen LAB head. Existing Windows symlink/pipe regression limitations remain recorded separately; this trial does not erase them.

Remaining work includes spatial presentation, SDK and source-specific Boss adapters, full representative behavior fixtures and controlled observer-effect measurement. These results do not declare the complete local handoff finished.
