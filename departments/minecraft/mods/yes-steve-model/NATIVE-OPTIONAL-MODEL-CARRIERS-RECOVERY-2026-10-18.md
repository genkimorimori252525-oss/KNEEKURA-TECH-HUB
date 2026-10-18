# Optional model aggregate: animation/controller carrier join

Static original-byte evidence only. Original SO SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. No original targets, assets, JVM, callbacks, or backend tests executed. Authoritative windows, file backing, hashes and three ELF RELATIVE records are in evidence.json; reproduce.py rebuilds those windows from the pinned SO. Other exploratory windows are not authoritative.

## Result

M+0x48 supplies the animation-file map, and M+0x80 supplies the controller-file array in PlayerModelData. These roles follow exact constructor argument dataflow joined to original Java declarations, rather than native layout resemblance. The native M+0x80 source is a string-key map, although the Java destination is an array. The native M+0x48 source additionally produces a distinct selector-ordered array that is not the controller-file argument.

The separately obtained metadata receipt animation-controller-metadata.json (SHA-256 96fa0fdf46499864b20060dd63853906b88cd95890ca693d9ca68e82109b2866) resolves d35598+0x90 to com/elfmcys/yesstevemodel/OOooOooOO00O00000oOOO0oo.<init>(GeoModel[],Map,oo0o0o0o00000ooOoooo00o0[],O0OO0oooo0oO0oOOo0OOooO0)V and d355b8+0x38 to com/elfmcys/yesstevemodel/oo0o0o0o00000ooOoooo00o0.<init>(Map)V. Full obfuscated descriptors/class hashes are in that receipt. MODEL-INPUT-CARRIERS-RECOVERY-2026-10-17 identifies the original carrier's geometry/controller array wrapping, retained animation map, and retained textures. Metadata resolution and bytecode declarations do not establish actual JVM construction.

## Presence and read order

At 41f584..41f60a, input mode reader+8 == 1 reads a u32-like slot+0x10 tag; tag exactly 1 initializes the optional aggregate at M+8 with 421c60. The initializer sets aggregate+0x138, hence M+0x140, to 1 at 421d26. Other-tag branch 41f76c is outside this cohort; do not infer all non-one tag behavior. In the other reader mode the existing presence byte is serialized, and the four readers run only for value 1.

Present aggregate read order is 421d60(R,M+0x48), 422230(R,M+0x80), 422680(R,M+0xb8), then 422db0(R,M+0x10). Common reader identities and primitive contracts are inherited from the modern-schema/source receipts: slot+0x10 var32, slot+0x48 owned string, slot+0x58 owned byte-buffer payload. No text/JSON assumption follows from the nested payload layouts.

## Immediate storage schema

1. A=M+0x48: hash-map header buckets A+0, bucket count +8, head +0x10, size +0x18. Nodes are 0x58 bytes: next+0, integer key+8, wrapper table+0x10, payload object+0x18, auxiliary string+0x38. Each wire entry is key, auxiliary string, then payload virtual+0x10. Input count is read at 421eab..421ebb; entry reads 421f31/421f3f/421f4f. Node allocation 422003..422017. Payload table d1cc18 has RELATIVE slot d1cc28 ->3491d0. That immediate parser owns a count-prefixed vector with begin/end/cap at payload+8/+0x10/+0x18, element stride 0x160 (349200..34928c). Deeper element schema is a frontier.

At 422031..422057 the vector triple is transferred to node+0x20/+0x28/+0x30 and the temporary is zeroed. Auxiliary string follows heap-transfer/inline-copy handling. Existing key hits branch to temporary cleanup at 422125; the already-read entry is not inserted. Input-mode clearing destroys nested vector elements and frees storage/nodes, then zeroes buckets/head/count. Bucket allocation may be retained. No explicit collection-count cap is established here.

2. B=M+0x80: same outer hash-map header layout, node size 0x88. Node next+0, owned string key+8, wrapper table+0x28, payload object+0x30, auxiliary string+0x68. Wire order is key string, auxiliary string, then nested payload (422407/422415/422423). Lookup helper4236f0 returns an occupied result tested at422439; the nonzero branch skips allocation and goes to temporary destruction. Input node allocation42246d, owned key transfer/copy follows. Payload table d1cc68 slot d1cc78 ->34ecd0. Its immediate storage is an owned ordered tree: sentinel payload+0x10, root+0x18, first+0x20, last+0x28, count+0x30. 34ecd0 destroys the previous tree and reads a count; deeper node contents remain untraced. Move4224f1..422552 transfers the tree and repairs root-parent/sentinel links, resetting temporary root/count. Outer string cleanup and tree destructor34ca40 are visible.

3. C=M+0xb8: counted string-keyed segmented record storage; 0xc0-byte records in 0x180-byte blocks (two records). Index internals and duplicate policy are not fully traced. Record wire order, directly shown in output-mode422cb9..422d33 and matching input reads422849..4228da: owned key string at record+0; auxiliary string+0x68; buffer object+0x38; var32 fields+0x58/+0x5c; for version>=23 var32+0x60/+0x64, otherwise both set1; then nested411a10 at record+0x88. The record includes additional wrapper/state fields; this is not a complete texture codec. Input transfer at4228da through4108f0 and cleanup34f950 form the nearest ownership boundary; no claim of complete exceptional ownership.

