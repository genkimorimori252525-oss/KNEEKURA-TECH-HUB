# Animation/keyframe selector reference provenance

## Result

The six original ELF RELATIVE relocations prove two distinct three-entry tables. The keyframe native selectors 0 and 1 alias exactly the same native wrapper; selector 2 selects another wrapper. The animation selectors 1, 2, 3 select three separate wrappers. Initializer 0x3c6f90 fills these wrappers' +0x20 members from five Java static object fields, accessed through manager 0xd355b0 slots +0x70 through +0x90. Literal Java field names remain a bounded metadata frontier in this receipt. No Java enum or ordinal assumption is required.

| Input selector | Table slot | RELATIVE target wrapper | Object-reference member | d355b0 descriptor slot |
|---|---|---|---|---|
| Animation 1 | d1b6c0 | d34950 | d34970 | +70 |
| Animation 2 | d1b6c8 | d34978 | d34998 | +78 |
| Animation 3 | d1b6d0 | d349a0 | d349c0 | +80 |
| Keyframe 0 | d1b6d8 | d349c8 | d349e8 | +88 |
| Keyframe 1 | d1b6e0 | d349c8 | d349e8 | +88 |
| Keyframe 2 | d1b6e8 | d349f0 | d34a10 | +90 |

Addresses are unrebased original ELF virtual addresses. evidence.json records each relocation record address/hash, type 8 and addend. A relocation gives the wrapper address, not the Java object reference; the latter is loaded from wrapper+0x20.

## Exact consumer reads

Animation 0x361d29 reads uint32 A+0x30, subtracts one, and unsigned-checks index <3 at 0x361d30..33. 0x361d3b loads the d1b6c0 table address; 0x361d42 loads its indexed pointer, saved at stack+0x2c8. At 0x36301e..26, that pointer is recovered and its +0x20 reference becomes R8 for the constructor selected by d355b0+0x68 (load 0x362fe7, call 0x36306c). This proves selector normalization, not a Java ordinal conversion.

Keyframe 0x364ccb reads uint32 K+0x10 (R14 is K+0xd0); 0x364cd2..d6 unsigned-checks <3. 0x364d04 loads d1b6d8, 0x364d0b indexes by this original selector, and 0x364d0f loads wrapper+0x20. JNI SetObjectField at 0x364d1d uses the raw-object field descriptor d355b0+0xb8 loaded at 0x364ce3. Parent's separately verified Java declaration is interface o00o00ooO000OoOoooO0000O; this report does not call it an enum. Native selectors 0 and 1 therefore deliver the same stored reference at this immediate field write, assuming no intervening mutation of that wrapper. This does not establish equality of other keyframe fields or later Java processing.

## Producer chains

All five normal resolved-metadata paths load descriptor[0] into RSI (class) and descriptor[8] into RDX (field ID), require both nonzero, and call JNI slot +0x488 = GetStaticObjectField. They retain the local result, call 0x41a560, then call JNI slot +0xa8 = NewGlobalRef with that local result. Nonzero-result gates precede publication into wrapper+0x20.

| Descriptor load | GetStaticObjectField | NewGlobalRef | Store of returned global reference |
|---|---|---|---|
| 3c70cb (+70) | 3c70ef | 3c7142 | 3c7195 → d34970 |
| 3c732b (+78) | 3c734f | 3c73a2 | 3c73ed → d34998 |
| 3c7574 (+80) | 3c759b | 3c75ee | 3c7639 → d349c0 |
| 3c77c0 (+88) | 3c77e7 | 3c783a | 3c7885 → d349e8 |
| 3c7a0c (+90) | 3c7a33 | 3c7a86 | 3c7ad1 → d34a10 |

Metadata-null branches leave this mainline for 3c9f38, 3c9fa7, 3ca016, 3ca085, 3ca0f4 respectively; their lazy-resolution details are outside this finite proof. Nonzero local/global object checks also lead to separate exceptional paths, so this static chain does not promise successful initialization. At 3c70b2..be a nonzero d355f1 bypasses this initialization block toward 3c80e9; this receipt does not derive the complete lifetime of that flag.

Wrapper replacement is ownership-aware: each publication first reads the former +0x20 reference; if nonzero, it invokes that wrapper's existing +0x18 cleanup callback, guarded by +0x10. The block then transfers replacement callback storage into wrapper offsets 0..0x18. Representative first-wrapper sequence is 3c718e..3c7249, with callback values formed from 326fc0 and 2aade0 at 3c715c..63. This does not retrace transitive collector behavior. Separate wrapper addresses do not prove distinct Java object identities; GetStaticObjectField values could alias.

## Finite remaining frontier

For exact names or literal labels, inspect existing metadata at *(d355b0)+{70,78,80,88,90}: descriptor[0] is the declaring class reference and descriptor[8] the static field ID. A preserved checkpoint may resolve their recorded identities without guest instructions. Reading wrapper Java-reference values alone is insufficient to infer field names or enum constants. No new callback execution was performed, and this report does not infer names from table order.

## Reproduction and limits

reproduce.py verifies the pinned original SO hash, extracts four source windows, hashes their bytes and six ELF relocation records, and hashes three prior receipts. It runs objdump on copied bytes only. Earlier receipts remain unchanged. No assets, target instructions, JVM, callbacks, CPUID guards or live Java references were executed. There is no whole-image absence claim and no observed runtime selection. All table alias findings derive from original relocations rather than a fixture's simulated successful backend.

[Evidence](NATIVE-ANIMATION-SELECTOR-PROVENANCE-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.

Later [exact static fields](NATIVE-LOOP-EASING-METADATA-2026-10-18.json) and [original class initializers](NATIVE-LOOP-EASING-INITIALIZERS-2026-10-18.json) join loop selectors1/2/3 to LOOP/PLAY_ONCE/HOLD_ON_LAST_FRAME. The [easing bootstrap join](NATIVE-KEYFRAME-EASING-JOIN-2026-10-18.json) joins selectors0/1 to the same linear factory and2 to Catmull. Index zero still uses each factory's transition branch; processor selection is not universally the current selector's resulting segment class.
