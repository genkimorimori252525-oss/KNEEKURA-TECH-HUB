# Model section M+0x178: three-map storage and immediate consumers

## Result

This section has a proven resource-like three-map structure. Its first binary-value map reaches a consumer that tests literal `vorbis` bytes; the second supplies a string to a Java-facing helper; the third becomes nested string/string Java-facing maps. No original evidence in this bounded slice identifies the aggregate as animation, controller or expression data. Those labels should remain unassigned.

All findings are original-byte static semantics. No target/JVM/native execution, assets, callback decoding or repository edits occurred. `evidence.json` lists authoritative source windows, ELF relocation records and hashes. Reproduction passed 15 windows and six exact RELATIVE targets.

## Root identity and schema

Let S=M+0x178. Constructor 424e08..424e0f stores d1c3d0 at M+178. Original ELF RELATIVE slot d1c3e0 (=table+10) targets 350570. Modern root 41f4a7..41f4b5 calls S's +10 slot before testing version 27 at 41f4b8; therefore this is shared by accepted modern versions 19..32, rather than only the >=27 vector branch.

350570 distinguishes reader byte+8==1 (input/deserialization established by prior reader cohort). In input mode it destroys existing nodes, zeros retained bucket entries, clears linked head/count, reads a 32-bit count through reader+10, and loops count times. Three consecutive maps are serialized; no section-specific version gate or explicit item-count cap appears in these loops. Prior reader+10 contract is variable-length unsigned32 with its documented noncanonical/overflow limitations. Reader+48 is length-prefixed string bytes, not independently validated UTF-8.

| Map | S bucket/count/head/size offsets | Root head | Node size | Per-entry input order and stored offsets |
|---|---|---|---|---|
|A|08/10/18/20|M+190|78|key string N+08; auxiliary string N+58; byte-buffer payload object N+30 (buffer N+38)|
|B|40/48/50/58|M+1c8|70|key string N+08; auxiliary string N+50; payload string N+30|
|C|78/80/88/90|M+200|90|key string N+08; auxiliary string N+70; nested string/string map object N+30|

The count/read-loop blocks are A:3507e6..3509f8, B:350697..3506d0 and 3509fd..350af1, C:350721..350761 and 350af6..350c9f. Other-mode branches traverse existing nodes and write the same ordering rather than allocating input entries. All map nodes have next pointer N+0. Strings use owned heap or inline storage, with pointer/length at the string base/+8 and inline storage at +10.

A payload: d1c2b8+10 RELATIVE ->34fa90, which tail-dispatches reader+58 on payload+8. For the established reader table d1d408, +58 RELATIVE ->4c4320. This reads length through reader+10, resizes the buffer via4c4aa0, stores logical length at buffer+18, requests that many stream bytes through stream+10, and advances reader+18 by the declared length after normal return. It does not inspect a separate status register; no failed-boolean assumption is made. Buffer getters d1d530+18/+20 resolve to2ba410/4c4a90: pointer buffer+8 and length buffer+18. Consequently A node owns data pointer N+40, capacity N+48 and length N+50. This is a byte-counted payload, with no schema/codec identity established by the reader alone.

C payload: d1c470+10 RELATIVE ->34fbe0. It calls34fc30 with two member-dispatch descriptors `{0x49,0}`; its odd-dispatch branch resolves these to reader virtual slot+48. Thus the nested payload is counted string-key/string-value entries, with 0x48-byte nodes, strings at nested-node+8/+28. No expression interpretation is established.

## Ownership and insertion

A insertion351c20, B351520 and C350d10 first call their lookup helpers and skip allocation when the returned existing-entry pointer is nonzero. The parser has already parsed the temporary entry, then cleans it up after insertion. This supports first-existing-value retention; the exact hash/equality helpers are not fully retraced here.

