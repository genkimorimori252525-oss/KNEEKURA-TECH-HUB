# Optional aggregate → animation/controller Java bridge

Read-only original-classfile verification. Exact original JAR SHA256 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f. Companion JSON binds the two decoded identities to reparsed class bytes and compares every method field against MODEL-INPUT-CARRIERS-EVIDENCE and ANIMATION-DATA-OWNERSHIP-EVIDENCE. Both match, including full operands and exception tables. The preserved source files at revision f184edabd1b5115ce5a24cb6d155ba5a669f5ba6 were also hash-rechecked against those evidence records.

## Exact argument order

Manager d35598+90 / callback410540 resolves public instance constructor owner `com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo`. Its existing semantic correspondence is PlayerModelData. Constructor argument order and exact stored fields:

1. GeoModel[] (`OOoOoooOOooO0o0000o0O0o0[]`): ObjectArrayList.wrap at bytecode6; stored as List field `Oo0Oo0o00O00Oo0OOoOOoooo` at9.
2. Animation-file Map: argument2 directly stored in Map field `o0OOooo0o0OO00OoOOOo0o0O` at14. Pinned source identifies Map<String,AnimationFile>; erased JVM descriptor alone does not establish that generic type.
3. AnimationControllerFile[] (`oo0o0o0o00000ooOoooo00o0[]`): ObjectArrayList.wrap at19; stored as List field `O00OOOooOoooOoo0o0o0oO0O` at22.
4. Texture FifoHashMap (`O0OO0oooo0oO0oOOo0OOooO0`): directly stored in `oOOOo0OOO0ooooo0O00OO0o0` at28. Pinned source identifies FifoHashMap<String,NativeTexture>.

Therefore the supplied native argument joins identify the M+48-derived Map as the animation-file map and the M+80-derived array (head M+90/count M+98) as controller files. Native callsites36ecb9/36ecfe and those memory-layout premises come from the static native analysis; this Java bridge does not independently retrace them.

The constructor returns at31. It does not clone the arrays, add unmodifiable list wrappers, copy the animation/texture maps, or validate required indices, lengths, contents or cross-file compatibility. The array-backed lists and referenced objects remain shared according to the invoked wrap API and preserved source correspondence.

## Controller-file wrapper

Manager d355b8+38 / callback40fe80 resolves public instance constructor `com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0.<init>(Ljava/util/Map;)V`. Pinned source correspondence is AnimationControllerFile, whose input is Map<String,AnimationControllerData>.

Bytecode5 allocates Object2ReferenceOpenHashMap;10 invokes its Map constructor;13 calls Object2ReferenceMaps.unmodifiable;16 stores that result in Map field `Oo0Oo0o00O00Oo0OOoOOoooo`;19 returns. The map container is shallow-copied and exposed read-only. Keys/controller objects and their nested state/expression objects are not deep-copied. This policy is distinct from PlayerModelData directly retaining the animation-file map and wrapping its controller-file array.

## Scope and exceptions

Obfuscated declarations, access flags, method hashes and instructions are exact original-artifact proofs. Readable semantic roles are retained from the existing pinned-source correspondence; no original symbol recovery, confidence promotion or whole-source equivalence is asserted. Successful return establishes only these local stores/wrapper operations. Both constructors have no local exception handlers; allocations, library calls or invalid inputs can throw. No controller-state existence, uniqueness across files, nonnull guarantees, successful native conversion, cleanup or animation execution is established. No new callbacks, JVM, target library or assets were executed.

[Bridge evidence](NATIVE-ANIMATION-CONTROLLER-JAVA-BRIDGE-2026-10-18.json), [exact identities](NATIVE-ANIMATION-CONTROLLER-METADATA-2026-10-18.json), [original Java carriers](MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17.md), [controller ownership](ANIMATION-DATA-OWNERSHIP-RECOVERY-2026-10-17.md).
