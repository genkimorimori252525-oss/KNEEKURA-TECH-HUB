# Bounded native controller construction

Static original-byte review only. SO SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. No target, callback, emulation, JVM, asset or installer execution. No repository edits. `reproduce.py` verifies inputs, extracts nine bounded windows, disassembles only copied bytes, records file backing/hashes and hashes prior receipts in `evidence.json`. Inputs verified unchanged afterward. No central mapping promotion or independent semantic review.

## Result and certainty boundary

The borrowed controller-file payload at outer node+0x30 is traversed by 365a10 into a Java map. Each inner tree node has key storage at +0x20 and a controller-data input at +0x40; 366110 builds that value from an initial string and a linked state collection. For every state it creates five Java arrays, one blend-like object and one boolean argument. Four expression-string paths invoke the already identified catching parser facade with boolean **false**. This differs from the earlier CommonAsset true call, but does not establish what the boolean means or prove successful parsing/evaluation.

Only two semantic metadata identities used here are independently resolved by existing receipts: d355b8+0x38 is the controller-file wrapper constructor; d355b0+0x48 is the parser method. Other constructor/factory slots below remain literal addresses. Their argument shapes correspond closely to the preserved Java controller/state declarations, but that correspondence is not fresh metadata decoding and is not an exact owner/name claim.

## 365a10: file wrapper and map boundary

Signature at machine level: hidden result wrapper RDI, JNIEnv RSI, borrowed file payload RDX, diagnostic context RCX, parser-reference wrapper R8. It saves RSI and R8 adjacently at stack+0x98/+0xa0 and passes that two-pointer context to 366110.

- 365a34..365a68 loads descriptor d356e0+0x60 and calls NewObjectV wrapper364a60 with no Java arguments. Returned object is retained at stack+0x50.
- 365aae..365aba loads first tree node from payload+0x20 and uses payload+0x10 as sentinel. 365ad3 advances through helper2ba620. Thus this inner traversal is ordered-tree iterator order, distinct from the outer hash-chain-to-array traversal already proved.
- 365ae4..365aee passes `[innerNode+0x20]` to JNI NewStringUTF. 365b0e passes `innerNode+0x40` to366110. No auxiliary outer string is involved in this immediate join.
- 365b3e..365b75 uses d356e0+0x68 with receiver stack+0x50, first argument converted key and second argument value wrapper+0x20. Wrapper364af0 is JNI CallVoidMethodV (slot0x1f0), **not a proved java.util.Map.put call or a returning put method**. It acts as insertion by dataflow into the known final Map argument; exact owner/name remains unresolved.
- 365c3b..365c69 invokes d355b8+0x38 through NewObjectV, sole Java argument map at stack+0x50. Existing `animation-controller-metadata.json` identifies `com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0.<init>(Ljava/util/Map;)V`.
- 365c7c..365c9d installs the result as a native local-reference wrapper (JNIEnv +0, deleter-manager +0x10, deleter360270 +0x18, jobject +0x20). After construction the temporary map local reference is released. Per-entry key/value local references are likewise released after insertion; native input nodes are borrowed, not transferred.

360270 resolves to JNI DeleteLocalRef (table0xb8). Java objects retained in arrays/maps are not invalidated by release of the temporary JNI local handles. Existing Java bridge proves the file wrapper shallow-copies its Map into a fastutil map and exposes an unmodifiable view; it does not clone controller objects. PlayerModelData separately wraps its supplied controller-file array without an unmodifiable wrapper; these are different ownership layers.

## 366110: controller-data input and state order

Let P be this function's borrowed RDX input (innerNode+0x40), and Ctx its RSI two-pointer context. Ctx+0 is JNIEnv; Ctx+8 points to the parser local-reference wrapper used by3742d0.

