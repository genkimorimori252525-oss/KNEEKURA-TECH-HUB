# Yes Steve Model (YSM) — architecture / animation / renderer research


Need a known query/class quickly? Use the optional [evidence locator](EVIDENCE-LOCATOR-2026-10-17.md); no startup audit or tool installation.

State/query extension navigation: [STATE-QUERY-INDEX-2026-10-17.md](STATE-QUERY-INDEX-2026-10-17.md). Use the relevant seam; no ordinary-startup audit is required.
Controller assembly/predicate continuation: [CONTROLLER-QUERY-INDEX-2026-10-17.md](CONTROLLER-QUERY-INDEX-2026-10-17.md).

For implementation reuse, start with [the compact contract guide](REUSE-CONTRACTS-2026-10-17.md).
Attachment/render lifecycle: [ATTACHMENT-RENDER-INDEX-2026-10-17.md](ATTACHMENT-RENDER-INDEX-2026-10-17.md).
Session and model state: [CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md](CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md).

Sound emission/resource lifetime: [SOUND-LIFECYCLE-INDEX-2026-10-17.md](SOUND-LIFECYCLE-INDEX-2026-10-17.md).

## Scope

- Target: **Yes Steve Model (YSM)**
- Primary adaptation anchor: Minecraft **1.20.1 + Forge**
- Distributed target: **2.6.5-forge+mc1.20.1**
- Main focus: model runtime, Molang, animation controllers, per-entity state, rendering, model distribution and integration seams
- Research status: **EXACT_JAR_ANCHORED / 955_CLASS_FOUNDATION_MAPPED / JAVA_OBFUSCATION_PARTIALLY_RECOVERED**
- Whole-target status: **IN_PROGRESS / NOT COMPLETE**
- Research date: 2026-10-05; latest continuation: **2026-10-17**

This workspace follows KNEEKURA's evidence rules: distributed artifact, release-line source candidate,
frontier source, community reconnaissance and comparative implementations are kept as separate tracks.

No Minecraft implementation code is changed here.

## Latest connected Java research

Start with [the October17 pipeline index](JAVA-PIPELINE-INDEX-2026-10-17.md) for
the state/query, controller, scheduler, storage and render-boundary chain.
The central map remains669; recent cohorts are primary static analysis pending
independent semantic review. [Scoped batch receipt](JAVA-PIPELINE-CHECKPOINT-2026-10-17.json).

## DISTRIBUTED ANCHOR

Official Modrinth release:

- version: **2.6.5-forge+mc1.20.1**
- version ID: **Zqooxsd2**
- Minecraft: **1.20.1**
- loader: **Forge**
- client + server
- previous page display size: **5.02 MB** (not used as binary identity)
- exact JAR size: **63,269,843 bytes**
- exact SHA-256: **25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f**
- exact SHA-1: **151ac7b24da8beeca1a20864565743cfd77af286**
- displayed license: **ARR**

The official distributed JAR is now an **EXACT BINARY ANCHOR**. Binary/source equivalence to the
public f184eda source candidate remains **NOT_ESTABLISHED**; exact binary identity and source identity
are deliberately separate claims.

## RELEASE-LINE SOURCE CANDIDATE

The now-public official Git history contains a strong 2.6.5 release-line candidate:

- repository: YesSteveModel/YesSteveModel
- revision: **f184edabd1b5115ce5a24cb6d155ba5a669f5ba6**
- tree: **da392147cdba57b734aa18e25674745291d7f24a**
- source-declared version: **2.6.5-forge+mc1.20.1**
- date: 2026-04-18
- tree: 1,888 entries / 1,513 blobs / 828 Java files / 669 main-resource blobs

History immediately around it is unusually useful:

1. e1413f7 raises mod_version from 2.6.4 to 2.6.5.
2. fb23351 fixes bundled Wine Fox model content while still declaring 2.6.5.
3. f184eda adds a Fast DEV build task and still declares 2.6.5.

This makes f184eda a strong **release-line source candidate**, but it is not asserted to be byte-for-byte
the source used for Modrinth version Zqooxsd2.

The historical tree has no root LICENSE file. The current public repository is Apache-2.0, but this
research does not silently project the current license backward onto the historical snapshot.

## FRONTIER SOURCE

Current official public reconstruction:

- repository: YesSteveModel/YesSteveModel
- branch: dev/1.20
- revision: **74c53b58b2f9b680a6c6dc5d5d41e7422fc000bb**
- tree: **6cb3ff6224bd19f76481dd59f40807e0c98da5ec**
- source-declared version: **3.0-dev-forge+mc1.20.1**
- license: Apache-2.0
- tree: 2,712 entries / 2,075 blobs / 1,140 Java files / 55 Proto files / 148 test blobs / 182 docs blobs

The FRONTIER is a substantial redesign and must not be silently attributed to the distributed 2.6.5
JAR. It is valuable because the maintainers now document ownership, lifecycle, network, animation,
model-management, JNI and renderer boundaries explicitly.

## Main result

YSM is not merely a replacement player renderer.

The recoverable architecture is closer to:

~~~text
Minecraft Entity state
        |
        v
per-entity state tracker + Molang context
        |
        v
coded / Bedrock / hybrid controllers
        |
        v
bone snapshot / flattened bone state
        |
        +------ event / sound / side-effect queues
        |
        v
