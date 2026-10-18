# One animation element: wire storage and immediate Java conversion

Static original-byte analysis of SO SHA-256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. No native targets, JVM, assets or original self-tests executed. evidence.json pins eleven authoritative windows and four ELF RELATIVE targets; reproduce.py rebuilds them. Exploratory windows are not authoritative. The previous optional-carrier receipt joins this path to PlayerModelData's animation-file map.

## Core result and ordering

The file payload3491d0 contains a count-prefixed vector of 0x160-byte elements; each element is parsed by34a2a0. ELF slot d1ced0 (table d1cec0+0x10) relocates to that parser. 349224 reads the count; 349496 parses a temporary; append/move follows. The temporary starts with an empty name, double -1 at+0x28, u32 1 at+0x30, absent optionals and zeroed vector storage (349407..349496). Existing vector contents are destroyed/cleared when reading; growth and element transfer preserve owned subobjects. Full allocation failure/unwind behavior is not established.

361740 passes payload+8 to361ba0 at361773. Converter361ba0 reads begin/end at argument+0/+8 (the element vector), steps by0x160 at361c60, creates a Java map and inserts each converted element using its name at363399..3633e4. There is no sorting in this immediate loop. Java map insertion behavior for duplicate names remains dependent on the exact map method; do not infer vector-wide name uniqueness or a sorted map.

## Element A schema

Wire order in34a2a0:
- A+8 owned name string via reader+0x48 at34a2c2.
- A+0x28 double destination via reader+0x38 at34a2d1. The established reader reads float32 then promotes; it is not an eight-byte serialized double.
- A+0x30 var32 via reader+0x10 at34a2e0.
- For version>=10, optional objects A+0x38, +0x78, +0xb8, each read by34b170, followed by optional bool storage A+0xf8/value and+0xf9/presence. Lower versions proceed to the vectors without reading these fields.
- A+0x100/+0x108/+0x110: counted vector, stride0x70; parser34b550, table d1ce98+0x10 ->34b550. Read at34a3e5; temporary parse34a5a1.
- A+0x118/+0x120/+0x128: counted vector, stride0x28; parser34b410, table d1ce70+0x10 ->34b410. Read at34a445; parse34aac2.
- For version>=11, A+0x130/+0x138/+0x140: counted vector, stride0x30; table d1ce48+0x10 ->34b2d0. Read34a4a5; element string and promoted number read inline at34ae6a/34ae79.

Each optional number/string object O has presence O+0x38. 34b170 reads a var32 presence tag, clears prior presence, accepts tag1 to construct/read O through34a220. 34a220 reads kind O+8: kind1 reads reader+0x38 into O+0x10; kind2 reads string into O+0x18. Other kinds return without a payload read. This is an observed structural tagged value, not a claim of globally validated expression syntax. Optional bool input likewise reads tag1 before reader+0x40; other-tag branch34ad4a clears presence. Reader bool validation itself is inherited from the established reader receipt.

The converter separately reads A+0x148/+0x150/+0x158 as a stride0x98 vector. There is no explicit fill of that vector in the scoped34a2a0 wire path; this cohort does not establish its upstream producer or absence across other construction paths. This distinction is important: a consumer branch alone does not establish serialized particle support.

## Scalar/optional conversion and final constructor

Name A+8 is converted twice through JNI NewStringUTF361c8a/361ce0, for the result-map key and element constructor argument. A+0x30 is checked as unsigned (value-1)<3 at361d29..361d33; valid values1..3 select pointer entries from d1b6c0, whose+0x20 Java references reach the final constructor. Enum constant identities are not decoded here.

Each present O is converted according to kind: kind1 passes its double unchanged to3744f0; kind2 passes its string to3742d0 with ECX=0. Unknown kind/absence yields a null reference. Immediate3744f0 invokes d355b0+0x50 without numeric scaling;3742d0's parser facade and caught-exception behavior belong to existing metadata/Java evidence, and normal return is not proof of expression success. No expression evaluation is executed.

A+0xf8 selects d34a90 versus d34a68; A+0xf9 decides whether the selected+0x20 reference or null is passed. Boxed Boolean identity is a metadata/frontier matter until joined to the constructor declaration.

Final constructor d355b0+0x68 is loaded362fe7 and called36306c. Argument order, correcting for each stack push, is:
1. name Java reference (original stack+0x1b0),
2. double A+0x28 in XMM0,
3. selected enum reference,
4. converted optional A+0x38 (stack+0x240),
5. optional A+0x78 (stack+0x210),
6. optional A+0xb8 (stack+0x1e0),
7. optional bool reference (stack+0x2c0),
8. A+0x100-derived array (stack+0x180),
9. A+0x130-derived array (stack+0x120),
10. A+0x148-derived array (stack+0x150),
11. A+0x118-derived array (stack+0x128).

