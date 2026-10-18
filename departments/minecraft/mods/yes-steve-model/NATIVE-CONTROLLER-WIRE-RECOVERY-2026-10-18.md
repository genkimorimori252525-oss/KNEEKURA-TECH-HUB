# Controller wire-to-construction join

Static original-byte review only. SO SHA-256 `15d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22`; JAR SHA-256 `25b5e902b96f4c298690208f8b433cbc31737c23f87590354dbd86f00207bc8f`. No target, emulation, JVM, assets, installers or repository edits. `reproduce.py` verifies the original inputs unchanged, extracts six windows, and independently verifies five ELF RELATIVE slot-to-body records; `evidence.json` hashes these and prior receipts. No independent semantic review or central promotion.

## Compact wire schema

Reader R input mode is byte R+8 ==1, version is unsigned dword R+0xc. Primitive slot identities inherit the modern-schema receipts: virtual+0x10 count/var32, +0x28 float, +0x40 boolean-byte, +0x48 owned string. These are binary-reader fields, not proof of JSON parsing.

For file payload F passed to365a10:

1. Count at34ed2c.
2. Repeat: controller key string at34ede7; controller value P through virtual d1cf60→34e310 at34edfe.
3. P begins with initial-state string P+8 (34e331), then state count (34e38c), then repeated state-name string (34e522) and state C via d1cf88→34d1e0 (34e532).
4. Each C reads, in wire order:
   - Count + pairs of owned strings into C+8 vector, stride0x48. Pair strings are element+8 and+0x28 (34d241,34d4c9,34d4d8).
   - Count + pairs of owned strings into C+0x20 vector, same stride/fields (34d291,34d909,34d918).
   - Counted owned-string vector C+0x50, stride0x20, via346ba0 (34d2a6).
   - Counted owned-string vector C+0x68, stride0x20, via346ba0 (34d2b2).
   - Blend representation: version<15 reads one float into C+0x88 and sets byte C+0x8c=1; version>=15 reads tagged blend object C+0x80 through d1cfb0→34cd90.
   - Boolean byte C+0xc0 via reader+0x40 (34d3f3).
   - Only version>=28: count + single-string records into C+0x38 vector, stride0x28, string element+8 (34d3f6,34d441,34dda1).

In the construction correspondence established previously, these are animation pairs, transition pairs, onEntry strings, onExit strings, blend data, shortest-path boolean and sound names. Sound names appear **last on the wire but third of the five Java array arguments**. Exact constructor owner decoding is handled separately; this report keeps the actual offsets authoritative.

## Native container layouts and duplicates

F's ordered-tree header has sentinel+0x10, root+0x18, first+0x20, last+0x28, count+0x30. 34ecd0 destroys previous root34ca40, resets the header, then reads entries. Each allocated tree node is0xa0 bytes (34ef00): tree links/color before+0x20, controller key owned string+0x20, P at+0x40. Thus P+8 appears as node+0x48 and its state map starts node+0x68.

Key/value are both read before controller-key lookup. Comparisons inspect key bytes and lengths (34ee63..34eef3); an existing equal key branches34f1aa without replacing the old value. A new key allocates a node, moves/copies string ownership, transfers the P state-map header and fixes its sentinel bucket pointer (34efe9..34f0ee), then inserts with2ba6d0 and increments F+0x30. Temporary cleanup follows either outcome. Duplicate input keys consume their entire values but the first retained controller survives. This is distinct from a last-wins policy.

P's states are a string-key **hash map**, not an authored-order list: buckets P+0x28, bucket count+0x30, global chain head+0x38, size+0x40; auxiliary hash policy and single-bucket storage occupy later offsets. State nodes are0xf8 bytes: next+0, owned key+8 (length+0x10, inline+0x18), C+0x28, cached hash+0xf0. 34e310 destroys prior nodes (34e3c5: state destructor34cb50, key cleanup, node free), zeroes buckets/head/size, reads state count, and parses each complete temporary before lookup34e8d0 at34e543.

Occupied lookup result at stack+0x120 makes34e551 skip allocation/insertion to34e852 temporary cleanup. Lookup compares matching lengths and byte equality, either via chain for small map size or hash/bucket for larger maps (34e8d0..34eaf0). Equal raw state names retain the first parsed value. New nodes transfer all five vector triples and zero temporary triples (34e5e3..34e69d), move blend tree with root-parent repair (34e6c2..34e758), and copy C+0xc0 (34e75e). Chain insertion and count increment are34e7d0..34e83c.

Consequently366110's P+0x38 linked traversal gives **hash-chain order**, not wire insertion order or lexical order. Also, Java Collectors.toMap duplicate rejection does not mean every duplicate wire state reaches that constructor: equal native raw keys were already discarded. This report does not infer pooled-name collision behavior.

## Blend tag and version boundary

For version<15,34d38a..34d3e1 reads one float, marks scalar, destroys/reset the blend tree. For version>=15, d1cfb0→34cd90 reads a var32 tag at34cdb9:

- Exactly1: set scalar flag1, initialize scalar to0, then read float into blend+8 = C+0x88 (34cdc7..34cdfd).
- Every non-one input tag: normalize scalar flag to0 at34cf52 and use counted float-pair tree; unknown tags are **not rejected by this immediate reader**.
- Tree input destroys previous root, resets sentinel/count, reads count (34ce45), then first and second float (34ce88/34ce96). Allocated node size0x28; first float node+0x20, second+0x24 (34cef0/34cefb). Tree ordering compares the first float. Existing equal ordinary finite keys skip insertion, retaining the first pair (34cecc..34ced5). No finite/NaN check is present in this slice; do not generalize comparator behavior to a valid ordering of NaNs.