native-capable geometry renderer
        |
        v
Minecraft VertexConsumer / draw pipeline
~~~

On the 2.6.5 release line, Java already owns the semantic animation state and feeds flattened bone
state through a JNI renderer boundary. The 3.0 frontier makes that separation even more explicit:
Java owns model identity, lifecycle, Molang/controllers and publication, while native code is treated
as a bounded capability layer for codec/render work.

## Highest-value reusable technologies

1. **Per-entity animation runtime** rather than model-global mutable animation state.
2. **Coded + Bedrock + hybrid controller polymorphism** behind a shared controller contract.
3. **Molang as a state/query language**, with explicit queued side-effect execution.
4. **Visibility/distance-aware animation throttling** for remote or culled entities.
5. **Flattened bone-state buffers** between semantic animation and hot rendering.
6. **Named locator/bone groups** for hands, head, equipment, passengers and first-person anchors.
7. **Async animation schedule / wait barrier** separated from the render commit.
8. **Java semantic layer / native geometry layer separation**.
9. FRONTIER: **Bake -> Extract -> Render** as explicit renderer stages.
10. FRONTIER: **exact-connection session ownership** and separation of catalog publication from model-content activation.
11. **Integration adapters as translators**, demonstrated by Touhou Little Maid, rather than giving every compatibility target a second animation engine.
12. Secondary technique: **semantic structural bytecode matching** from YSM Mapping API for version-resilient external integration.

## Java obfuscation status

A bounded public-evidence pass now recovers a useful subset of the distributed 2.6.5 Java shell:

- native-library bootstrap;
- capability attachment/provider;
- final Java/native renderer bridge;
- player/arm/background render hooks;
- vehicle/projectile/fishing-hook replacement helpers;
- paperdoll/preview render path;
- Carry On and Jade integration anchors;
- TaCZ binding/render/animation seams;
- core animatable/render-layer semantic types;
- a separate unresolved-owner bone accessor surface.

The mapping is keyed by **owner + member + JVM descriptor** because YSM reuses the same obfuscated
member strings across unrelated methods and fields.

The machine-readable map deliberately keeps distributed-artifact observations separate from the
version-matched public source candidate. This exposed concrete source/artifact divergence around the
preview/paperdoll renderer instead of silently forcing them to agree.

The current machine-readable map contains **669** mappings (**405 CONFIRMED / 264 HIGH**).
Every recorded owner/member/descriptor contract passes against the exact official JAR: **295 class
targets, 365 exact methods and 9 exact fields, with 0 failures**. The whole-JAR Foundation Map covers
**955 / 955 classes**. Two large formerly-UNKNOWN islands are now separated as bundled **Concentus
(131 classes)** and **Gagravarr/VorbisJava (86 classes)**; only **15 degree-0 singleton classes** remain
UNKNOWN.

A whole-JAR Foundation Map now classifies the exact Java artifact by structural domain. The strongest mapped hubs are `IContext` (degree 103), `Function$ArgumentCollection` (86), `Function` (85), `ExecutionContext` (58), `PlayerAnimatableCapability` (57), `YesSteveModel` (50), `YSMBinding` (48) and `NetworkHandler` (47). The strongest cross-domain seam is **CAPABILITY ↔ NETWORK (88 internal edges)**.

The October 5 practical continuation closed loop/control execution, the finite math registration cohort,
property stores, parser lifecycle and typed AST roles, then exhausts a finite directly grounded
source/literal/relational shortlist across controller, GUI, renderer and compatibility roles. All 18
additional concrete source leads also received actual dispositions. At that historical checkpoint, **432 main-component classes
remained unseeded; 661 overall**, including 214 bundled media and 15 isolated classes. This is semantic
recovery; original names and whole-artifact/source equivalence remain unproven. See
[SEMANTIC-RECOVERY-2026-10-05.md](SEMANTIC-RECOVERY-2026-10-05.md) for the stopping boundary and
[SEMANTIC-COVERAGE-2026-10-05.json](SEMANTIC-COVERAGE-2026-10-05.json) for every remaining owner.

Protected native internals remain out of scope.

## October 16 continuation

The [binary evaluator pass](BINARY-EVALUATOR-RECOVERY-2026-10-16.md) connects all
16 operator-table slots to exact lambda implementation handles and reviewed
instruction/control-flow semantics. It adds **20 methods and one field**, preserving
all 604 prior mapping rows. Three wrapper factories, dispatch, short-circuit and
conversion order are covered; this is member-level depth within an existing mapped
class, not 21 additional classes or completion of the entire MOD.

Use [current coverage](SEMANTIC-COVERAGE-2026-10-16.json) and
[current verification](SEMANTIC-VERIFICATION-2026-10-16.json) for this continuation.
October 5 dated coverage and verification files remain historical receipts.
At the October 16 checkpoint, the remaining counts were **432 main / 661 total unseeded**.
No game or target-JAR execution is claimed.

The next [processor lifecycle review](ANIMATION-PROCESSOR-RECOVERY-2026-10-16.md)
retains exact queue, shouldTick and exception paths. Its bounded findings passed
independent review, 146 regression checks, 11 corruption controls and 26 caller
checks. **That processor study itself added no central mappings**; its October 16
checkpoint remained at 625 before the subsequent October 17 additions.
This is not full processor-body semantic closure or a reproduced runtime defect.

