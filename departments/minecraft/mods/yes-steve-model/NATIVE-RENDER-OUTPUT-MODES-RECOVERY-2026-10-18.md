# Renderer continuation: output persistence and mode identities

Continuation of [renderer/lifetime recovery](NATIVE-RENDER-LIFETIME-RECOVERY-2026-10-18.md); earlier evidence remains unchanged. Exact original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22 and JAR SHA25625b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f. Static inspection only, no target/JVM/emulator execution. Independent semantic review NOT_RUN.

## Three selectors are now named

- Mode1: LEFT_ARM, native integer key0.
- Mode2: RIGHT_ARM, native integer key1.
- Mode3: BACKGROUND, native integer key2.
- Mode0: all bones, does not take the selector lookup.

This is grounded in original Java callers, not native string guesses. Exact original class `o0oo00OoO00OO0Oo0oo00ooo` compares HumanoidArm.LEFT at bytecode155..158, pushes1 at161 or2 at165, saves the local, and passes it to the native wrapper at253. The background class `O000O0O00ooo000O0oOOoo00` passes null output at185 and literal3 at188 to its wrapper call200. Both full method records were reparsed from the hash-pinned original JAR and compared against existing detailed evidence. Pinned source NativeRenderer names these constants; its SHA256 is retained in the continuation receipt.

Native helper0x3982d0 is an integer-key map lookup, not an opaque decoder. It compares selector key with node.u32(+8), returning the matching node or null. At0x37f650, mode-1 becomes that key. Node.u32(+12) is startBone; endBone=startBone+descriptor[start].u32(+0x6c)+1. Thus Java-request identities are joined to exact native selector keys and ranges. This does not prove the model builder populated a correctly named bone in each key, nor that every model contains those entries.

## Output slot3 has unresolved meaning; not established W

The guarded global initializer at0x37b9e0 installs scratch object0xd34b60 and zeros buffer pointer0xd34b68/capacity0xd34b70. Prepare helper requests16*totalBoneCount bytes through0x4c4aa0 with initialize flag1.

Allocator wrapper behavior is concrete:
1. Request<=capacity: immediate return, no reset.
2. Capacity0: allocate through0xcbf560; when initialize flag is nonzero, call0x5766d0(pointer,0,size). Its inspected implementation is byte fill. The initial output allocation is therefore zero-filled.
3. Nonzero insufficient capacity: choose max(requested,2*capacity), call reallocation-like helper0xcc9c90, store returned pointer/capacity. This branch does not test initialize flag and has no clearing call. Bounded inspection of0xcc9c90 confirms allocator size-class behavior and an unchanged-pointer return branch; complete allocator semantics are not claimed.

Per-bone output pointer is scratchBase+16*index. The located tracking writer loads that pointer at0x37e953, writes XY as8 bytes and Z as4 bytes at+8. No+12 write appears in this output writer. The helper's one located load of this stored output pointer is this writer. Four floats are nevertheless copied to Java. Therefore:

- Slot3 starts zero for bones covered by the first zero-filled allocation.
- No per-render computation or reset of slot3 is established.
- Newly exposed bytes after growth are not guaranteed zero by this analysis.
- Do not label slot3 homogeneous W, a fresh flag, a meaningful coordinate, or universally zero.
- This is scoped dataflow evidence, not a whole-program proof that no other aliased code ever writes the buffer.

A scan of all executable PT_LOAD bytes for RIP-relative displacement candidates referencing0xd34b60/68/70/78 found seven candidates, all retained in `rip-candidates.json`: initializer writes, allocation object address/size, per-bone pointer creation, and JNI copy source. These candidates support locality but are not a complete alias analysis.

## Selected-range copy can include stale untracked XYZ

The output scratch is global, reused when capacity suffices, and not initialized from the caller's Java output array. Only a tracked bone's transform writes its XYZ; one accumulated flag enables copying the entire selected range at4 floats/bone. Therefore untracked entries inside that copied range may contain previous native scratch values. They are not guaranteed to preserve that caller's previous Java output, nor guaranteed to be fresh for the current model.

Concrete static witness, without executing the target: renderA tracks bone0 and writes its XYZ. A later renderB reuses capacity, leaves bone0 untracked, but tracks another bone in the same selected range. The latter tracking sets the copy-back flag; range copy includes old scratch XYZ for bone0. This describes a possible dataflow when those paths are reached, not an observed game defect. Reuse across different model objects is also not excluded by a model-local output-buffer identity: native scratch is global.

If no tracking work occurs, no output copy takes place and Java output remains untouched by this seam. Background mode normally supplies null output, suppressing copy-back even if its input unexpectedly requests tracking. Subtree modes copy only their selected interval.

## Reproduction

`build_receipt.py` verifies original hashes,11 byte anchors,6 raw windows, and2 complete original-JAR caller methods. [Evidence receipt](NATIVE-RENDER-OUTPUT-MODES-EVIDENCE-2026-10-18.json) includes bytes/hashes/backing, full caller evidence, pinned source hashes and the original cohort receipt hash. Last result: SOURCE_VERIFIED, no target executed. Remaining bounded uncertainties: newly allocated growth bytes, whole-program alias writers, and model-builder mapping from semantic bone names to selector keys.
