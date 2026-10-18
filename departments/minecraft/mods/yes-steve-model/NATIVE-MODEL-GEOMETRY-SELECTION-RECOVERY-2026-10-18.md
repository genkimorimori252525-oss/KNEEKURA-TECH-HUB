# Exact model collection selection into geometry construction

## Result

0x36d8c0 accepts borrowed model M in RDX and has three concrete collection routes into0x36a6e0:

1. Optional integer-keyed map at M+0x10: matched map-node+0x18 is the geometry source.
2.0x348-stride vector M+0x148..M+0x150: each entry E supplies E+0x28.
3.0x348-stride vector M+0x160..M+0x168: each entry E supplies E+0x28.

These are sequential construction routes, not a choice of one active entry based on its identifier. The integer-map route is conditional on M+0x140==1; both vector routes are reached afterward on the normal path, including when the optional map is absent. Identifier strings are converted for Java construction, not compared to choose a single geometry in these loops.

The integer-map selector set comes from a distinct global ordered container, not directly from all keys stored in the model. Its contents and semantic names remain unresolved. The only proven distinguished key here is numeric1, which receives two additional model flags.

Static original ELF analysis only. No target/JVM execution, assets or repository edits. evidence.json pins9 authoritative original-byte ranges and links6 preceding receipts. Address-named exploratory excerpts have no broader whole-function evidentiary status.

## Borrowed source and output aggregate identity

At0x36d8d8, RDX is saved as M in R15. This is the same top-level model pointer produced by the versioned parsers and passed by0x35d548/0x35d54b. At each geometry call below, RDX is a pointer into model-owned storage; no source geometry is cloned or reference-counted by the selection instructions.

Inside0x36a6e0,0x36a70a stores RDX into stack+0x160, the aggregate A's first field.0x36a79f..0x36a7a7 then reads `[source+8,source+0x10)` and computes a0x80-stride bone count. This pins source identity to the exact aggregate consumed by the already-proven hierarchy and native registry constructor. The hierarchy's wrapper source pointers are therefore into these selected model-owned bone vectors.

The deferred caller later invokes0x345030 and frees the0x5d0 model at0x35dcc0/0x35dccd. Source pointers are borrowed for synchronous construction. This does not prove every nested field is copied by every downstream helper, or that a runtime callback cannot fail; the earlier ownership limits remain.

## Optional integer-map route

0x36d99f checks byte M+0x140 against1. If absent,0x36dad1 jumps to the first vector route0x36ef0e. If present, the worker also reads M+0x250 uint32 and M+0x5c9 byte for later construction arguments. This presence byte matches the optional M+8 aggregate initialized by the <=18 converter; the map can also be populated through the common modern root's optional section. It is therefore a common-layout route, not an unconditional version<=18 test.

Before lookup, a temporary40-byte-stride auxiliary sequence is assembled from other fields of this optional aggregate. This cohort preserves its pointer/count dataflow but does not assign a semantic type or retrace its unrelated payloads.

The selector sequence is explicit:

-0x36dd89 loads global d35bc8 as the Java output array length.
-0x36dda5 loads first selector-tree node from d35bb8; d35ba8 is the sentinel.
-0x36ddfd reads the selector uint32 at tree-node+0x20.
-0x36dde5 advances via known tree-successor0x2ba620; the output index increments separately.

The map lookup uses M+0x10 buckets, M+0x18 bucket count, M+0x20 head and M+0x28 count. It compares selector against map-node+8, using either bucket traversal or linked traversal. On success0x36dea2 adds0x18 to the node pointer, producing G=node+0x18. This exactly matches the <=18 conversion's destination geometry offset, and the common optional-map layout.

Missing keys reach0x36df40, zero the temporary result wrapper and continue to SetObjectArrayElement at0x36dfc0 with a null element. No fallback to another model key is present in this window. Output array ordering is selector-tree iteration order, not model-map iteration order. Without initializer/state proof, no selector names, total count or fixed key set is claimed.

### The two map call variants

Both calls use RDI=result wrapper, RSI=JNIEnv, RDX=G, RCX=temporary auxiliary-sequence pointer, R8=its element count. R9 points to a stack adapter with vtable d1b828 and a pointer to the current numeric selector.

- Selector1 calls0x36a6e0 at0x36df27. Stack arguments7..10 are M+0x5c9 byte, M+0x49a byte, M+0x49c byte, M+0x250 uint32.
- Other found selectors call at0x36dfa2 with the same source and common arguments, but stack arguments8 and9 are explicitly zero.

These offsets/values are proven. Names such as body, skin, armor or visibility mode are not assigned to numeric selector1 or those flags without separate metadata/use proof. The incoming fourth argument to0x36d8c0 is not the key used in this lookup; keys are loaded from the global tree.

## Vector routes and identifiers

The first vector starts at0x36ef0e: array length is derived from `(M+0x150−M+0x148)/0x348`, then entries are visited by address with increments0x348 at0x36ef97. The second begins0x36f704 and uses M+0x160/+0x168 with increments at0x36f787. Both iterate all entries on the ordinary successful JNI path. They do not inspect the root format version; all completed deserializers/converters feed this common layout.

For each entry, the identifier vector E+8/+0x10 is converted to a Java array. Each stored string pointer is passed to JNI NewStringUTF(+0x538), then stored using SetObjectArrayElement(+0x570). No identifier equality/hash lookup is involved before the geometry call. The conversion is conditional on successful/non-null Java allocation paths, so this is not a guarantee every entry always reaches native construction in the presence of JNI errors.

Each entry also supplies E+0x2c0 to helper0x4c8000, whose output at the caller's stack+0xb0 becomes one auxiliary argument. Its detailed format/ownership is deliberately not expanded. A stack adapter with vtable d1b760 stores the current E pointer. These adapters remain distinct from the integer-selector adapter.

The exact calls are:

-0x36f1ad for E in the first vector.
-0x36f99d for E in the second vector.

Both set RDX=E+0x28, RCX=&helper output, R8=1, R9=&entry adapter. Stack arguments7..9 are zero; argument10 is M+0x250. Thus the geometry source identity is the same E+0x28 that0x424920 deserializes and the compatibility converters move. Entry identifiers label the constructed Java-side objects; their downstream behavior remains outside this selection slice.

## Version joins and stopping point

-<=18: integer-map conversion produces nodes with G=node+0x18, while key3 produces an E in M+0x148 with G=E+0x28. Both consumer routes now have exact pointers.
-19..20: first compatibility map produces M+0x148 entries.
-21..26: a second compatibility map also produces M+0x160 entries.
->=27: direct vectors produce the same two in-memory entry collections, regardless of their different wire order.

No runtime-selected active model, render outcome, full Java publication or all exception cleanup is asserted. The next concrete unresolved boundary is the initializer/content/semantic identity of selector tree d35ba8 and the exact adapter metadata meanings, if those are needed. Root schema and renderer expansion are unnecessary to preserve the now-proven pointer/ownership join.

reproduce.py verifies9 original-byte windows and the hashes of6 prior receipts without executing target code.

Evidence: [NATIVE-MODEL-GEOMETRY-SELECTION-EVIDENCE-2026-10-18.json](NATIVE-MODEL-GEOMETRY-SELECTION-EVIDENCE-2026-10-18.json). [Preceding contract](NATIVE-MODERN-MODEL-SCHEMA-RECOVERY-2026-10-18.md). Raw ranges/reproduction scripts remain external.