## October 17 continuous research

[Active research queue](CONTINUOUS-RESEARCH-QUEUE.md): saving a cohort is not a stop.
The reviewed bone/queue, interpolation and animation-point batch adds 37 mappings:
13 bone/queue methods, 16 MathUtil methods plus one class role, and 7 point methods.
See [checkpoint verification](ANIMATION-PIPELINE-VERIFICATION-2026-10-17.json).

There are now **295 class-role rows**, but **309 distinct owners with any semantic
mapping**: fourteen owners have reviewed member mappings without a separate class-role
row. The graph's still-unseeded count is **646 total / 417 main**, not 955 minus the
class-role-row count. The subsequent keyframe-producer pass is included in these latest counts. None of these counts is a whole-target completion percentage.

- [Bone commit and queue consumers](BONE-COMMIT-QUEUE-RECOVERY-2026-10-17.md)
- [Interpolation boundary](INTERPOLATION-BOUNDARY-RECOVERY-2026-10-17.md)
- [Animation point lifecycle](ANIMATION-POINT-RECOVERY-2026-10-17.md)

Next connected producer and Java bone-state work continues. Native internals,
model protection bypass, game execution and global source equivalence remain out
of this static continuation's claims.

The next [keyframe producer pass](KEYFRAME-PRODUCER-RECOVERY-2026-10-17.md) adds seven
reviewed method mappings, bringing the map to 669. Its 125 checks and 20 corruption
controls passed; [verification](KEYFRAME-PRODUCER-VERIFICATION-2026-10-17.json).
[Java bone-state and allocation](BONE-STATE-RECOVERY-2026-10-17.md) is also recorded
with strict evidence checks, but independent semantic review is still pending and
it adds no central mappings yet.

[Easing/raw-keyframe preparation](EASING-RAW-FACTORY-RECOVERY-2026-10-17.md) now
records Java factory selection and initialization/aliasing semantics with 162 strict
checks and 16 corruption controls. Independent review is pending; the central
mapping count remains 669.

[Coded/predicate controller state decisions](CODED-CONTROLLER-STATE-RECOVERY-2026-10-17.md)
deepen existing method-shape mappings with 170 strict checks and 16 corruption
controls. Pause, STOP captured-state and predicate/context cleanup are explicitly
bounded; independent review is pending and no existing rows are recounted.

[Player clock and transitions](ANIMATION-PLAYER-CLOCK-RECOVERY-2026-10-17.md) now
retain exact threshold ordering, cache capture and duration-unit arithmetic with
278 strict checks and 18 corruption controls. Independent review is pending;
no new central mapping rows are claimed for this depth-only continuation.

## Important limits

- Public release-line source candidate equivalence to the distributed JAR is not proven.
- Native internal implementation of protected 2.6.5 binaries is not analyzed.
- Encrypted-model protection is not bypassed.
- Reddit / user reports are reconnaissance only.
- Runtime performance and correctness have not yet been measured in KNEEKURA LAB.
- Current 3.0-dev architecture contains known unresolved concurrency, render-context and end-to-end validation gaps documented by its own maintainers.

## Files

- [CONTINUATION-PLAN-2026-10-16.md](CONTINUATION-PLAN-2026-10-16.md)
- [ARTIFACT-REACQUISITION-2026-10-16.json](ARTIFACT-REACQUISITION-2026-10-16.json)
- [BINARY-EVALUATOR-RECOVERY-2026-10-16.md](BINARY-EVALUATOR-RECOVERY-2026-10-16.md)
- [BINARY-EVALUATOR-EVIDENCE-2026-10-16.json](BINARY-EVALUATOR-EVIDENCE-2026-10-16.json)
- [SEMANTIC-COVERAGE-2026-10-16.json](SEMANTIC-COVERAGE-2026-10-16.json)
- [SEMANTIC-VERIFICATION-2026-10-16.json](SEMANTIC-VERIFICATION-2026-10-16.json)

