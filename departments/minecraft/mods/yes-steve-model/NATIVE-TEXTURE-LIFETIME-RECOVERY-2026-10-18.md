# NativeTexture upload and native-storage release

## Result

The original-YSM upload entry uses a Java long as a native registry key, not a raw pointer. A matching native record supplies source data to GL upload helper3a52c0; that helper queries the currently bound GL_TEXTURE_2D name and inserts it into a separate integer set. Native free(J)V removes the handle-keyed source-data record and frees native allocations. It does not issue GL deletion, erase the separate GL-name set, or reset a Java texture ID in its inspected body.

No native/JVM/emulator/GPU execution or repository edits. `reproduce.py` verifies original SO/JAR hashes, both exact native declarations, seven original-byte code windows and upstream dossier hashes. Fresh original class parsing finds private-final long `Oo0Oo0o00O00Oo0OOoOOoooo:J` and a separate Map field; the encoded native field descriptor remains independently unresolved rather than being named by elimination. Primary static review; independent semantic review NOT_RUN.

## Exact methods and Java lifecycle join

Owner `com/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0`:
- instance private-native `O00OOOooOoooOoo0o0o0oO0O()V` →3bf0c0
- static private-native `Oo0Oo0o00O00Oo0OOoOOoooo(J)V` →3bf540

The binding names/descriptors/access are preserved in NATIVE-TEXTURE-LIFETIME-EVIDENCE-2026-10-18.json and independently checked against the original classfile. Existing NATIVE-TEXTURE-JAVA-BOUNDARY evidence establishes constructor storage of the long and Cleaner registration, plus load's render-thread-or-queued dispatch. Its doLoad obtains inherited integer getId, calls GlStateManager._bindTexture with it, then invokes native upload. No native method body in this receipt should be projected into the older Java-only dossier.

A Java load return may mean only that work was queued. The native upload body does not independently call the inherited getId or set a Java integer texture field. Binding and upload remain different steps; external AbstractTexture/GlStateManager effects are not rederived here.

## Handle lookup and metadata boundary

`3bf0cd` preserves the Java receiver. TLS setup establishes an environment, then manager d355c0 record+40 must have both class and member handles (`3bf0ff..3bf11b`), otherwise native error construction code0x3e is used. `3bf12e` invokes JNI GetLongField at table offset328 on the receiver. The returned 64-bit value is saved as a key; helper41a560 is called afterward (full helper exception semantics are outside this slice).

Exact field-identity follow-up evidence:
- manager+40 descriptor derives from callback40fe40: LEA408a77, helper406770 call408a97, record store408ab8, manager global store408b09
- callback40fe40 reads encoded source4019f, length79 (0x4f), through decoderd14730
- constructor record+38 is callback40fe20, source46cc3 length63; record+48 is callback40fe60, source41370 length95, not invoked by the upload body

Original-JAR long-field candidate is known, but the native→field textual identity is not claimed until that callback is decoded. No decoded integer-ID field metadata is needed to describe this body because it has no such field access.

`3bf149..3bf150` conditionally locks d34920 when threading markerd2cf70 is nonzero. The body then searches registry bucketsd348b0, bucket-countd348b8, before-first noded348c0, element-countd348c8; each node's 64-bit key is at+8. Missing keys branch to3bf399, unlock and return, without upload. There is no dereference of the Java long as an address and no unconditional free(long). Zero is not given a separate entry guard; it is treated as a key for lookup.

The model-receive dossier independently records producer375430 allocating an incrementing handle, constructing its Java carrier, and inserting a0x58-byte node in this exact registry underd34920. This joins receive storage to upload/release without borrowing unrelated audio-pointer conventions. Geometry and GL-name registries remain distinct.

## Matched-record source transformation and upload

A found node is retained in R13 while the same mutex stays held. Its source wrapper is node+10 and another wrapper is node+40.

1. `3bf234..3bf304` allocates a temporary0x9d8-byte state. Virtual+18/+20 calls on node+40 feed573dd0 with literal 64-bit0xd017cbba7b5d3581; the result seeds a recurrence using0x5851f42d4c957f2d. This constructs312 64-bit words and an index/cached-word state.
2. At3bf2ee..3bf2ff, node+18 and node+28 are supplied as source/destination pointer and equal bounds to4df880. The inspected helper uses generated64-bit words from43bfe0 XORed with input chunks and byte tails. Source and destination are the same pointer on this path, so the native record's bytes are transformed in place. No complete cryptographic/codec identity is asserted.
3. If node DWORD+38==1, `3bf318..3bf33d` obtains data from source wrapper virtual+18, loads node+30/+34 as two integers and calls3a52c0(environment,data,integer1,integer2). The helper's concrete GL calls use these integers as width and height, establishing their upload role on this branch.
4. Otherwise `3bf344` calls4c8000 on the source wrapper, obtains a temporary wrapper, then passes its data and temporary+28/+2c dimensions to the same helper at3bf37d. Temporary pointer stack+10 is freed afterward when nonnull. This branch is a conversion/decode boundary; its exact supported file format and all validation remain outside this slice.
5. On normal completion both branches call3a58e0(node+10) at3bf394. That helper reconstructs the same style state using the wrapper at argument+30 (node+40) and reapplies4df880 to argument+8/+18 (node+18/+28), then frees only its temporary0x9d8-byte state. This is a paired in-place transformation, not source-buffer destruction. Calling it “free source data” would be wrong. Bit-exact restoration depends on the same seed/data assumptions; full virtual helper semantics were not executed or exhaustively proved.