- 366132..36613c converts `[P+8]` using NewStringUTF, retaining the result at stack+0x230. Its position as first argument of the final constructor matches the preserved initial-state-string role; the native bytes alone do not name it.
- 366189..3661a7 allocates an object array using class from d355b8+0x48, count **low32(P+0x40)**, null initial element.
- 3661bd obtains first linked state node from P+0x38; 3661e3 advances via node+0. Array index increments in this linked order. No sort, deduplication or count-versus-chain check is added in this immediate construction loop.
- Node string pointer/length are node+8/+0x10. 366200..36624b makes an owned temporary string copy (small/heap branches). The source state-data object is node+0x28; 36625b..366268 copies it using368de0 into stack+0x2b8. This is an actual temporary native copy, not Java shallow-copy semantics.
- 3679b6..3679d4 places each constructed state into the object array using JNI SetObjectArrayElement; the temporary state local reference is then released.
- 367c0e..367c4b constructs d355b8+0x40 with converted P+8 string and completed state array. The resulting local wrapper is returned; temporary initial string and array local handles are released.

There is no local initial-state membership check here. The already reviewed Java constructor pools initialState, builds an immutable state-map wrapper through Collectors.toMap, and rejects duplicate pooled keys through that Java collector. That Java ownership/validation statement remains separate from the as-yet unresolved exact native +0x40 owner.

## Copied state structure and five arrays

Call368de0 copies the following offsets from source C=node+0x28 to same offsets of temporary T=stack+0x2b8. It installs native vtable d1cf78; copies two vector allocations via369090/369220; copies third vector through3693b0; copies two later vectors through3364e0; copies the blend subobject scalar word and tree; then copies final byte C+0xc0. Element-copy helper internals are not fully audited, so no universal deep-copy claim follows. The native temporary is destroyed with34cb50 at36798c before advancing.

Arrays below are listed in eventual constructor order. Role labels in parentheses are Java-shape correspondence, **not newly decoded slot identities**.

1. A (animation pairs): T+8/+0x10 begin/end, stride0x48. Allocation366279..3662a9 uses class d355b8+0x60 and element count span/0x48. At3662f9 the element's +8 pointer becomes a Java string. If qword element+0x30 is zero, the second reference is null (366344..36638f). Otherwise element+0x28 string is sent to3742d0 with flag0 at366358. At366392..3663c2 d355b8+0x60 is called through3654b0, a **CallStaticObjectMethodV** wrapper, with string and expression-or-null. Result enters A at3664d3. The same descriptor supplies array element class and factory method.
2. B (transition pairs): T+0x20/+0x28 begin/end, stride0x48. Allocation3665b7..3665e7 again uses d355b8+0x60. Element+8 becomes first string; element+0x28 goes unconditionally to3742d0 with flag0 (36667c..366691). Static factory at3666d0 receives both; element inserted3667e1. There is **no animation-style length guard** on this path.
3. S (sound names): T+0x38/+0x40 begin/end, stride0x28. Allocation3668c7..3668f7 uses class d356e0+0x78. Element+8 becomes a Java string at36693f and is inserted366987. No parser call is present in this loop.
4. E (onEntry): T+0x50/+0x58 begin/end, stride0x20. Allocation366a47..366a71 uses class d355b0+0x58. Each element+0 pointer goes to3742d0 with flag0 at366abc; returned object is inserted366ad2.
5. X (onExit): T+0x68/+0x70 begin/end, stride0x20. Same class slot, allocation366b6b..366b95. Each element+0 pointer goes to3742d0 flag0 at366bd8; inserted366bee.

The span division and source strides are explicit. No content, collection cap, valid modified-UTF encoding, nonnull element or parse-success guarantee is established by array construction.

## Blend-shaped dispatch and final state arguments