- [ARCHITECTURE-RESEARCH-2026-10-05.md](ARCHITECTURE-RESEARCH-2026-10-05.md)
- [MOLANG-SURFACE-2026-10-05.md](MOLANG-SURFACE-2026-10-05.md)
- [TLM-INTEGRATION-2026-10-05.md](TLM-INTEGRATION-2026-10-05.md)
- [MODEL-DISTRIBUTION-2026-10-05.md](MODEL-DISTRIBUTION-2026-10-05.md)
- [OBFUSCATION-RESEARCH-2026-10-05.md](OBFUSCATION-RESEARCH-2026-10-05.md)
- [OBFUSCATION-MAP-2026-10-05.json](OBFUSCATION-MAP-2026-10-05.json)
- [EXACT-JAR-STRUCTURAL-SCAN-2026-10-05.md](EXACT-JAR-STRUCTURAL-SCAN-2026-10-05.md)
- [FOUNDATION-MAP-2026-10-05.md](FOUNDATION-MAP-2026-10-05.md)
- [FOUNDATION-MAP-INDEX-2026-10-05.json](FOUNDATION-MAP-INDEX-2026-10-05.json)
- [SEED-RECOVERY-EVIDENCE-2026-10-05.json](SEED-RECOVERY-EVIDENCE-2026-10-05.json)
- [MOLANG-EVALUATION-RECOVERY-2026-10-05.md](MOLANG-EVALUATION-RECOVERY-2026-10-05.md)
- [MOLANG-EVALUATION-EVIDENCE-2026-10-05.json](MOLANG-EVALUATION-EVIDENCE-2026-10-05.json)
- [MOLANG-EVALUATOR-RECOVERY-2026-10-05.md](MOLANG-EVALUATOR-RECOVERY-2026-10-05.md)
- [MOLANG-EVALUATOR-EVIDENCE-2026-10-05.json](MOLANG-EVALUATOR-EVIDENCE-2026-10-05.json)
- [CHINESE-COMMUNITY-OBFUSCATION-RECON-2026-10-05.md](CHINESE-COMMUNITY-OBFUSCATION-RECON-2026-10-05.md)
- [SEMANTIC-RECOVERY-2026-10-05.md](SEMANTIC-RECOVERY-2026-10-05.md)
- [SEMANTIC-COVERAGE-2026-10-05.json](SEMANTIC-COVERAGE-2026-10-05.json)
- [SEMANTIC-VERIFICATION-2026-10-05.json](SEMANTIC-VERIFICATION-2026-10-05.json)
- [FAILURE-REPAIR-HISTORY.md](FAILURE-REPAIR-HISTORY.md)
- [RECONNAISSANCE-2026-10-05.md](RECONNAISSANCE-2026-10-05.md)
- [SOURCE-INVENTORY-2026-10-05.json](SOURCE-INVENTORY-2026-10-05.json)

## Research boundary

KNEEKURA does not need to defeat YSM's historical protection mechanisms to recover useful
engineering. The public source/history already exposes the model/animation/controller/integration
architecture. Where 2.6.5 native internals remain opaque, use documented Java/JNI contracts and
bounded runtime observation rather than protection bypass.

- [Bedrock state scheduling and queue-production join](BEDROCK-CONTROLLER-RECOVERY-2026-10-17.md): 36-method static dossier; independent review pending.

- [Animatable frame gates and model lifecycle](ANIMATABLE-FRAME-RECOVERY-2026-10-17.md): 72-method static dossier; independent review pending.

- [Async animation submission and wait boundary](ASYNC-ANIMATION-RECOVERY-2026-10-17.md): 46-method static dossier; independent review pending.

- [Animatable override inventory](ANIMATABLE-OVERRIDE-RECOVERY-2026-10-17.md) and [exact world-render hook annotations](WORLD-RENDER-HOOK-RECOVERY-2026-10-17.md): bounded static closure; runtime injection unverified.

- [Model readiness and rendering-scope gates](MODEL-READINESS-SCOPE-RECOVERY-2026-10-17.md): holder replacement, fallback eligibility and hook predicate; runtime outcomes unverified.

- [Texture-holder readiness and lifetime](TEXTURE-HOLDER-LIFETIME-RECOVERY-2026-10-17.md): Java publication, queued registration and delayed release; GPU behavior unverified.

- [Client tick and humanoid render selection](RENDER-SELECTION-RECOVERY-2026-10-17.md): event cancellation, texture overrides and model/layer ordering; runtime rendering unverified.

- [Java render-cycle and array handoff](JAVA-RENDER-BOUNDARY-RECOVERY-2026-10-17.md): exact native declaration boundary and legacy Java writer; native implementation unresolved.

- [State tracker and position-delta input](STATE-TRACKER-INPUT-RECOVERY-2026-10-17.md): entity/render tick cache lifetimes and interpolated displacement; runtime behavior unverified.

- [Movement-query provenance and units](MOVEMENT-QUERY-RECOVERY-2026-10-17.md): velocity versus sampled displacement, time units and directional-input formulas; wrapper propagation pending.

- [Variable and numeric conversion boundaries](VARIABLE-CONVERSION-RECOVERY-2026-10-17.md): context guards, raw values, NaN/infinity and typed evaluation; not universal sanitation.

- [Variable AST and return cleanup](VARIABLE-AST-RETURN-RECOVERY-2026-10-17.md): target dispatch, raw return propagation and finally boundaries; parser lookup pending.

- [Parser binding and storage indirection](PARSER-BINDING-STORAGE-RECOVERY-2026-10-17.md): namespace capture, aliases, variable addresses and parse-reset boundaries.

- [Runtime storage and call frames](RUNTIME-STORAGE-FRAMES-RECOVERY-2026-10-17.md): public/scoped aliasing, temp frames and deferred cleanup; lifetime callers remain bounded.

- [Storage lifecycle direct callers](STORAGE-CALLERS-RECOVERY-2026-10-17.md): fixed-JAR initialize/push/pop closure; root-temp and public-map limits.

- [Function and loop ordering](FUNCTION-LOOP-ORDER-RECOVERY-2026-10-17.md): lazy argument getters, loop limits, foreach assignment and control cleanup.

- [User-function target cache](USER-FUNCTION-CACHE-RECOVERY-2026-10-17.md): successful/missing lookup retention and parser call-validation join; added after the fixed17-cohort receipt.

- [Parser pool lifetime](PARSER-POOL-LIFETIME-RECOVERY-2026-10-17.md): rent/return reset, per-parser fn binding and dynamic args lookup; native loader lifetime unproven.

