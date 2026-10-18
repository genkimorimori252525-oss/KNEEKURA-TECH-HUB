# Root section M+0x390: bounded schema and conversion contract

## Proven result

S=M+0x390 contains two float32 values, a string-pair collection, two version-gated vectors with nested string/numeric records, and trailing strings/booleans. It is consumed by3a7cc0, with exact literal fallback `idle` and nested discriminators `range`/`radio`. These literals alone do not establish an animation/controller/expression class identity. Java metadata remains the finite naming frontier.

Static original-byte work only. No original target, JVM, assets or callbacks executed. The pinned original SO hash and exact byte ranges/ELF relocations are recorded in evidence.json; reproduce.py verifies20 selected ranges and4 RELATIVE targets. Exploratory files not listed by evidence.json are not authoritative instruction-boundary evidence.

## Root and reader identities

424eef..424ef6 stores d1d030 at M+390. ELF slot d1d040 resolves to354e00. Modern root41f629..41f63a invokes this section's slot+10. Reader contracts are inherited from the preserved model-modern-schema-contract receipt: +28 reads4 raw bytes used as float32; +38 reads float32 and promotes to float64; +40 validates boolean0/1; +48 reads length-prefixed string bytes; +10 supplies the documented variable-length unsigned32 count. No UTF-8 validation or canonical variable-integer claim is added.

## Immediate wire order and storage

| Order | Destination relative to S | Operation and gate |
|---|---|---|
|1|+08,+0c|two4-byte reads through reader+28,354e17..354e30|
|2|+10|352db0: count followed by string/string pairs|
|3|+98/+a0/+a8|version>=12: counted vector of0x80-byte entries, parser356040|
|4|+b0/+b8/+c0|version>=12: counted vector of0xb0-byte entries, parser355cf0|
|5|+c8,+e8|two strings,355808..355827|
|6|+109|boolean,35582a..355838|
|7|+108|boolean if version>=8|
|8|+10a|boolean if version>=13|
|9|+10b|boolean if version>=14|
|10|+10c|boolean if version>=17|
|11|+10d|boolean if version>=32|
|12|+110,+130|two strings if version>=20|

The gates are nested: failure of a threshold exits the trailing schema. For accepted modern versions19..32 the >=8/12/13/14/17 fields are always present; the final strings start at20 and +10d at32. The >=32 boolean is serialized before the >=20 strings. No values are read into alignment padding.

352db0 input mode clears prior contents and reads a count, then two strings per entry at352f1c/352f2a. It creates owned pair temporaries, calls353180, and frees residual temporaries. Storage is segmented: records are0x40 bytes (two0x20 native strings), blocks0x200 bytes (eight records), with an8-byte-per-slot hash/index structure. 353180 hashes the first string using2ac0c0 and tests slot/index/hash/string length/bytes. This cohort does not fully prove duplicate-key replacement policy or complete iterator invariants. The serialized counterpart traverses pair records in storage order (3530d5..353109), not a simple contiguous vector assumed from appearance. The collection spans0x88 bytes, ending before S+98.

First vector entry E (0x80): tabled1d058 slot+10 RELATIVE->356040. Input order is strings E+8,E+28,E+48, then counted nested vector at E+68/+70/+78, stride0x128. Nested entry F tabled1d080 slot+10 RELATIVE->356840 reads four strings F+8/+28/+48/+68, three promoted float32 values into doubles F+88/+90/+98, then352db0 string-pair collection F+a0. These are three4-byte serialized numbers, not serialized doubles.

Second vector entry H (0xb0): tabled1d0a8 slot+10 RELATIVE->355cf0 reads string H+8 then352db0 collection H+28. The vector input path clears existing elements through their virtual destructor, reads count, parses a temporary, and appends. No fixed semantic names are assigned to these strings or numbers.

## Ownership

354e63..354e95 destroys old first-vector entries and resets end to begin. Appending transfers heap string pointers and resets temporary strings; inline strings copy. The nested vector triple transfers and the temporary clears. Growth allocates/rebuilds owned entries and frees old storage. The second-vector path3553f1..355428 similarly destroys0xb0 records and resets end; appended strings and nested collection transfer through354a40. Nested0x128 entries use3564a0 for transfer, with temporary destruction3566e0. These helpers' complete exception guarantees and allocator limits remain outside this slice. There is no evidence of borrowing the temporary stack entries after append.

## Nearest consumers and exact limits

36d99f..36d9ae preserves model M at stack+d8.3715a1..3715af passes M to3a59f0. At3a6ce8..3a6d0d, nonzero M+140 selects the conversion that passes S=M+390 to3a7cc0. RCX is loaded via [M+f0] as a fallback pointer; its semantic identity is not established. Zero M+140 branches to365720 at3a775e; this cohort does not trace that alternative implementation.

3a7cc0 borrows S:
- S+c8 is used if its length S+d0 is nonzero; otherwise incoming fallback RCX is used. JNI+538 receives the selected pointer at3a7cf4.
- S+e8 is copied when its length S+f0 is nonzero; otherwise3a7dbd writes exact four-byte literal `idle`, then JNI+538 receives it at3a7de5. This is a default string, not by itself an animation-state proof.
- The0x80 vector count is computed from(S+a0 - S+98)/128 at3a839f..3a83ad. JNI+560 allocates an object array using class descriptor managerd355a0+68. The nested0x128 vector uses class slot+70 at3a8530..3a855c. These prove typed Java array construction, not class names.
- Nested F+8 length==5 is checked at3a8724. Bytes equal `range` branch to3a87f6; bytes equal `radio` branch to3a88a5; other values use d355a0+78 at3a875c..3a8795. `range` construction uses slot+80 and reads F+88/+90/+98 doubles. The literal comparison is exact; a UI interpretation is plausible but remains proposed without original Java identity.
- The0xb0 vector count is computed at3a9592..3a95ae, and its array class is managerd355a0+60 at3a958b. Low32 counts are supplied to JNI; full representability/limit guarantees are not established.
- Final construction uses managerd355a0+58 at3a9d86, then364a60 at3a9e04. S+8/+c are loaded as float32 and promoted for variadic passing; S+109/+108/+10b are passed as zero-extended bytes. Returned reference is stored in the caller's JNI-reference wrapper at3a9e1e..3a9e3f. Native S ownership does not transfer at this immediate boundary.

A direct geometry connection is separately proven: S+10a=M+49a and S+10c=M+49c are loaded at36def6/36defd and passed on the key1 geometry construction call36df27->36a6e0. Their exact semantic labels remain unresolved. This joins serialized booleans to the existing geometry contract without claiming every field is renderer data.

## Finite next frontier

Resolve original Java metadata for d355a0+58 (final constructor), +60/+68/+70 (array classes), and only then the range/radio constructors if needed. Those identities can distinguish configuration/control metadata from animation/controller/expression payloads. This report does not decode all3a7cc0 behavior, trace365720, prove full duplicate handling in353180, or expand unrelated root sections. No runtime selection, successful object construction or complete model-load claim is made.

Evidence: [NATIVE-MODEL-SECTION390-EVIDENCE-2026-10-18.json](NATIVE-MODEL-SECTION390-EVIDENCE-2026-10-18.json). Later [three exact identities](NATIVE-SECTION390-METADATA-2026-10-18.json) resolve slots+0x58/+0x60/+0x68 only. Slot+0x68 owner matches the existing [ExtraAnimationButton carrier evidence](ROULETTE-FORM-OWNERSHIP-RECOVERY-2026-10-17.md); readable labels retain their prior semantic scope. Other metadata slots and full argument semantics remain bounded. Raw ranges/reproduction scripts remain external.
