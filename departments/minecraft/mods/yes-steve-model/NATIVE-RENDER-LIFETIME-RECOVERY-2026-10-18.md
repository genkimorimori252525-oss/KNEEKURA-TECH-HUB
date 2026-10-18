# Native renderer and model lifetime: exact static contract

Original Linux x86-64 image SHA256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; original JAR SHA256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. The recovered binding receipt joins renderer entry `0x3bf750` and GeoModel release `0x3c1160` to exact original native declarations. This analysis reads original file-backed machine bytes, not a simulated memory snapshot. No target execution, JVM, Unicorn, installers, or host worker threads. Independent semantic review NOT_RUN.

## Reusable contracts established

1. **Model lifetime is handle-registry based.** Renderer reads the model Java long with JNI GetLongField (table offset0x328), then searches the registry whose buckets are at0xd341b8, bucket count0xd341c0, sentinel/list0xd341c8, count0xd341d0, lock0xd341f8. Nodes contain next+0, key+8, model pointer+16, ownership control pointer+24. Renderer retains the control count before releasing the registry lock and releases it on exit. Release receives its Java long in RDX, searches the same registry, unlinks a found node, releases its owned model, frees a32-byte node, decrements registry count. Missing release keys take the no-erase return path. Renderer lookup itself lacks the same null checks in its search loop; do not promise stale/invalid handles are safe.
2. **Original arrays cross a copying JNI seam.** The wrapper forwards Java input/output objects to helper0x37bd80. That helper uses GetFloatArrayRegion at0x37bf48, not GetDirectBufferAddress or pinned float-array access. Mode0 selects [0,boneCount); input start is12*startBone, length12*(endBone-startBone), native destination offset48*startBone. Native bone descriptors have stride120 bytes. Input scratch stride48 bytes matches the previously established12-float Java contract.
3. **Output refresh is conditional.** Output scratch stride16 bytes matches4 floats/bone. At0x37eb01 SetFloatArrayRegion copies start4*startBone, length4*(endBone-startBone), only when output is nonnull and an accumulated tracking-work bit is set. Merely calling render does not establish refreshed absolute-pivot output. The copy covers the selected region, not only individually tracked bones; freshness of untracked entries in that region is not established.
4. **Tracking predicate is broader than Java getter truth.** Native slot11 is compared to0; unequal OR unordered enters the tracking-transform path. Thus ordinary1 enables it, but2, negative values and NaN also enter. Java getter exact1 semantics must not be substituted for this native predicate. +0 and -0 skip it.
5. **Located output writer stores XYZ, not an established fourth value.** The tracking path combines a transformed translation with four matrix lanes, scales X by-16, Y by+16, Z by+16, then writes output byte offsets0,4,8. Slot3 is not written by this located writer. The fourth slot remains unresolved; do not label it homogeneous W or guarantee preservation/zero. Native position inputs in the same tracking path scale X by-1/16 and Y,Z by+1/16. Full coordinate-frame/matrix equivalence is not claimed.
6. **Bounded mode and texture gates exist.** Negative texture, empty model and texture outside the first descriptor's40-byte-stride texture table return false. Nonzero modes outside1..3 return false. Modes1..3 query model+0x18 with mode-1, obtain startBone from result+0xc, and end=start+descriptor[start].u32(+0x6c)+1. Interpreting this as a selected subtree is supported by contiguous descendant skipping using the same+0x6c, but the semantic names of the three selectors remain unresolved.

## Entry ABI and argument mapping

Linux SysV JNI entry includes JNIEnv in RDI and jclass in RSI. The body obtains its working JNI context through TLS rather than retaining incoming RDI. Java arguments map as follows after the prologue (RSP moved down0x148 from entry):

- RDX: VertexConsumer; RCX: PoseStack.Pose; R8: Matrix4f; R9: forceLegacy boolean
- [RSP+0x150]: GeoModel; +0x158 input float[]; +0x160 output float[]
- +0x168 texture index; +0x170 mode; +0x178,+0x180 packed lighting/overlay in wrapper order
- XMM0..3 RGBA; [RSP+0x188] renderOnGui

Native entry explicitly skips work for null VertexConsumer, Pose, Matrix4f, GeoModel or input float[]. Output float[] is optional at the copy-back seam. It checks resolved model pointer and nonempty model vector. Java array lengths are not queried before this helper's region operation; this is not proof that short arrays are safe or exception-clean.

Renderer builds a stack settings record with the two packed ints, RGBA, a fetched static boolean, GUI flag, texture index, and16 Matrix4f values read through GetFloatField. The field-ID catalog order is retained in disassembly; exact names of native catalog entries are not promoted here.

## Draw dispatch and important callees

- `0x37bd80`: prepare bone transforms/geometry and optional output-array update. Draw dispatch requires its true return and nonzero global total count0xd34c30.
- `0x398e50`: backend selector, receiving forceLegacy. Its returned codes1..6 drive jump tables at0x585f8 and0x58610. Backend identity remains unresolved.
- For both tables codes2..6 go to direct wrappers `0x384740`, `0x384430`, `0x383e10`, `0x384120`, `0x384a50`. Code1 follows raw-buffer handling through0x398760; mode changes its callback between0x381f30 and0x37fae0.
- GUI plus model byte+0x54 diverts to0x385080 (mode0) or0x385390 (nonzero mode), still passing forceLegacy.
- Raw36-byte vertex path requests36*totalCount bytes; sorting/copying moves144-byte four-vertex groups, with8-byte sort entries. The inspected0x383e10 wrapper instead uses54-byte vertices and216-byte four-vertex groups. These layouts cannot be conflated with Java legacy writer's12-float +2-int arrays without tracing its actual producing callback.
- Work dispatch stores callback/context at worker-state+0x20, atomically adds pending count at+0xc0, increments generation+0x40, then spins until pending zero before clearing callback. This proves a worker-oriented architecture, not successful runtime concurrency, and suggests why inventing a zero-worker simulation would be unsound.
- `0x41a560`: JNI exception-check/translation helper (ExceptionCheck0x720; pending-exception handling includes ExceptionClear0x88).
- `0x329bd0`: slow shared-ownership release helper. `0xd14790`/`0xd147b0` bracket registry access conditionally; lock/unlock identification is structural pending import-label verification.

## Evidence and reproduction

[Evidence receipt](NATIVE-RENDER-LIFETIME-EVIDENCE-2026-10-18.json) includes17 source-backed claim anchors, exact bytes, hashes, ELF backing records, constants and jump tables, plus the exact two declaration bindings. Seven raw binary/disassembly windows are retained outside Git alongside ranges.json. `build_receipt.py` verifies both original artifact hashes and every window's source bytes, then writes the receipt. Last run: SOURCE_BYTES_VERIFIED,17 anchors,7 windows. This is source-byte consistency verification, not dynamic correctness testing. Windows marked `window_not_proven_function_boundary` may include trailing code or end before a function ends.

Read first: Java render-boundary and bone-state recovery dossiers in the project. Those establish Java wrapper ordering and12/4 allocation contract independently of these native findings. Remaining work: exact backend enum/callback identities, full transform equivalence and parent propagation, output fourth-slot provenance, exception-path behavior, concurrency safety and actual visual correctness.
