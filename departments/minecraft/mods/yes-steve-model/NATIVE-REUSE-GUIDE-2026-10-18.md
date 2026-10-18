# Native reuse guide — read only the seam you need

Scope: exact YSM2.6.5 Forge1.20.1 release, original Linux x86-64 library. [Exact identities and seventeen original-JAR entry mappings](NATIVE-EXACT-BINDINGS-RECOVERY-2026-10-18.md). This guide joins evidence; it does not promote the Java map or certify whole-runtime behavior. No automatic audit, dependency installation or whole-repository scan is needed.

[Machine-readable entry routing](NATIVE-ENTRY-CONTRACT-INDEX-2026-10-18.json) links all17 original-YSM declarations to bounded entry contracts, plus the5 separately discovered LWJGL wrappers. These coverage counts do not mean all transitive implementations or runtime behavior are recovered.

## Choose the smallest entry point

| Question | Evidence to open |
|---|---|
| Which native function implements this Java declaration? | [Original-YSM bindings](NATIVE-EXACT-BINDINGS-2026-10-18.json) and [client LWJGL bindings](NATIVE-CLIENT-LWJGL-BINDINGS-2026-10-18.json); use owner+name+descriptor, never declaration order |
| What do export/reload completion signals mean? | [Export/reload](NATIVE-SERVER-EXPORT-RELOAD-RECOVERY-2026-10-18.md); submission, native callback, Java commit and later publication differ |
| How does texture source storage relate to GL deletion? | [Texture lifetime](NATIVE-TEXTURE-LIFETIME-RECOVERY-2026-10-18.md); native long, CPU source data and GL names are separate |
| How is texture source storage transformed and restored? | [XOR stream](NATIVE-TEXTURE-XOR-RECOVERY-2026-10-18.md), then [exact MT19937-64 comparison](NATIVE-MT19937-64-COMPARISON-2026-10-18.md); normal-path restoration is conditional |
| How does the shared payload decoder frame data? | [Framing](NATIVE-PAYLOAD-FRAMING-RECOVERY-2026-10-18.md), [lazy dispatch](NATIVE-DECODER-DISPATCH-RECOVERY-2026-10-18.md), [CPU resolver](NATIVE-DECODER-RESOLVER-RECOVERY-2026-10-18.md), [generic transform](NATIVE-DECODER-GENERIC-RECOVERY-2026-10-18.md); generic HChaCha-form caller requests 30 rounds, not HChaCha20 |
| How do server requests retain recipients and incoming buffers? | [Server transport](NATIVE-SERVER-TRANSPORT-RECOVERY-2026-10-18.md); pending requests, receive tasks and client queues are distinct |
| How does received model data become geometry? | [Receive](NATIVE-CLIENT-RECEIVE-RECOVERY-2026-10-18.md), then [geometry construction](NATIVE-GEOMETRY-BUILD-RECOVERY-2026-10-18.md) |
| How are native bone indices and depths produced? | [Hierarchy/order/capacity](NATIVE-BONE-HIERARCHY-RECOVERY-2026-10-18.md) |
| What transform should a bone apply? | [Affine/parent contract](NATIVE-BONE-AFFINE-RECOVERY-2026-10-18.md), then [normal arithmetic](NATIVE-NORMAL-MATRIX-RECOVERY-2026-10-18.md) only if needed |
| When are output pivots current? | [Output/modes](NATIVE-RENDER-OUTPUT-MODES-RECOVERY-2026-10-18.md) |
| How do native vertices reach Java? | [Backend/legacy writer](NATIVE-RENDER-BACKENDS-RECOVERY-2026-10-18.md) |
| What shared graphics methods can client setup register? | [Five LWJGL wrappers](NATIVE-LWJGL-WRAPPERS-RECOVERY-2026-10-18.md); static forwarding/skip rules, not installed-runtime proof |
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

## Evidence boundaries

- The seventeen-entry receipt covers the discovered JNI_OnLoad table matching original-YSM declarations; it is not an inventory of every registration site or third-party native declaration. [Client startup](NATIVE-CLIENT-STARTUP-RECOVERY-2026-10-18.md) has a separate five-descriptor LWJGL registration site, now exactly matched to the declared3.3.1 dependency. The [direct-call inventory](NATIVE-REGISTRATION-DIRECT-CALLS-2026-10-18.json) covers original-file E8 calls only, not every possible registration mechanism.
- Exact binding/constructor identities combine original instruction stores, separately guarded metadata callback decoding and exact original-JAR declarations where available.
- Native body contracts are bounded original-byte analysis. Each dossier records anchors and unresolved cases. Authored numerical fixtures check their stated mathematics only.
- Actual RegisterNatives success, complete JNI_OnLoad, host JVM execution, real worker scheduling, full model validation and visual correctness remain unproven.
- Read historical receipts as historical. Keep original binary inputs and raw traces outside Git. No inference from a successful metadata decode should silently become a runtime guarantee.

## Focused review status

A separate [original-byte review](NATIVE-BONE-FOCUSED-REVIEW-2026-10-18.json) checked affine/pivot composition, stale selected-range output, qualified depth-bank capacity, and negative-normal fallthrough. It found no contradiction within the documented bounds;64 listed ranges/anchors matched original bytes. This review does not approve the whole renderer/project or establish runtime equivalence, complete alias analysis, or malformed-input safety.

A second [focused original-byte review](NATIVE-SHUTDOWN-GL-FOCUSED-REVIEW-2026-10-18.json) checked the shutdown helper's gates/imports and all five LWJGL wrapper pairings/argument paths. It found no contradiction within the scoped claims. It did not run signals, GL operations or registration, and it is not whole-project approval.