- [Struct copy and change tracking](STRUCT-COPY-CHANGE-RECOVERY-2026-10-17.md): aliasing/read-only contracts and mutation-before-notification order; no network guarantees.

- [Pooled names and change codec](POOLED-NAME-CHANGE-CODEC-RECOVERY-2026-10-17.md): process-local IDs, text-name conversion and directional data maps; no network execution.

- [Roaming state merge](ROAMING-STATE-MERGE-RECOVERY-2026-10-17.md): per-model readiness, local/remote replacement, queued deltas and vehicle propagation.

- [Entity-load application](ENTITY-LOAD-APPLICATION-RECOVERY-2026-10-17.md): client deferral, cache/exception boundaries and selected property-application sequence.

- [Player property/query provenance](PLAYER-PROPERTY-QUERY-RECOVERY-2026-10-17.md): presence masks, local/remote sources, axis conversion and explicit JOML dependency comparison.

- [Server property producer](SERVER-PROPERTY-PRODUCER-RECOVERY-2026-10-17.md): delta caches, coalescing, rate gate and full-builder distinction.
- [Server full synchronization](SERVER-FULL-SYNC-RECOVERY-2026-10-17.md): END-tick dirty branching, model-ready builder, queued consumers and client application order.

- [Property/reset lifecycle join](PROPERTY-RESET-LIFECYCLE-RECOVERY-2026-10-17.md): inherited geometry resets, full-state ordering and a bounded scalar-write inventory; runtime concerns remain conditional.

- [Full-state and dirty-mark callers](FULL-SYNC-CALLERS-RECOVERY-2026-10-17.md): all fixed-JAR direct call sites and shared lambda fallback handles; no universal runtime closure.

- [Equipment and effect queries](EQUIPMENT-EFFECT-QUERY-RECOVERY-2026-10-17.md): slot/provider precedence, short-circuit tags, durability, actual enchantment argument index and remote/live effect sources.

- [Resource arguments and equipment adapters](RESOURCE-ARGUMENT-ADAPTER-RECOVERY-2026-10-17.md): literal-ID caching, typed strings and optional-mod present-empty/fallback boundaries.

- [World/position/camera queries](WORLD-QUERY-INPUT-RECOVERY-2026-10-17.md): offset evaluation/range/rounding, tag short-circuiting, interpolated position and camera orientation convention.

- [Time/controller queries](TIME-CONTROLLER-QUERY-RECOVERY-2026-10-17.md): clock units and boxing, nullable context defaults, and distinct coded/Bedrock all-versus-any completion producers.

- [Child context and arrow evaluation](CHILD-CONTEXT-ARROW-RECOVERY-2026-10-17.md): selective field copying, null projectile-owner wrappers, shared storage and evaluator return-state transfer.

- [Foreign/public binding reachability](FOREIGN-BINDING-RECOVERY-2026-10-17.md): existing implementation versus bounded absence of outside-pair class references.
- [Actual selected Vineflower comparison](VINEFLOWER-COMPARISON-2026-10-17.md): eight unchanged class inputs, four derived Java outputs, four corroborated branches; no target runtime or source-equivalence claim.

- [Typed query variable guards](TYPED-QUERY-GUARDS-RECOVERY-2026-10-17.md): 17 exact type predicates, raw callback results, invalid-variable/function distinction and child-entity guard limits.

- [Query-name implementation lookup](QUERY-REGISTRATION-RECOVERY-2026-10-17.md): 171 base constructor registrations with compact JSONL lookup; conditional Curios extensions remain explicitly separate.

- [Curios query extension](CURIOS-QUERY-EXTENSION-RECOVERY-2026-10-17.md): four real/placeholder names, per-thread argument caches, render toggles and cosmetic-over-raw selection.

- [Projectile/fishing/client hit inputs](PROJECTILE-HIT-INPUT-RECOVERY-2026-10-17.md): default versus cached item IDs, global client hit source, and exact mixin annotation/refmap boundaries.

- [Living/environment inputs](LIVING-ENVIRONMENT-INPUTS-RECOVERY-2026-10-17.md): 57 named callback roots plus ladder evaluator; actual weather/pose/shoulder/blink/attribute/angle sources and the deprecated null biome-category helper.

- [View/render/texture inputs](VIEW-TEXTURE-INPUT-RECOVERY-2026-10-17.md): broad versus exclusive/first-person predicates, preview inventory flags, head-offset adapter and model texture-name fallback.

- [Bone parameter queries](BONE-PARAMETER-QUERY-RECOVERY-2026-10-17.md): live read-only vector views, rotation signs/degrees, raw position/scale and explicit tracking request without native output-refresh proof.

- [Stateful smoothing](SMOOTHING-STATE-RECOVERY-2026-10-17.md): shared key/type reuse, first-return versus simulated state, manager clock ordering and exact first/second-order arithmetic boundaries.

- [Particle/sound dispatch](PARTICLE-SOUND-DISPATCH-RECOVERY-2026-10-17.md): emission/fake-player gates, count-zero/absolute-axis particle semantics, synchronous sound configuration before duplicate checks; actual javap corroboration recorded.

- [Input/sync/defer boundaries](INPUT-SYNC-DEFER-RECOVERY-2026-10-17.md): cached in-game input, local/remote sync and task enqueue, deferred value capture with a nonselecting name parameter; no actual input or traffic tested.

