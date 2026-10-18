# Modern model root and bone deserialization contract

## Result

The modern entrypoint 0x41f490 is not one invariant schema for all versions above18. It branches at version27. For27 and later, it reads root+0x160 then root+0x148 as two counted vectors of0x348-byte entries parsed by424920. Each entry embeds, at+0x28, a geometry aggregate with a counted vector of0x80-byte bone records. The bone parser348550 fills the exact parent/name/visibility/pivot/rotation offsets used in the previously established hierarchy and geometry-build consumers. The bridge here establishes native storage identity and read order, not JSON field names or a complete file decoder.

Static analysis only; no target, emulator, JVM, assets, network requests, or repository edits. Original SO SHA25615d0379718c5a293fc2f36fe17f2f95d5a031b8d5564f06355e08640f22b4c22. reproduce.py PASS:11 selected original-byte ranges,10 original ELF RELATIVE relocations. evidence.json is authoritative; address-named exploratory excerpts can contain unreviewed neighboring code or truncated trailing instructions and are not whole-function claims.

## Reader primitives independently verified

For the upstream-established reader vtable d1d408, raw slots are zero in the file: ELF R_X86_64_RELATIVE records, not raw zeros, resolve dispatch.

- Slot+0x10 (d1d418)->4c39e0. Unsigned32 storage assembled from one to five bytes: payload7-bit groups at shifts0,7,14,21 and final shift28. A high bit on each of the first four continues; fifth-byte high bit enters an error path. The fifth payload is shifted in32-bit arithmetic without a demonstrated check that bits4..6 are zero, so do not claim canonical/overflow-rejecting ULEB32.
- Slot+0x28 (d1d430)->4c3f90. Requests exactly4 bytes directly into destination from reader+0x10's stream. No byte swap in this helper. Bone consumers interpret these as float32.
- Slot+0x38 (d1d440)->4c3fc0. Calls slot+0x28 into temporary float32, then cvtss2sd and stores float64. Thus double-valued native property destinations are populated from4-byte floats, not8-byte serialized doubles.
- Slot+0x40 (d1d448)->4c3ff0. Reads one byte, accepts only0 or1, otherwise enters error path.
- Slot+0x48 (d1d450)->4c40d0. Reads length via slot+0x10, rejects length>=0x1000001 (allows up to16MiB), adjusts the destination string length, then requests exactly that many raw bytes. This selection establishes no encoding/UTF-8 validation. NUL-terminated native string layout is distinct from wire length prefix.

This is file-format primitive evidence under the reader identity furnished by the upstream source-acquisition evidence. No underlying stream successful-read/EOF contract is newly proven here.

## Root layout and order at41f490

Let M=rdi root; R=rsi reader; version=R+0xc; read mode R+8==1.

1. M+0x178 virtual slot+0x10 always runs first (41f4a7..41f4b5). Constructor424e08..424e0f installs d1c3d0; RELATIVE d1c3e0 resolves350570. Its body remains opaque in this cohort.
2. For version>=27: first clear/read M+0x160 vector, then M+0x148 vector. Each begin/end/capacity triple is spaced8 bytes. Counts use reader+0x10. A count0 skips the loop via subtract1/unsigned borrow. Each item initializes a temporary0x348 object, calls424920, then move-constructs via4240e0 or grows via424780. End increments0x348 (41f7b8,41fa08).
3. For version<27: call41fc70 at41fc38 instead of the two modern vector readers, then join at41f584. This legacy-compatible map/conversion body is not fully reconstructed here. Upstream entrypoint gating makes relevant range19..26; do not apply27+ vector wire ordering to19..26.
4. A varuint selector follows. Exactly1 activates optional region M+8 via421c60, with presence byte M+0x140. The active branch invokes421d60(R,M+0x48),422230(R,M+0x80),422680(R,M+0xb8),422db0(R,M+0x10), in that order. Non1 follows absence/destruction logic; it is not proven to reject values>1.
5. Remaining calls: string(M+0x230);4211d0(R,M+0x258);virtual(M+0x390,+0x10);421280(R,M+0x4e0); if version>=20,421280(R,M+0x518); if version>=27,varuint(M+0x250);421070(R,M+0x550);string(M+0x5a8).

Constructor424eef..424ef6 installs d1d030 at M+0x390; RELATIVE d1d040 resolves354e00. No semantic label is assigned to the opaque root sections. No complete root schema length or absolute wire offsets follow while they remain opaque.

