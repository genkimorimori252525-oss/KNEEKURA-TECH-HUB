# Legacy model root conversion, accepted versions 1..18

## Result and boundary

0x425190 uses a separate legacy temporary root and converts it into the same 0x5d0 model shape constructed by0x424db0. It does not simply invoke the modern root parser with a smaller version. The nearest geometry and bone parsers are shared: legacy optional geometry reader0x436db0 calls0x347dd0, which calls bone reader0x348550, exactly the modern geometry route. The bounded difference is legacy root organization and conversion/ownership, not a proven alternate bone-record layout.

Only original ELF bytes were parsed/disassembled. No target, JVM, original asset, backend test or repository mutation occurred. evidence.json is the authoritative selection of aligned code ranges, ELF backing offsets, hashes and relocations. Address-named exploratory excerpts can contain neighboring or partially decoded instructions; no claims rely on their arbitrary endpoints. Prior receipts are unchanged.

## Root and ownership phases

The upstream0x41db40 reader dispatches accepted versions<=18 to0x425190; the previous source-acquisition report pins the length, header/version and rejection-registry gates. Acceptance still depends on those gates and all later parsing. Version19..26 is a different0x41fc70 modern-root conversion frontier and is not included here.

Let L denote0x425190's stack+0x8d8 temporary. At0x4251a9 it installs vtable d1c218 and initializes embedded containers and optional members. It calls0x42b970(L,reader) at0x425439. Only after that deserializer returns normally does it allocate0x5d0 at0x425443, zero it, call0x424db0 and store the new model pointer M through the caller's output at0x425467. Conversion then continues, so the published pointer alone does not prove successful completion. 0x421c60 initializes the optional aggregate at M+8; its presence flag is set at aggregate+0x138. All exceptional output cleanup remains outside this bounded audit.

### Proven prefix of legacy root serialization

- L+8/+0x10/+0x18 is a begin/end/capacity vector of uint32 elements. 0x42b9c8 reads its count through reader+0x10;0x42ba1b reads each element through the same method. In read mode, prior logical contents are cleared and elements appended at stride4. Capacity growth is explicit. No semantic name is assigned to these integers.
- L+0x20 is an integer-keyed hash-map header: buckets+0x20, bucket count+0x28, linked head+0x30, entry count+0x38. The map's count is read at0x42bb15. Each entry key is read at0x42bba1, followed by0x436db0 for its optional geometry value at0x42bbaf.
- A new map node is0x1c0 bytes (0x42bc7b), key at node+8 and geometry at node+0x10. Presence is node+0x1b8. The geometry's bone-vector pointers from the temporary value are moved into node+0x18/+0x20/+0x28, and the temporary is zeroed at0x42bca8..0x42bce4. These bytes are pointers and ownership state, not embedded bone contents.

The remaining root containers and version gates are substantial and deliberately left unresolved. This is a reusable prefix plus geometry route, not the full legacy schema.

## Shared geometry and bone input contract

0x436db0 reads a uint32 discriminator via reader+0x10. Only discriminator1 constructs/deserializes a present geometry. It first clears any existing present value, initializes vtable d1cb78, vector begin/end/capacity at geometry+8/+0x10/+0x18 and property state, sets presence+0x1a8, then calls0x347dd0 at0x436ebb. Other discriminator values leave/reset absence; no stricter0-or1 validation is claimed for this optional-value discriminator.

0x347dd0 clears old0x80 bone entries in read mode, reads their count through reader+0x10 and calls0x348550 for each entry at0x347f5f. After the bone vector it invokes the embedded properties parser at geometry+0x20 through virtual+0x10. Original relocation d1cb88→347dd0 and d1cdb8→348550 anchors the shared types. Modern report independently resolves the same property parser and its float32-to-double storage; those results are linked rather than rederived here.

The directly proven0x348550 bone field sequence is:

