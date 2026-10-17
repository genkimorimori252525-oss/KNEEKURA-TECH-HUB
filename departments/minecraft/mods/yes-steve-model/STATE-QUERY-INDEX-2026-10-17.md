# State/query extension index — 2026-10-17

Start here for the server/player-state and query-input extension to the earlier
[JAVA-PIPELINE-INDEX](JAVA-PIPELINE-INDEX-2026-10-17.md). Read the one relevant row,
then its exact evidence/tool only when needed; ordinary repository work need not
read every instruction snapshot or rerun unrelated checks.

## Choose the seam

| Question | Focused dossier |
|---|---|
| What state changes are staged and rate-gated? | [Server producer](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md) |
| When does dirty model state replace delta updates with a full snapshot? | [Full synchronization](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md) |
| Does geometry reset occur before or after received properties? | [Property/reset lifecycle](PROPERTY-RESET-LIFECYCLE-RECOVERY-2026-10-17.md) |
| Which Java paths request another full update? | [Full/dirty callers](FULL-SYNC-CALLERS-RECOVERY-2026-10-17.md) |
| Which armor/effect source does a query actually use? | [Equipment/effect queries](EQUIPMENT-EFFECT-QUERY-RECOVERY-2026-10-17.md) |
| Are strings parsed/cached, and what does a missing cosmetic item mean? | [Resource/adapters](RESOURCE-ARGUMENT-ADAPTER-RECOVERY-2026-10-17.md) |
| Are world offsets interpolated/local-axis, and what is camera rotation? | [World/position/camera](WORLD-QUERY-INPUT-RECOVERY-2026-10-17.md) |
| Which clock, units and completion flag does a query read? | [Time/controller queries](TIME-CONTROLLER-QUERY-RECOVERY-2026-10-17.md) |
| Does a child entity also switch animation context and storage? | [Child/arrow context](CHILD-CONTEXT-ARROW-RECOVERY-2026-10-17.md) |

Each dossier identifies method/field scope and its matching evidence/verification.
The scalar-write inventory is documented with the property/reset dossier, making
ten separately runnable tools behind these nine topic entries.

## Preserve these distinctions in reconstruction

- Full-message flag is not unconditional clearing of every client field.
- Model-ready geometry load may happen at a different time from packet handling.
- A static conditional stale/reset concern is not a reproduced game defect.
- Cosmetic present-empty differs from absent; general armor and elytra selection
  use different fallback chains.
- Enchantment aggregation actually rereads argument 1; do not silently rewrite it
  to the loop index or assume lazy getters are evaluated just once.
- Resource cache holds a parsed identifier, not a registry object.
- Relative-block offsets all evaluate before the range test; position uses an
  effective animation partial tick, and camera query is not an entity look-at.
- all/any completion flags differ for Bedrock aggregation despite equality on the
  coded single-player producer path. Finished flag is not a universal IDLE test.
- Child context retains parent animatable/event/animation references but does not
  inherit controller/debug/emission fields; evaluator child creation is separate.

## Fixed checkpoint, not whole-project acceptance

[STATE-QUERY-EXTENSION-CHECKPOINT-2026-10-17.json](STATE-QUERY-EXTENSION-CHECKPOINT-2026-10-17.json)
records a single batch rerun of exactly ten named tools against the fixed artifact
and pinned source. All ten passed; 16 overlapping method snapshots were compared
with no conflicts. Central mapping bytes remained unchanged at 669 rows. The
batch took about 3.2 seconds on the recording environment; that timing is not a
portable performance promise or game benchmark.

Reproduce with tools/state_query_extension_checkpoint_ysm_265.py and its required
--jar, --source-root, --out parameters. The script stores artifact/evidence/tool
receipt hashes, validates negative controls, and compares overlapping bodies.
It runs static Python auditors only. No game/JVM/native/GPU execution, packet send
or whole-repository CI is included. It does not alter the earlier fixed17 manifest
or imply all post17 research cohorts are part of this ten-cohort batch.

Independent semantic review remains NOT_RUN for this extension. The unchanged
669 map is not a percent-complete measure; captured method counts include overlap
and supporting declarations. Raw JAR/source inputs remain external to Git.

## Still open

Resolve conditional reset concerns only with an appropriate real runtime receipt
or stronger evidence, not a guessed patch. Continue public/foreign binding
reachability and remaining typed-query/entity-specific input paths. Native model
loading/render producers and actual optional-mod implementations remain outside
the proven Java boundary. This index is a checkpoint, not a stopping instruction.

- [Shield/effect event producers](SHIELD-EFFECT-EVENT-PRODUCERS-RECOVERY-2026-10-17.md): NBT key-presence cooldown versus positive counter, effect-event guards, coalesced byte-level staging and presence-mask query provenance. The fixed6 [checkpoint](SHIELD-EFFECT-QUERY-CHECKPOINT-2026-10-17.json) compares eight repeated snapshots without conflict; no live event timing or transport was tested.