Successful insertion allocates exactly78/70/90 bytes. Heap string pointers transfer and the temporary strings reset to empty inline state; inline strings are copied. A moves the buffer pointer/capacity/length triple at351cf1..351d0a, clearing its temporary. C moves nested-map ownership at350ddc..350e7c, fixes inline bucket/sentinel linkage, then resets the temporary map. Therefore entries retain owned payloads rather than borrow the parser's temporary stack objects. The parser later frees any remaining temporary allocations. Destructor350460 frees C nodes and buckets, then invokes map destructors for B and A; the input reset paths show A buffer and all string cleanup directly.

## Nearest model consumer

36d8d8 saves incoming model pointer in R15. The established36d8c0 body subsequently walks these exact heads:

- A:36ff80 loads M+190;36ffb0 follows N+0. N+8 becomes a Java string via JNI+538 at36ffc8. N+50 affects mode/size branches at370023..370047. N+38 getters supply pointer and length to JNI+728 at370073 (NewDirectByteBuffer under the established JNI table contract). This exposes borrowed native bytes; it does not by itself prove Java copies them or safely retains them beyond native model destruction.
- A's immediate processing branch calls4d8730 at370177 and tests output/payload bytes against little-endian immediates0x62726f76 and0x7369 at370352..370368, corresponding to `vorbis` at offsets1..6. This is direct evidence of an audio-related recognition branch, not proof every payload is valid Vorbis or a complete codec identification. Construction branches use manager d35598+88 at3702c7/3704c1/370547/3705c9; exact Java class/member identity remains unresolved here. Results enter the first Java-facing map through d356e0+68 at3706b5..3706ec.
- B:370973 loads M+1c8;3709a0 follows N+0. Key N+8 becomes a Java string at3709b7. Payload pointer N+30 is passed to3742d0 at3709ef..370a03 with ECX=1. Helper3742d0 converts it through JNI+538, then calls via descriptor manager d355b0+48 at374327..37435c with that string and normalized flag. Result enters the second map via d356e0+68 at370a08..370a3f. No controller/expression semantics can be inferred from this unnamed Java method.
- C:370b92 loads M+200;370bd8 follows N+0;370bf6 converts outer key N+8.370caf loads nested head N+48.370cc0 follows nested next;370cd8 and370d17 convert nested strings+8/+28, then d356e0+68 receives each pair at370d5b..370d8d. The nested map is inserted under the outer key at370e80..370ebc. The outer auxiliary string N+70 is not consumed by this immediate conversion loop.

The three resulting object references (stack100,140,170) are passed together to d35598+80 via364a60 at370fa9..370fed. Exact Java constructor identity is a finite metadata frontier. The source aggregate remains native-model-owned; Java-facing conversion does not move its native map nodes. Full returned-object lifetime is outside this slice.

## Limits and next frontier

The strongest next step is exact original-JAR identity matching for d35598+80/+88 and d355b0+48, using already preserved metadata if available. This can name the three-map aggregate and the second map's string-to-object operation without tracing unrelated root sections. A separate bounded lifetime question is whether the Java constructor receiving A's direct buffer copies or retains native memory. Full4d8730 codec behavior, all size/mode branches, allocation failure, malicious counts and deeper Java execution are not established. No full asset decoder or animation schema is claimed.

Evidence: [NATIVE-MODEL-RESOURCE-SECTION-EVIDENCE-2026-10-18.json](NATIVE-MODEL-RESOURCE-SECTION-EVIDENCE-2026-10-18.json). The separate [exact Java identity receipt](NATIVE-RESOURCE-CONSUMER-METADATA-2026-10-18.json) closes the metadata slots left unresolved in this static cohort; semantic/ownership joins require the original Java evidence. Raw ranges/reproduction scripts remain external.

Later [Java bridge](NATIVE-RESOURCE-JAVA-BRIDGE-2026-10-18.md) joins the exact metadata to existing CommonAssetData/SoundData/MolangParser semantic evidence. Successful SoundData construction copies native buffer bytes; the Molang parser catching wrapper may return fallback, so normal return is not parse-success proof. Earlier unresolved-name wording above describes the static-only cohort.