- [Utility/noise/diagnostic queries](UTILITY-NOISE-DEBUG-RECOVERY-2026-10-17.md): native-noise call boundary, local mod metadata, block-name comparisons and debug-first lazy argument gates.
- [Control priority and action queries](CONTROL-PRIORITY-ACTIONS-RECOVERY-2026-10-17.md): cached first-match main-animation selection, typed guards and coded-controller action entry points.

- [Control equipment/riding predicates](CONTROL-EQUIPMENT-PREDICATES-RECOVERY-2026-10-17.md): raw-slot provenance, actual hand-independent action gates, prefix matching and classifier precedence.

- [Optional maid query adapter](MAID-QUERY-ADAPTER-RECOVERY-2026-10-17.md): cached availability, sixteen real/fallback names and wrong-entity/default-type distinctions.

- [Client compatibility initialization](CLIENT-COMPAT-INITIALIZATION-RECOVERY-2026-10-17.md): declared event registration, 24-adapter-before-native ordering and separate parser/hint lazy lifetimes.

- [Hybrid controller / ParCool join](HYBRID-PARCOOL-CONTROLLER-RECOVERY-2026-10-17.md): Bedrock/builtin coded handoff, active-queue selection and external animator-name versus model-clip distinction.

- [Player controller discovery/assembly](PLAYER-CONTROLLER-ASSEMBLY-RECOVERY-2026-10-17.md): two-stage factories, ordered expansion, resource/event/clip precedence and preview/armor-slot boundaries.

- [Coded player-main selection](PLAYER-MAIN-SELECTION-RECOVERY-2026-10-17.md): state registration, mod-adapter precedence, loop overrides and differences from cached ctrl movement queries.

- [Humanoid hand predicates](HUMANOID-HAND-PREDICATES-RECOVERY-2026-10-17.md): hold pause gates, item-reference tracking, swing/use state distinctions and version-aware loop selection.

- [Conditional names and model ingestion](CONDITIONAL-ANIMATION-NAMES-RECOVERY-2026-10-17.md): merged/default animation-key registration through a lambda handle, tag precedence and cosmetic-aware armor conditions.

- [Riding/passenger/armor predicates](RIDING-ARMOR-PREDICATES-RECOVERY-2026-10-17.md): adapter/legacy fallback order, first-passenger scope and chair-model-ID versus entity-type matching.

- [First-person arm assembly](FIRST-PERSON-ARM-ASSEMBLY-RECOVERY-2026-10-17.md): separate animation/condition maps, shared holder/roaming inputs and eight isolated JDK regex contract cases.

- [Vehicle/projectile controllers](VEHICLE-PROJECTILE-CONTROLLERS-RECOVERY-2026-10-17.md): factory discovery, fly/air literal mismatch, retained root-rotation queue and external aircraft rotation inputs.

- [Extra/preview controllers](EXTRA-PREVIEW-CONTROLLERS-RECOVERY-2026-10-17.md): cap lifecycle, hover/focus preview gates, sampled emission flags and distinct sound cleanup scope.

- [Optional gun-animation adapters](GUN-ANIMATION-ADAPTERS-RECOVERY-2026-10-17.md): provider/null fallback order, distinct ID domains, nine ctrl callbacks and wrapper guard differences.

- [Inner gun-animation state](GUN-INNER-ANIMATION-RECOVERY-2026-10-17.md): event-reset coalescing, provider-specific local/synced thresholds and explicit loop/fallback policies.

- [CarryOn/SWEM/Create inputs](CARRY-HORSE-SKYHOOK-RECOVERY-2026-10-17.md): carry-state priority, horse gait/jump naming, skyhook membership and accessor transformation boundary.

- [Music/BetterCombat inputs](MUSIC-COMBAT-QUERY-INPUTS-RECOVERY-2026-10-17.md): retained music cache, reflected-field readiness and attack-start to swing synchronization boundary.

- [Backpack/spell/blade inputs](BACKPACK-SPELL-BLADE-INPUTS-RECOVERY-2026-10-17.md): rendered backpack precedence, query-versus-playback reset and version-specific combo naming; legacy memory access remains unexecuted.

- [Additional ctrl/tlm/math lookup](EXTRA-BINDING-CATALOG-RECOVERY-2026-10-17.md): 149 static registration sites for109 names, preserving optional real/fallback branches; integrated with the opt-in locator.

- [Locator hierarchy/matrix preparation](LOCATOR-MATRIX-PREPARATION-RECOVERY-2026-10-17.md): supplied hierarchy ownership, ancestor/leaf transform distinction, scale-flag consumption and18 direct caller sites.

- [Attachment render layers](ATTACHMENT-RENDER-LAYERS-RECOVERY-2026-10-17.md): ordinary/special hand paths, extra locators, head/elytra/parrot/backpack transforms and cleanup boundaries.

- [Passenger positioning and optional hat selection](PASSENGER-HAT-ATTACHMENT-RECOVERY-2026-10-17.md): capability/list-index gates, local pose transforms and provider selection.

- [Player render entry and event ordering](PLAYER-RENDER-ENTRY-RECOVERY-2026-10-17.md): default layers, cancellation and separate texture reads.

- [First-person render and registry](FIRST-PERSON-RENDER-REGISTRY-RECOVERY-2026-10-17.md): cached entity, arm-mode arguments, reload and optional layer timing.