4. D=M+0x10: integer-key map with 0x1e0-byte nodes, next+0/key+8, aggregate wrapper+0x10, common geometry G=node+0x18, auxiliary string+0x1c0. Wire count followed by key, auxiliary string, G virtual parser (422f4e/422f5f/422f6d); insertion423020 then temporary destructor3467b0. RELATIVE d1cb88 ->347dd0 proves the same geometry schema used by modern entry E+0x28. This is the previously documented optional geometry-map route into36a6e0, not an extra animation schema.

## Immediate native-to-Java joins

36d99f checks M+0x140 ==1 and preserves M at stack+0xd8. The existing geometry-selection receipt covers the optional geometry route; local reload36e04d preserves M in RBP for the first map consumer.

A consumer36e207..36e489 constructs a Java map through d356e0+0x60 and retains its local reference at stack+0x100. It walks M+0x58, then node+0 links. Integer key node+8 is looked up in global ordered selector tree d35be0 (root d35be8); a found label or a fallback string is passed to418b60. Payload node+0x18 is borrowed by361740 at36e398, with a key adapter d1b850 referencing node+8. The returned Java object and converted key enter map insertion d356e0+0x68 at36e39d..36e3d4. Native auxiliary string node+0x38 is not read by this immediate loop. 361740 sends payload+8 to361ba0 then constructs through d355b0+0x60; its nested element conversion is the next bounded frontier.

A second A consumer36e489..36e6bc allocates an array using d355b0+0x60 and global selector count d35c00, iterates ordered selectors from d35bf0, finds A by integer key, converts present payload through361740 or inserts null on absence, and stores the array at stack+0x140. It is separate from the following array and is not constructor argument3 below. Selector labels/keys in this d35be0 tree are not identified by the previously proven distinct d35ba8 geometry-selector tree.

B consumer36e6bd..36e806 allocates a Java object array through class metadata d355b8+0x38 with length low32(M+0x98), walks M+0x90/head by next links, and for each node calls365a10 with borrowed node+0x30 plus d1b878 adapter referencing node+8. It inserts returned objects sequentially with JNI slot+0x570 and saves the array at stack+0x170. Thus native linked traversal order becomes Java array order, not lexical sorting established here. Native auxiliary string node+0x68 is not read by this immediate loop. 365a10 walks the payload's ordered tree (first payload+0x20, sentinel+0x10), converts each inner key using JNI NewStringUTF at365aee and passes the inner value to366110 at365b39. The value address is inner-node+0x40 (365b0e). Inner value semantics are a frontier.

C consumer36e806..36ecb2 computes record count from segmented iterators, creates two Java arrays, copies each record key using NewStringUTF36e9cb and converts its corresponding value in the parallel loop, advancing 0xc0 and switching blocks after0x180 bytes. d355e8+0x50 combines those arrays at36eba7; reference stored at stack+0x1c0. This is the fourth carrier argument, the texture carrier by original Java declaration. No pixel format or GPU upload semantics inferred.

Final call36ecb2..36ed07 loads constructor d35598+0x90. Exact variadic argument order into364a60 at36ecfe:
- RCX = stack+0x70, geometry array from the established optional geometry route.
- R8 = stack+0x100, A-derived Java map, hence animation-file map.
- R9 = stack+0x170, B-derived Java array, hence controller-file array.
- Stack argument = original stack+0x1c0, C-derived texture carrier (the explicit eight-byte stack adjustment changes the push operand to+0x1c8).

Nested native containers remain borrowed during conversion. The final Java constructor receives Java references, not ownership of native map nodes/vector allocations. Local reference wrappers have cleanup calls, but complete exception handling and Java transitive copies are outside this static cohort. Original Java retention behavior is supplied by the cited carrier evidence, not inferred from C++ moves.

## Finite next frontier

Smallest remaining content seam is A's 0x160-element parser under3491d0 and conversion361ba0, or B's ordered-tree values under34ecd0 and conversion366110. Do one pair at a time to join serialized fields to exact animation/controller Java classes. Optional sections elsewhere, expression execution, texture payload codecs and runtime model loading remain outside scope.

Java bridge addition: NATIVE-ANIMATION-CONTROLLER-JAVA-BRIDGE-2026-10-18 confirms the semantic labels come from pinned-source correspondence, while original classfiles prove the exact erased declarations and stores. Controller-file construction shallow-copies its Map into Object2ReferenceOpenHashMap then wraps it unmodifiable. This does not deep-copy controller objects. The native-to-Java source offsets and argument order above remain independently established here.

[Native evidence](NATIVE-OPTIONAL-MODEL-CARRIERS-EVIDENCE-2026-10-18.json), [exact identities](NATIVE-ANIMATION-CONTROLLER-METADATA-2026-10-18.json), [Java ownership bridge](NATIVE-ANIMATION-CONTROLLER-JAVA-BRIDGE-2026-10-18.md), [geometry selection](NATIVE-MODEL-GEOMETRY-SELECTION-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
