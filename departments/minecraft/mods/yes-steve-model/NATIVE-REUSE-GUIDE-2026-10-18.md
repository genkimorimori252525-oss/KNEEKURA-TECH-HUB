# Native reuse guide — read only the seam you need

Scope: exact YSM2.6.5 Forge1.20.1 release, original Linux x86-64 library. [Exact identities and seventeen original-JAR entry mappings](NATIVE-EXACT-BINDINGS-RECOVERY-2026-10-18.md). This guide joins evidence; it does not promote the Java map or certify whole-runtime behavior. No automatic audit, dependency installation or whole-repository scan is needed.

[Machine-readable entry routing](NATIVE-ENTRY-CONTRACT-INDEX-2026-10-18.json) links all17 original-YSM declarations to bounded entry contracts, plus the5 separately discovered LWJGL wrappers. These coverage counts do not mean all transitive implementations or runtime behavior are recovered.

[Exact manager-slot lookup](NATIVE-JAVA-MEMBER-INDEX-2026-10-18.md) covers52 selected Java-member slots with source receipts; it is separate from the17 original native-entry declarations. Query the required manager+offset rather than rereading every metadata cohort.

## Choose the smallest entry point

| Question | Evidence to open |
|---|---|
| Which native function implements this Java declaration? | [Original-YSM bindings](NATIVE-EXACT-BINDINGS-2026-10-18.json) and [client LWJGL bindings](NATIVE-CLIENT-LWJGL-BINDINGS-2026-10-18.json); use owner+name+descriptor, never declaration order |
| What do export/reload completion signals mean? | [Export/reload](NATIVE-SERVER-EXPORT-RELOAD-RECOVERY-2026-10-18.md); submission, native callback, Java commit and later publication differ |
| How does texture source storage relate to GL deletion? | [Texture lifetime](NATIVE-TEXTURE-LIFETIME-RECOVERY-2026-10-18.md); native long, CPU source data and GL names are separate |
| How is texture source storage transformed and restored? | [XOR stream](NATIVE-TEXTURE-XOR-RECOVERY-2026-10-18.md), then [exact MT19937-64 comparison](NATIVE-MT19937-64-COMPARISON-2026-10-18.md) and optional [authored reference checker](NATIVE-MT19937-64-REFERENCE-2026-10-18.md); normal-path restoration is conditional |
| How does the shared payload decoder frame data? | [Framing](NATIVE-PAYLOAD-FRAMING-RECOVERY-2026-10-18.md), [lazy dispatch](NATIVE-DECODER-DISPATCH-RECOVERY-2026-10-18.md), [CPU resolver](NATIVE-DECODER-RESOLVER-RECOVERY-2026-10-18.md), [generic transform](NATIVE-DECODER-GENERIC-RECOVERY-2026-10-18.md), [buffered stream](NATIVE-DECODER-STREAM-RECOVERY-2026-10-18.md), [material provenance](NATIVE-DECODER-MATERIAL-RECOVERY-2026-10-18.md); generic HChaCha-form caller requests 30 rounds, not HChaCha20 |
| How do server requests retain recipients and incoming buffers? | [Server transport](NATIVE-SERVER-TRANSPORT-RECOVERY-2026-10-18.md); pending requests, receive tasks and client queues are distinct |
| How does received model data become geometry? | [Receive](NATIVE-CLIENT-RECEIVE-RECOVERY-2026-10-18.md), [selector3 package](NATIVE-SELECTOR3-SCHEMA-RECOVERY-2026-10-18.md), [file/model acquisition](NATIVE-SOURCE-ACQUISITION-RECOVERY-2026-10-18.md), then [geometry construction](NATIVE-GEOMETRY-BUILD-RECOVERY-2026-10-18.md) |
| Which model/bone bytes populate renderer input? | [Modern root and bone schema](NATIVE-MODERN-MODEL-SCHEMA-RECOVERY-2026-10-18.md), [legacy conversion](NATIVE-LEGACY-MODEL-SCHEMA-RECOVERY-2026-10-18.md), [versions19..26](NATIVE-MODEL-V19-26-RECOVERY-2026-10-18.md), [nested23-scalar records](NATIVE-BONE-PRIMITIVE-SCHEMA-RECOVERY-2026-10-18.md); native struct size is not wire size |
| Which parsed model entries are constructed? | [Collection selection](NATIVE-MODEL-GEOMETRY-SELECTION-RECOVERY-2026-10-18.md) and [native main/arm selector registration](NATIVE-MODEL-SELECTOR-REGISTRATION-RECOVERY-2026-10-18.md); vectors are enumerated, not filtered to one active identifier |
| How are primitive records packed and retained? | [Packing](NATIVE-PRIMITIVE-PACKED-CONSUMER-RECOVERY-2026-10-18.md), [pair math/classification](NATIVE-PRIMITIVE-PAIR-CLASSIFIER-RECOVERY-2026-10-18.md), [nested attachment/ownership](NATIVE-GEOMETRY-PACKED-ATTACHMENT-RECOVERY-2026-10-18.md); finalized batch pointer headers are masked |
| How are masked batch pointers consumed? | [Representative decode and mask source](NATIVE-GEOMETRY-BATCH-UNMASK-RECOVERY-2026-10-18.md), [28 non-GUI sites](NATIVE-GEOMETRY-UNMASK-COVERAGE-RECOVERY-2026-10-18.md), [GUI dispatch and8 more sites](NATIVE-GUI-BYPASS-RECOVERY-2026-10-18.md); header-contract coverage, not complete emission equivalence |
| What does the sampled fourth byte mean? | Start with the [five-provider scope index](NATIVE-PROVIDER-CONTRACT-INDEX-2026-10-18.md). [Provider boundary](NATIVE-PROVIDER-OUTPUT-FORMAT-RECOVERY-2026-10-18.md); [selector2 PNG output](NATIVE-PNG-OUTPUT-CHANNEL-RECOVERY-2026-10-18.md) establishes RGBA8 alpha only for that provider; [selector3 traced callback](NATIVE-SELECTOR3-CALLBACK-RECOVERY-2026-10-18.md) synthesizes255 in the covered paths, while [selector4](NATIVE-SELECTOR4-OUTPUT-RECOVERY-2026-10-18.md) can overwrite from a separate plane |
| How are native bone indices and depths produced? | [Hierarchy/order/capacity](NATIVE-BONE-HIERARCHY-RECOVERY-2026-10-18.md) |
| How do wire keyframes reach Java values and easing? | [Animation element](NATIVE-ANIMATION-ELEMENT-RECOVERY-2026-10-18.md), [raw record](NATIVE-KEYFRAME-ELEMENT-RECOVERY-2026-10-18.md), [six-pair Java bridge](NATIVE-KEYFRAME-JAVA-BRIDGE-2026-10-18.md), [selector provenance](NATIVE-ANIMATION-SELECTOR-PROVENANCE-RECOVERY-2026-10-18.md); native does not apply the Java rotation conversion |
| How do controller states and blends arrive? | [Wire schema](NATIVE-CONTROLLER-WIRE-RECOVERY-2026-10-18.md), [construction](NATIVE-CONTROLLER-CONSTRUCTION-RECOVERY-2026-10-18.md), [Java bridge](NATIVE-CONTROLLER-JAVA-BRIDGE-2026-10-18.md); preserve raw-key versus pooled-key duplicate handling and separate time multipliers |
| Does the fresh animation wire reader populate particles? | [Fresh-path proof](NATIVE-PARTICLE-FRESH-WIRE-RECOVERY-2026-10-18.md); empty vector for that path, not global particle-support absence |
| Which vectors build projectile/vehicle carriers? | [Vector-carrier joins](NATIVE-VECTOR-MODEL-CARRIERS-RECOVERY-2026-10-18.md) and [exact identities](NATIVE-VECTOR-CARRIER-METADATA-2026-10-18.json); optional animation/controller and primary texture stay distinct |
| What transform should a bone apply? | [Affine/parent contract](NATIVE-BONE-AFFINE-RECOVERY-2026-10-18.md), then [normal arithmetic](NATIVE-NORMAL-MATRIX-RECOVERY-2026-10-18.md) only if needed |
| When are output pivots current? | [Output/modes](NATIVE-RENDER-OUTPUT-MODES-RECOVERY-2026-10-18.md) |
| How do native vertices reach Java? | [Backend/legacy writer](NATIVE-RENDER-BACKENDS-RECOVERY-2026-10-18.md) |
| What shared graphics methods can client setup register? | [Five LWJGL wrappers](NATIVE-LWJGL-WRAPPERS-RECOVERY-2026-10-18.md); static forwarding/skip rules, not installed-runtime proof |
| Where do animation/controller inputs come from? | [Optional native carriers](NATIVE-OPTIONAL-MODEL-CARRIERS-RECOVERY-2026-10-18.md), [exact Java binding](NATIVE-ANIMATION-CONTROLLER-METADATA-2026-10-18.json), [array/map ownership](NATIVE-ANIMATION-CONTROLLER-JAVA-BRIDGE-2026-10-18.md); distinguish the animation map from its extra selector-ordered array |
| What is serialized in model section0x390? | [Section schema](NATIVE-MODEL-SECTION390-RECOVERY-2026-10-18.md) and [three exact constructor identities](NATIVE-SECTION390-METADATA-2026-10-18.json); one array matches existing ExtraAnimationButton evidence, but not all field semantics are closed |
| How do native resource maps reach Java? | [Three-map section](NATIVE-MODEL-RESOURCE-SECTION-RECOVERY-2026-10-18.md), [exact metadata](NATIVE-RESOURCE-CONSUMER-METADATA-2026-10-18.json), [Java bridge](NATIVE-RESOURCE-JAVA-BRIDGE-2026-10-18.md); SoundData copies bytes on successful construction, while the catching Molang parser can return a fallback |
| How do audio buffers and native handles live? | [Audio contract](NATIVE-AUDIO-CONTRACT-RECOVERY-2026-10-18.md); encoded pointers differ from geometry registry keys |
| What do initialization/shutdown returns establish? | [Common native lifecycle](NATIVE-COMMON-LIFECYCLE-RECOVERY-2026-10-18.md); attempted-init and shutdown-requested are not completion flags |
| How can interrupted guarded analysis resume? | [Current handoff](NATIVE-CURRENT-HANDOFF-2026-10-18.md); do not replace missing runtime state with successful stubs |