- [Arm replacement event gates](ARM-REPLACEMENT-EVENTS-RECOVERY-2026-10-17.md): ordinary versus SWarfare cancellation timing and pose scope.

- [Attachment/render navigation and bounded batch](ATTACHMENT-RENDER-INDEX-2026-10-17.md): seven connected dossiers plus shared-adapter overlap checks.

- [Vehicle/projectile render entry](VEHICLE-PROJECTILE-RENDER-RECOVERY-2026-10-17.md): outer invisibility gate, OR/AND pass distinction, transforms and culling boundary.

- [Dispatcher replacement routing](DISPATCHER-RENDER-REPLACEMENT-RECOVERY-2026-10-17.md): conditional original-call suppression, direct overloads, yaw adapters and fishing-hook mutation.

- [Fishing-line geometry](FISHING-LINE-GEOMETRY-RECOVERY-2026-10-17.md): endpoint camera conventions, 17-point curve, terminal tangent and Iris tail; reuses existing evidence.

- [Player replacement view gates](PLAYER-REPLACEMENT-VIEW-GATES-RECOVERY-2026-10-17.md): self/other config, first-person interoperability and pre-render cancellation.

- [Shader and buffer adapters](SHADER-BUFFER-ADAPTERS-RECOVERY-2026-10-17.md): Oculus/PBR initialization, signed ID packing and fixed-buffer flush scope.

- [GUI preview state](GUI-PREVIEW-STATE-RECOVERY-2026-10-17.md): restoration order, fake-player caller boundary and a selected Vineflower comparison.

- [Client session and skin events](CLIENT-SESSION-SKIN-EVENTS-RECOVERY-2026-10-17.md): login notice lifetime, respawn copy bridge and concrete texture-override writer.

- [Client model synchronization state](CLIENT-MODEL-SYNC-STATE-RECOVERY-2026-10-17.md): listener lifetime, terminal counter reset, queue publication and native abort boundary.

- [Sync state UI consumers](SYNC-STATE-UI-CONSUMERS-RECOVERY-2026-10-17.md): polled counters, queue-based loading measure and limits of terminal callback interpretation.

- [Sound instance lifetime](SOUND-INSTANCE-LIFETIME-RECOVERY-2026-10-17.md): actor tracking, deferred stream completion, looping EOF and close ownership.

- [Sound data and PCM cache](SOUND-DATA-PCM-CACHE-RECOVERY-2026-10-17.md): buffer sharing, marker lookup semantics, segment read size and resource lifetime.

- [Audio decoder Java boundary](AUDIO-DECODER-JAVA-BOUNDARY-RECOVERY-2026-10-17.md): stream EOF/close, zero-position slices, decoder pooling and explicit native declarations.

- [Sound keyframe cleanup](SOUND-KEYFRAME-CLEANUP-RECOVERY-2026-10-17.md): consumed-versus-emitted cursor and exact transition/reset/trim caller inventory.

- [Ordered segments and blend transition](ORDERED-SEGMENT-TRANSITION-RECOVERY-2026-10-17.md): cursor-dependent endpoints, lazy ordering checks, shared segments and exact callers.

- [Instruction and debug evaluation](INSTRUCTION-DEBUG-EVALUATION-RECOVERY-2026-10-17.md): cursor commit order, emission flags and non-read-only debug expression execution.

- [Molang event wrappers](MOLANG-EVENT-WRAPPER-RECOVERY-2026-10-17.md): retained handler/argument lists, init flag timing and actual update/sync callers.

- [Animation data ownership](ANIMATION-DATA-OWNERSHIP-RECOVERY-2026-10-17.md): mixed copy/view policies, controller validation boundaries and particle-field reader inventory.

- [Model asset helper ownership](MODEL-ASSET-HELPERS-RECOVERY-2026-10-17.md) and [client-model composition](CLIENT-MODEL-COMPOSITION-RECOVERY-2026-10-17.md): reuse existing builder evidence; keep fallback, shared references and event registration distinct.

- [Authored geometry defaults](GEOMETRY-AUTHORED-DEFAULTS-RECOVERY-2026-10-17.md): distinguish input carriers, mutable state, relative snapshots and unobserved native readers.

- [TLM live location adapter](TLM-LOCATION-ADAPTER-RECOVERY-2026-10-17.md): cached live wrappers, per-call lists, authored pivots and backpack-to-elytra fallback.

- [Typed function guards](TYPED-FUNCTION-GUARDS-RECOVERY-2026-10-17.md) and [debug message delivery](DEBUG-MESSAGE-DELIVERY-RECOVERY-2026-10-17.md): context rejection, live receiver lookup and formatting boundaries.

- [Lexer tokens and diagnostics](LEXER-TOKEN-DIAGNOSTICS-RECOVERY-2026-10-17.md): previous-token numeric branches, cursor clone offsets, locale and reader boundaries.

- [Parser numeric rejection and reader ownership](PARSER-ENTRY-OWNERSHIP-RECOVERY-2026-10-17.md): token classification vs numeric conversion, error-state commitment and caller-owned vs convenience-owned readers.

- [Model input carriers](MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17.md) and [model-local translation fallback](MODEL-LANGUAGE-FALLBACK-RECOVERY-2026-10-17.md): retained references and per-language-map selection.