All stack offsets above refer to RSP before the temporary eight-byte alignment subtraction at363032. No multiply/divide/time conversion occurs between loading A+0x28 at363018 and this constructor call. Units cannot be established from floating-point representation alone. Existing ANIMATION-DATA-OWNERSHIP evidence describes the Java Animation carrier's double-to-float narrowing and shallow array wrapping; exact manager-slot identity is being proven separately and must be joined before assigning all readable field names.

## Immediate bone-array boundary

B is a0x70-byte record: name B+8 via reader+0x48, and three vectors B+0x28, +0x40, +0x58 via34b5a0 (34b564/56e/57a/590). Each vector's immediate reader clears prior elements and reads a count, stepping0x180 per nested element. Nested keyframe schema/math is out of scope.

Converter computes (A+0x108-A+0x100)/0x70 at361f66..361f8d and allocates the Java array using metadata d355b0+0x98. It walks B in source order, converts name, and calls364b80 on B+0x28 with ECX=1, B+0x40 with0, and B+0x58 with0 (36204c/362062/362079). These flags are exact; rotation/position/scale units and interpolation semantics are not inferred from them. Constructor d355b0+0x98 at362085/3620cb receives name and the three resulting list references in that order. Objects are inserted sequentially through JNI SetObjectArrayElement362298. Native vector storage remains borrowed during conversion.

## Immediate event-array boundaries

Keep vector offsets and metadata offsets distinct:

A+0x130, stride0x30: record S has string S+8 and promoted float32 S+0x28. Parser34b2d0 and inline34ae6a/34ae79 prove that order. Array class d355b0+0x128 at3623ac; constructor same slot at362477/3624a9 receives the number and Java string. No native numeric scaling at this call. Sequential insertion362566. This is a different source vector from the next use of the same class.

A+0x118, stride0x28: record I has nested vector at I+8 (346ba0) and promoted float32 at I+0x20 (34b410). Converter allocates an array using d355b0+0x128 at362bab; each I's nested vector is treated as0x20-byte strings and converted to an array using d355b0+0x58 at362c39/362c56. It allocates the event object with JNI AllocObject at362d62, using class d355b0+0x128, rather than invoking that class's constructor in this branch. Field d355b0+0x138 is written with JNI SetObjectField362ded; field+0x140 is written with SetFloatField362e4b after explicit double-to-float narrowing362e3d of I+0x20. Field identities remain a precise metadata frontier. Allocation/field writes are static callsites, not proof of initialized runtime objects or successful JNI operations.

A+0x148, stride0x98: array class d355b0+0x130 at362667; constructor same slot at36282c/362873. Converter passes four strings at record+0x10/+0x38/+0x58/+0x78 and double record+0x30, in the constructor's mixed register/stack order. First string+0x10 is passed after the number, then+0x38,+0x58,+0x78. Its source producer remains unresolved here. Numeric loading at36284f has no local scaling. This is the +0x130 metadata slot; it must not be confused with the A+0x130 vector using metadata+0x128.

Array lengths are computed from native spans, narrowed into JNI jint registers. Positive signed-count branches and 0x7fffffff masking are visible for loops; they do not prove a global size bound or successful allocations. No sorting or timestamp monotonicity validation is established in these immediate loops.

## Ownership and stopping boundary

Wire parsers own strings/nested vectors and clear/move temporary storage. Converters borrow native records and create Java references. Local reference wrappers are cleaned up after construction/insertion; full unwind/global-reference lifetime is outside this cohort. Java carriers may retain shallow array/list views, per existing Java receipts; native container moves are not Java deep-copy guarantees.

Finite next steps: join the four constructor metadata slots and two AllocObject field slots; then, if authorized, trace only one0x180 keyframe parser with364b80, or resolve the A+0x148 producer. Do not expand controller schemas, expression execution, all event emitters or an asset decoder from this result.

[Evidence](NATIVE-ANIMATION-ELEMENT-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.

Later closure: [four constructors](NATIVE-ANIMATION-ELEMENT-METADATA-2026-10-18.json) and [two AllocObject field identities](NATIVE-EVENT-FIELD-METADATA-2026-10-18.json). The last four constructor arrays are bone, sound-event, particle-event and instruction-event counterparts, retaining existing Java evidence confidence. [Fresh particle-vector proof](NATIVE-PARTICLE-FRESH-WIRE-RECOVERY-2026-10-18.md) is limited to the fresh reader/append path and unchanged subsequent input.
