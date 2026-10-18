# Model root compatibility conversion for versions19..26

## Result

The remaining root-version gap is a string-keyed-map compatibility representation. 0x41fc70 deserializes maps whose values are the same0x348 entry type used by the newer root. It moves the entries into common model vectors and copies each map key into that entry's identifier-string vector. Geometry remains at entry+0x28 and uses the shared0x347dd0→0x348550 parsers.

Exact version split:

-19..20: one map, appended to model+0x148/+0x150/+0x158.
-21..26: that map first, then a second map appended to model+0x160/+0x168/+0x170.
->=27, per the completed modern receipt: direct counted vectors, +0x160 first and +0x148 second.
-<=18, per the completed legacy receipt: a separate legacy root with integer-keyed optional geometry and conversion into the same model shape.

These are different serialized representations. Shared destination types do not establish wire compatibility.

This report is static original-byte analysis only. No original target/JVM, assets or repository files were executed/read/modified respectively. evidence.json pins the original image, authoritative code windows and backing hashes. Earlier receipts remain unchanged. Exploratory address-named excerpts are not additional whole-function proofs.

## Dispatch and common continuation

The upstream binary reader selects0x41f490 only for versions>18. Inside that parser, root+0x178 is handled first; comparison at0x41f4b8 branches to0x41fc32 for version<27. That branch calls0x41fc70 with the same model and reader and returns to the shared continuation0x41f584. This helper does not allocate a separate root model; it modifies the already constructed0x5d0 model. No independent input-version validation is attributed to the helper itself.

## First map: versions19..26

In read mode1,0x41fc70 initializes a temporary hash header at stack+0x28. Header buckets/count/head/size are stack+0x28/+0x30/+0x38/+0x40.0x41fcdf reads a base128 uint32 count via reader+0x10. Each entry initializes an owned string key and temporary0x348 entry, reads the key through reader+0x48 at0x42030c, then calls0x424920 at0x42031a.

Lookup compares byte lengths and byte equality through0xd14780, whose original ELF import chain resolves to bcmp. A matching key branches to0x420748, which destroys the newly parsed temporary entry and key without replacing the old value. Thus the shown read loop keeps the first encountered equal key; duplicate values still must be parsed before being discarded. This is not a skip-over of their encoded bytes.

A new map node allocation is0x370 bytes at0x420409. Node+0 is next, node+8/+0x10 stores key pointer/length with inline storage+0x18, and node+0x28 stores the0x348 entry.0x420518 calls0x4240e0 to move the parsed temporary entry into the node. After insertion, the temporary is destroyed at0x420750. Hash-table resizing and linking are visible; no portable hash algorithm or deterministic serialized-order preservation is claimed.

After all input entries,0x41fced enumerates the linked nodes.0x41fd38 supplies node+0x28 to0x4240e0, appending to the vector with begin/end/capacity M+0x148/+0x150/+0x158. The in-capacity branch advances end by0x348 at0x41fd58..0x41fd60; capacity growth delegates to0x424780.

The helper then appends a copy of node's key to the new entry's identifier vector E+8/+0x10/+0x18. The pointer calculation uses newEnd−0x340=E+8. The in-capacity string path0x41fdaa..0x41fe02 allocates if needed, copies length+1 including terminator, writes length and advances identifier end by0x20. The growth branch uses0x337980 with key pointer/length. In this version range,0x424920 does not deserialize an identifier vector itself: its version>=27 tail is skipped, as shown at0x4249f4..0x424a17. Therefore the map key supplies the identifier in this compatibility path.

Map-node iteration follows next pointers at0x41fd27. This is temporary hash linked-list order, not a proven preservation of source wire order or lexicographic ordering.

## Second map: only versions21..26

After destroying first-map storage,0x41fe41 compares reader.version against20 and returns for <=20. For>20 it initializes another temporary map, reads count at0x41fe9b, key at0x4209fc and value through0x424920 at0x420a0a. Its corresponding insertion/duplicate/cleanup block extends through0x420e65.

Conversion0x41ff38..0x41ff60 appends to M+0x160/+0x168/+0x170, again at stride0x348, then appends the map key to each new entry's identifier vector. This map is absent from this helper's19..20 read path; in the established newly constructed-model pipeline its corresponding destination remains at constructor state. The helper's general behavior on arbitrary prepopulated model objects is not asserted.

The wire ordering is thus +0x148 map before +0x160 map, unlike >=27's direct-vector order. This difference is material for reuse of a root deserializer.

## Geometry ownership join

0x4240e0 is an entry move constructor, not a deep bone-copy parser. Its prefix:

- Copies identifier vector E+8/+0x10/+0x18 and zeros the source vector at0x4240f5..0x424113.
- Installs wrapper vtable d1cb50 at E+0x20 and geometry vtable d1cb78 at E+0x28.
- Copies geometry's bone vector E+0x30/+0x38/+0x40 and zeros the source pointers at0x42412a..0x424145.
- Transfers or inline-copies the adjacent property string at E+0x50, resets the old string, copies scalar property storage and moves the property-array pointers. Deeper optional sections are left bounded.

The same helper performs temporary→map-node and map-node→model-vector transfers. After model conversion, temporary node entries are destroyed by0x3462c0, keys are freed if non-inline, and nodes freed with size0x370 (first map0x41fee9..0x41ff08; second0x4200a0..0x4200d4). Source bone-vector pointers have been cleared before those destructors, while the model entry owns the transferred vector. Full exception unwinding and all nested aliasing contracts remain unresolved.

0x424920 invokes the geometry at E+0x28 through its virtual+0x10 at0x4249e6..0x4249f1. Original relocation d1cb88→0x347dd0 proves the join to the existing common geometry/bone contract. No re-scaling or reinterpretation of bone fields is visible in the move prefix. Existing downstream geometry uses the common source shape; the exact runtime selection of a particular entry is outside this root-conversion slice.

## Limits and stopping point

Entry optional fields retain internal gates (for example>=22 and>=23 in0x424920), but their full schemas are already bounded by the modern report and are not expanded here. Nothing establishes successful scheduling, a real loaded model, complete exception cleanup, canonical identifiers, or all field semantics. Root dispatch/conversion is now covered for accepted1..18,19..20,21..26 and>=27; any further work should follow an exact geometry-selection or named optional-field question rather than expand the asset format generally.

reproduce.py verifies7 source windows,3 original ELF relocations and the bcmp import chain, linking all three preceding version/source receipts. It runs only authored Python and objdump.

Evidence: [NATIVE-MODEL-V19-26-EVIDENCE-2026-10-18.json](NATIVE-MODEL-V19-26-EVIDENCE-2026-10-18.json). Related [modern schema](NATIVE-MODERN-MODEL-SCHEMA-RECOVERY-2026-10-18.md), [legacy schema](NATIVE-LEGACY-MODEL-SCHEMA-RECOVERY-2026-10-18.md) and [framed source input](NATIVE-SOURCE-ACQUISITION-RECOVERY-2026-10-18.md). Raw evidence remains external.