- [NativeTexture Java boundary](NATIVE-TEXTURE-JAVA-BOUNDARY-RECOVERY-2026-10-17.md): render-call scheduling, shallow PBR ownership and distinct cleanup layers; native methods remain declarations only.

- [Optional one-file method evidence viewer](MEMBER-EVIDENCE-VIEWER-2026-10-17.md): compact signatures first, exact full member on demand, no automatic audits or tool probes.

- [Maid entity control](MAID-ENTITY-CONTROL-RECOVERY-2026-10-17.md) and [controller/renderer registration](MAID-CONTROLLER-REGISTRATION-RECOVERY-2026-10-17.md): remote-struct no-op overrides,13 priority states,22 discovery sites and deferred renderer creation.

- [Maid rendering/capability consumers](MAID-RENDER-CAPABILITY-RECOVERY-2026-10-17.md): fallback retrieval differs from rendering, layer/offset contracts, empty roaming callback and absent remote-event handler.

- [First-person background and movement stop](CLIENT-VIEW-MOVEMENT-RECOVERY-2026-10-17.md): early render latch, shared initial-state mode3 submission and input-driven local-stop-before-send ordering.

- [Extra-animation key routing](EXTRA-ANIMATION-KEY-ROUTING-RECOVERY-2026-10-17.md): explicit registration delegation, eight shortcuts, category routing and different UI/movement/network guards.

- [Connected Java reuse batch review](JAVA-REUSE-BATCH-REVIEW-2026-10-17.md):35 fixed cohorts, explicit cross-dossier consistency and task-scoped routing; no semantic-completion percentage.

- [Common-side maid/model copy](MAID-COMMON-MODEL-COPY-RECOVERY-2026-10-17.md): separate install gate, empty roaming-map transfers, bounded vehicle reachability and exact creative-copy NBT mutation.

- [Animation packet routing](ANIMATION-PACKET-ROUTING-RECOVERY-2026-10-17.md): explicit direction/sender/target paths, guarded transport helper and separation of routing, authorization and completion.

- [Molang command and separate relay producers](MOLANG-COMMAND-PRODUCER-RECOVERY-2026-10-17.md), with [declared-target validation](DECLARED-TARGET-INVENTORY-2026-10-17.md) before relying on exact-symbol zero-call results.

- [Roulette expression forms](ROULETTE-EXPRESSION-UI-RECOVERY-2026-10-17.md): three GUI emitters, local queue before optional relay, distinct parse-exception ownership, display versus sent slider values, and eight JDK-only lexical predicate examples.

- [Expression versus state transport](EXPRESSION-STATE-TRANSPORT-INDEX-2026-10-17.md): optional end-to-end route guide; local queue, dirty state, drain-before-channel-check and remote application are distinct boundaries.

- [Roulette form ownership and selection](ROULETTE-FORM-OWNERSHIP-RECOVERY-2026-10-17.md): shared arrays/maps, subclass-based form dispatch, model-wide navigation cache, and remote/local animation target distinctions.

- [Configured button sound reachability](ROULETTE-SOUND-CONSUMERS-2026-10-17.md): stored sound field versus fixed UI click requests; exact getter/field inventory does not prove global runtime non-use.
- [User-function comment filtering](USER-FUNCTION-COMMENT-FILTER-2026-10-17.md): optional preprocessing, quote rules, CRLF handling and removed-block token adjacency; reuses existing parser evidence.

- [Client model containers](CLIENT-MODEL-CONTAINERS-RECOVERY-2026-10-17.md): shared data, constructor-time factory assembly, separate default texture inputs and nullable GUI image lookups.

- [Packed color and renderer channels](COLOR-CHANNEL-CONTRACT-RECOVERY-2026-10-17.md): ARGB masks, float conversion, default WHITE and actual getter consumers; Java preparation is separate from GPU output.

- [Inherited symbolic-owner candidates](INHERITED-CALL-CANDIDATES-2026-10-17.md): optional follow-up to exact caller scans; nominal ancestry candidates remain separate from proven JVM dispatch.
- [Humanoid texture registration](HUMANOID-TEXTURE-REGISTRATION-2026-10-17.md): selected readiness versus pre-registration, retained holders and first-live identity-cache delay.

- [Connected transport/render review](TRANSPORT-RENDER-BATCH-REVIEW-2026-10-17.md): later fixed27-cohort integrity batch, selected Vineflower comparison and explicit remaining evidence limits.

- Before recapturing a class after an owner-name miss, use the [optional locator source-path search](EVIDENCE-LOCATOR-2026-10-17.md). It finds existing source-track cohorts without guessing a class mapping or treating file presence as full semantic coverage.

## Projectile and vehicle capability transport extension

[Projectile owner-state transport](PROJECTILE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) and [vehicle transfer](VEHICLE-CAPABILITY-TRANSPORT-RECOVERY-2026-10-17.md) close the next Java-side branch: retained server maps, deferred versus optional-only producers, NBT/string-pool wire conversion, explicit lazy initialization and later processor installation. A queued callback is not a frozen launch snapshot; wrapper capability presence is not rendering readiness. The fixed8 [checkpoint](ENTITY-CAPABILITY-TRANSPORT-CHECKPOINT-2026-10-17.json) joins these two cohorts with six existing anchors, without changing older manifests or promoting the central map.