Selected catch paths also converge on the reapplication call; other unwind paths free temporary state and unlock. This is not a proof every exceptional path completes reapplication or preserves all state. The upload does not erase its registry node or free node+18 on its normal return, allowing source storage to remain until explicit release.

## GL upload and separate integer-set join

Both upload branches reach the already verified3a52c0. It calls saved original LWJGL nglGetIntegerv for0x8069, verified by original GL11C ConstantValue as GL_TEXTURE_BINDING_2D. Binding0 skips its upload/insert body. Nonzero binding requests TexImage2D/TexSubImage2D and then inserts that queried 32-bit GL name into setd348e8/f0/f8/d34900. This GL integer is distinct from the Java long handle and from the native source pointer.

The five client-registration wrappers use that separate set: DeleteTextures forwards first then erases integer keys; four other wrappers conditionally skip forwarding based on their first argument's numeric membership. Those precise API-argument caveats remain in NATIVE-LWJGL-WRAPPERS-RECOVERY-2026-10-18.md. NativeTexture upload does not prove GPU success simply because its GL-name set receives an entry; no GL-error test separates upload requests from insertion in3a52c0.

## free(J)V: release native storage, not GL name

`3bf544` preserves the incoming Java long from RDX. `3bf551..3bf558` conditionally locks the SAME d34920. The same handle registry is searched, including full 64-bit key comparisons at3bf5bc/3bf611. A miss skips to unlock/return at3bf723; repeated release after successful removal therefore finds no entry unless that key has been reintroduced elsewhere.

For a match, `3bf671..3bf6fe` finds the predecessor, updates affected bucket links and unlinks the node. Then:
- node+18 is passed to deallocation helpercc74a0 when nonnull, at3bf70a
- the node itself is deallocated with size0x58 at3bf717
- registry element-countd348c8 is decremented at3bf71c
- the mutex is released, with a tail call on the threaded branch

This full release body makes no JNI field read/write, no saved LWJGL export call, no call to the five wrappers, and no access to GL-name setd348e8..d34900. Therefore it establishes native-storage release independently of actual GL texture deletion. It does not set the Java final long to zero, invalidate every Java reference, or invoke an inherited close/release method. Java Cleaner scheduling, this native source-data release, Minecraft texture-ID release, and original LWJGL deletion remain separate boundaries.

## Bounds

No claim of installed native overrides, uploaded pixels, correct graphics context/thread, complete image decoder, global texture lifecycle, or full exception rollback. Native registry lookup/free is serialized when the image's threading marker is present; external ownership/concurrency beyond those guards remains unproved. The field callback metadata is the remaining narrow identity gap, not a reason to fabricate a Java texture-ID read or broaden raw-pointer conclusions from other natives.


## Subsequent exact texture-identity closure

The earlier unresolved labels describe the original-byte static pass preserved in NATIVE-TEXTURE-LIFETIME-EVIDENCE-2026-10-18.json. Separate guarded metadata receipt NATIVE-TEXTURE-METADATA-2026-10-18.json (SHA256702036d578ad1922c203224c0aae5df71165ca510f8bcfaadd03a5b52826a88d) now independently resolves both callbacks against the exact original-YSM class:

- callback40fe20, managerd355c0+38: com/elfmcys/yesstevemodel/O0O00000Ooooo00oooo0ooo0.<init>(J)V, public
- callback40fe40, managerd355c0+40: same owner, Oo0Oo0o00O00Oo0OOoOOoooo:J, private-final instance field (access0x12)

Both original-class matches have SHA2566f85b1ec64d10ac43fe6c8cfd34c0b89889dd1832419da05cb2e407a69c3949e. This closes the receive-constructor→Java-long-field→native-GetLongField join, without renaming the long as a raw address. The pinned original Java constructor evidence shows aload_0 at11, lload_1 at12 and putfield of this exact field at13, then Cleaner registration using the same supplied long. NATIVE-TEXTURE-IDENTITY-CLOSURE-2026-10-18.json pins that Java evidence and constructor Code hash, together with the separate metadata receipt. Thus native receive's handle can be followed into the exact Java final field and back into upload's registry lookup. The GL integer still comes from the binding query, not this long field. No constructor execution, upload, native registration or GPU success was observed.
