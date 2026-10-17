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