- T+0x8c byte exactly1 (stack+0x344 at366ca0) selects scalar constructor slot d355b8+0x50. T+0x88 float is widened to double with cvtss2sd at366cde..366ce7 and passed to NewObjectV366cf0. No time scaling is present in this conversion.
- Otherwise T+0xb8 count is checked at366e50. Nonempty tree iteration begins T+0xa8, sentinel T+0x98; each node's floats+0x20/+0x24 are copied into parallel native float buffers. Those become two Java float arrays through NewFloatArray/SetFloatArrayRegion (3670bd/3670d8 and367137/367152). Slot d355b8+0x58 receives the two arrays at3671d8, in the same paired tree order. Tree balancing/comparator and downstream interpolation semantics are not recovered here.
- If this non-scalar tree is empty, slot d355b8+0x50 receives double zero at367386..3673b6. Thus the immediate construction distinguishes scalar, nonempty paired-array, and empty-to-zero paths; it does not prove all serialized tag semantics.
- 36761c..36762e converts the copied state name. Final d355b8+0x48 NewObjectV call3676d8 has exact Java argument order: state-name string, A, B, S, E, X, blend result, zero-extended T+0xc0 byte. The last five are stack variadic arguments; offsets must account for the initial sub rsp,8 and successive pushes. This matches the preserved Java state constructor's shape but exact metadata owner remains a frontier.

The prior Java analysis establishes array-wrap views for A/S/E/X with unmodifiable wrappers, rebuilding transition pair containers while retaining expressions, direct blend/boolean retention, and pooled name behavior. Native copying and fresh JNI arrays do not convert these Java objects into deeply immutable snapshots.

## Exact expression bridge and error caveat

3742d0 receives result wrapper, parser wrapper, C string, boolean flag. It NewStringUTFs the string, loads manager d355b0+0x48, uses parser-wrapper+0x28 as the Java receiver and wrapper+0 as JNIEnv, and calls36d530 (JNI CallObjectMethodV slot0x118). The boolean is low8(ECX), zero-extended into R8D. Returned reference is wrapped and checked through41a560; temporary string local ref is released.

Existing resource metadata identifies public instance `com/elfmcys/yesstevemodel/OooOoOoOOOOo000oo0oo00oo.Oo0Oo0o00O00Oo0OOoOOoooo(Ljava/lang/String;Z)Lcom/elfmcys/yesstevemodel/O0o0OOO00000oO00O00oOOo0;`. Its original Java bridge calls an unsafe sibling, catches Exception on bytecode interval[0,6), logs and returns fallback. Therefore ordinary JNI return/ExceptionCheck-clear is **not parse-success evidence**. Nothing here evaluates the result or proves runtime model loading. All four controller calls use false; meaning of flag remains intentionally unnamed.

## Finite next frontier

1. Decode/verify exact descriptor identities for d355b8+0x40,+0x48,+0x50,+0x58,+0x60 and relevant collection slots d356e0+0x60,+0x68,+0x78 and d355b0+0x58. This would convert the explicit shape correspondences into exact native-to-Java identities; do not substitute readable source names now.
2. Pair the controller tree parser34ecd0's immediate node/value reader with P+8, P+0x38/+0x40 and source state C offsets above. This is the bounded wire-to-construction seam; root codecs/assets and animation schema are unnecessary.
3. If pursuing ownership further, audit only368de0's element-copy helpers369090/369220/3693b0/3364e0 and the state destructor34cb50. The complete exceptional cleanup graph and transitive deep copy remain unproved.

[Evidence](NATIVE-CONTROLLER-CONSTRUCTION-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.

Subsequent closure: [five exact identities](NATIVE-CONTROLLER-STATE-METADATA-2026-10-18.json), [wire producer](NATIVE-CONTROLLER-WIRE-RECOVERY-2026-10-18.md), and [Java bridge](NATIVE-CONTROLLER-JAVA-BRIDGE-2026-10-18.md). [Checkpoint collection proof](NATIVE-JAVA-COLLECTION-METADATA-2026-10-18.json) identifies HashMap.put(Object,Object):Object while the native helper still uses CallVoidMethodV; no runtime correctness or defect is inferred. Scalar formal Java constructor is(F)V; the native double is C variadic promotion.