1. Byte string into B+8 via reader+0x48, matching the established parent-name storage.
2. Counted nested vector B+0x28/+0x30/+0x38, stride0x28, records parsed by0x3489f0. Its deeper schema is not expanded.
3. Byte string into B+0x40 via reader+0x48, matching the established bone-name storage.
4. Five validated byte booleans B+0x60,+0x61,+0x62,+0x63,+0x64 via reader+0x40.
5. Six fields B+0x68,+0x6c,+0x70,+0x74,+0x78,+0x7c via reader+0x28. The linked modern receipt resolves these as float32. Existing geometry receipt identifies their pivot/rotation use.

No version load/check appears in this immediate field sequence. This does not prove invariance of0x3489f0, all property fields, or every deeper version-dependent structure. Bone ownership, name strings and source ordering then enter the already-proven hierarchy producer, which establishes its own order independently of serialized order.

## Conversion into common model shape

The converter iterates L+0x30's linked map nodes beginning0x425476. It examines each node's integer key at+8. Tags are kept numeric; only the literal synthesized identifier below is named.

### Key3: a modern0x348 entry with literal identifier

0x4254cf tests key3. This branch appends a freshly initialized0x348 entry E to M's vector at+0x148/+0x150/+0x158. The in-capacity case initializes E and advances end by0x348 at0x4256c0..0x4256cf; growth delegates to0x432100 at0x425784. It inserts the original literal `arrow` into E's first string-vector field, with literal stores at0x4257c2/0x4257cb and length5 at0x4257d3. This is an exact string, not a guessed category name.

The source geometry's bone-vector pointers at old node+0x18/+0x20/+0x28 are copied into a temporary geometry and cleared in the old node at0x425a1d..0x425a3e. Later0x426e84 computes destination `(saved new end)-0x328`, i.e. E+0x20, and calls0x432460. That wrapper contains geometry at+8, so the destination geometry is E+0x28, matching the modern entry layout.

0x432460 specifically moves source wrapper+0x10/+0x18/+0x20 into destination wrapper+0x10/+0x18/+0x20, zeros source vector pointers, and destroys/frees the destination's old0x80-stride bone vector. It then delegates property movement at wrapper+0x28 to0x436750. Thus the bone allocation is transferred; bone coordinates are not visibly rescaled or reparsed by this move helper. Full string/controller/property conversion remains a separate frontier.

### Other keys: normalized integer map in M+0x10

The non-key3 path records `(source key==2)` at0x4256f3 and derives destination key `1+(source key==2)` at0x426497..0x42649f. Therefore inspected key2 maps to2, while other non3 values map to1. No claim is made that every numeric input tag is valid or meaningful elsewhere.

The converter searches the map rooted at M+0x10. New nodes are0x1e0 bytes at0x426fb2; key is node+8, wrapper vtable d1cb50 at+0x10 and geometry vtable d1cb78 at+0x18. Bone-vector ownership is moved into node+0x20/+0x28/+0x30. Linking is explicit at0x42752f..0x42757f. Existing-key branches skip insertion and destroy the temporary; this scoped route is not evidence that the original serialized map preserves every entry or ordering.

The original legacy node's bone vector is already cleared before this destination insertion route (0x425717..0x425738). This is another reason to distinguish owned converted objects from borrowed legacy-root storage. Other field movements and all exceptional cases are not certified by these windows.

## Concrete stopping point

The common parsed-storage conversion is established: legacy integer-keyed optional geometry → shared347dd0/348550 bone storage → converted modern map or348-entry vector → existing geometry construction consumers. Remaining work should target a particular unresolved root field or exact destination selection in36d8c0; it should not expand into a general legacy asset decoder. Version19..26 conversion41fc70 is explicitly separate.

Verification: reproduce.py passes17 aligned original-byte windows and5 exact ELF relocations, linking source-acquisition, bone-hierarchy and modern-schema receipts. It executes only authored Python and objdump, never original machine code.

Evidence: [NATIVE-LEGACY-MODEL-SCHEMA-EVIDENCE-2026-10-18.json](NATIVE-LEGACY-MODEL-SCHEMA-EVIDENCE-2026-10-18.json). Related [modern schema](NATIVE-MODERN-MODEL-SCHEMA-RECOVERY-2026-10-18.md) and [source acquisition](NATIVE-SOURCE-ACQUISITION-RECOVERY-2026-10-18.md). Raw excerpts/reproduction scripts remain external.