## Modern entry to geometry aggregate

Let E be either0x348 vector entry.424920's read order is:

-424a20(R,E+0x1f0), an optional subobject; version>=22 additionally424bc0(R,E+0x240).
-string(E+0x2f0),reader slot+0x58(E+0x2c0),varuint(E+0x2e0),varuint(E+0x2e4).
-version>=23: varuint(E+0x2e8),varuint(E+0x2ec); older versions explicitly set both to1.
-411a10(R,E+0x310),string(E+0x1d0).
-virtual(E+0x28,+0x10) at4249e6..4249f1.
-version>=27:346ba0(R,E+8).

Temporary construction41f7fe..41f805 installs d1cb78 at E+0x28 (temporary base rsp+0x10, store rsp+0x38). RELATIVE d1cb88 resolves347dd0. Thus G=E+0x28 is the geometry aggregate consumed by this serializer, without guessing by struct resemblance.

347dd0 reads count then0x80-byte bones into G+8/+0x10/+0x18; it constructs temporary bone vtable d1cda8 and calls348550 at347f5f. RELATIVE d1cdb8 independently agrees348550. It then dispatches embedded G+0x20 through virtual+0x10 (347e49..347e58). E construction installs d1d300 at E+0x48=G+0x20, and RELATIVE d1d310 resolves347860.

347860's prefix reads a string at P+8, four float32-promoted-to-double values at P+0x28/+0x30/+0x38/+0x40, then a varuint-counted array of promoted values at P+0x48/+0x50/+0x58. Since P=G+0x20, these are exactly G+0x48/+0x50/+0x58/+0x60 and array G+0x68/+0x70 used by the prior Java properties constructor evidence. It next reads P+0x60/+0x68 similarly and contains a further optional region; no complete properties schema is claimed.

## Bone record B: verified serialized order

348550 supplies:
1. string at B+8. Prior hierarchy consumer uses pointerB+8,lengthB+0x10 as parent name.
2. varuint count, followed by0x28-byte elements in B+0x28/+0x30/+0x38. Each temporary uses vtable d1cd08, calls3489f0 at34874f, and advances destination by0x28 at348721. Their detailed content is the next frontier.
3. string at B+0x40. Prior hierarchy and JNI consumer use this as bone name (lengthB+0x48).
4. Five independently validated boolean bytes to B+0x60,+0x61,+0x62,+0x63,+0x64, in order.
5. Six4-byte scalar reads to B+0x68,+0x6c,+0x70,+0x74,+0x78,+0x7c, in order.

The prior geometry-build consumer maps B+0x61..63 to three Java constructor boolean arguments and B+0x68..7c to authored pivots and rotations; the native geometry producer scales only pivot copies by1/16. Here the producer establishes their wire reads. B+0x60 and+0x64 remain unnamed. No rotation-unit, transform-order, JSON, or source field spelling is inferred.

Move sequences348078..348107 preserve bone fields into the retained0x80-byte vector record; temporary offsets differ because its base is rsp+0x10. The bone vector's G+8/+0x10 and stride0x80 match the prior hierarchy consumer's exact source aggregate layout. A complete audit of which root collection/variant each36d8c0 branch selects is not part of this result.

## Bounded next frontier and limitations

Next:3489f0, the immediate parser of B+0x28's0x28-byte elements, and only its immediate element-dispatch target if needed to pin primitive geometry fields. This advances geometry payload layout while preserving a finite stopping point. Do not expand unrelated root sections or all transitive parser calls.

Still unresolved:19..26 root mapping conversion41fc70; opaque root350570/354e00 and optional sections; entry slot+0x58 and411a10; complete properties optional fields; root-selection to every construction branch; graph validation/cycle/depth bounds; numeric count/allocation limits; malformed/truncated input behavior outside the selected helpers. This is not a usable full decoder, successful model load, or exploit finding.

Evidence: [NATIVE-MODERN-MODEL-SCHEMA-EVIDENCE-2026-10-18.json](NATIVE-MODERN-MODEL-SCHEMA-EVIDENCE-2026-10-18.json). Related [source acquisition](NATIVE-SOURCE-ACQUISITION-RECOVERY-2026-10-18.md), [geometry construction](NATIVE-GEOMETRY-BUILD-RECOVERY-2026-10-18.md) and [bone hierarchy](NATIVE-BONE-HIERARCHY-RECOVERY-2026-10-18.md). Raw evidence remains external.
