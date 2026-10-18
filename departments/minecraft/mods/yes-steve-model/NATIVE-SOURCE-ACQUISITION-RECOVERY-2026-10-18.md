# Resource source acquisition to borrowed geometry input

## Findings

The distinct 0x38-stride resource collection supplies a path, not the model bytes directly. The deferred worker copies that path, combines it with a retained base path, reads the resulting regular file in `rb` mode into a reusable buffer, and passes the buffer into binary frame reader 0x41db40. That reader produces the model pointer later passed to 0x36d8c0. The modern model allocation is 0x5d0 bytes. The worker destroys and frees it after the geometry work; the geometry call receives a borrowed model pointer. This does not establish that every nested field is independently owned or that downstream geometry retains no aliases.

All claims are static original-byte claims. No original assets, file opens, decoder executions, JVM executions or repository edits were performed. The authoritative code windows, ELF backing offsets and SHA256 values are in evidence.json; exploratory address-named windows are not additional whole-function claims. Earlier receipts remain unchanged.

## Distinct resource collection and path ownership

At 0x35d261..0x35d277, the task capture supplies a retained context, start index and end index. The worker checks its index against the end and checks cancellation byte d338c8 before processing (0x35d2cd and 0x35d310). At 0x35d31f..0x35d33c it obtains collection base through context+0, computes index*0x38, and reads record+0x18 pointer and +0x20 length. Record+8/+0x10 later supply two 64-bit values. This collection is not the selector3 package's 0x48-stride vector.

0x35c9c0 constructs a temporary at worker stack+0x10: pointer at+0, length at+8, inline storage/capacity at+0x10, auxiliary path representation at+0x20. It rejects a null source with nonzero length, copies exactly length bytes, and appends a NUL. Lengths >=16 allocate length+1; smaller strings use inline storage. It initializes the auxiliary representation through 0x318dd0 and 0x3196a0. These are path-object operations, not file contents parsing.

0x35caa0 receives output at stack+0xa8, borrowed base object context+8, and the temporary path. It copies the base string including terminator, copies the base's auxiliary representation via 0x31c410, then calls 0x31cc30 with the copied destination and temporary path. The inspected combine prefix can replace via 0x31ca70 or append components via 0x2fc030; it is not sound to describe this as unconditional string concatenation. Absolute-path handling, normalization and confinement require a separate full path-helper analysis. The original temporary is destroyed immediately at 0x35d35c..0x35d390; the combined object survives file acquisition and is destroyed at 0x35dcd2..0x35dd18. The source record's original path bytes remain borrowed.

## File size, open and exact read boundary

0x4e0060 receives the combined path and destination buffer object. 0x310e10 calls 0x310cd0, whose original import chain resolves to __xstat. It reads the path's first pointer, requires stat mode `(mode & 0xf000)==0x8000`, and returns the size field. Errors/nonregular files route through the error-code wrapper. No actual filesystem state was queried by this research.

0x4e007e rejects sizes >=0x4200001, hence the accepted requested size is at most 0x4200000 (69,206,016 bytes). The stream open at 0x4e00c6 passes mode12. Original mode jump-table entry 0x54354 selects 0x2baf48, returning literal `rb` at 0x42799; 0x2bafd0 reaches original fopen through the two-stage import chain. The close helper reaches fclose. Import metadata identifies the original ELF symbols, not observed installed bindings.

The worker's destination is a lazily initialized reusable buffer at TLS-object+0x138 (0x35e020..0x35e05d), vtable d1d530. Its layout is data pointer+8, capacity+0x10, logical length+0x18. 0x4c4aa0 reserves owned storage, allocating or growing it; 0x4e00f8 sets logical length to the stat size. 0x4e0110..0x4e0135 repeatedly reads into data+accumulated with remaining size; nonpositive gcount exits. It closes the stream and requires accumulated==expected at 0x4e0161; a short read throws. File growth beyond the earlier size is not checked by a second stat or extra-byte probe. Exceptions and file changes are not equivalent to a successful stable snapshot.