## Contracts to preserve

1. **Geometry handles are registry keys.** Do not generalize one native handle representation to unrelated subsystems. Geometry uses registry d341b8 and retained shared ownership; texture uses a different registry d348b0. The shown geometry publication narrows an internal64-bit key to32 bits and then zero-extends into Java long. This is an observed width boundary, not proof of rollover behavior. Preserve exact ownership and cleanup rather than casting Java long to an address.

2. **Scheduling and publication are separate.** Receive retains a ByteBuffer global reference, queues it, and a later consumer obtains direct address/capacity. Retention does not freeze bytes. The builder installs a deferred callable before geometry creation; installation is not execution, success or rendering readiness.

3. **Bone order is shared, but not original input order.** Native records and Java bones use the same flattened vector. Reached rooted components use depth-first preorder, with reverse byte-lexicographic sibling/root order. Duplicate retained names, missing parents, cycles and global validation require the hierarchy dossier; never assume every input node was visited. Native depth stores only the low byte of a32-bit producer value. The maxDepth+1 bank sizing proof requires representable, valid depth relationships.

4. **Input and pivot coordinates differ deliberately.** Per-bone input is12 floats: rotationXYZ,positionXYZ,scaleXYZ,ownHidden,childrenHidden,tracking. Position conversion is(-x,y,z)/16. Native authored pivot p is the common Java-visible pivot source divided by16 on all three axes, with no additional X flip in the shown producer. With column vectors the reached affine path is P·T(positionConverted)·T(p)·Rz·Ry·Rx·S·T(-p). The optional algebra checker verifies the mathematical composition, not native float32/trig bits.