C blend layout: vtable+0x80, scalar+0x88, scalar flag+0x8c, tree sentinel+0x98/root+0xa0/first+0xa8/last+0xb0/count+0xb8. It joins exactly to366110's scalar/paired-array/empty-to-zero constructor branches. Paired float arrays therefore represent native key-ordered tree iteration, not arbitrary wire pair order. No interpolation formula or expression evaluation is established.

For version<28, the reader returns at34d44f before sound-vector clearing/reading. In this **fresh parsed-state path**,34e49a..34e4c6 initialized all five vector triples to zero, so older input yields an empty sound array downstream. Do not claim34d1e0 globally clears preexisting sounds when called on a reused state with an older version; the early-return branch itself does not.

P's temporary initial string is initialized to literal `default` at34ed94..34edaa, then34e331 unconditionally reads the wire string over it. This is initialization evidence, not a fallback for missing or empty input.

## Ownership and construction join

Pair records own two strings; the virtual leaf d1cfd8→34e180 serializes them in +8 then+0x28 order. Sound records own one string, d1d000→34e0c0. 346ba0 clears prior owned strings, reads count, appends0x20-byte strings with inline-copy/heap-transfer branches; input order is retained inside vectors. Vector growth/cleanup is visible, but comprehensive exception safety is not claimed.

The wire-owned C feeds the existing368de0 temporary copy and366110 conversion. Both pair vectors become static-factory Java pairs: first pair category parses its second string only when length+0x30 is nonzero; second pair category parses unconditionally. Entry/exit strings also parse unconditionally; sound strings do not call the parser. All four parser calls pass flag0 to3742d0. Its exact original Java facade catches Exception and may return fallback, so normal return is not parse success and no evaluation is proved. The final controller/file construction and Java shallow-copy/view distinctions remain as documented by the construction receipt.

## Closed seam and remaining frontier

Closed: counted controller-key tree → initial-state string/state hash map → five field vectors, versioned blend, boolean → documented366110 argument offsets. Read order, version15/28 gates, native equal-key suppression, and owned transfer-versus-Java-local-reference boundaries are now explicit.

Remaining after the supplemental identity join below: full exceptional ownership validation, malformed UTF/count/NaN behavior, and downstream transition/interpolation/evaluation semantics. None requires expanding root codecs or loading assets. The immediate controller/state wire schema itself has no unresolved nested field parser after these bounded leaves.

## Supplemental exact identities and ABI refinement

Received after the bounded wire analysis: `../controller-state-classfile-verified.json`, SHA-256 `00ea3532db7f0b6408b8e55fc21b3d773ada069699b85a64974b0c8d48769a61`, independently joins five guarded modeled metadata callback results to exact original classfiles/dependency. This wire work only reads that receipt; it runs no callbacks. It closes the earlier construction report's provisional identity frontier without rewriting that historical report:

- d355b8+0x40: `com/elfmcys/yesstevemodel/ooOo0OoOoo0ooOOoOO0o000O.<init>(String,O00ooo0OooOo00o0o0Oo00oO[])V`.
- d355b8+0x48: `com/elfmcys/yesstevemodel/O00ooo0OooOo00o0o0Oo00oO.<init>` with String, Pair[], Pair[], String[], expression[], expression[], blend-base, boolean. Full obfuscated descriptor is preserved in the receipt.
- d355b8+0x50: `com/elfmcys/yesstevemodel/OoooOo0OOOoOOoOOooOOoO00.<init>(F)V`. The formal Java parameter is **float**, not double. Native cvtss2sd and zero-in-XMM0 are C variadic argument promotion into NewObjectV, not a double-valued Java field/constructor. Earlier construction wording describing the native double register representation must not be read as a Java signature.
- d355b8+0x58: `com/elfmcys/yesstevemodel/o0o00oo00Oo0oo00ooOO0ooo.<init>([F[F)V`.
- d355b8+0x60: static `org/apache/commons/lang3/tuple/Pair.of(Object,Object):Pair`, classfile-verified against pinned commons-lang3 3.12.0. It also supplies the Pair array element class.

`../java-collection-checkpoint-proof.json`, SHA-256 `92881115933bfed72990b8d7cacf44e6d5231961fd64520c2f7735e06f20eccb`, is a zero-instruction read of an existing modeled checkpoint plus exact declared java.base classfiles. It identifies d356e0+0x60 as HashMap.<init>()V; +0x68 as HashMap.put(Object,Object):Object; +0x78 as String.<init>()V, whose owner class is used for the sound string array.

The decoded +0x68 method **is HashMap.put**, refining the earlier conservative unknown-name statement. The original native call helper still uses JNI **CallVoidMethodV**, despite the decoded return descriptor Object. Both are evidence facts; this static analysis proves neither runtime correctness nor a reproduced defect. Do not change the call-family record to CallObjectMethodV to make it fit the descriptor.

[Evidence](NATIVE-CONTROLLER-WIRE-EVIDENCE-2026-10-18.json). Raw binary excerpts and reproduction scripts remain external. Read the [current reuse guide](NATIVE-REUSE-GUIDE-2026-10-18.md) for later metadata/Java refinements to this static cohort.
