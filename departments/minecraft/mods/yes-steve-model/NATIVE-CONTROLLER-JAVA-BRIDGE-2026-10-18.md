# Bounded native → Java controller bridge

PRIMARY_STATIC_REVIEW_ONLY. No confidence promotion or independent semantic review. Original JAR SHA256 25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f; original SO SHA256 15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. Pinned source revision f184edabd1b5115ce5a24cb6d155ba5a669f5ba6 remains correspondence evidence, not recovered names or whole-artifact equivalence. Historical AnimationControllerInstance/AnimationPlayer source-divergence status is unchanged.

## Closed join

The previously proved native 365a10/366110 call sites now join exact metadata to original Java constructors. `controller-state-classfile-verified.json` is reused, without rerunning its callbacks. Our verification reads only original classfiles/source and existing receipts.

| Native manager d355b8 slot | Exact original Java owner, relative to com/elfmcys/yesstevemodel/ | Native → Java arguments |
|---|---|---|
| +38 | oo0o0o0o00000ooOoooo00o0 | Map constructor: controller-file map |
| +40 | ooOo0OoOoo0ooOOoOO0o000O | String initial state, O00ooo0OooOo00o0o0Oo00oO[] states |
| +48 | O00ooo0OooOo00o0o0Oo00oO | name, Pair[] animations, Pair[] transitions, String[] sounds, expression[] onEntry, expression[] onExit, blend object, boolean shortest-path |
| +50 | OoooOo0OOOoOOoOOooOOoO00 | formal Java (F)V scalar |
| +58 | o0o00oo00Oo0oo00ooOO0ooo | ([F[F)V: first float array time, second position |
| +60 | org/apache/commons/lang3/tuple/Pair (absolute owner) | static of(Object,Object):Pair; pinned commons-lang3 3.12.0 receipt reused |

State native offsets are C+8 animations, +20 transitions, +38 sounds, +50 onEntry, +68 onExit, +80 blend, +c0 boolean. Native construction at 3676d8 places these in the Java argument order above. Wire order differs: animations, transitions, onEntry, onExit, blend, boolean, then sounds only for version >=28. Blend uses legacy scalar before version15. See preserved wire report for exact primitive calls and branch addresses.

## Duplicate and ownership boundaries

The native controller tree and state hash map first parse the entire incoming key/value, then retain the existing entry on an equal raw key. Native state equality lookup at 34e543/34e551 precedes rejected-temporary cleanup; controller-tree skip is 34f1aa. Thus equal raw duplicates can disappear before Java construction. States are traversed in native hash-chain order, not promised wire or lexical order.

Original Java controller-data constructor pools the initial-state string at bytecode6. At18..45 it streams the states array, uses pooled-state-name and identity functions, calls two-argument Collectors.toMap at31 with no merge function, then constructs an Int2ReferenceOpenHashMap and unmodifiable wrapper. Duplicate pooled keys reaching this Java collection step follow its duplicate-key rejection. This does not mean every duplicate in the wire reaches Java, or establish a concrete raw-to-pooled collision case. No initial-state membership check appears in this constructor.

Original state constructor retains its name and pools it. It wraps animations/sounds/onEntry/onExit arrays with ReferenceArrayList.wrap then unmodifiable views (64/67,116/119,128/131,140/143). These wrappers do not deep-copy the backing arrays or expression objects. Transitions instead pass through stream mapping and a new array: the synthetic pair mapper pools the destination key and creates IntReferenceImmutablePair retaining the existing expression reference. The blend object and boolean are directly stored at152/158. State objects are retained in the new controller map. The controller-file Map constructor shallow-copies into Object2ReferenceOpenHashMap at10, then exposes an unmodifiable map at13. Native temporary ownership and JNI local-reference release do not imply deep Java immutability or whole-path exception safety.

## Three independently preserved arithmetic facts

1. Native scalar float at C+88, or zero for the empty non-scalar tree branch, reaches d355b8+50. Its formal Java constructor is (F)V. The native cvtss2sd before NewObjectV is C variadic promotion; it does not change the formal Java parameter to double. Original Java bytecodes5..9 load the float, load20.0F, fmul at8, then store the result. Its length getter returns that stored float.
2. Native nonempty blend tree passes node+20 keys as the first float array and node+24 values as the second, in tree order. Java ([F[F)V uses adjacent first-array elements, multiplies both by20 at39/48, complements adjacent second-array elements as1-position at54/62, and constructs time.length-1 segment objects. It owns the new segment list rather than retaining the two input arrays as its representation. Its length getter delegates to the searcher's cached right bound, as separately established by ORDERED-SEGMENT-TRANSITION; this pass does not reopen search algorithms.
3. The separately documented player owner OOOO0o0oo0o000oOOooOoOo0, method oooooooOOoOOoO00OooOo00O()F, calls interface length at4, loads20.0F at9, and fmul at11. This is another multiplication, not division. For the scalar implementation given1.0F, the local arithmetic is20.0F stored/returned, then400.0F from that player getter. No native wire-unit assumption, compensating factor, intended-unit inference, runtime measurement, or runtime-defect conclusion is introduced.

## Parser and JNI caveats retained

All four native controller expression call paths use flag false with helper3742d0. Animation pairs with an empty expression string skip parsing and keep null; transition conditions and onEntry/onExit strings take the catching facade. The already verified facade calls its unsafe sibling, catches Exception, logs and returns fallback. A normal JNI return is not parse-success or evaluation proof, and this pass assigns no undocumented meaning to false.

The separate collection checkpoint proves d356e0+68 is HashMap.put(Object,Object):Object. Original helper364af0 nevertheless invokes JNI CallVoidMethodV slot1f0. These are distinct proven facts. Neither changing the recorded call family nor claiming successful execution/ABI defect is justified here. d356e0+60 is HashMap.<init>()V; +78 identifies String for array construction.

## Verification and remaining boundary

verify.py independently reparses 12 selected original Java methods, compares complete instruction/operand/code-hash/access/exception records with the three frozen dossiers, verifies relevant bootstrap records, checks four metadata owner class hashes/signatures, verifies six actual pinned source files and revision, and checks original SO/JAR hashes. Result:83 checks passed,3 narrow corruption controls rejected,0 failures. This is a bounded integrity/correspondence recheck, not an independent semantic review or new runtime test. Exact method records, source records and hashed prior evidence links are in evidence.json.

No new callback, target JVM, native execution, assets, repository edit, or confidence promotion occurred. Remaining finite boundaries are exceptional native/JNI ownership and malformed-input behavior, raw-string conversion/pool collision reachability, and actual downstream runtime timing/evaluation. They are not prerequisites for the constructor/argument/ownership bridge closed here.

[Evidence](NATIVE-CONTROLLER-JAVA-BRIDGE-2026-10-18.json). Full raw extraction artifacts and reproduction scripts remain external. This report does not promote the central map or prove actual runtime success.