5. **Normals are not certified by generic inverse transpose.** The native path has explicit uniform-scale branches, sign XOR, signed bit seed and two ordered binary32 refinements. Use its exact bounded dossier when numeric compatibility matters. Negative-scale arithmetic-model examples are not observed game defects or guarantees about downstream normalization.

6. **Four output floats do not mean four fresh values.** Located writer updates XYZ only. Slot3 has unresolved meaning. Global scratch is initially cleared but reused without reset; conditional selected-range copy can include stale untracked entries. With no tracking work, this seam does not copy output. Modes1/2/3 select LEFT_ARM/RIGHT_ARM/BACKGROUND; mode0 selects all bones. Native flags accept nonzero or unordered values, not only Java's exact1 convention.

7. **Legacy vertex layout is now connected end-to-end.** Forced code6 uses12 float components per vertex: xyz,RGBA,UV,normalXYZ; plus two ints: overlay,light. The exact original nested Java writer consumes that layout. Code1 instead writes36-byte native vertices. Do not conflate those layouts or infer a backend's identity from byte stride. Optional Minecraft/Sodium field strings were decoded, but their external class declarations were not available for all checks.

8. **Audio reset is not destruction or rewind.** Audio handles encode pointers. The Java wrapper passes buffer slices, and input storage is borrowed; successful init retains the original Java input. Reset clears activity and input address/length; destroy frees native allocations but does not invalidate the Java final handle. Decode returns byte counts, with several zero/error branches. Read the exact lifetime and failure limits before pooling or retrying.

