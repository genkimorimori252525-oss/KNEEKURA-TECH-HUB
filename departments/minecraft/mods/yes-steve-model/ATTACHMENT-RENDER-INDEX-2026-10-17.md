# Attachment and first-person render evidence index

Fixed artifact2.6.5 Forge1.20.1; primary static review only. Central669 mappings unchanged. This index joins Java-side attachment and event flow without claiming native/GPU output or independent semantic approval.

| Question | Dossier |
|---|---|
| How are locator hierarchies and matrices prepared? | [Locator matrices](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md) |
| Which consumers discard/use the returned ancestor-scale flag? | [Exact caller inventory](LOCATOR-MATRIX-CALLERS-EVIDENCE-2026-10-17.json) |
| How do items, head, elytra, parrots and backpacks attach? | [Concrete layers](ATTACHMENT-RENDER-LAYERS-RECOVERY-2026-10-17.md) |
| How are passenger poses and optional hats selected? | [Passenger and hats](PASSENGER-HAT-ATTACHMENT-RECOVERY-2026-10-17.md) |
| When do player events and texture reads happen? | [Player entry](PLAYER-RENDER-ENTRY-RECOVERY-2026-10-17.md) |
| How do arm modes, cached entities and renderer reloads connect? | [Arm render and registry](FIRST-PERSON-RENDER-REGISTRY-RECOVERY-2026-10-17.md) |
| When is ordinary/provider arm rendering cancelled? | [Arm replacement events](ARM-REPLACEMENT-EVENTS-RECOVERY-2026-10-17.md) |

The fixed9-cohort [checkpoint](ATTACHMENT-RENDER-CHECKPOINT-2026-10-17.json) runs these seven audits plus two earlier shared-adapter anchors. All9 passed in2.246seconds;29 overlapping method snapshots matched,0 conflicts. That comparison tests exact snapshot consistency, not independent semantic review. Existing17/10/9/14 manifests remain frozen. No whole-project CI or target runtime was run.

Run tools/attachment_render_checkpoint_ysm_265.py explicitly with --jar, --source-root and --out. Normal evidence searches do not run this batch. Do not treat captured declarations, overlap counts, audit checks or registry flags as completion percentages or successfully rendered frames.

Next connected Java question: vehicle/projectile renderer entry and render-type/culling behavior, avoiding the already reviewed controller and native-wrapper paths.

## Later render lifecycle extension

- [Vehicle/projectile entries](VEHICLE-PROJECTILE-RENDER-RECOVERY-2026-10-17.md) and [dispatcher replacement](DISPATCHER-RENDER-REPLACEMENT-RECOVERY-2026-10-17.md): direct animatable overloads differ from concrete entity-entry gates.
- [Fishing-line geometry](FISHING-LINE-GEOMETRY-RECOVERY-2026-10-17.md): reuses dispatcher snapshots, does not add a new method count.
- [Player view gates](PLAYER-REPLACEMENT-VIEW-GATES-RECOVERY-2026-10-17.md): external first-person animation coexistence and earlier cancellation.
- [Shader/buffer adapters](SHADER-BUFFER-ADAPTERS-RECOVERY-2026-10-17.md): state sampling, provider registration, signed ID arithmetic and flush scope.
- [GUI preview state](GUI-PREVIEW-STATE-RECOVERY-2026-10-17.md): temporary mutation, actual fake-player caller boundary and selected Vineflower comparison.

A separate fixed8-cohort [render-lifecycle checkpoint](RENDER-LIFECYCLE-CHECKPOINT-2026-10-17.json) passed in1.991seconds with24 overlapping snapshots and0 conflicts. Six later cohorts plus two earlier anchors were checked; the fixed9 above remains unchanged. The seven-case JDK packing model and one-class Vineflower run have their own receipts and are not Minecraft/native tests.
