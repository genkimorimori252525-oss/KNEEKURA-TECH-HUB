# One native keyframe record and immediate Java boundary

Static-only original SO SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. No targets, JVM, assets, callback decoders or tests executed. Nine authoritative original-byte windows, three ELF RELATIVE targets, and prior receipt hashes are in evidence.json and reproducible via reproduce.py. Other extraction windows are exploratory.

## Result

The 0x180-byte record carries one promoted float32, one var32 selector, one mandatory three-component tagged number/string aggregate, and an optional second aggregate. Native conversion allocates Java objects without constructors, writes fields, and forwards the array and the low byte of the caller's rotation flag to a static Java method. No native degrees/radians or seconds/ticks scaling occurs in this immediate parser-to-field-write path. Downstream Java conversion remains a distinct boundary.

## Owned vector and wire fields

34b5a0 is called for each of the three vectors in a bone record. Input mode clears old owned elements with virtual destructors, retains the vector allocation where possible, reads a count through reader+0x10 at34b609 and constructs each temporary before34b794 calls34c7c0. Output mode walks elements at0x180 stride and invokes their virtual parser. Append/growth ownership beyond the immediate temporary constructor is not fully traced in this cohort; prior animation evidence establishes the borrowed vector consumer.

ELF RELATIVE d1ce30 ->34c7c0, d1ce08 ->34c760, d1cde0 ->34a220 establish the three nested parser identities. For record K:
- K+8: reader+0x38 at34c7d8. Established reader4c3fc0 reads float32 and promotes to double. This numeric field is the timestamp candidate; its exact Java field identity is still metadata-dependent here.
- K+0x10: var32 selector via reader+0x10 at34c7e5.
- K+0x18: mandatory triple object, parsed through its virtual+0x10 at34c7f3.
- K+0xc8: optional triple object; K+0x178 is presence. Input reads a var32 presence tag34c813 and clears prior presence. Exactly tag1 initializes/reads the object (34c958 sets presence1,34c965 calls34c760). Other tags clear old storage and leave it absent. The old heap strings are freed during replacement/removal. No version gate appears in this immediate record parser.

34c760 parses three component objects T+8, T+0x40 and T+0x78 in that order. Therefore mandatory component addresses are K+0x20,+0x58,+0x90; optional component addresses are K+0xd0,+0x108,+0x140. Each component V uses34a220: kind var32 at V+8; kind1 reads promoted float32 into V+0x10; kind2 reads owned string into V+0x18. Other kinds consume no additional component payload in this parser. This describes actual branching, not a complete validity guarantee. Components own their strings; numeric and string slots are structurally separate.

## Borrowed conversion and source ordering

364b80 receives a vector header (begin/end at+0/+8), an environment/context and ECX flag. It saves ECX at stack+0x1c, computes the Java array length from byte span divided by0x180 using shifts/inverse multiplication, and narrows to jint for NewObjectArray364bd4. Class metadata is d355b0+0xa8. No explicit length/range validation is established by that arithmetic.

Records are processed in native vector order. The loop keeps R14=K+0xd0; its unusual next-record comparison uses K+0x180 before advancing to next K+0xd0 (364c00..364c1b). It allocates each Java object via JNI AllocObject364c3c, again using class d355b0+0xa8. It does not call a constructor for these objects in this loop. Sequential SetObjectArrayElement364ebe publishes each resulting local reference into the Java array. Complete null/allocation/exception recovery is not inferred from the normal path.

## Exact immediate Java slot/write map

All slots below are offsets from manager d355b0. They denote descriptors/field metadata, not native K offsets.

- +0xa8: array element class at364bad and AllocObject class at364c2b.
- +0xb0: double field, SetDoubleField364cbd receives unchanged K+8.
- +0xb8: object field, SetObjectField364d1d receives a Java reference selected from d1b6d8 by K+0x10. Converter enforces unsigned selector<3 at364ccb..364cd6, so accepted selector values are0,1,2. Selected object identities and interpolation meanings were unresolved in this static cohort. The later exact metadata proves an interface-typed field, not a Java enum.
- +0xc0/+0xc8: numeric/expression fields for component K+0x20; helper365540 call364d4d.
- +0xd0/+0xd8: same for K+0x58, call364d71.
- +0xe0/+0xe8: same for K+0x90, call364d95.
- +0xf0/+0xf8: same for K+0xd0, call364dc6 when K+0x178==1.
- +0x100/+0x108: same for K+0x108, call364df8.
- +0x110/+0x118: same for K+0x140, call364e2a.
- +0x120: boolean field set to true via SetBooleanField364e70 when the second triple is absent. Present-path value is left to raw allocation defaults/other behavior; do not infer an explicit false write here.

365540 examines component kind. Kind1 loads the double V+0x10 and writes the first field descriptor through SetDoubleField365575, then checks JNI status. Kind2 passes V+0x18 string to3742d0 with ECX=0 at36561a, then writes the returned Java reference into the second field through365780 -> SetObjectField3657a0. The parser facade's exact semantics and exception/fallback behavior are already a separate Java bridge; no expression evaluation or parser-success claim is made here. Other kinds take the error path365649 outside this cohort. No multiplication, division, sign flip, or float narrowing occurs along these immediate numeric field writes. Wire float32 precision is already fixed before promotion.

## Rotation flag and stopping boundary

The original animation converter calls364b80 for bone+0x28 with ECX=1 at362047/36204c, bone+0x40 with0 at362060/362062, and bone+0x58 with0 at362077/362079. Those associations are exact; rotation/position/scale readable roles require the original BoneAnimation constructor correspondence.

At364f89..364fc3, manager+0xa0 supplies a static method. The complete Java object array is RCX and zero-extended low byte of saved ECX is R8D. Helper3654b0 packages varargs and calls JNI CallStaticObjectMethodV through slot+0x398 at36552c. The returned object is retained in the output reference wrapper at364fd9..364ffa. Thus flag1 versus0 is forwarded to Java postprocessing, rather than applied as a native numeric transform in this loop. This static method may sort, scale, adapt or validate records; none of those operations is established without its exact metadata/Java body. The native source-order array does not imply final returned-list order.

## Reuse boundary

The native wire/owned storage and Java raw-field transfer are now bounded. Native records remain borrowed while Java objects and the array are created. No native record pointer is passed as the returned list, and no deep-copy guarantee follows for parsed expression objects. Normal JNI status checks do not establish runtime success.

Smallest next step: exact identities and original Java body for manager+0xa0, plus class+0xa8 and fields+0xb0/+0xb8/+0x120. The remaining six field-pair names can be joined afterward. This is the precise boundary for timestamp units, rotation conversion and output ordering; interpolation implementations and runtime evaluation should remain separate.

[Evidence](NATIVE-KEYFRAME-ELEMENT-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.

Later [primary metadata](NATIVE-KEYFRAME-PRIMARY-METADATA-2026-10-18.json), [six field pairs](NATIVE-KEYFRAME-PAIR-METADATA-2026-10-18.json), [Java bridge](NATIVE-KEYFRAME-JAVA-BRIDGE-2026-10-18.md), and [focused independent review](NATIVE-KEYFRAME-JOIN-FOCUSED-REVIEW-2026-10-18.md) refine those identities. [Easing bootstrap join](NATIVE-KEYFRAME-EASING-JOIN-2026-10-18.json) proves selectors0/1 share the linear factory and2 selects Catmull, with index-zero/processor-selection caveats.