9. **Shutdown is a process-lifecycle operation, not a generic reusable reset.** Common init sets an attempted latch before setup. The first native shutdown sets its gate before cleanup and installs a detached helper that attempts self-SIGKILL after a requested ten-second sleep if the process is still alive. No normal-path timer cancellation was found in the inspected code. Signal/thread behavior was never executed. Repeated shutdown returns, callback registration, flag clearing and queued null-buffer aborts do not prove completion.

10. **Native layout is not serialized layout.** Accepted file versions1..18,19..20,21..26 and27..32 have distinct root representations. Versions19..26 convert string-keyed maps to common entries;27..32 read direct vectors in the opposite collection order. Bone fields reach the same common storage, but retained record strides include vtables/padding: an inner0xc0-byte record reads92 wire bytes. Native double properties are read as float32 then promoted. Read the versioned schema before attempting compatibility; no complete decoder or real model load is certified.

## Evidence boundaries

- The seventeen-entry receipt covers the discovered JNI_OnLoad table matching original-YSM declarations; it is not an inventory of every registration site or third-party native declaration. [Client startup](NATIVE-CLIENT-STARTUP-RECOVERY-2026-10-18.md) has a separate five-descriptor LWJGL registration site, now exactly matched to the declared3.3.1 dependency. The [direct-call inventory](NATIVE-REGISTRATION-DIRECT-CALLS-2026-10-18.json) covers original-file E8 calls only, not every possible registration mechanism.
- Exact binding/constructor identities combine original instruction stores, separately guarded metadata callback decoding and exact original-JAR declarations where available.
- Native body contracts are bounded original-byte analysis. Each dossier records anchors and unresolved cases. Authored numerical fixtures check their stated mathematics only.
- Actual RegisterNatives success, complete JNI_OnLoad, host JVM execution, real worker scheduling, full model validation and visual correctness remain unproven.
- Read historical receipts as historical. Keep original binary inputs and raw traces outside Git. No inference from a successful metadata decode should silently become a runtime guarantee.

## Focused review status

