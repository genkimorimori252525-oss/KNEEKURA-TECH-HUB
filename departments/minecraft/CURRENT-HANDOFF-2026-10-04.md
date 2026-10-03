# KNEEKURA Minecraft — Current Handoff

Date: 2026-10-04 (Asia/Tokyo). **Work in progress**: the user's full remaining `/goal` is active. Continue from [remaining execution matrix](vanilla-ai/REMAINING-EXECUTION-MATRIX-2026-10-04.md); the approved architecture/full criteria remain [LOCAL-EXECUTION-HANDOFF-2026-10-02.md](LOCAL-EXECUTION-HANDOFF-2026-10-02.md).

TECH HUB is the only source repository. LAB is its `departments/minecraft/lab` feature; no standalone LAB repository changes are required. Draft PR79 retains its foundation; Draft PR80 carries this continuation. Do not equate a completed implementation slice with full operational acceptance.

## New verified source work

- Exact Forge 1.20.1 JAR research includes 896 entity-package class headers, 101 Mob-derived classes /79 concrete and corresponding method-body exports. [Public metadata inventory](vanilla-ai/ANCHOR-MOB-CLASS-INVENTORY-2026-10-04.json) contains hashes/inheritance/method/constructed-Goal metadata, not private paths or decompiled bodies. Full per-algorithm semantic and registry/runtime coverage are separate remaining items.
- [Result research](vanilla-ai/NATIVE-RESULT-HOOK-RESEARCH-2026-10-04.md) distinguishes original successful `randomTeleport` from failed/pre-event attempts, projectile impact from damage return/HP effects, and original TF phase prerequisites. Independently sourced NeoForge1.21.1 damage-post concepts and modern Paper reports do not become ANCHOR truth.
- The original `LivingEntity.randomTeleport(DDDZ)Z` RETURN now supplies a bounded `CONTROL_TELEPORT_RETURN` under the existing explicitly armed `control` burst channel. Exactly selected subject/channel/thread/context/window/event/byte gates remain in force; no teleport replay or fabricated reason.
- Retained Decision treats the actual boolean as a RESULT. Only a valid true return becomes an `EXPLICIT_TELEPORT` break between existing SERVER samples. Same-tick placement requires matching writer identity and explicit sequence order. Callback coordinates are never additional sampled positions.
- The optional native cache consumes only flushed canonical successful callbacks as pending gaps. False/malformed/stale/revision-mismatched or ambiguously ordered callbacks do not become successful typed gaps. The cache remains display-only, default-OFF and bounded to128 real position samples.
- Related-projectile capture now registers only an actually accepted fresh spawn owned by the selected Mob. Cached owner fields, exact references, finite16 retention and the existing burst gates bound spawn/completed-tick/base-impact/Arrow-or-Fireball original hurt-call receipts. Actual boolean and cached HP delta remain separate facts; the original hurt call executes once and exceptions propagate. Retained projectile traces use independent UUIDs and one global128-position budget, with a separate default-OFF presentation layer. Custom attacks, explosions and missing/cancelled invocations remain outside proven coverage.
- A retained-presentation regression exposed dropped teleport callbacks between bounded SERVER samples. The presentation now preserves those existing callback records, so a successful original short teleport also cuts its retained-view segment.

## Verification class and limits

The current source slice passed Motion/Decision **98 tests /0 skipped**, including RED→GREEN typed teleport and related-projectile result/trace/presentation regressions. Genuine mapped Forge API contracts passed exact-owner/channel/thread/context/cap/no-replay/single-original-call/exception tests, and production Gson projectile output passed the Node validator. Pure native cache RED→GREEN passed. Combined owner/Arena/camera/writer/world/API regression passed; all actual bridge sources, including the new Mixins, compiled locally against hash-checked genuine dependencies.

**Native firing of the new teleport/projectile Mixins has not yet been accepted.** Current source/API tests are not a successful real Enderman teleport or integrated ranged trial. The damage-site redirect's compatibility with the full runtime stack also needs a native launch. Existing native-r13/r14/r15 proof remains tied to its original producer SHAs; none is retroactively relabeled as this generation.

The published teleport generation `2cfe15163caabf42be21224e7e8d0d5aab6d9314` has all three exact-HEAD CI checks SUCCESS: source push run `37142669732`, source PR run `37142673919`, pytest run `37142673973`. New ranged-result publication must use its own exact HEAD checks; this earlier success is not its acceptance. Windows full-suite limitations remain visible in the previous handoff.

## Next required work

1. Prove actual typed teleport and shot→projectile→hit/miss in frozen private native runs, including transform compatibility and missing/cancelled outcome limits of the new callbacks. Related-projectile native drawing is not yet established by the retained layer.
2. Use separately labeled damageable/phase-appropriate private TF fixtures. Prior r13 Boss invulnerability prevented damage-driven Ur-Ghast transition acceptance.
3. Complete remaining all-algorithm/terrain/community/FRONTIER and original path-frontier/effective/custom control research; add only confirmed missing hooks with RED→GREEN regressions.
4. Complete integrated pursuit/Brain/custom-flight/missing-capture and Boss coordination examples, same-initial-state observer-effect trials, raw capture separation and actual pixels/GPU coverage.
5. Independently review the new whole diff, verify final exact HEAD CI/genuine Forge regressions, and reconcile every original completion item. The full goal stays active while required work remains.

Original world85/85 hashes were reverified unchanged at discovery; the pinned MOD checkout is clean at53a84d0. New private evidence uses C: because K: had approximately1.9GB free; preceding evidence and predecessor worlds are preserved. No user/private runtime data, credentials or raw source bodies are committed.