0x35d3b5..0x35d3c7 calls buffer virtual +0x18/+0x20. Original relocations d1d548→0x2ba410 and d1d550→0x4c4a90 prove these return buffer+8 and buffer+0x18. File bytes remain owned by the reusable buffer; 0x41db40 borrows them during synchronous parsing.

## Binary framing and exact model handoff

Call 0x35d3f6 passes:

- RDI: address of model-output pointer at stack+0xa0.
- RSI/RDX: loaded file bytes and logical length.
- RCX/R8: material pointer and length, loaded from the retained context+0x10 object.
- R9 and stack argument7: resource record+8 and +0x10.
- Stack argument8: uint32 from context+0x18.

0x41db56 first requires length>0x100, before its footer load. It loads the final8 bytes, hashes the preceding length−8 bytes with 0x573dd0 and seed f346451e53a22261, XORs that result with the two resource values, and compares to the footer. This is an exact comparison formula, not proof of cryptographic authentication. File+0 fixed uint32 must equal1. File+4 fixed uint32 must be within1..32; a match in the d35c58 registry also routes to rejection. No names for those registry entries are assigned.

At 0x41dcf6..0x41dd21 a raw stream borrows data+8 and is assigned length N−8, position0. Preserve this literal transition: it does not simply advertise N−16. For versions>=30 it consumes a byte and compares it against the low byte of argument8. It then constructs the known transformed stream through 0x4dc3a0 and generated-word XOR wrapper, followed by 0x4dd7f0. The ordering here differs from the shared selector decoder. Intermediate stream semantics, truncation behavior and full framing are outside this cohort.

0x41def1 obtains two bytes, masks the value to10 bits and consumes that many further bytes, then constructs the reader at stack+0x28: vtable d1d408, readmode1 at+8, fixed-header version at+c, buffered stream pointer at+0x10. This is a binary reader interface; the current parser entry 0x41f490 invokes reader virtual+0x10 at 0x41f516, whose ELF target is the already-proven base128 uint32 reader 0x4c39e0. These operations establish binary structured input on the modern path. They do not prove that no nested field later contains text or JSON.

Version<=18 calls legacy 0x425190 with the output address. Version>18 allocates0x5d0, zeroes it, calls 0x424db0, stores the new pointer through output at 0x41dfab, then calls modern parser0x41f490. Publication precedes parser completion, so output being nonnull is not a standalone success indicator. Normal return cleans temporary streams/generator state; the model survives to the caller. Full exceptional cleanup is not asserted.

At 0x35d500..0x35d511, a matched package 0x48-record's boolean+0x41 is copied into model+0x5c9. The worker loads the produced pointer at0x35d51e, passes it as RDX at0x35d548 into0x36d8c0, then eventually calls model destructor0x345030 at0x35dcc0 and frees0x5d0 at0x35dccd. Cancellation after parsing routes to the same visible cleanup site. This proves a bounded ownership interval for the top-level model, not all transitive error/cancellation paths or field aliasing.

## Next frontier and stopping point

The most useful next scope is modern parser0x41f490 plus constructor0x424db0, restricted to fields consumed by0x36a6e0 and0x375e30. Its schema requires a separate bounded trace. Legacy parser0x425190 is a distinct version<=18 frontier. No full resource decoder, decryption tool, asset extraction, or model schema beyond the proven entry/interface was produced here.

Run reproduce.py to verify/recreate17 pinned source windows,4 original ELF import chains,3 relocations and the `rb` mode mapping. No target code is executed by that verifier.

Evidence: [NATIVE-SOURCE-ACQUISITION-EVIDENCE-2026-10-18.json](NATIVE-SOURCE-ACQUISITION-EVIDENCE-2026-10-18.json). Related [selector3 package contract](NATIVE-SELECTOR3-SCHEMA-RECOVERY-2026-10-18.md) and [geometry construction](NATIVE-GEOMETRY-BUILD-RECOVERY-2026-10-18.md). Raw evidence and reproduction scripts remain external.