A separate [original-byte review](NATIVE-BONE-FOCUSED-REVIEW-2026-10-18.json) checked affine/pivot composition, stale selected-range output, qualified depth-bank capacity, and negative-normal fallthrough. It found no contradiction within the documented bounds;64 listed ranges/anchors matched original bytes. This review does not approve the whole renderer/project or establish runtime equivalence, complete alias analysis, or malformed-input safety.

A second [focused original-byte review](NATIVE-SHUTDOWN-GL-FOCUSED-REVIEW-2026-10-18.json) checked the shutdown helper's gates/imports and all five LWJGL wrapper pairings/argument paths. It found no contradiction within the scoped claims. It did not run signals, GL operations or registration, and it is not whole-project approval.

A third [focused original-byte review](NATIVE-GENERIC-TRANSFORM-FOCUSED-REVIEW-2026-10-18.json) checked the generic derivation/block transforms, fixed round-count propagation, state layout and counter/tail writes. No contradiction was found within those claims; actual backend selection and whole-project correctness remain unproven.

A fourth [focused review](NATIVE-KEYFRAME-JOIN-FOCUSED-REVIEW-2026-10-18.md) independently checked the six component pairs, low-byte rotation flag, timestamp narrowing, contiguous reference alias and AllocObject distinction.120 mechanical checks passed with one corrected interface/enum terminology issue. Metadata payload decoding was inherited, not repeated; this is not whole-project/runtime approval.

## Explicit virtual Forge path frontier

[Reviewed Path model and bounded continuation](NATIVE-FORGE-PATH-CONTINUATION-2026-10-18.md) documents the synthetic config path, 71 scoped tests, independent review and strict next secure_getenv("TMPDIR") stop. This does not prove real Forge setup or filesystem success.

The [next explicit absent-environment cohort](NATIVE-ABSENT-ENVIRONMENT-CONTINUATION-2026-10-18.md) reaches the mandatory `/tmp` status query. Environment selection and filesystem status remain separate contracts.

## Native initialization I/O and archive boundary

Use [owned config/temp paths](NATIVE-INIT-PATH-CONSUMERS-2026-10-18.md), [builtin cleanup/notice output](NATIVE-BUILTIN-CLEANUP-NOTICE-2026-10-18.md), [ModList-to-archive graph](NATIVE-MODLIST-MAP-CONTRACT-2026-10-18.md), then [archive integrity/resource consumers](NATIVE-ARCHIVE-PATH-CONSUMER-2026-10-18.md). These static contracts distinguish destructive cleanup, metadata identity, actual filesystem state, filtered integrity and resource writes; none is a blanket successful initialization fixture.

[Blacklist line filtering and destination selection](NATIVE-BUILTIN-SELECTION-2026-10-18.md) distinguishes untrimmed patterns, CR→LF processing, exact prefix gating and lexical suffix normalization. [Regex semantics](NATIVE-BLACKLIST-REGEX-2026-10-18.md) proves full-range matching and native-supported option mapping. Path containment remains unproved, not demonstrated unsafe or safe.

[Manifest numeric formatting](NATIVE-HASH-MANIFEST-FORMAT-2026-10-18.md) and [first-wins duplicate-name collection](NATIVE-ARCHIVE-DUPLICATE-NAMES-2026-10-18.md) complete the bounded ordered-serialization contract. Runtime locale, parser-wide duplicate acceptance, actual records and successful aggregate equality remain unknown.

## Model configuration → renderer/Molang inputs

[Main geometry flags](NATIVE-MAIN-GEOMETRY-FLAGS-2026-10-18.md) gives exact byte flow and a bounded truth table for build routing versus renderer bypass. [ConfigForms→Java](NATIVE-CONFIGFORMS-JAVA-JOIN-2026-10-18.md) joins model field order and native default selection to original Checkbox/Range/Radio constructors, completing the seam into existing Java form/expression/UI research. [Selected member index](NATIVE-JAVA-MEMBER-INDEX-2026-10-18.md) now contains52 slots; no central-map promotion.
